> **Round 8 (2026-09-23):** this file served the hand-built process, which the owner retired for v1 (AI builds v1; SPEC round-8 note); it is kept for reference only.

# HINTS: NYC 311 PL-300 showcase (v1, round 6), Tier 1

This file is public. Read it **after** SPEC.md.

**What Tier 1 is.** Each entry gives only:
- **Concept:** the idea being tested;
- **Trap:** the mistake that fails reconciliation or an interview question, described by its **symptom**.

It names **no functions and no step orders**. Those are **Tier 2**, sealed in the answer key (Part T), under the same IDs (H1.9 here ↔ T1.9 there). Open a Tier-2 entry only under the protocol's step 4 (PROCESS.md §P3), and log it as `HINT-2 OPENED`. The tracker then marks the skill **O+h**.

**Where help may come from, and where it may not** (PROCESS.md §P1–§P3):
- **Allowed without a log entry:** SPEC, this file, PROCESS.md, `research-exam.md` (once the lead has stripped its two function notes; if you read them, say so in the EXPOSURE line), `research-mac.md`, `research-data.md` (the round-4 redacted copy; if you read the round-1 version, say so in the EXPOSURE line), the `expected/` files, the check queries, the reconcile CLI's output and its source (`tools/reconcile/`, comparison only since round 7) and the Microsoft documentation. The expected values tell you **what** the answer is, not how to reach it.
- **Logged, and it lowers the marker:** a Tier-2 hint (`HINT-2 OPENED`, O+h); the key (`KEY OPENED`, O\*); the twin's source in the engine repo (`TWIN READ`: a docstring gives O+h, code gives O\*). The twin is not in your working copy on purpose. It is a finished implementation of every rule and measure, so reading it is closer to opening the key than to reading a hint.
- **Do not start building before both gates are signed** in `docs/decisions.md`: G0 (sealing, signed) and G1 (engine ready, PROCESS.md §P4). The engine's files are already in `data/` and `expected/`, but they are final only once the `ENGINE READY` line exists, and again after any task 3b change to the reference files (which regenerates them).

---

## H1. Power Query

- **H1.1 Structure.** *Concept:* a query that reads a data source must not also combine data from other queries, or the privacy firewall stops the refresh. *Trap:* a reusable helper that reads a file counts as reading the source in whichever query calls it. *Trap (round 6):* the list of files to fetch comes from the manifest, which is itself read from the source; a query that takes the file names from another query and then fetches the files stops with "references other queries or steps, so it may not directly access a data source". *Trap:* the model reads two web sources (the repo and the weather API), so their privacy levels and credentials must be compatible; write down what you chose and why.
- **H1.2 Parameters (1.1.4).** *Concept:* one switch changes the data files, the expected files and the reconcile file together, and one base address serves every file. *Trap (round 6):* an address built as one piece of text works in the editor's preview, and then the service refuses to refresh it (or the web editor refuses it outright) as a dynamic data source. *Trap:* deriving the weather end date from the manifest sends data read from the repo into a web request; keep that parameter static.
- **H1.3 Manifest (1.3.5).** *Concept:* the manifest is a record that holds a list of records; the window becomes one record, the file list a table. *Trap:* one file entry has a null month; the conversion must tolerate it. *Trap:* a manifest that lists a file missing at the source must stop the refresh loudly, naming the file, not load fewer rows quietly.
- **H1.4 Extract Files (1.3.8, 2.3.1).** *Concept:* the manifest says which files exist and what each one is; each compressed file becomes a table. *Trap (round 6):* the files arrive exactly as stored, gzip-compressed; read as text, a file becomes one column of garbage. *Trap:* some descriptors contain commas inside quotes, and some text contains `’`; if either comes out garbled or splits a row, the read options are wrong.
- **H1.5 Reading one role (1.3.8).** *Concept:* every row must know which file it came from and that file's `as_of`. *Trap:* after the files are appended, that information is gone.
- **H1.6 R01 text hygiene.** *Concept:* control characters first, then whitespace; empty becomes null. *Trap:* cleaning only the columns you remember.
- **H1.7 R02 date parsing.** *Concept:* the text is US 12-hour and must be read the same way on any machine. *Trap:* a parse that follows the locale of whatever machine evaluates it (a service region, a browser language, an en-CA setting) misreads `03/04/2026` or errors on it. *Trap:* if the parser swallows its own failures, you cannot flag and count them.
- **H1.8 R09 / R10 keys (1.3.9).** *Concept:* Power Query compares text case-sensitively and the model does not, so two spellings that Power Query keeps apart can collide in the model. *Trap:* a raw type that differs only in case, apostrophes or spacing must land on exactly one key. *Trap:* the dimension and the facts must use the **same** key recipe, or C3's "Unmatched Complaint Rows" is not blank.
- **H1.9 The cleaning function (R01–R20).** *Concept:* one function applied to both roles; everything is a flag or a derived column; nothing is dropped for quality; types are set once, at the end. *Trap (R03):* comparisons with a missing value do not quietly return false in M; handle the missing cases first, which the SPEC precedence already does. *Trap (R03):* comparing against one global date instead of each row's own `as_of` gives the same answer in v1 and breaks v2. *Trap (R05):* "zero" means under one whole minute after rounding down, so a 59-second close is zero and 525,600 minutes plus a few seconds is still valid. *Trap (R07 / R18):* decide what a missing status means; SPEC R07 and R18 say it counts as not Closed, and a comparison with a missing value must not quietly give the opposite. No v1 row has a missing status, so no check will catch this: get it right by reading, because v2 data may have one. *Trap (R18):* a close that fails to parse is not "a close value present"; it is counted once, under R02. *Trap (R13):* a ZIP with letters in it (the data has `Unkno`) must be flagged, not raise an error. *Trap (R19):* age is measured at the window **end**, not at `as_of`, in whole calendar days, and carry-in rows are included. *Trap (R19):* a row that is not open at the window end gets key 0, not an empty key; an empty key lands on Age Band's blank member and shows "(Blank)" on the axis. *Trap:* declaring a column's type is not the same as converting it; errors appear where the conversion happens.
- **H1.10 R20 backlog exit.** *Concept:* each eligible request leaves the operational backlog exactly once: by closing within 365 days, or by ageing out on day 366. *Trap:* a request that closes on day 400 has already aged out; it must not also exit as "Closed". *Trap:* an exit after the window end is not an exit in this model. *Trap:* days are calendar days: a close on day 365 at a later clock time than the creation is still "Closed", even when it is more than 525,600 minutes (R05 then says over a year; R20 does not read the minutes). Check your boundaries against the R20 golden rows in C5 and C5b (days 365, 366 and 400; an exit on the window end; an exit after it; carry-in exits on the window start).
- **H1.11 Load Errors (1.2.3).** *Concept:* a diagnostic that is not loaded, so it costs nothing at refresh, and counts error cells per column of the final tables. *Trap:* checking a step before the types are set finds nothing, because that is where errors appear.
- **H1.12 Requests Daily (1.3.3, 2.3.3).** *Concept:* reduce the facts to the grain of four dimensions. *Trap:* the wrong grain (for example including the descriptor) gives about 879k rows instead of about 337k, and the table no longer fits a type-grain Complaint dimension. *Trap:* anything that references Requests re-reads every file; time the refresh, because that measurement is your 1.3.7 answer.
- **H1.13 Complaint (1.3.6, 1.3.8).** *Concept:* a dimension built from the distinct keys of **both** roles, then enriched by two merges. *Trap:* built from the window only, older carry-in types land on the blank member. *Trap:* keeping the baseline request count puts a city-wide volume in a dimension that RLS cannot filter.
- **H1.14 Weather (1.3.5, 1.2.3).** *Concept:* columnar JSON, one list per variable, becomes a table column by column; a failed call must still give a typed, empty table. *Trap:* an error-catching wrapper around something lazy may not catch an error raised later. *Trap:* the City Hall coordinates snap to New Jersey.
- **H1.15 Date (2.1.4).** *Concept:* a contiguous, unique, non-null day list with fiscal attributes, window flags and one merge. *Trap:* NYC FY2026 runs 1 July 2025 – 30 June 2026, so a July date belongs to the next calendar year's FY number. *Trap:* "Month Name" does not sort itself.
- **H1.16 DQ Rules (1.3.4, 1.3.3, 1.3.8).** *Concept:* count flag values per rule **for each role** (Requests and Opening Backlog), add the distinct counts of the three consolidated keys, then compare with the twin's counts so that a rule missing on either side still shows. *Trap:* counting the window table only gives a mismatch on every carry-in row of `rule_counts.csv`, and hides the carry-in status conflicts. *Trap:* comparing on the rule key alone collides the two roles. *Trap:* the naive order of operations builds a 60-million-row intermediate, which on a trial capacity is the difference between a refresh and a memory error; think about which step shrinks the data first. *Trap:* computing the mismatch in the report lets slicers create false mismatches; this table should be static and city-wide.
- **H1.17 Reconciliation Results.** *Concept:* until the first reconcile run is pushed, the file is not at the source; the query must still return a typed, empty table. *Trap (round 6):* a missing web file is an HTTP error, not an empty file. *Trap:* the same lazy-evaluation trap as H1.14. *Trap:* page 10 shows the previous run until the new file is pushed, the few-minute cache has passed, and the model is refreshed.

---

## H2. Model

- **H2.0 Relationships (2.1.3).** *Concept:* many-to-one, single direction, no path between two facts; Opening Backlog must reach the same five dimensions as Requests, but not Date. *Trap:* auto-detected relationships, especially a guessed bidirectional one, break the RLS reasoning. *Trap:* the second Date relationship stays inactive.
- **H2.1 Breach Flag (2.1.5).** *Concept:* a row-level comparison with an attribute of a related dimension. *Trap:* returning 0 when the row is not assessable makes every breach denominator wrong; it must be BLANK.
- **H2.2 Backlog Flow (2.2.7).** *Concept:* a table of signed daily flows built from the two loaded facts: + on opening, − on exit. *Trap:* if the two sides count different populations, the fast backlog drifts away from the naive one over time (C4 grows apart month by month). *Trap:* a request that leaves twice, or never, does the same. *Trap:* one way of building this table produces a circular dependency once it is related to the dimensions. *Trap:* the table is built from several parts; if a window exit and a carry-in exit share a date, agency, borough and type, they must end up as **one** row. Every sum still agrees if they do not, but the table is then not at its grain (107,468 rows in full, 62,716 in dev).
- **H2.3 Age Band (2.2.7, 3.3.2).** *Concept:* a banding table with a sort key, including a member for "not open at the window end". *Trap:* equal-width bins cannot make 0–7 / 8–30 / 31–90; equal-width bins belong on page 7 (H2.7). *Trap:* the band is the age on 31 Aug 2026; used as a filter on any other date it describes the wrong population, which is why the age chart cross-filters nothing.
- **H2.4 Threshold table (what-if).** *Concept:* a one-column table of the allowed values and a measure that returns the selected one, with a default; Desktop's what-if dialog would generate both, the browser has no such dialog, so you build them. *Trap:* with nothing selected, or several values, the measure must return the default, not BLANK; C3's what-if column expects 72. *Trap:* the step and the end value must give exactly 84 rows (4 … 336). *Trap:* a constant line cannot hold a typed-in measure; look for the conditional (fx) option.
- **H2.5 Groups (3.3.2).** *Concept:* a grouping of a dimension's members is a new column of that dimension, made on the model side: the skill Desktop's Groups dialog teaches. The browser has no such dialog, so you model the column yourself; built in M it would be Power Query, not the grouping skill. *Trap:* an agency your grouping forgets gets a blank group, which shows as "(Blank)" on page 5; every canonical agency, `UNKNOWN` included, needs a group.
- **H2.6 Properties (2.1.1).** *Trap:* once the calculation group exists, implicit measures are off: every number on a visual must be an explicit measure.
- **H2.7 Bins (3.3.2; page 7).** *Concept:* equal-width binning is a column holding the bin each row falls in (here 1,440 minutes, one day), the column Desktop's bins dialog would create; in the browser you model it. *Trap:* a row with no Resolution Minutes must get no bin, not the first bin. *Trap:* the histogram's bins must sort as numbers; if 10,080 comes before 1,440 on the axis, they are sorting as text.

---

## H3. Measures

**General trap:** a measure that the calculation group transforms (the (TC) set) must be correct under every item. Ask yourself what would happen to another measure it referenced when the "PY" item is active.

| ID | Measure | Concept | Trap (symptom) |
|---|---|---|---|
| H3.1 | Requests / Requests (Daily) | single aggregation; the same count on the reduced table | Requests (Daily) is right only at its own grain; put it on a visual with a Channel slicer and it silently ignores the slicer. That is why the usage rule keeps it off visuals |
| H3.2 | Requests Closed | role-playing date | September 2026 closes (a partial month) appear on the axis; carry-in closes creep in |
| H3.3 | Requests Without Valid Close | a filtered count that respects an existing filter on its own column | A visual filtered to Closed Valid = True still shows the full count instead of BLANK |
| H3.4 | Digital Share | how a measure's own filter meets an existing filter on the same column | PHONE row shows a large percentage (digital ÷ phone) instead of 0%; a row with requests but no digital ones shows blank instead of 0% |
| H3.5 | Open Backlog EOP | a semi-additive stock with a rolling age limit | (1) Lines that run flat to December. (2) Values before the window start. (3) Carry-in has no Date relationship. (4) A request with no close must count as open. (5) 0, not BLANK, inside the window. (6) The 365-day limit moves with the as-of date |
| H3.6 | Open Backlog EOP (Fast) | the same value from cumulative flows | Correct under Agency and Borough, wrong under a Complaint or Channel filter it cannot see; C4's PHONE columns catch it. Also wrong when a field of the flow table itself (the flow type) is on the visual: the naive measure cannot see that filter, so the two part company |
| H3.7 | Backlog Inflow / Outflow | guarded flows | A wrong number instead of BLANK under an unreachable filter (including one on a Requests Daily column); a negative outflow; aged-out exits missing, so the running net no longer lands on the backlog |
| H3.8 | Median / P25 / P75 / P90 | statistics | An empty set errors or shows 0; the P-values differ from the twin in the last digits (inclusive vs exclusive); a visual filtered to Valid For Resolution = False still shows the valid median |
| H3.9 | Median (Mature) | intersecting with an existing filter | A visual filtered to "not mature" (or "not valid") still shows the mature median |
| H3.10 | Benchmark Eligible / SLA Met % / SLA Breach Rate | BLANK-safe ratios | In DAX, BLANK equals 0, so "flag = 0" picks up non-assessable rows; breach rate shows 100% on an empty cell; a cell with eligible rows but none met shows blank instead of 0% |
| H3.11 | SLA Met % (What-if) | a threshold value in a calculation | C3 expects the default (72) when nothing is selected |
| H3.12 | Agency Rank | ranking over the visible agencies | An agency with no data ranks #1 "fastest"; totals show a rank; a slicer-hidden agency still takes a rank |
| H3.13 | Drillthrough Label / Rule Mismatches / Reconciliation Pass Rate / DQ Access Note | labels, table emptiness under RLS | A borough manager sees "0 mismatches" for rules he cannot see |

---

## H4. Calculation group `Time Calc`

- **Concept:** one set of time logic applied to a whitelist of measures, with a completeness rule.
- **Trap 1: partial periods.** FY2026 against FY2025 compares twelve months with ten. Check your understanding against SPEC §7's list of which rows must be BLANK; C1 has a row for each of them, with BLANK values.
- **Trap 2: stock measures.** Year-to-date has no meaning for a closing balance, and a stock can go wrong under it in more than one way, one of which shows only after the window ends. Decide what FYTD means for a stock and say it explicitly.
- **Trap 2b: the window.** Year-to-date at a Sep–Dec 2026 month still finds July and August data, so a flow runs flat to December unless the item knows where the data stops.
- **Trap 3: non-whitelisted measures.** They should show nothing under FYTD or PY, not their current value under that heading. Some measures do not respond to Date at all, so an item would leave them unchanged. C1's Requests (Daily) column tests this.
- **Trap 4:** the prior-year dates you get back depend on which dates exist in the Date table; your completeness rule should not.
- **Day-1 spike:** Key Influencers against the calculation group (SPEC §8). Build it before and after, and screenshot both.

---

## H5. RLS

- **Concept:** filter the dimension; single-direction relationships carry the filter to every fact.
- **Trap 1:** disconnected tables are not reached by the Borough rule; tables with city-wide numbers need their own rule.
- **Trap 2:** the "easy" dynamic RLS uses a bidirectional relationship; SPEC forbids it. Be ready to explain why.
- **Trap 3 (round 6):** the browser has no View as. Test as role simulates a role; whether it can also make the dynamic rule see another person's name is not settled, and the listed test names are not users of your tenant. Record what it did. Testing the dynamic role as yourself is still a real check: you are not in `borough_access.csv`, so you must see nothing.
- **Trap 3b:** opening the report as yourself proves nothing about RLS; as the workspace owner the roles do not apply to you.
- **Trap 3c:** a listed name must match `borough_access.csv` exactly, and one test user has two boroughs.
- **Trap 4:** UNKNOWN-borough rows disappear for every borough role. That is correct; say so on page 10.
- **Trap 5:** Analyze → Explain the increase does not run on a model with roles. That is why SPEC asks for an RLS-free copy. *Trap (round 6):* made in the Git-connected workspace, the copy is committed with your next commit, and the sealing CI fails after it is already public.

---

## H6. Report

- **Anomaly detection:** it needs a single-value line on a date axis with no legend and no other analytics lines.
- **Forecast:** same constraints. If the line runs flat to December, the forecast starts from the flat part.
- **Error bars:** the bounds are measures.
- **Visual calculations:** think about what a running sum runs **along**.
- **Selection pane (3.2.7):** group the page 1 cards and name the group; layer order and tab order are set in the same pane. (The round-2 chart/table toggle is v2.)
- **Key Influencers:** a numeric target changes the analysis type. It samples its input: write that down.
- **Decomposition tree:** AI splits on a simple measure only.
- **Drillthrough button:** its text can come from a measure; it is disabled until one Complaint Type is selected.
- **Age chart on page 3:** it must show 31 Aug 2026 whatever the Date slicer says, and clicking a band must not filter the other page 3 visuals.
- **KPI matrix on page 1:** rows are fiscal years; the Date slicer must not reach it, or its rows stop being whole years and the RLS Test-as-role check has nothing fixed to compare with.
- **Accessibility:** alt text (can be dynamic), tab order, never colour alone.

---

## H7. When a check fails

| Symptom | Look at |
|---|---|
| C1 counts off by a small constant in one month | R16 duplicates, a missing file (the `L` rows), or a row with an unparseable created date |
| C1 extra rows with a blank Borough | R12 not applied in one of the two tables, or the Borough dimension missing a member |
| C1 PY or YoY % present where the expected value is BLANK | The completeness rule, the clip to the window, or the whitelist (Requests (Daily) column) |
| C1 rows `missing` whose expected values are all BLANK | The query lost its "Check Row" column, or the copy dropped empty cells: the row must be there, with BLANKs |
| C1 FYTD has values at Sep–Dec 2026 months | The FYTD item is not capped to the data window (H4 Trap 2b) |
| C2 Digital Share large on PHONE rows | H3.4 |
| C3 rank starts at an agency with a blank median | H3.12 |
| C3 Breach Rate 1.0 somewhere | H3.10 |
| C3 Unmatched Complaint Rows not blank | H1.8, H1.13 |
| C4 Fast > naive, growing over time | H2.2: the populations of the two sides differ |
| C4 Fast < naive from the first window months (Sep 2024), gap growing | Aged-out exits counted twice, or late closes not moved into "Aged out" (H1.10) |
| C4 naive higher than expected from the first window months (Sep 2024), gap growing | The 365-day limit is missing or fixed at one date (H3.5) |
| C4 PHONE columns differ | H3.6, or Opening Backlog lacks its Channel relationship |
| C4 values on dates after 2026-08-31 | The window cap is missing |
| C5 golden row: R03 wrong | Precedence order, or the comparison uses the wrong `as_of` |
| C5 golden row: Complaint Key wrong | The normalization order in SPEC R09 |
| C5 golden row: Backlog Exit wrong | R20 boundaries: day 365 is still "Closed"; day 366 is "Aged out" |
| Any check: BLANK where 0 is expected, or the reverse | Re-read SPEC §6 for the BLANK/0 column of that measure |
