#!/usr/bin/env python3
"""
Model fidelity check for NYC311-Operations.SemanticModel (TMDL). Python 3.9+, standard library only.

The v1 model is AI-built and owner-directed (decision of 23 Sep 2026): it was written from the
reference solution in answer-key/ANSWER-KEY.md (parts K1-K7) and from _design/SPEC.md. This tool
keeps the two in step. It prints one line per object and exits 1 on any unexplained difference.

Section 1, code fidelity. Every M and DAX block in the TMDL (shared expressions, M and calculated
partitions, measures, calculated columns, calculation items and their format-string expressions,
role filters) is compared with the block of the same name in the answer key, after normalisation:
comments removed, whitespace outside string literals collapsed, and whitespace next to punctuation
dropped. So re-indentation (TMDL needs tabs) and comments never count; a changed token always does.
Intentional differences are listed in ALLOWED below, each with its reason.

Section 2, check-query names. Every table, column and measure that checks/dax/*.dax names must
exist in the model, under exactly that name (SPEC 9.2).

Section 3, model references. Every Table[Column] that the model's own DAX names must exist, and
every bare [Measure] in a measure or calculation item must be a measure, and no measure may
share a name with a column (case-insensitive).

What a pass does NOT prove: that Power Query or DAX run, or that any number reconciles. Nothing
here evaluates M or DAX; that happens only in Power BI (SPEC 9.4), and until then every result is
[unrun]. The answer key is gitignored, so in a clone without it section 1 is skipped (exit 2);
--no-key runs sections 2 and 3 alone.

Usage:  python3 tools/check_model_fidelity.py [--repo DIR] [--model DIR] [--key FILE] [--no-key]
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys
from typing import Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------- allow-list (each with a reason)
# Keys are object ids as printed by this tool: (kind, name) or ("RLS", role, table).
ALLOWED: Dict[Tuple[str, ...], Dict[str, object]] = {
    ("M", "pDataBaseUrl"): {
        "replace": [("<github-user>", "rashadul122")],
        "reason": "SPEC 3.2/3.4 leave the GitHub account as a placeholder to fill in task 1; "
                  "the owner's account is rashadul122",
    },
    ("M", "Borough"): {
        "no_key": True,
        "reason": "the key gives no code for Borough, only a one-line note that it follows the Agency "
                  "pattern (borough, borough_sort); written from that note and SPEC 3.5",
    },
    ("M", "Channel"): {
        "no_key": True,
        "reason": "the key gives no code for Channel, only a one-line note naming its three renamed "
                  "columns; written from that note and SPEC 3.5",
    },
    ("M", "Borough Access"): {
        "no_key": True,
        "reason": "the key gives no code for Borough Access, only a one-line note naming its two "
                  "renamed columns; written from that note and SPEC 3.5",
    },
    ("M", "Requests Daily"): {
        "replace": [('{{"Requests", each', '{{"Request Count", each')],
        "reason": "the count column is named Request Count, not Requests, so no column shares a name "
                  "with the [Requests] measure (section 3 name check); SPEC 5.1 never names this column "
                  "and no check query or expected file uses it",
    },
    ("DAX", "Requests (Daily)"): {
        "replace": [("'Requests Daily'[Requests]", "'Requests Daily'[Request Count]")],
        "reason": "reads the renamed count column (see M / Requests Daily)",
    },
    ("M", "_Measures"): {
        "no_key": True,
        "reason": "the measure home table of SPEC 5.1 (no rows); the key has no query for it",
    },
}

DAX_WORDS = ("VAR ", "RETURN", "IF ", "IF(", "EVALUATE", "DEFINE", "ORDER BY")


# ---------------------------------------------------------------- normalisation
def strip_comments(code: str) -> str:
    """Remove // and /* */ comments outside "..." and '...' literals (M and DAX)."""
    out: List[str] = []
    i, n = 0, len(code)
    while i < n:
        c = code[i]
        if code.startswith("//", i):
            j = code.find("\n", i)
            i = n if j < 0 else j
            continue
        if code.startswith("/*", i):
            j = code.find("*/", i + 2)
            i = n if j < 0 else j + 2
            out.append(" ")
            continue
        if c in "\"'":
            j = i + 1
            while j < n:
                if code[j] == c:
                    if j + 1 < n and code[j + 1] == c:      # doubled quote = escaped
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


def normalise(code: str) -> str:
    """Comments out; whitespace outside literals collapsed; whitespace next to punctuation dropped."""
    lits: List[str] = []

    def keep(m: "re.Match[str]") -> str:
        lits.append(m.group(0))
        return "\x01%d\x02" % (len(lits) - 1)

    s = re.sub(r'"(?:[^"]|"")*"|\'(?:[^\']|\'\')*\'', keep, strip_comments(code))
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r" ?([^\w .#@]) ?", r"\1", s)
    return re.sub(r"\x01(\d+)\x02", lambda m: lits[int(m.group(1))], s)


# ---------------------------------------------------------------- TMDL side
_OBJ = re.compile(r"^(table|role|expression|measure|column|calculationItem|tablePermission|partition|"
                  r"source|formatStringDefinition)\b\s*(.*)$")


def _name(rest: str) -> Tuple[str, str]:
    rest = rest.strip()
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


def _depth(line: str) -> int:
    return len(line) - len(line.lstrip("\t"))


def _collect(lines: List[str], i: int, d: int, first: str) -> Tuple[str, int]:
    """Expression starting on line i (declared at depth d): inline text, or the deeper lines below."""
    if first:
        return first, i + 1
    body: List[str] = []
    j = i + 1
    while j < len(lines):
        ln = lines[j]
        if ln.strip() and _depth(ln) <= d + 1:
            break
        body.append(ln)
        j += 1
    while body and not body[-1].strip():
        body.pop()
    pad = min((_depth(x) for x in body if x.strip()), default=0)
    return "\n".join(x[pad:] if x.strip() else "" for x in body), j


class Model:
    def __init__(self, definition: str):
        self.code: Dict[Tuple[str, ...], str] = {}
        self.where: Dict[Tuple[str, ...], str] = {}
        self.columns: Dict[str, Set[str]] = {}
        self.measures: Set[str] = set()
        self.tables: Set[str] = set()
        files = [os.path.join(definition, "expressions.tmdl")] + \
            sorted(glob.glob(os.path.join(definition, "tables", "*.tmdl"))) + \
            sorted(glob.glob(os.path.join(definition, "roles", "*.tmdl")))
        for f in files:
            if os.path.exists(f):
                self._read(f, os.path.relpath(f, os.path.dirname(definition)))

    def _put(self, oid: Tuple[str, ...], code: str, where: str) -> None:
        if oid in self.code:
            raise SystemExit("model: %s defined twice (%s, %s)" % (_fmt(oid), self.where[oid], where))
        self.code[oid] = code
        self.where[oid] = where

    def _read(self, path: str, rel: str) -> None:
        lines = open(path, encoding="utf-8").read().split("\n")
        table = role = item = None
        part: Optional[Tuple[str, str]] = None
        i = 0
        while i < len(lines):
            ln = lines[i]
            body = ln.strip()
            d = _depth(ln)
            m = _OBJ.match(body) if body and not body.startswith("///") else None
            if not m:
                i += 1
                continue
            kind, rest = m.group(1), m.group(2)
            where = "%s:%d" % (rel, i + 1)
            if kind == "table" and d == 0:
                table, role, part = _name(rest)[0], None, None
                self.tables.add(table)
                self.columns.setdefault(table, set())
            elif kind == "role" and d == 0:
                role, table = _name(rest)[0], None
            elif kind == "expression" and d == 0:
                name, tail = _name(rest)
                code, i = _collect(lines, i, d, tail[1:].strip() if tail.startswith("=") else "")
                self._put(("M", name), code, where)
                continue
            elif kind in ("measure", "column") and d == 1 and table:
                name, tail = _name(rest)
                (self.measures.add(name) if kind == "measure" else self.columns[table].add(name))
                if tail.startswith("="):
                    code, i = _collect(lines, i, d, tail[1:].strip())
                    self._put(("DAX", name), code, where)
                    continue
            elif kind == "calculationItem" and table:
                name, tail = _name(rest)
                item = name
                code, i = _collect(lines, i, d, tail[1:].strip() if tail.startswith("=") else "")
                self._put(("ITEM", name), code, where)
                continue
            elif kind == "formatStringDefinition" and item:
                tail = rest[1:].strip() if rest.startswith("=") else rest
                code, i = _collect(lines, i, d, tail)
                self._put(("FMT", item), code, where)
                continue
            elif kind == "partition" and d == 1 and table:
                pname, tail = _name(rest)
                part = (pname, tail.lstrip("= ").strip())
            elif kind == "source" and part and table:
                tail = rest[1:].strip() if rest.startswith("=") else rest
                code, i = _collect(lines, i, d, tail)
                lang = {"m": "M", "calculated": "DAX"}.get(part[1], part[1])
                self._put((lang, table), code, where)
                continue
            elif kind == "tablePermission" and role:
                tname, tail = _name(rest)
                code, i = _collect(lines, i, d, tail[1:].strip() if tail.startswith("=") else "")
                self._put(("RLS", role, tname), code, where)
                continue
            i += 1


# ---------------------------------------------------------------- key side
class Key:
    def __init__(self, path: str, dax_names: Set[str]):
        self.code: Dict[Tuple[str, ...], str] = {}
        self.where: Dict[Tuple[str, ...], str] = {}
        text = open(path, encoding="utf-8").read()
        heading = ""
        for m in re.finditer(r"^(#{2,3} [^\n]*)$|^```(\w*)\n(.*?)^```", text, re.S | re.M):
            if m.group(1):
                heading = m.group(1)
                continue
            lang, block = m.group(2), m.group(3)
            line_no = text.count("\n", 0, m.start()) + 1
            section = (re.match(r"#+ (\w+(?:\.\d+)?)", heading) or re.match("(.*)", heading)).group(1)
            where = "key %s (line %d)" % (section, line_no)
            if lang == "m":
                self._m_block(block, heading, where)
            elif lang == "dax":
                if heading.startswith("## K6"):
                    label = self._label(block)
                    self._put(("ITEM", label), block, where)
                else:
                    self._dax_block(block, dax_names, where)
            elif lang == "":
                if block.startswith("role "):
                    self._roles(block, where)
                elif "calculationGroup" in block:
                    item = None
                    for ln in block.split("\n"):
                        mm = re.match(r"^\t+calculationItem\s+('(?:[^']|'')*'|\S+)", ln)
                        if mm:
                            item = mm.group(1).strip("'")
                        mm = re.match(r"^\t+formatStringDefinition\s*=\s*(.+)$", ln)
                        if mm and item:
                            self._put(("FMT", item), mm.group(1), where)

    def _put(self, oid, code, where):
        if oid in self.code:
            raise SystemExit("key: %s appears twice (%s, %s)" % (_fmt(oid), self.where[oid], where))
        self.code[oid] = code
        self.where[oid] = where

    @staticmethod
    def _label(block: str) -> str:
        first = block.split("\n", 1)[0]
        m = re.match(r"^//\s*(.+?)(\s{2,}.*)?$", first)
        return m.group(1).strip() if m else ""

    def _m_block(self, block: str, heading: str, where: str) -> None:
        lines = block.split("\n")
        if "K1.1" in heading:                        # parameters: "// name" then the value line
            for k, ln in enumerate(lines):
                mm = re.match(r"^//\s*(\S+)", ln)
                if mm and k + 1 < len(lines):
                    self._put(("M", mm.group(1)), lines[k + 1], where)
            return
        if lines[0].startswith("//"):
            name = self._label(block)
        else:
            mm = re.search(r"`([^`]+)`", heading)
            name = mm.group(1) if mm else ""
        self._put(("M", name), block, where)

    def _dax_block(self, block: str, names: Set[str], where: str) -> None:
        lines = block.split("\n")
        starts: List[Tuple[int, str]] = []
        for k, ln in enumerate(lines):
            if not ln or ln[0].isspace() or ln.startswith(("//", ")", "{", "}")) or ln.startswith(DAX_WORDS):
                continue
            mm = re.match(r"^(.+?) =(\s|$)", ln)
            if not mm:
                continue
            name = mm.group(1).strip()
            if name in names or "( " not in name:
                starts.append((k, name))
        for j, (k, name) in enumerate(starts):
            end = starts[j + 1][0] if j + 1 < len(starts) else len(lines)
            first = lines[k][len(name):].lstrip()[1:]
            self._put(("DAX", name), "\n".join([first] + lines[k + 1:end]), where)

    def _roles(self, block: str, where: str) -> None:
        role = None
        lines = block.split("\n")
        i = 0
        while i < len(lines):
            ln = lines[i]
            mm = re.match(r"^role\s+(.+)$", ln)
            if mm:
                role = _name(mm.group(1))[0]
                i += 1
                continue
            mm = re.match(r"^\ttablePermission\s+(.+)$", ln)
            if mm and role:
                tname, tail = _name(mm.group(1))
                code, i = _collect(lines, i, 1, tail[1:].strip() if tail.startswith("=") else "")
                self._put(("RLS", role, tname), code, where)
                continue
            i += 1


# ---------------------------------------------------------------- checks
def _fmt(oid: Tuple[str, ...]) -> str:
    return "%-4s %s" % (oid[0], " / ".join(oid[1:]))


def _first_diff(a: str, b: str) -> str:
    k = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    lo = max(0, k - 40)
    return "model ...%s...\n            key   ...%s..." % (a[lo:k + 40], b[lo:k + 40])


def fidelity(model: Model, key: Key) -> int:
    bad = 0
    print("== 1. Code fidelity: TMDL vs answer key (normalised: comments and whitespace ignored)")
    for oid in sorted(set(model.code) | set(key.code), key=lambda o: (o[0], o[1:])):
        allow = ALLOWED.get(oid, {})
        if oid not in key.code:
            if allow.get("no_key"):
                print("  NO-KEY    %s  [allowed: %s]" % (_fmt(oid), allow["reason"]))
            else:
                print("  EXTRA     %s  (%s): no block of that name in the key" % (_fmt(oid), model.where[oid]))
                bad += 1
            continue
        if oid not in model.code:
            print("  MISSING   %s  (%s): not in the model" % (_fmt(oid), key.where[oid]))
            bad += 1
            continue
        mine, ref = normalise(model.code[oid]), key.code[oid]
        for a, b in allow.get("replace", []):
            ref = ref.replace(a, b)
        ref = normalise(ref)
        if mine == ref:
            tag = "MATCH*" if allow.get("replace") else "MATCH"
            note = "  [allowed: %s]" % allow["reason"] if allow.get("replace") else ""
            print("  %-9s %s%s" % (tag, _fmt(oid), note))
        else:
            print("  MISMATCH  %s  (%s vs %s)\n            %s" % (_fmt(oid), model.where[oid], key.where[oid],
                                                              _first_diff(mine, ref)))
            bad += 1
    stale = [o for o in ALLOWED if o not in model.code and o not in key.code]
    for o in stale:
        print("  STALE     allow-list entry %s matches nothing" % _fmt(o))
        bad += 1
    return bad


_QREF = re.compile(r"('(?:[^']|'')+'|\b[A-Za-z_][A-Za-z0-9_]*)\[([^\]]+)\]")
_BARE = re.compile(r"(?<![\w'\]])\[([^\]]+)\]")


def _refs(dax: str) -> Tuple[List[Tuple[str, str]], List[str]]:
    s = strip_comments(dax)
    s = re.sub(r'"(?:[^"]|"")*"', '""', s)                  # string literals out
    q = [(t.strip("'").replace("''", "'"), c) for t, c in _QREF.findall(s)]
    bare_src = _QREF.sub("", s)
    return q, _BARE.findall(bare_src)


def check_queries(model: Model, repo: str) -> int:
    bad = 0
    print("== 2. Names used by checks/dax/*.dax exist in the model")
    files = sorted(glob.glob(os.path.join(repo, "checks", "dax", "*.dax")))
    if not files:
        print("  FAIL      no check queries found under checks/dax/")
        return 1
    for f in files:
        text = open(f, encoding="utf-8").read()
        head = re.split(r"\bORDER\s+BY\b", text)[0]          # ORDER BY names the query's own columns
        q, bare = _refs(head)
        missing = []
        for t, c in q:
            if t not in model.tables:
                missing.append("table %s" % t)
            elif c not in model.columns.get(t, set()):
                missing.append("column %s[%s]" % (t, c))
        for mname in bare:
            if mname not in model.measures:
                missing.append("measure [%s]" % mname)
        name = os.path.basename(f)
        if missing:
            bad += 1
            print("  FAIL      %s: %s" % (name, "; ".join(sorted(set(missing)))))
        else:
            print("  OK        %s: %d column and %d measure references" % (name, len(set(q)), len(set(bare))))
    return bad


def model_refs(model: Model) -> int:
    bad = 0
    print("== 3. References inside the model's DAX resolve")
    n = 0
    for oid, code in sorted(model.code.items()):
        if oid[0] not in ("DAX", "ITEM", "RLS"):
            continue
        q, bare = _refs(code)
        missing = []
        for t, c in q:
            if t not in model.tables:
                missing.append("table %s" % t)
            elif c not in model.columns.get(t, set()):
                missing.append("column %s[%s]" % (t, c))
        if oid[0] == "ITEM" or (oid[0] == "DAX" and oid[1] in model.measures):
            missing += ["measure [%s]" % b for b in bare if b not in model.measures]
        n += 1
        if missing:
            bad += 1
            print("  FAIL      %s (%s): %s" % (_fmt(oid), model.where[oid], "; ".join(sorted(set(missing)))))
    print("  %s %d DAX objects checked" % ("OK       " if not bad else "FAIL     ", n))
    # A measure must not share a name with any column. Possibly stricter than the engine needs
    # (whether the service rejects a cross-table clash is [unverified]); Microsoft's offline TMDL
    # parser accepts even a same-table clash, so nothing else on this Mac would catch one.
    clashes = sorted((m, t) for t, cols in model.columns.items() for m in model.measures
                     if m.lower() in {c.lower() for c in cols})
    for m, t in clashes:
        bad += 1
        print("  FAIL      measure [%s] has the same name as column %s[%s]" % (m, t, m))
    print("  %s %d measures, none named like a column" % ("OK       " if not clashes else "FAIL     ",
                                                          len(model.measures)))
    return bad


def main(argv: Optional[List[str]] = None) -> int:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", default=here)
    ap.add_argument("--model", default=None, help="the .SemanticModel folder (default: in --repo)")
    ap.add_argument("--key", default=None, help="the answer key (default: answer-key/ANSWER-KEY.md in --repo)")
    ap.add_argument("--no-key", action="store_true", help="run sections 2 and 3 only")
    a = ap.parse_args(argv)
    model_dir = a.model or os.path.join(a.repo, "NYC311-Operations.SemanticModel")
    definition = os.path.join(model_dir, "definition")
    if not os.path.isdir(definition):
        print("no TMDL folder at %s" % definition)
        return 2
    model = Model(definition)
    bad = 0
    key_path = a.key or os.path.join(a.repo, "answer-key", "ANSWER-KEY.md")
    skipped = False
    if a.no_key:
        skipped = True
        print("== 1. Code fidelity: skipped (--no-key)")
    elif not os.path.exists(key_path):
        skipped = True
        print("== 1. Code fidelity: skipped, no answer key at %s (it is gitignored)" % key_path)
    else:
        key = Key(key_path, {o[1] for o in model.code if o[0] == "DAX"})
        bad += fidelity(model, key)
    bad += check_queries(model, a.repo)
    bad += model_refs(model)
    print("%d problem(s). Structure and text only: no M or DAX was evaluated [unrun]." % bad)
    if bad:
        return 1
    return 2 if skipped and not a.no_key else 0


if __name__ == "__main__":
    sys.exit(main())
