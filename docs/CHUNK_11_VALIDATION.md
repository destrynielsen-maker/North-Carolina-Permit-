# Chunk 11 — permit authority and prime-builder attribution audit

**Date:** November 12, 2026
**Status:** Source-role audit and five synthetic tests committed; automated output and independent permit-level confirmation are separate checkpoints.

## Why the county GIS feed does not identify the actual issuer

Wake's `Building_Permits` GIS service has `ISSUE_DATE`, `PERMIT_NUMBER`, `CONTRACTOR`, `LINK`, district and coordinates but **no field documenting the government office that issued the permit**. The Wake Planning Jurisdictions layer provides *planning* areas, not issuer identities.

Government pages establish that multiple towns share the Wake County portal and/or inspection services but have distinct permitting roles:

- **Knightdale** explicitly says its Development Services staff reviews, invoices, and *issues* building permits filed in the Wake portal: https://www.knightdalenc.gov/development-services/permits-and-inspections/building-permits
- **Rolesville** says it *issues* building permits after Wake County approves the application; Wake County performs inspections: https://www.rolesvillenc.gov/planning/frequently-asked-questions-0
- **Wendell** processes building permit applications and zoning inspections while Wake County conducts building inspections; exact issuance authority for an individual record still requires checking: https://wildforwendell.com/town/departments-planning-building-permits-8694ea6a09
- **Zebulon** has a shared municipal/Wake process; verify exact agency of issuance for each permit rather than assigning it from a planning polygon: https://www.townofzebulon.org/o/planning

Wake public permit search: https://wakecountync-energovpub.tylerhost.net/apps/selfservice

**Rule:** Track `planning_area`, `permit_portal`, `issuing_authority`, and `inspection_authority` as *separate* concepts. Do not declare the issuer from the GIS polygon or from a Wake County URL. No records from this pilot are added to the sales dashboard.

## Brunswick — what we can and cannot identify

The [Brunswick Permit Reports](https://brunswickcountync.gov/195/Permit-Reports) site links residential-new-home and live permit data. The official GIS layer provides `PermitNumber`, `ProjectNumber`, `DateIssued`, `ParcelAddress`, `PermitType`, `PermitStatus`, `Jurisdiction` and **`SubContractor`**, but it does not expose a field explicitly defining the prime/general building contractor.

**Rule:** Never use `SubContractor` as the builder for rankings. We can screen permits without naming a builder, but cannot claim the prime-builder attribution requirement has been met until another authoritative record is verified.

Brunswick public permitting portal for manual search: https://bcpp.brunswickcountync.gov/ . Some project details may require an account.

## New read-only audit

`src/validate_chunk11.py` is limited to:
- 32 Wake new one- and two-family issued-permit GIS records and Wake's official planning polygon layer. It aggregates planning areas, permits requiring issuer review, boundary errors, and sanitized public-link **hostnames only**.
- 50 Brunswick active residential new-home records. It counts nonblank permit/project identifiers, nonblank `SubContractor` fields, dates in the past 365 days and future dates, but does **not** export contractor names or assign prime builders.
- Errors are recorded and the pilot returns `enabled_for_collection=false` for both counties.

`tests/test_chunk11.py` contains five synthetic tests for authority-role distinctions, unsafe URL stripping, ambiguous/missing areas, and safe GC non-attribution. The GitHub workflow runs the audit after existing permit collection and previous read-only checks, with expected output `public/data/chunk11_validation.json`.

## Release gates

**Wake:** Confirm the *actual* permit-issuing office for a sample in each major planning jurisdiction, verify Raleigh overlap beyond a small batch, and document a stable permit identity and dedupe rule.

**Brunswick:** Identify a trusted prime-builder field or an official public permit detail that records the actual GC, verify issue dates, and confirm standalone new-home classifications.

Both sources remain **disabled**. The existing dashboard last reported **3,174 screened candidates** across Raleigh, New Hanover County, Mecklenburg and Greensboro. The project-level `live_verified` flag stays false until independent agency record checks succeed.

## Next chunk

Use the Chunk 11 audit results to decide whether Wake should be a separate labeled service-area dataset rather than a county-issued dataset. For Brunswick, investigate the county portal's official permit detail records and verify builders on a small manual sample before publishing any builder rankings.

## Confirmed automated results — 2026-11-12T20:20:51.909060+00:00

The first post-Chunk-11 GitHub collection committed `public/data/chunk11_validation.json`. The Actions workflow reached the output-commit stage after the new five-test suite; the GitHub Pages deployment step was not independently inspected.

### Wake new-dwelling permits — 32 record pilot

| Planning area | Sampled permits |
|---|---:|
| KNIGHTDALE | 8 |
| ROLESVILLE | 7 |
| WENDELL | 9 |
| ZEBULON | 3 |
| no_matching_polygon | 5 |
| **Total** | **32** |

Evidence-group counts:
- Towns that explicitly say they issue their own building permits (Knightdale + Rolesville): **15** sampled locations. This is guidance, not record-level verification.
- Shared municipal/Wake arrangements requiring role review (Wendell + Zebulon): **12**.
- Unmatched/unknown planning polygons: **5**.
- Raleigh planning area matches: **0** in this sample only.
- Boundary errors: **0**.

All **32** sample records expose a `LINK` on hostname `energovcitizenaccess.tylertech.com`; this alone does **not** establish that the link opens the correct record or remains current. A separate official public search portal is https://wakecountync-energovpub.tylerhost.net/apps/selfservice .

**No issuer was automatically assigned to an individual permit**, and no Wake records entered the published leads.

### Brunswick recent active residential permits — 50 record pilot

- Nonblank permit IDs: **50 / 50**
- Nonblank project IDs: **50 / 50**
- Nonblank `SubContractor` fields: **50 / 50**
- Verified prime builders: **0**
- Recent issue dates within 365 days: **50**
- Future-dated records: **0**
- Jurisdiction breakdown: BRUNSWICK COUNTY 45, NAVASSA 4, NORTHWEST 1

An occupied `SubContractor` field is **not** evidence of the actual GC or homebuilder. The next task is verifying the prime contractor in the official portal by the captured project/permit identifier and checking whether a reliable public export/API field exists.

### Final decision

Neither Wake nor Brunswick has enough verified issuer/prime-builder evidence for full sales-lead promotion. Current dashboard total remains **3174** screened permits across the four existing jurisdictions. Leave `live_verified=false` and both candidate sources disabled.

Suggested Chunk 12: inspect Wake `LINK` deep links for reliable record-level verification and confirm official issuance roles by town; request or research Brunswick public permit detail builder fields rather than assuming the subcontractor is the prime builder.
