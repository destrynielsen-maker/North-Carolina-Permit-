# Mecklenburg commercial open-data compliance and historical snapshot

**Date:** November 12, 2026  
**Status:** Live GIS polling disabled; 701 previously screened permit records preserved as a read-only historical snapshot.

## Why we changed this

The official [Mecklenburg County GIS Open Mapping Reuse Policy](https://maps.mecklenburgcountync.gov/openmapping/index.html) allows lawful reuse of downloaded GIS files in commercial products but prohibits commercial applications from integrating with or continuously consuming the county's live API, web, and map services. Commercial consumers must download and host their own copies.

The county's [Open Mapping Data catalog](https://maps.mecklenburgcountync.gov/openmapping/data.html) provides **Accela Building Permits** and **Accela Permits** downloadable data, as well as the distinct legacy **Winchester Building Permits** set. Dataset download and local processing is the appropriate future integration, not live ArcGIS polling by the hosted sales application.

## Implemented changes

- In `src/collect.py`, the `mecklenburg` source is set `enabled=False` and `snapshot_only=True`. The scheduled collector never calls the county's GIS endpoint.
- The first revised collection freezes the pre-pause Mecklenburg records to `public/data/mecklenburg_snapshot.json`; future collection runs read this local archive and **do not replace it** with new ArcGIS data.
- Every archived record in the displayed dataset is marked `collection_mode=historic_snapshot`, `snapshot_as_of_utc=2026-11-12T22:34:56.402783+00:00`, with a warning that current status is unverified.
- The records remain accessible through our existing `permit.html?id=...` links, including subdivision/parcel/building-area information from the historical snapshot.
- The main dashboard defaults to **Current collections**; a selector can include/show only the historical Charlotte snapshot. Archived records are visually flagged and exported with their collection mode and snapshot date.
- The historical records are excluded from **new-permit RSS**, builder rankings and default current sales-list filtering.
- `public/data/sources.json` records Mecklenburg as `historic snapshot - live API polling disabled`, `qualified=0` and `archived_count=701`. This does not imply that the former records were deleted.
- `public/data/mecklenburg_snapshot_info.json` provides static provenance and a link to the official dataset download/reuse pages.
- `public/data/sales_field_coverage.json` identifies the 701 historical Mecklenburg records separately.

## Confirmed automated result

The first successful refresh with the revised policy reported:

| Market | Current screened permits | Historical snapshot |
|---|---:|---:|
| Raleigh | 781 | 0 |
| New Hanover County | 813 | 0 |
| Greensboro | 879 | 0 |
| Mecklenburg / Charlotte | 0 | 701 |
| **Total** | **2,473** | **701** |

**Total records available for current and historic research: 3,174.** Current screened records are not independently audited sales leads either.

The original invalid Accela ArcGIS contractor pilot was sourced to Anaheim, California, so its source and UI were removed. Its output is explicitly `rejected_wrong_jurisdiction` and cannot be used as a North Carolina contractor source. See [corrected Accela investigation](MECKLENBURG_ACCELA_DISCOVERY.md).

## Guardrails / next steps

- Never call the commercial-prohibited Mecklenburg live API from a GitHub Actions run, backend, or client browser script.
- Keep historical records and export files clearly labeled by their actual snapshot date, rather than implying they are current status.
- Download **official Mecklenburg Accela Building Permits** from the county Open Mapping catalog for local processing. We do not yet have a validated copy of this dataset, so no ungrounded field mapping or builder identification is implemented.
- Upon receiving an actual CSV/ZIP or GeoPackage download, inspect its schema and source metadata, then build a deterministic importer and a non-promoting QA preview before activation.
- Avoid promoting property owners, applicants, or trade subcontractors to general contractors without explicit agency evidence.

The next chunk should implement a local official-download importer and a controlled distribution process rather than attempting an automated county API integration.

## Confirmed final refresh — 2026-11-12T22:51:12.030983+00:00

The revised workflow passed **123 automated tests with 0 failures** (CI check time `2026-11-12T22:50:57.042011+00:00`). The last successfully generated source-status report contains:

- **Current screened:** 2473 (Raleigh, New Hanover, Greensboro)
- **Historic Mecklenburg:** 701 (frozen, collected November 12, 2026)
- **Scheduled Mecklenburg live GIS queries:** disabled
- **New Mecklenburg permits added automatically:** 0

The historical archive is present at `public/data/mecklenburg_snapshot.json`. Current users see active collections by default; they can switch to **Historic Charlotte only** or **Include historic Charlotte** on the dashboard. The permit details explicitly warn that historical status has not been refreshed. Historic source buttons open the County's official open-data **download catalog**, rather than invoking the county's commercial-restricted GIS API through our application.

Both dashboard scripts (`public/index.html` and `public/permit.html`) were separately syntax-checked after the changes; the latest GitHub Pages browser rendering was not independently verified. The collector test suite includes archiving, non-polling, RSS exclusion, snapshot immutability and historical display tests.

**Release conclusion:** Commercial-use compliance safeguard implemented. Next implement the local downloadable Mecklenburg Accela Building Permits importer after an actual official dataset file is available. Do not revert to periodic live API polling.
