# Raw audit: nyc311-erm2-nwe9-snapshot, full, role window

NorthLedger stage-1 profile of the extract as received (no cleaning rule applied). Every file's sha256 and row count were checked against the manifest before loading; every column is stored as text, exactly as read.

- Rows: 7,542,606 from 24 file(s)
- Data Health Score: 96.6 / 100
- Facts: 38 SQL facts, 38 reproduced on re-run

| Column | Type guess | Null-like | Null-like % | Distinct | Notes |
|---|---|---|---|---|---|
| unique_key | numeric | 0 | 0.0 | 7,542,606 | 7,542,606 of 7,542,606 numbers are stored as text; they will sort '10' before '9'. |
| created_date | date | 0 | 0.0 | 6,214,276 | day/month order read from the values: month-first, because 4,551,974 date(s) have a second part above 12. |
| closed_date | date | 197,015 | 2.6 | 4,927,647 | day/month order read from the values: month-first, because 4,412,837 date(s) have a second part above 12.; 2.6% null-like (197,015 of 7,542,606 values). |
| agency | text | 0 | 0.0 | 16 |  |
| agency_name | text | 0 | 0.0 | 16 |  |
| complaint_type | text | 0 | 0.0 | 205 | 205 distinct values collapse to 201 once trimmed and lowercased; casing/padding is splitting the same real value. |
| descriptor | text | 175,069 | 2.3 | 1,066 | 1,066 distinct values collapse to 1,062 once trimmed and lowercased; casing/padding is splitting the same real value.; 2.3% null-like (175,069 of 7,542,606 values). |
| location_type | text | 931,547 | 12.4 | 160 | 160 distinct values collapse to 159 once trimmed and lowercased; casing/padding is splitting the same real value.; 12.4% null-like (931,547 of 7,542,606 values). |
| incident_zip | numeric | 65,740 | 0.9 | 441 | mixed content: 0 date-like, 7,476,863 numeric and 3 text values.; 7,476,863 of 7,476,863 numbers are stored as text; they will sort '10' before '9'.; 0.9% null-like (65,740 of 7,54 |
| borough | text | 0 | 0.0 | 6 |  |
| city | text | 355,161 | 4.7 | 318 | 318 distinct values collapse to 258 once trimmed and lowercased; casing/padding is splitting the same real value.; 4.7% null-like (355,161 of 7,542,606 values). |
| status | text | 0 | 0.0 | 7 |  |
| resolution_action_updated_date | date | 74,776 | 1.0 | 4,608,232 | day/month order read from the values: month-first, because 4,492,889 date(s) have a second part above 12.; 1.0% null-like (74,776 of 7,542,606 values). |
| community_board | text | 0 | 0.0 | 77 |  |
| council_district | numeric | 164,208 | 2.2 | 51 | 7,378,398 of 7,378,398 numbers are stored as text; they will sort '10' before '9'.; 2.2% null-like (164,208 of 7,542,606 values). |
| police_precinct | text | 0 | 0.0 | 78 |  |
| open_data_channel_type | text | 0 | 0.0 | 5 |  |
| latitude | numeric | 129,655 | 1.7 | 821,483 | 7,412,951 of 7,412,951 numbers are stored as text; they will sort '10' before '9'.; 1.7% null-like (129,655 of 7,542,606 values). |
| longitude | numeric | 129,655 | 1.7 | 821,490 | 7,412,951 of 7,412,951 numbers are stored as text; they will sort '10' before '9'.; 1.7% null-like (129,655 of 7,542,606 values). |

## Facts

- extract_window holds 7542606 rows across 19 columns [raw.rows]
- 2,222,826 of 143,309,514 cells in extract_window are missing (empty, or a placeholder such as N/A or #N/A) [raw.null_like_cells]
- extract_window scores 98.4/100 on completeness [raw.completeness_pct]
- 0 of 7542606 rows in extract_window are exact duplicates of another row [raw.duplicate_rows]
- 0 rows in extract_window are dated after 2026-09-23 in column created_date [raw.future_dated_rows]
- 12.4% of extract_window.location_type is null-like [raw.col.location_type.null_like_pct]
- 4.7% of extract_window.city is null-like [raw.col.city.null_like_pct]
- 180,866 of the 197,015 empty values in extract_window.closed_date are on rows whose status is not 'Closed', while only 16,149 of the 7,340,869 rows where status is 'Closed' lack one. The gaps follow status, so they come from how those records work (the value may not exist yet, or may never be collected there) rather than from random loss. Confirm with whoever owns the data [raw.col.closed_date.gaps_follow.status]
- 16,149 rows in extract_window have status 'Closed' but no closed_date. Everywhere else status is 'Closed', closed_date is present, so these are the gaps to fix [raw.col.closed_date.null_like_where.status]
- 10,328 values in extract_window.complaint_type are letter-case variants of a more common spelling, so one category is counted as several [raw.col.complaint_type.variant_spellings]
- 152,354 values in extract_window.descriptor are placeholders for a missing value (such as 'N/A', '#N/A' or a blank) rather than true NULLs, so counts and joins treat them as real [raw.col.descriptor.placeholder_values]
- 394 values in extract_window.descriptor are letter-case variants of a more common spelling, so one category is counted as several [raw.col.descriptor.variant_spellings]
- 3,729 values in extract_window.location_type are placeholders for a missing value (such as 'N/A', '#N/A' or a blank) rather than true NULLs, so counts and joins treat them as real [raw.col.location_type.placeholder_values]
- 14,943 values in extract_window.location_type are letter-case variants of a more common spelling, so one category is counted as several [raw.col.location_type.variant_spellings]
- 3 values in extract_window.incident_zip are placeholders for a missing value (such as 'N/A', '#N/A' or a blank) rather than true NULLs, so counts and joins treat them as real [raw.col.incident_zip.placeholder_values]
- 6,319 values in extract_window.borough break the column's UPPER-case convention, so one value can be stored several ways [raw.col.borough.off_convention_casing]
- 2 values in extract_window.city are placeholders for a missing value (such as 'N/A', '#N/A' or a blank) rather than true NULLs, so counts and joins treat them as real [raw.col.city.placeholder_values]
- 431 values in extract_window.city break the column's UPPER-case convention, so one value can be stored several ways [raw.col.city.off_convention_casing]
- 95,926 values in extract_window.community_board break the column's UPPER-case convention, so one value can be stored several ways [raw.col.community_board.off_convention_casing]
- 0 values in unique_key are blank or a missing-value placeholder [raw.col.unique_key.null_like_count]
- 0 values in created_date are blank or a missing-value placeholder [raw.col.created_date.null_like_count]
- 197,015 values in closed_date are blank or a missing-value placeholder [raw.col.closed_date.null_like_count]
- 0 values in agency are blank or a missing-value placeholder [raw.col.agency.null_like_count]
- 0 values in agency_name are blank or a missing-value placeholder [raw.col.agency_name.null_like_count]
- 0 values in complaint_type are blank or a missing-value placeholder [raw.col.complaint_type.null_like_count]
- 175,069 values in descriptor are blank or a missing-value placeholder [raw.col.descriptor.null_like_count]
- 931,547 values in location_type are blank or a missing-value placeholder [raw.col.location_type.null_like_count]
- 65,740 values in incident_zip are blank or a missing-value placeholder [raw.col.incident_zip.null_like_count]
- 0 values in borough are blank or a missing-value placeholder [raw.col.borough.null_like_count]
- 355,161 values in city are blank or a missing-value placeholder [raw.col.city.null_like_count]
- 0 values in status are blank or a missing-value placeholder [raw.col.status.null_like_count]
- 74,776 values in resolution_action_updated_date are blank or a missing-value placeholder [raw.col.resolution_action_updated_date.null_like_count]
- 0 values in community_board are blank or a missing-value placeholder [raw.col.community_board.null_like_count]
- 164,208 values in council_district are blank or a missing-value placeholder [raw.col.council_district.null_like_count]
- 0 values in police_precinct are blank or a missing-value placeholder [raw.col.police_precinct.null_like_count]
- 0 values in open_data_channel_type are blank or a missing-value placeholder [raw.col.open_data_channel_type.null_like_count]
- 129,655 values in latitude are blank or a missing-value placeholder [raw.col.latitude.null_like_count]
- 129,655 values in longitude are blank or a missing-value placeholder [raw.col.longitude.null_like_count]
