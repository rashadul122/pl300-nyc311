# Raw audit: nyc311-erm2-nwe9-snapshot, dev, role carryin

NorthLedger stage-1 profile of the extract as received (no cleaning rule applied). Every file's sha256 and row count were checked against the manifest before loading; every column is stored as text, exactly as read.

- Rows: 8,037 from 1 file(s)
- Data Health Score: 76.0 / 100
- Facts: 35 SQL facts, 35 reproduced on re-run

| Column | Type guess | Null-like | Null-like % | Distinct | Notes |
|---|---|---|---|---|---|
| unique_key | numeric | 0 | 0.0 | 8,037 | 8,037 of 8,037 numbers are stored as text; they will sort '10' before '9'. |
| created_date | date | 0 | 0.0 | 7,996 | day/month order read from the values: month-first, because 5,177 date(s) have a second part above 12. |
| closed_date | date | 2,860 | 35.6 | 4,341 | day/month order read from the values: month-first, because 2,414 date(s) have a second part above 12.; 35.6% null-like (2,860 of 8,037 values). |
| agency | text | 0 | 0.0 | 14 |  |
| agency_name | text | 0 | 0.0 | 14 |  |
| complaint_type | text | 0 | 0.0 | 126 | 126 distinct values collapse to 115 once trimmed and lowercased; casing/padding is splitting the same real value. |
| descriptor | text | 1,202 | 15.0 | 410 | 410 distinct values collapse to 385 once trimmed and lowercased; casing/padding is splitting the same real value.; 15.0% null-like (1,202 of 8,037 values). |
| location_type | text | 1,319 | 16.4 | 59 | 59 distinct values collapse to 58 once trimmed and lowercased; casing/padding is splitting the same real value.; 16.4% null-like (1,319 of 8,037 values). |
| incident_zip | numeric | 442 | 5.5 | 193 | 7,595 of 7,595 numbers are stored as text; they will sort '10' before '9'.; 5.5% null-like (442 of 8,037 values). |
| borough | text | 0 | 0.0 | 6 |  |
| city | text | 713 | 8.9 | 48 | 8.9% null-like (713 of 8,037 values). |
| status | text | 0 | 0.0 | 7 |  |
| resolution_action_updated_date | date | 852 | 10.6 | 5,696 | day/month order read from the values: month-first, because 3,675 date(s) have a second part above 12.; 10.6% null-like (852 of 8,037 values). |
| community_board | text | 0 | 0.0 | 73 |  |
| council_district | numeric | 545 | 6.8 | 51 | 7,492 of 7,492 numbers are stored as text; they will sort '10' before '9'.; 6.8% null-like (545 of 8,037 values). |
| police_precinct | text | 0 | 0.0 | 78 |  |
| open_data_channel_type | text | 0 | 0.0 | 4 |  |
| latitude | numeric | 140 | 1.7 | 6,767 | 7,897 of 7,897 numbers are stored as text; they will sort '10' before '9'.; 1.7% null-like (140 of 8,037 values). |
| longitude | numeric | 140 | 1.7 | 6,767 | 7,897 of 7,897 numbers are stored as text; they will sort '10' before '9'.; 1.7% null-like (140 of 8,037 values). |

## Facts

- extract_carryin holds 8037 rows across 19 columns [raw.rows]
- 8,213 of 152,703 cells in extract_carryin are missing (empty, or a placeholder such as N/A or #N/A) [raw.null_like_cells]
- extract_carryin scores 94.6/100 on completeness [raw.completeness_pct]
- 0 of 8037 rows in extract_carryin are exact duplicates of another row [raw.duplicate_rows]
- 0 rows in extract_carryin are dated after 2026-09-23 in column created_date [raw.future_dated_rows]
- 35.6% of extract_carryin.closed_date is null-like [raw.col.closed_date.null_like_pct]
- 16.4% of extract_carryin.location_type is null-like [raw.col.location_type.null_like_pct]
- 15.0% of extract_carryin.descriptor is null-like [raw.col.descriptor.null_like_pct]
- 170 values in extract_carryin.complaint_type are letter-case variants of a more common spelling, so one category is counted as several [raw.col.complaint_type.variant_spellings]
- 22 values in extract_carryin.descriptor are placeholders for a missing value (such as 'N/A', '#N/A' or a blank) rather than true NULLs, so counts and joins treat them as real [raw.col.descriptor.placeholder_values]
- 127 values in extract_carryin.descriptor are letter-case variants of a more common spelling, so one category is counted as several [raw.col.descriptor.variant_spellings]
- 1 values in extract_carryin.location_type are placeholders for a missing value (such as 'N/A', '#N/A' or a blank) rather than true NULLs, so counts and joins treat them as real [raw.col.location_type.placeholder_values]
- 60 values in extract_carryin.location_type are letter-case variants of a more common spelling, so one category is counted as several [raw.col.location_type.variant_spellings]
- 19 values in extract_carryin.borough break the column's UPPER-case convention, so one value can be stored several ways [raw.col.borough.off_convention_casing]
- 1 values in extract_carryin.city break the column's UPPER-case convention, so one value can be stored several ways [raw.col.city.off_convention_casing]
- 472 values in extract_carryin.community_board break the column's UPPER-case convention, so one value can be stored several ways [raw.col.community_board.off_convention_casing]
- 0 values in unique_key are blank or a missing-value placeholder [raw.col.unique_key.null_like_count]
- 0 values in created_date are blank or a missing-value placeholder [raw.col.created_date.null_like_count]
- 2,860 values in closed_date are blank or a missing-value placeholder [raw.col.closed_date.null_like_count]
- 0 values in agency are blank or a missing-value placeholder [raw.col.agency.null_like_count]
- 0 values in agency_name are blank or a missing-value placeholder [raw.col.agency_name.null_like_count]
- 0 values in complaint_type are blank or a missing-value placeholder [raw.col.complaint_type.null_like_count]
- 1,202 values in descriptor are blank or a missing-value placeholder [raw.col.descriptor.null_like_count]
- 1,319 values in location_type are blank or a missing-value placeholder [raw.col.location_type.null_like_count]
- 442 values in incident_zip are blank or a missing-value placeholder [raw.col.incident_zip.null_like_count]
- 0 values in borough are blank or a missing-value placeholder [raw.col.borough.null_like_count]
- 713 values in city are blank or a missing-value placeholder [raw.col.city.null_like_count]
- 0 values in status are blank or a missing-value placeholder [raw.col.status.null_like_count]
- 852 values in resolution_action_updated_date are blank or a missing-value placeholder [raw.col.resolution_action_updated_date.null_like_count]
- 0 values in community_board are blank or a missing-value placeholder [raw.col.community_board.null_like_count]
- 545 values in council_district are blank or a missing-value placeholder [raw.col.council_district.null_like_count]
- 0 values in police_precinct are blank or a missing-value placeholder [raw.col.police_precinct.null_like_count]
- 0 values in open_data_channel_type are blank or a missing-value placeholder [raw.col.open_data_channel_type.null_like_count]
- 140 values in latitude are blank or a missing-value placeholder [raw.col.latitude.null_like_count]
- 140 values in longitude are blank or a missing-value placeholder [raw.col.longitude.null_like_count]
