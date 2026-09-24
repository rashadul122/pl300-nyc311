#!/usr/bin/env python3
"""
python -m northledger.pbi -- does the owner's Power BI model return the expected numbers?

    reconcile [--repo PATH] --profile dev|full [--checks C1,C3]

For each check Cn it joins

    observed/<profile>/Cn.tsv (or Cn.csv)   what the owner's DAX returned: the grid pasted
                                            from DAX query view, or a DAX Studio export
    expected/<profile>/Cn.csv               what the independent pandas twin computed

on the key columns named in checks/spec/Cn.json, and compares every measure cell
(SPEC 9.4):

    counts and whole numbers    exact
    hours, ratios, averages     relative tolerance (1e-9 in the published specs)
    BLANK and 0                 different values: they never match each other
    booleans, dates, text       exact, after the display format is normalised

A row only in expected is "missing"; a row only in observed (or a second copy of
one) is "extra". That includes an expected row whose measure values are all BLANK
(C1's completeness-guard rows, C4's month ends outside the window): the constant
"Check Row" column makes DAX return it, so it must be in observed with its BLANKs,
and if it is absent every cell of it is "missing", which fails the check.

A spec measure may carry "constant": the value every expected cell of that column
holds (Check Row = 1). An expected file that breaks it is bad input (exit 2).

Which checks run (--checks names them; case does not matter, c5B = C5b):

    default     every checks/spec/Cn.json except the opt-in ones: C1-C5, C5b and L
    opt-in      C4r, the interview drill's check (SPEC Appendix C); only with --checks C4r

Load rows (check_id L, SPEC 9.4): each window file's manifest rows against C1's
observed Current Requests for that Year Month (month rows, summed over boroughs),
and the carry-in file's rows against C3's observed Carry-in Rows summed over
agencies. The manifest is data/<profile>/manifest.json.

Results go to reconcile/<profile>/reconciliation_results.csv:

    check_id, key, measure, expected, observed, status (pass|fail|missing|extra), run_at

The rows of the checks that ran (and the L rows they feed) are replaced; rows of
checks that did not run are kept with their own run_at, so skipping a check never
makes page 10 look greener.

Observed files may be tab-, comma- or semicolon-separated, UTF-8 (with or without a
BOM) or UTF-16. Headers such as 'Date'[Year Month], Borough[Borough] and [Requests]
become Year Month, Borough and Requests. Values such as 1,234  12.5%  +3.1%  True
and 8/31/2026 12:00:00 AM are understood; a decimal comma (12,5) is not, on purpose:
the model's culture is en-US, and guessing would turn 12,5 into 125.

Exit codes: 0 every cell passes, 1 any cell is fail/missing/extra, 2 bad input
(a clear message, and nothing is written).
"""
from __future__ import annotations

import argparse
import codecs
import collections
import csv
import datetime as _dt
import io
import json
import math
import os
import re
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

EXIT_PASS, EXIT_FAIL, EXIT_BAD = 0, 1, 2
PROFILES = ("dev", "full")
RESULT_COLUMNS = ["check_id", "key", "measure", "expected", "observed", "status", "run_at"]
STATUSES = ("pass", "fail", "missing", "extra")

NUMERIC_KINDS = ("count", "integer", "hours", "ratio", "average")
WHOLE_KINDS = ("count", "integer")
KINDS = NUMERIC_KINDS + ("boolean", "date", "text")
KEY_KINDS = ("text", "integer", "boolean", "date")

_CHECK_FILE = re.compile(r"^(C[1-9][0-9]*[a-z]?)\.json$")
_CHECK_ID = re.compile(r"^C([1-9][0-9]*)([a-z]?)$")
# Checks that run only when --checks names them (lead decision 2: C4r is the drill's check).
OPT_IN_CHECKS = ("C4r",)
LOAD_CHECK = "L"
# The load check (SPEC 9.4) reads these observed columns; a spec without them does not feed it.
LOAD_WINDOW_SOURCE = ("C1", ("Year Month", "Time View"), "Requests", "Current")
LOAD_CARRYIN_SOURCE = ("C3", "Carry-in Rows")
_LOAD_MEASURE_WINDOW = "Rows (C1 Current Requests, summed over boroughs)"
_LOAD_MEASURE_CARRYIN = "Rows (C3 Carry-in Rows, summed over agencies)"
_LOAD_SOURCE = re.compile(r"^Rows \((C[1-9][0-9]*[a-z]?) ")


class BadInput(Exception):
    """The inputs cannot be reconciled at all. The message says what to fix."""


# --------------------------------------------------------------------------- spec

def _rule(obj: Any, where: str, key: bool = False) -> Dict[str, Any]:
    if not isinstance(obj, dict):
        raise BadInput("%s must be an object like {\"kind\": \"count\", \"compare\": \"exact\"}" % where)
    kind = obj.get("kind")
    allowed = KEY_KINDS if key else KINDS
    if kind not in allowed:
        raise BadInput("%s: kind must be one of %s, not %r" % (where, ", ".join(allowed), kind))
    compare = obj.get("compare", "exact")
    constant = None
    if "constant" in obj:
        constant = obj["constant"]
        if key or kind not in WHOLE_KINDS or compare != "exact":
            raise BadInput("%s: constant is only for an exact count or integer measure" % where)
        if isinstance(constant, bool) or not isinstance(constant, int):
            raise BadInput("%s: constant must be a whole number, not %r" % (where, constant))
    if compare == "exact":
        return {"kind": kind, "compare": "exact", "rel_tol": 0.0, "constant": constant}
    if compare == "rel_tol" and not key:
        if kind not in NUMERIC_KINDS:
            raise BadInput("%s: rel_tol only applies to numbers, not to kind %r" % (where, kind))
        tol = obj.get("rel_tol")
        if isinstance(tol, bool) or not isinstance(tol, (int, float)) or not (0 < tol < 1):
            raise BadInput("%s: rel_tol must be a number between 0 and 1, not %r" % (where, tol))
        return {"kind": kind, "compare": "rel_tol", "rel_tol": float(tol), "constant": None}
    raise BadInput("%s: compare must be %s, not %r"
                   % (where, "'exact'" if key else "'exact' or 'rel_tol'", compare))


class Spec(object):
    """checks/spec/Cn.json: the key columns and each measure's comparison."""

    def __init__(self, check_id: str, keys: List[Tuple[str, Dict[str, Any]]],
                 measures: "collections.OrderedDict[str, Dict[str, Any]]",
                 overrides: List[Tuple[Dict[str, str], Dict[str, Dict[str, Any]]]], path: str = ""):
        self.check_id = check_id
        self.keys = keys
        self.measures = measures
        self.overrides = overrides
        self.path = path

    @property
    def key_names(self) -> List[str]:
        return [k for k, _ in self.keys]

    def rule(self, measure: str, key_texts: Dict[str, str]) -> Dict[str, Any]:
        for when, rules in self.overrides:
            if measure in rules and all(key_texts.get(k) == v for k, v in when.items()):
                return rules[measure]
        return self.measures[measure]


def spec_from_dict(d: Any, check_id: str, where: str = "spec") -> Spec:
    if not isinstance(d, dict):
        raise BadInput("%s must be a JSON object" % where)
    if d.get("check_id") != check_id:
        raise BadInput("%s: check_id is %r but the file is for %s" % (where, d.get("check_id"), check_id))
    raw_keys = d.get("keys")
    if not isinstance(raw_keys, list) or not raw_keys:
        raise BadInput("%s: keys must be a non-empty list of {\"name\", \"kind\"}" % where)
    keys = []
    for i, k in enumerate(raw_keys):
        name = k.get("name") if isinstance(k, dict) else None
        if not isinstance(name, str) or not name.strip():
            raise BadInput("%s: keys[%d] needs a name" % (where, i))
        keys.append((name, _rule(k, "%s: key %r" % (where, name), key=True)))
    raw_measures = d.get("measures")
    if not isinstance(raw_measures, dict) or not raw_measures:
        raise BadInput("%s: measures must be a non-empty object {name: {kind, compare}}" % where)
    measures = collections.OrderedDict()
    for name, r in raw_measures.items():
        measures[name] = _rule(r, "%s: measure %r" % (where, name))
    names = [k for k, _ in keys] + list(measures)
    dupes = sorted(set(n for n in names if [m.casefold() for m in names].count(n.casefold()) > 1))
    if dupes:
        raise BadInput("%s: column name(s) used twice: %s" % (where, ", ".join(dupes)))
    overrides = []
    for i, o in enumerate(d.get("overrides") or []):
        w = "%s: overrides[%d]" % (where, i)
        when = o.get("when") if isinstance(o, dict) else None
        if not isinstance(when, dict) or not when:
            raise BadInput("%s needs a non-empty 'when' {key column: value}" % w)
        for k, v in when.items():
            if k not in dict(keys) or not isinstance(v, str):
                raise BadInput("%s: 'when' may only name key columns with text values, not %r" % (w, k))
        rules = o.get("measures")
        if not isinstance(rules, dict) or not rules:
            raise BadInput("%s needs a non-empty 'measures' object" % w)
        parsed = {}
        for m, r in rules.items():
            if m not in measures:
                raise BadInput("%s: %r is not one of the spec's measures" % (w, m))
            parsed[m] = _rule(r, "%s: measure %r" % (w, m))
        overrides.append((dict(when), parsed))
    return Spec(check_id, keys, measures, overrides, where)


def load_spec(path: str, check_id: str, label: Optional[str] = None) -> Spec:
    label = label or path
    if not os.path.isfile(path):
        raise BadInput("%s not found" % label)
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f, object_pairs_hook=collections.OrderedDict)
    except ValueError as exc:
        raise BadInput("%s is not valid JSON: %s" % (label, exc))
    return spec_from_dict(d, check_id, label)


# --------------------------------------------------------------------------- reading grids

_HEADER = re.compile(r"^(?:'(?:[^']|'')*'|[^\[\]']*)?\[([^\]]+)\]$")


def normalise_header(h: Optional[str]) -> str:
    """'Date'[Year Month] -> Year Month; Borough[Borough] -> Borough; [Requests] -> Requests."""
    h = (h or "").replace("\ufeff", "").strip()
    m = _HEADER.match(h)
    return m.group(1).strip() if m else h


def _read_text(path: str, label: str) -> str:
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError as exc:
        raise BadInput("%s cannot be read: %s" % (label, exc.strerror or exc))
    if data.startswith(codecs.BOM_UTF16_LE) or data.startswith(codecs.BOM_UTF16_BE):
        return data.decode("utf-16")
    if data.startswith(codecs.BOM_UTF8):
        return data[len(codecs.BOM_UTF8):].decode("utf-8", errors="replace")
    if b"\x00" in data[:400]:
        try:
            return data.decode("utf-16-le")
        except UnicodeDecodeError:
            pass
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")


def read_grid(path: str, label: str) -> Tuple[List[str], List[Tuple[int, List[str]]]]:
    """Header names (normalised) and the data rows, each with its line number."""
    text = _read_text(path, label)
    first = next((ln for ln in text.splitlines() if ln.strip()), "")
    if not first:
        raise BadInput("%s is empty: paste the whole result grid, header row included" % label)
    if "\t" in first:
        delim = "\t"
    elif first.count(";") > first.count(","):
        delim = ";"
    else:
        delim = ","
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delim)
    rows = []
    try:
        for r in reader:
            if any(c.strip() for c in r):
                rows.append((reader.line_num, r))
    except csv.Error as exc:
        raise BadInput("%s line %d cannot be read: %s" % (label, reader.line_num, exc))
    header = [normalise_header(h) for h in rows[0][1]]
    named = [h for h in header if h]
    seen = set()
    for h in named:
        if h.casefold() in seen:
            raise BadInput("%s has the column %r twice (after removing table names)" % (label, h))
        seen.add(h.casefold())
    width = len(header)
    out = []
    for line, r in rows[1:]:
        if len(r) > width:
            # A trailing tab or semicolon is harmless; in a comma file an extra field means an
            # unquoted 1,234 has shifted every value after it, even when the spilled cell is empty.
            if delim == "," or any(c.strip() for c in r[width:]):
                hint = (" A number with a thousands separator must be quoted in a comma-separated file"
                        " (\"1,234\"): export again, or paste the grid as tab-separated text."
                        if delim == "," else "")
                raise BadInput("%s line %d has %d fields but the header has %d.%s"
                               % (label, line, len(r), width, hint))
            r = r[:width]
        elif len(r) < width:
            r = r + [""] * (width - len(r))   # a tool that drops trailing empty fields dropped BLANKs
        out.append((line, r))
    return header, out


# --------------------------------------------------------------------------- values

Cell = collections.namedtuple("Cell", "blank ok text number raw")

_EXPECTED_INT = re.compile(r"^-?\d+$")
_EXPECTED_NUM = re.compile(r"^-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?$")
_EXPECTED_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_PLAIN_NUMBER = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$")
_GROUPED_NUMBER = re.compile(r"^[+-]?\d{1,3}(?:,\d{3})+(?:\.\d*)?(?:[eE][+-]?\d+)?$")
_NON_FINITE = {"nan": float("nan"), "infinity": float("inf"), "+infinity": float("inf"),
               "-infinity": float("-inf"), "inf": float("inf"), "+inf": float("inf"),
               "-inf": float("-inf"), "\u221e": float("inf"), "+\u221e": float("inf"),
               "-\u221e": float("-inf")}
_ISO_DATETIME = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})"
                           r"(?:[T ](\d{1,2}):(\d{2})(?::(\d{2})(?:\.\d+)?)?)?Z?$")
_US_DATETIME = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})"
                          r"(?:\s+(\d{1,2}):(\d{2})(?::(\d{2}))?(?:\s*([AaPp])\.?[Mm]\.?)?)?$")
_KIND_WORDS = {"count": "a count", "integer": "a whole number", "hours": "a number of hours",
               "ratio": "a ratio", "average": "a number", "boolean": "TRUE or FALSE",
               "date": "a date", "text": "text"}


def _num_text(n: float) -> str:
    if math.isnan(n):
        return "NaN"
    if math.isinf(n):
        return "Infinity" if n > 0 else "-Infinity"
    if n.is_integer() and abs(n) < 2 ** 53:
        return str(int(n))
    return repr(n)


def _observed_number(s: str) -> Optional[float]:
    t = s
    for ch in ("\xa0", "\u202f", "\u2009"):
        t = t.replace(ch, "")
    pct = t.endswith("%")
    if pct:
        t = t[:-1].rstrip()
    low = t.lower()
    if low in _NON_FINITE:
        return _NON_FINITE[low]
    if "," in t:
        if not _GROUPED_NUMBER.match(t):
            return None                   # 12,5 is not 125: refuse rather than guess
        t = t.replace(",", "")
    if not _PLAIN_NUMBER.match(t):
        return None
    v = float(t)
    return v / 100.0 if pct else v


def _date_text(y: int, mo: int, d: int, h: int = 0, mi: int = 0, se: int = 0) -> Optional[str]:
    try:
        v = _dt.datetime(y, mo, d, h, mi, se)
    except ValueError:
        return None
    return v.date().isoformat() if (h, mi, se) == (0, 0, 0) else v.isoformat()


def _observed_date(s: str) -> Optional[str]:
    m = _ISO_DATETIME.match(s)
    if m:
        y, mo, d, h, mi, se = (int(x) if x else 0 for x in m.groups())
        return _date_text(y, mo, d, h, mi, se)
    m = _US_DATETIME.match(s)
    if m:
        mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        h = int(m.group(4) or 0)
        mi = int(m.group(5) or 0)
        se = int(m.group(6) or 0)
        ampm = (m.group(7) or "").upper()
        if ampm:
            if not 1 <= h <= 12:
                return None
            h = (0 if h == 12 else h) + (12 if ampm == "P" else 0)
        return _date_text(y, mo, d, h, mi, se)
    return None


def parse_observed(kind: str, raw: Optional[str]) -> Cell:
    """Lenient: whatever DAX query view or DAX Studio shows for a value of this kind."""
    s = (raw or "").replace("\ufeff", "").strip()
    low = s.lower()
    if s == "" or low == "(blank)" or (kind != "text" and low == "blank"):
        return Cell(True, True, "", None, raw or "")
    if kind in NUMERIC_KINDS:
        n = _observed_number(s)
        return Cell(False, n is not None, _num_text(n) if n is not None else s, n, raw)
    if kind == "boolean":
        ok = low in ("true", "false")
        return Cell(False, ok, low.upper() if ok else s, None, raw)
    if kind == "date":
        d = _observed_date(s)
        return Cell(False, d is not None, d or s, None, raw)
    return Cell(False, True, s, None, raw)


def parse_expected(kind: str, raw: Optional[str]) -> Cell:
    """Strict: the expected-file format of twin/CONTRACT.md. Raises ValueError otherwise."""
    s = (raw or "").strip()
    if s == "":
        return Cell(True, True, "", None, raw or "")
    if kind in WHOLE_KINDS:
        if not _EXPECTED_INT.match(s):
            raise ValueError("%r is not %s in the expected-file format (digits only)" % (raw, _KIND_WORDS[kind]))
        return Cell(False, True, str(int(s)), float(int(s)), raw)
    if kind in NUMERIC_KINDS:
        if not _EXPECTED_NUM.match(s):
            raise ValueError("%r is not %s in the expected-file format (repr of a float)" % (raw, _KIND_WORDS[kind]))
        n = float(s)
        return Cell(False, True, _num_text(n), n, raw)
    if kind == "boolean":
        if s not in ("TRUE", "FALSE"):
            raise ValueError("%r is not TRUE or FALSE" % raw)
        return Cell(False, True, s, None, raw)
    if kind == "date":
        m = _EXPECTED_DATE.match(s)
        if not m or _date_text(*(int(x) for x in m.groups())) is None:
            raise ValueError("%r is not a YYYY-MM-DD date" % raw)
        return Cell(False, True, s, None, raw)
    return Cell(False, True, s, None, raw)


def _shown(c: Cell) -> str:
    return "BLANK" if c.blank else c.text


def compare_cells(rule: Dict[str, Any], e: Cell, o: Cell) -> Tuple[str, str]:
    """('pass' | 'fail', why). BLANK only ever equals BLANK."""
    if e.blank and o.blank:
        return "pass", ""
    if e.blank:
        if o.ok and o.number == 0:
            return "fail", ("expected BLANK, observed 0: BLANK and 0 are different values "
                            "(SPEC 6), and this measure must return BLANK here")
        return "fail", "expected BLANK, observed %s" % _shown(o)
    if o.blank:
        if e.number == 0:
            return "fail", ("expected 0, observed BLANK: 0 means counted and none (SPEC 6), "
                            "so this measure must return 0 here")
        return "fail", "expected %s, observed BLANK" % e.text
    if not o.ok:
        return "fail", "observed %r is not %s" % (o.raw, _KIND_WORDS[rule["kind"]])
    if rule["kind"] in NUMERIC_KINDS:
        if rule["compare"] == "rel_tol":
            same = math.isclose(o.number, e.number, rel_tol=rule["rel_tol"], abs_tol=0.0)
        else:
            same = o.number == e.number
        if same:
            return "pass", ""
        if rule["compare"] == "rel_tol" and math.isfinite(o.number) and e.number:
            return "fail", "expected %s, observed %s (relative difference %.3g, tolerance %g)" % (
                e.text, o.text, abs(o.number - e.number) / abs(e.number), rule["rel_tol"])
        return "fail", "expected %s, observed %s" % (e.text, o.text)
    if o.text == e.text:
        return "pass", ""
    return "fail", "expected %s, observed %s" % (e.text, o.text)


def _looks_display_rounded(e: Cell, o: Cell) -> bool:
    """True when the observed text is the expected value rounded to a display format."""
    if e.blank or o.blank or not o.ok or e.number is None or o.number is None:
        return False
    t = (o.raw or "").strip().replace(",", "")
    pct = t.endswith("%")
    t = t.rstrip("%").strip()
    if "e" in t.lower() or not _PLAIN_NUMBER.match(t):
        return False
    decimals = len(t.split(".", 1)[1]) if "." in t else 0
    if decimals > 4:
        return False
    shown = float(t)
    want = e.number * 100.0 if pct else e.number
    return round(want, decimals) == round(shown, decimals) and want != shown


# --------------------------------------------------------------------------- one check

def _key_text(names: Sequence[str], values: Sequence[str]) -> str:
    return "; ".join("%s=%s" % (n, v) for n, v in zip(names, values))


def reconcile_check(spec: Spec, expected_path: str, observed_path: str,
                    expected_label: Optional[str] = None,
                    observed_label: Optional[str] = None) -> Dict[str, Any]:
    """Compare one check. Raises BadInput when the files cannot be compared at all."""
    elabel = expected_label or expected_path
    olabel = observed_label or observed_path
    names = spec.key_names
    wanted = names + list(spec.measures)

    eh, erows = read_grid(expected_path, elabel)
    missing = [c for c in wanted if c not in eh]
    if missing:
        raise BadInput("%s has no column(s) %s: the expected file and %s disagree"
                       % (elabel, ", ".join(missing), spec.path))
    unknown = [c for c in eh if c and c not in wanted]
    if unknown:
        raise BadInput("%s has column(s) %s that %s does not compare: add them to the spec"
                       % (elabel, ", ".join(unknown), spec.path))
    eidx = {c: eh.index(c) for c in wanted}
    expected = collections.OrderedDict()
    for line, r in erows:
        try:
            kcells = [parse_expected(rule["kind"], r[eidx[k]]) for k, rule in spec.keys]
        except ValueError as exc:
            raise BadInput("%s line %d, a key column: %s" % (elabel, line, exc))
        kt = tuple(c.text for c in kcells)
        if kt in expected:
            raise BadInput("%s line %d repeats the key %s" % (elabel, line, _key_text(names, kt)))
        key_texts = dict(zip(names, kt))
        cells = {}
        for m in spec.measures:
            rule = spec.rule(m, key_texts)
            try:
                cells[m] = parse_expected(rule["kind"], r[eidx[m]])
            except ValueError as exc:
                raise BadInput("%s line %d, column %r: %s" % (elabel, line, m, exc))
            const = rule.get("constant")
            if const is not None and (cells[m].blank or cells[m].number != const):
                raise BadInput("%s line %d, column %r is %s, but %s fixes it at %d on every row: "
                               "regenerate the expected file" % (elabel, line, m, _shown(cells[m]),
                                                                  spec.path, const))
        expected[kt] = cells

    oh, orows = read_grid(observed_path, olabel)
    by_fold = {}
    for i, h in enumerate(oh):
        if h:
            by_fold.setdefault(h.casefold(), i)
    oidx = {}
    for c in wanted:
        i = oh.index(c) if c in oh else by_fold.get(c.casefold())
        if i is not None:
            oidx[c] = i
    notes = []
    no_key = [k for k in names if k not in oidx]
    if no_key:
        raise BadInput("%s has no key column(s) %s (it has: %s). Paste the whole result grid of %s, "
                       "header row included." % (olabel, ", ".join(no_key),
                                                  ", ".join(h for h in oh if h) or "nothing",
                                                  spec.check_id))
    absent = [m for m in spec.measures if m not in oidx]
    if absent:
        notes.append("%s has no column(s) %s: every cell of them is 'missing'" % (olabel, ", ".join(absent)))
    ignored = [h for h in oh if h and h not in wanted and h.casefold() not in [w.casefold() for w in wanted]]
    if ignored:
        notes.append("%s column(s) not in the spec were ignored: %s" % (olabel, ", ".join(ignored)))

    observed = collections.OrderedDict()
    duplicates = []
    for line, r in orows:
        kcells = [parse_observed(rule["kind"], r[oidx[k]]) for k, rule in spec.keys]
        kt = tuple(c.text for c in kcells)
        cells = {m: r[oidx[m]] for m in spec.measures if m in oidx}
        if kt in observed:
            duplicates.append((kt, cells))
        else:
            observed[kt] = cells

    rows = []
    fails = []
    rounded = 0
    for kt, ecells in expected.items():
        key_texts = dict(zip(names, kt))
        ktext = _key_text(names, kt)
        orow = observed.get(kt)
        for m in spec.measures:
            e = ecells[m]
            rule = spec.rule(m, key_texts)
            if orow is None or m not in orow:
                rows.append([spec.check_id, ktext, m, e.text, "", "missing"])
                continue
            o = parse_observed(rule["kind"], orow[m])
            status, why = compare_cells(rule, e, o)
            rows.append([spec.check_id, ktext, m, e.text, o.text, status])
            if status == "fail":
                fails.append("[%s] %s: %s" % (ktext, m, why))
                if rule["compare"] == "rel_tol" and _looks_display_rounded(e, o):
                    rounded += 1
    extras = [(kt, cells) for kt, cells in observed.items() if kt not in expected] + duplicates
    for kt, cells in extras:
        key_texts = dict(zip(names, kt))
        for m in spec.measures:
            o = parse_observed(spec.rule(m, key_texts)["kind"], cells.get(m, ""))
            rows.append([spec.check_id, _key_text(names, kt), m, "", o.text, "extra"])
    if rounded:
        notes.append("%d failing cell(s) equal the expected value rounded to the displayed decimals: the "
                     "grid was probably copied with format strings applied. Export unformatted values "
                     "(DAX Studio -> Export to CSV) and reconcile again." % rounded)
    missing_keys = [kt for kt in expected if kt not in observed]
    blank_missing = [_key_text(names, kt) for kt in missing_keys
                     if all_blank_row(spec, dict(zip(names, kt)), expected[kt])]
    if blank_missing:
        notes.append("%d missing row(s) have only BLANK measure values in expected, e.g. [%s]. They still "
                     "count: SPEC 9.4 requires them in observed, with their BLANKs. Keep the constant "
                     "\"Check Row\" column in the query (it makes DAX return them) and paste the whole grid."
                     % (len(blank_missing), blank_missing[0]))
    return _result(spec.check_id, rows, fails, notes, expected_rows=len(expected),
                   missing_rows=[_key_text(names, kt) for kt in missing_keys],
                   blank_missing_rows=blank_missing,
                   extra_rows=[_key_text(names, kt) for kt, _ in extras],
                   spec=spec, observed=observed, observed_columns=list(oidx))


def all_blank_row(spec: Spec, key_texts: Dict[str, str], cells: Dict[str, Cell]) -> bool:
    """Every numeric measure of the row is BLANK (constants such as Check Row and the booleans aside)."""
    numeric = [m for m in spec.measures
               if spec.rule(m, key_texts)["kind"] in NUMERIC_KINDS and spec.rule(m, key_texts).get("constant") is None]
    return bool(numeric) and all(cells[m].blank for m in numeric)


def _result(check_id: str, rows: List[List[str]], fails: List[str], notes: List[str], **extra: Any) -> Dict[str, Any]:
    counts = collections.Counter(r[5] for r in rows)
    out = {"check_id": check_id, "rows": rows, "counts": {s: counts.get(s, 0) for s in STATUSES},
           "fails": fails, "notes": notes, "expected_rows": 0, "missing_rows": [], "blank_missing_rows": [],
           "extra_rows": []}
    out.update(extra)
    return out


# --------------------------------------------------------------------------- load rows (L)

def load_manifest(path: str, label: str) -> List[Dict[str, Any]]:
    """The manifest's file entries: name, role (window|carryin), month (window: YYYY-MM), rows."""
    if not os.path.isfile(path):
        raise BadInput("%s not found: the load check (L) compares its rows with C1 and C3" % label)
    try:
        with open(path, encoding="utf-8") as f:
            m = json.load(f)
    except ValueError as exc:
        raise BadInput("%s is not valid JSON: %s" % (label, exc))
    files = m.get("files") if isinstance(m, dict) else None
    if not isinstance(files, list) or not files:
        raise BadInput("%s has no files list" % label)
    out = []
    for i, f in enumerate(files):
        where = "%s files[%d]" % (label, i)
        if not isinstance(f, dict):
            raise BadInput("%s is not an object" % where)
        name, role, rows = f.get("name"), f.get("role"), f.get("rows")
        if not isinstance(name, str) or not name:
            raise BadInput("%s has no name" % where)
        if role not in ("window", "carryin"):
            raise BadInput("%s (%s): role must be window or carryin, not %r" % (where, name, role))
        if isinstance(rows, bool) or not isinstance(rows, int) or rows < 0:
            raise BadInput("%s (%s): rows must be a whole number, not %r" % (where, name, rows))
        month = f.get("month")
        if role == "window" and not (isinstance(month, str) and re.match(r"^\d{4}-\d{2}$", month)):
            raise BadInput("%s (%s): a window file needs month YYYY-MM, not %r" % (where, name, month))
        out.append({"name": name, "role": role, "month": month if role == "window" else None, "rows": rows})
    return out


def _feeds_window_load(res: Dict[str, Any]) -> bool:
    cid, keys, measure, _ = LOAD_WINDOW_SOURCE
    spec = res["spec"]
    return res["check_id"] == cid and all(k in spec.key_names for k in keys) and measure in spec.measures


def _feeds_carryin_load(res: Dict[str, Any]) -> bool:
    cid, measure = LOAD_CARRYIN_SOURCE
    return res["check_id"] == cid and measure in res["spec"].measures


def _observed_sum(values: List[str]) -> Tuple[Optional[float], Optional[str]]:
    """Sum of observed counts (a BLANK adds nothing); (None, raw) at the first value that is no number."""
    total = 0.0
    for raw in values:
        c = parse_observed("count", raw)
        if c.blank:
            continue
        if not c.ok or not math.isfinite(c.number):
            return None, raw
        total += c.number
    return total, None


def _load_row(key: str, measure: str, expected: Optional[int], observed: Optional[float],
              bad_raw: Optional[str], column_absent: bool) -> Tuple[List[str], str]:
    exp_text = "" if expected is None else str(expected)
    if column_absent:
        return [LOAD_CHECK, key, measure, exp_text, "", "missing"], "the observed column is absent"
    if bad_raw is not None:
        return [LOAD_CHECK, key, measure, exp_text, bad_raw, "fail"], "observed %r is not a count" % bad_raw
    obs_text = _num_text(observed)
    if expected is None:
        return [LOAD_CHECK, key, measure, "", obs_text, "extra"], "no manifest file for these rows"
    if observed == expected:
        return [LOAD_CHECK, key, measure, exp_text, obs_text, "pass"], ""
    return [LOAD_CHECK, key, measure, exp_text, obs_text, "fail"], (
        "manifest %s rows, the model loaded %s" % (exp_text, obs_text))


def load_rows(files: List[Dict[str, Any]], c1: Optional[Dict[str, Any]] = None,
              c3: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """SPEC 9.4 load rows: manifest rows per window month (vs C1) and for the carry-in (vs C3)."""
    rows, fails = [], []

    def add(key, measure, expected, observed, bad_raw, absent):
        row, why = _load_row(key, measure, expected, observed, bad_raw, absent)
        rows.append(row)
        if row[5] != "pass":
            fails.append("[%s] %s" % (key, why))

    if c1 is not None:
        _, (ym, tv), measure, current = LOAD_WINDOW_SOURCE
        names = c1["spec"].key_names
        iy, it = names.index(ym), names.index(tv)
        absent = measure not in c1["observed_columns"]
        by_month = collections.OrderedDict()
        for kt, cells in c1["observed"].items():
            if kt[it] == current and kt[iy] != "":
                by_month.setdefault(kt[iy], []).append(cells.get(measure, ""))
        months = collections.OrderedDict()
        for f in files:
            if f["role"] == "window":
                months.setdefault(f["month"], []).append(f)
        for month, fs in months.items():
            total, bad = _observed_sum(by_month.get(month, []))
            add("File=%s; Month=%s" % ("+".join(f["name"] for f in fs), month), _LOAD_MEASURE_WINDOW,
                sum(f["rows"] for f in fs), total, bad, absent)
        for month, values in by_month.items():
            if month not in months:
                total, bad = _observed_sum(values)
                if bad is not None or total:
                    add("File=; Month=%s" % month, _LOAD_MEASURE_WINDOW, None, total, bad, absent)

    if c3 is not None:
        _, measure = LOAD_CARRYIN_SOURCE
        absent = measure not in c3["observed_columns"]
        total, bad = _observed_sum([cells.get(measure, "") for cells in c3["observed"].values()])
        carry = [f for f in files if f["role"] == "carryin"]
        if carry:
            add("File=%s" % "+".join(f["name"] for f in carry), _LOAD_MEASURE_CARRYIN,
                sum(f["rows"] for f in carry), total, bad, absent)
        elif bad is not None or total:
            add("File=", _LOAD_MEASURE_CARRYIN, None, total, bad, absent)

    return _result(LOAD_CHECK, rows, fails, [], expected_rows=len(rows))


# --------------------------------------------------------------------------- the repo

def _check_sort_key(cid: str) -> Tuple[int, str]:
    m = _CHECK_ID.match(cid)
    if m:
        return int(m.group(1)), m.group(2)
    return (10 ** 6, cid)                 # L (load) rows and anything unknown go last


def available_checks(repo: str) -> List[str]:
    d = os.path.join(repo, "checks", "spec")
    if not os.path.isdir(d):
        return []
    found = [m.group(1) for m in (_CHECK_FILE.match(n) for n in os.listdir(d)) if m]
    return sorted(found, key=_check_sort_key)


def default_checks(have: Sequence[str]) -> List[str]:
    """The checks a run without --checks reconciles: every spec except the opt-in ones (C4r)."""
    return [c for c in have if c not in OPT_IN_CHECKS]


def parse_checks(text: Optional[str]) -> Optional[List[str]]:
    """'c1, C5B' -> ['C1', 'C5b']."""
    if text is None:
        return None
    out = []
    for part in text.split(","):
        p = part.strip()
        if not p:
            continue
        m = re.match(r"^[cC]([1-9][0-9]*)([a-zA-Z]?)$", p)
        if not m:
            raise BadInput("--checks takes check ids like C1,C3,C5b, not %r" % p)
        cid = "C%s%s" % (m.group(1), m.group(2).lower())
        if cid not in out:
            out.append(cid)
    if not out:
        raise BadInput("--checks is empty: name at least one check, e.g. --checks C1")
    return out


def _observed_file(repo: str, profile: str, cid: str) -> Tuple[str, str]:
    base = os.path.join("observed", profile, cid)
    found = [base + ext for ext in (".tsv", ".csv") if os.path.isfile(os.path.join(repo, base + ext))]
    if not found:
        raise BadInput("%s.tsv not found (nor %s.csv): paste the %s result grid there, or leave %s "
                       "out with --checks" % (base, base, cid, cid))
    if len(found) > 1:
        raise BadInput("both %s and %s exist: keep only the one you mean" % tuple(found))
    return os.path.join(repo, found[0]), found[0]


def _read_existing(path: str, label: str) -> List[List[str]]:
    if not os.path.exists(path):
        return []
    text = _read_text(path, label)
    rows = list(csv.reader(io.StringIO(text, newline="")))
    if not rows:
        return []
    if rows[0] != RESULT_COLUMNS:
        raise BadInput("%s has an unexpected header %s: move it aside and run again"
                       % (label, ",".join(rows[0])))
    return [r for r in rows[1:] if r]


def _replaced_by(row: List[str], checks: Sequence[str]) -> bool:
    """Does this run replace an existing results row? Its check ran, or it is an L row that check feeds."""
    if row[0] == LOAD_CHECK:
        m = _LOAD_SOURCE.match(row[2] if len(row) > 2 else "")
        return bool(m) and m.group(1) in checks
    return row[0] in checks


def reconcile_repo(repo: str, profile: str, checks: Optional[Sequence[str]] = None,
                   run_at: Optional[str] = None) -> Dict[str, Any]:
    """Reconcile the checks of one profile and write the results file. BadInput writes nothing."""
    if profile not in PROFILES:
        raise BadInput("profile must be dev or full, not %r" % profile)
    repo = os.path.abspath(repo or ".")
    if not os.path.isdir(repo):
        raise BadInput("repo %s is not a folder" % repo)
    have = available_checks(repo)
    if not have:
        raise BadInput("%s has no checks/spec/Cn.json: is --repo the pl300-nyc311 folder?" % repo)
    if checks is None:
        checks = default_checks(have)
        if not checks:
            raise BadInput("checks/spec holds only opt-in checks (%s): name them with --checks"
                           % ", ".join(have))
    else:
        checks = parse_checks(",".join(checks))
    unknown = [c for c in checks if c not in have]
    if unknown:
        raise BadInput("no spec for %s in checks/spec (there are: %s)" % (", ".join(unknown), ", ".join(have)))
    checks = sorted(checks, key=_check_sort_key)
    not_run_opt_in = [c for c in have if c in OPT_IN_CHECKS and c not in checks]
    run_at = run_at or _dt.datetime.now().replace(microsecond=0).isoformat()

    problems, results = [], []
    for cid in checks:
        try:
            spec = load_spec(os.path.join(repo, "checks", "spec", cid + ".json"), cid,
                             os.path.join("checks", "spec", cid + ".json"))
            elabel = os.path.join("expected", profile, cid + ".csv")
            epath = os.path.join(repo, elabel)
            if not os.path.isfile(epath):
                raise BadInput("%s not found: generate it with python -m twin --profile %s" % (elabel, profile))
            opath, olabel = _observed_file(repo, profile, cid)
            results.append(reconcile_check(spec, epath, opath, elabel, olabel))
        except BadInput as exc:
            problems.append("%s: %s" % (cid, exc))

    c1 = next((r for r in results if _feeds_window_load(r)), None)
    c3 = next((r for r in results if _feeds_carryin_load(r)), None)
    for res, fed, what in ((r, c1, "Year Month and Time View keys and a Requests measure") for r in results
                           if r["check_id"] == LOAD_WINDOW_SOURCE[0]):
        if fed is None:
            res["notes"].append("no load rows (L) for the window files: the spec has no %s" % what)
    for res in (r for r in results if r["check_id"] == LOAD_CARRYIN_SOURCE[0]):
        if c3 is None:
            res["notes"].append("no load row (L) for the carry-in file: the spec has no %s measure"
                                % LOAD_CARRYIN_SOURCE[1])
    load = None
    if c1 is not None or c3 is not None:
        mlabel = os.path.join("data", profile, "manifest.json")
        try:
            load = load_rows(load_manifest(os.path.join(repo, mlabel), mlabel), c1, c3)
        except BadInput as exc:
            problems.append("%s: %s" % (LOAD_CHECK, exc))

    out_label = os.path.join("reconcile", profile, "reconciliation_results.csv")
    out_path = os.path.join(repo, out_label)
    try:
        kept = [r for r in _read_existing(out_path, out_label) if not _replaced_by(r, checks)]
    except BadInput as exc:
        problems.append(str(exc))
        kept = []
    if problems:
        raise BadInput("\n".join(problems))

    if load is not None:
        results.append(load)
    new_rows = [r + [run_at] for res in results for r in res["rows"]]
    merged = sorted(kept + new_rows, key=lambda r: _check_sort_key(r[0]))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(RESULT_COLUMNS)
        w.writerows(merged)
    os.replace(tmp, out_path)
    total = collections.Counter(r[5] for r in new_rows)
    passed = all(res["counts"]["pass"] == len(res["rows"]) for res in results)
    return {"repo": repo, "profile": profile, "checks": checks, "run_at": run_at, "results": results,
            "opt_in_not_run": not_run_opt_in,
            "path": out_path, "label": out_label, "kept_rows": len(kept),
            "counts": {s: total.get(s, 0) for s in STATUSES},
            "exit_code": EXIT_PASS if passed else EXIT_FAIL}


# --------------------------------------------------------------------------- CLI

def _print_run(run: Dict[str, Any], limit: int = 10) -> None:
    print("Reconcile %s profile in %s (run_at %s)" % (run["profile"], run["repo"], run["run_at"]))
    for res in run["results"]:
        c = res["counts"]
        n = len(res["rows"])
        if c["pass"] == n:
            print("  %-4s PASS  %d/%d cells  (%d rows)" % (res["check_id"], n, n, res["expected_rows"]))
        else:
            print("  %-4s FAIL  %d/%d cells pass: %d fail, %d missing, %d extra  (%d missing rows, %d extra rows)"
                  % (res["check_id"], c["pass"], n, c["fail"], c["missing"], c["extra"],
                     len(res["missing_rows"]), len(res["extra_rows"])))
        for line in res["fails"][:limit]:
            print("        %s" % line)
        if len(res["fails"]) > limit:
            print("        ... and %d more failing cells" % (len(res["fails"]) - limit))
        for k in res["missing_rows"][:5]:
            print("        missing row [%s]" % k)
        for k in res["extra_rows"][:5]:
            print("        extra row   [%s]" % k)
        for note in res["notes"]:
            print("        note: %s" % note)
    for cid in run.get("opt_in_not_run", []):
        print("  %-4s not run: it is opt-in (the interview drill's check); run it with --checks %s" % (cid, cid))
    c = run["counts"]
    n = sum(c.values())
    print("Wrote %s: %d cells from this run (%s)%s"
          % (run["label"], n, ", ".join(res["check_id"] for res in run["results"]),
             "; kept %d rows of other checks from earlier runs" % run["kept_rows"] if run["kept_rows"] else ""))
    print("%s: %d/%d cells pass" % ("PASS" if run["exit_code"] == EXIT_PASS else "FAIL", c["pass"], n))


def cmd_reconcile(a: argparse.Namespace) -> int:
    run = reconcile_repo(a.repo, a.profile, parse_checks(a.checks))
    _print_run(run)
    return run["exit_code"]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m northledger.pbi",
                                description="Reconcile the owner's Power BI check results with the twin's.")
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("reconcile", help="compare observed/<profile>/Cn with expected/<profile>/Cn (SPEC 9.4)")
    s.add_argument("--repo", default=".", help="the pl300-nyc311 folder (default: the current folder)")
    s.add_argument("--profile", required=True, choices=PROFILES)
    s.add_argument("--checks", help="comma-separated check ids, e.g. C1,C3 or C4r (default: every "
                                    "checks/spec/Cn.json except the opt-in %s)" % ", ".join(OPT_IN_CHECKS))
    s.set_defaults(fn=cmd_reconcile)
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = build_parser()
    try:
        a = p.parse_args(argv)
    except SystemExit as exc:          # argparse has printed its own usage message
        return EXIT_PASS if exc.code in (0, None) else EXIT_BAD
    if not getattr(a, "fn", None):
        p.print_help()
        return EXIT_BAD
    try:
        return a.fn(a)
    except BadInput as exc:
        print("Cannot reconcile:")
        for line in str(exc).splitlines():
            print("  %s" % line)
        print("Nothing was written.")
        return EXIT_BAD
    except Exception as exc:  # noqa: BLE001 - a clear refusal, never a traceback
        print("Stopped: %s (%s). The results file is written in one step, so it is either the "
              "previous one or complete." % (type(exc).__name__, str(exc)[:200]))
        return EXIT_BAD


if __name__ == "__main__":
    sys.exit(main())
