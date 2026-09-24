#!/usr/bin/env python3
"""
python -m northledger.pbi reconcile: the owner's DAX results against the twin's expected values.

SPEC 9.4: counts exact, hours and ratios within a relative 1e-9, BLANK and 0 different,
missing and extra rows reported, a results file page 10 can read, and exit codes a
script can trust (0 pass, 1 any non-pass, 2 bad input, never a traceback).
"""
from __future__ import annotations

import codecs
import csv
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from northledger import pbi as P  # noqa: E402

PL300 = os.environ.get("NL_PL300_REPO") or os.path.join(os.path.dirname(HERE), "pl300-nyc311")


class _Skip(Exception):
    pass


def _ex(kind):
    return {"kind": kind, "compare": "exact"}


def _rel(kind):
    return {"kind": kind, "compare": "rel_tol", "rel_tol": 1e-9}


SPEC_C3 = {"check_id": "C3", "keys": [{"name": "Agency", "kind": "text"}],
           "measures": {"Requests": _ex("count"), "Median Hours": _rel("hours"),
                        "SLA Met % (Benchmark)": _rel("ratio"), "SLA Breach Rate": _rel("ratio"),
                        "Agency Rank": _ex("integer"), "Unmatched Complaint Rows": _ex("count")}}
EXP_C3 = ("Agency,Requests,Median Hours,SLA Met % (Benchmark),SLA Breach Rate,Agency Rank,Unmatched Complaint Rows\n"
          "DOB,1200,30.25,0.75,0.25,2,\n"
          "HPD,500,12.5,,,1,\n"          # no eligible rows: Met % and Breach Rate are BLANK
          "OTI,40,3,0,1,3,\n")           # eligible rows, none met: Met % is 0, not BLANK
PBI_HEADER = ("Agency[Agency]\t[Requests]\t[Median Hours]\t[SLA Met % (Benchmark)]\t[SLA Breach Rate]"
              "\t[Agency Rank]\t[Unmatched Complaint Rows]\n")
OBS_C3 = PBI_HEADER + ("DOB\t1,200\t30.25\t75.0%\t25%\t2\t\n"
                       "HPD\t500\t12.5\t\t(Blank)\t1\t\n"
                       "OTI\t40\t3\t0\t1\t3\t\n")

SPEC_C1 = {"check_id": "C1",
           "keys": [{"name": "Fiscal Year", "kind": "text"}, {"name": "Year Month", "kind": "text"},
                    {"name": "Borough", "kind": "text"}, {"name": "Time View", "kind": "text"}],
           "measures": {"Is FY Total": _ex("boolean"), "Is Month Total": _ex("boolean"),
                        "Check Row": dict(_ex("count"), constant=1),
                        "Requests": _ex("count"), "Requests (Daily)": _ex("count")},
           "overrides": [{"when": {"Time View": "YoY %"},
                          "measures": {"Requests": _rel("ratio"), "Requests (Daily)": _rel("ratio")}}]}
# SPEC 9.2 round 4: four Time Views, the constant Check Row, and rows whose measures are all BLANK.
EXP_C1 = ("Fiscal Year,Year Month,Borough,Time View,Is FY Total,Is Month Total,Check Row,Requests,Requests (Daily)\n"
          ",,BRONX,Current,TRUE,TRUE,1,2000,2000\n"
          ",,BRONX,FYTD,TRUE,TRUE,1,1000,\n"                      # FY2027 to date; Daily is off the whitelist
          ",,BRONX,PY,TRUE,TRUE,1,,\n"                           # completeness guard: all BLANK
          "FY2027,,BRONX,Current,FALSE,TRUE,1,2000,2000\n"
          "FY2027,,BRONX,YoY %,FALSE,TRUE,1,,\n"                 # all BLANK
          "FY2027,2026-08,BRONX,Current,FALSE,FALSE,1,1000,1000\n"
          "FY2027,2026-08,BRONX,FYTD,FALSE,FALSE,1,2000,\n"
          "FY2027,2026-08,BRONX,PY,FALSE,FALSE,1,950,\n"         # Requests (Daily) is off the whitelist
          "FY2027,2026-08,BRONX,YoY %,FALSE,FALSE,1,0.05263157894736842,\n"
          "FY2027,2026-08,QUEENS,Current,FALSE,FALSE,1,500,500\n"
          "FY2027,2026-09,BRONX,Current,FALSE,FALSE,1,,\n"       # after the window: all BLANK
          "FY2027,2026-09,BRONX,FYTD,FALSE,FALSE,1,,\n")         # the FYTD cap: all BLANK
C1_HEADER = ("'Date'[Fiscal Year]\t'Date'[Year Month]\tBorough[Borough]\t'Time Calc'[Time View]\t[Is FY Total]"
             "\t[Is Month Total]\t[Check Row]\t[Requests]\t[Requests (Daily)]\n")
OBS_C1_ROWS = ["\t\tBRONX\tCurrent\tTrue\tTrue\t1\t2,000\t2000",
               "\t\tBRONX\tFYTD\tTrue\tTrue\t1\t1000\t",
               "\t\tBRONX\tPY\tTrue\tTrue\t1\t\t",
               "FY2027\t\tBRONX\tCurrent\tFalse\tTrue\t1\t2000\t2000",
               "FY2027\t\tBRONX\tYoY %\tFalse\tTrue\t1\t\t",
               "FY2027\t2026-08\tBRONX\tCurrent\tFalse\tFalse\t1\t1,000\t1000",
               "FY2027\t2026-08\tBRONX\tFYTD\tFalse\tFalse\t1\t2000\t",
               "FY2027\t2026-08\tBRONX\tPY\tFalse\tFalse\t1\t950\t",
               "FY2027\t2026-08\tBRONX\tYoY %\tFalse\tFalse\t1\t" + repr(0.05263157894736842 * (1 + 3e-10)) + "\t",
               "FY2027\t2026-08\tQUEENS\tCurrent\tFalse\tFalse\t1\t500\t500",
               "FY2027\t2026-09\tBRONX\tCurrent\tFalse\tFalse\t1\t\t",
               "FY2027\t2026-09\tBRONX\tFYTD\tFalse\tFalse\t1\t\t"]
OBS_C1 = C1_HEADER + "\n".join(OBS_C1_ROWS) + "\n"
C1_CELLS = 12 * 5
C1_GUARD_KEY = "Fiscal Year=; Year Month=; Borough=BRONX; Time View=PY"
C1_GUARD_ROW = "\t\tBRONX\tPY\tTrue\tTrue\t1\t\t"


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(content if isinstance(content, bytes) else content.encode("utf-8"))


def _check(spec, expected, observed, name="obs.tsv"):
    root = tempfile.mkdtemp(prefix="nl_pbi_chk_")
    e, o = os.path.join(root, "expected.csv"), os.path.join(root, name)
    _write(e, expected)
    _write(o, observed)
    return P.reconcile_check(P.spec_from_dict(spec, spec["check_id"]), e, o)


def _cells(res):
    return {(r[1], r[2]): r[5] for r in res["rows"]}


def _bad(fn, *args, **kw):
    try:
        fn(*args, **kw)
    except P.BadInput as exc:
        return str(exc)
    raise AssertionError("expected BadInput from %s" % fn.__name__)


def _repo(specs, expected, observed, profile="dev"):
    root = tempfile.mkdtemp(prefix="nl_pbi_repo_")
    for cid, spec in specs.items():
        _write(os.path.join(root, "checks", "spec", cid + ".json"), json.dumps(spec))
    for cid, text in expected.items():
        _write(os.path.join(root, "expected", profile, cid + ".csv"), text)
    for name, text in observed.items():
        _write(os.path.join(root, "observed", profile, name), text)
    return root


def _results(root, profile="dev"):
    with open(os.path.join(root, "reconcile", profile, "reconciliation_results.csv"), encoding="utf-8") as f:
        return list(csv.reader(f))


def _cli(*args):
    env = dict(os.environ, PYTHONWARNINGS="ignore", PYTHONPATH=HERE)
    p = subprocess.run([sys.executable, "-m", "northledger.pbi"] + list(args), cwd=HERE, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    return p.returncode, p.stdout


# --------------------------------------------------------------------------- BLANK vs 0

def test_blank_and_zero_are_different_values_both_ways():
    obs = PBI_HEADER + ("DOB\t1200\t30.25\t0.75\t0.25\t2\t0\n"      # Unmatched: BLANK expected, 0 observed
                        "HPD\t500\t12.5\t0\t\t1\t\n"                 # Met %: BLANK expected, 0 observed
                        "OTI\t40\t3\t\t1\t3\t\n")                    # Met %: 0 expected, BLANK observed
    res = _check(SPEC_C3, EXP_C3, obs)
    c = _cells(res)
    assert c[("Agency=DOB", "Unmatched Complaint Rows")] == "fail", c
    assert c[("Agency=HPD", "SLA Met % (Benchmark)")] == "fail", c
    assert c[("Agency=OTI", "SLA Met % (Benchmark)")] == "fail", c
    assert c[("Agency=HPD", "SLA Breach Rate")] == "pass", c            # BLANK = BLANK
    assert res["counts"]["fail"] == 3, res["counts"]
    whys = " | ".join(res["fails"])
    assert "expected BLANK, observed 0" in whys and "expected 0, observed BLANK" in whys, whys
    row = [r for r in res["rows"] if r[1] == "Agency=HPD" and r[2] == "SLA Met % (Benchmark)"][0]
    assert row[3] == "" and row[4] == "0", row                           # BLANK is written as an empty field


def test_blank_tokens_all_mean_blank_and_never_zero():
    for raw in ("", "   ", "(Blank)", "(blank)", "BLANK"):
        c = P.parse_observed("ratio", raw)
        assert c.blank and c.number is None, (raw, c)
    assert not P.parse_observed("count", "0").blank
    assert P.parse_observed("text", "BLANK").text == "BLANK"             # a text value, not a BLANK marker
    status, _ = P.compare_cells(P._rule(_ex("count"), "t"), P.parse_expected("count", ""),
                                P.parse_observed("count", "0"))
    assert status == "fail"


# --------------------------------------------------------------------------- numbers

def test_power_bi_headers_and_display_formats_pass():
    res = _check(SPEC_C3, EXP_C3, OBS_C3)
    assert res["counts"] == {"pass": 18, "fail": 0, "missing": 0, "extra": 0}, (res["counts"], res["fails"])
    row = [r for r in res["rows"] if r[1] == "Agency=DOB" and r[2] == "SLA Met % (Benchmark)"][0]
    assert row[4] == "0.75", row                                         # 75.0% is written as 0.75


def test_counts_are_exact():
    def one(value):
        obs = PBI_HEADER + ("DOB\t%s\t30.25\t0.75\t0.25\t2\t\nHPD\t500\t12.5\t\t\t1\t\nOTI\t40\t3\t0\t1\t3\t\n" % value)
        return _cells(_check(SPEC_C3, EXP_C3, obs))[("Agency=DOB", "Requests")]
    assert one("1,200") == "pass" and one("1200.0") == "pass" and one("1200") == "pass"
    assert one("1201") == "fail" and one("1200.5") == "fail" and one("1199.9999999") == "fail"


def test_relative_tolerance_edges():
    def one(value):
        obs = PBI_HEADER + ("DOB\t1200\t%s\t0.75\t0.25\t2\t\nHPD\t500\t12.5\t\t\t1\t\nOTI\t40\t3\t0\t1\t3\t\n" % value)
        res = _check(SPEC_C3, EXP_C3, obs)
        return _cells(res)[("Agency=DOB", "Median Hours")], res
    assert one(repr(30.25))[0] == "pass"
    assert one(repr(30.25 * (1 + 5e-10)))[0] == "pass"                  # inside 1e-9
    assert one(repr(30.25 * (1 - 5e-10)))[0] == "pass"
    status, res = one(repr(30.25 * (1 + 2e-9)))                          # outside 1e-9
    assert status == "fail" and "relative difference" in res["fails"][0], res["fails"]
    assert one(repr(30.25 * (1 - 2e-9)))[0] == "fail"
    assert one("30.3")[0] == "fail"
    # a ratio of exactly 0 has no relative room: 1e-15 is not 0
    obs = PBI_HEADER + "DOB\t1200\t30.25\t0.75\t0.25\t2\t\nHPD\t500\t12.5\t\t\t1\t\nOTI\t40\t3\t1e-15\t1\t3\t\n"
    assert _cells(_check(SPEC_C3, EXP_C3, obs))[("Agency=OTI", "SLA Met % (Benchmark)")] == "fail"
    obs = PBI_HEADER + "DOB\t1200\t30.25\t0.75\t0.25\t2\t\nHPD\t500\t12.5\t\t\t1\t\nOTI\t40\t3\t0.0%\t100%\t3\t\n"
    assert _check(SPEC_C3, EXP_C3, obs)["counts"]["fail"] == 0


def test_display_rounded_values_fail_with_a_hint():
    exp = EXP_C3.replace("DOB,1200,30.25,0.75", "DOB,1200,30.25,0.7512345678")
    obs = OBS_C3.replace("75.0%", "75.1%")
    res = _check(SPEC_C3, exp, obs)
    assert _cells(res)[("Agency=DOB", "SLA Met % (Benchmark)")] == "fail"
    assert any("format strings" in n for n in res["notes"]), res["notes"]


def test_a_decimal_comma_is_refused_not_read_as_a_bigger_number():
    assert P.parse_observed("hours", "30,25").ok is False
    assert P.parse_observed("count", "1,200").number == 1200.0
    assert P.parse_observed("count", "1,200,300").number == 1200300.0
    assert P.parse_observed("ratio", "+3.1%").number == 3.1 / 100.0
    obs = OBS_C3.replace("DOB\t1,200\t30.25", "DOB\t1,200\t30,25")
    res = _check(SPEC_C3, EXP_C3, obs)
    assert _cells(res)[("Agency=DOB", "Median Hours")] == "fail"
    assert "is not a number of hours" in res["fails"][0], res["fails"]


def test_non_finite_observed_values_fail():
    for raw in ("NaN", "Infinity", "-Infinity", "\u221e"):
        obs = OBS_C3.replace("DOB\t1,200\t30.25", "DOB\t1,200\t%s" % raw)
        assert _cells(_check(SPEC_C3, EXP_C3, obs))[("Agency=DOB", "Median Hours")] == "fail", raw


# --------------------------------------------------------------------------- rows

def test_missing_extra_and_duplicate_rows_are_reported_per_cell():
    obs = PBI_HEADER + ("DOB\t1200\t30.25\t0.75\t0.25\t2\t\n"
                        "OTI\t40\t3\t0\t1\t3\t\n"
                        "DOT\t7\t1\t1\t0\t4\t\n"                   # not expected
                        "DOB\t1200\t30.25\t0.75\t0.25\t2\t\n"      # pasted twice
                        "\tt\t\t\t\t\t\n")                          # a blank Agency member
    res = _check(SPEC_C3, EXP_C3, obs)
    c = _cells(res)
    assert all(c[("Agency=HPD", m)] == "missing" for m in SPEC_C3["measures"]), c
    assert res["missing_rows"] == ["Agency=HPD"], res["missing_rows"]
    assert sorted(res["extra_rows"]) == ["Agency=", "Agency=DOB", "Agency=DOT"], res["extra_rows"]
    assert res["counts"] == {"pass": 12, "fail": 0, "missing": 6, "extra": 18}, res["counts"]
    extra = [r for r in res["rows"] if r[1] == "Agency=DOT" and r[2] == "Requests"][0]
    assert extra[3:6] == ["", "7", "extra"], extra
    missing = [r for r in res["rows"] if r[1] == "Agency=HPD" and r[2] == "Requests"][0]
    assert missing[3:6] == ["500", "", "missing"], missing


def test_a_missing_measure_column_marks_its_cells_missing_and_a_missing_key_is_bad_input():
    obs = "Agency[Agency]\t[Requests]\nDOB\t1200\nHPD\t500\nOTI\t40\n"
    res = _check(SPEC_C3, EXP_C3, obs)
    assert res["counts"] == {"pass": 3, "fail": 0, "missing": 15, "extra": 0}, res["counts"]
    assert any("Median Hours" in n for n in res["notes"]), res["notes"]
    msg = _bad(_check, SPEC_C3, EXP_C3, "[Requests]\t[Median Hours]\n1200\t30.25\n")
    assert "no key column(s) Agency" in msg, msg


def test_short_rows_are_padded_because_only_blanks_can_be_dropped():
    obs = PBI_HEADER + "DOB\t1200\t30.25\t0.75\t0.25\t2\nHPD\t500\t12.5\t\t\t1\nOTI\t40\t3\t0\t1\t3\n"
    assert _check(SPEC_C3, EXP_C3, obs)["counts"]["fail"] == 0


# --------------------------------------------------------------------------- headers, files

def test_header_normalisation():
    n = P.normalise_header
    assert n("'Date'[Year Month]") == "Year Month"
    assert n("Date[Year Month]") == "Year Month"
    assert n("\ufeff'Time Calc'[Time View]") == "Time View"
    assert n("[Requests (Smart)]") == "Requests (Smart)"
    assert n("[SLA Met % (Benchmark)]") == "SLA Met % (Benchmark)"
    assert n("'It''s'[X]") == "X"
    assert n("  Agency  ") == "Agency"
    obs = OBS_C3.replace("Agency[Agency]", "agency[AGENCY]").replace("[Median Hours]", "[median hours]")
    assert _check(SPEC_C3, EXP_C3, obs)["counts"]["fail"] == 0            # DAX names are case-insensitive
    dup = OBS_C3.replace("[Requests]", "Agency[Agency]")
    assert "twice" in _bad(_check, SPEC_C3, EXP_C3, dup)


def test_tab_comma_semicolon_utf8_bom_and_utf16_files_all_read():
    comma = ("Agency,Requests,Median Hours,SLA Met % (Benchmark),SLA Breach Rate,Agency Rank,Unmatched Complaint Rows\n"
             "DOB,\"1,200\",30.25,75%,0.25,2,\nHPD,500,12.5,,,1,\nOTI,40,3,0,1,3,\n")
    semi = comma.replace(",", ";").replace("\"1;200\"", "1200")
    for name, content in (("a.csv", comma), ("b.csv", semi), ("c.tsv", codecs.BOM_UTF8 + OBS_C3.encode("utf-8")),
                          ("d.tsv", OBS_C3.encode("utf-16")), ("e.tsv", OBS_C3.replace("\n", "\r\n"))):
        res = _check(SPEC_C3, EXP_C3, content, name)
        assert res["counts"]["pass"] == 18 and res["counts"]["fail"] == 0, (name, res["counts"], res["fails"])


def test_an_unquoted_thousands_separator_in_a_comma_file_is_bad_input():
    bad = ("Agency,Requests,Median Hours,SLA Met % (Benchmark),SLA Breach Rate,Agency Rank,Unmatched Complaint Rows\n"
           "DOB,1,200,30.25,0.75,0.25,2,\n")
    msg = _bad(_check, SPEC_C3, EXP_C3, bad, "a.csv")
    assert "line 2" in msg and "quoted" in msg, msg


def test_the_expected_file_must_follow_the_contract_format():
    for bad, what in ((EXP_C3.replace("DOB,1200", "DOB,\"1,200\""), "count"),
                      (EXP_C3.replace(",0.75,", ",75%,"), "ratio"),
                      (EXP_C3 + "DOB,1,1,1,0,1,\n", "repeats the key"),
                      (EXP_C3.replace("Unmatched Complaint Rows\n", "Unmatched Complaint Rows,Extra\n"), "does not compare")):
        msg = _bad(_check, SPEC_C3, bad, OBS_C3)
        assert what in msg, (what, msg)
    spec = {"check_id": "C5", "keys": [{"name": "Unique Key", "kind": "integer"}],
            "measures": {"Closed Valid": _ex("boolean"), "Closed Date": _ex("date")}}
    assert "TRUE or FALSE" in _bad(_check, spec, "Unique Key,Closed Valid,Closed Date\n1,True,2026-08-01\n",
                                   "Unique Key\tClosed Valid\tClosed Date\n1\tTrue\t2026-08-01\n")
    assert "YYYY-MM-DD" in _bad(_check, spec, "Unique Key,Closed Valid,Closed Date\n1,TRUE,8/1/2026\n",
                                "Unique Key\tClosed Valid\tClosed Date\n1\tTrue\t2026-08-01\n")


# --------------------------------------------------------------------------- booleans, dates, C1 shape

def test_booleans_and_us_style_dates():
    spec = {"check_id": "C5", "keys": [{"name": "Unique Key", "kind": "integer"}],
            "measures": {"Created Date": _ex("date"), "Closed Valid": _ex("boolean"),
                         "Breach Flag": _ex("integer"), "R03": _ex("text")}}
    exp = ("Unique Key,Created Date,Closed Valid,Breach Flag,R03\n"
           "66012345,2026-08-31,TRUE,0,\n"
           "66012346,2026-08-01,FALSE,,after_as_of\n"
           "66012347,2026-08-15,true_is_not_allowed_here,1,\n")
    assert "TRUE or FALSE" in _bad(_check, spec, exp, "x")
    exp = exp.replace("true_is_not_allowed_here", "FALSE")
    obs = ("[Unique Key]\t[Created Date]\t[Closed Valid]\t[Breach Flag]\t[R03]\n"
           "66,012,345\t8/31/2026 12:00:00 AM\tTrue\t0\t\n"
           "66012346\t2026-08-01T00:00:00\tfalse\t\tafter_as_of\n"
           "66012347\t8/15/2026\tFALSE\t1\t\n")
    res = _check(spec, exp, obs)
    assert res["counts"]["pass"] == 12 and res["counts"]["fail"] == 0, (res["counts"], res["fails"])
    obs2 = obs.replace("8/31/2026 12:00:00 AM", "8/31/2026 12:00:00 PM").replace("\tfalse\t", "\tno\t")
    c = _cells(_check(spec, exp, obs2))
    assert c[("Unique Key=66012345", "Created Date")] == "fail", c        # noon is not the date
    assert c[("Unique Key=66012346", "Closed Valid")] == "fail", c
    obs3 = obs.replace("66012346\t2026-08-01T00:00:00\tfalse\t\t", "66012346\t2026-08-01T00:00:00\tfalse\t0\t")
    assert _cells(_check(spec, exp, obs3))[("Unique Key=66012346", "Breach Flag")] == "fail"   # BLANK is not 0


def test_date_parser_edges():
    d = lambda s: P.parse_observed("date", s)  # noqa: E731
    assert d("12/31/2025 12:00:00 AM").text == "2025-12-31"
    assert d("1/2/2026 1:05:09 PM").text == "2026-01-02T13:05:09"
    assert d("2026-08-31 00:00:00").text == "2026-08-31"
    assert d("2026-08-31T00:00:00.000").text == "2026-08-31"
    assert not d("2/30/2026").ok and not d("31/08/2026").ok and not d("8/31/2026 13:00:00 PM").ok
    assert d("8/31/2026 13:00:00").text == "2026-08-31T13:00:00"


def test_c1_yoy_rows_compare_as_ratios_and_totals_as_booleans():
    obs = OBS_C1
    res = _check(SPEC_C1, EXP_C1, obs)
    assert res["counts"] == {"pass": C1_CELLS, "fail": 0, "missing": 0, "extra": 0}, (res["counts"], res["fails"])
    # the YoY % ratio also reads as a percentage
    pct = obs.replace(repr(0.05263157894736842 * (1 + 3e-10)), "5.263157894736842%")
    assert _check(SPEC_C1, EXP_C1, pct)["counts"]["fail"] == 0
    # the whitelist: Requests (Daily) must be BLANK under PY and FYTD, not the unchanged count
    wl = obs.replace("BRONX\tPY\tFalse\tFalse\t1\t950\t", "BRONX\tPY\tFalse\tFalse\t1\t950\t950").replace(
        "BRONX\tFYTD\tFalse\tFalse\t1\t2000\t", "BRONX\tFYTD\tFalse\tFalse\t1\t2000\t2000")
    res = _check(SPEC_C1, EXP_C1, wl)
    c = _cells(res)
    assert c[("Fiscal Year=FY2027; Year Month=2026-08; Borough=BRONX; Time View=PY", "Requests (Daily)")] == "fail"
    assert c[("Fiscal Year=FY2027; Year Month=2026-08; Borough=BRONX; Time View=FYTD", "Requests (Daily)")] == "fail"
    assert res["counts"]["fail"] == 2, res["fails"]
    # FYTD is a count: the 3e-10 slip that passes on the YoY % ratio fails there, as on Current
    for view, good, slipped in (("Current", "1,000", "1000.0000003"), ("FYTD", "2000", "2000.0000006")):
        row = "2026-08\tBRONX\t%s\tFalse\tFalse\t1\t" % view
        assert row + good in obs, view
        c = _cells(_check(SPEC_C1, EXP_C1, obs.replace(row + good, row + slipped)))
        assert c[("Fiscal Year=FY2027; Year Month=2026-08; Borough=BRONX; Time View=%s" % view, "Requests")] == "fail", view
    # 0 where the completeness guard or the FYTD cap wants BLANK, and a wrong subtotal flag
    bad = obs.replace("YoY %\tFalse\tTrue\t1\t\t", "YoY %\tFalse\tTrue\t1\t0\t").replace(
        "2026-09\tBRONX\tFYTD\tFalse\tFalse\t1\t\t", "2026-09\tBRONX\tFYTD\tFalse\tFalse\t1\t0\t").replace(
        "\t\tBRONX\tCurrent\tTrue\tTrue", "\t\tBRONX\tCurrent\tFalse\tTrue")
    res = _check(SPEC_C1, EXP_C1, bad)
    c = _cells(res)
    assert c[("Fiscal Year=FY2027; Year Month=; Borough=BRONX; Time View=YoY %", "Requests")] == "fail", c
    assert c[("Fiscal Year=FY2027; Year Month=2026-09; Borough=BRONX; Time View=FYTD", "Requests")] == "fail", c
    assert c[("Fiscal Year=; Year Month=; Borough=BRONX; Time View=Current", "Is FY Total")] == "fail", c
    assert res["counts"]["fail"] == 3 and sum("expected BLANK, observed 0" in f for f in res["fails"]) == 2, res["fails"]


# --------------------------------------------------------------------------- all-BLANK rows, Check Row

def test_an_all_blank_expected_row_absent_from_observed_is_missing_and_fails():
    # present with its BLANKs: compared cell by cell and passes
    res = _check(SPEC_C1, EXP_C1, OBS_C1)
    assert all(_cells(res)[(C1_GUARD_KEY, m)] == "pass" for m in SPEC_C1["measures"]), _cells(res)
    # absent: every cell of it is 'missing', and nothing else changes
    assert C1_GUARD_ROW in OBS_C1_ROWS
    obs = C1_HEADER + "\n".join(r for r in OBS_C1_ROWS if r != C1_GUARD_ROW) + "\n"
    res = _check(SPEC_C1, EXP_C1, obs)
    c = _cells(res)
    assert [c.get((C1_GUARD_KEY, m)) for m in SPEC_C1["measures"]] == ["missing"] * 5, res["counts"]
    assert res["counts"] == {"pass": C1_CELLS - 5, "fail": 0, "missing": 5, "extra": 0}, res["counts"]
    assert res["missing_rows"] == [C1_GUARD_KEY] and res["blank_missing_rows"] == [C1_GUARD_KEY], res
    assert any("only BLANK measure values" in n and "Check Row" in n for n in res["notes"]), res["notes"]
    # the same through the CLI: a fail (exit 1), the missing cells in the results file
    root = _repo({"C1": SPEC_C1}, {"C1": EXP_C1}, {"C1.tsv": obs})
    _manifest(root, [_mfile("w_2026-08.csv.gz", "window", 1500, "2026-08")])
    code, out = _cli("reconcile", "--repo", root, "--profile", "dev")
    assert code == 1 and "C1   FAIL" in out and "missing row [%s]" % C1_GUARD_KEY in out, (code, out)
    rows = _results(root)[1:]
    assert sorted(r[2] for r in rows if r[5] == "missing") == sorted(SPEC_C1["measures"]), rows
    assert {r[1] for r in rows if r[5] == "missing"} == {C1_GUARD_KEY}
    assert [r[5] for r in rows if r[0] == "L"] == ["pass"], [r for r in rows if r[0] == "L"]
    assert all(r[5] == "pass" for r in rows if r[5] != "missing"), [r for r in rows if r[5] not in ("pass", "missing")]
    # a row that is missing but not all-BLANK is 'missing' too, without the Check Row note
    obs = C1_HEADER + "\n".join(r for r in OBS_C1_ROWS if not r.startswith("FY2027\t2026-08\tQUEENS")) + "\n"
    res = _check(SPEC_C1, EXP_C1, obs)
    assert res["counts"]["missing"] == 5 and res["blank_missing_rows"] == [], res
    assert P.all_blank_row(P.spec_from_dict(SPEC_C1, "C1"), {"Time View": "PY"},
                           {m: P.parse_expected("count", "") for m in SPEC_C1["measures"]})


def test_check_row_is_a_constant_the_expected_file_must_hold():
    spec = P.spec_from_dict(SPEC_C1, "C1")
    assert spec.measures["Check Row"]["constant"] == 1 and spec.measures["Requests"]["constant"] is None
    for bad in ("2", ""):
        exp = EXP_C1.replace("FY2027,,BRONX,Current,FALSE,TRUE,1,", "FY2027,,BRONX,Current,FALSE,TRUE,%s," % bad)
        msg = _bad(_check, SPEC_C1, exp, OBS_C1)
        assert "fixes it at 1 on every row" in msg and "line 5" in msg, msg
    # observed: a Check Row that is not 1, or BLANK, fails like any other cell
    obs = OBS_C1.replace("FY2027\t\tBRONX\tCurrent\tFalse\tTrue\t1\t", "FY2027\t\tBRONX\tCurrent\tFalse\tTrue\t\t")
    c = _cells(_check(SPEC_C1, EXP_C1, obs))
    assert c[("Fiscal Year=FY2027; Year Month=; Borough=BRONX; Time View=Current", "Check Row")] == "fail"
    for rule, what in (({"kind": "ratio", "compare": "exact", "constant": 1}, "only for an exact count"),
                       ({"kind": "count", "compare": "exact", "constant": "1"}, "whole number"),
                       ({"kind": "count", "compare": "exact", "constant": True}, "whole number"),
                       ({"kind": "count", "compare": "rel_tol", "rel_tol": 1e-9, "constant": 1}, "only for an exact")):
        s = json.loads(json.dumps(SPEC_C1))
        s["measures"]["Check Row"] = rule
        assert what in _bad(P.spec_from_dict, s, "C1"), (rule, what)
    s = json.loads(json.dumps(SPEC_C1))
    s["keys"][0]["constant"] = 1
    assert "only for an exact count" in _bad(P.spec_from_dict, s, "C1")


# --------------------------------------------------------------------------- C4r is opt-in

SPEC_C4 = {"check_id": "C4", "keys": [{"name": "Date", "kind": "date"}, {"name": "Borough", "kind": "text"}],
           "measures": {"Check Row": dict(_ex("count"), constant=1), "Open Backlog EOP": _ex("count"),
                        "Open Backlog EOP (Fast)": _ex("count"), "EOP PHONE": _ex("count"),
                        "EOP (Fast) PHONE": _ex("count")}}
EXP_C4 = ("Date,Borough,Check Row,Open Backlog EOP,Open Backlog EOP (Fast),EOP PHONE,EOP (Fast) PHONE\n"
          "2024-08-31,BRONX,1,,,,\n"                  # before the window: BLANK
          "2026-08-31,BRONX,1,120,120,40,40\n"
          "2026-08-31,UNKNOWN,1,0,0,0,0\n"            # inside the window a stock is 0, not BLANK
          "2026-09-30,BRONX,1,,,,\n")                 # after the last data date: BLANK
OBS_C4 = ("'Date'[Date]\tBorough[Borough]\t[Check Row]\t[Open Backlog EOP]\t[Open Backlog EOP (Fast)]\t[EOP PHONE]"
          "\t[EOP (Fast) PHONE]\n"
          "8/31/2024 12:00:00 AM\tBRONX\t1\t\t\t\t\n"
          "8/31/2026 12:00:00 AM\tBRONX\t1\t120\t120\t40\t40\n"
          "8/31/2026 12:00:00 AM\tUNKNOWN\t1\t0\t0\t0\t0\n"
          "9/30/2026 12:00:00 AM\tBRONX\t1\t\t\t\t\n")
SPEC_C4R = {"check_id": "C4r", "keys": SPEC_C4["keys"],
            "measures": {m: r for m, r in SPEC_C4["measures"].items() if "Fast" not in m}}
EXP_C4R = "".join(",".join(v for i, v in enumerate(line.split(",")) if i not in (4, 6)) + "\n"
                  for line in EXP_C4.strip().split("\n"))
OBS_C4R = "".join("\t".join(v for i, v in enumerate(line.split("\t")) if i not in (4, 6)) + "\n"
                  for line in OBS_C4.strip().split("\n"))


def test_c4r_is_opt_in_and_runs_only_when_named():
    assert P.OPT_IN_CHECKS == ("C4r",)
    assert P.default_checks(["C1", "C2", "C3", "C4", "C4r", "C5", "C5b"]) == ["C1", "C2", "C3", "C4", "C5", "C5b"]
    assert P.parse_checks("c4R") == ["C4r"] and P.parse_checks("C4, C4r") == ["C4", "C4r"]
    assert _check(SPEC_C4R, EXP_C4R, OBS_C4R)["counts"] == {"pass": 12, "fail": 0, "missing": 0, "extra": 0}
    # the default run skips C4r, so a missing observed/dev/C4r.tsv is no problem, and says how to run it
    root = _repo({"C3": SPEC_C3, "C4": SPEC_C4, "C4r": SPEC_C4R}, {"C3": EXP_C3, "C4": EXP_C4, "C4r": EXP_C4R},
                 {"C3.tsv": OBS_C3, "C4.tsv": OBS_C4})
    run = P.reconcile_repo(root, "dev", run_at="2026-09-22T09:00:00")
    assert run["checks"] == ["C3", "C4"] and run["exit_code"] == 0 and run["opt_in_not_run"] == ["C4r"], run["checks"]
    code, out = _cli("reconcile", "--repo", root, "--profile", "dev")
    assert code == 0 and re.search(r"C4r +not run: it is opt-in", out) and "--checks C4r" in out, out
    assert {r[0] for r in _results(root)[1:]} == {"C3", "C4"}
    before = {tuple(r) for r in _results(root)[1:]}
    # named, it runs, and it needs its observed file like any other check
    code, out = _cli("reconcile", "--repo", root, "--profile", "dev", "--checks", "C4r")
    assert code == 2 and "C4r.tsv not found" in out and "Traceback" not in out, out
    _write(os.path.join(root, "observed", "dev", "C4r.tsv"), OBS_C4R)
    run = P.reconcile_repo(root, "dev", ["c4R"], run_at="2026-09-22T10:00:00")
    assert run["checks"] == ["C4r"] and run["exit_code"] == 0 and run["opt_in_not_run"] == [], run
    rows = _results(root)[1:]
    assert [r[0] for r in rows].count("C4r") == 4 * 3 and all(r[5] == "pass" for r in rows), rows
    assert {r[6] for r in rows if r[0] == "C4r"} == {"2026-09-22T10:00:00"}
    assert {tuple(r) for r in rows if r[0] in ("C3", "C4")} == before       # the C3 / C4 rows are kept as they were
    # a later default run keeps the drill's rows as they were, and a C4r failure fails a named run
    run = P.reconcile_repo(root, "dev", run_at="2026-09-22T11:00:00")
    assert {r[6] for r in _results(root)[1:] if r[0] == "C4r"} == {"2026-09-22T10:00:00"}
    _write(os.path.join(root, "observed", "dev", "C4r.tsv"), OBS_C4R.replace("UNKNOWN\t1\t0", "UNKNOWN\t1\t"))
    code, out = _cli("reconcile", "--repo", root, "--profile", "dev", "--checks", "C4,C4r")
    assert code == 1 and "expected 0, observed BLANK" in out, out
    # only opt-in specs: the default run has nothing to do and says so
    only = _repo({"C4r": SPEC_C4R}, {"C4r": EXP_C4R}, {"C4r.tsv": OBS_C4R})
    assert "only opt-in checks" in _bad(P.reconcile_repo, only, "dev")
    assert P.reconcile_repo(only, "dev", ["C4r"])["exit_code"] == 0


def test_spec_validation_rejects_bad_specs():
    base = json.loads(json.dumps(SPEC_C3))
    cases = []
    s = json.loads(json.dumps(base)); s["measures"]["Requests"] = {"kind": "boolean", "compare": "rel_tol", "rel_tol": 1e-9}
    cases.append((s, "only applies to numbers"))
    s = json.loads(json.dumps(base)); s["measures"]["Requests"] = {"kind": "count", "compare": "approx"}
    cases.append((s, "compare must be"))
    s = json.loads(json.dumps(base)); s["measures"]["Median Hours"]["rel_tol"] = 0
    cases.append((s, "between 0 and 1"))
    s = json.loads(json.dumps(base)); s["keys"] = [{"name": "Agency", "kind": "hours"}]
    cases.append((s, "kind must be one of"))
    s = json.loads(json.dumps(base)); s["overrides"] = [{"when": {"Agency": "DOB"}, "measures": {"Nope": _ex("count")}}]
    cases.append((s, "not one of the spec's measures"))
    s = json.loads(json.dumps(base)); s["overrides"] = [{"when": {"Requests": "1"}, "measures": {"Requests": _ex("count")}}]
    cases.append((s, "only name key columns"))
    s = json.loads(json.dumps(base)); s["check_id"] = "C4"
    cases.append((s, "check_id"))
    for spec, what in cases:
        msg = _bad(P.spec_from_dict, spec, "C3")
        assert what in msg, (what, msg)


# --------------------------------------------------------------------------- the CLI and the results file

def test_cli_exit_codes_results_file_and_no_tracebacks():
    root = _repo({"C3": SPEC_C3}, {"C3": EXP_C3}, {"C3.tsv": OBS_C3})
    code, out = _cli("reconcile", "--repo", root, "--profile", "dev")
    assert code == 0 and "C3   PASS" in out, (code, out)
    rows = _results(root)
    assert rows[0] == ["check_id", "key", "measure", "expected", "observed", "status", "run_at"], rows[0]
    assert len(rows) == 19 and all(r[5] == "pass" for r in rows[1:]), rows
    assert dt.datetime.strptime(rows[1][6], "%Y-%m-%dT%H:%M:%S"), rows[1]
    before = open(os.path.join(root, "reconcile", "dev", "reconciliation_results.csv"), "rb").read()

    _write(os.path.join(root, "observed", "dev", "C3.tsv"), OBS_C3.replace("HPD\t500\t12.5\t\t", "HPD\t500\t12.5\t0\t"))
    code, out = _cli("reconcile", "--repo", root, "--profile", "dev", "--checks", "c3")
    assert code == 1 and "expected BLANK, observed 0" in out, (code, out)
    assert [r[5] for r in _results(root)[1:]].count("fail") == 1

    def refused(*args):
        code, out = _cli(*args)
        assert code == 2 and "Traceback" not in out, (args, code, out)
        return out
    before = open(os.path.join(root, "reconcile", "dev", "reconciliation_results.csv"), "rb").read()
    assert "not found" in refused("reconcile", "--repo", root, "--profile", "full")
    assert "no spec for C1, C9" in refused("reconcile", "--repo", root, "--profile", "dev", "--checks", "C1,C9")
    assert "check ids like" in refused("reconcile", "--repo", root, "--profile", "dev", "--checks", "all")
    refused("reconcile", "--repo", root, "--profile", "prod")
    refused("reconcile", "--profile", "dev")                                   # --repo defaults to cwd: no specs
    assert "is --repo" in refused("reconcile", "--repo", tempfile.mkdtemp(), "--profile", "dev")
    refused()
    _write(os.path.join(root, "observed", "dev", "C3.csv"), "x\n")
    assert "keep only the one" in refused("reconcile", "--repo", root, "--profile", "dev")
    os.remove(os.path.join(root, "observed", "dev", "C3.csv"))
    _write(os.path.join(root, "checks", "spec", "C3.json"), "{not json")
    assert "not valid JSON" in refused("reconcile", "--repo", root, "--profile", "dev")
    after = open(os.path.join(root, "reconcile", "dev", "reconciliation_results.csv"), "rb").read()
    assert after == before, "a refused run must not touch the results file"


SPEC_C3L = json.loads(json.dumps(SPEC_C3))
SPEC_C3L["measures"]["Carry-in Rows"] = _ex("count")
EXP_C3L = "\n".join(line + ("," + tail) for line, tail in zip(
    EXP_C3.strip().split("\n"), ["Carry-in Rows", "10", "5", ""])) + "\n"
OBS_C3L = "\n".join(line + ("\t" + tail) for line, tail in zip(
    OBS_C3.strip("\n").split("\n"), ["[Carry-in Rows]", "10", "5", ""])) + "\n"


def _manifest(root, files, profile="dev"):
    _write(os.path.join(root, "data", profile, "manifest.json"),
           json.dumps({"dataset": "t", "profile": profile, "files": files}))


def _mfile(name, role, rows, month=None):
    return {"name": name, "role": role, "month": month, "rows": rows, "sha256": "x", "bytes": 1,
            "dialect": "us12h", "source": "t", "as_of": "2026-09-20T01:51:01"}


def test_load_rows_compare_the_manifest_with_c1_and_c3():
    root = _repo({"C1": SPEC_C1, "C3": SPEC_C3L}, {"C1": EXP_C1, "C3": EXP_C3L},
                 {"C1.tsv": OBS_C1, "C3.tsv": OBS_C3L})
    files = [_mfile("w_2026-08.csv.gz", "window", 1500, "2026-08"),      # BRONX 1,000 + QUEENS 500
             _mfile("carry.csv.gz", "carryin", 15)]                       # DOB 10 + HPD 5 + OTI BLANK
    _manifest(root, files)
    run = P.reconcile_repo(root, "dev", run_at="2026-09-22T09:00:00")
    load = [r for r in _results(root)[1:] if r[0] == "L"]
    assert run["exit_code"] == 0, [r for r in _results(root)[1:] if r[5] != "pass"]
    assert load == [
        ["L", "File=w_2026-08.csv.gz; Month=2026-08", "Rows (C1 Current Requests, summed over boroughs)",
         "1500", "1500", "pass", "2026-09-22T09:00:00"],
        ["L", "File=carry.csv.gz", "Rows (C3 Carry-in Rows, summed over agencies)", "15", "15", "pass",
         "2026-09-22T09:00:00"]], load
    # a file the model did not load, a month the manifest does not know, a carry-in count off by one
    _manifest(root, [_mfile("w_2026-07.csv.gz", "window", 700, "2026-07"),
                     _mfile("w_2026-08.csv.gz", "window", 1400, "2026-08"),
                     _mfile("carry.csv.gz", "carryin", 16)])
    _write(os.path.join(root, "observed", "dev", "C1.tsv"),
           OBS_C1 + "FY2027\t2026-09\tQUEENS\tCurrent\tFalse\tFalse\t1\t3\t3\n")
    run = P.reconcile_repo(root, "dev", run_at="2026-09-22T09:30:00")
    assert run["exit_code"] == 1
    load = {r[1]: (r[3], r[4], r[5]) for r in _results(root)[1:] if r[0] == "L"}
    assert load == {"File=w_2026-07.csv.gz; Month=2026-07": ("700", "0", "fail"),
                    "File=w_2026-08.csv.gz; Month=2026-08": ("1400", "1500", "fail"),
                    "File=; Month=2026-09": ("", "3", "extra"),
                    "File=carry.csv.gz": ("16", "15", "fail")}, load
    # FYTD / PY / YoY % rows, subtotals, the grand total and all-BLANK months never count as loaded rows
    code, out = _cli("reconcile", "--repo", root, "--profile", "dev")
    assert code == 1 and "manifest 1400 rows, the model loaded 1500" in out, out


def test_load_rows_need_a_valid_manifest_and_the_observed_column():
    root = _repo({"C3": SPEC_C3L}, {"C3": EXP_C3L}, {"C3.tsv": OBS_C3L})
    code, out = _cli("reconcile", "--repo", root, "--profile", "dev")
    assert code == 2 and "manifest.json not found" in out and "Traceback" not in out, out
    assert not os.path.exists(os.path.join(root, "reconcile", "dev", "reconciliation_results.csv"))
    _manifest(root, [_mfile("w.csv.gz", "window", 1, None)])
    assert "month YYYY-MM" in _bad(P.reconcile_repo, root, "dev")
    _manifest(root, [_mfile("carry.csv.gz", "carryin", "15")])
    assert "whole number" in _bad(P.reconcile_repo, root, "dev")
    _manifest(root, [_mfile("carry.csv.gz", "carryin", 15)])
    _write(os.path.join(root, "observed", "dev", "C3.tsv"), OBS_C3)        # no Carry-in Rows column
    run = P.reconcile_repo(root, "dev")
    load = [r for r in _results(root)[1:] if r[0] == "L"]
    assert run["exit_code"] == 1 and [r[3:6] for r in load] == [["15", "", "missing"]], load
    # a C3 spec that does not name Carry-in Rows feeds no load row, and says so
    root = _repo({"C3": SPEC_C3}, {"C3": EXP_C3}, {"C3.tsv": OBS_C3})
    run = P.reconcile_repo(root, "dev")
    assert run["exit_code"] == 0 and any("no load row" in n for n in run["results"][0]["notes"])


def test_results_merge_keeps_other_checks_and_replaces_the_ones_that_ran():
    root = _repo({"C1": SPEC_C1, "C3": SPEC_C3L}, {"C1": EXP_C1, "C3": EXP_C3L},
                 {"C1.tsv": OBS_C1, "C3.tsv": OBS_C3L})
    _manifest(root, [_mfile("w_2026-08.csv.gz", "window", 1500, "2026-08"), _mfile("carry.csv.gz", "carryin", 15)])
    run = P.reconcile_repo(root, "dev", ["C3"], run_at="2026-09-22T10:00:00")
    assert run["exit_code"] == 0 and [r[0] for r in _results(root)[1:]] == ["C3"] * 21 + ["L"]
    run = P.reconcile_repo(root, "dev", ["C1"], run_at="2026-09-22T11:00:00")
    assert run["exit_code"] == 0 and run["kept_rows"] == 22, run["kept_rows"]
    rows = _results(root)[1:]
    assert [r[0] for r in rows] == ["C1"] * C1_CELLS + ["C3"] * 21 + ["L"] * 2, [r[0] for r in rows]
    assert {r[6] for r in rows if r[0] == "C3"} == {"2026-09-22T10:00:00"}
    _write(os.path.join(root, "observed", "dev", "C3.tsv"),
           OBS_C3L.replace("OTI\t40", "OTI\t41").replace("\t2\t\t10\n", "\t2\t\t11\n"))
    run = P.reconcile_repo(root, "dev", ["c3"], run_at="2026-09-22T12:00:00")
    assert run["exit_code"] == 1
    rows = _results(root)[1:]
    assert len(rows) == C1_CELLS + 23 and {r[6] for r in rows if r[0] == "C1"} == {"2026-09-22T11:00:00"}
    assert {tuple(r[1:4] + [r[6]]) for r in rows if r[0] == "L"} == {
        ("File=w_2026-08.csv.gz; Month=2026-08", "Rows (C1 Current Requests, summed over boroughs)", "1500",
         "2026-09-22T11:00:00"),
        ("File=carry.csv.gz", "Rows (C3 Carry-in Rows, summed over agencies)", "15", "2026-09-22T12:00:00")}
    assert [r for r in rows if r[5] == "fail"] == [
        ["C3", "Agency=DOB", "Carry-in Rows", "10", "11", "fail", "2026-09-22T12:00:00"],
        ["C3", "Agency=OTI", "Requests", "40", "41", "fail", "2026-09-22T12:00:00"],
        ["L", "File=carry.csv.gz", "Rows (C3 Carry-in Rows, summed over agencies)", "15", "16", "fail",
         "2026-09-22T12:00:00"]], [r for r in rows if r[5] == "fail"]
    run = P.reconcile_repo(root, "dev", None, run_at="2026-09-22T13:00:00")   # default: every non-opt-in spec
    assert run["checks"] == ["C1", "C3"] and {r[6] for r in _results(root)[1:]} == {"2026-09-22T13:00:00"}
    _write(os.path.join(root, "reconcile", "dev", "reconciliation_results.csv"), "a,b\n1,2\n")
    assert "unexpected header" in _bad(P.reconcile_repo, root, "dev", ["C1"])


def test_check_ids_with_a_letter_sort_after_their_number():
    assert P.parse_checks("c5B, C1,C10,c1") == ["C5b", "C1", "C10"]
    assert sorted(["L", "C10", "C5b", "C5", "C2"], key=P._check_sort_key) == ["C2", "C5", "C5b", "C10", "L"]
    for bad in ("5", "C0", "C5bb", "all"):
        assert "check ids like" in _bad(P.parse_checks, bad), bad


def test_main_in_process_returns_codes_and_never_raises():
    assert P.main(["reconcile", "--repo", tempfile.mkdtemp(), "--profile", "dev"]) == 2
    assert P.main(["reconcile", "--profile", "nope"]) == 2
    assert P.main([]) == 2


# --------------------------------------------------------------------------- the published files

def _pl300():
    if not os.path.isdir(os.path.join(PL300, "checks", "spec")):
        raise _Skip("no pl300-nyc311 repo at %s (set NL_PL300_REPO)" % PL300)
    return PL300


def _spec_9_2_blocks():
    text = open(os.path.join(_pl300(), "_design", "SPEC.md"), encoding="utf-8").read()
    sec = text[text.index("### 9.2 Query text"):text.index("### 9.3 Golden rows")]
    return re.findall(r"```dax\n(.*?)```", sec, flags=re.S)


def _spec_9_2_by_id():
    """SPEC 9.2's query blocks keyed by the check id in their first comment line (// C4r - ...)."""
    out = {}
    for b in _spec_9_2_blocks():
        m = re.match(r"^// (C[1-9][0-9]*[a-z]?) - ", b)
        assert m, b.splitlines()[0]
        out[m.group(1)] = b
    return out


def test_published_dax_c1_to_c4_and_c4r_are_spec_9_2_verbatim():
    blocks = _spec_9_2_by_id()
    assert sorted(blocks) == ["C1", "C2", "C3", "C4", "C4r", "C5"], sorted(blocks)
    for cid in ("C1", "C2", "C3", "C4", "C4r"):
        got = open(os.path.join(_pl300(), "checks", "dax", cid + ".dax"), encoding="utf-8").read()
        assert got == blocks[cid], "checks/dax/%s.dax differs from SPEC 9.2" % cid
    c1 = blocks["C1"]
    assert '{ "Current", "FYTD", "PY", "YoY %" }' in c1 and '"Check Row", 1,' in c1, c1


def _dax_outputs(dax, grouped=True):
    """The output column names of a check query: "Name" expressions plus Table[Column] group-bys."""
    body = dax.split("ORDER BY")[0]
    outputs = re.findall(r'"([^"]+)"\s*,', body)
    for rollup in re.findall(r"ROLLUPADDISSUBTOTAL\s*\((.*?)\)\s*,", body):
        outputs += re.findall(r'"([^"]+)"', rollup)          # its last name is followed by ')', not ','
    if grouped:
        outputs = re.findall(r"^\s*(?:'[^']+'|\w+)\[([^\]]+)\]\s*,\s*$", body, flags=re.M) + outputs
    return set(outputs)


def test_published_specs_load_and_name_exactly_the_dax_output_columns():
    repo = _pl300()
    blocks = _spec_9_2_by_id()
    have = P.available_checks(repo)
    assert have == ["C1", "C2", "C3", "C4", "C4r", "C5", "C5b"], have
    assert P.default_checks(have) == ["C1", "C2", "C3", "C4", "C5", "C5b"]     # lead decision 2: C4r opt-in
    views = set(re.search(r"TREATAS \( \{ (.*?) \}", blocks["C1"]).group(1).replace('"', "").split(", "))
    assert views == {"Current", "FYTD", "PY", "YoY %"}, views
    c5 = _dax_outputs(blocks["C5"], grouped=False)
    want = {"C1": (_dax_outputs(blocks["C1"]) - views) | {"Fiscal Year", "Year Month"},
            "C2": _dax_outputs(blocks["C2"]), "C3": _dax_outputs(blocks["C3"]), "C4": _dax_outputs(blocks["C4"]),
            "C4r": _dax_outputs(blocks["C4r"]), "C5": c5,
            "C5b": c5 - {"Breach Flag"}}                                        # SPEC 9.2: same minus Breach Flag
    specs = {}
    for cid, outputs in want.items():
        spec = specs[cid] = P.load_spec(os.path.join(repo, "checks", "spec", cid + ".json"), cid)
        names = spec.key_names + list(spec.measures)
        assert sorted(names) == sorted(outputs), (cid, sorted(names), sorted(outputs))
        for m, rule in spec.measures.items():
            if rule["kind"] in ("count", "integer", "boolean", "date", "text"):
                assert rule["compare"] == "exact", (cid, m, rule)
            else:
                assert rule["compare"] == "rel_tol" and rule["rel_tol"] == 1e-9, (cid, m, rule)
            assert (rule["constant"] == 1) == (m == "Check Row"), (cid, m, rule)   # Check Row: exactly 1
        raw = json.load(open(os.path.join(repo, "checks", "spec", cid + ".json"), encoding="utf-8"))
        dax = raw.get("dax")
        for path in (dax.values() if isinstance(dax, dict) else [dax]):
            assert path in ("checks/dax/%s.dax" % cid, "checks/dax/%s.dev.dax" % cid,
                            "checks/dax/%s.full.dax" % cid), (cid, path)
            if cid not in ("C5", "C5b"):
                assert os.path.isfile(os.path.join(repo, path)), (cid, path)
    for cid in ("C1", "C4", "C4r"):
        assert "Check Row" in specs[cid].measures, cid
    # C4r is C4 without the two Fast columns, compared the same way
    assert specs["C4r"].keys == specs["C4"].keys
    assert dict(specs["C4r"].measures) == {m: r for m, r in specs["C4"].measures.items() if "(Fast)" not in m}
    c1 = specs["C1"]
    assert c1.rule("Requests", {"Time View": "YoY %"})["kind"] == "ratio"
    for view in ("Current", "FYTD", "PY"):
        assert c1.rule("Requests", {"Time View": view})["kind"] == "count", view
    assert c1.rule("Requests (Daily)", {"Time View": "FYTD"})["kind"] == "count"
    assert P._feeds_window_load({"check_id": "C1", "spec": c1}), "C1 must feed the load rows (SPEC 9.4)"
    assert P._feeds_carryin_load({"check_id": "C3", "spec": specs["C3"]}), "C3 must feed the carry-in load row"


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    failed = skipped = 0
    for fn in TESTS:
        try:
            fn()
            print("  PASS  %s" % fn.__name__)
        except _Skip as exc:
            skipped += 1
            print("  SKIP  %s: %s" % (fn.__name__, exc))
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print("  FAIL  %s: %s: %s" % (fn.__name__, type(exc).__name__, str(exc)[:300]))
    print("\n%d/%d passed, %d skipped" % (len(TESTS) - failed - skipped, len(TESTS), skipped))
    if failed:
        sys.exit(1)
    print("ALL TESTS PASSED")
