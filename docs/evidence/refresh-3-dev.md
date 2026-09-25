# Dev profile in the Power BI service: refresh 3 and reconciliation, 25 Sep 2026

- **Where:** workspace NYC311-Operations (Power BI Premium Per User trial), synced from this repo by Fabric Git
  integration at commit c6d461b. Data sources github.com and archive-api.open-meteo.com, both Anonymous / Public.
- **Refresh 3:** on demand, started 00:37:31, succeeded 00:39:57 ET. Refreshes 1 and 2 failed; the causes and
  fixes are the two FIX lines of 24 and 25 Sep in `docs/decisions.md`.
- **How the grids were taken:** each query in `checks/dax/` was run against the refreshed model through the Power BI
  Execute Queries REST API (the same engine as DAX query view), with `includeNulls` so BLANK stays empty. The rows
  were written to `observed/dev/Cn.tsv` unchanged; the SHA-256 of every grid was computed in the Power BI page and
  matched on disk.
- **Reconcile** (`PYTHONPATH=tools/reconcile python3 -m northledger.pbi reconcile --repo . --profile dev`):

  | Check | Result |
  |---|---|
  | C1 | PASS 4,920 / 4,920 cells (984 rows) |
  | C2 | PASS 315 / 315 (105 rows) |
  | C3 | PASS 224 / 224 (16 rows) |
  | C4 | PASS 1,080 / 1,080 (216 rows) |
  | C5 | PASS 624 / 624 (24 golden rows) |
  | C5b | PASS 150 / 150 (6 golden carry-in rows) |
  | L | PASS 25 / 25 (every file's rows vs the manifest) |
  | **All default checks** | **PASS 7,338 / 7,338** |
  | C4r (opt-in drill) | PASS 648 / 648 |

- **First run of the check queries:** C1 and C4/C4r returned 48 and 6 extra rows, all on Date's blank member with
  every measure BLANK (see the FIX line of 25 Sep on the check queries). With the blank member excluded, the same
  model returned the expected rows exactly; the new grids were verified to be the old ones minus those rows.
- **Weather check** (decisions.md WEATHER CHECK):
  `[Weather days in window] = 730`, `[Days in window] = 730`, `[Weather days total] = 988`. The fallback did not fire.

Still [unrun]: the full profile, RLS with Test as role, every report page (no screenshots yet), the Key Influencers
analysis type, anomaly Explain-by fields and the decomposition-tree AI levels.
