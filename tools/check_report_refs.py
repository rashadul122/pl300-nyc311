#!/usr/bin/env python3
"""Check that the PBIR report references only model objects that exist in the TMDL.

    python3 tools/check_report_refs.py [PROJECT_DIR] [--pages p01,p03,p04]

PROJECT_DIR defaults to the repo root (the parent of tools/). The report folder is the one
NYC311-Operations.pbip points at (else the only *.Report folder); its model is the folder
definition.pbir's byPath names. Python 3 standard library only.

Errors (exit 1):
  - model references: every Column / Measure / Hierarchy / HierarchyLevel expression, and every
    From entity, in any visual.json, page.json (filters), report.json or bookmark, names a table,
    column, measure, hierarchy or level that the TMDL declares, with the right kind (a Measure
    reference must be a measure, a Column reference a column); SourceRef aliases resolve through
    the enclosing From list;
  - calculation items: a literal compared with a calculation-group column (for example a visual
    filter on 'Time Calc'[Time View]) must be one of that group's calculation items;
  - report wiring: every formatting selector's "metadata" is a queryRef of the same visual; every
    visualInteractions source/target and every parentGroupName is a visual on the same page; every
    bookmark a button links to exists; every drillthrough button's target page exists and has a
    Drillthrough pageBinding; pages.json lists only existing page folders; a bookmark names only
    existing pages and visuals; filter names are unique across the report;
  - slicer sync (SPEC §8): pages 1, 3, 4 and 5 each hold a slicer in sync groups SyncDate
    (Date.Date) and SyncBorough (Borough.Borough), page 10 holds none in SyncBorough, every slicer
    in a group projects that group's one field, and only slicers carry a syncGroup.

What it does NOT do: evaluate DAX, render visuals, or validate the files against Microsoft's JSON
schemas. A clean run means "every name resolves", not "Power BI renders it".
"""
from __future__ import annotations

import json
import os
import re
import sys
from typing import Dict, List, Optional

# SPEC §8: "The Date range and Borough slicers are synced across pages 1, 3, 4 and 5. Page 10 is
# not synced to Borough." group name -> (the one queryRef its slicers project, required pages,
# pages that must stay out of it)
SYNC_GROUPS = {
    "SyncDate": ("Date.Date", {"p01", "p03", "p04", "p05"}, set()),
    "SyncBorough": ("Borough.Borough", {"p01", "p03", "p04", "p05"}, {"p10"}),
}

_DECL = re.compile(r"^(table|column|measure|hierarchy|level|calculationGroup|calculationItem)\b\s*(.*)$")


def _name(rest: str) -> str:
    rest = rest.strip()
    if rest.startswith("'"):
        i, out = 1, []
        while i < len(rest):
            if rest[i] == "'":
                if i + 1 < len(rest) and rest[i + 1] == "'":
                    out.append("'")
                    i += 2
                    continue
                break
            out.append(rest[i])
            i += 1
        return "".join(out)
    return re.split(r"\s*=|\s", rest, maxsplit=1)[0]


def load_model(definition_dir: str) -> Dict[str, dict]:
    """tables -> {columns, measures, hierarchies{name: levels}, calc_items, calc_group}"""
    tables: Dict[str, dict] = {}
    for dirpath, _, files in os.walk(definition_dir):
        for f in sorted(files):
            if not f.endswith(".tmdl"):
                continue
            table: Optional[dict] = None
            hier: Optional[str] = None
            in_cg = False
            fence = False
            for raw in open(os.path.join(dirpath, f), encoding="utf-8").read().split("\n"):
                line = raw.rstrip("\r")
                if line.strip().startswith("```"):
                    fence = not fence
                    continue
                if fence or not line.strip() or line.strip().startswith("///"):
                    continue
                depth = len(line) - len(line.lstrip("\t"))
                m = _DECL.match(line.strip())
                if depth == 0:
                    table, hier, in_cg = None, None, False
                    if m and m.group(1) == "table":
                        n = _name(m.group(2))
                        table = tables.setdefault(n, {"columns": set(), "measures": set(), "hierarchies": {},
                                                      "calc_items": [], "calc_group": False})
                    continue
                if table is None or not m:
                    continue
                kind, n = m.group(1), _name(m.group(2))
                if depth == 1:
                    hier, in_cg = None, False
                    if kind == "column":
                        table["columns"].add(n)
                    elif kind == "measure":
                        table["measures"].add(n)
                    elif kind == "hierarchy":
                        hier = n
                        table["hierarchies"][n] = []
                    elif kind == "calculationGroup":
                        in_cg = True
                        table["calc_group"] = True
                elif depth == 2:
                    if kind == "level" and hier is not None:
                        table["hierarchies"][hier].append(n)
                    elif kind == "calculationItem" and in_cg:
                        table["calc_items"].append(n)
    return tables


class Checker:
    def __init__(self, tables: Dict[str, dict]):
        self.t = tables
        self.errors: List[str] = []
        self.refs = 0

    def err(self, where: str, msg: str) -> None:
        self.errors.append("%s: %s" % (where, msg))

    # ---- model references
    def _entity(self, sref: dict, scope: List[Dict[str, Optional[str]]], where: str) -> Optional[str]:
        if not isinstance(sref, dict):
            return None
        if "Entity" in sref:
            return sref["Entity"]
        alias = sref.get("Source")
        for frame in reversed(scope):
            if alias in frame:
                return frame[alias]            # None for a subquery alias
        self.err(where, "SourceRef alias %r is not defined by an enclosing From" % alias)
        return None

    def _table(self, ent: str, where: str) -> Optional[dict]:
        tb = self.t.get(ent)
        if tb is None:
            self.err(where, "table %r does not exist in the model" % ent)
        return tb

    def walk(self, node, scope: List[Dict[str, Optional[str]]], where: str) -> None:
        if isinstance(node, list):
            for x in node:
                self.walk(x, scope, where)
            return
        if not isinstance(node, dict):
            return
        pushed = False
        if isinstance(node.get("From"), list):
            frame: Dict[str, Optional[str]] = {}
            for fr in node["From"]:
                if not isinstance(fr, dict):
                    continue
                if "Entity" in fr:
                    self.refs += 1
                    self._table(fr["Entity"], where)
                    frame[fr.get("Name")] = fr["Entity"]
                else:
                    frame[fr.get("Name")] = None       # subquery
            scope = scope + [frame]
            pushed = True
        for key in ("Column", "Measure"):
            ref = node.get(key)
            if isinstance(ref, dict) and "Property" in ref and isinstance(ref.get("Expression"), dict):
                sref = ref["Expression"].get("SourceRef")
                if sref is not None:
                    ent = self._entity(sref, scope, where)
                    if ent is not None:
                        self.refs += 1
                        tb = self._table(ent, where)
                        prop = ref["Property"]
                        if tb is not None:
                            bucket, other = ("columns", "measures") if key == "Column" else ("measures", "columns")
                            if prop not in tb[bucket]:
                                hint = " (it is a %s)" % other[:-1] if prop in tb[other] else ""
                                self.err(where, "%s %r.%r does not exist%s" % (key.lower(), ent, prop, hint))
        hl = node.get("HierarchyLevel")
        if isinstance(hl, dict):
            h = (hl.get("Expression") or {}).get("Hierarchy")
            if isinstance(h, dict):
                ent = self._entity((h.get("Expression") or {}).get("SourceRef"), scope, where)
                if ent is not None:
                    self.refs += 1
                    tb = self._table(ent, where)
                    if tb is not None:
                        levels = tb["hierarchies"].get(h.get("Hierarchy"))
                        if levels is None:
                            self.err(where, "hierarchy %r.%r does not exist" % (ent, h.get("Hierarchy")))
                        elif hl.get("Level") not in levels:
                            self.err(where, "level %r of hierarchy %r.%r does not exist"
                                     % (hl.get("Level"), ent, h.get("Hierarchy")))
        # literals compared with a calculation-group column must be calculation items
        cond = node.get("In")
        if isinstance(cond, dict) and isinstance(cond.get("Values"), list):
            exprs = cond.get("Expressions") or []
            for i, e in enumerate(exprs):
                c = e.get("Column") if isinstance(e, dict) else None
                if not c:
                    continue
                ent = self._entity((c.get("Expression") or {}).get("SourceRef"), scope, where)
                tb = self.t.get(ent) if ent else None
                if tb and tb["calc_group"] and c.get("Property") in tb["columns"]:
                    for row in cond["Values"]:
                        v = ((row[i] if i < len(row) else {}).get("Literal") or {}).get("Value", "")
                        item = v[1:-1].replace("''", "'") if v.startswith("'") else v
                        if item not in tb["calc_items"]:
                            self.err(where, "%r is not a calculation item of %r (items: %s)"
                                     % (item, ent, ", ".join(tb["calc_items"])))
        for k, v in node.items():
            if k != "From":
                self.walk(v, scope, where)
            else:
                for fr in v if isinstance(v, list) else []:
                    if isinstance(fr, dict) and "Expression" in fr:
                        self.walk(fr["Expression"], scope[:-1] if pushed else scope, where)


def _query_refs(visual: dict) -> set:
    refs = set()
    qs = ((visual.get("query") or {}).get("queryState") or {})
    for role in qs.values():
        for p in (role or {}).get("projections", []):
            refs.add(p.get("queryRef"))
            if "NativeVisualCalculation" in (p.get("field") or {}):
                refs.add(p["field"]["NativeVisualCalculation"].get("Name"))
    return refs


def _selectors(node, out):
    if isinstance(node, dict):
        sel = node.get("selector")
        if isinstance(sel, dict) and "metadata" in sel:
            out.append(sel["metadata"])
        for v in node.values():
            _selectors(v, out)
    elif isinstance(node, list):
        for v in node:
            _selectors(v, out)


def _literal(prop) -> Optional[str]:
    v = (((prop or {}).get("expr") or {}).get("Literal") or {}).get("Value")
    if isinstance(v, str) and v.startswith("'") and v.endswith("'"):
        return v[1:-1].replace("''", "'")
    return v


def find_report(project: str) -> str:
    for f in sorted(os.listdir(project)):
        if f.endswith(".pbip"):
            doc = json.load(open(os.path.join(project, f), encoding="utf-8"))
            for a in doc.get("artifacts", []):
                p = (a.get("report") or {}).get("path")
                if p:
                    return os.path.normpath(os.path.join(project, p))
    reps = [d for d in os.listdir(project) if d.endswith(".Report")]
    if len(reps) != 1:
        raise SystemExit("cannot tell which *.Report folder to check in %s" % project)
    return os.path.join(project, reps[0])


def run(project: str, pages_only: Optional[List[str]] = None):
    report = find_report(project)
    pbir = json.load(open(os.path.join(report, "definition.pbir"), encoding="utf-8"))
    by = ((pbir.get("datasetReference") or {}).get("byPath") or {}).get("path")
    if not by:
        return ["%s: definition.pbir has no byPath model reference" % report], "no check run"
    model_def = os.path.normpath(os.path.join(report, by, "definition"))
    if not os.path.isdir(model_def):
        return ["definition.pbir byPath %r does not resolve to a model definition folder" % by], "no check run"
    ck = Checker(load_model(model_def))
    rdef = os.path.join(report, "definition")
    rel = lambda p: os.path.relpath(p, project)

    pages_dir = os.path.join(rdef, "pages")
    page_names = sorted(d for d in os.listdir(pages_dir) if os.path.isdir(os.path.join(pages_dir, d))) \
        if os.path.isdir(pages_dir) else []
    page_json = {}
    page_visuals: Dict[str, Dict[str, dict]] = {}
    for pn in page_names:
        pj = os.path.join(pages_dir, pn, "page.json")
        if os.path.isfile(pj):
            page_json[pn] = json.load(open(pj, encoding="utf-8"))
        vis = {}
        vdir = os.path.join(pages_dir, pn, "visuals")
        for vn in sorted(os.listdir(vdir)) if os.path.isdir(vdir) else []:
            vp = os.path.join(vdir, vn, "visual.json")
            if os.path.isfile(vp):
                vis[vn] = (vp, json.load(open(vp, encoding="utf-8")))
        page_visuals[pn] = vis

    bm_dir = os.path.join(rdef, "bookmarks")
    bookmarks = {}
    for f in sorted(os.listdir(bm_dir)) if os.path.isdir(bm_dir) else []:
        if f.endswith(".bookmark.json"):
            doc = json.load(open(os.path.join(bm_dir, f), encoding="utf-8"))
            bookmarks[doc.get("name", f[:-len(".bookmark.json")])] = (os.path.join(bm_dir, f), doc)

    checked = [p for p in page_names if not pages_only or p in pages_only]
    for pn in checked:
        if pn not in page_json:
            ck.err(rel(os.path.join(pages_dir, pn)), "page folder has no page.json")
            continue
        pj = page_json[pn]
        where = rel(os.path.join(pages_dir, pn, "page.json"))
        if pj.get("name") != pn:
            ck.err(where, "name %r does not match its folder %r" % (pj.get("name"), pn))
        ck.walk(pj, [], where)
        names = set(page_visuals[pn])
        for it in pj.get("visualInteractions", []):
            for side in ("source", "target"):
                if it.get(side) not in names:
                    ck.err(where, "visualInteractions %s %r is not a visual on this page" % (side, it.get(side)))
        groups = {n for n, (_, v) in page_visuals[pn].items() if "visualGroup" in v}
        for vn, (vp, v) in page_visuals[pn].items():
            w = rel(vp)
            if v.get("name") != vn:
                ck.err(w, "name %r does not match its folder %r" % (v.get("name"), vn))
            ck.walk(v, [], w)
            pg = v.get("parentGroupName")
            if pg and pg not in groups:
                ck.err(w, "parentGroupName %r is not a visual group on this page" % pg)
            vis = v.get("visual") or {}
            qrefs = _query_refs(vis)
            sels: List[str] = []
            _selectors(vis.get("objects"), sels)
            for m in sels:
                if m not in qrefs:
                    ck.err(w, "formatting selector metadata %r is not a queryRef of this visual" % m)
            for link in (vis.get("visualContainerObjects") or {}).get("visualLink", []):
                props = link.get("properties") or {}
                typ = _literal(props.get("type"))
                if typ == "Bookmark":
                    b = _literal(props.get("bookmark"))
                    if b not in bookmarks:
                        ck.err(w, "button links to bookmark %r, which does not exist" % b)
                elif typ == "Drillthrough":
                    target = _literal(props.get("drillthroughSection"))
                    tp = page_json.get(target)
                    if tp is None:
                        ck.err(w, "drillthrough target page %r does not exist" % target)
                    elif (tp.get("pageBinding") or {}).get("type") != "Drillthrough":
                        ck.err(w, "drillthrough target page %r has no Drillthrough pageBinding" % target)
                elif typ == "PageNavigation":
                    target = _literal(props.get("navigationSection"))
                    if target not in page_json:
                        ck.err(w, "page navigation target %r does not exist" % target)

    # slicer sync groups (SPEC §8): a page follows a sync group only if it holds a slicer in it
    members: Dict[str, Dict[str, List[tuple]]] = {}
    for pn in page_names:
        for vn, (vp, v) in page_visuals[pn].items():
            vis = v.get("visual") or {}
            sg = vis.get("syncGroup")
            if not isinstance(sg, dict):
                continue
            w = rel(vp)
            if vis.get("visualType") != "slicer":
                ck.err(w, "syncGroup on a %r visual; sync groups apply only to slicers" % vis.get("visualType"))
            members.setdefault(sg.get("groupName"), {}).setdefault(pn, []).append((w, sorted(_query_refs(vis))))
    for grp, (field, required, excluded) in SYNC_GROUPS.items():
        pages_in = members.get(grp, {})
        for pn in sorted(required):
            if pn in page_json and pn in checked and pn not in pages_in:
                ck.err(rel(os.path.join(pages_dir, pn)),
                       "page has no slicer in sync group %r (SPEC §8 syncs it across %s)"
                       % (grp, ", ".join(sorted(required))))
        for pn in sorted(excluded):
            if pn in pages_in and pn in checked:
                ck.err(rel(os.path.join(pages_dir, pn)), "page must not be in sync group %r (SPEC §8)" % grp)
        for pn, lst in pages_in.items():
            for w, refs in lst:
                if pn in checked and refs != [field]:
                    ck.err(w, "slicer in sync group %r projects %s, expected [%r]" % (grp, refs, field))

    # filter names must be unique across the whole report definition (filterConfiguration schema)
    seen: Dict[str, str] = {}
    def filters_of(doc, w):
        if isinstance(doc, dict):
            for f in (doc.get("filterConfig") or {}).get("filters", []) if isinstance(doc.get("filterConfig"), dict) else []:
                n = f.get("name")
                if n in seen:
                    ck.err(w, "filter name %r is also used in %s" % (n, seen[n]))
                seen.setdefault(n, w)
    for pn in page_names:
        if pn in page_json:
            filters_of(page_json[pn], rel(os.path.join(pages_dir, pn, "page.json")))
        for vn, (vp, v) in page_visuals[pn].items():
            filters_of(v, rel(vp))

    rj = os.path.join(rdef, "report.json")
    if os.path.isfile(rj):
        ck.walk(json.load(open(rj, encoding="utf-8")), [], rel(rj))
    pj = os.path.join(pages_dir, "pages.json")
    if os.path.isfile(pj):
        for pn in json.load(open(pj, encoding="utf-8")).get("pageOrder", []):
            if pn not in page_json:
                ck.err(rel(pj), "pageOrder names %r, which has no page folder with a page.json" % pn)
    for bn, (bp, doc) in bookmarks.items():
        w = rel(bp)
        ck.walk(doc, [], w)
        es = doc.get("explorationState") or {}
        if es.get("activeSection") and es["activeSection"] not in page_json:
            ck.err(w, "activeSection %r is not a page" % es["activeSection"])
        for sec, st in (es.get("sections") or {}).items():
            if sec not in page_json:
                ck.err(w, "section %r is not a page" % sec)
                continue
            for vn in (st.get("visualContainers") or {}):
                if vn not in page_visuals.get(sec, {}):
                    ck.err(w, "visual %r is not on page %r" % (vn, sec))
        for vn in (doc.get("options") or {}).get("targetVisualNames", []):
            if not any(vn in vs for vs in page_visuals.values()):
                ck.err(w, "targetVisualNames %r is not a visual of the report" % vn)
    bj = os.path.join(bm_dir, "bookmarks.json")
    if os.path.isfile(bj):
        def names(items):
            for it in items:
                yield from (it.get("children") or [it.get("name")]) if "children" in it else [it.get("name")]
        for bn in names(json.load(open(bj, encoding="utf-8")).get("items", [])):
            if bn not in bookmarks:
                ck.err(rel(bj), "bookmark %r has no .bookmark.json file" % bn)

    ck.summary = "%d model reference(s) checked on page(s) %s" % (ck.refs, ", ".join(checked) or "-")
    return ck.errors, ck.summary


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    pages = None
    if "--pages" in argv:
        i = argv.index("--pages")
        pages = [p for p in argv[i + 1].split(",") if p]
        del argv[i:i + 2]
    project = argv[0] if argv else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    errors, summary = run(project, pages)
    for e in errors:
        print(e)
    print("%s; %d problem(s)." % (summary, len(errors)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
