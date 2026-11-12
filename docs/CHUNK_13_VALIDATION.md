# Chunk 13 — Official-record lookup workbench and portal migration gate

**Date:** November 12, 2026
**State:** Read-only workbench committed; direct-record confirmation across new portals remains unresolved.

## Primary findings

**Wake:** The official [2026 permit-portal instructions](https://s3.us-west-1.amazonaws.com/wakegov.com.if-us-west-1/s3fs-public/documents/2026-01/how_to_register_guide.pdf) direct users to `https://wakecountync-energovpub.tylerhost.net/apps/selfservice`. The existing GIS `LINK` field pointed to the old `energovcitizenaccess.tylertech.com` domain in 32/32 sampled issued new-dwelling records. The path fragment followed a record-specific `#/permit/...` route, but this is an *old client-side fragment*. A successful HTTP load of the site's JavaScript shell does not confirm that it loaded the correct permit. **No old-to-new direct-link mapping has been verified.**

**Brunswick:** The official [Permits & Development](https://brunswickcountync.gov/808/Permits-Development) page links its [public permit search](https://apps.brunsco.net/bcms/dashboard/) and the [permit portal](https://bcpp.brunswickcountync.gov/). The latter requires JavaScript for the public web parser; the county [project guide](https://www.brunswickcountync.gov/922/Start-a-Project) explains that an account can be required for project tracking and documents. The official [Permit Reports](https://brunswickcountync.gov/195/Permit-Reports) site allows downloading active/archived permit data, but the accessible 20-field GIS view still exposes `SubContractor` with no verified prime-builder field. Secondary services may claim contractor coverage but are not substitutes for an authoritative field definition.

## What is now built

- `src/review_chunk13.py` creates a bounded **research-only** manual-review queue of up to eight Wake new-dwelling and eight Brunswick new-home records.
- Each review item has a permit number, issue date, an exact government ArcGIS query with the permit number, and the official current portal-search URL. Brunswick entries also include project number and public source address; no `SubContractor` is exposed as a builder.
- Wake entries retain only the safe legacy link category, not a guessed rewritten record URL. Contractor names, where exposed, are clearly labeled `contractor_as_listed_unverified`; issuing agency remains unknown.
- Filters exclude invalid permit IDs, future records, old records, and missing issue dates. All entries explicitly set `included_in_sales_leads=false`.
- `public/index.html` has a separate **County research queue — NOT published leads** section and links to the exact record query and official portal search, distinct from the active lead listings, leaderboards, RSS and sales exports.
- `tests/test_chunk13.py` adds five offline tests for source/field allowlists, ID validation, date guards, correct lookup URLs and subcontractor exclusion.
- GitHub Actions runs the script and produces `public/data/chunk13_review_queue.json` upon a successful refresh.

## Verification classification

**Exact GIS lookup** is a convenient official record query but relies on the *same source* that produced the candidate. It is not an independently verified official permit-detail page. **Official portal search** requires the user to enter the permit number; it is not a direct deep link. An HTTP request does not execute the JavaScript fragment route, and cannot prove a permit is displayed.

The review queue is **not an additional live market**. Wake issuer geography and Raleigh overlap, and Brunswick prime-builder attribution, remain unresolved. No record in this queue should be included in the current **3,174** screened permit candidates or claimed as a verified sales lead.

## Release gates

Wake:
1. Open the original specific permit link and independently find the same permit number in the current official portal (within normal portal access, not by guessing a route).
2. Confirm permit status, issue date, address, issuing authority and actual contractor on a bounded sample.
3. Document reliable migration to individual record URLs only if manually reproducible; otherwise retain the official search page and permit number.
4. Reconcile Raleigh overlap with issuing-authority evidence.

Brunswick:
1. Open the county public permit search by permit/project number and confirm date, status and work classification.
2. Identify an official prime GC or builder field or record with clear semantics; do **not** use the `SubContractor` GIS field.
3. Build and test a documented source-specific contractor mapping, or keep the builder blank.
4. Complete a sample of independently verified new-building permits before any feed promotion.

**At checkpoint:** live workflow output must be checked separately; do not infer data refresh success from a code commit.
