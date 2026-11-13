# Greensboro and New Hanover sales contact checkpoint — 2026-11-13

## Verified source boundaries

- Greensboro's official Building Permits GIS layer exposes `Contractor`, `BuildingSqFt`, `NumStories`, and `PermitNum`. It does **not** expose contractor phone or email in the inspected layer. Schema: https://gis.greensboro-nc.gov/arcgis/rest/services/EngineeringInspections/BuildingPermits_MS/MapServer/6?f=pjson
- Greensboro's individual permit pages use the supported `frmBuildingPermitView.aspx?bldgPermitNumber=<numeric>` pattern and can display contractor office/mobile numbers and email slots. These are **permit-specific pages**, not a guarantee that each field is populated. Example: https://bisched.greensboro-nc.gov/frmBuildingPermitView.aspx?bldgPermitNumber=202610242
- New Hanover's official Building Permits feature layer exposes `GENERAL_CONTRACTOR` and a separately labeled `PROJECT_CONTACT`; the inspected layer does not include a clear general-contractor phone/email field. Schema: https://gisport.nhcgov.com/server/rest/services/Thematic/BuildingPermits/FeatureServer/0?f=pjson
- New Hanover COAST assistance is a public permit-help channel (910-798-7308, option 1, and coast@nhcgov.com). **These are county help contacts, not builder contacts.** County FAQ: https://hhs.nhcgov.com/m/faq

## Implemented

- Collector maps Greensboro `BuildingSqFt` and `NumStories` into existing project-detail fields.
- Sales CSV includes stories.
- Source-field coverage diagnostics now count `stories_available` independently of `square_feet_available`.
- Added tests for valid/invalid values and coverage counts.

## Safety and remaining checks

Do not infer contractor contacts from owner, project contact, tax record, or a same-name company. A future contact enrichment requires a direct official permit-page match on permit number and contractor identity, provenance, permitted reuse, bounded queries, and tests for ambiguous/missing data. No bulk secondary contact scraping or automatic promotion was added.

After the next successful collection, compare `public/data/sales_field_coverage.json` values for Greensboro `square_feet_available` and `stories_available` to the prior baseline (both unavailable in the report before this change). Check CI and GitHub Pages independently; a source-code commit is not proof of successful site deployment.
