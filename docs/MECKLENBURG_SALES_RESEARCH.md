# Sales-intelligence expansion — Mecklenburg contractor research

**Date:** November 12, 2026

## Goal

Move the North Carolina sales dashboard closer to permit-specific builder outreach, particularly in Mecklenburg/Charlotte where the selected GIS permit feed does not provide a verified building contractor name or direct business phone/email.

Do **not** populate an owner, applicant, project contact, subcontractor, developer or parcel tax record as the building general contractor simply because that field is present.

## Official government source research

1. [Mecklenburg current building-permit GIS layer](https://meckgis.mecklenburgcountync.gov/server/rest/services/BuildingPermits/FeatureServer/0): publishes `projname`, `projnum`, `subdiv`, `parcelnum`, `taxjuris`, `projphase`, `totalsqft`, `heatsqft`, `unheatsqft`, `numunits`, and more. It includes `ownname` (property owner), but **no explicit contractor/GC field** in the selected layer.
2. [Mecklenburg Permit and Plan Review Status Portal](https://gis.mecklenburgcountync.gov/meck-accela/): official permit search, accepting permit number, address or parcel number. **This is an official search page, not a tested individual permit-specific deep link.**
3. [Mecklenburg Building Permits Issued Daily](https://code.mecknc.gov/node/1041): county instructions explain contractor filtering and CSV/XLSX export of a specific date range. The search/report requires interactive use; the project has not validated a reliable public record-level export/API that joins its contractor data to the GIS record. **No automated builder attribution is claimed.**
4. [North Carolina Licensing Board for General Contractors lookup](https://portal.nclbgc.org/Public/Search): supports search by license number and company name. It is a **verification/research step**, not proof of which contractor worked on an individual permitted building.
5. [New Hanover official building-permits layer](https://gisport.nhcgov.com/server/rest/services/Thematic/BuildingPermits/FeatureServer/0): publishes general contractor and project contact separately, along with area data. No explicit business phone/email fields in the selected source feed.
6. [Greensboro official Building Permit Query](https://bisched.greensboro-nc.gov/frmBuildingPermitView.aspx?bldgPermitNumber=202518414): individual permit page pattern remains the official primary external deep link, while the project's sales-friendly permit detail is the main user-facing page.

## Completed changes

- **Permit detail page:** Mecklenburg project details now include sourced subdivision, parcel, tax jurisdiction, project phase and total/heated/unheated square footage. The existing builder section remains blank/unknown when not included in the GIS source.
- **Charlotte research actions:** county permit search and county issued-permit contractor-report links are available in the project page; a Copy Permit Number button makes manual lookup quicker.
- **NC contractor license verification:** a separate official license-search link is available when a builder name is present. The link opens a search rather than claiming that a matching license has been found.
- **Main sales dashboard:** a Builder listed / Builder missing — research filter and a direct Mecklenburg county-permit-search link in empty-builder rows.
- **CSV:** includes additional project and property data from the official GIS source.
- **Coverage reporting:** aggregate counts include parcel/subdivision/construction square-footage availability by jurisdiction. No new personal contact data are inferred.

## Safety and quality

- Property owner (`ownname`) is **not** promoted to builder.
- No contractor identity or contact is guessed or imported from unrelated records.
- Source data remain clearly labeled as screened, not individually audited.
- No new counties enabled, no automated source joins, no broad write to the main permit dataset from secondary websites.
- No bogus permit-specific portal URL constructed. The county portal link is explicitly a manual search.
- Changes are covered by the three new tests in `tests/test_sales_details.py`, expanding the sales-detail suite from 10 to 13 tests.
- The previously verified CI run passed 113 tests. The **new** suite and contact coverage require a subsequent successful refresh to confirm.

## Next checkpoint

Check `public/data/ci_test_status.json` for a fresh run with 116 tests passing, then inspect `public/data/sales_field_coverage.json` to determine how often Mecklenburg's new square-footage and subdivision/parcel fields are populated. The GitHub Pages deployment still needs its own live-browser check.

For reliable Charlotte builder attribution, evaluate the county's official contractor-filterable issued-permits export in a controlled discovery pilot. Do not join automatically by address/project name alone, because one site may have many permits and contractors.
