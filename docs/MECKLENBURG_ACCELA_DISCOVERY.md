# Mecklenburg / Charlotte — current Accela building permits contractor-source pilot

**Date:** November 12, 2026  
**Status:** Read-only official ArcGIS pilot. No changes to production permit or builder rankings.

## Critical source distinction

Our 701 current screened Charlotte-area records came from the county's older `BuildingPermits/FeatureServer/0` GIS layer, which has project, property and size fields but does not publish the building general contractor.

The county's [Building Permits Issued Daily](https://code.mecknc.gov/node/1041) report describes a contractor filter and CSV/Excel exports. However, the [county statistical reporting page](https://code.mecknc.gov/site-menu/public-records/statistical-data) explains that some historical reporting relates to legacy permit portals and updated Accela statistical reporting is still in development. **We cannot assume an exported contractor row matches a current Accela record merely because both came from Mecklenburg County.**

A better official source was discovered independently:

**[Accela Building Permits — official ArcGIS FeatureServer layer](https://services3.arcgis.com/hPs600I3X0RTaaaq/arcgis/rest/services/Accela_Building_Permits/FeatureServer/0)**

The layer's published schema includes:

| Purpose | Field |
|---|---|
| Permit/case reference | `casenumber` |
| Recorded status | `casestatus` |
| Issued date | `permitissued` (ArcGIS date) |
| Work classification | `typeofwork` |
| Building description | `description` |
| Residential/commercial | `comres` |
| Address and parcel | `address`, `parcel` |
| Job valuation | `jobvaluation` |
| Contractor as published | `contractorsname` |
| Contractor phone as published | `contractorsphone` |
| Owner-builder flag | `ownerbuilder` |
| Exact feature query | `OBJECTID` |

The presence of `contractorsname` and `contractorsphone` gives us a potential authoritative way to produce actionable Charlotte leads without using a third-party contractor directory or silently substituting an owner for the builder. Whether each row identifies the responsible **prime builder** still requires checking source semantics and actual permits.

## Implemented bounded pilot

`src/probe_mecklenburg_accela.py` is a read-only, source-scoped discovery check. It:

1. Checks the official layer's schema before processing records.
2. Requests up to **250** recently issued building records, ordered by real issue date, not application date.
3. Rejects missing/old/future dates, void/pending statuses, trade-only work, and records without explicit new-building evidence.
4. Counts current contractor and business phone availability among *screened new-construction records*.
5. Compares **exact case numbers** to the 701 previously screened Charlotte records, reporting overlap as a diagnostic only. It never merges records solely by address or company name.
6. Outputs a maximum of **12** clearly labeled government-source research candidates, each with case number, issue date, type, address, contractor and phone **as listed**, and a direct exact ArcGIS `OBJECTID` query.
7. Never writes `permits.json`, builder rankings, RSS, the live county source list or other customer-facing sales feeds.

The result is `public/data/mecklenburg_accela_pilot.json` after a successful GitHub workflow run. On request or schema failure, the pilot records a non-promotion error instead of producing false leads. The separate `tests/test_mecklenburg_accela_pilot.py` contains **10 synthetic tests** of schema controls, new-building screening, contractor attribution, phone hygiene, exact-ID comparison and fail-closed behavior.

## Promotion gates

Before adding Accela records to the main North Carolina dashboard:

- Inspect real `casestatus`, `typeofwork`, `comres`, `casenumber` and `description` values from the pilot; adjust classification based on evidence.
- Confirm whether source `contractorsname` is a building general contractor or another relationship for this specific layer, and how to interpret `ownerbuilder`.
- Check a small sample of actual individual permit records in the county Accela portal.
- Compare permit identity and project-level overlap with the older GIS feed; exact-number collisions and address overlap need separate treatment.
- Only then consider enabling the Accela source under its own `mecklenburg_accela` identity with the same sales-friendly permit-detail URL style and a separate official source link.

**Do not treat a successful GIS query, a contractor-name field, or a legacy Power BI report as proof of a verified GC on an individual project.**

## Next checkpoint

Review the first pilot output and match counts. If it yields appropriate new-construction candidates and published contractor data, build a conservative live collector for this *new* source rather than joining county statistical reports based on names or addresses.
