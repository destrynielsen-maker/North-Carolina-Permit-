# Chunk 14 — independent-verification gate and source-record consistency audit

**Date:** November 12, 2026

## Evidence

GitHub Actions generated `public/data/chunk14_validation.json` at **2026-11-12T20:50:20.366285+00:00**. It re-queried the exact ArcGIS OBJECTIDs in the bounded Chunk 13 research queue.

| Source | Attempted | Current GIS record match | Independent portal verifications |
|---|---:|---:|---:|
| Wake | 8 | 8 | 0 |
| Brunswick | 8 | 8 | 0 |
| **Total** | **16** | **16** | **0** |

For Wake, the tests compare permit number, issued date, work class, contractor as listed, and status. For Brunswick, they compare permit number, project number, issue date, permit type, address, reported jurisdiction, and Active status. All 16 checked records matched their *original official GIS layers*; a second read of the same source does not constitute independent permitting-portal verification.

The code includes 0 offline unit tests for matching and changed records, errors, invalid IDs, and no-promotion behavior. Tests were included in the workflow producing the refreshed output.

## Issuer and builder evidence

**Wake:** GIS object IDs uniquely identify features within the current GIS layer, but they do not identify which town/county issued the permits. The current Wake public portal remains a manually navigated search. The older GIS `LINK` URLs must not be rewritten to a new host without successful record-level navigation.

**Brunswick:** The project numbers help search the official portal; `SubContractor` is not an authenticated primary-builder field. The current public GIS layer does not support a legitimate assertion of general contractor identity. A reliable prime-builder mapping remains unestablished.

## Non-promotion checks

The 8 Wake and 8 Brunswick research records are isolated in `public/data/chunk13_review_queue.json`; their `included_in_sales_leads` flags are false. Chunk 14 also reports `new_leads_promoted=0` and `independently_verified=false`.

The active permit collector remains at **3174 screened candidates** across Raleigh, New Hanover, Mecklenburg and Greensboro, with no Wake or Brunswick records added.

## Next release gate — manual permit-portal verification

A Wake permit must be located by number in the county's current public portal; verify its issue date, status, project site, named issuer and licensed contractor, then record the actual URL if stable. For Brunswick, search by project number rather than common permit number, and confirm which entity is listed as licensed GC/homebuilder on the municipal permit detail.

If the public portal does not expose the necessary information without authentication, document that limitation rather than claiming verification or attempting a URL substitution.

**Decision: Keep both sources disabled.** No county should be promoted solely because 16 same-source record checks passed.
