# Chunk 10 — Wake planning-jurisdiction overlay and Brunswick new-home filter

**Date:** November 12, 2026
**Status:** Read-only pilot code and 7 synthetic tests committed. Live result publication and separate official permit-detail verification are independent release gates.

## Starting point

The existing live dashboard includes four markets and 3,174 screened candidate permits: Raleigh 781, New Hanover County 813, Mecklenburg County / Charlotte 701, and Greensboro 879. These are not individually certified sales leads.

## Wake County — official planning-jurisdiction layer

The [Wake County Planning Jurisdictions MapServer layer](https://maps.wake.gov/arcgis/rest/services/Jurisdictions/Jurisdictions/MapServer/1) is an official maintained polygon layer; source [data catalog](https://catalog.data.gov/dataset/planning-jurisdictions). It reports `JURISDICTION` labels including RALEIGH, CARY, APEX, WAKE FOREST, GARNER, etc. It represents municipal **planning jurisdiction**, which includes ETJ, not necessarily the permit-issuing office.

The [City of Raleigh ETJ explanation](https://raleighnc.gov/planning/services/annexations/extraterritorial-jurisdiction-etj) confirms its planning/building rules extend outside city limits, reinforcing why using only corporate limits would be unsafe.

**Read-only pilot** in `src/validate_chunk10.py`:
- Query up to 20 recent Wake records explicitly classified as `New One- and Two-Family Dwelling`, with current `Issued` status.
- Request permit geometries projected to NC State Plane coordinate reference 2264.
- Query the official planning-jurisdiction polygons with a point intersection per record.
- Report only aggregate counts: Raleigh planning area, other named jurisdictions, missing points, unmatched polygons, ambiguities and errors.
- Never treat missing polygon as proof a permit belongs to the county, and never add any of these records to the lead dashboard.

**Gate:** even a matched polygon is planning authority, not independently confirmed permit issuer. The City/Raleigh feed overlaps must be separately audited before enabling Wake.

## Brunswick County — official residential new-home filter

The [Brunswick County Permit Reports page](https://brunswickcountync.gov/195/Permit-Reports) links an officially maintained dataset with a pre-filtered residential new-home view. It identifies `ProjectType=Residential`, `PermitStatus=Active` and `PermitType` in `NEW HOME`, `RESIDENTIAL MODULAR` and `TOWNHOME` (a screened candidate set, not audited issuance).

**Read-only pilot** in `src/validate_chunk10.py`:
- Request at most 100 newest matching records, ordered by the source text `DateIssued` field.
- Count parseable dates in the last 365 days separately from unparseable, old or **future-dated** records (previous test found 2099).
- Report permit-type and jurisdiction counts only; no raw permit rows and **no inferred GC** from `SubContractor`.
- Do not permit any results into the live dashboard or RSS.

The permit-locations layer lacks a verified prime/general-contractor field, and `Active` is not independent proof a new home was actually issued. Continue source search before promotion.

## Automated validation and files

- New script: `src/validate_chunk10.py`.
- New offline tests: `tests/test_chunk10.py` (7 tests covering polygon classification, unknown areas, ambiguity, errors, filter safety and future dates).
- GitHub Actions workflow: `.github/workflows/permits.yml`, runs the new script after existing scheduled collection and probes.
- Expected output after successful automation: `public/data/chunk10_validation.json`.
- Existing `public/data/chunk8_validation.json` and dashboard stay unchanged in scope.

**No claim of source promotion or verification is justified by these scripts alone.** If the new report has not been generated, review the Actions run and fix the failure before interpreting any sample counts.

## Next checkpoint

Check the published report, assess whether Wake jurisdiction labels are sufficiently useful for an anti-overlap rule, inspect Brunswick's newest filtered permit sample, and perform independent agency-level record checks before enabling any new jurisdiction.

## Confirmed live result — 2026-11-12T20:12:37.401186+00:00

GitHub Actions generated `public/data/chunk10_validation.json`. The 7 new unit tests and existing test suite were passed by the workflow before creating this report; the GitHub Pages step itself was not separately inspected.

### Wake planning boundaries — 20 issued new-dwelling records

- KNIGHTDALE: **1**
- ROLESVILLE: **7**
- WENDELL: **6**
- ZEBULON: **3**
- No polygon match: **3**
- Matched Raleigh planning jurisdiction: **0**
- Boundary API query errors: **0**

Seventeen sampled points matched named non-Raleigh **planning areas**, but this does not establish their building-permit **issuer**. Three points had no polygon match and remain unknown. These 20 records are not a statistically comprehensive test of the Wake GIS layer's scope. Raleigh ETJ is included in the planning layer; future full-source overlap validation is still required.

### Brunswick new residential construction filter — 100 records

- 97 records: `NEW HOME`
- 3 records: `RESIDENTIAL MODULAR`
- All 100 are filtered `Active` residential permit records
- All 100 were parseable and dated **2026-10-23 to 2026-11-10**; zero future, stale or unparseable dates in this sample
- Jurisdictions: BRUNSWICK COUNTY **83**, NAVASSA **6**, NORTHWEST **1**, SHALLOTTE **6**, ST. JAMES **3**, VARNAMTOWN **1**

The refined source is materially more relevant to new construction than the general all-permit sample. It still lacks a verified general contractor field and independent permit-record checks. Do not promote these candidate records into the sales dashboard on this evidence alone.

### Dashboard and release gates

The active collector totals after the pilot remain **3174** screened permits across Raleigh, New Hanover, Mecklenburg and Greensboro. Both pilot sources still report `enabled_for_collection=false`; no pilot data entered the lead dataset.

Recommended Chunk 11 scope: crosscheck larger Wake samples against official permit-issuing agencies and boundaries; verify how Brunswick identifies prime building contractors; cross-verify a sample of new-home permits in official county permit detail; enable a jurisdiction only after a documented review gate.
