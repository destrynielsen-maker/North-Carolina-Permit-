# Chunk 6 — post-Mecklenburg validation, contractor normalization and Wake safeguards

**Date:** 2026-11-12. **Status:** Code and 27 offline tests complete; first post-change collector refresh confirmed; official record-level verification pending.

## Post-fix live collection evidence

GitHub `public/data/sources.json` at `2026-11-12T18:56:03Z`:

| Market | Records scanned | Screened new-construction candidates |
|---|---:|---:|
| Raleigh | 3,005 | 781 |
| New Hanover County | 21,445 | 813 |
| Mecklenburg County / Charlotte | 1,729 | 701 |
| Greensboro | 3,594 | 879 |
| **Total** | **29,773** | **3,174** |

Mecklenburg increased **7 -> 701** after the word-bounded `new bldg` change. Aggregated rejection reasons changed from 815 `no_explicit_new_construction` and 907 `excluded_work_or_trade` before the fix to 121 and 907 after the fix. This strongly supports a lexical undercount but **does not independently certify the newly accepted 694 permits**.

The project still sets `live_verified=false` and shows the data as screened candidates.

## Chunk 6 changes

- Exclude additional permit statuses: on hold, stop work order, and revoked, even when issue dates and new-build descriptions exist.
- Normalize builder grouping **conservatively** for case, punctuation and known license-decorations. Preserve legal-entity and trading-as detail, and expose `aliases` on each builder rollup. The original `builder`, `projects`, `valuation` and `jurisdictions` fields remain for dashboard compatibility.
- Create `public/data/overlap_audit.json` after successful scans. It counts exact cross-source permit-number collisions, separately tracking when issue dates also match, without deleting or merging any permits. Address similarity never constitutes proof of identity.
- Add four unit tests for the status, builder and cross-source collision policies. **27 tests passed in the local development environment.** The later generated-data commit provides evidence that the workflow passed its test and collection stages, but the Pages deployment stage was not independently inspected.
- Do not turn on Wake County until a trustworthy issue date, issuer jurisdiction and overlap rule are validated.

## Record-level validation limitations

Observed an independent listing for Raleigh permit `BLDR-049954-2026` at 2100 Breeze Rd and contractor Allure Homes, LLC, which matches the project's published RSS snapshot; the third-party listing labels its date as filing, **not official issuance**, so it is partial corroboration only. The issuing agency's permit detail has not been directly verified in this checkpoint. Source schema verification and individual permit verification are different steps.

Primary official sources:
- Raleigh: https://services.arcgis.com/v400IkDOw1ad7Yad/arcgis/rest/services/Building_Permits_Issued_Past_180_Days/FeatureServer/0
- Mecklenburg: https://meckgis.mecklenburgcountync.gov/server/rest/services/BuildingPermits/FeatureServer/0
- Greensboro: https://gis.greensboro-nc.gov/arcgis/rest/services/EngineeringInspections/BuildingPermits_MS/MapServer/6
- New Hanover: https://gisport.nhcgov.com/server/rest/services/Thematic/BuildingPermits/FeatureServer/0

## Wake County decision: not enabled

Official Wake data catalog: https://catalog.data.gov/dataset/building-permits-ff506 . The Wake open-data dataset says permit records are geocoded nightly and legacy records may be incomplete; its ArcGIS URL is https://maps.wake.gov/arcgis/rest/services/Inspections/Building_Permits/MapServer/0 . The endpoint could not be independently interrogated during this checkpoint.

**Gates before enabling:** confirm authoritative issue-date and status fields; exact issuer identifiers and source coverage; City of Raleigh overlap; source-specific permit IDs and duplicate-review audit; live sample of new-build vs alteration/trade records; tests. Avoid comparing street address alone and avoid stripping punctuation from permit IDs to create artificial equivalence.

## Next chunk

1. Confirm the 27-test GitHub workflow, refreshed builder aliases and overlap report.
2. Official record-level spot checks, especially newly included Mecklenburg new-building records.
3. Complete Wake schema/jurisdiction discovery; enable only if data and duplicate gates pass.
4. Expand to at least one additional quality source (e.g. Johnston, Brunswick, Cabarrus or Buncombe), subject to authoritative issued-date and eligibility fields.

## First post-Chunk-6 live refresh confirmed

`public/data/sources.json` reports a new collection at **2026-11-12 19:02:03 UTC** with the same screened market totals: Raleigh 781, New Hanover 813, Mecklenburg 701 and Greensboro 879 (total **3,174**).

New `public/data/overlap_audit.json` is present with `wake_enabled=false` and **zero exact cross-source permit-number collision pairs** across active markets. This is a baseline, not proof of perfect project de-duplication.

The updated `public/data/builders.json` contains **378 builder groups**, with **five groups** retaining multiple source-name variants after conservative normalization. For example, the two punctuation/case spellings of **Stanley Martin Homes LLC** now total **116 screened projects** in one displayed group. No fuzzy merging of different legal entities was performed.

**Still pending:** agency-level verification of sample issued permits, Wake source schema/jurisdiction, and explicit confirmation of the Pages deployment step for this refresh.
