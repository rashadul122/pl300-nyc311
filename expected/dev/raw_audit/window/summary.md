# Raw audit: nyc311-erm2-nwe9-snapshot, dev, role window

NorthLedger stage-1 profile of the extract as received (no cleaning rule applied). Every file's sha256 and row count were checked against the manifest before loading; every column is stored as text, exactly as read.

- Rows: 301,688 from 24 file(s)
- Data Health Score: 96.8 / 100
- Facts: 36 SQL facts, 36 reproduced on re-run

| Column | Type guess | Null-like | Null-like % | Distinct | Notes |
|---|---|---|---|---|---|
| unique_key | numeric | 0 | 0.0 | 301,688 | 301,688 of 301,688 numbers are stored as text; they will sort '10' before '9'. |
| created_date | date | 0 | 0.0 | 297,486 | day/month order read from the values: month-first, because 182,063 date(s) have a second part above 12. |
| closed_date | date | 7,874 | 2.6 | 270,760 | day/month order read from the values: month-first, because 176,456 date(s) have a second part above 12.; 2.6% null-like (7,874 of 301,688 values). |
| agency | text | 0 | 0.0 | 16 |  |
| agency_name | text | 0 | 0.0 | 16 |  |
| complaint_type | text | 0 | 0.0 | 186 | 186 distinct values collapse to 184 once trimmed and lowercased; casing/padding is splitting the same real value. |
| descriptor | text | 6,970 | 2.3 | 871 | 871 distinct values collapse to 868 once trimmed and lowercased; casing/padding is splitting the same real value.; 2.3% null-like (6,970 of 301,688 values). |
| location_type | text | 37,179 | 12.3 | 131 | 131 distinct values collapse to 130 once trimmed and lowercased; casing/padding is splitting the same real value.; 12.3% null-like (37,179 of 301,688 values). |
| incident_zip | numeric | 2,649 | 0.9 | 245 | 299,039 of 299,039 numbers are stored as text; they will sort '10' before '9'.; 0.9% null-like (2,649 of 301,688 values). |
| borough | text | 0 | 0.0 | 6 |  |
| city | text | 14,427 | 4.8 | 67 | 67 distinct values collapse to 61 once trimmed and lowercased; casing/padding is splitting the same real value.; 4.8% null-like (14,427 of 301,688 values). |
| status | text | 0 | 0.0 | 7 |  |
| resolution_action_updated_date | date | 2,998 | 1.0 | 240,001 | day/month order read from the values: month-first, because 179,672 date(s) have a second part above 12.; 1.0% null-like (2,998 of 301,688 values). |
| community_board | text | 0 | 0.0 | 77 |  |
| council_district | numeric | 6,661 | 2.2 | 51 | 295,027 of 295,027 numbers are stored as text; they will sort '10' before '9'.; 2.2% null-like (6,661 of 301,688 values). |
| police_precinct | text | 0 | 0.0 | 78 |  |
| open_data_channel_type | text | 0 | 0.0 | 5 |  |
| latitude | numeric | 5,232 | 1.7 | 149,462 | 296,456 of 296,456 numbers are stored as text; they will sort '10' before '9'.; 1.7% null-like (5,232 of 301,688 values). |
| longitude | numeric | 5,232 | 1.7 | 149,462 | 296,456 of 296,456 numbers are stored as text; they will sort '10' before '9'.; 1.7% null-like (5,232 of 301,688 values). |

## Facts

- extract_window holds 301688 rows across 19 columns [raw.rows]
- 89,222 of 5,732,072 cells in extract_window are missing (empty, or a placeholder such as N/A or #N/A) [raw.null_like_cells]
- extract_window scores 98.4/100 on completeness [raw.completeness_pct]
- 0 of 301688 rows in extract_window are exact duplicates of another row [raw.duplicate_rows]
- 0 rows in extract_window are dated after 2026-09-23 in column created_date [raw.future_dated_rows]
- 12.3% of extract_window.location_type is null-like [raw.col.location_type.null_like_pct]
- 4.8% of extract_window.city is null-like [raw.col.city.null_like_pct]
- 7,225 of the 7,874 empty values in extract_window.closed_date are on rows whose status is not 'Closed', while only 649 of the 293,621 rows where status is 'Closed' lack one. The gaps follow status, so they come from how those records work (the value may not exist yet, or may never be collected there) rather than from random loss. Confirm with whoever owns the data [raw.col.closed_date.gaps_follow.status]
- 649 rows in extract_window have status 'Closed' but no closed_date. Everywhere else status is 'Closed', closed_date is present, so these are the gaps to fix [raw.col.closed_date.null_like_where.status]
- 384 values in extract_window.complaint_type are letter-case variants of a more common spelling, so one category is counted as several [raw.col.complaint_type.variant_spellings]
- 6,059 values in extract_window.descriptor are placeholders for a missing value (such as 'N/A', '#N/A' or a blank) rather than true NULLs, so counts and joins treat them as real [raw.col.descriptor.placeholder_values]
- 21 values in extract_window.descriptor are letter-case variants of a more common spelling, so one category is counted as several [raw.col.descriptor.variant_spellings]
- 143 values in extract_window.location_type are placeholders for a missing value (such as 'N/A', '#N/A' or a blank) rather than true NULLs, so counts and joins treat them as real [raw.col.location_type.placeholder_values]
- 574 values in extract_window.location_type are letter-case variants of a more common spelling, so one category is counted as several [raw.col.location_type.variant_spellings]
- 249 values in extract_window.borough break the column's UPPER-case convention, so one value can be stored several ways [raw.col.borough.off_convention_casing]
- 19 values in extract_window.city break the column's UPPER-case convention, so one value can be stored several ways [raw.col.city.off_convention_casing]
- 3,928 values in extract_window.community_board break the column's UPPER-case convention, so one value can be stored several ways [raw.col.community_board.off_convention_casing]
- 0 values in unique_key are blank or a missing-value placeholder [raw.col.unique_key.null_like_count]
- 0 values in created_date are blank or a missing-value placeholder [raw.col.created_date.null_like_count]
- 7,874 values in closed_date are blank or a missing-value placeholder [raw.col.closed_date.null_like_count]
- 0 values in agency are blank or a missing-value placeholder [raw.col.agency.null_like_count]
- 0 values in agency_name are blank or a missing-value placeholder [raw.col.agency_name.null_like_count]
- 0 values in complaint_type are blank or a missing-value placeholder [raw.col.complaint_type.null_like_count]
- 6,970 values in descriptor are blank or a missing-value placeholder [raw.col.descriptor.null_like_count]
- 37,179 values in location_type are blank or a missing-value placeholder [raw.col.location_type.null_like_count]
- 2,649 values in incident_zip are blank or a missing-value placeholder [raw.col.incident_zip.null_like_count]
- 0 values in borough are blank or a missing-value placeholder [raw.col.borough.null_like_count]
- 14,427 values in city are blank or a missing-value placeholder [raw.col.city.null_like_count]
- 0 values in status are blank or a missing-value placeholder [raw.col.status.null_like_count]
- 2,998 values in resolution_action_updated_date are blank or a missing-value placeholder [raw.col.resolution_action_updated_date.null_like_count]
- 0 values in community_board are blank or a missing-value placeholder [raw.col.community_board.null_like_count]
- 6,661 values in council_district are blank or a missing-value placeholder [raw.col.council_district.null_like_count]
- 0 values in police_precinct are blank or a missing-value placeholder [raw.col.police_precinct.null_like_count]
- 0 values in open_data_channel_type are blank or a missing-value placeholder [raw.col.open_data_channel_type.null_like_count]
- 5,232 values in latitude are blank or a missing-value placeholder [raw.col.latitude.null_like_count]
- 5,232 values in longitude are blank or a missing-value placeholder [raw.col.longitude.null_like_count]
