DHWANI-SANJEEVANI FACILITY DATA AUDIT
===================================

Input source: geocode_health_centre.csv (user-supplied file)
Resource URL recorded in metadata: https://www.data.gov.in/resource/all-india-health-centres-directory-7th-october-2016
The supplied filename is consistent with the All India Health Centres Directory resource dated 7 October 2016. Treat this as an older reference directory, not a current authoritative operational list; confirm the exact source version and refresh date before production.

Total source health-centre records: 200,438
Filtered PHC + CHC records: 35,122
PHC records: 29,733
CHC records: 5,389
Coordinates within broad India envelope: 34,936
Records needing coordinate review: 186
Records flagged for possible duplicate name in same state/district: 296

IMPORTANT LIMITATIONS
- This dataset is a facility directory, NOT an ASV inventory.
- Every ASV status is UNKNOWN / NOT_VERIFIED in the inventory template.
- A coordinate passing the broad bounds check is not independently validated against official maps.
- Suspect coordinate records are preserved separately and should not be used for nearby search until fixed from an authoritative source.
- Possible duplicate names are flagged but not deleted; duplicate locations need manual/authoritative reconciliation.
- State labels are preserved as supplied, including separate "Andhra Pradesh" and "Andhra Pradesh Old" labels. Do not merge without validating source semantics.
- No claim is made that PHCs or CHCs consistently have ASV. Real inventory requires authorised, current confirmation.

OUTPUT FILES
- phc_chc_facilities_clean.csv: all PHC/CHC rows, with coordinate flags and inventory fields marked unknown.
- phc_chc_facilities_for_nearby_search.json: coordinate records passing broad validation for FastAPI nearest-facility lookup.
- phc_chc_facilities_for_nearby_search.geojson: same valid-location subset for map tools.
- phc_chc_coordinate_review.csv: records with missing/non-numeric or suspicious coordinates.
- asv_inventory_template.csv: separate inventory schema, statuses intentionally UNKNOWN.
- state_summary.csv: state-wise counts.
