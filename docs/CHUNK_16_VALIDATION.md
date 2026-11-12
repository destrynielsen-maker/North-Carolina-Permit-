# Chunk 16 — Review issue linkage and official portal verification gate

**Date:** November 12, 2026
**Status:** Two real verification issues created; dashboard linkage and four safety tests committed. Independent permit-portal review still outstanding.

## Confirmed current records

The current four-market production collector reports **3,174 screened permits** (Raleigh 781; New Hanover 813; Mecklenburg 701; Greensboro 879). These are screened candidates, not independently audited sales leads.

Wake and Brunswick remain in an eight-record-per-county research queue. A successful re-query of the same GIS layer is **not** independent validation in the county permit portal.

## Human verification tasks created

1. [Wake permit RBPR-183204-2026 — issue #1](https://github.com/destrynielsen-maker/North-Carolina-Permit-/issues/1)
   - GIS feature OBJECTID: **128361**.
   - GIS reported issue date: **2026-11-10**.
   - Work class: **New One- and Two-Family Dwelling**.
   - Required checks: actual permit issuer, current issue status, project site, principal builder or licensed GC, Raleigh overlap, stable official record URL, and review evidence.
2. [Brunswick project 701942 — issue #2](https://github.com/destrynielsen-maker/North-Carolina-Permit-/issues/2)
   - GIS feature OBJECTID: **284255**.
   - County PermitNumber field: **1000**, which is repeated for multiple sampled projects.
   - GIS reported issue date: **2026-11-10**.
   - Site: **6402 CASTLEBROOK WAY SW 28469**.
   - Required checks: project 701942 in official public portal; original issue date and status; actual licensed prime GC; distinguish the GIS `SubContractor` from the homebuilder.

Both issues were actually created; they remain research tasks, not approvals.

## Dashboard improvement

- New `public/data/verification_issues.json` is a read-only mapping from those two GIS OBJECTIDs to GitHub issues #1 and #2.
- For existing tasks the dashboard shows **Open review #1** or **Open review #2**. Other items retain the **Start verification** link that opens a prefilled GitHub *draft issue*.
- Only URLs matching the specific project GitHub issue path are accepted from the manifest.
- Closing a GitHub issue, submitting a draft, or entering text **does not** change `permits.json`, RSS, builder rankings, or `live_verified`.
- Four new tests in `tests/test_chunk16.py` check the record mapping, safe URLs, existing-vs-draft issue navigation, and strict non-promotion.

## Independent portal access findings

Wake County's [old permit-search service](https://permitsearch.wake.gov/) explicitly says records after July 1, 2018 should be viewed in the newer portal. Its [2026 user guidance](https://s3.us-west-1.amazonaws.com/wakegov.com.if-us-west-1/s3fs-public/documents/2026-01/logging_in_as_a_registered_user.pdf) directs users to https://wakecountync-energovpub.tylerhost.net/apps/selfservice . This is a JavaScript-driven portal; the web reader could not verify permit RBPR-183204-2026 in an independent record detail.

Brunswick's [official Permit Reports](https://brunswickcountync.gov/195/Permit-Reports) page publishes archived and live permit datasets, with warnings that live permits can be voided or revised. Its public [Permit Portal](https://bcpp.brunswickcountync.gov/) exposes only a JavaScript-required shell in the available reader, not an independently inspected record with a licensed prime GC.

**Independent official portal permit verification: 0 completed.** That limitation remains explicit. Do not assign Wake's issuing authority from planning polygons or Brunswick's builder from `SubContractor`.

## Next release gate

The two GitHub review tasks are actionable when a reviewer can navigate the county portal in an authenticated or public browser session, collect an authoritative record URL or official permit evidence, and record the original issue date, current status, actual issuer, site, GC identity and duplicate decision. Completing those checks may justify a source-specific expansion proposal, but publication requires explicit review and tested rules.

Until then **Wake and Brunswick stay disabled** and the 3,174-screened-permit baseline stays unchanged.
