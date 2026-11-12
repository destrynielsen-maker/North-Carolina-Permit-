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

## Chunk 7 investigation: additional sources (not live)

| Area | Official evidence | Status | Hold reason |
|---|---|---|---|
| Wake County | [Building Permits data catalog](https://catalog.data.gov/dataset/building-permits-ff506) and [GIS service](https://maps.wake.gov/arcgis/rest/services/Inspections/Building_Permits/MapServer/0) | Metadata probe staged | Verify issued-date field, local issuing jurisdiction, City of Raleigh overlap; service may be inaccessible from automation |
| Brunswick County | [Official permit report directory](https://brunswickcountync.gov/195/Permit-Reports) and [Permit Locations GIS](https://services1.arcgis.com/W6gamXPYQeLXrdAd/arcgis/rest/services/Permit_Locations/FeatureServer/0) | Metadata probe staged | Published `DateIssued` is **text**, not a proper GIS date. Need format and status validation; `SubContractor` is **not** a general contractor field |
| Cabarrus County | [Accela permit search](https://aca-prod.accela.com/CABARRUS/Cap/CapHome.aspx?TabName=PERMITS&module=Permits) and [GIS Plan Reviews layer](https://location.cabarruscounty.us/arcgisservices/rest/services/Current_Accela_Permits/Plan_Reviews/MapServer/0) | Metadata probe staged | Accessible GIS layer includes `B1_FILE_DD` and `B1_APPL_STATUS_DATE`, not an authoritative building-permit issue date |
| Johnston County | [County-issued permit search by work type/date](https://www.johnstonnc.gov/insp/Worktypelookup.cfm) | Manual-source candidate only | Official web form reports work type, date, contractor and valuation, but no validated API/automated feed yet |

Read-only staging probes are implemented in `src/probe_sources.py` and run without enabling any of these counties. They write `public/data/source_probes.json` once the revised workflow completes.

## Chunk 10 official release-gate sources

- **Wake planning jurisdiction polygon layer:** https://maps.wake.gov/arcgis/rest/services/Jurisdictions/Jurisdictions/MapServer/1 . Government maintained dataset explicitly includes municipal corporate limits and extra-territorial planning jurisdiction. Its `JURISDICTION` attribute distinguishes `RALEIGH` from other named city planning areas. It is not by itself proof of which office issued the building permit.
- **Raleigh ETJ explanation:** https://raleighnc.gov/planning/services/annexations/extraterritorial-jurisdiction-etj . City confirms Raleigh planning and building regulations extend outside city limits in the ETJ.
- **Brunswick county's filtered residential-new-home archive:** https://brunswickcountync.gov/195/Permit-Reports . Official site links to `Monthly Permit Locations` filtered to `ProjectType=Residential`, `PermitStatus=Active`, `PermitType` values `NEW HOME`, `RESIDENTIAL MODULAR` and `TOWNHOME`. The filter is a candidate-screening aid, not confirmation of individual permit issuance.
- **Brunswick development pipeline context:** https://brunswickcountync.gov/1008/Development-Dashboards-Maps . Official residential and commercial development dashboards are updated monthly; municipal coverage is explicitly incomplete.

`src/validate_chunk10.py` runs **read-only** bounded Wake polygon checks and Brunswick new-home record sampling. **Neither feed is enabled automatically**, regardless of pilot results. Null/ambiguous boundary results, future dates, missing GC information and records that cannot be independently checked remain blocked.

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
