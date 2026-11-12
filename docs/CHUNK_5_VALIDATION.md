# Chunk 5 — permit screening validation checkpoint

Date: 2026-11-12

## Live collection baseline before screening change

| Source | Scanned | Qualifying candidates |
|---|---:|---:|
| Raleigh | 3,005 | 781 |
| New Hanover County | 21,445 | 813 |
| Mecklenburg County / Charlotte | 1,729 | 7 |
| Greensboro | 3,594 | 879 |
| **Total** | **29,773** | **2,480** |

Source for these figures: `public/data/sources.json`, collected 2026-11-12 18:50:43Z.

## Mecklenburg root cause and remediation

The published aggregate diagnostics expose permit type values `One/Two Family New Bldg` and `Commercial New Bldg`, but initial new-construction screening did not accept the abbreviation `New Bldg`. As a result, 815 of 1,729 Mecklenburg records were rejected under `no_explicit_new_construction` (distinct from 907 excluded because of alterations, trade work, etc.).

Changed the new-build keyword classifier to recognize the **word-bounded `new bldg` phrase**. A record must still have an actual issue date and valid status, and fail all exclusion checks before being qualified. This is a targeted lexical correction, not a blanket allowance for `New`.

Added four tests covering detached homes, apartments, alterations disguised in new-building permit descriptions, and existing-building permits. All 23 offline tests passed locally.

**New Mecklenburg totals are pending an automated refresh.** The new keyword does not guarantee a specific count increase. Source-based permit-by-permit audit also remains outstanding.

## Greensboro verification

Greensboro's official permit data returned 3,594 issued-date candidate rows in the collection scan, with 879 qualifying after screening. Collector uses source fields `IssuedDate`, `ApplicationType`, `OccupancyDesc`, `Contractor`, and `TotalCost`; detailed record spot-check against the municipal system is still pending.

## Wake County duplicate guard (not yet enabled)

City of Raleigh's building permit feed and Wake County's building-permit feed are separately maintained sources covering overlapping geography and potentially the same permit. Without a verified issuing-jurisdiction, record identity, and cross-source comparison, adding all Wake permits can double count Raleigh opportunities.

- Keep Wake collector **disabled** until official issue-date status fields and exact permit jurisdiction are verified.
- Before enabling, confirm if Wake data includes City of Raleigh permits; construct a tested permit-number + jurisdiction (or agency ID) deduplication policy.
- Do not deduplicate merely by normalized street address: multiple distinct permits can share an address.
- Track scope separately: Wake county/unincorporated jurisdictions vs Raleigh municipal feeds.

## Further requirements

- Independent permit-by-permit confirmation against official source systems before labeling any record as a verified sales lead.
- Refresh the GitHub Actions workflow, compare before/after category distributions and Mecklenburg rejected reasons, and inspect any anomalous increase.
- Keep status `live_verified=false` until the underlying records, not just aggregate schemas, have been sampled.
