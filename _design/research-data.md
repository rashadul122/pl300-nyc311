# Research: data

> **Redacted in round 4 (2026-09-22; the sealing rules are in PROCESS.md §P1, private).** The Power Query sketch (§6) and every Power Query M and DAX function name were removed, because they matched sealed Tier-2 hints. Every fact and count is unchanged: the US 12-hour date text, the en-CA mis-parse risk, the case collision, the column profile. The unredacted original is kept in the engine repo's history (`pl300-nyc311-engine/history/research-data.unredacted.md`). Whether the owner read it before this redaction is asked in the EXPOSURE record (PROCESS.md §P2, private).
>
> **Superseded recommendations.** This file is the pre-design data profile. Its recommendations (the extract summary below, §6 and §8) are superseded by SPEC wherever they differ: the dev profile is the 1-in-25 sample over all 24 months, not August 2026 alone; the Date table runs 2024-01-01 to 2026-12-31; Complaint is a type-grain dimension (descriptor is a Requests column, and there is no Category → Type → Descriptor hierarchy); latitude/longitude are not loaded in v1, so there is no rounding; and there is no geography dimension (borough is its own dimension, ZIP a Requests column, community board, council district and precinct are not loaded). The facts and counts stand.

I profiled all 22,542,090 rows of nyc_311 read-only, in about 4.5 minutes of database time: one parallel streaming pass, one full key pass, and one aggregate checks pass. big_data.db was not modified (same size, same 02:29:40 timestamp); only its -shm sidecar was touched, which any reader of this database does. Every figure below is from the full table unless marked as sampled.

**Dates**
- `created_date` is 100% in one text format, `MM/DD/YYYY hh:mm:ss AM|PM` (US 12-hour clock, local NYC time, no offset). The range is 2020-01-01 00:00:00 to 2026-09-20 01:51:01.
- Rows per year: 2020 2.94M, 2021 3.22M, 2022 3.17M, 2023 3.22M, 2024 3.46M, 2025 3.66M, 2026 (to Sep 20) 2.87M.
- `closed_date` is present on 98.07% of rows, but only 94.39% for 2026, because recent requests are still open.

**Keys**
- `unique_key` is unique in every row, always 8 numeric characters. It is a clean fact key.

**Resolution time (closed minus created)**
- Negative: 0.21%. 96% of these are DOT rows with status `Pending`.
- Zero: 2.26%. They cluster in DOHMH (31%), DOB (13%), DOT (9%) and DEP (7%).
- Longer than a year: 1.25%.
- Placeholder close dates: 112 in 1899/1900, 636 before 2020, and 2 after the snapshot (the latest is in 2033).
- Day-precision closes (exactly midnight): 87% of DOB and 27% of DSNY closes.
- Status and closed date disagree: 53,931 `Closed` rows have no closed date, and about 81,000 non-closed rows have one.
- In a 5% sample, the median is 8.4 hours against a mean of 220 hours, so use the median.

**Messy categories**
- 21 agency codes and 22 agency names. DCA and DCWP are the same agency after a rename, as are DOITT and OTI. DHS has two names, and there are two internal 311 codes.
- 276 complaint types, with 17 groups that differ only by case or punctuation. Some cross agencies: `Elevator` is DOB and `ELEVATOR` is HPD, and `Plumbing` vs `PLUMBING` spans DOB/HPD. This matters because Power BI treats text case-insensitively, so these keys need normalizing before building a dimension. That is known engine behavior; I could not test it without Power BI.
- 1,362 descriptors.
- 227 location types; 13.1% are blank, and there are overlaps like `Street/Sidewalk` vs `Street` vs `Sidewalk`.
- Borough: 5 real values plus `Unspecified` (40,744) and blank (38,433). Only 1,447 of those can be recovered from zip.
- Zip: 98.6% are valid 5-digit NYC codes, 1.4% blank, and 447 junk rows.
- 25 zips map to more than one borough, so zip cannot sit cleanly under borough in the model.
- `city` has 154 case-variant groups.

**Too sparse or redundant to use**
- 10 columns are at least 97.9% empty or placeholder: due_date, facility_type, park_facility_name, vehicle_type, taxi_company_borough, taxi_pick_up_location and the four bridge/highway columns.
- `park_borough` is identical to `borough`.
- `location` and the x/y state-plane columns duplicate latitude/longitude.

**Recommended extract**
- 24 complete months, created 2024-09-01 to 2026-08-31: 7,542,606 rows and 19 lean columns.
- Two years are needed for year-over-year DAX.
- Write it as 24 monthly `.csv.gz` files of about 15–19 MB each. Uncompressed, the biggest month would be about 94 MB, too close to GitHub's 100 MB limit.
- Keep the roughly 400 MB total out of git history (regenerate it by script or attach it to a release). Commit only August 2026 (328,828 rows, about 18 MB gzipped) as a sample.
- If the VM struggles, the 12- or 13-month windows are about 3.9M or 4.2M rows, but year-over-year is then lost or limited.

**Live API check**
- The public API for the same data is dataset erm2-nwe9, "311 Service Requests from 2020 to Present".
- Its field names are `complaint_type`, `descriptor` and `descriptor_2` rather than the local names, and it returns ISO timestamps.
- It can aggregate on the server. Its July and August 2026 counts are 3 and 10 rows higher than the local snapshot.

None of this was run in Power BI. Import comfort in the VM and the .pbix size are estimates only.

## Findings

- [verified] nyc_311 has 22,542,090 rows with dense rowids 1..22,542,090; rows are NOT stored in date order (rowid 1 = 2020-03, rowid 5,000,000 = 2026-04, rowid 22,000,000 = 2020-01, last rowid = 2026-09), so rowid ranges are not date ranges and any date-bounded extract needs one full scan (no index on created_date; no indexes at all in the DB).  (sqlite_master listing + point lookups by rowid (file:...big_data.db?mode=ro))
- [verified] created_date: 100% of 22,542,090 rows match the single text format 'MM/DD/YYYY hh:mm:ss AM|PM' (22 chars, US 12-hour, local NYC wall-clock, no offset). Range 2020-01-01 00:00:00 to 2026-09-20 01:51:01. closed_date and resolution_action_updated_date use the same format whenever non-blank (0 non-conforming values).  (full streaming scan, GLOB '[01][0-9]/[0-3][0-9]/[12][0-9][0-9][0-9] [01][0-9]:[0-5][0-9]:[0-5][0-9] [AP]M' (scan311.py, 6 parallel rowid slices))
- [verified] Rows per created year: 2020 2,942,024; 2021 3,220,882; 2022 3,169,960; 2023 3,224,723; 2024 3,456,769; 2025 3,655,040; 2026 (Jan 1 to Sep 20) 2,872,692. Monthly volume 159k (2020-04) to 348,511 (2026-01); September 2026 is partial (206,163).  (full scan, Counter on created year-month)
- [verified] closed_date present on 22,106,844 rows (98.07%); by year 98.76/99.02/99.20/98.08/98.17/98.48% for 2020-2025 but only 94.39% for 2026 (right-censoring of still-open requests).  (full scan)
- [verified] unique_key is unique across all 22,542,090 rows, always 8-character numeric text, min 40287734 max 70480488: safe as the fact primary key, typed as whole number.  (full key-only pass with numpy.unique)
- [verified] Resolution time (closed_date - created_date) buckets over all rows: no close 1.93%, negative 0.21% (47,047), exactly zero 2.26% (508,444), under 1 min 0.34%, 1 min-1 h 24.28%, 1 h-1 d 30.65%, 1-7 d 22.52%, 7-30 d 9.97%, 30 d-1 y 6.61%, 1-3 y 0.94%, over 3 y 0.31%.  (full scan, julianday difference of ISO-converted timestamps)
- [verified] Negative durations are almost entirely one pattern: 45,121 of 47,047 are DOT rows with status 'Pending'; only 1,117 are under 1 hour (clock skew). Sampled quantiles of the negatives: median -63 h, 10th percentile -264 h.  (full aggregate checks pass (checks311.py) + 5% systematic sample (rowid % 20 = 0) for quantiles)
- [verified] Absurd closed dates: 112 in 1899/1900 (1899-12-31 19:00:00 looks like a 1900-01-01 UTC placeholder shown in Eastern time), 636 before 2020, 2 after the 2026-09-20 snapshot (max 2033-03-01). 5.77% of closes are exactly 12:00:00 AM (day precision): DOB 573,115 of 661,806 (87%), DSNY 668,424 of 2,507,156 (27%).  (full scan + full aggregate checks pass)
- [verified] Zero-duration closes concentrate by agency: DOHMH 31.15%, DOB 13.40%, DOT 9.40%, DEP 7.11% of their rows; share with no close is high for TLC 23%, EDC 21%, DHS 19%, DPR 14%.  (full scan, agency x bucket Counter)
- [verified] Median and p90 resolution hours for valid durations (0 < h < 1 year): overall median 8.4 h, p90 437 h, mean 220 h (heavily skewed). Medians: NYPD 0.9 h, DEP 23 h, DSNY 52 h, DOT 59 h, HPD 104 h, DOB 370 h, TLC 1,084 h.  (5% systematic sample, rowid % 20 = 0 (1,127,104 rows))
- [verified] Status versus closed_date is inconsistent: 53,931 'Closed' rows have no closed_date; about 81,128 non-Closed rows have one (Pending 46,609, Assigned 15,695, Open 13,860, Unspecified 2,722, In Progress 2,130, Started 112). Status has 8 values: Closed 97.95%, In Progress 1.26%, Open 0.37%, Pending 0.28%, Assigned 0.11%, Started 0.02%, Unspecified 0.01%, Cancel (1 row).  (full scan)
- [verified] Agency: 21 codes and 22 names (22 code/name pairs). Rename pairs split the same entity: DCA (27,905) and DCWP (125,702) both file 'Consumer Complaint'; DOITT (669) and OTI (933). DHS has a second name 'Operations Unit - Department of Homeless Services' (28 rows). There are internal codes 'NYC311-PRD'/'HIQA' (371) and '3-1-1' (1). The top 3 agencies (NYPD 43.7%, HPD 19.8%, DSNY 11.2%) hold 75% of rows.  (full scan)
- [verified] problem_formerly_complaint_type has 276 distinct values (0 blank), 295 agency x type pairs; top 10 types cover 53.5% of rows, top 50 cover 90.0%, top 100 cover 98.4%; 54 types have under 100 rows. 17 groups differ only by case or punctuation (HEAT/HOT WATER vs Heat/Hot Water, PLUMBING vs Plumbing, 'Litter Basket / Request' vs 'Litter Basket Request'), and some cross agencies ('Elevator' = DOB 123,562 vs 'ELEVATOR' = HPD 11,490).  (full scan)
- [likely] The Power BI engine (VertiPaq) compares text case-insensitively while Power Query is case-sensitive. So 'Elevator'/'ELEVATOR' survive Power Query Remove Duplicates, then collide on the one side of a relationship at refresh: complaint keys must be case-normalized in M before building the dimension.  (Known Power BI engine behavior; not testable here (no Power BI))
- [verified] problem_detail_formerly_descriptor has 1,362 distinct values and 1,643 type x descriptor pairs; 0.70% blank plus 480,531 'N/A' (2.13%); 43 case-variant groups (ENTIRE BUILDING vs Entire Building, etc.).  (full scan)
- [verified] location_type has 227 distinct values and 13.13% blank. Overlapping labels: Street/Sidewalk 28.6%, Street 9.1%, Sidewalk 7.3%; 'RESIDENTIAL BUILDING' 19.7% vs 'Residential Building' 33,059 vs 'Residential Building/House' 12.2%; '1-2 Family Dwelling' variants with missing spaces; placeholders N/A 39,981, Other (Explain Below) 44,550, Other 26,668.  (full scan)
- [verified] borough: BROOKLYN 30.00%, QUEENS 24.06%, BRONX 21.27%, MANHATTAN 20.12%, STATEN ISLAND 4.20%, 'Unspecified' 40,744 (0.18%), blank 38,433 (0.17%). 38,415 of the 38,433 blank-borough rows also lack latitude, and only 1,447 of the 79,177 missing-borough rows can be recovered via a zip-to-modal-borough lookup. park_borough has exactly the same counts as borough (redundant).  (full scan with empty-value bitmask)
- [verified] incident_zip has 679 distinct values: 98.598% are 5-digit NYC-range (10xxx-14xxx; 407 distinct, 224 with 100 or more rows), 1.400% blank, 422 rows other 5-digit (e.g. 00083 x33, out-of-state 17110/92108), 13 rows 1-4 digits ('0', '0000'), 12 rows text (NA, N/A, na, '1055O', 'Unkno'). No ZIP+4 and no float-like zips. 25 zips map to more than one borough (163,914 rows, 0.73%, sit off their zip's modal borough).  (full scan)
- [verified] Too sparse to use (share empty or placeholder): due_date 99.65%, taxi_company_borough 99.94%, road_ramp 99.77%, bridge_highway_direction 99.67%, park_facility_name 99.50% ('Unspecified'), bridge_highway_name 99.38%, bridge_highway_segment 99.39%, taxi_pick_up_location 99.12%, facility_type 98.98%, vehicle_type 97.90%. Weak: additional_details 63.06%, landmark 42.27%, intersection streets about 35%, cross streets about 27%. Usable: latitude/longitude 1.87% blank (1 row outside the NYC bounding box), council_district 2.37% blank, police_precinct 1.85% 'Unspecified', community_board 1.6% 'Unspecified <BORO>' or '0 Unspecified', open_data_channel_type 8.60% UNKNOWN.  (full scan, 44-column empty and placeholder bitmasks + aggregate checks pass)
- [verified] The lean 19-column extract measures 268.6 bytes per row as CSV and 55.2 bytes per row gzipped (level 6). The largest month (348,511 rows) is therefore about 94 MB as raw CSV (too close to GitHub's 100 MB hard limit) but about 19 MB gzipped.  (1M-row sample (10 rowid slices of 100k) written to CSV + gzip; extract_monthly.py test on 394,056 rows measured 52.1 B/row gz)
- [verified] Window sizes (full counts): Aug 2026 = 328,828 rows; Jun-Aug 2026 = 1,006,770; Sep 2025-Aug 2026 (12 months) = 3,942,833 (about 218 MB gz total); Aug 2025-Aug 2026 (13 months) = 4,246,872; Sep 2024-Aug 2026 (24 months) = 7,542,606 (about 416 MB gz total); calendar 2024-2025 = 7,111,809.  (full-scan month Counter x measured bytes per row)
- [verified] The public API source is NYC Open Data dataset erm2-nwe9, '311 Service Requests from 2020 to Present'. Its field names are complaint_type / descriptor / descriptor_2, where the local extract has problem_formerly_complaint_type / problem_detail_formerly_descriptor / additional_details. It returns ISO timestamps ('2026-09-21T01:51:08.000') and numbers as JSON strings. SoQL server-side aggregation ($select date_trunc_ym + count, $group) works.  (curl https://data.cityofnewyork.us/api/views/erm2-nwe9.json and /resource/erm2-nwe9.json with $select/$where/$group)
- [verified] API vs local reconciliation: July 2026 API 343,112 vs local 343,109 (+3); August 2026 API 328,838 vs local 328,828 (+10). The live dataset drifts after the local snapshot; the local max created is 2026-09-20 01:51:01 and the API max was 2026-09-21 01:51:08 at query time.  (curl SoQL aggregate query vs full-scan month Counter)
- [likely] Power BI Project (PBIP) folders gitignore .pbi/cache.abf (the imported data) by default, so committing the PBIP never commits the model data; the 100 MB concern then applies only to committed source files (and to a .pbix if one is ever committed).  (Knowledge of PBIP defaults; not verifiable on this Mac)
- [likely] Power Query can read the gzip-compressed CSV files directly, without unzipping them first. The US 12-hour text must be parsed with an explicit en-US culture: a VM set to en-CA would otherwise mis-parse or error.  (Knowledge of Power Query; not run (no Power BI available). Function names redacted in round 4)
- [unverified] Import comfort of 7.5M rows in a Windows 11 ARM VM and the resulting .pbix size could not be measured here.  (No Windows/Power BI on this machine)

## Details

# nyc_311 profiling for the PL-300 star schema (read-only)

**Scope and method.** I opened `<portfolio>/agent-demo/big_data.db` only with `file:...?mode=ro` plus `PRAGMA query_only=1`. After the work, the database file is unchanged: 26,108,944,384 bytes, modified 2026-09-22 02:29:40. Only SQLite's WAL `-shm` sidecar was touched, which any reader of a WAL-mode database does.

Database time used, about 4.5 minutes in total:
- One accidental `min(rowid),max(rowid)` full scan: 34 s.
- One streaming pass in 6 parallel rowid slices: 105 s wall. SQL computed per-row ISO timestamps, format flags, resolution hours and 44-column empty/placeholder bitmasks; Python kept the counters.
- One key-uniqueness pass: 41 s.
- One aggregate-only checks pass, also 6 slices: 85 s wall.

Every figure below is **full-table (22,542,090 rows)** unless marked **[sampled]**.

Scratch scripts, session-scoped (copy what you need):
- `<scratch folder>/scan311.py`
- `.../scratchpad/checks311.py`
- `.../scratchpad/merge311.py`
- `.../scratchpad/extract_monthly.py` (tested)
- Merged counters: `.../scratchpad/merged.pkl`

The database has **no indexes at all**. Rows are stored in export-chunk order, not date order:

| rowid | created |
|---|---|
| 1 | 2020-03 |
| 5,000,000 | 2026-04 |
| 22,000,000 | 2020-01 |
| 22,542,090 | 2026-09 |

So rowid ranges make good cheap *samples* but not date windows. Any date-bounded extract costs one full scan (about 40–100 s).

---
## 1. Dates

- **Format:** `created_date` is 100% `MM/DD/YYYY hh:mm:ss AM|PM`: 22 characters, US 12-hour clock, NYC local wall-clock, no offset. Every non-blank `closed_date` (22,106,844) and `resolution_action_updated_date` (22,350,587) has the same format, with 0 non-conforming values.
  - Durations that cross a DST change are off by ±1 h.
  - The live API returns ISO instead (`2026-09-21T01:51:08.000`), so the two sources need different parsing.
- **Range:** created 2020-01-01 00:00:00 to 2026-09-20 01:51:01. Created times at exactly 12:00:00 AM: 19,644 (0.09%, negligible).
- **Hour of day:** the peak is 09:00–11:00 (about 1.33–1.35M each) and the trough is 04:00 (246k). This is useful for a time-of-day dimension.

**Rows per year, closed-date share, and share not in `Closed` status:**

| year | rows | closed_date present | status not Closed |
|---|---|---|---|
| 2020 | 2,942,024 | 98.76% | 1.94% |
| 2021 | 3,220,882 | 99.02% | 1.43% |
| 2022 | 3,169,960 | 99.20% | 1.17% |
| 2023 | 3,224,723 | 98.08% | 1.51% |
| 2024 | 3,456,769 | 98.17% | 1.12% |
| 2025 | 3,655,040 | 98.48% | 1.47% |
| 2026 (to Sep 20) | 2,872,692 | 94.39% | 6.31% |
| **all** | **22,542,090** | **98.07%** | |

**Monthly counts, last 25 months:**

| month | rows | month | rows | month | rows |
|---|---|---|---|---|---|
| 2024-09 | 306,770 | 2025-05 | 295,058 | 2026-01 | 348,511 |
| 2024-10 | 306,803 | 2025-06 | 306,442 | 2026-02 | 334,690 |
| 2024-11 | 293,515 | 2025-07 | 315,883 | 2026-03 | 342,388 |
| 2024-12 | 313,949 | 2025-08 | 304,039 | 2026-04 | 302,191 |
| 2025-01 | 348,180 | 2025-09 | 302,684 | 2026-05 | 331,979 |
| 2025-02 | 255,364 | 2025-10 | 336,612 | 2026-06 | 334,833 |
| 2025-03 | 281,221 | 2025-11 | 304,905 | 2026-07 | 343,109 |
| 2025-04 | 272,549 | 2025-12 | 332,103 | 2026-08 | 328,828 |
| | | | | 2026-09 (partial) | 206,163 |

## 2. Keys

`unique_key` is unique in every row (22,542,090 distinct), always 8-character numeric text, from 40287734 to 70480488. Type it as a whole number. It is a clean fact key.

## 3. Resolution time

**How to compute it.** Convert both columns to ISO, then take julianday(closed) − julianday(created) × 24 for hours. The SQL:

```sql
substr(d,7,4)||'-'||substr(d,1,2)||'-'||substr(d,4,2)||' '||
printf('%02d',(CAST(substr(d,12,2) AS INTEGER)%12)+(CASE WHEN substr(d,21,2)='PM' THEN 12 ELSE 0 END))||substr(d,14,6)
```

**Buckets over all rows:**

| bucket | rows | share |
|---|---|---|
| no close | 435,246 | 1.93% |
| **negative** | **47,047** | **0.21%** |
| **zero** | **508,444** | **2.26%** |
| under 1 min | 76,075 | 0.34% |
| 1 min – 1 h | 5,472,771 | 24.28% |
| 1 h – 1 d | 6,909,231 | 30.65% |
| 1 – 7 d | 5,076,550 | 22.52% |
| 7 – 30 d | 2,247,315 | 9.97% |
| 30 d – 1 y | 1,489,030 | 6.61% |
| **1 – 3 y** | **211,558** | **0.94%** |
| **over 3 y** | **68,823** | **0.31%** |

**Anomalies:**
- **Negatives:** 45,121 of the 47,047 are DOT rows with status `Pending`. Only 1,117 are under 1 h (clock skew). [sampled] Negative quantiles: median −63 h, 10th percentile −264 h, 1st percentile −5,485 h.
- **Placeholder or absurd closed dates:**
  - 112 in 1899/1900. `1899-12-31 19:00:00` looks like a 1900-01-01 UTC placeholder shown in Eastern time.
  - 636 before 2020.
  - 2 after the snapshot; the maximum is 2033-03-01.
- **Zero-duration rows by agency:** DOHMH 31.15%, DOB 13.40%, DOT 9.40%, DEP 7.11%. These look like administrative or auto-closes.
- **Day-precision closes** (exactly 12:00:00 AM) are 5.77% of all closes: DOB 573,115 of 661,806 (87%) and DSNY 668,424 of 2,507,156 (27%). Durations for those agencies are floored to a day boundary.
- **Share with no close, by agency:** TLC 23.0%, EDC 20.8%, DHS 19.1%, DPR 13.7%, OOS 17.3%.
- **Longer than a year:** EDC 24.5% and DPR 14.4% of their rows.
- **`resolution_action_updated_date`:** earlier than created on 502,324 rows (2.23%), and more than 1 day away from closed_date on 606,719 rows (2.69%). Do not use it as the close timestamp.
- **Status vs closed date:** 53,931 `Closed` rows have no closed_date, and about 81,128 non-Closed rows have one.
- **Right-censoring:** 5.61% of 2026 rows have no close, against 0.8–1.9% in earlier years. Resolution measures for recent cohorts are biased low, so apply a maturity rule (for example, only requests created at least 30 days before the snapshot).

**[sampled: 5% systematic, rowid % 20 = 0, 1,127,104 rows]** For valid durations (0 < h < 1 y, 94.35% of the sample): overall median 8.4 h, p90 437 h, mean 220 h. Use the median and percentiles, not the mean.

Median hours by agency:

| agency | median h |
|---|---|
| NYPD | 0.9 |
| DHS | 5.6 |
| OSE | 16.3 |
| DEP | 23.2 |
| DCWP | 44.3 |
| DSNY | 51.6 |
| DOT | 58.6 |
| HPD | 103.6 |
| DOHMH | 105.2 |
| DPR | 252.7 |
| DOB | 369.6 |
| EDC | 891.5 |
| TLC | 1,083.8 |

**Suggested validity rule** (flag and quarantine rather than delete, matching the trust-engine brand): valid when closed is present, closed ≥ created, closed ≤ snapshot, and closed year ≥ 2020. Separately flag zero, under 1 min, over 1 y, and midnight-only closes as "day precision".

## 4. Categoricals: distinct counts, top values, messy variants

**agency / agency_name:** 21 codes and 22 names, forming 22 pairs.

| agency | rows |
|---|---|
| NYPD | 9,861,405 |
| HPD | 4,455,776 |
| DSNY | 2,526,968 |
| DOT | 1,512,906 |
| DEP | 1,201,270 |
| DPR | 856,864 |
| DOB | 661,907 |
| DOHMH | 544,555 |
| DHS | 297,079 |
| TLC | 202,895 |
| EDC | 178,126 |
| DCWP | 125,702 |
| OSE | 70,955 |
| DCA | 27,905 |
| DOE | 8,783 |
| OOS | 4,415 |
| DFTA | 2,605 |
| OTI | 933 |
| DOITT | 669 |
| NYC311-PRD ('HIQA') | 371 |
| '3-1-1' | 1 |

Remaps a dimension needs:
- DCA → DCWP (renamed; both file 'Consumer Complaint').
- DOITT → OTI (renamed).
- DHS has a second name, 'Operations Unit - Department of Homeless Services' (28 rows).
- 'NYC311-PRD'/'HIQA' and '3-1-1' are 311-internal codes. NYC311-PRD files Street/Sidewalk/Curb Condition rows that otherwise belong to DOT.

**problem_formerly_complaint_type:** 276 distinct, 0 blank, 295 agency×type pairs. Top 10 types cover 53.5% of rows, top 20 cover 68.5%, top 50 cover 90.0%, top 100 cover 98.4%. 54 types have under 100 rows and 25 have under 10, so group a long tail as "Other" in visuals. The top 10:

| complaint type | rows |
|---|---|
| Illegal Parking | 2,927,763 |
| Noise - Residential | 2,558,566 |
| HEAT/HOT WATER | 1,652,138 |
| Noise - Street/Sidewalk | 1,167,728 |
| Blocked Driveway | 1,075,484 |
| UNSANITARY CONDITION | 706,019 |
| Request Large Bulky Item Collection | 632,148 |
| Street Condition | 514,669 |
| Water System | 422,863 |
| Noise - Vehicle | 413,660 |

- **17 case or punctuation variant groups**, for example:
  - HEAT/HOT WATER 1,652,138 vs Heat/Hot Water 1,814 (both HPD).
  - PLUMBING (HPD) 406,185 vs Plumbing (DOB 20,486 + HPD 1,525).
  - **Elevator (DOB) 123,562 vs ELEVATOR (HPD) 11,490.**
  - 'Litter Basket / Request' 3,950 vs 'Litter Basket Request' 18,406.
  - "Building Marshals office" vs "Building Marshal's Office".
- HPD's own types are UPPERCASE; other agencies use Title Case.
- 19 types appear under more than one agency, mostly because of the renames above.
- There are also semantic near-duplicates that a category hierarchy should group: 'Noise' (DEP) vs 'Noise - Residential' (NYPD), and 'Derelict Vehicles' (DSNY) vs 'Abandoned Vehicle' (NYPD).
- **Model implication (likely, not testable here):** the Power BI engine compares text case-insensitively and Power Query does not. Normalize the key text (for example, case and surrounding whitespace) before removing duplicates, or refresh fails with duplicate values on the one side of the relationship.

**problem_detail_formerly_descriptor:**
- 1,362 distinct values; 1,643 complaint×descriptor pairs.
- 0.70% blank, plus 'N/A' 480,531 (2.13%) and 'Unspecified' 42.
- 43 case-variant groups (ENTIRE BUILDING vs Entire Building, MOLD vs Mold, and others).

**location_type:** 227 distinct; 13.13% blank.
- Top values: Street/Sidewalk 28.61%, RESIDENTIAL BUILDING 19.71%, Residential Building/House 12.19%, Street 9.13%, Sidewalk 7.29%, Store/Commercial 1.86%.
- Messy variants:
  - 'Residential Building' 33,059 vs 'RESIDENTIAL BUILDING'.
  - '1-2 Family Dwelling' 64,386 vs '1-2 FamilyDwelling', '1/2 Family Dwelling' and '1-2Family Dwelling'.
  - '3+ Family Apt. Building' 120,764 vs '3+ Family Apartment Building' 50,514.
- Placeholders: N/A 39,981, Other (Explain Below) 44,550, Other 26,668, Unknown 202.

**borough:**

| value | rows | share |
|---|---|---|
| BROOKLYN | 6,762,069 | 30.00% |
| QUEENS | 5,422,765 | 24.06% |
| BRONX | 4,794,868 | 21.27% |
| MANHATTAN | 4,535,929 | 20.12% |
| STATEN ISLAND | 947,282 | 4.20% |
| 'Unspecified' | 40,744 | 0.18% |
| '' (blank) | 38,433 | 0.17% |

- 38,415 of the 38,433 blank-borough rows also lack latitude.
- Only 1,447 of the 79,177 missing-borough rows can be recovered through a zip→modal-borough lookup, so keep an "Unknown" member.
- `park_borough` is byte-identical in counts to `borough`, so drop it.

**status:** Closed 97.95%, In Progress 1.26%, Open 0.37%, Pending 0.28%, Assigned 0.11%, Started 0.02%, Unspecified 0.01%, Cancel 1 row.

**incident_zip:** 679 distinct values.

| class | rows | share |
|---|---|---|
| 5-digit NYC range 10xxx–14xxx (407 distinct; 224 with ≥100 rows) | 22,226,051 | 98.598% |
| blank | 315,592 | 1.400% |
| other 5-digit | 422 | |
| 1–4 digits ('0' ×8, '0000', '1155', …) | 13 | |
| text (NA ×4, N/A ×3, na, '1055O', 'Unkno', 'Unsur') | 12 | |

- Other 5-digit includes '00083' ×33, possibly the Central Park special code (unverified), and out-of-state codes such as 17110 and 92108.
- There are no ZIP+4 values, no 9-digit values and no float-like zips.
- **25 zips map to more than one borough** (163,914 rows, 0.73%, are off their zip's modal borough). So ZIP → Borough is not a clean hierarchy: keep borough on the fact or use a location dimension keyed on (borough, zip).

**Other useful dimensions:**
- **open_data_channel_type:** ONLINE 41.54%, PHONE 29.82%, MOBILE 20.03%, UNKNOWN 8.60%, OTHER 0.02%.
- **community_board:** 79 distinct.
  - 'Unspecified <BORO>' 320,228 (1.42%), '0 Unspecified' 40,744, and an odd 'QENB' ×2.
  - Values look like '12 BRONX'.
- **council_district** [sampled 1M]: 2-digit text with a leading zero ('05'), 52 distinct, 2.37% blank (full).
- **police_precinct:** 'Precinct NN', 78 distinct in the 1M sample; 'Unspecified' 1.85% (full).
- **city:** 698 distinct, 5.23% blank, 154 case-variant groups (JAMAICA 465,613 vs Jamaica 59,545; ASTORIA vs Astoria 41,691). It is a postal city, not the borough.
- **latitude/longitude:** 1.87% blank; 1 row outside the NYC box (40.45–40.95, −74.30 to −73.65).
  - [sampled 1M] They carry 13–15 decimals, which makes them nearly unique. Round to 5 decimals (about 1 m) in Power Query to cut model size.

## 5. Sparsity: which columns to drop

Share that is empty or a placeholder (Unspecified, N/A, NA, Unknown):
- **Drop, at least 97.9% unusable:**
  - due_date 99.65%, taxi_company_borough 99.94%, road_ramp 99.77%.
  - bridge_highway_direction 99.67%, park_facility_name 99.50%, bridge_highway_segment 99.39%, bridge_highway_name 99.38%.
  - taxi_pick_up_location 99.12%, facility_type 98.98%, vehicle_type 97.90%.
- **Weak:** additional_details 63.06% (API name `descriptor_2`), landmark 42.27%, intersection_street_1/2 34.8%, cross_street_1/2 27.4%.
- **Redundant:** park_borough (= borough); location, x_coordinate_state_plane and y_coordinate_state_plane (= lat/long).
- **Exclude for size or privacy:**
  - incident_address and street_name (4.16% blank).
  - bbl (11.73% blank).
  - resolution_description: about 250 characters of boilerplate that doubles CSV size (467 vs 234 B/row in a 200k sample).
- **Good (at most 2.4% missing):** unique_key, created_date, agency, agency_name, complaint type, status (0%); resolution_action_updated_date 0.85%; incident_zip 1.40%; borough 0.35%; lat/long 1.87%; closed_date 1.93%; council_district 2.37%; descriptor 2.84%.

## 6. Recommended extract

**Recommendation: 24 complete months, created 2024-09-01 to 2026-08-31 = 7,542,606 rows, 19 lean columns.**

Why:
- Two years are needed for the PL-300 time-intelligence work: prior-year comparisons, rolling 12 months, YoY %.
- It ends on the latest complete month.
- The API can top up September 2026 onward.

Storage:
- Write one gzip CSV per month: about 15–19 MB each, all under GitHub's 50 MB warning.
- Raw monthly CSV would be up to about 94 MB (348,511 rows × 268.6 B), which is too close to the 100 MB block. Do not commit raw CSV.

Git:
- The total is about 416 MB gzipped (about 2.0 GB raw). Keep it **out of git history**: regenerate it with the script below, or attach a zip to a GitHub Release.
- Commit only **2026-08** (328,828 rows, about 18 MB gz) as the dev sample, behind a Power Query folder parameter.
- The PBIP's `.pbi/cache.abf` is gitignored by default (likely), so model data never enters the repo.

Lighter fallbacks if the VM is slow:

| window | rows | gzipped | cost |
|---|---|---|---|
| 13 months (Aug 2025–Aug 2026) | 4,246,872 | ~234 MB | only one month of YoY |
| 12 months (Sep 2025–Aug 2026) | 3,942,833 | ~218 MB | no YoY |
| calendar 2024–2025 | 7,111,809 | | clean annual YoY, much less censoring, but 9 months stale |

**Unverified:** import time and memory in a Windows 11 ARM VM, and .pbix size. To keep the model small:
- Split datetimes into a date column plus a time column.
- Round lat/long to 5 decimals.
- Type unique_key as Int64.
- Drop resolution_description.

**Extract SQL** (read-only; one full scan, about 40–100 s; columns renamed to the API names so local and API data share a schema):

```sql
SELECT unique_key, created_date, closed_date, agency, agency_name,
       problem_formerly_complaint_type    AS complaint_type,
       problem_detail_formerly_descriptor AS descriptor,
       location_type, incident_zip, borough, city, status,
       resolution_action_updated_date, community_board, council_district,
       police_precinct, open_data_channel_type, latitude, longitude
FROM nyc_311
WHERE substr(created_date,7,4) || substr(created_date,1,2) BETWEEN '202409' AND '202608';
```

The filter works on a derived YYYYMM key because the text dates don't sort.

**Monthly gzip splitter:** tested on a 400k-rowid slice. It wrote 24 files, the round trip was 394,056 rows / 19 columns, unique_key stayed unique, and it measured 52.1 B/row gz. Invocation:

```
venv/bin/python extract_monthly.py <OUT_DIR> 202409 202608
```

It writes `nyc311_YYYY-MM.csv.gz`. Core loop:

```python
con = sqlite3.connect("file:.../big_data.db?mode=ro", uri=True); cur = con.execute(SQL)
hdr = [d[0] for d in cur.description]; files = {}
for row in cur:
    ym = row[1][6:10] + "-" + row[1][0:2]
    if ym not in files:
        fh = gzip.open(f"{out}/nyc311_{ym}.csv.gz", "wt", newline="", encoding="utf-8", compresslevel=6)
        w = csv.writer(fh); w.writerow(hdr); files[ym] = (fh, w)
    files[ym][1].writerow(row)
```

Keep the extract raw: row filter and column selection only. All cleaning (en-US date parsing, agency remaps, case normalization, zip validation, lat/long rounding, placeholder→null, quarantine flags) is the owner's Power Query work to do and defend.

**Facts the Power Query work must respect (NOT run; no Power BI here; the round-1 sketch was redacted in round 4):**
- The files are gzip-compressed CSV, UTF-8, with quoted fields that can contain commas.
- The date text is US 12-hour. It must be parsed with an explicit en-US culture, because a Toronto (en-CA) VM would otherwise mis-parse `03/14/2020 03:07:31 PM`.
- How to read, combine and type the files is the owner's work (SPEC §4 R02; HINTS H1.4, H1.7).

## 7. Live API (for the "connect custom data" requirement), verified 2026-09-22

- **Dataset:** `https://data.cityofnewyork.us/resource/erm2-nwe9.json`, "311 Service Requests from 2020 to Present". Metadata rowsUpdatedAt = 2026-09-21 21:38 EDT.
- **Field names:** `complaint_type`, `descriptor`, `descriptor_2`. The local CSV-derived names are `problem_formerly_complaint_type`, `problem_detail_formerly_descriptor`, `additional_details`. Plus four `:@computed_region_*` fields.
- **Formats:** timestamps are ISO; counts come back as JSON strings.
- **Aggregation works server-side:**
  - `$select=date_trunc_ym(created_date) as ym, count(*) as n&$where=created_date >= '2026-07-01T00:00:00' and created_date < '2026-09-01T00:00:00'&$group=ym`
  - It returned 2026-07 = 343,112 and 2026-08 = 328,838.
- **Reconciliation:** the local counts are 343,109 and 328,828, so the API is higher by 3 and 10 rows. The live data drifts after the local snapshot. This is a ready-made evidence-ledger / reconciliation item: an API top-up (for example, a daily-aggregated SoQL query for September 2026 onward) appended to the historical extract, with a documented count check.
- **Date range:** at query time the API ran from 2020-01-01T00:00:00 to 2026-09-21T01:51:08. The local max created is 2026-09-20 01:51:01.

## 8. Star-schema implications (for the design agent)

- **Fact, one row per request:**
  - unique_key (PK, Int64); created date key + created time; closed date key + closed time.
  - resolution minutes as an integer; avoid a high-cardinality decimal.
  - Validity/quarantine flags; agency, complaint, location-type, geography, status and channel keys.
- **Dates:** one date dimension, 2020-01-01 to 2026-12-31. Active relationship on created, **inactive on closed** (a role-playing date activated only inside measures, a PL-300 staple). Clamp or flag closed dates outside the 2020–snapshot range before relating.
- **Agency dimension:** canonical code after the DCA→DCWP and DOITT→OTI remaps; one name per code (fix the DHS variant); an "311 internal" group.
- **Complaint dimension:** case-normalized key; Category → Type → Descriptor hierarchy; "Other" bucket for the long tail.
- **Geography dimension:** Borough plus an Unknown member; ZIP validated (5-digit 10xxx–14xxx, else Unknown); community board / council district / precinct as attributes. Remember that zip→borough is many-to-many for 25 zips.
- **Status and Channel:** small dimensions; UNKNOWN channel is 8.6%.
- **Storytelling caveats to surface in the report:**
  - Right-censoring of recent months.
  - DOB/DSNY day-precision closes.
  - DOHMH/DOB zero-duration auto-closes.
  - DOT Pending negatives.
  - Median, not mean.
