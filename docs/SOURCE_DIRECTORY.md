# North Carolina source directory — November 12, 2026

Field schema verification does not prove live query success or record accuracy.

| Area | Official source | Collector | Caveat |
|---|---|---|---|
| Raleigh | [Issued past 180 days](https://services.arcgis.com/v400IkDOw1ad7Yad/arcgis/rest/services/Building_Permits_Issued_Past_180_Days/FeatureServer/0) | Mapped | 180-day feed; overlaps Wake |
| New Hanover County | [Issued building permits](https://gisport.nhcgov.com/server/rest/services/Thematic/BuildingPermits/FeatureServer/0) | Mapped | GIS monthly refresh; work class screening required |
| Mecklenburg / Charlotte | [Building permits](https://meckgis.mecklenburgcountync.gov/server/rest/services/BuildingPermits/FeatureServer/0) | Mapped | Contractor not in chosen layer |
| Wake County | [Open data](https://data-wake.opendata.arcgis.com/datasets/Wake::building-permits) | Paused | Schema/overlap testing |
| Durham | [Monthly construction activity reports](https://www.durhamnc.gov/308/Monthly-Construction-Activity-Reports) | Paused | Current GIS layer has no issue-date field |

## Next integrations
Guilford/Greensboro, Brunswick, Cabarrus, Johnston, Buncombe/Asheville.

## Qualification policy
- Require actual issue date; never substitute application date.
- Remove pending/void/withdrawn/expired, renovation, additions and trade permits.
- Treat published records as screened candidates until manually checked.
- Keep field-level source citations and track errors rather than silently claiming full coverage.
