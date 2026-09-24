# Raw audit: nyc311-erm2-nwe9-snapshot, full, role carryin

NorthLedger stage-1 profile of the extract as received (no cleaning rule applied). Every file's sha256 and row count were checked against the manifest before loading; every column is stored as text, exactly as read.

- Rows: 201,517 from 1 file(s)
- Data Health Score: 75.8 / 100
- Facts: 35 SQL facts, 35 reproduced on re-run

| Column | Type guess | Null-like | Null-like % | Distinct | Notes |
|---|---|---|---|---|---|
| unique_key | numeric | 0 | 0.0 | 201,517 | 201,517 of 201,517 numbers are stored as text; they will sort '10' before '9'. |
| created_date | date | 0 | 0.0 | 186,622 | day/month order read from the values: month-first, because 129,128 date(s) have a second part above 12. |
| closed_date | date | 71,716 | 35.6 | 67,238 | day/month order read from the values: month-first, because 60,413 date(s) have a second part above 12.; 35.6% null-like (71,716 of 201,517 values). |
| agency | text | 0 | 0.0 | 15 |  |
| agency_name | text | 0 | 0.0 | 15 |  |
| complaint_type | text | 0 | 0.0 | 181 | 181 distinct values collapse to 168 once trimmed and lowercased; casing/padding is splitting the same real value. |
| descriptor | text | 30,277 | 15.0 | 779 | 779 distinct values collapse to 740 once trimmed and lowercased; casing/padding is splitting the same real value.; 15.0% null-like (30,277 of 201,517 values). |
| location_type | text | 32,354 | 16.1 | 110 | 110 distinct values collapse to 109 once trimmed and lowercased; casing/padding is splitting the same real value.; 16.1% null-like (32,354 of 201,517 values). |
| incident_zip | numeric | 11,128 | 5.5 | 243 | 190,389 of 190,389 numbers are stored as text; they will sort '10' before '9'.; 5.5% null-like (11,128 of 201,517 values). |
| borough | text | 0 | 0.0 | 6 |  |
| city | text | 17,477 | 8.7 | 76 | 76 distinct values collapse to 67 once trimmed and lowercased; casing/padding is splitting the same real value.; 8.7% null-like (17,477 of 201,517 values). |
| status | text | 0 | 0.0 | 7 |  |
| resolution_action_updated_date | date | 21,527 | 10.7 | 108,383 | day/month order read from the values: month-first, because 91,601 date(s) have a second part above 12.; 10.7% null-like (21,527 of 201,517 values). |
| community_board | text | 0 | 0.0 | 77 |  |
| council_district | numeric | 13,811 | 6.9 | 51 | 187,706 of 187,706 numbers are stored as text; they will sort '10' before '9'.; 6.9% null-like (13,811 of 201,517 values). |
| police_precinct | text | 0 | 0.0 | 78 |  |
| open_data_channel_type | text | 0 | 0.0 | 5 |  |
| latitude | numeric | 3,668 | 1.8 | 102,574 | 197,849 of 197,849 numbers are stored as text; they will sort '10' before '9'.; 1.8% null-like (3,668 of 201,517 values). |
| longitude | numeric | 3,668 | 1.8 | 102,573 | 197,849 of 197,849 numbers are stored as text; they will sort '10' before '9'.; 1.8% null-like (3,668 of 201,517 values). |

## Facts

- extract_carryin holds 201517 rows across 19 columns [raw.rows]
- 205,626 of 3,828,823 cells in extract_carryin are missing (empty, or a placeholder such as N/A or #N/A) [raw.null_like_cells]
- extract_carryin scores 94.6/100 on completeness [raw.completeness_pct]
- 0 of 201517 rows in extract_carryin are exact duplicates of another row [raw.duplicate_rows]
- 0 rows in extract_carryin are dated after 2026-09-23 in column created_date [raw.future_dated_rows]
- 35.6% of extract_carryin.closed_date is null-like [raw.col.closed_date.null_like_pct]
- 16.1% of extract_carryin.location_type is null-like [raw.col.location_type.null_like_pct]
- 15.0% of extract_carryin.descriptor is null-like [raw.col.descriptor.null_like_pct]
- 4,017 values in extract_carryin.complaint_type are letter-case variants of a more common spelling, so one category is counted as several [raw.col.complaint_type.variant_spellings]
- 584 values in extract_carryin.descriptor are placeholders for a missing value (such as 'N/A', '#N/A' or a blank) rather than true NULLs, so counts and joins treat them as real [raw.col.descriptor.placeholder_values]
- 3,236 values in extract_carryin.descriptor are letter-case variants of a more common spelling, so one category is counted as several [raw.col.descriptor.variant_spellings]
- 25 values in extract_carryin.location_type are placeholders for a missing value (such as 'N/A', '#N/A' or a blank) rather than true NULLs, so counts and joins treat them as real [raw.col.location_type.placeholder_values]
- 1,337 values in extract_carryin.location_type are letter-case variants of a more common spelling, so one category is counted as several [raw.col.location_type.variant_spellings]
- 504 values in extract_carryin.borough break the column's UPPER-case convention, so one value can be stored several ways [raw.col.borough.off_convention_casing]
- 38 values in extract_carryin.city break the column's UPPER-case convention, so one value can be stored several ways [raw.col.city.off_convention_casing]
- 11,988 values in extract_carryin.community_board break the column's UPPER-case convention, so one value can be stored several ways [raw.col.community_board.off_convention_casing]
- 0 values in unique_key are blank or a missing-value placeholder [raw.col.unique_key.null_like_count]
- 0 values in created_date are blank or a missing-value placeholder [raw.col.created_date.null_like_count]
- 71,716 values in closed_date are blank or a missing-value placeholder [raw.col.closed_date.null_like_count]
- 0 values in agency are blank or a missing-value placeholder [raw.col.agency.null_like_count]
- 0 values in agency_name are blank or a missing-value placeholder [raw.col.agency_name.null_like_count]
- 0 values in complaint_type are blank or a missing-value placeholder [raw.col.complaint_type.null_like_count]
- 30,277 values in descriptor are blank or a missing-value placeholder [raw.col.descriptor.null_like_count]
- 32,354 values in location_type are blank or a missing-value placeholder [raw.col.location_type.null_like_count]
- 11,128 values in incident_zip are blank or a missing-value placeholder [raw.col.incident_zip.null_like_count]
- 0 values in borough are blank or a missing-value placeholder [raw.col.borough.null_like_count]
- 17,477 values in city are blank or a missing-value placeholder [raw.col.city.null_like_count]
- 0 values in status are blank or a missing-value placeholder [raw.col.status.null_like_count]
- 21,527 values in resolution_action_updated_date are blank or a missing-value placeholder [raw.col.resolution_action_updated_date.null_like_count]
- 0 values in community_board are blank or a missing-value placeholder [raw.col.community_board.null_like_count]
- 13,811 values in council_district are blank or a missing-value placeholder [raw.col.council_district.null_like_count]
- 0 values in police_precinct are blank or a missing-value placeholder [raw.col.police_precinct.null_like_count]
- 0 values in open_data_channel_type are blank or a missing-value placeholder [raw.col.open_data_channel_type.null_like_count]
- 3,668 values in latitude are blank or a missing-value placeholder [raw.col.latitude.null_like_count]
- 3,668 values in longitude are blank or a missing-value placeholder [raw.col.longitude.null_like_count]
