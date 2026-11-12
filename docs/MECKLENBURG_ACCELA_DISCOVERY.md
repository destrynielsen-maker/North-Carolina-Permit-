# Mecklenburg Accela investigation — source correction and withdrawal

**Updated November 12, 2026**

## Critical retraction

An ArcGIS layer initially investigated as a Mecklenburg County "Accela Building Permits" contractor source:

`https://services3.arcgis.com/hPs600I3X0RTaaaq/arcgis/rest/services/Accela_Building_Permits/FeatureServer/0`

was **incorrectly attributed to Mecklenburg County, North Carolina**. Its coordinate reference system is California State Plane Zone VI, and subsequent source checking established that the data belonged to **Anaheim, California**.

The initial read-only pilot was immediately **withdrawn** when this was discovered. The code that queried the source, its tests, and the false research panel were removed. The original pilot output was replaced with a `rejected_wrong_jurisdiction` marker and **zero eligible North Carolina records**. **No Anaheim permit or contractor records entered the production North Carolina leads.**

**Do not reuse the ArcGIS URL above for any North Carolina sales intelligence.** Its field schema is *not* evidence of a Mecklenburg government builder/GC source.

## Mecklenburg's actual current source options

The County's [Open Mapping portal](https://maps.mecklenburgcountync.gov/openmapping/data.html) lists downloadable **Accela Building Permits** (current building permits), **Accela Permits** (all permit types), and a separately named **Winchester Building Permits** legacy dataset.

The official county [Reuse Policy](https://maps.mecklenburgcountync.gov/openmapping/index.html) allows commercial reuse of **downloaded, locally hosted copies**, but specifically **prohibits commercial apps from continuously querying County live map/API services**. Therefore:

- Scheduled calls to `https://meckgis.mecklenburgcountync.gov/server/rest/services/BuildingPermits/FeatureServer/0` have been disabled in the North Carolina collector.
- The last previously collected **701** screened Mecklenburg records remain available as a **frozen historic snapshot**, dated **November 12, 2026**.
- Historical records are clearly labeled, excluded by default from current sales opportunities, and not included in new-permit RSS feeds or builder rankings.
- Current live collection now covers Raleigh, New Hanover County, and Greensboro; Mecklenburg will return only after a local/offline import from permitted official downloads with source and classification validation.

No official Mecklenburg builder field or prime-contractor mapping has been established from the actual published County GIS dataset. Do not substitute property owners, applicants, or subcontractors for building GCs.

## Recommended compliant replacement

1. Visit the [official Mecklenburg Open Mapping Data catalog](https://maps.mecklenburgcountync.gov/openmapping/data.html) and download the published **Accela Building Permits** file in the supported format (CSV/ZIP or GeoPackage).
2. Retain the dated downloaded file locally or within a controlled organization-owned storage area; record the download time, filename, size and source catalogue link.
3. Inspect the actual downloaded schema and specifically determine whether it has an explicit general contractor field and authoritative issued-date/work-class fields.
4. Build a **local, deterministic importer**, with source-specific tests, new-construction screening, exact permit identifiers, duplicate controls and a dry-run review report. Do not silently join or infer builders from addresses/owners.
5. Only when validated, publish the locally processed permit data and refresh on a cadence compatible with the government's download and reuse rules. No direct live API polling by our commercial dashboard.

## Provenance documents

- [Official Mecklenburg Open Mapping reuse policy](https://maps.mecklenburgcountync.gov/openmapping/index.html)
- [Official Mecklenburg open-data catalog](https://maps.mecklenburgcountync.gov/openmapping/data.html)
- [Charlotte snapshot provenance](../public/data/mecklenburg_snapshot_info.json)
- [North Carolina sales-detail rollout](SALES_DETAIL_ROLLOUT_CHUNK2.md)

**Status:** Withdrawn invalid pilot; commercially compliant downloaded-data replacement not yet implemented.
