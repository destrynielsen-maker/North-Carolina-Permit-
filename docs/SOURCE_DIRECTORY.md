# North Carolina source directory — November 12, 2026

Field schema verification does not prove live query success or record accuracy.

| Area | Official source | Collector | Caveat |
|---|---|---|---|
| Raleigh | [Issued past 180 days](https://services.arcgis.com/v400IkDOw1ad7Yad/arcgis/rest/services/Building_Permits_Issued_Past_180_Days/FeatureServer/0) | Mapped | 180-day feed; overlaps Wake |
| New Hanover County | [Issued building permits](https://gisport.nhcgov.com/server/rest/services/Thematic/BuildingPermits/FeatureServer/0) | Mapped | GIS monthly refresh; work class screening required |
| Mecklenburg / Charlotte | [Building permits](https://meckgis.mecklenburgcountync.gov/server/rest/services/BuildingPermits/FeatureServer/0) | Mapped | Contractor not in chosen layer |
| Greensboro | [Building Permits Dashboard GIS layer](https://gis.greensboro-nc.gov/arcgis/rest/services/EngineeringInspections/BuildingPermits_MS/MapServer/6) | Collector enabled; new record verification pending | `IssuedDate`, `ApplicationType`, `OccupancyDesc`, `Contractor`, `TotalCost`; conservative screening, no source-record QA yet |
| Wake County | [Open data](https://data-wake.opendata.arcgis.com/datasets/Wake::building-permits) | Paused | Schema/overlap testing |
| Durham | [Monthly construction activity reports](https://www.durhamnc.gov/308/Monthly-Construction-Activity-Reports) | Paused | Current GIS layer has no issue-date field |

## Next integrations
Guilford County beyond Greensboro, Brunswick, Cabarrus, Johnston, Buncombe/Asheville.

## Qualification policy
- Require actual issue date; never substitute application date.
- Remove pending/void/withdrawn/expired, renovation, additions and trade permits.
- Treat published records as screened candidates until manually checked.
- Keep field-level source citations and track errors rather than silently claiming full coverage.

## Chunk 4 source-quality checks

- Current published screening baseline (November 12, 2026): Raleigh 781 of 3,005; New Hanover County 813 of 21,445; Mecklenburg 7 of 1,729. These are **candidate** records, not verified projects. Greensboro numbers are pending its first successful query.
- Mecklenburg's issue-date, work-type, permit-type and construction-type field **names exist** in its official ArcGIS layer. The seven-record result alone is insufficient to conclude low development activity or broken code. Diagnostics now record top status, work, permit-type and rejection reason counts for follow-up.
- `public/data/diagnostics.json` will contain aggregated status/type/rejection counts after the next successful collector run; it does not publish rejected permit addresses or other record-level rejection data.
- Raleigh and Wake City/County permit overlap remains a **blocker for adding Wake**. Wake and Durham remain paused.
- Independent permit-by-permit verification was not possible from the available live query interface in this session. Do not present the counts as audited leads.
