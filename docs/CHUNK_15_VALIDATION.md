# Chunk 15 — Manual permit-portal verification workflow

**Date:** November 12, 2026
**Scope:** Wake County and Brunswick County; both remain research-only. No new sales leads are promoted.

## What was established

- **Wake:** Its current public EnerGov portal is a client-side application. Opening the portal's home page or rewriting an older `#/permit/...` link onto the new hostname **does not** verify that the intended permit opens. The 32 previously audited GIS links all used the old `energovcitizenaccess.tylertech.com` host. No current-portal deep link has been independently verified. Current portal: https://wakecountync-energovpub.tylerhost.net/apps/selfservice
- **Brunswick:** The public permit portal is https://bcpp.brunswickcountync.gov/ and public permit search/report links are available from https://brunswickcountync.gov/808/Permits-Development . The published 20-field GIS layer has `SubContractor` but not a confirmed licensed prime-general-contractor field. A nonblank trade-contractor value is **not** proof of the homebuilder.

## Implemented workflow

The North Carolina dashboard's **County research queue — NOT published leads** now has **Start verification** on each of the up to eight Wake and eight Brunswick research rows.

This button/link:
1. Opens a **draft GitHub issue** in the owner's North Carolina repository with the county, permit/project reference, exact GIS feature OBJECTID, issue date, and official lookup links prefilled.
2. Provides a reviewer checklist: locate the actual permit in the public portal; verify current status, issuing jurisdiction, work type, address, primary GC role and potential duplicate projects; preserve the official record URL and evidence date.
3. Does **not** submit the issue automatically, mark a record verified, change a permit's status, infer a contractor, enable a source, or add leads to the dataset.

The user must submit the draft issue and conduct actual official portal review. The existing queue and `public/data/chunk14_validation.json` remain independent from the production `permits.json`, RSS and builder rankings.

## Quality controls

- Exact GIS links query `OBJECTID` rather than a Brunswick `PermitNumber` that may repeat.
- No unsafe HTML is added to the dashboard by reviewer-provided text; issue URL parameters are encoded.
- New `tests/test_chunk15.py` enforces manual-review semantics, required evidence fields, source identifiers and zero lead promotion.
- GitHub Pages source code was updated directly. The commit and synthetic tests are distinct from successfully confirming the latest Pages deployment.

## Verification outcome and next release gate

**Official portal-level review: still 0 independently verified permits.** The review workflow is a workbench for collecting evidence, not evidence in itself. Existing four-market screened-candidate count remains **3,174** as of the latest confirmed data snapshot.

For Wake, require a documented portal-specific permit record and actual issuing authority before deciding how to merge with Raleigh. For Brunswick, require a primary GC field or authoritative permit document showing the builder, not `SubContractor`, before contractor attribution.

If official portal review requires an authenticated session or is not navigable without JavaScript, record that blocker. Do not bypass authentication or pretend the GIS recheck is a portal verification.

## Next checkpoint

Verify GitHub Actions runs the new safety tests successfully and that the dashboard code and review queue remain published. Then use actual human permit portal reviews to close the evidence gaps rather than creating another automated GIS consistency pass.
