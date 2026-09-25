#!/usr/bin/env python3
"""
TMDL text-property check for NYC311-Operations.SemanticModel. Python 3.9+, standard library only.

Why it exists. The first Power BI service refresh (24 Sep 2026) failed with "The ''Channel Group''
column does not exist in the rowset". 80 of the 123 sourceColumn values were written
`sourceColumn: 'Channel Group'`. In TMDL, single quotes enclose object names and references to
other objects (sortByColumn, a hierarchy level's column, fromColumn, toColumn, queryGroup). On a
plain text property they are kept as part of the value, so Microsoft's TOM stored
"'Channel Group'" and the engine looked for a column with apostrophes in its name. Microsoft's TMDL
parser, pbip_lint, check_model_fidelity.py and check_report_refs.py all passed that model.
Microsoft Learn, TMDL overview (https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview):
the double quotes around a text property value are optional and are stripped; references "follow
the same escaping and single-quote (') enclosing requirements of object declaration".

Section 1, quoting. A `name: value` property whose value is enclosed in single quotes must be a
reference to another object (REFERENCES below). On any other property the quotes become part of
the text, which is what failed refresh 1. A text value that really starts and ends with a quote
must be written in double quotes, "'X'"; beware that Microsoft's serializer (a commit from the
workspace) writes it back bare as 'X', which this section then flags. Keywords and property names
are compared case-insensitively, as TMDL reads them.

Section 2, source columns. For each table:
  - M partition: every column without a DAX expression has a sourceColumn. Its name must be one the
    partition's Power Query can produce: it appears as a text literal "Name" or a quoted identifier
    #"Name" in the partition query, or in a shared expression or table query that the partition
    reaches. A plain name may instead appear as a word, such as a type field [Date = date]. A
    column taken straight from a file header that no step names fails here on purpose: type it
    in a step (Table.TransformColumnTypes), as every query in this model does.
  - calculated table: sourceColumn is written [Name], the form Microsoft's own TMDL export of this
    model writes, or Table[Name] / 'Table'[Name] for a column that keeps its lineage. Name must
    appear in the table's DAX as "Name" or [Name].
  - calculation group: sourceColumn is Name or Ordinal (Microsoft Learn, calculation groups:
    https://learn.microsoft.com/en-us/analysis-services/tabular-models/calculation-groups).

What a pass does NOT prove: that M or DAX runs, or that a name survives to the query's last step (a
name that a later step removes still passes). Nothing is evaluated here; that happens only in Power
BI (SPEC 9.4).

Usage:  python3 tools/check_tmdl_text.py [--repo DIR] [--model DIR]
Exit 0 clean, 1 any problem, 2 no TMDL folder.
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys
from typing import Dict, List, Optional, Set, Tuple

# TOM properties that hold a reference to another object, so single quotes are name syntax, not
# text. The first five are used in this model; the rest are the other reference properties TMDL
# writes (variations, aggregations, related-column details, entity and query partitions).
REFERENCES = {p.lower() for p in (
    "sortByColumn", "column", "fromColumn", "toColumn", "queryGroup",
    "relationship", "defaultHierarchy", "defaultColumn", "baseColumn", "baseTable",
    "groupByColumn", "expressionSource", "dataSource",
)}                                  # compared lower-case: TMDL reads keywords case-insensitively
CALC_GROUP_SOURCES = {"Name", "Ordinal"}

_PROP = re.compile(r"^(\t*)([A-Za-z][A-Za-z0-9]*)[ \t]*:[ \t]*(.*?)[ \t]*$")
_WORD = re.compile(r"^(\t*)([A-Za-z][A-Za-z0-9]*)\b[ \t]*(.*)$")


# ---------------------------------------------------------------- TMDL reading
def _depth(line: str) -> int:
    return len(line) - len(line.lstrip("\t"))


def _name(rest: str) -> Tuple[str, str]:
    """'My Name' tail / Name tail -> (name, tail); '' when the keyword takes no name."""
    rest = rest.strip()
    if not rest or rest.startswith("="):
        return "", rest
    if rest.startswith("'"):
        i = 1
        while i < len(rest):
            if rest[i] == "'":
                if i + 1 < len(rest) and rest[i + 1] == "'":
                    i += 2
                    continue
                break
            i += 1
        return rest[1:i].replace("''", "'"), rest[i + 1:].strip()
    m = re.match(r"([^\s=]+)\s*(.*)$", rest)
    return (m.group(1), m.group(2).strip()) if m else ("", "")


def _expression(lines: List[str], i: int, d: int, tail: str) -> Tuple[str, int]:
    """The value after '=' on line i (declared at depth d): inline, ``` fenced, or the deeper lines."""
    if not tail.startswith("="):
        return "", i + 1
    first = tail[1:].strip()
    if first == "```":
        j = i + 1
        while j < len(lines) and lines[j].strip() != "```":
            j += 1
        return "\n".join(lines[i + 1:j]), j + 1
    if first:
        return first, i + 1
    j = i + 1
    while j < len(lines) and not (lines[j].strip() and _depth(lines[j]) <= d + 1):
        j += 1
    return "\n".join(lines[i + 1:j]), j


class Tmdl:
    def __init__(self, definition: str):
        self.props: List[Tuple[str, str, str]] = []                # (where, property, raw value)
        self.tables: Dict[str, Dict[str, object]] = {}
        self.expressions: Dict[str, str] = {}
        for f in sorted(glob.glob(os.path.join(definition, "**", "*.tmdl"), recursive=True)):
            self._read(f, os.path.relpath(f, os.path.dirname(definition)))

    def _read(self, path: str, rel: str) -> None:
        lines = open(path, encoding="utf-8").read().split("\n")
        table: Optional[Dict[str, object]] = None
        column: Optional[Dict[str, object]] = None
        i = 0
        while i < len(lines):
            ln = lines[i]
            body = ln.strip()
            where = "%s:%d" % (rel, i + 1)
            if not body or body.startswith("///"):
                i += 1
                continue
            d = _depth(ln)
            m = _PROP.match(ln)
            if m:
                prop, value = m.group(2), m.group(3)
                self.props.append((where, prop, value))
                if prop.lower() == "sourcecolumn" and column is not None and d == 2:
                    column["source"] = value
                    column["source_where"] = where
                i += 1
                continue
            w = _WORD.match(ln)
            if not w:
                i += 1
                continue
            word = w.group(2).lower()
            name, tail = _name(w.group(3))
            code, nxt = _expression(lines, i, d, tail)
            if d == 0:
                table = column = None
                if word == "table":
                    table = self.tables.setdefault(name, {"kind": None, "code": "", "columns": [], "where": where})
                elif word == "expression":
                    self.expressions[name] = code
            elif table is not None and d == 1:
                column = None
                if word == "column":
                    column = {"name": name, "calc": tail.startswith("="), "source": None, "where": where}
                    table["columns"].append(column)                 # type: ignore[union-attr]
                elif word == "partition":
                    table["kind"] = tail.lstrip("= ").strip().lower()
                elif word == "calculationgroup":
                    table["kind"] = "calculationgroup"
            elif table is not None and d == 2 and word == "source":
                table["code"] = code
            i = nxt


# ---------------------------------------------------------------- the names a query can produce
def _strip(code: str, quotes: str, dash_comments: bool) -> str:
    """Comments out (// and /* */, and -- when asked), outside the given literal quote characters."""
    out: List[str] = []
    i, n = 0, len(code)
    while i < n:
        c = code[i]
        if code.startswith("//", i) or (dash_comments and code.startswith("--", i)):
            j = code.find("\n", i)
            i = n if j < 0 else j
            continue
        if code.startswith("/*", i):
            j = code.find("*/", i + 2)
            i = n if j < 0 else j + 2
            out.append(" ")
            continue
        if c in quotes:
            j = i + 1
            while j < n:
                if code[j] == c:
                    if j + 1 < n and code[j + 1] == c:
                        j += 2
                        continue
                    break
                j += 1
            out.append(code[i:j + 1])
            i = j + 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


_M_TOKEN = re.compile(r'#"((?:[^"]|"")*)"|"((?:[^"]|"")*)"|(\[\s*)?([A-Za-z_][A-Za-z0-9_.]*)')
_M_STEP = re.compile(r'(?m)^\s*(#"(?:[^"]|"")*"|[A-Za-z_][A-Za-z0-9_]*)\s*=(?![=>])')


def _m_names(code: str) -> Tuple[Set[str], Set[str]]:
    """(names the code writes: literals, quoted identifiers, words; query names it may reference)."""
    s = _strip(code, '"', False)
    steps = {x[2:-1].replace('""', '"') if x.startswith("#") else x for x in _M_STEP.findall(s)}
    produced: Set[str] = set()
    refs: Set[str] = set()
    for m in _M_TOKEN.finditer(s):
        if m.group(1) is not None:
            v = m.group(1).replace('""', '"')
            produced.add(v)
            refs.add(v)
        elif m.group(2) is not None:
            produced.add(m.group(2).replace('""', '"'))
        else:
            produced.add(m.group(4))
            if not m.group(3):                                   # [Name] is a field, not a query
                refs.add(m.group(4))
    return produced, refs - steps


def _dax_names(code: str) -> Set[str]:
    s = _strip(code, "\"'", True)
    return {v.replace('""', '"') for v in re.findall(r'"((?:[^"]|"")*)"', s)} | set(re.findall(r"\[([^\]]+)\]", s))


# ---------------------------------------------------------------- checks
def check_quotes(model: Tmdl) -> int:
    print("== 1. Single quotes only on references (a text property keeps them as part of its value)")
    bad = refs = 0
    for where, prop, value in model.props:
        if len(value) < 2 or not (value.startswith("'") and value.endswith("'")):
            continue
        if prop.lower() in REFERENCES:
            refs += 1
            continue
        bad += 1
        print("  FAIL      %s  %s: %s  (a text property keeps the quotes; write %s: %s, or %s: \"%s\" "
              "if the quotes really belong to the value)"
              % (where, prop, value, prop, value[1:-1].replace("''", "'"), prop, value))
    print("  %s %d properties read, %d quoted references, %d quoted text values"
          % ("OK       " if not bad else "FAIL     ", len(model.props), refs, bad))
    return bad


def check_sources(model: Tmdl) -> int:
    print("== 2. Every sourceColumn names a column its partition produces")
    queries = dict(model.expressions)
    queries.update({t: str(tb["code"]) for t, tb in model.tables.items() if tb["kind"] == "m"})
    parsed = {q: _m_names(code) for q, code in queries.items()}

    def reachable(start: str) -> Set[str]:
        seen, todo = {start}, [start]
        while todo:
            for r in parsed[todo.pop()][1]:
                if r in parsed and r not in seen:
                    seen.add(r)
                    todo.append(r)
        return seen

    bad = 0
    for tname in sorted(model.tables):
        tb = model.tables[tname]
        kind = tb["kind"]
        cols = [c for c in tb["columns"] if not c["calc"]]            # type: ignore[union-attr]
        problems: List[str] = []
        if kind is None:
            problems.append("no partition (%s)" % tb["where"])
        elif kind == "m":
            names: Set[str] = set()
            for q in reachable(tname):
                names |= parsed[q][0]
        elif kind == "calculated":
            names = _dax_names(str(tb["code"]))
        elif kind == "calculationgroup":
            names = CALC_GROUP_SOURCES
        else:
            names = set()
            problems.append("partition type %s is not checked by this tool" % kind)
        for c in cols:
            raw = c["source"]
            if raw is None:
                problems.append("column %s (%s): no sourceColumn" % (c["name"], c["where"]))
                continue
            v = str(raw)
            if len(v) >= 2 and v.startswith('"') and v.endswith('"'):
                v = v[1:-1].replace('""', '"')
            if kind == "calculated":
                mm = re.match(r"^(?:'(?:[^']|'')+'|[A-Za-z_][A-Za-z0-9_ ]*)?\[(.+)\]$", v)
                if not mm:
                    problems.append("column %s (%s): sourceColumn %s is not written [Name] or Table[Name]" % (c["name"], c["source_where"], raw))
                elif mm.group(1) not in names:
                    problems.append("column %s (%s): sourceColumn %s, the DAX never names %s"
                                    % (c["name"], c["source_where"], raw, mm.group(1)))
            elif kind in ("m", "calculationgroup") and v not in names:
                what = "the partition's Power Query never names" if kind == "m" else "a calculation group column binds Name or Ordinal, not"
                problems.append("column %s (%s): sourceColumn %s, %s %s" % (c["name"], c["source_where"], raw, what, v))
        if problems:
            bad += len(problems)
            for p in problems:
                print("  FAIL      %s: %s" % (tname, p))
        else:
            print("  OK        %s (%s): %d source column(s)" % (tname, kind, len(cols)))
    return bad


def main(argv: Optional[List[str]] = None) -> int:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", default=here)
    ap.add_argument("--model", default=None, help="the .SemanticModel folder (default: in --repo)")
    a = ap.parse_args(argv)
    model_dir = a.model or os.path.join(a.repo, "NYC311-Operations.SemanticModel")
    definition = os.path.join(model_dir, "definition")
    if not os.path.isdir(definition):
        print("no TMDL folder at %s" % definition)
        return 2
    model = Tmdl(definition)
    bad = check_quotes(model) + check_sources(model)
    print("%d problem(s). Text and names only: no M or DAX was evaluated [unrun]." % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
