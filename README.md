# NYC 311 Service Operations: a Power BI project (PL-300 showcase)

**AI-built, owner-directed.** A Power BI semantic model and report for New York City 311 service requests: intake, backlog, time to resolve, benchmark breaches and data-quality controls. The model and report are Power BI Project (PBIP) files: TMDL for the model and the enhanced PBIR format for the report.

> "AI-built, owner-directed: the Power Query, model, measures, RLS and report were written by AI (Claude) from a specification the owner directed; the numbers are checked against an independent Python twin with the reconcile CLI."

**Status (23 Sep 2026): written, not yet run in Power BI.** The files exist and their structure has been checked on a Mac. Nothing has been refreshed, calculated or rendered in Power BI yet, so this README quotes **no result from the model**. Anything that needs Power BI is marked **[unrun]**.

## What it is

The report is for a City 311 operations manager, and for borough managers who see only their own boroughs. It answers eight questions:

| # | Question | Page |
|---|---|---|
| Q1 | How many requests came in, and is that normal against last year? | 1 Overview |
| Q2 | How big is the backlog at period end, by agency and borough, and is it growing? | 3 Backlog |
| Q3 | How long do requests take (median, P25/P75/P90) by agency, and who is slowest? | 4 Resolution & Benchmark |
| Q4 | What share met the internal benchmark, and what if the target were X hours? | 4 |
| Q5 | Which days were abnormal, and do weather, weekday or the complaint mix explain them? | 1 |
| Q6 | What drives benchmark breaches? | 5 Drivers (AI) |
| Q7 | Are residents moving from phone to online and mobile? | 1 |
| Q8 | Which numbers should I not trust yet? | 10 Data Quality & Method |

Page 7 (Complaint Detail) is a hidden drillthrough page, reached from page 4.

**For a bank reviewer:** this is complaint and case-handling operations: intake, backlog, time to resolve, breach drivers and data-quality controls. It has the same shape as a bank's complaint-handling and operations reporting.

**"SLA" honesty.** The data has no official service-level targets (its due date is almost always empty). The report uses an **internal benchmark** instead: per complaint category, the 75th percentile of resolution hours in the year before the reporting window (Sep 2023 to Aug 2024). It is labelled as such and is not NYC policy. The benchmark hours are an input from the Python side of the project; `data/reference/sla_baseline_summary.csv` documents how they were derived.

## What is built

| Part | Where | State |
|---|---|---|
| Semantic model (TMDL): Power Query, star schema, measures, the Time Calc calculation group, RLS roles | `NYC311-Operations.SemanticModel/` | Written by AI. Structure checked on a Mac (below). **[unrun]** |
| Report (enhanced PBIR), with the base theme as its custom theme | `NYC311-Operations.Report/` | Written by AI. Structure checked on a Mac. **[unrun]** |
| Project pointer | `NYC311-Operations.pbip` | Written by AI |
| The data extract: a frozen snapshot, `as_of` 20 Sep 2026, window Sep 2024 to Aug 2026 | `data/dev/` (committed), `data/full/manifest.json` | Dev: a 1-in-25 sample, 301,688 window rows + 8,037 carry-in rows. Full: 7,542,606 + 201,517 rows, too large for Git, meant to be a release asset (`data-v1`) |
| Reference tables (agency remap, complaint categories, channels, boroughs, benchmark hours, test users for dynamic RLS) | `data/reference/` | Data only |
| Expected values from the Python twin, for both profiles | `expected/dev/`, `expected/full/` | Computed by the twin (a separate pandas implementation of the same rules) |
| Check queries (DAX) | `checks/dax/` | Written. **[unrun]** |
| Reconcile CLI (Python standard library only) | `tools/reconcile/` | Runs; its own tests pass |
| Base theme and its contrast check | `theme/` | Written |
| Specification | `_design/SPEC.md` | The source of truth for behaviour |

**What "structure checked on a Mac" means.** Power BI Desktop does not run on a Mac. Two checks did run:
- a structural lint (the NorthLedger engine's `pbip_lint`): encoding, tab indentation, JSON schemas, `.platform` ids, the report's link to the model, and that every relationship, sort-by column and hierarchy level points at a column that exists;
- **Microsoft's own TMDL parser**, driven locally through the Power BI Modeling MCP binary: it loads the model folder and lists its tables and relationships.

Neither check evaluates DAX or Power Query M, or draws a visual. A model that passes both can still fail to refresh, or return wrong numbers.

## What is [unrun] until the project is opened in Power BI

- **Refresh:** no Power Query has run, and nothing has been read from GitHub or from the weather API.
- **DAX:** no measure, calculated table, calculated column, calculation item or RLS filter has been evaluated.
- **Visuals:** no page has been rendered, so there are **no screenshots**. They will be added when real ones exist, never mock-ups.
- **Reconciliation:** `observed/` and `reconcile/` are empty. No check query has run, so **no number in the model is claimed to be correct yet**.
- **RLS:** no role has been tested with Test as role.
- **Two settings that must be finished in the Power BI service** (the file format has no documented way to store them):
  - page 1's daily line chart: anomaly detection's *Explain by* fields (Borough, Category, Channel, Precip Bucket, Day Name) are added in the service, under Analytics > Find anomalies;
  - page 5's decomposition tree: the file saves both AI levels as the "MaxSplit" method, read here as Desktop's *High value* split; confirm in the service that both levels show the AI bulb and *High value*.
  Each visual carries a `serviceStep` note with the exact step.

The reconciliation below is the only proof of the numbers. One limit applies even after it passes: the model and the twin were both written by AI from the same specification, so an error in the specification itself would pass in both. The hand-checked golden rows (C5, C5b) and the engine's raw audit reduce that risk; they do not remove it.

## How the numbers are checked

1. In Power BI, run each query in `checks/dax/` in the DAX query view, copy the result grid, and save it as `observed/<profile>/Cn.tsv`.
2. From the repo root, with Python 3.9 or later and nothing to install:
   ```
   PYTHONPATH=tools/reconcile python3 -m northledger.pbi reconcile --repo . --profile dev
   ```
   This compares every observed cell with `expected/<profile>/` and writes `reconcile/<profile>/reconciliation_results.csv`. Counts must match exactly, hours and ratios to a relative tolerance of 1e-9, and BLANK and 0 are different values.
3. The CLI's own tests: `NL_PL300_REPO="$PWD" python3 tools/reconcile/tests/test_pbi_reconcile.py`.

| Check | What it proves |
|---|---|
| C1 | Request counts by fiscal year, month and borough, and the Time Calc items (FYTD, PY, YoY %) with their completeness guard |
| C2 | Closures on the inactive close-date relationship; digital share by channel |
| C3 | Resolution statistics, the internal benchmark, the what-if default and the agency rank, by agency |
| C4 | The backlog at every month end, by borough; the fast and the row-by-row versions must be equal |
| C5, C5b | 33 real requests chosen to hit each cleaning rule, checked column by column |

Once results exist, anyone with a clone can re-run the CLI on the committed files and get the same result in every column except the run time.

## How to reproduce

**In a Fabric workspace (browser, Mac or Windows).** Summarised from SPEC §2.1 and §3.2; loading these AI-written files into a workspace has not been tried yet **[unrun]**.
1. Create a workspace on a Fabric capacity (a Fabric trial works). Turn on the setting that lets users edit data models in the Power BI service.
2. Fork or copy this repo. In the workspace settings, connect Git integration to your copy: branch `main`, Git folder = the repo root. Git integration then brings in the semantic model and the report, both named `NYC311-Operations`.
3. In the semantic model's settings, set the parameter **`pDataBaseUrl`** to your copy's address. Its default is `https://github.com/rashadul122/pl300-nyc311`, which works only once that repo is public. The model reads every data file relative to that address, over HTTPS, with no gateway.
4. Under data source credentials, set both web sources (GitHub and the Open-Meteo archive) to **Anonymous** with privacy level **Public**, then refresh.
5. `pProfile` defaults to `dev`, which loads the sample committed with the repo. For the full profile, publish the full files as release `data-v1` on your copy, set `pProfile` to `full`, and refresh.
6. Run the checks as above.

**In Power BI Desktop (Windows).** Open `NYC311-Operations.pbip` (untried).

## Data source and licence

- **311 requests:** City of New York, NYC Open Data, dataset `erm2-nwe9` ("311 Service Requests from 2020 to Present"). The files in `data/` are a frozen snapshot taken 20 Sep 2026 (latest created time 01:51:01, New York time), with a row filter and 19 columns selected. The dev profile keeps requests whose `unique_key` is divisible by 25. The data is public and is used under the NYC Open Data Terms of Use; this repo claims no rights over it.
- **Weather:** the Open-Meteo historical weather API (Central Park, New York), read at refresh time, not stored in this repo. Weather data by Open-Meteo.com, under its CC BY 4.0 licence.
- **This repo's own code and files:** no licence has been chosen yet.

## Not in v1, and why

- **Copilot:** it needs a paid Fabric capacity; trial capacities are excluded.
- **Automatic page refresh:** the model is import-only, with no DirectQuery source.
- **Power BI service features:** app, dashboards, alerts, subscriptions, scheduled refresh, workspace roles, RLS group membership and endorsement are planned for v2.
- **The page 1 mobile layout:** moved to v2.
- **Desktop dialogs the design replaced:** what-if parameter, Groups, bins and View as have documented model or service equivalents: a threshold table with its value measure, an Agency Group column, a bin column, and Test as role.

The full v2 list is in SPEC §13.

## Repository map

```
NYC311-Operations.pbip            project pointer
NYC311-Operations.SemanticModel/  the model (TMDL)
NYC311-Operations.Report/         the report (PBIR)
_design/SPEC.md                   the specification: rules, tables, measures, pages, checks
_design/HINTS.md                  concept notes from the earlier hand-built plan (reference only)
data/                             the extract (dev committed; full manifest only) and reference tables
checks/                           DAX check queries and their comparison rules
expected/                         the twin's expected values, per profile
observed/, reconcile/             pasted Power BI results and the comparison output (empty until run)
theme/                            base report theme and contrast check
tools/                            reconcile CLI, sealing check, git hooks
docs/decisions.md                 decision log
```

Decisions, including the owner's 23 Sep 2026 decision to have AI build v1, are logged in [`docs/decisions.md`](docs/decisions.md).
