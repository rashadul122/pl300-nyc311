# NorthLedger PL-300 showcase: NYC 311 Service Operations. SPEC (v1, round 8)

> **Round 8 (2026-09-23): owner decision.** The owner decided that **AI builds v1**. The Power Query, model, measures, calculation group, RLS roles and report are written by AI (Claude) from the reference solution, which is now unsealed for the builders, and delivered as TMDL and PBIR files in this repo (`NYC311-Operations.SemanticModel/`, `NYC311-Operations.Report/`, `NYC311-Operations.pbip`). The project is labelled **"AI-built, owner-directed"**, and §0.1 carries the new authorship statement.
> - **Retired for v1:** the hand-built process: the attempt → reconcile → hint → key protocol, the hint ladder (HINTS.md and the Tier-2 hints), the exposure record, the study-tracker markers and the README's marker summary, and the interview drill (Appendix C). Where later sections still say "the owner builds", "owner-written" or "his model", read "the builders"; where they describe the retired process, they no longer apply to v1.
> - **Kept:** the reconciliation loop (§9.4) is unchanged, and it is **the only proof of the numbers**. Nothing in the model is called reconciled, and no figure is quoted from it, until C1–C5 have run in Power BI and the reconcile CLI has compared them with `expected/`. Until then the model is [unrun].
> - **Everything else is unchanged:** every behaviour, table, measure, check, RLS requirement, page and file requirement below still applies. The answer key and `_design/PROCESS.md` stay untracked and ignored, and `tools/check_sealed.sh` still guards them.

Revision of `DESIGN.md`, dated 2026-09-22 (rounds 2 to 5 the same day; round 5 writes in the figures of the engine build). **Round 6 (2026-09-23) moves the build into the browser**: the Power BI service with Fabric web modelling, instead of Power BI Desktop in a Windows VM (§2.1). This file is **public** and is committed with the project.

It says **what** the Power BI work must do and **how it is checked**. It contains **no Power Query M, no model TMDL and no measure DAX**, and it describes measures by **behaviour** (which filters they respect, when they return BLANK or 0, which relationship they must use), never by the functions that implement them. Those are the owner's work, and the owner defends them in an interview. Three companion files go with it:

| File | Visibility | Contents |
|---|---|---|
| `SPEC.md` (this file) | Public, committed | Business questions, extract and manifest, cleaning rules stated as outcomes, star schema, measure catalogue as definition plus required behaviour, RLS requirements, report page specs, the DAX check queries and their expected-value files, the v1/v2 scope, the README skeleton, the interview drill |
| `HINTS.md` | Public, committed | **Tier 1 only:** for each query, measure, calculation item and role, the concept tested and the trap (as a symptom). No function names, no step orders |
| `_design/PROCESS.md` | **Private.** Gitignored; never committed; the owner reads it | Sealing and the repo split (gate G0) with `tools/check_sealed.sh`; the exposure record; the attempt → reconcile → hint → key protocol; gates G0 and G1; owner hours, cut list, checkpoints and hard stop; the PL-300 study tracker (all 78 skills) with its markers |
| `answer-key/ANSWER-KEY.md` | **Sealed.** Gitignored `answer-key/` folder; never committed | Part T: **Tier-2 hints** (functions and step orders). Parts K1–K8: full reference M, DAX, calculation items and RLS. Part K9: model answers for the interview drill. Opened one section at a time under the protocol in PROCESS.md |

**Status labels**
- **[twin]**: computed by the engine's pandas twin from the extract files in `data/`, and asserted by the engine's tests (the engine's `RESULTS.md` lists each figure with its cause). Where a figure was first counted by query, the twin either confirmed it or replaced it, and the cause of every change is stated where the figure sits.
- **[measured]**: counted read-only against `big_data.db` (`file:...?mode=ro`, `PRAGMA query_only=1`) or against the full-profile extract files (which are row-for-row copies of it), and not recomputed by the twin.
- **[research]**: from the research files.
- **[unrun]**: nothing here has been executed in Power BI Desktop or the Service. That includes the DAX check queries below.
- **[likely]**: documented by Microsoft or strongly indicated, but not yet tried in this browser build. Each one is checked in the first smoke test (task 1) or at its first use, and the result is logged in `docs/decisions.md`.

---

## 0. Authorship, and where the process lives

### 0.1 Authorship statement
The README, and the Data Quality & Method page, use exactly this text (round 8):

> "AI-built, owner-directed: the Power Query, model, measures, RLS and report were written by AI (Claude) from a specification the owner directed; the numbers are checked against an independent Python twin with the reconcile CLI."

The round-7 statement, its exposure-record sentence and the README's marker summary described the hand-built process, which round 8 retired for v1; they are withdrawn and are not used anywhere.

What the engine (Claude plus the NorthLedger Python code) **produces**:
- the extract files and manifests;
- reference CSVs (data only), including the draft complaint category map and complaint aliases (owner-reviewed), the benchmark hours and the baseline summary behind them;
- the NorthLedger raw audit of the extract: the generic engine's profile of each role of each profile, checked against the manifest and written to `expected/<profile>/raw_audit/` (§3.5), with its map onto `rule_counts.csv`;
- the pandas twin and its tests (in the **separate engine repo**; the owner receives only their outputs);
- the expected-value files;
- the DAX check queries in §9, which name measures but reveal no measure logic;
- the reconcile CLI (vendored into this repo under `tools/reconcile/`, §9.4), lint scripts, the sealing check and a base theme JSON;
- this SPEC, HINTS, PROCESS and the sealed key.

What the builders (AI, round 8) **also produce**: every M query, relationship, column property, measure, calculation item, role and report visual, written as TMDL (`NYC311-Operations.SemanticModel/`) and PBIR (`NYC311-Operations.Report/`), and the `NYC311-Operations.pbip` pointer file (§3.2). A Fabric workspace reads these folders through Git integration; any change made there comes back through the same integration. (Until round 7 the engine wrote no TMDL, and the owner built the model and report in the browser.)

### 0.2 Sealing, gates and hours (private)
**Round 8:** the hand-built parts of this process (the protocol, hint and key logging, the exposure record, the tracker markers and the drill) are retired for v1. The sealing rules below still hold: the answer key and PROCESS.md stay untracked, ignored and out of history.

The owner's process is in `_design/PROCESS.md`: sealing and the repo split (gate G0), the exposure record, the attempt → reconcile → hint → key protocol, gate G1 (engine ready), the hours, the cut list and the study tracker. It is **private**: gitignored, never committed, and read by the owner. Three facts from it matter to any reader of this repo:
- The sealed answer key (`answer-key/`, gitignored) and the engine's source and design history (the sibling repo `pl300-nyc311-engine/`, local-only until v1 is green, then published) never enter this repo. `tools/check_sealed.sh` enforces this as a pre-commit hook, a pre-push hook and a CI job. **Commits that Fabric Git integration makes from the workspace do not run the local hooks; for those commits the CI job is the guard** (§3.2).
- The owner builds each item from this SPEC and HINTS first. A Tier-2 hint or a key section is opened only after a failed, committed attempt, and every opening is logged in `docs/decisions.md`, which the README links.
- No task that touches this repo starts before gate G0 (sealing) is signed, and no build task starts before gate G1 (engine outputs ready) is signed. Both sign-offs are lines in `docs/decisions.md`.

---

## 1. Subject, audience and business questions

**Subject:** City of New York 311 service requests, dataset `erm2-nwe9`, as a local snapshot.

**Persona:** a City 311 operations manager, plus borough managers, whose needs drive RLS.

**For a bank reviewer (README line):** this is complaint and case-handling operations: intake, backlog, time to resolve, breach drivers and data-quality controls. It has the same shape as a bank's complaint-handling and operations reporting.

| # | Question | v1 page | Answered by |
|---|---|---|---|
| Q1 | How many requests came in, and is that normal against last year? | 1 | Requests, Time Calc (PY, YoY %) with completeness guard |
| Q2 | How big is the operational backlog at period end, by agency and borough, and is it growing? | 3 | Open Backlog EOP (semi-additive, rolling 365-day age limit), Backlog Inflow / Outflow, age bands |
| Q3 | How long do requests take (median, P25/P75/P90) by agency, and who is slowest? | 4 | Resolution statistics, Agency Rank |
| Q4 | What share met the internal benchmark, and what if the target were X hours? | 4 | SLA Met % (Benchmark), SLA Met % (What-if) |
| Q5 | Which days were abnormal, and do weather, weekday or the complaint mix explain them? | 1 | Anomaly detection with Explain-by fields from Date and dimensions |
| Q6 | What drives benchmark breaches? | 5 | Key Influencers on Breach Flag; Decomposition tree |
| Q7 | Are residents shifting channel (online/mobile vs phone)? | 1 | Digital Share (its own small visual, titled for Q7) |
| Q8 | Which numbers should I not trust yet? | 10 | DQ rule table (Power Query vs twin), load reconciliation, check pass rate, method notes |

**"SLA" honesty.** The data carries no official service-level targets: `due_date` is 99.65% empty [research]. The report therefore uses two clearly labelled mechanisms.
- **Internal benchmark.**
  - Definition: per complaint **category**, the p75 of resolution hours over valid-for-resolution requests (R05) **created Sep 2023 – Aug 2024**, the baseline year before the reporting window. Rounded to the nearest whole hour (an exact half rounds up), minimum 1.
  - Categories with fewer than 30 baseline **valid** rows (R05-valid requests of the baseline year: `baseline_valid_rows` in §3.5) get no benchmark. In v1 every one of the 12 categories has at least 50,090 such rows, so all have one [twin].
  - Every baseline-year request is keyed: the category map also covers the 6 complaint keys that occur only in the baseline year, and the engine stops rather than leave any key unmapped (§3.5).
  - Labelled "internal benchmark derived from the Sep 2023 – Aug 2024 baseline year; not NYC policy".
  - Because the baseline sits **outside** the reporting window, Met % is not about 75% by construction in year one.
  - Caveat: the baseline p75 excludes zero-minute and over-1-year requests (R05).
  - **Reproducibility.** The baseline year lies outside the extract (the carry-in file holds only baseline-year requests still open at the window start), so the owner cannot recompute the p75 from the repo. The benchmark hours are therefore an **engine-provided input**, and the README and page 10 say so. To keep the method auditable, the engine also ships `data/reference/sla_baseline_summary.csv` (§3.5): per category, the baseline valid-row count and the p50 / p75 / p90 resolution minutes, the baseline window and `as_of`. The engine recomputes the p75 from `big_data.db`, and its tests assert that every benchmark equals the rounded summary p75 [twin].
- **What-if threshold** (4 to 336 hours) for "what if the target were 48 h?".

---

## 2. Scope: v1 and v2

**v1 is a frozen snapshot with an explicit `as_of`.** It is sized for a **60 h** owner cap. The plan, what is cut first and the hard stop are in PROCESS.md (§12).

| Area | v1 (this spec) | v2 (later sprint, §13) |
|---|---|---|
| Data | Frozen snapshot `as_of = 2026-09-20T01:51:01`; a **full** profile and a **dev** profile over the **same 24-month window** (dev = a 1-in-25 sample); read over HTTPS from the owner's public GitHub repo (dev files committed, full files as release assets; §3.2), no gateway; one date dialect (US 12-hour) | Monthly SODA pipeline with **per-file `as_of`** and a closure-delta re-pull (the examiner's cutoff fix); the ISO dialect; scheduled refresh |
| Report pages | 1 Overview (with the Q7 channel visual), 3 Backlog, 4 Resolution & Benchmark, 5 Drivers (AI), 7 Complaint Detail (the single drillthrough), 10 Data Quality & Method | 2 Volume & Trend, 6 Weather & Calendar, 8 Agency Scorecard, 9 tooltip page, 11 About; the page 1 mobile layout (round-6 cut) |
| Measures | **23 owner-written** (about 9 are one or two lines) plus the threshold value measure (§6.4), which the browser build writes by hand | Aggregation-aware Requests (Smart), Avg Daily Requests, Requests YoY %, rolling 28D, z-score, load-reconciliation measures, Backlog (Closing) |
| Check queries | C1–C5 (§9), all runnable in dev | Rolling 28D, z-score (weekday baseline), weather comparisons, dimension counts |
| Dropped from v1 | Borough Population, the transpose exercise, the quick-measure comparison, DAX UDFs, personalization, the live SODA pipeline, Time of Day and Location Type dimensions, latitude/longitude, **Holidays**, the ISO date dialect, the page 3 decomposition tree, the story bookmark sequence, the narrative visual, four of the five static borough roles; **round 3:** the page 5 ZIP cluster scatter and the page 4 chart/table bookmark toggle; **round 4:** the page 5 monthly column chart (Explain the increase is evidenced in `docs/evidence/` only) | Each listed in §13 |
| Service (tier 1) | v1 is **built** in the service (§2.1), and uses only what building needs: one workspace on a Fabric trial capacity with web modelling on and Git integration to this repo, manual refresh with anonymous credentials, and Test as role for RLS | App, dashboards, alerts, subscriptions, scheduled refresh, workspace roles and item access, RLS groups, promote / certify |

**Development mode is the default, and it covers the whole window.** Parameter `pProfile = "dev"` loads the **1-in-25 sample** (requests whose `unique_key` is divisible by 25; engine-written, committed with the repo) of **both** the 24 window months and the carry-in file. Because a request is either wholly in the sample or wholly out of it, every row-level identity (Fast = naive backlog, the R19/R20 counts, the load reconciliation) holds in dev exactly as in full. The dev profile therefore exercises what the one-month design could not: PY / YoY % and the completeness guard, the FY rollups, and C4 at all 24 month ends, with all six boroughs present for the RLS checks. The twin publishes expected values for **both** profiles. The full profile is loaded only for the full reconciliation, which the plan budgets at **two** full refresh cycles, not one. The dev profile replaced the round-1 one-month profile in round 2; the owner ratifies that change in `docs/decisions.md` before building (PROCESS.md).

### 2.1 Where v1 is built: the browser (round 6)
- **Tools.** The owner builds in a browser on the Mac: Power Query Online, web modelling (model view, DAX, calculated tables and columns, calculation groups, RLS roles), the web DAX query view and web report editing, in a workspace on a **Fabric trial capacity**. Nothing is installed; there is no Power BI Desktop and no gateway. The owner creates the Microsoft tenant and the trials himself; the engine never does (PROCESS.md).
- **Commits.** The workspace is connected to this repo through **Fabric Git integration**, which writes the model as TMDL and the report as PBIR (§3.2).
- **Desktop-only tools and their browser substitutes.** Microsoft documents no web entry point for four Desktop dialogs [research]. Where SPEC used them, it now states the **behaviour** and allows any web implementation (a calculated table or column, or TMDL view on the web):
  - the what-if dialog → the threshold table and its value measure (§5.1, §6.4);
  - the Groups dialog → the Agency Group column (§5.1);
  - bins → the page 7 resolution histogram's bin column (§5.4, §8);
  - View as → **Test as role** in the service (§9.4 step 5).
- **Tools that do not run on a Mac.** DAX Studio is replaced by the Fabric notebook **Memory Analyzer** (model size) and **Performance Analyzer** in web report editing (§11).
- **What stays [likely] until tried** (each is checked in task 1's smoke test or at first use, and logged):
  - gzip decompression in Power Query Online, and a service refresh through GitHub's redirects (§3.2);
  - the web DAX query view's Copy giving a tab-delimited grid with headers (§9.4);
  - web UI for sort-by columns, hierarchies, a not-loaded query and a list-of-values parameter (TMDL view on the web is the fallback);
  - in web report editing: drillthrough setup, the export setting, alt text, tab order and the fx constant line.
  - the service's export of the report to PDF, for the README (Appendix B item 0; round 7).
- **After the trial** (round 7). The committed model and report folders open only in a Fabric workspace or, [likely], in Power BI Desktop on Windows. So the README carries the report itself as six page PNGs and a PDF, taken before the Fabric trial ends (Appendix B item 0), and the reconciliation re-runs from a clone with the vendored CLI and no Power BI (§9.4, Appendix B item 6).

---

## 3. The extract, the files and the manifest

### 3.1 Profiles and counts

| Profile | Window (created) | Window files | Window rows | Carry-in file | Carry-in rows (eligible) |
|---|---|---|---|---|---|
| `dev` (default; committed with the repo) | 2024-09-01 – 2026-08-31 | 24 × `nyc311_s25_YYYY-MM.csv.gz` (10,197 – 13,935 rows each) [twin] | **301,688** [twin] | `nyc311_carryin_s25.csv.gz`: the same key rule applied to the full carry-in file | **8,037** (6,835) [twin] |
| `full` (final run; gitignored, published as release assets) | 2024-09-01 – 2026-08-31 | 24 × `nyc311_YYYY-MM.csv.gz` (389,846,371 bytes gz in total, about 390 MB) | **7,542,606** [twin] | `nyc311_carryin.csv.gz`: created 2023-09-01 – 2024-08-31, with **no valid close before 2024-09-01** | **201,517** (171,302) [twin] |

- **The carry-in rule: no *valid* close before the window start.** A request created in the carry-in period is in the carry-in file unless it has a **valid** close dated before 2024-09-01. Valid here means what R03 means: present, parseable, year ≥ 2020, and on or after the created time. A placeholder close (1900) or a close earlier than the request's own created time therefore does **not** remove a request: it reaches the file, and R03, R07 and R18 then treat it exactly as they treat a window row. Full profile: 1,577 carry-in rows are kept this way [twin], all with a negative close: 1,100 whose status is not Closed (R18: open and eligible; each ages out within the window, by 1 Sep 2025 at the latest, and is stale at the window end) and 477 with status Closed (R07: ineligible). The stale exclusion below uses the same predicate. (The round-4 draft judged the raw close, so it dropped these rows and made carry-in R18 structurally zero; the build changed the rule, and every figure that depends on it changed with it.)
- **The dev sample is representative.** `unique_key` is assigned in creation order, so "divisible by 25" is a systematic sample that spreads evenly over days, agencies and boroughs. Sample × 25 ÷ full, for the five boroughs: 0.998 – 1.010 (Staten Island 11,705 sample rows); UNKNOWN 0.985 (249 sample rows against 252.8 expected: small-count noise, since its sampling standard deviation is about 6%); by month: 0.997 – 1.003 [twin]. The engine asserts the ratios within ±1.5% by month and by borough; UNKNOWN meets that band by only 0.01 percentage points.
- **Stale policy (rolling; R20).** A request that has been open **more than 365 days** is stale: it is not operational backlog. The measures apply this **at every as-of date** (§6.2). The extract applies the same rule once, early, at the window start, only to keep the files small: requests created before the carry-in period with no valid close before the window start are excluded and counted in the manifest's `stale_excluded`. Full profile: **285,164**; dev: 11,432 [twin]. Because it shares the carry-in predicate, the count includes 43,438 old requests whose only close is invalid (42,802 negative, 636 pre-2020), and 8,439 of the 285,164 have status Closed: it counts requests without a valid close by the window start, not only open-status ones. Because the rule is rolling, none of these rows could have counted anyway.
- **Why the rule must be rolling.** Under a one-time cut-off, "open" at a month end would include requests that have since passed 365 days. Their share of all open requests grows from **4.4%** at Sep 2024 (7,539 of 170,554) to **30.25%** at Aug 2026 (84,050 of 277,887: 43,169 carry-in rows plus 40,881 window-created rows) [twin]. The backlog trend and its YoY would then partly measure the widening age range, not the operation.
- **Why so many carry-in rows are ineligible.** 30,215 of the 201,517 full carry-in rows are `Closed` with no valid close date (R07) [twin]: 29,738 with no close at all (R03 `missing`), plus the 477 with a negative close that the carry-in rule keeps. They cannot be placed in time, so they are excluded from backlog.
- **The extract is raw.** It applies a row filter (and, for dev, the key rule) and a column selection only: 19 columns, renamed to the SODA API field names. All cleaning is the owner's Power Query work.

### 3.2 Folder layout the model reads

```
pl300-nyc311/
  NYC311-Operations.pbip                 pointer to the report folder, a few lines   (owner, hand-written; committed)
  NYC311-Operations.Report/              report definition (PBIR)                   (Fabric Git integration; committed from the workspace)
  NYC311-Operations.SemanticModel/       model definition, TMDL (definition/model.tmdl must be tracked; CI checks it)   (Fabric Git integration)
  _design/      SPEC.md, HINTS.md, research-exam.md, research-mac.md, research-data.md   (committed)
                PROCESS.md                                                                (private; gitignored)
  data/dev/     manifest.json, 24 × nyc311_s25_YYYY-MM.csv.gz, nyc311_carryin_s25.csv.gz   (engine; committed)
  data/full/    manifest.json (committed); 24 monthly files and nyc311_carryin.csv.gz (gitignored; release asset data-v1)
  data/reference/  agency_remap.csv, agency_dim.csv, complaint_alias.csv, complaint_category_map.csv,
                   channel.csv, borough.csv, borough_access.csv, sla_benchmarks.csv,
                   sla_baseline_summary.csv                                               (engine; committed, data only)
  checks/dax/   C1–C4.dax, C4r.dax, C5.dev.dax, C5.full.dax, C5b.dev.dax, C5b.full.dax    (engine; committed)
  checks/spec/  C1–C5b.json, C4r.json: key columns and comparison rule per column        (engine; committed)
  expected/<profile>/  C1.csv … C5.csv, C4r.csv, C5b.csv, rule_counts.csv, backlog_facts.csv   (engine; committed)
  theme/        the base theme JSON, with its contrast-check output                       (engine; committed)
  observed/<profile>/  C1.tsv … C5b.tsv (owner pastes), rls_checks.csv                   (owner)
  reconcile/<profile>/reconciliation_results.csv   (reconcile CLI; committed and pushed, because page 10 reads it from GitHub)
  docs/decisions.md    G0 / G1 sign-offs, exposure record, hint/key/twin log, decisions   (owner + lead)
  docs/evidence/       screenshots (spikes, Explain the increase), Performance Analyzer JSON, Memory Analyzer output   (owner)
  docs/screenshots/    one PNG per v1 page (six) and NYC311-Operations.pdf, the report exported from the service; embedded and linked in the README   (owner, before the Fabric trial ends)
  tools/        check_sealed.sh, hooks/pre-commit, hooks/pre-push                         (engine; committed)
  tools/reconcile/     the reconcile CLI, vendored: northledger/pbi.py (+ a one-line __init__.py) and tests/test_pbi_reconcile.py,
                       copied from northledger-core at a logged sha256; Python 3 standard library only   (engine; committed)
  .github/workflows/sealing.yml                                                           (engine; committed)
  answer-key/   ANSWER-KEY.md only                                                        (gitignored, sealed)

pl300-nyc311-engine/   (sibling repo, local-only until v1 is green; NOT in the owner's working copy)
  twin/, tools/ (extract.py, reference.py, cli_selftest.py, tests/), run_tests.sh, RESULTS.md,
  evidence/ (red-first logs and build reports),
  history/ (DESIGN.md, critiques.json, design-plan.json, research-format.md, REVISION-NOTES.md,
            research-data.unredacted.md)
```

**The item names are fixed.**
- The semantic model and the report in the owner's workspace are both named `NYC311-Operations`. The workspace is connected to this repo's `main` branch with the **repo root** as its Git folder. Fabric Git integration therefore writes `NYC311-Operations.SemanticModel/` (TMDL) and `NYC311-Operations.Report/` (PBIR), each with a `.platform` file [research]. That `NYC311-Operations.SemanticModel/definition/model.tmdl` is among the files it writes is [likely]; the first commit in task 1 checks it. The CI job fails if that file is not tracked (PROCESS.md).
- **Fabric commits do not run the local hooks.** The pre-commit and pre-push hooks guard only commits made on the Mac. Commits made from the workspace are checked by the CI job alone, after they are already on GitHub. So nothing sealed may ever be an item in the Git-connected workspace.
- **The `.pbip` file.** Git integration writes no `.pbip` file, and Microsoft calls it optional [research]. The owner hand-writes `NYC311-Operations.pbip` (a pointer to the report folder, a few lines) after the first report commit, so the project also opens in Power BI Desktop on Windows [likely].
- **The copies stay out of Git.** The RLS-free copy for Explain the increase (§8 spike 2) is named `_scratch-insights-no-rls` so that it can never be mistaken for the deliverable. It lives, like the drill's rebuild copy (Appendix C), in a **second workspace that is not connected to Git**, so it can never be committed. The sealing check still flags that name if it ever reaches the repo.

**Where the model reads the files.** Every file is addressed relative to the parameter `pDataBaseUrl` (§3.4), whose default is `https://github.com/rashadul122/pl300-nyc311`: the owner's public repo (round 8). A fork points it at its own copy.

| Files | Path relative to `pDataBaseUrl` |
|---|---|
| dev manifest and the 25 dev files | `raw/main/data/dev/` + file name |
| full manifest | `raw/main/data/full/manifest.json` |
| the 25 full files | `releases/download/data-v1/` + file name (the release assets) |
| reference CSVs | `raw/main/data/reference/` + file name |
| twin rule counts | `raw/main/expected/<profile>/rule_counts.csv` |
| last reconciliation | `raw/main/reconcile/<profile>/reconciliation_results.csv` (absent until the first reconcile run is pushed) |

- **Checked on 2026-09-23** with HEAD requests against a public repo:
  - github.com answers a `raw/<branch>/<path>` address with a redirect to raw.githubusercontent.com, which caches a file for up to 5 minutes (`max-age=300`);
  - it answers a `releases/download/<tag>/<asset>` address with a redirect to a signed release-assets.githubusercontent.com address;
  - a missing path returns HTTP 404.
- **Requirements:**
  - The repo is public, so the source needs anonymous credentials only, and no gateway.
  - The model refreshes **in the Power BI service**, not only in the editor. The service refuses dynamic data sources [research], so the base address stays a fixed parameter value, and each file is addressed relative to it.
  - A service refresh that follows GitHub's redirects is [likely], and so is decompressing gzip in Power Query Online. Task 1's smoke test checks both.
  - A push is not visible to a refresh for up to 5 minutes (the cache above).
- **Secondary source.** If the smoke test fails, the files may instead be uploaded in the browser to the Files area of a Fabric Lakehouse, in the workspace that is not connected to Git, and read from there [unverified]. A Lakehouse is not a Power BI item: when the Fabric trial ends it is kept for only 7 days [research].

### 3.3 `manifest.json` (one per profile folder)
```json
{
  "dataset": "nyc311-erm2-nwe9-snapshot",
  "profile": "dev",
  "window_start": "2024-09-01",
  "window_end": "2026-08-31",
  "sample": "unique_key % 25 == 0",
  "files": [
    {"name": "nyc311_s25_2024-09.csv.gz", "role": "window", "month": "2024-09", "rows": 0,
     "sha256": "…", "bytes": 0, "dialect": "us12h", "source": "snapshot-2026-09-20",
     "as_of": "2026-09-20T01:51:01"},
    "… 23 more window files …",
    {"name": "nyc311_carryin_s25.csv.gz", "role": "carryin", "month": null, "rows": 8037,
     "sha256": "…", "bytes": 0, "dialect": "us12h", "source": "snapshot-2026-09-20",
     "as_of": "2026-09-20T01:51:01"}
  ]
}
```
- `sample` is `null` in the full manifest.
- Both manifests also carry `carryin_created_start`, `carryin_created_end` and `stale_excluded` (full 285,164; dev 11,432; §3.1). Extra top-level keys are allowed; the model reads only `window_start`, `window_end` and `files`.
- **`as_of` is per file.** In v1 every file carries the same value: the snapshot's latest `created_date`, 2026-09-20 01:51:01, NYC local time [measured]. The M must still read `as_of` **per row from its file**. v2 then changes only the data, never the rule (§13.1).
- **Switching profile.** `window_start` / `window_end` drive the Date table's `In Data Window` flag, so changing `pProfile` is the only switch needed.

### 3.4 Parameters the owner creates (1.1.4)

| Parameter | Type | Default | Use |
|---|---|---|---|
| `pDataBaseUrl` | Text | `https://github.com/rashadul122/pl300-nyc311` (round 8) | Base address of every file the model reads (§3.2). Replaces round 5's `pRepoRoot` (a Parallels shared-folder path) |
| `pProfile` | Text, list {dev, full} | `dev` | Chooses the data files and manifest, the expected files and the reconcile file |
| `pWeatherLat` / `pWeatherLon` | Text | `40.7812` / `-73.9665` (Central Park) | Open-Meteo. **Not** 40.7128, −74.0060: the API snaps that to a New Jersey grid cell [research] |
| `pWeatherEnd` | Text | `2026-09-14` | Weather archive end date. A static parameter, deliberately **not** derived from the manifest, so no data read from the repo flows into the weather request |

Parameters are created in the Power Query editor. Their values can be changed later in the semantic model's settings in the service, which is how `pProfile` switches to `full` (§9.4) [research].

### 3.5 Engine-written file schemas (data only; header row, UTF-8, comma-separated)

| File | Columns |
|---|---|
| `agency_remap.csv` | from_code, to_code |
| `agency_dim.csv` | agency, agency_name (every canonical code, plus `UNKNOWN`). agency_name is the most frequent raw name of that code in the extract; for `311` that rule gives "HIQA" (the NYC311-PRD rows) rather than "3-1-1", which the owner reviews in task 3b |
| `complaint_alias.csv` | from_key, to_key (both already normalized by R09). Engine draft reference data, owner-reviewed in task 3b: two **evidence aliases** found in the data, `HAZARDOUS MATERIAL` → `HAZARDOUS MATERIALS` and `BOILER` → `BOILERS`, plus the illustrative `LITTER BASKET/REQUEST` → `LITTER BASKET REQUEST`, which matches 0 rows in v1 (the data already spells it the target way) |
| `complaint_category_map.csv` | complaint_key, category, category_sort. A **superset**: every key found in either role of either profile, plus the 6 keys that occur only in the baseline year (ELECTRONICS WASTE APPOINTMENT, EXECUTIVE INSPECTIONS, SEASONAL COLLECTION, STALLED SITES, SUSTAINABILITY ENFORCEMENT, UNLICENSED DOG), so the baseline summary keys every baseline row; 210 keys. The Complaint dimension is built from extract keys only, so the baseline-only rows never reach the model. Engine draft, owner-reviewed |
| `channel.csv` | channel, channel_group, channel_sort |
| `borough.csv` | borough, borough_sort (6 rows) |
| `borough_access.csv` | user_principal_name, borough (test UPNs: `bk.manager@example.test` → BROOKLYN; `qn.si.manager@example.test` → QUEENS and STATEN ISLAND). They are not users of any tenant, deliberately: a public repo must not carry the owner's tenant user names. §9.4 step 5 says what that means for testing |
| `sla_benchmarks.csv` | category, benchmark_hours, baseline_requests, method. baseline_requests holds the same count as the summary's baseline_valid_rows. **baseline_requests is not loaded** (§10) |
| `sla_baseline_summary.csv` | category, baseline_valid_rows, p50_minutes, p75_minutes, p90_minutes, baseline_start (`2023-09-01`), baseline_end (`2024-08-31`), as_of. Per category, over R05-valid requests created in the baseline year, keyed through R09 and `complaint_category_map.csv`; percentiles numpy `linear`. benchmark_hours = p75_minutes ÷ 60 rounded to the nearest hour (an exact half rounds up), minimum 1, only where baseline_valid_rows ≥ 30. **Not loaded by the model**: it documents the benchmark method, and the engine recomputes it from `big_data.db` |
| `expected/<profile>/rule_counts.csv` | role (`window` = Requests, `carryin` = Opening Backlog), rule_key, rule_id, flag_value, kind (`flag` / `distinct`), description, rows_expected, raw_audit_rows. Layout below |
| `expected/<profile>/raw_audit/<role>/` | The NorthLedger raw audit of each role (`window`, `carryin`): `data-health.json` (the full column profile), `evidence-ledger.json` (every SQL fact with its query, re-run before the temporary table was dropped), `provenance.json` (each file's sha256 and rows checked against the manifest) and `summary.md` (a column table). Every column is read as text, exactly as in the file |
| `expected/<profile>/raw_audit/raw_audit_map.csv` | role, rule_key, audit_fact, audit_condition, separating_cases, raw_audit_rows, note, manifest_sha256. The twin copies `raw_audit_rows` into `rule_counts.csv` and refuses a map whose `manifest_sha256` no longer matches the manifest |
| `expected/<profile>/backlog_facts.csv` | as_of, operational_open, stale_open, stale_share (month ends; feeds the page 3 caption and the Method panel) |
| `reconcile/<profile>/reconciliation_results.csv` | check_id (`C1`…`C5`, `C5b`, `C4r` (opt-in: only in a drill run, §9.4), `L` for load), key, measure, expected, observed, status (`pass` / `fail` / `missing` / `extra`), run_at (ISO). One row **per cell**, so an expected row that is absent from observed shows as `missing` on each of its cells (5 for a C1 row) |

**Reading the reference files.** Every cell passes R01; `agency_remap.csv` codes are upper-cased (R08); a blank `benchmark_hours` means the category has no benchmark; each file's key appears once (the engine asserts it and fails on a duplicate, a missing file or a missing column).

**`rule_counts.csv` layout.** It counts **both roles**, because the carry-in status conflicts (R07: 30,215 of 201,517 carry-in rows [twin]) are a headline data-quality fact.
- **Flag rows** (`kind = flag`): one row per role × flag column × flag value, for the eight flag columns of §5.1 (R02, R03, R05, R06, R07, R12, R13, R18). `rule_key` = `<rule id>|<flag value>` (`R03|negative`, `R07|status_conflict`), `rule_id` = `R03`, `flag_value` = `negative`. `rows_expected` = the number of rows of that role carrying that value. `raw_audit_rows` = the NorthLedger raw audit's count for the **corresponding** condition, filled **only** when the engine has checked, on that profile's rows, that every case separating the two definitions occurs 0 times; otherwise empty (informational, never compared). Equal numbers do not make equal definitions: `expected/<profile>/raw_audit/raw_audit_map.csv` lists, per role and rule key, the audit fact used, both definitions, the separating cases with their counts, and why a row is empty. In v1 this fills `R03|missing` in both roles of both profiles and `R13|missing` in three of the four role-profile pairs. The full profile's window is the exception: 3 ZIPs there are the text `NA` or `N/A` (keys 64727810, 66052994, 68988428), missing to the audit but `invalid` under R13, so the definitions part and that cell stays empty. Every other flag row has no counterpart in the audit and stays empty. **Only non-zero rows are written**, because a zero row would read as a false mismatch.
- **Distinct rows** (`kind = distinct`): per role, two rows for each of R08 (agency), R09 (complaint key) and R17 (channel). `rule_key` = `R08|raw` and `R08|after`; `flag_value` = `raw` or `after`. `raw` = the number of distinct non-null values of the extract column (`agency`, `complaint_type`, `open_data_channel_type`) after R01 only, compared case-sensitively as Power Query compares. `after` = the number of distinct values of the derived column (Agency, Complaint Key, Channel). `raw_audit_rows` is empty. Only `after` rows are compared with Power Query (§6.6); `raw` rows are twin figures and are labelled "(twin)" on page 10.
- **Order:** role, rule_id, kind, flag_value, each sorted as text (so every `carryin` row comes before every `window` row). The key of a row is (role, rule_key).

**Privacy levels and credentials (all sources in §3.2 and §3.4):** both sources, the repo's base address and Open-Meteo, are Web sources with **anonymous** credentials and privacy level **Public**, set in the semantic model's data source credentials in the service, because the data is public NYC data. A Lakehouse source, if used (§3.2), is Organizational. Every query that reads a source must still refresh without a Formula.Firewall error. Record the settings and any Formula.Firewall message in `docs/decisions.md` (1.1.2).

---

## 4. Cleaning rules (outcomes, not code)

Rules apply identically to the window files and the carry-in file, through **one reusable function**; copy-paste is not allowed. The twin implements the same rules independently. Power Query **never drops a row for quality**. It flags the row, and measures exclude flagged rows by rule. The only removals are the extract-level stale exclusion and R16 de-duplication (expected 0).

| Rule | v1? | Outcome required |
|---|---|---|
| **R01** Text hygiene | v1 | Every text field has control characters (Unicode category Cc) removed and then leading/trailing whitespace trimmed. An empty result is null. |
| **R02** Date parsing | v1 | `created_date` and `closed_date` parse from US 12-hour `MM/dd/yyyy hh:mm:ss tt` (culture en-US), naive NYC wall-clock time. A value present but unparseable becomes null and is flagged `created_unparseable` or `closed_unparseable` (column `R02 Parse`). Expected: 0 in v1 [research: 100% conform]. The ISO dialect is v2 (§13.1). |
| **R03** Close validity | v1 | A close is **valid** only if it is present, created is present, its year is ≥ 2020, it is ≥ created, and it is ≤ **the row's own file `as_of`**. Otherwise column `R03 Close` holds the first matching reason: `missing` (no close, or no created) → `pre_2020` (placeholder years such as 1899) → `negative` (before created) → `after_as_of`. `Closed Date` holds the **date** of a valid close only, and is null otherwise. `Closed Valid` = no R03 flag. [twin, full window: missing 197,015; negative 1,896; after_as_of 1; pre_2020 0, in both roles of both profiles] |
| **R04** Resolution minutes | v1 | For valid closes only: whole minutes, rounded down, from created to closed. Null otherwise. |
| **R05** Valid for resolution | v1 | `Valid For Resolution` = close valid **and** 1 ≤ minutes ≤ 525,600, on the **whole minutes of R04**. Flag `R05 Resolution` = `zero` (under 1 whole minute, so a close 1–59 seconds after created is zero: automatic or administrative closes) or `over_1y`. [twin, full window: 7,184,315 valid; zero 151,079; over 1 year 8,300. The round-4 draft figures (7,202,886 / 132,506 / 8,302) used exact durations; on whole minutes, 18,573 closes of 1–59 s are zero and 2 closes at 525,600 minutes plus a few seconds are valid] |
| **R06** Day precision | v1 | A valid close whose time is exactly 00:00:00 is flagged `day_precision` (column `R06 Day Precision`). The row stays valid. DOB closes are 87% day-precision [research]. [twin: 222,316 window] |
| **R07** Status conflict | v1 | Status `Closed` with **no valid close** → flag `status_conflict`. A missing status counts as not Closed (no v1 row has a missing status; §9.3). `Backlog Eligible` = no R07 flag **and** a parseable created date. An ineligible row cannot be placed in time, so it is excluded from backlog (both the open and the exit side). [twin: 16,703 window; 30,215 carry-in] |
| **R08** Agency remap | v1 | Canonical agency code through `agency_remap.csv`: DCA→DCWP, DOITT→OTI, NYC311-PRD→311, 3-1-1→311. Codes are upper-cased; a blank becomes `UNKNOWN`. Every canonical code, including `UNKNOWN`, exists in `agency_dim.csv`. |
| **R09** Complaint key | v1 | Key from the complaint type: R01, then upper-case, then remove apostrophes (`'` and `’`), then collapse runs of spaces to one space, then replace `" / "` with `"/"`. Then apply `complaint_alias.csv` (normalized from-key → to-key; in v1 `HAZARDOUS MATERIAL` → `HAZARDOUS MATERIALS` and `BOILER` → `BOILERS`; the file's `LITTER BASKET/REQUEST` → `LITTER BASKET REQUEST` row is illustrative and matches no v1 row, §3.5). A null result becomes `(NONE)`. **One function** serves Requests, Opening Backlog and the Complaint dimension. It exists because the model compares text case-insensitively and Power Query does not, so `Elevator` (DOB) and `ELEVATOR` (HPD) would collide on the one side [research, likely]. [twin, full window: 205 distinct raw types after R01 (case-sensitive) → 201 after upper-casing → **199 keys**: the apostrophe pair (Building Marshal's Office / Building Marshals office) and the `HAZARDOUS MATERIAL` alias each merge one. Carry-in: 181 → 168 → 167, the `BOILER` alias merging one. Without the two aliases the window figure would be 200] |
| **R10** Descriptor | v1 | Same normalization as R09, without the alias step. `N/A`, `UNSPECIFIED` or null → `(NONE)`. Kept as a **column on Requests**, not as a dimension (§5.1). |
| R11 Location type | v2 | Not loaded in v1. |
| **R12** Borough | v1 | Upper-case. One of BRONX, BROOKLYN, MANHATTAN, QUEENS, STATEN ISLAND; anything else, including `Unspecified` and blank, becomes `UNKNOWN`, which is a real dimension member. Flag `R12 Borough = unknown`. [twin: 6,319 in the window] |
| **R13** ZIP | v1 | Exactly 5 digits and 10000–14999 → kept. Blank → `UNKNOWN` with flag `missing`; anything else → `UNKNOWN` with flag `invalid` (column `R13 ZIP`). ZIP is a **column on Requests** (data category PostalCode); v1 has no ZIP dimension. |
| R14 Latitude/longitude | v2 | **Not loaded in v1.** These are the highest-cardinality columns after Unique Key, and v1 has no map. See 2.3.1 and decisions.md. |
| R15 Council district | v2 | Not loaded in v1. |
| **R16** Unique key | v1 | Whole number. At most one row per key across all loaded files of a role; when duplicates exist, keep the row from the latest `as_of`. Expected duplicates in v1: 0. Window keys and carry-in keys never overlap: the twin asserts it. |
| **R17** Channel | v1 | Upper-case. ONLINE, PHONE, MOBILE and OTHER are kept; blank or `UNKNOWN` → `UNKNOWN`; any other value → `OTHER`. [twin: 591,480 UNKNOWN in the window] |
| **R18** Open with invalid close | v1 | Status is **not** `Closed` (a missing status counts as not Closed), a close value is present, but it is not valid (R03) → flag `open_invalid_close`. **Status wins:** the request is treated as **open** and is eligible for backlog. It is counted on the Data Quality page. Mostly DOT `Pending` rows with negative durations [research]. An **unparseable** close is not "a close value present" here: R02 flags it once (`closed_unparseable`) and R03 treats it as `missing`. [twin: 1,343 window; 1,100 carry-in, all kept by the carry-in rule of §3.1; 0 unparseable closes in v1] |
| **R19** Age at window end | v1 | For every backlog-eligible request **open at the window end** (created on or before it, and no valid close on or before it), **whatever its age**: age = window end − created date, in **whole days between the two calendar dates** (the created time of day is ignored). `Age Band Key`: 1 = 0–7, 2 = 8–30, 3 = 31–90, 4 = 91–365, **5 = over 365 = stale** (outside the operational backlog, R20). **Every other row gets 0, "Not open at window end", never null**: closed on or before the window end, not backlog-eligible (R07, or no parseable created date), or created after the window end. The twin asserts: bands 1–4 together **equal** Open Backlog EOP at the window end; band 5 equals the stale-open count; band 0 equals all remaining rows, so no row has a null key. [twin, full: bands 1–4 = **193,837**; band 5 = **84,050** (43,169 carry-in + 40,881 window-created); total open 277,887. The carry-in part of band 5 includes the 1,100 carry-in R18 rows of §3.1] |
| **R20** Backlog life | v1 | A backlog-eligible request is in the **operational backlog** from its created date until its **exit**. The exit is its valid close date if that is **at most 365 days** after the created date (exit `Closed`); otherwise it is the created date **+ 366 days** (exit `Aged out`), whether or not it closes later. Days are **whole-day differences between calendar dates**, as in R19: a close on day 365 is exit `Closed` whatever its clock time, even when it lasts more than 525,600 minutes (R05 then flags it `over_1y` while R20 says `Closed`; golden row 65583800). Columns `Backlog Exit Date` and `Backlog Exit` hold the exit only when the exit date is **on or before the window end**; otherwise both are null. There is **no lower bound** on the exit date: under the carry-in rule no carry-in row has a valid close before the window start, so no exit falls before 2024-09-01. Ineligible rows: null. Equivalently, a request is in the operational backlog at the end of day D when it is eligible, created on or before D **and on or after D − 365**, and has no valid close on or before D. [twin, full, exits inside the window: Closed 7,283,336 window + 101,695 carry-in; Aged out 48,730 window + 69,607 carry-in. Every one of the 171,302 eligible carry-in rows exits inside the window, the earliest on 2024-09-01] |

**Other decisions stated as outcomes**
- **Right-censoring.** A request created on or before `as_of` − 30 days is a **mature cohort** (Date column `Is Mature Cohort`; compared as dates: created date ≤ the `as_of` date − 30 days, so 2026-08-21 in v1). Resolution KPIs on the Overview use mature cohorts. Resolution statistics cover closed requests only, so they are **optimistic**, especially P90. The card shows the count of requests without a valid close beside the median, and the Method panel says so.
- **DST.** Durations use naive wall-clock time on both sides, so a DST crossing is off by ±1 h identically in M and the twin. This is documented, not a reconciliation risk.
- **Import errors.** Parse failures are caught and flagged (R02), never left as error cells. A diagnostic query `Load Errors` counts error cells **per column on the typed outputs** of Requests and Opening Backlog. It is not loaded, so it never runs during refresh; run it in dev mode. Expected: 0. If it is not 0, the owner replaces errors in the named columns and records why.

- **Parsing and comparison details.** The twin and the owner's Power Query both follow these; each settles a point the rule table leaves open.
  - Text hygiene (R01) comes first: a date that is blank after R01 is absent, not unparseable.
  - A date parses only when its whole text is the US 12-hour form: two-digit month, day, hour (01–12), minute and second, a four-digit year, one space, then AM or PM in either letter case. 12 AM is midnight and 12 PM is noon. Any other present value is unparseable, including an ISO value (v2), a one-digit field and an impossible calendar date.
  - When both dates are unparseable, `R02 Parse` says `created_unparseable`.
  - Every rule after R02 reads the parsed value, so an unparseable close is "no close": its R03 reason is `missing`, it is not "a close value present" for R18, and it is counted once, under R02.
  - R03 `pre_2020` tests the close year only. A close equal to created is valid; a close equal to `as_of` is valid.
  - R05 `zero` means under one whole minute after rounding down (0–59 seconds). R05 and R06 flags exist for valid closes only.
  - R07 and R18 compare the R01-cleaned status with the exact text `Closed`, letter case included; a missing status and any other text (`closed`, `Unspecified`) is not Closed.
  - R08: an agency code that is not in the remap table is kept, upper-cased.
  - R12: a literal `UNKNOWN` borough is flagged `unknown`, like blank and `Unspecified`.
  - R13: only the digits 0–9 count as digits.
  - R19 and R20 compare calendar dates: "age in days" and "days after the created date" are whole-day differences between dates.
  - R19: an R18 row (status wins) has no valid close, so it is open and is banded.
  - R20: an exit is kept for any exit date on or before the window end; there is no lower bound.

---

## 5. Star schema

### 5.1 Tables

**Facts**

| Table | Grain | Rows (full / dev) | Built by the owner as |
|---|---|---|---|
| **Requests** | 1 row per service request created in the window | 7,542,606 / 301,688 [twin] | Power Query: the function applied to the window files |
| **Opening Backlog** | 1 row per carry-in request | 201,517 / 8,037 [twin] | Power Query: **the same function** applied to the carry-in file |
| **Requests Daily** | created date × agency × **complaint type** × borough | **336,894** / **108,103** [twin: 22.4× fewer than detail in full. The figure depends on the two R09 aliases, which merge 53 day × agency × borough groups; without them it would be 336,947]. At type\|descriptor grain it would be 879,418 (8.6×) [twin], which is why the Complaint dimension is at **type** grain | Power Query Group By over Requests (1.3.3, 2.3.3). **Pre-committed switch (§11):** if the projected full refresh is over 30 min, it is built instead as a DAX calculated table from Requests, and 1.3.3 is shown by the DQ Rules group-by alone |
| **Backlog Flow** | date × agency × borough × flow type (`Opened`, `Closed`, `Aged out`), holding a signed count (+ opened, − exits). **Exactly one row per key:** a window exit and a carry-in exit of the same type on the same date, agency and borough are **one** row, not two. Only dates inside the window occur (R20 drops exits after the window end) | **107,468** / **62,716** [twin] (a table that keeps window and carry-in exits apart would have 112,302 / 63,840 rows: 4,834 / 1,124 keys twice) | **DAX calculated table** from Requests and Opening Backlog (2.2.7). Use case: it derives from two loaded tables and avoids a third full re-read of the files (2.1.5). Why the grain is exact: every sum over it is the same either way, but the stated grain, its row count and the VertiPaq figures recorded in §11 describe the table only if each key occurs once |

**Requests Daily usage rule (2.3.3).** Its only measure, Requests (Daily), is correct only where every field in the context is Date, Agency, Complaint or Borough. **In v1 no visual uses it.** It exists to show the reduced-granularity table, its measured size, its equality with the detail count (C1) and its query-time difference (§11). Routing visuals through it automatically needs an aggregation-aware measure; that is a v2 item (§13.2), and docs/decisions.md must say why Desktop's *Manage aggregations* does not apply here (user-defined aggregations need the detail table in DirectQuery; v1 is import-only).

**Dimensions**

| Table | Key | Attributes | Source |
|---|---|---|---|
| **Date** | Date (day) | 2024-01-01 → 2026-12-31 (1,096 rows). Year; Quarter; Month No; Month Name (sort by Month No); Year Month `yyyy-MM` (sorts as text); Fiscal Year `FY2026` (NYC FY starts 1 July) with Fiscal Year No (sort); Fiscal Month No; Day of Week No (Mon = 1); Day Name (sort by Day of Week No); Is Weekend; **In Data Window** (from the manifest); **Is Mature Cohort** (from `as_of`); Temp Max C, Temp Min C, Precip mm, Snow cm (Open-Meteo); Precip Bucket (Dry < 0.2 mm, Light < 5, Moderate < 20, Heavy, Unknown when null) with Precip Bucket Sort. **Marked as date table** | Owner M, with one merge |
| **Agency** | Agency (canonical code, visible) | Agency Name; **Agency Group** (3.3.2): the owner's grouping of the agencies into a few named groups, a column **of the Agency table**, with every agency, `UNKNOWN` included, in exactly one group and no blank group. It is the model-side grouping that Desktop's Groups dialog would make. That dialog has no documented web entry point [research], so any web implementation in the model is allowed (a calculated column, or TMDL view); a column added in Power Query is not the skill | `agency_dim.csv` (no group column in the CSV) |
| **Complaint** | Complaint Key (hidden) | Complaint Type (display), Category, Category Sort, Benchmark Hours. Hierarchy Category → Complaint Type | Owner M: **distinct keys from all extract files of both roles** through the R09 function, then merges with `complaint_category_map.csv` (engine draft, **owner-reviewed**) and `sla_benchmarks.csv`. An unmapped key gets Category `Unmapped` (expected 0) |
| **Borough** | Borough (visible) | Borough Sort | `borough.csv` (6 rows, including UNKNOWN) |
| **Channel** | Channel (visible) | Channel Group (Digital = ONLINE, MOBILE; Phone; Other/Unknown), Channel Sort | `channel.csv` |
| **Age Band** | Age Band Key (hidden) | Age Band (`Not open at window end`, `0-7 days` … `Over 365 days (stale)`), Min Days, Max Days (blank for key 0); Age Band sorted by key. **Meaningful only at the window end** (§6.2) | **DAX calculated table** (6 rows, keys 0–5) |

**Support tables**

| Table | What it is | Visible to borough roles? |
|---|---|---|
| **SLA Threshold Hours** | Threshold table: one whole-number column, also named SLA Threshold Hours, holding 4 to 336 in steps of 4 (84 rows), and the value measure of §6.4 with default 72. Desktop's what-if dialog would generate both; it has no documented web entry point [research], so the owner builds them (a calculated table and a measure, or TMDL view) | yes |
| **Time Calc** | Calculation group (§7) | yes |
| **Borough Access** | UPN → Borough for dynamic RLS; hidden | own rows only |
| **DQ Rules** | One row per role and rule key: Power Query's count of rows per rule and flag value over **both** Requests and Opening Backlog, plus Power Query's distinct counts of Agency, Complaint Key and Channel per role (the `after` rows), **merged** with the twin's `rule_counts.csv` on (role, rule key) so that a rule present on only one side still appears: Role, Rule Key, Rule Id, Flag Value, Kind, Description, Rows Flagged (Power Query), Rows Expected (Twin), Rows (Raw Audit, informational), Mismatch (0/1) | **no** (table permission) |
| **Reconciliation Results** | The last reconcile CLI run, including the `L` (load) rows: check id, key, measure, expected, observed, status, run at | **no** |
| **_Measures** | Measure home table | – |

The manifest is read by staging queries only; v1 loads no manifest table (the load reconciliation is done by the CLI, §9.4).

**Requests / Opening Backlog columns** (identical schema, both produced by one function):
- Unique Key (whole number, summarize none)
- Source File (hidden)
- Created Date (hidden, relationship key)
- Created Hour (whole number, summarize none)
- Closed Date (hidden, valid close only)
- Closed Valid
- Resolution Minutes (whole number)
- Valid For Resolution
- Backlog Eligible
- Backlog Exit Date, Backlog Exit (hidden; R20)
- Status
- Agency, Complaint Key, Borough, Channel, Age Band Key (hidden relationship keys)
- Descriptor
- ZIP (PostalCode)
- Flag columns, hidden, in display folder *Data Quality*: `R02 Parse`, `R03 Close`, `R05 Resolution`, `R06 Day Precision`, `R07 Status Conflict`, `R12 Borough`, `R13 ZIP`, `R18 Open Invalid Close`

Requests also gets the calculated column **Breach Flag** (§5.4).

**Not loaded** in v1: agency_name (taken from the dimension), location_type, city, resolution_action_updated_date (unreliable [research]), community_board, council_district, police_precinct, latitude and longitude. The datetime is split into Created Date and Created Hour; minutes and seconds are dropped after R04 (2.3.1).

### 5.2 Diagram

```
                         Date (marked)                 Age Band (calc table)
              active ┌──────┼──────────────┐                 │ 1
    ┌── created ─────┘      │ active       │ active          │
    │   (inactive: closed)  │              │                 ▼ *
    ▼ *                     ▼ *            ▼ *        ┌───────────────┐
┌─────────────┐    ┌───────────────┐ ┌──────────────┐ │   (also to    │
│  Requests   │    │ Requests Daily│ │ Backlog Flow │ │ Opening Backlog)
│ 1 row/req   │    │ day×agcy×type │ │ day×agcy×boro│ └───────────────┘
│ (window)    │    │ ×borough      │ │ ×flow (calc) │
└─────────────┘    └───────────────┘ └──────────────┘   ┌─────────────────┐
  * │ * │ * │ * │     * │ * │ * │         * │ * │        │ Opening Backlog │
    │   │   │   │       │   │   │           │   │        │ 1 row/carry-in  │
    ▼   ▼   ▼   ▼       ▼   ▼   ▼           ▼   ▼        └─────────────────┘
 Agency Complaint Borough Channel   (the same dims)      * to Agency, Complaint,
   1       1        1       1                              Borough, Channel, Age Band
                    ▲                                      (no Date relationship)
                    │ RLS filter enters here and flows to every fact
```

### 5.3 Relationships
All are **many-to-one, single direction, active** unless stated. There are **no bidirectional and no many-to-many** relationships (2.1.3), and no path between two facts.

| From (many) | To (one) | Active | Why |
|---|---|---|---|
| Requests[Created Date] | Date[Date] | yes | the "created" role |
| Requests[Closed Date] | Date[Date] | **no** | **Role-playing date** (2.1.2), activated only inside measures |
| Requests[Agency] / [Complaint Key] / [Borough] / [Channel] / [Age Band Key] | Agency / Complaint / Borough / Channel / Age Band | yes | – |
| Opening Backlog[Agency] / [Complaint Key] / [Borough] / [Channel] / [Age Band Key] | same five | yes | So **both parts** of the backlog respond to the same five dimensions. Opening Backlog has **no** Date relationship: its created dates fall before the window |
| Requests Daily[Created Date] / [Agency] / [Complaint Key] / [Borough] | Date / Agency / Complaint / Borough | yes | Conformed dimensions |
| Backlog Flow[Date] / [Agency] / [Borough] | Date / Agency / Borough | yes | – |

Disconnected: SLA Threshold Hours, Time Calc, Borough Access, DQ Rules, Reconciliation Results. `_Measures` has no rows.

**Referential integrity requirement:** on every **active** relationship whose key is populated, no fact row may land on a dimension's blank member. Invalid values map to explicit members instead: `UNKNOWN` borough, agency and ZIP, `(NONE)` complaint, and Age Band key 0 ("Not open at window end") for every row R19 does not band. Backlog Flow dates all fall inside the window, so they always exist in Date. Check C3 counts unmatched Complaint rows and must return blank; C1, C2 and C3 would show a blank Borough, Channel or Agency row as an "extra" key. **Two stated exceptions:**
- **Requests[Closed Date]** (the inactive, role-playing key) is null for every row without a valid close (every R03-flagged row: 198,912 in the full window). When a measure activates that relationship, those rows attach to Date's blank member; Requests Closed removes them with its data-window condition (§6.1).
- **An R02 `created_unparseable` row** would have a null Created Date and so sit on Date's blank member through the active relationship. v1 has none; C1 (its totals) and the `L` load rows would expose one.

### 5.4 Properties, calculated column and calculated tables
- **Hidden:** every fact-side key, the flag columns, Source File, the Backlog Exit columns, Borough Access and the Complaint Key. Staging queries, functions and parameters are **not loaded** (1.3.10).
- **Sort-by:** Month Name → Month No; Day Name → Day of Week No; Fiscal Year → Fiscal Year No; Borough → Borough Sort; Channel → Channel Sort; Category → Category Sort; Age Band → Age Band Key; Precip Bucket → Precip Bucket Sort.
- **Hierarchies:** Date: Year → Quarter → Month Name → Date. Date: Fiscal Year → Fiscal Month No → Date. Complaint: Category → Complaint Type.
- **Data categories:** Requests[ZIP] = PostalCode. Borough is left uncategorized: "StateOrProvince" would be wrong, which is worth one interview sentence.
- **Summarize none** on Unique Key, Created Hour, Year, Month No, Fiscal Year No, Age Band Key and Benchmark Hours.
- **Formats:** counts `#,##0`; hours `#,##0.0`; percentages `0.0%`; YoY % `+0.0%;-0.0%;0.0%`.
- **Model settings:** culture en-US; auto date/time **off**; `discourageImplicitMeasures` (forced by the calculation group; see the §8 page 5 spike).
- **Display folders:** Volume, Backlog, Resolution, Service Benchmark, Ranking, Data Quality, Labels.

**Calculated column `Requests[Breach Flag]`** (whole number):
- 1 = breached, 0 = met, BLANK = not assessable.
- Assessable means Valid For Resolution **and** the request's category has a benchmark.
- Breached means Resolution Minutes > Benchmark Hours × 60.
- Use case (2.1.5): a row-level comparison against a dimension attribute, which is cheap as a column. The alternative is a 7.5M-row Power Query merge. It also gives Key Influencers a numeric row-level target (§8, page 5).

**Two more calculated columns, each replacing a Desktop dialog (§2.1):**
- `Agency[Agency Group]` (§5.1).
- `Requests[Resolution Minutes (bins)]` (whole number, summarize none; page 7): the 1-day bin that Desktop's bins would give Resolution Minutes, that is, the lower edge of the 1,440-minute bin the row falls in (0, 1,440, 2,880 …), and BLANK where Resolution Minutes is BLANK. Any web implementation in the model is allowed.

**Calculated tables:**
- `Backlog Flow` (§5.1): opened counts from eligible window requests at their created date; exit counts from eligible requests (window **and** carry-in) at their R20 exit date, typed `Closed` or `Aged out`; one row per date × agency × borough × flow type, so window and carry-in exits that share a key are summed into one row.
- `Age Band` (6 rows: key 0 "Not open at window end", bands 1–4, and band 5 "Over 365 days (stale)")
- `SLA Threshold Hours` (the threshold table, §5.1)
- `Requests Daily`, only if the §11 refresh projection triggers the switch

---

## 6. Measure catalogue (definition + required behaviour; no DAX)

**23 owner-written measures**, plus the threshold value measure (§6.4). Desktop's what-if dialog would have generated that one; the browser build writes it by hand, and it is still not counted in the 23. The "Required behaviour" column says what must be true of the result: which filters it respects, when it is BLANK or 0, and (where the design fixes it) which relationship it must use. How to achieve it is the owner's work; HINTS.md (Tier 1) names the concept and the trap.

Conventions that apply to every measure:
- **BLANK means "no data or not applicable". 0 means "counted, and none".** Each row says which one applies.
- **The data-window cap.** Measures plotted on a date axis return **BLANK for dates after the last in-window date** (2026-08-31 in both profiles), and stock measures return BLANK before the window start. The window must come from `Date[In Data Window]` (the manifest), **not** from the fact tables, so it cannot move under RLS.
- **A measure's own row condition never replaces a filter; it intersects with it.** Where a measure restricts rows by a column (Closed Valid, Valid For Resolution, Breach Flag, Is Mature Cohort, Channel), an existing filter on that same column still applies. A visual filtered to Closed Valid = True shows BLANK for Requests Without Valid Close, not the unfiltered count; one filtered to Valid For Resolution = False shows BLANK for the median.
- **(TC)** marks the measures the calculation group transforms: Requests, Requests Closed, Open Backlog EOP, Median Resolution Hours (Mature). Under every Time Calc item a (TC) measure must return that item applied to **itself**. A (TC) measure may not refer to another measure. HINTS H4 explains the trap this rule avoids.
- **What is reconciled under the items, stated exactly.** Only **Requests** is reconciled under FYTD, PY and YoY % (C1). The other three (TC) measures are reconciled under **Current** only (C2, C3, C4). The page 1 matrix shows Open Backlog EOP and Median (Mature) under PY and YoY %, and nothing shows Requests Closed under an item in v1; showing a value is not checking it. So the README quotes no PY or YoY % figure for those three: a backlog trend is quoted from C4's reconciled month-end values instead (§7, Appendix B).

### 6.1 Volume

| Measure | Definition | Required behaviour | BLANK / 0 | Format | Check |
|---|---|---|---|---|---|
| **Requests** (TC) | Number of requests created in the filter context | Responds to every dimension and to direct filters on Requests columns (2.2.1) | BLANK when none | `#,##0` | C1, C2, C3 |
| **Requests (Daily)** | The same count read from Requests Daily | Equals Requests wherever the context uses only Date, Agency, Complaint and Borough. Hidden. **Usage rule (§5.1): on no v1 visual.** Not on the Time Calc whitelist, so it must be BLANK under FYTD, PY and YoY % (C1 tests this) | BLANK when none | `#,##0` | C1 |
| **Requests Closed** (TC) | Requests **created in the window** whose **valid** close date falls in the date context **and inside the data window** | A date on the axis means the **close** date: the measure must use the **inactive Closed Date relationship** (2.1.2). Closes after the last in-window date are never counted. Carry-in closures are not included (they are backlog exits) | BLANK when none | `#,##0` | C2 |
| **Requests Without Valid Close** | Requests in context with no valid close (R03 flagged: still open, or a missing, pre-2020, negative or after-`as_of` close). These are excluded from the resolution statistics, and so are the R05 `zero` and `over_1y` rows, which this count does not include | Respects every filter; its Closed Valid condition intersects with any filter on Closed Valid | BLANK when none | `#,##0` | C3 |
| **Digital Share** | Share of requests in context that came through ONLINE or MOBILE | With a Channel filter already on the context, the digital count must stay **inside** it: Channel = PHONE gives **0%**, Channel = ONLINE gives **100%**, never a digital ÷ phone ratio | BLANK when Requests is BLANK; 0% when requests exist but none are digital | `0.0%` | C2 (every channel row) |

### 6.2 Backlog (semi-additive, 2.2.5)

Backlog is a **stock**. It sums across agencies, boroughs, complaints and channels, and takes the **last date** across time. It counts the **operational** backlog: requests open **no more than 365 days** at the as-of date (R20). Stale requests are reported separately in the Method panel (§8), never silently added.

| Measure | Definition | Required behaviour | BLANK / 0 | Format | Check |
|---|---|---|---|---|---|
| **Open Backlog EOP** (TC; the "naive" definition) | At the as-of date D: backlog-eligible requests from **both** Requests and Opening Backlog that were created on or before D **and on or after D − 365**, and were not validly closed on or before D. D = the last date in the filter context, **capped at the last in-window date** | **Responds to** Date, Agency, Borough, Complaint, Channel and Age Band. **Returns BLANK** when a Requests or Opening Backlog column is filtered directly (Status, ZIP, Descriptor, flags): only one of its two parts could honour that filter. A month, quarter or FY cell shows the value at that period's last in-window date | BLANK when the context's first date is after the last in-window date, or the capped D is before the window start. Inside the window it is **a number, 0 when nothing is open** (a stock is zero, not unknown) | `#,##0` | C4 |
| **Open Backlog EOP (Fast)** | **Identical value** to Open Backlog EOP in **every** context | Wherever Backlog Flow can answer the context (Date, Agency, Borough only), it must be computed from Backlog Flow: the eligible carry-in opening balance plus the signed flows up to the capped D. In any context Backlog Flow cannot answer, it must still return the naive value. That includes a filter on a **Backlog Flow column** (for example Flow), which Backlog Flow would honour and the naive measure cannot, and a filter on a Requests Daily column. Used for the Performance Analyzer comparison (2.3.2) and on the page 3 agency line | as Open Backlog EOP | `#,##0` | C4 (equality columns, including under a Channel filter) |
| **Backlog Inflow** / **Backlog Outflow** | Eligible requests opened / eligible exits (R20 `Closed` **and** `Aged out`, window **and** carry-in) per in-window date in context. Outflow is shown as a positive number | For every in-window date: carry-in opening + running Inflow − running Outflow = Open Backlog EOP. In a context Backlog Flow cannot answer (a Complaint, Channel or Age Band filter, or a filter on a Requests, Opening Backlog or Requests Daily column) they return **BLANK**, not a wrong number | BLANK when none, or when the context cannot be answered | `#,##0` | – (the page 3 matrix; visual calculations derive net and running net) |

**Age Band is meaningful only at the window end.** Age Band Key is each request's age on 31 Aug 2026 (R19). Under an Age Band filter, Open Backlog EOP at any other date counts the requests that are in that band **at the window end**, which is not an age view of that date. So Age Band is used on one visual only, the page 3 age chart, which is fixed to 31 Aug 2026 and cross-filters nothing (§8).

**Equality requirement:** Fast = naive at every date, in every combination of Date × Agency × Borough, and in every other context.
- **Why they can differ in principle:** both the opened side and the exit side must count **only eligible** rows (otherwise a status-conflict row is opened and never exits, and Fast drifts upward: the old design's bug), and a request must leave the Fast balance **exactly once**, either when it closes within 365 days or when it ages out, never both.
- **Two independent tests:**
  - the twin asserts equality at **every day** and every month end, overall and by agency × borough, in both profiles;
  - C4 asserts it in the owner's model at every month end, by borough, with and without a Channel filter.

### 6.3 Resolution (2.2.4)

| Measure | Definition | Required behaviour | BLANK / 0 | Format | Check |
|---|---|---|---|---|---|
| **Median Resolution Hours** | Median Resolution Minutes ÷ 60 over Valid For Resolution rows | Respects every filter; its Valid For Resolution condition intersects with any filter on that column | BLANK when no valid rows | `#,##0.0` | C3 |
| **P25 / P75 / P90 Resolution Hours** | The same, at percentiles 0.25 / 0.75 / 0.90, **inclusive** interpolation (equal to numpy `linear`) | As the median. An empty set must give BLANK, never an error or 0 | BLANK when no valid rows | `#,##0.0` | C3 |
| **Median Resolution Hours (Mature)** (TC) | Median over valid rows whose created date is a mature cohort | Both conditions must **intersect** with existing filters: a visual filtered to Is Mature Cohort = False, or to Valid For Resolution = False, must return BLANK, not the mature median | BLANK when none | `#,##0.0` | C3 |

### 6.4 Service benchmark and what-if

| Measure | Definition | Required behaviour | BLANK / 0 | Format | Check |
|---|---|---|---|---|---|
| **Benchmark Eligible Requests** | Rows with a non-blank Breach Flag | – | BLANK when none | `#,##0` | C3 |
| **SLA Met % (Benchmark)** | Breach Flag = 0 rows ÷ eligible rows | A row whose Breach Flag is BLANK must never count as met. Its Breach Flag conditions intersect with any filter on Breach Flag | **BLANK when no eligible rows; 0% when eligible rows exist but none met** | `0.0%` | C3 |
| **SLA Breach Rate** | Breach Flag = 1 rows ÷ eligible rows | Computed from breaches, not derived from Met % | **BLANK (never 100%) when no eligible rows; 0% when none breached** | `0.0%` | C3 |
| **SLA Threshold Hours Value** | The selected threshold hour, default 72 | The value measure of the threshold table (§5.1), hand-written in the browser build; not counted in the 23 | 72 when none or several are selected | `0` | C3 (default) |
| **SLA Met % (What-if)** | Valid rows with minutes ≤ threshold × 60 ÷ valid rows | Follows the threshold slicer; its Valid For Resolution condition intersects with any filter on that column | BLANK when no valid rows; 0% when none met | `0.0%` | C3 (at the 72 h default) |

### 6.5 Ranking and labels

| Measure | Definition | Required behaviour | BLANK / 0 | Check |
|---|---|---|---|---|
| **Agency Rank (Median Resolution)** | Dense rank, fastest = 1, of Median Resolution Hours (Mature) among the agencies **visible in the visual** (respecting slicers) **that have a value** | An agency with a BLANK median gets no rank and **must not shift** anyone else's rank; ties share a rank and the next rank follows without a gap | BLANK outside an agency row (subtotals, cards), and for an agency whose median is BLANK | C3 |
| **Drillthrough Label** | "See detail for <Complaint Type>" when exactly one type is in context, else "Select a complaint type" | – | – | – |

### 6.6 Data quality and reconciliation (page 10; City Operations only)

| Measure | Definition | BLANK behaviour |
|---|---|---|
| **Rule Mismatches** | Number of DQ Rules rows, **both roles**, where Rows Flagged (Power Query) ≠ Rows Expected (Twin): every `flag` row, and the `distinct` `after` rows. A missing side counts as a mismatch. `distinct` `raw` rows are twin-only and never compared | **BLANK when the DQ Rules table is empty to the viewer** (borough roles), never "0 mismatches" |
| **Reconciliation Pass Rate** | Share of Reconciliation Results rows with status `pass` (checks and `L` rows) | BLANK when there are no results |
| **DQ Access Note** | "Data-quality and reconciliation detail is shown to City Operations only." when DQ Rules is empty to the viewer | BLANK otherwise |

---

## 7. Calculation group `Time Calc` (2.2.8)

**Structure:** column `Time View`, sorted by `Ordinal`; precedence 1.

**Items, in this order:**
1. **Current:** the measure unchanged.
2. **FYTD:** fiscal year to date, with year end 30 June, **capped to the data window**: the dates from 1 July of the fiscal year that contains the context's last date up to that last date, intersected with the data window. It returns **BLANK when the context's first date is after the last in-window date**, so a Sep–Dec 2026 month never shows the Jul–Aug 2026 total. At the grand total it gives FY2027 to date (Jul–Aug 2026), as year-to-date does at any total. **Stock rule (unchanged):** for Open Backlog EOP it returns the measure unchanged, because a closing balance is already "to date"; the measure's own window cap then gives BLANK after the window.
3. **PY:** the same period one year earlier. It must use the context's dates **clipped to the data window**, so a partial current period is compared with the same partial period.
4. **YoY %:** (current − PY) ÷ PY, with format string `+0.0%;-0.0%;0.0%`. **BLANK when PY is BLANK or 0** (a stock such as Open Backlog EOP can be 0; the counts are BLANK, not 0, when there is nothing). A BLANK current with a non-zero PY counts as 0, so it gives −100%.

(The absolute YoY item is v2; it adds nothing the owner cannot already show.)

**Completeness guard for PY and YoY % (required):**
- The item returns a value only if the clipped current period, shifted back 12 months, starts **on or after the window start**. Otherwise it returns BLANK.
- Consequences (both profiles; they share the window):
  - **BLANK:** months Sep 2024 – Aug 2025; FY2025; FY2026, whose prior year FY2025 is partial; the grand total. Also BLANK, having no in-window dates: months Jan–Aug 2024 and Sep–Dec 2026, and FY2024.
  - **Valid:** months Sep 2025 – Aug 2026; FY2027 (Jul–Aug 2026 vs Jul–Aug 2025).
  - **Calendar years** follow the same rule (calendar 2024 and 2025 BLANK; calendar 2026 valid, Jan–Aug vs Jan–Aug). This is specified, but **not reconciled in v1**: C1 groups by fiscal year and month, and v1 has no calendar-year visual.
- **The guard deliberately blanks backlog YoY at FY2026.** The guard is one rule, judged on the period's start, for all four (TC) measures. So at FY2026 the page 1 matrix shows BLANK for Open Backlog EOP under PY and YoY %, although both balances (30 Jun 2026 and 30 Jun 2025) lie inside the window. This is chosen, not overlooked: one rule keeps the item logic single, and C1 reconciles it with Requests. The like-for-like stock comparison at that date is still shown, at the month Jun 2026, whose shifted period starts inside the window.
- **Requests Closed under PY is not like-for-like in the first valid months.** Requests Closed counts closes of window-created requests only (§6.1). In the base months just after the window start, many closes belong to carry-in requests, which it leaves out: 14.0% of Sep 2024's closes, 4.4% of Oct 2024's and 2.4% of Nov 2024's [measured]. The guard marks Sep 2025 valid, so its PY is understated and its YoY % overstated by about 16 points; the same bias, shrinking as the base month moves away from the window start, reaches the later months and the FY2027 row. v1 keeps Requests Closed on the whitelist so that the four (TC) measures stay one set, but **no v1 visual or check shows it under an item, and the README quotes no Requests Closed PY or YoY %**. A close-side guard is v2.
- **Whitelist:** items other than Current apply only to the (TC) measures and return BLANK for any other measure. Two reasons. The item logic (the clip to the window, the completeness guard, the FYTD cap) is specified for the four (TC) measures, and reconciled for Requests (C1; §6). And some measures do not respond to Date at all (the labels, and the DQ and reconciliation measures), so an item would show their current value under a "PY" or "FYTD" heading. C1 proves the whitelist with Requests (Daily), which is not on the list.
- **Backlog YoY is like-for-like.** Because R20 is rolling, the backlog at Aug 2026 and at Aug 2025 are both "open at most 365 days". [twin, full: 193,837 vs 139,405 = +39.0%, the C4 month-end values summed over boroughs; the un-aged count would have said +47.7% (277,887 vs 188,176)]. The README cites this from C4's month ends, which are reconciled, not from the PY item, which is not reconciled for this measure (§6).

---

## 8. Report (v1): pages as specifications

The owner builds every page in web report editing in the Power BI service; the engine supplies only a base theme JSON (`theme/`, §3.2) with contrast checked at ≥ 4.5:1, and the check's output is kept with it. Canvas 16:9. The **Date range and Borough slicers are synced** across pages 1, 3, 4 and 5. Page 10 is **not** synced to Borough.

| # | Page | Must contain | Skills |
|---|---|---|---|
| 1 | **Overview: "How is 311 doing?"** | **Cards:** <br>• Requests <br>• Open Backlog EOP <br>• Median Resolution Hours (Mature), with the reference label Requests Without Valid Close, labelled "no valid close" <br>• SLA Met % (Benchmark), labelled "vs Sep 2023 – Aug 2024 baseline", visual filter Is Mature Cohort = True <br><br>**Daily line of Requests with anomaly detection:** no legend and no other analytics lines, as the visual requires. Explain-by fields: Borough, Category, Channel, Precip Bucket, Day Name. <br><br>**KPI matrix:** rows Fiscal Year; columns Time Calc (Current, PY, YoY %); values Requests, Open Backlog EOP and Median (Mature). The Date slicer's interaction with the matrix is **none**, so its rows are always whole fiscal years (FY2024 and the Sep–Dec 2026 part of FY2027 hold no window data). With the Borough slicer cleared, its Current Requests cells are the **RLS Test-as-role target** (§9.4). <br><br>**Q7 channel visual:** a small line of Digital Share by Year Month, titled "Q7: share of requests made online or by mobile". <br><br>A text box "Data through 31 Aug 2026 (snapshot as of 20 Sep 2026)" (v1 is frozen). Page navigator. **Bookmark:** Reset filters, on a button. **Selection pane:** the four cards grouped as a named group, and the layer order and tab order set. (The mobile layout is cut in round 6: it is v2, §13.2.) | 3.1.1, 3.1.2, 3.1.6, 3.2.1, 3.2.3, 3.2.4, 3.2.7, 3.3.5, 2.2.8 in use |
| 3 | **Backlog** | **Line:** Open Backlog EOP by date, no legend, with **Forecast** (30 days) in the Analytics pane. The window cap is what makes the forecast start from real data. <br>**Line:** Open Backlog EOP (Fast) by Agency, Top 5 by the measure. <br>**Matrix:** Year Month × Backlog Inflow / Backlog Outflow, with **visual calculations** Net = Inflow − Outflow and Running Net = running sum of Net. <br>**Column:** Open Backlog EOP by **Age Band** (bands 1–4), visual filter Date = 2026-08-31, and the Date slicer's interaction with this visual set to **none** (3.2.3); **its outgoing interactions to every other page 3 visual set to none** as well, because Age Band is meaningful only at the window end (§6.2); title "Operational backlog by age, 31 Aug 2026". <br>**Caption** under it, typed from `backlog_facts.csv` (full profile): "City-wide, full profile, not filtered by borough or slicers: a further 84,050 requests (30.2% of everything open) had been open more than 365 days and are outside the operational backlog (rule R20)." <br>**Text:** which filters each backlog measure respects (§6.2) | 2.2.5 in use, 3.1.11, 3.2.3, 3.3.2, 3.3.4 |
| 4 | **Resolution & Benchmark** | **Bar:** Median Resolution Hours by Agency, with **error bars P25–P75** and a **constant line bound to SLA Threshold Hours Value** (fx). <br>**Threshold slicer** on SLA Threshold Hours (one value at a time) and an SLA Met % (What-if) card. <br>**Matrix** Agency × Borough of SLA Met % (Benchmark) with **conditional formatting**: rules with icons + text, never colour alone; data bars on Benchmark Eligible Requests. <br>**Table:** Agency, Median (Mature), Agency Rank. <br>**Bar:** SLA Breach Rate by Complaint Type, plus a **drillthrough button** whose label is the Drillthrough Label measure and whose destination is page 7. <br>**Edited interactions:** the cards do not cross-filter from the bar. <br>**Custom tooltip fields** on the median bar: P90, Requests, Requests Without Valid Close <br>(The round-2 chart/table bookmark toggle is cut in round 3; it is v2, §13.2.) | 3.1.5, 3.2.2 (partial), 3.2.3, 3.2.8, 3.3.4 |
| 5 | **Drivers (AI)** | **Key Influencers**. Plan A′: analyze **Requests[Breach Flag]**, analysis type Continuous, explained by Channel, Borough, Agency Group, Day Name, Is Weekend, Precip Bucket, Created Hour. Record that Key Influencers samples its input. <br>**Decomposition tree** on Requests with **AI (high value) splits**. <br>**Agency Group** (§5.1), the model-side grouping that stands in for Desktop's Groups dialog <br>(The round-2 ZIP cluster scatter is cut in round 3; clustering is v2, §13.2. The monthly column chart that existed only for the Explain-the-increase screenshot is cut in round 4: that evidence is made on the RLS-free copy and kept in `docs/evidence/`, spike 2. Digital Share moved to page 1 as the Q7 visual.) | 3.3.2 (groups), 3.3.3; 3.3.1 on the RLS-free copy (spike 2) |
| 7 | **Complaint Detail** (drillthrough; hidden) | Drillthrough field Complaint[Complaint Type], "keep all filters" on, back button. <br>Top 10 descriptors. Monthly trend. <br>**Resolution histogram** of Requests by `Resolution Minutes (bins)` (1-day bins, §5.4; the browser stand-in for Desktop bins), bins in numeric order, visual filter Valid For Resolution = True. <br>Request table: Unique Key, Created Date, Closed Date, Status, Agency, Borough, Channel. **No address** | 3.1.9, 3.2.8, 3.3.2 |
| 10 | **Data Quality & Method** | **DQ Access Note** (for borough roles). <br>**Rule table** from DQ Rules (`flag` rows): Role (window / carry-in), Rule Id, Flag Value, Description, Rows Flagged (Power Query), Rows Expected (Twin), a mismatch icon, and the raw-audit figure as a grey **informational** column (the audit is written independently of R01–R20, so it is never compared). A blank cell means the audit has no corresponding measure, or the engine could not show the two definitions agree on this profile; the page says so and points to `raw_audit_map.csv`, and a tooltip may carry its note. <br>**Key consolidation table** (the `distinct` rows, per role: R08 agencies, R09 complaint keys, R17 channels): Raw (twin), After (twin), After (Power Query) and a mismatch icon. The column headers say which side produced each number. <br>**Load reconciliation** per file: the `L` rows of Reconciliation Results. **Reconciliation Pass Rate** and the last run. <br>**Flag drill:** a table of Requests with slicers on the flag columns. **Method panel:** as_of and window; the dev sample rule; benchmark ≠ SLA, and **the benchmark hours are an engine-provided input** from the baseline year, documented in `sla_baseline_summary.csv`; censoring (the resolution statistics are optimistic, P90 most; they exclude requests with no valid close **and** the R05 zero-minute and over-1-year rows); day-precision and zero-minute closes; **staleness (R20), headed "city-wide, full profile, not filtered by borough or slicers": the backlog counts requests open at most 365 days; the stale share of everything open rose from 4.4% (Sep 2024) to 30.2% (Aug 2026); the carry-in holds requests created Sep 2023 – Aug 2024 with no valid close before 1 Sep 2024; 285,164 older requests with no valid close by then were excluded at extract; 6,319 window requests have an UNKNOWN borough**; what v1 does not show (Copilot, automatic page refresh, Service features); the authorship statement (§0.1), verbatim: "AI-built, owner-directed: the Power Query, model, measures, RLS and report were written by AI (Claude) from a specification the owner directed; the numbers are checked against an independent Python twin with the reconcile CLI." | Q8; 1.2.x in the open |

**Across all v1 pages:**
- **Alt text** on every visual, dynamic where useful; tab order set; no information carried by colour alone (3.2.12).
- **Export setting:** "summarized data only" (report setting; the tenant side is v2) (3.2.9).
- **Theme:** apply the base theme and customize it (3.1.4).
- **Page configuration:** backgrounds, the drillthrough page type, hidden page 7 (3.1.9).
- **Sorting** set on visuals (3.2.5).

**Three day-1 spikes, recorded in `docs/decisions.md` with screenshots:**
1. **Key Influencers vs the calculation group.** Build the page 5 Key Influencers (Plan A′, numeric Breach Flag) **before** adding Time Calc, then after.
   - If Plan A′ is blocked: try Plan A, the measure SLA Breach Rate with Expand-by fields.
   - If both are blocked, **Plan B:** keep Time Calc on a documented branch, and replace the page 1 matrix with explicit PY / YoY % measures, stated honestly.
2. **Explain the increase on an RLS-free copy.** Microsoft's insights documentation lists "RLS or OLS enabled data models" as unsupported [examiner, from desktop-insights, updated 2026-09-18].
   - Make a copy of the model named `_scratch-insights-no-rls` in the workspace that is **not** connected to Git (§3.2), and delete all its roles. How to copy a model authored in the browser is [unverified]: a deployment pipeline, the Fabric item-definition API, or rebuilding in the copy only what the chart needs; PROCESS.md lists the options. In the copy, add a monthly column chart of Requests and run Analyze → Explain the increase on it. Screenshot it to `docs/evidence/`. The committed report carries no chart for this.
   - If the calculation group also blocks insights, delete it in the copy and record that. **Unverified until run.**
   - v2 note: insights are also unsupported in reports distributed as an **app**.
3. **Decomposition tree AI splits** work on Requests (page 5). v1 has no backlog decomposition tree.

---

## 9. Check queries and reconciliation

### 9.1 What is checked, and what the check replaces
Five DAX queries, saved as `checks/dax/C1.dax` … `C4.dax` plus per-profile `C5` / `C5b` files, and the drill variant `C4r.dax`. They contain **measure names, dimension columns and plain filters only; no measure logic**. The owner pastes each one into the **web DAX query view** (the semantic model's "Write DAX queries" in the service; it needs write permission and the workspace setting that lets users edit data models in the service [research]). The web view returns at most 99,999 rows per query [research]; the largest check, C1, has 984. The twin writes `expected/<profile>/Cn.csv` for **both** profiles, and **every check runs in dev**.

| Check | Replaces (old design) | Proves |
|---|---|---|
| **C1 Volume & time intelligence** | Q02 / Q02b, **plus** the partial-period rows of Q07 and the Q10 aggregate equality | Fact load and relationships; Requests (Daily) = Requests at its grain; Time Calc FYTD (with its window cap), PY and YoY %; the **completeness guard**, through rows whose values are all BLANK (the constant "Check Row" makes every fiscal year, month, borough and Time View combination appear); the **whitelist** (Requests (Daily) BLANK under FYTD, PY and YoY %). The per-month totals feed the load reconciliation of the window files. FY Current rows per borough are the **RLS Test-as-role targets**. Calendar years are not checked (§7) |
| **C2 Flows by channel** | Q03 | Closures on the inactive relationship, inside the window; Digital Share at 0% / 100% on single-channel rows |
| **C3 Resolution & benchmark by agency** | Q04, **plus** Q05 (benchmark, what-if default), Q09 (blank-safe rank) and the RI part of Q12 | Statistics with inclusive interpolation; BLANK-safe Met % and Breach Rate; the rank ignoring blank agencies; zero unmatched Complaint rows; the carry-in row count for the load reconciliation |
| **C4 Backlog at month ends** | Q06 | Naive = Fast at every month end and borough, also under a Channel filter; the rolling age limit (the values are the operational backlog); BLANK before the window and after the last data date |
| **C5 Golden rows** (C5 over Requests, C5b over Opening Backlog) | Q13 | Row-level Power Query (R01–R20) and the Breach Flag column on 33 real unique keys (§9.3) |

Dropped for v1: Q01 (rule counts; now compared **inside** the report by DQ Rules), Q08 (rolling 28D and z-score; v2), Q10b (the aggregation-aware fallback; the measure is v2), Q11 (weather, and the zero-day case of Avg Daily; v2), and Q12's dimension row counts (v2).

### 9.2 Query text (engine-authored, public, [unrun])
```dax
// C1 - volume and time intelligence, by fiscal year / month and borough
EVALUATE
SUMMARIZECOLUMNS (
    ROLLUPADDISSUBTOTAL ( 'Date'[Fiscal Year], "Is FY Total", 'Date'[Year Month], "Is Month Total" ),
    Borough[Borough],
    'Time Calc'[Time View],
    TREATAS ( { "Current", "FYTD", "PY", "YoY %" }, 'Time Calc'[Time View] ),
    FILTER ( ALL ( 'Date'[Year Month] ), NOT ISBLANK ( 'Date'[Year Month] ) ),
    "Check Row", 1,
    "Requests", [Requests],
    "Requests (Daily)", [Requests (Daily)]
)
ORDER BY 'Date'[Fiscal Year], 'Date'[Year Month], Borough[Borough], 'Time Calc'[Time View]
```
```dax
// C2 - opened, closed and digital share by month and channel
EVALUATE
SUMMARIZECOLUMNS (
    'Date'[Year Month],
    Channel[Channel],
    "Requests", [Requests],
    "Requests Closed", [Requests Closed],
    "Digital Share", [Digital Share]
)
ORDER BY 'Date'[Year Month], Channel[Channel]
```
```dax
// C3 - resolution, benchmark and rank by agency; carry-in rows for the load check
EVALUATE
SUMMARIZECOLUMNS (
    Agency[Agency],
    "Requests", [Requests],
    "Median Hours", [Median Resolution Hours],
    "P25 Hours", [P25 Resolution Hours],
    "P75 Hours", [P75 Resolution Hours],
    "P90 Hours", [P90 Resolution Hours],
    "Median Hours (Mature)", [Median Resolution Hours (Mature)],
    "Without Valid Close", [Requests Without Valid Close],
    "Benchmark Eligible", [Benchmark Eligible Requests],
    "SLA Met % (Benchmark)", [SLA Met % (Benchmark)],
    "SLA Breach Rate", [SLA Breach Rate],
    "SLA Met % (What-if default)", [SLA Met % (What-if)],
    "Agency Rank", [Agency Rank (Median Resolution)],
    "Unmatched Complaint Rows", CALCULATE ( [Requests], ISBLANK ( Complaint[Complaint Type] ) ),
    "Carry-in Rows", COUNTROWS ( 'Opening Backlog' )
)
ORDER BY Agency[Agency]
```
```dax
// C4 - backlog at every month end, by borough; naive vs fast, with and without a Channel filter
EVALUATE
SUMMARIZECOLUMNS (
    'Date'[Date],
    Borough[Borough],
    FILTER ( ALL ( 'Date'[Date] ), NOT ISBLANK ( 'Date'[Date] ) && 'Date'[Date] = EOMONTH ( 'Date'[Date], 0 ) ),
    "Check Row", 1,
    "Open Backlog EOP", [Open Backlog EOP],
    "Open Backlog EOP (Fast)", [Open Backlog EOP (Fast)],
    "EOP PHONE", CALCULATE ( [Open Backlog EOP], Channel[Channel] = "PHONE" ),
    "EOP (Fast) PHONE", CALCULATE ( [Open Backlog EOP (Fast)], Channel[Channel] = "PHONE" )
)
ORDER BY 'Date'[Date], Borough[Borough]
```
```dax
// C4r - the drill's live rebuild (Appendix C): C4 with the naive columns only
EVALUATE
SUMMARIZECOLUMNS (
    'Date'[Date],
    Borough[Borough],
    FILTER ( ALL ( 'Date'[Date] ), NOT ISBLANK ( 'Date'[Date] ) && 'Date'[Date] = EOMONTH ( 'Date'[Date], 0 ) ),
    "Check Row", 1,
    "Open Backlog EOP", [Open Backlog EOP],
    "EOP PHONE", CALCULATE ( [Open Backlog EOP], Channel[Channel] = "PHONE" )
)
ORDER BY 'Date'[Date], Borough[Borough]
```
C4r has its own expected file, `expected/<profile>/C4r.csv` (the C4 values without the Fast columns), so it runs on a copy of the model that holds Open Backlog EOP and nothing else. It is **opt-in**: the reconcile CLI runs it only when asked (§9.4).
```dax
// C5 - golden rows (the key list is generated by the engine into the file, per profile)
EVALUATE
CALCULATETABLE (
    SELECTCOLUMNS (
        Requests,
        "Unique Key", Requests[Unique Key], "Created Date", Requests[Created Date],
        "Created Hour", Requests[Created Hour], "Closed Date", Requests[Closed Date],
        "Closed Valid", Requests[Closed Valid], "Resolution Minutes", Requests[Resolution Minutes],
        "Valid For Resolution", Requests[Valid For Resolution], "Backlog Eligible", Requests[Backlog Eligible],
        "Backlog Exit Date", Requests[Backlog Exit Date], "Backlog Exit", Requests[Backlog Exit],
        "Status", Requests[Status], "Agency", Requests[Agency], "Complaint Key", Requests[Complaint Key],
        "Descriptor", Requests[Descriptor], "Borough", Requests[Borough], "Channel", Requests[Channel],
        "ZIP", Requests[ZIP], "Age Band Key", Requests[Age Band Key], "Breach Flag", Requests[Breach Flag],
        "R02", Requests[R02 Parse], "R03", Requests[R03 Close], "R05", Requests[R05 Resolution],
        "R06", Requests[R06 Day Precision], "R07", Requests[R07 Status Conflict], "R12", Requests[R12 Borough],
        "R13", Requests[R13 ZIP], "R18", Requests[R18 Open Invalid Close]
    ),
    TREATAS ( { 0 /* engine inserts the golden unique keys for the profile */ }, Requests[Unique Key] )
)
ORDER BY [Unique Key]
```
C5 covers the window table; the carry-in golden rows use the same query over `'Opening Backlog'` (`C5b.dev.dax` / `C5b.full.dax`, same columns except Breach Flag). C5 itself is split the same way (`C5.dev.dax` / `C5.full.dax`), because the golden keys differ by profile.
- **Why there is no `Source = "snapshot"` filter** (the old design claimed one that did not reach every table): the twin reads **the identical files** the model reads, as listed in the manifest. The live API's +3 / +10 row drift [research] matters only when the twin's raw counts are compared with `big_data.db`, and that comparison happens in the engine.
- **Fallbacks if a construct is rejected by DAX query view** [unrun]:
  - C1's ROLLUPADDISSUBTOTAL: split C1 into a month query and an FY query;
  - the constant column in C1, C4 and C4r: drop "Check Row". The all-BLANK rows then disappear, the expected files must be regenerated without them, and the completeness guard is proven only by the absence of rows, which is weaker; record it in docs/decisions.md.
  - **Why a constant is safe under the calculation group:** a calculation item transforms measure references only; "Check Row" is a constant expression, not a measure, so it stays 1 under every Time View.

### 9.3 Golden rows (engine)
**33 real unique keys** [twin]: 30 from the dev sample (divisible by 25, so checkable in dev mode and in full) and 3 tagged `full` (67996481, the extract's only `after_as_of` close; 64410145, exactly 525,600 minutes plus 1 second; 63528478, ZIP `Unkno`). 27 are window keys (C5: 24 in dev, 27 in full) and 6 are carry-in keys (C5b). Each is chosen to hit one rule: a `negative` close, an `after_as_of` close, a Closed row without a close (R07, in both roles), a DOT Pending row with a negative close (R18, in both roles; the carry-in one is kept by the §3.1 carry-in rule), a zero-minute close, an over-1-year close, a DOB midnight close (R06), an `Elevator` / `ELEVATOR` pair, the R09 aliases, an apostrophe key, a text ZIP, an out-of-range ZIP and a blank ZIP (R13), an `Unspecified` borough (R12), a literal `UNKNOWN` channel (R17), NYC311-PRD (R08), a request open at the window end in each age band 1–5, each at its band edge (R19); two Age Band key 0 rows, one closed before the window end and one ineligible under R07 (R19); and for R20: window requests closed on day 365 (exit `Closed`, one of them over 525,600 minutes), on day 366 and on day 400 (exit `Aged out` at created + 366), one still open that aged out inside the window, one aged out exactly on the window end, one whose exit falls after the window end (null exit), and carry-in requests that aged out, or closed, on 2024-09-01. The extra keys over the round-4 target of about 28 are these rule-edge rows.

**Targets that do not occur in the data, and what covers them instead:**

| Target | In the data | Covered by |
|---|---|---|
| An R03 `pre_2020` close | 0 rows in either role of either profile | Unit test on synthetic rows (1899 and 2019 closes): `test_r03_each_reason_in_precedence_order` |
| A missing status with a close value (R18, not R07) | 0 blank statuses in 7,744,123 rows | Unit test on synthetic rows: `test_r07_r18_missing_status_counts_as_not_closed` |
| A blank channel (R17) | 0 blank values | Stand-ins 62332700 and 65999375, which carry the literal `UNKNOWN` that R17 maps the same way; the blank case is in the unit test `test_r17_channel` |
| ZIP `1055O` (R13) | does not occur | Stand-ins 63528478 (`Unkno`, full) and 65727775 (`02062`, dev: five digits outside 10000–14999) |
| A `Litter Basket / Request` row (R09 alias) | matches 0 rows | Stand-ins 69542000 (`HAZARDOUS MATERIAL` → `HAZARDOUS MATERIALS`, window) and 59446500 (`BOILER` → `BOILERS`, carry-in) |

- The unit tests above are in the engine's twin suite and run on synthetic data, labelled as such; they prove the rule, not the owner's M. Where no real row exists, C5 cannot test the owner's M for that case, and HINTS says so.
- Each expected row is **hand-checked** against its raw line and the §4 wording, and a second script written from SPEC wording alone re-derived every cell. Each twin test is **proven red first** by breaking its rule on purpose.

### 9.4 The loop
1. In dev mode, paste `Cn.dax` into the web DAX query view, run it, press **Copy**, and save the clipboard on the Mac as `observed/dev/Cn.tsv`. The web view discards its query tabs when it closes, so `checks/dax/` is the only saved copy of the queries.
   - Microsoft documents that Copy puts the whole grid on the clipboard, tab-delimited, with headers [research]. That the web view behaves the same, and how a BLANK cell comes out, are [likely]; task 1's smoke test checks both. The CLI already accepts `'Date'[Year Month]`-style headers, tab, comma or semicolon separators, UTF-8 or UTF-16, and an empty cell or `(Blank)` as BLANK.
   - There is no DAX Studio on a Mac. If Copy fails, the fallback is the Execute Queries REST API run from the Mac (v2, optional; it drops BLANK cells from its JSON unless nulls are requested [research]).
2. `PYTHONPATH=tools/reconcile python3 -m northledger.pbi reconcile --repo . --profile dev`, run from the repo root, joins observed with expected on the key columns. The CLI is **in this repo**, under `tools/reconcile/` (§3.2): a copy of the comparison-only module from the engine's `northledger-core` package, standard library only (Python 3.9 or later; nothing to install), with its own tests (`NL_PL300_REPO="$PWD" python3 tools/reconcile/tests/test_pbi_reconcile.py`). It contains no rule or measure logic and never imports the twin, so publishing it seals nothing away from the owner and gives nothing away to him. Anyone with a clone can re-run it on the committed `observed/` and `expected/` files and get the same `reconciliation_results.csv`, cell for cell and status for status (only the `run_at` column differs):
   - integer counts: **exact**;
   - hours and ratios: relative tolerance **1e-9**;
   - **BLANK and 0 are different values** and must match exactly.
   - **An expected row whose measure values are all BLANK** (C1's guard rows, C4's rows outside the window) must be **present** in observed, with BLANKs: the "Check Row" column makes it appear. It is compared cell by cell like any other row. If it is absent, the CLI reports `missing` on **each of its cells** (5 for a C1 row), and each is a fail.
   - **"Check Row" is a declared constant.** In `checks/spec/C1.json`, `C4.json` and `C4r.json` the column carries `"constant": 1`; the CLI refuses (exit 2, nothing written) an expected file whose Check Row is not 1 on every row, and compares the observed column exactly.
   - **Load rows (`L`):** each window file's manifest `rows` against C1's observed Current Requests for that Year Month (detail rows, summed over boroughs); the carry-in file's `rows` against C3's Carry-in Rows summed over agencies.
   - **Which checks run.** With no `--checks`, the CLI runs C1–C5, C5b and the `L` rows. **C4r is opt-in** (`--checks C4r`): it is the drill's check, and a normal run neither needs `observed/<profile>/C4r.tsv` nor writes a C4r row.
   - It writes `reconcile/dev/reconciliation_results.csv`, with pass / fail / missing / extra per cell. The rows of the checks that ran are replaced; the rows of checks that did not run are kept with their own run time, so skipping a check never makes page 10 greener.
3. Iterate until **all five checks are green in dev**, including the FYTD / PY / YoY % / FY rows of C1 and all 36 month ends of C4 (24 inside the window, 12 BLANK outside it). Then set `pProfile` to `full` in the semantic model's settings, refresh in the service (the full files come from the release assets), and run C1–C5 again (`--profile full`). This full run comes straight after RLS and before the report polish (§12). Budget: two full refresh cycles; if the second is not green, the fix is reproduced in dev first.
4. Commit and push `reconcile/<profile>/reconciliation_results.csv`, wait out the 5-minute raw cache (§3.2), and refresh the model in the service, so page 10 shows the latest results. A stale or failed reconciliation is **visible in the report**.
5. **RLS checks** (not DAX; recorded in `observed/<profile>/rls_checks.csv`: role, page, check, expected, observed, pass, where pass is `pass`, `fail` or `gap`, and a `gap` row's observed cell says why the check could not run). The browser has no View as dialog [research]. The checks use **Test as role** on the semantic model's Security page in the service.
   - **Workspace roles bypass RLS.** RLS does not apply to workspace Admins, Members or Contributors [research]. Opening the report as the owner therefore proves nothing about the roles; only Test as role does.
   - **Static role Brooklyn** → the page 1 **KPI matrix** (rows Fiscal Year, Borough slicer cleared; the Date slicer does not reach it): each FY row's Current Requests = the C1 row (that Fiscal Year, FY total, BROOKLYN, Current).
   - **Dynamic role, as yourself.** Microsoft says Test as role evaluates dynamic rules with the tester's own identity [research]. The owner's UPN is not in `borough_access.csv`, so every Borough member is hidden: the KPI matrix cells are BLANK and page 10 shows the DQ Access Note. This is the negative case: an unlisted user sees nothing.
   - **Dynamic role, as another user.** Try Test as role's option to view as a specific person, with `bk.manager@example.test` (expected: Brooklyn only) and `qn.si.manager@example.test` (expected: Queens + Staten Island, and the KPI matrix cells equal the sum of those two boroughs' C1 rows). Learn is contradictory on whether that option changes what the dynamic rule sees, and these UPNs are not tenant users [research]. If the service does not accept them, or evaluates the owner's identity anyway, record each as `gap` with the reason. Do **not** replace the listed UPNs with tenant users: the file is engine reference data in a public repo. The README then states that the positive dynamic case was not tested in the browser.
   - **Every borough role:** page 10 shows the DQ Access Note, **no** rule rows and **no** mismatch.
   - **City Operations** sees every borough, including UNKNOWN.

### 9.5 The twin's own tests (engine; all green, each proven red first, **before gate G1 is signed**)
- **Raw counts** equal `big_data.db` along two independent paths (SQL vs pandas on the files): full 7,542,606 and 201,517; dev 301,688 and 8,037 [twin].
- **Dev sample:** every dev key is divisible by 25 and present in full; sample × 25 ÷ full within ±1.5% by borough and by month (§3.1: UNKNOWN passes by 0.01 percentage points).
- **Golden rows:** red first, then green (§9.3), plus the synthetic unit tests named there for the targets that do not occur.
- **Fast = naive** at every day and every month end, overall and by agency × borough, in both profiles.
- **R20:** each eligible row exits at most once; exits are dated inside the window; opening + opened − exits = operational backlog at every day; every eligible carry-in row exits by the window end (full: 101,695 closed + 69,607 aged out = 171,302 [twin]).
- **R19:** bands 1–4 = Open Backlog EOP at the window end; band 5 = stale open (the figure in `backlog_facts.csv`); band 0 = every other row; no null Age Band Key in either role.
- **Backlog Flow grain:** one row per date × agency × borough × flow type (107,468 full, 62,716 dev).
- **Aggregates:** Requests (Daily) = Requests at its grain.
- **BLANK cases** exist in the expected files **as rows**: PY / YoY % at FY2025, FY2026, the grand total and every month Sep 2024 – Aug 2025; FYTD at the months Sep–Dec 2026; Requests (Daily) under FYTD, PY and YoY %. C1 has one row for every Fiscal Year × Year Month (with the FY and grand-total rollups) × Borough × Time View combination.
- **BLANK cases that cannot occur in the real C3.** Breach rate with no eligible rows, and rank for a blank median, are not C3 rows in either profile: all 16 agencies with requests have benchmark-eligible rows and a mature median, and the UNKNOWN agency has no rows at all, so the query returns no row for it. These two cases are covered by unit tests on synthetic data (`test_c3_blank_safe_ratios_and_carry_in_rows`, `test_c3_rank_ignores_blank_medians_and_is_dense`); the C3 rules themselves are checked on every real row.
- **FYTD cap:** FYTD Requests at FY2027 and at the grand total equals Requests for Jul–Aug 2026; at Sep–Dec 2026 months it is BLANK.
- **rule_counts:** flag rows for both roles; the carry-in R07 row equals the carry-in status-conflict count; `distinct` rows in the §3.5 layout.
- **Reference files:** every complaint key found in either role of either profile, and every key of the baseline year, has a category (none `Unmapped`; the generator stops on an unmappable key); every canonical agency, including `UNKNOWN`, is in `agency_dim.csv`; every Channel value is in `channel.csv`; `borough.csv` has 6 rows; each `sla_benchmarks` benchmark equals its `sla_baseline_summary` p75 rounded as §1 states.
- **C4r** equals C4 without its Fast columns.
- **numpy `linear`** equals the inclusive-percentile definition in §6.3 on a hand example.
- **Manifest rows** = loaded rows per file; duplicates = 0; carry-in ∩ window keys = ∅.
- **R03 partition:** the R03 reasons plus Closed Valid rows partition all rows.

### 9.6 What this proves, stated honestly
- **Before Power BI runs:** the expected values follow the spec, they are re-runnable ledger facts, and the raw counts agree on two paths. None of that shows that the owner's M or DAX is right.
- **After C1–C5 pass:** each matching cell is independent evidence that his Power Query + model + DAX equals the spec on real data.
- **Common-mode weakness:** if the spec itself is wrong, both implementations can agree on the wrong answer. The independently written raw audit (page 10, informational) mitigates it **only for the conditions it shares with the rules**: in v1, a missing close (R03) and a blank ZIP (R13), where its counts equal the twin's once the engine has checked that no separating case occurs (it found one: 3 placeholder ZIPs in the full window, so that cell is left empty). It says nothing about the other rules. What mitigates the rest in v1: the hand-checked golden rows; the engine's independent recomputations, written from SPEC wording alone without importing the twin, which agreed with the expected files on every cell they cover; and the lead reading the sealed answer key against the twin.

---

## 10. RLS requirements (4.2.4), in words

- **City Operations:** sees everything, including the UNKNOWN borough.
- **Borough Manager – Brooklyn** (the one static role; the other four would differ only in the literal, so they are not built):
  - sees only its borough through a filter on the **Borough** dimension, which then flows to every fact;
  - **table permissions deny** (the filter is false for every row) `DQ Rules`, `Reconciliation Results` and `Borough Access`. Those tables hold city-wide numbers, including C1's per-borough observed values.
- **Borough Manager (Dynamic):**
  - `Borough Access` is filtered to the signed-in user's UPN;
  - Borough is filtered to the boroughs listed for that UPN (one or several), with **no bidirectional relationship and no security-filtering-behaviour change**;
  - `DQ Rules` and `Reconciliation Results` are denied.
- **No stored volumes outside the facts.** No dimension may carry a precomputed count. That is why v1 has no ZIP dimension, and why the SLA benchmark file's baseline-request count is **not loaded**. Benchmark Hours are a city-wide threshold, not a volume; that is disclosed on page 10.
- **UNKNOWN-borough rows** (6,319 in the full window [twin]) are visible to City Operations only. Page 10 says so.
- **Typed city-wide figures.** The page 3 caption and the page 10 Method panel carry static, city-wide, full-profile numbers that RLS cannot filter. They are public facts about the whole dataset, not borough volumes, but they sit beside RLS-filtered visuals, so each is labelled "city-wide, full profile, not filtered by borough or slicers".
- **The role-playing relationship is RLS-compatible:** activating an inactive relationship is restricted when RLS is defined on a table in that relationship, and no RLS sits on Requests or Date.
- **Testing:** §9.4 step 5. Service group membership (4.2.5) is v2.

---

## 11. Performance and size (2.3.x)

- **Performance Analyzer** (2.3.2), in web report editing (View → Performance Analyzer) [research]:
  - page 3 agency line with Open Backlog EOP vs (Fast);
  - three runs each, in dev and full;
  - record visual ms and DAX ms in `docs/decisions.md`, and export the JSON to `docs/evidence/`.
- **DAX query view** (2.3.2): C1–C5 live in `checks/dax/`, since the web view keeps no saved queries (§9.4). Time one query grouped by month and borough with Requests, then with Requests (Daily), three runs each. That timing is the performance evidence for the reduced-granularity table. Whether the web DAX query view shows a query's duration is [unverified]. If it does not, time the two versions with Performance Analyzer on a temporary table visual on a scratch report page, and delete that page before the next commit (the Requests Daily usage rule, §5.1, is about the committed report). DAX Studio's Server Timings are dropped (a Windows tool).
- **Model size:** open the Fabric notebook **Memory Analyzer** from the semantic model in the full profile. It needs the Fabric trial capacity and Build permission [research]. Record the total and the top 5 columns, and save the output to `docs/evidence/`. Record also whether the full model fits under **1 GB**, the model size limit of a Pro workspace [research], which applies once the Fabric trial ends.
- **Optional (15 min):** in the scratch workspace, load a dev copy **with** latitude/longitude as decimal at 5 dp, then record the column sizes with the Memory Analyzer, to support the "removed in v1" decision. Fixed decimal would cut them to 4 dp.
- **Refresh:**
  - **Projection before the full profile exists in the model (end of task 4, pre-committed).** Time a dev refresh of Requests alone in the service (a table-level refresh; take the duration from the refresh history; three runs, take the median) and record `projected full refresh = 25 × that time × 4`. The files now come over the network from GitHub, so the time includes the download. The factor 4 counts the loaded queries that each pass over every window file: Requests, Requests Daily and DQ Rules (each runs the R01–R20 chain) and Complaint (which decompresses every file again). **If the projection is over 30 min, Requests Daily is built as a DAX calculated table from Requests** (§5.1), so one pass disappears. The decision and both numbers go in `docs/decisions.md`, and the full-reconciliation hours are re-derived from the projection.
  - Record the actual full refresh time. Each loaded query that references the file chain re-reads the files: Requests, Opening Backlog, Requests Daily (unless switched), Complaint and DQ Rules.
  - This is the **reference-vs-duplicate impact** of 1.3.7, measured rather than asserted. Backlog Flow is a DAX table precisely to avoid another re-read.
  - One **duplicate** of Requests is made as a debug fork, then deleted, and the reason is recorded.

---

## 12. Gates and owner time: in PROCESS.md (private)

The gates (G0 sealing, G1 engine ready, each with its checklist and sign-off line), the owner hours per task, the cut list, the checkpoints and the hard stop are in `_design/PROCESS.md`. Two scheduling rules are public because they decide what the README can claim:
- **The full-profile reconciliation (C1–C5 in `full`) runs straight after RLS, before any report polish,** and it is protected like the interview drill: if time runs short, report polish is cut, never the full reconciliation.
- **What is not green when the hard stop arrives ships as "not finished in v1"** in the README, never as done. A minimal README (the authorship statement, the reconciliation pass rate, that list, the log link, and the page screenshots with the PDF export, Appendix B item 0) is itself protected, so the list is always written and a reviewer can always see the report.

---

## 13. v2 backlog (not in v1; specified so nothing is lost)

### 13.1 Automated pipeline with per-source cutoffs (fixes the examiner's critical cutoff bug)
- **Pull.** `data/pipeline_soda.py` (stdlib) pulls one month from `erm2-nwe9`:
  - `$select` for the 19 columns; `$where` on created_date;
  - `$order=:id`, `$limit=50000`, with an offset loop. `$order=unique_key` timed out in a probe [research].
  - Output: an ISO-dialect file with `as_of` = **pull time** (NYC local). R02 then gains the ISO branch (`yyyy-MM-ddTHH:mm:ss`, fraction ignored).
- **Closure delta.** Every run also re-pulls **rows whose `closed_date` or status changed since the previous `as_of`** for keys created before the current month. This goes to `nyc311_updates_<date>.csv.gz` (role `update`, its own `as_of`).
  - **R16** keeps, per Unique Key, the row with the **latest `as_of`**; the de-duplication must be order-stable (see the Tier-2 hint for R16).
  - This makes snapshot requests that were open at 2026-09-20 close properly, and it exercises R16 on real duplicates.
- **R03 is unchanged:** a close is valid only up to **its own file's** `as_of`. Pipeline closes after 2026-09-20 are therefore valid, not `after_as_of`. Right-censoring maturity uses the minimum `as_of` over the files that hold the cohort.
- **R20 is unchanged:** staleness is already relative to each as-of date, so a rolling window needs no new staleness rule; only the extract-level exclusion and the carry-in period are recomputed relative to `window_start`.
- **The window becomes rolling:**
  - `window_end` = the last complete day across all sources;
  - the twin re-reads the same manifest, so reconciliation stays exact without any Source filter.
- **Web source mode for Service refresh: in v1 since round 6.** The browser build already reads the repo over HTTPS from a fixed base address with relative paths (§3.2), and task 1 tests a service refresh. v2 adds `.github/workflows/monthly-311.yml`, which the owner activates, and a scheduled refresh.

### 13.2 Other v2 items
- **Tier 1 Service sprint** (in the v1 tenant while its trials last, otherwise a new trial; 6–8 h; v1 already has the workspace, credentials and manual refresh):
  - scheduled refresh, app with audiences, dashboard + data alert, subscription, promote / certify;
  - workspace roles, item access, Build permission + a thin live-connected report (the shared-model half of 1.1.1);
  - RLS group membership;
  - sensitivity labels: study from the documentation on this route (they need Purview labels, which a Business trial does not have);
  - the tenant export setting;
  - a Publish-to-web public copy with no roles and no Key Influencers.
- **Copilot: study only.** The four Copilot skills need a paid Fabric F2+ capacity, and trials are excluded [research]. The report says "Copilot not demonstrated".
- **Optional relational module (examiner, medium):**
  - load one month into a Fabric Warehouse or SQL database on the trial capacity [unverified]. A PostgreSQL on the Mac would need a gateway, which is Windows-only;
  - show folding indicators and View Native Query vs the CSV path;
  - build a DirectQuery table in a composite model, as a real 1.1.3 decision;
  - set **automatic page refresh** on a DirectQuery page (3.2.13).
  - 4–6 h.
- **Pages:** the page 1 mobile layout (round-6 cut: editing it in the service is [unverified], and the plan was over the hours cap); 2 Volume & Trend (small multiples, calculation-group slicer), 6 Weather & Calendar, 8 Agency Scorecard (a second drillthrough), 9 report-page tooltip (completes 3.2.2), 11 About; the page 3 backlog decomposition tree with manual splits; the story bookmark sequence; a narrative visual; the page 4 chart/table bookmark toggle (show/hide groups; round-3 cut); the page 5 ZIP scatter with **Find clusters** (completes 3.3.2; round-3 cut); a calendar-year check query for the §7 calendar rows.
- **Measures:**
  - **Requests (Smart)**: equals Requests in every context, reads Requests Daily whenever the context allows (completes 2.3.3 with automatic routing), tested under Channel, Age Band and Status filters;
  - Avg Daily Requests with zero-request days counted (the old Q11 zero-day case);
  - Requests YoY % as a measure that applies the calculation item (for card reference labels), and the absolute YoY item;
  - Carry-in Backlog card; a "Data Through" measure; load-reconciliation measures inside the model;
  - Rolling 28D;
  - **Daily z-score against the same weekday over the prior 8 weeks.** The trailing-28-day version would flag most weekends because of the weekly cycle.
  - **Backlog (Closing)** over a month-end `Backlog Snapshot` table (the periodic-snapshot semi-additive pattern exam items use), reconciled against EOP;
  - a quick-measure comparison (2.2.6);
  - a DAX UDF (bonus; not on the outline).
- **Power Query:**
  - Holidays (Nager.Date, a list-of-records JSON; one row per date before the Date merge);
  - pivot and transpose exercises, for example Open-Meteo built the long way (completes 1.3.4);
  - Borough Population unpivot, labelled "2014 DCP projection";
  - Location Type and Time of Day dimensions;
  - latitude/longitude via ZIP centroids, if a map is added.
- **Personalization** (3.2.11), shown in the Service.

---

## Appendix A: PL-300 study tracker (moved)

The 78-row skill tracker, with its status and O / O+h / O\* / O(x) markers, is the owner's **private** study tracker. Since round 4 it lives in `_design/PROCESS.md` and is not published. Round 8 retired the tracker's markers and the README's marker summary for v1 (§0.1); the README may still give the recount (v1 / partly v1 / note only / v2 / not covered).

## Appendix B: README skeleton (public)
0. **What the report looks like** (first, above the findings): the six v1 pages as PNGs from `docs/screenshots/`, embedded in the README, and a link to `docs/screenshots/NYC311-Operations.pdf`, the report exported to PDF from the service. They are taken in the full profile, by the owner (a workspace admin, so RLS does not apply and the pages show what City Operations sees), before the Fabric trial ends (§12). That the service exports this report to PDF is [likely]; if it does not, the PNGs alone meet this item: after it, the model and report folders open only in a Fabric workspace or, [likely], in Power BI Desktop on Windows, so for a reviewer on a Mac or a phone the PNGs and the PDF are the report. Each PNG's caption names its page and the `as_of` date. Page 7 is a hidden drillthrough page, so its PNG is taken after drilling through from page 4, and the PDF may leave it out [likely].
1. **Three findings for an operations manager.** They come from the reconciled model and each is cited to a **reconciled** check-query value or to a visual shown in a page screenshot (item 0). Examples: the slowest agency against its own baseline benchmark (C3); the operational backlog trend from C4's month-end values and its age mix at window end (with the stale share); the channel shift (C2). No finding quotes a PY or YoY % for a measure other than Requests, because only Requests is reconciled under the Time Calc items (§6).
2. **Three hard modeling problems in the model (round 8: designed in the spec, implemented by AI):**
   - the semi-additive backlog with its carry-in, eligibility rule, rolling 365-day age limit and naive-vs-fast equality;
   - the role-playing close date;
   - the case-collision complaint key.

   These were designed in the AI-assisted spec and its review rounds and implemented by AI (round 8); the README says so. A separate short list, **"Decisions I made"**, names only decisions the owner made and logged in `docs/decisions.md`, for example the round-8 decision itself, the refresh projection and the Requests Daily switch (§11), the privacy levels (§3.5), the category-map, alias and agency-name review (task 3b), and the dev-profile ratification.
3. **Trust:** the reconciliation pass rate (C1–C5, C5b and the load rows, both profiles), the DQ rule match count, and the authorship statement (§0.1), verbatim: "AI-built, owner-directed: the Power Query, model, measures, RLS and report were written by AI (Claude) from a specification the owner directed; the numbers are checked against an independent Python twin with the reconcile CLI." The marker summary and the hint and key-opening log are retired with the hand-built process (round 8). The README links `docs/decisions.md`, never the private process file.
4. **Domain line** for bank reviewers (§1).
5. **What is not shown in v1 and why:** Copilot, automatic page refresh, the Tier 1 Service features, the page 1 mobile layout, and the Desktop dialogs the browser build replaced (what-if, Groups, bins, View as; §2.1). Also the positive dynamic-RLS case, if §9.4 step 5 recorded it as a `gap`.
6. How to reproduce: the dev profile works from the repo alone (the model reads the repo's own files; point `pDataBaseUrl` at your copy); the full profile comes from release `data-v1`. **The reconciliation needs no Power BI at all:** in a clone, with Python 3.9 or later and nothing to install, `PYTHONPATH=tools/reconcile python3 -m northledger.pbi reconcile --repo . --profile dev` (then `--profile full`) re-compares the committed `observed/` grids with the committed `expected/` files and rewrites `reconcile/<profile>/reconciliation_results.csv`, which must match the committed one in every column but `run_at` (§9.4); `NL_PL300_REPO="$PWD" python3 tools/reconcile/tests/test_pbi_reconcile.py` runs the CLI's own tests. The model and report folders can be synced into a Fabric workspace through Git integration, or opened in Power BI Desktop through `NYC311-Operations.pbip` [likely]. The benchmark hours are an engine-provided input: `sla_baseline_summary.csv` documents them, and the engine recomputes them from `big_data.db`.

## Appendix C: Interview drill (task 15)

**Retired for v1 (round 8).** The drill served the hand-built process. It is kept below as a study aid only; v1 does not depend on it, and the README does not claim it. C4r and its opt-in CLI run stay available.

**Format.** Done after task 14 and before the Fabric trial ends, with the workspace closed and no notes. A timer, a screen recording, and 2 minutes per answer. Then one live rebuild. Model answers are sealed in the answer key (Part K9); open them only **after** recording all seven answers, and log `DRILL | <date> | questions missed | what I changed`. Repeat the missed questions two days later.

**The seven scored questions.** Four come from the hiring review, adapted to v1. Three (3, 4 and 7) are about the owner's **own** implementation. SPEC and HINTS state only the behaviour those queries and columns must have, so the answers are the owner's own choices and his reasons for them: a question whose answer SPEC or HINTS already states tests memory, not understanding.
1. Why is the backlog semi-additive? What would the FYTD item do to it without the stock rule, both inside the window and after it? Why do the time items apply only to a whitelist of measures?
2. In Agency Rank, the ranking evaluates the median once per agency. Walk through how the filter context for each agency is created, and why an agency with no median must not get rank 1.
3. Walk through your own DQ Rules query, step by step. At each step that changes the number of rows, which columns does it keep, and why each one? What would one column fewer, or one more that no rule needs, cost there?
4. Your manifest lists **two** files that are not at the source. In which query and at which step does your M fail, and does the refresh error name one file or both, by manifest name or by address? The source already fails on its own for a missing file: why did you add your own check, or why not? And why is failing better than loading fewer rows?
5. How does the dynamic role find a user's boroughs without a bidirectional relationship, and why did you avoid the bidirectional bridge?
6. Why is a median over closed requests optimistic, and what does the 30-day maturity rule not fix?
7. Put Agency Group (your grouping column on Agency, §5.1) on the rows of a visual with Open Backlog EOP (Fast). Which way does your Fast measure compute its value there, does it still equal the naive measure, and why?

**Fluency questions** (asked if time allows; their answers are in SPEC, so they are not scored): why the backlog excludes requests open more than 365 days, and how Fast still equals naive when a request can leave by closing or by ageing out; why Requests Daily is on no visual; why Digital Share is 0% under a PHONE filter; why `Elevator` and `ELEVATOR` collide in the model but not in Power Query; why UNKNOWN-borough rows and the data-quality rows are visible only to City Operations.

**Live rebuild.** In a copy of the model in the workspace that is not connected to Git (§3.2), with every measure deleted, write Open Backlog EOP from the SPEC definition within 15 minutes and check it with **C4r** (C4 with the naive columns only, §9.2, against `expected/dev/C4r.csv`). C4r is opt-in, so name it: `--checks C4r`. Run the CLI with `--repo` pointing at a scratch copy **outside** the repo (holding `checks/`, `expected/`, `data/dev/manifest.json` and the pasted `observed/dev/C4r.tsv`), so that drill rows never enter the repo's `reconciliation_results.csv`, which page 10's pass rate reads. Pass: C4r green, or the failing cells explained correctly.

**Pass mark.** Six of seven answered correctly without notes, and the rebuild passes. Otherwise the missed items go into a second pass, and the README does not claim the drill until it is passed.
