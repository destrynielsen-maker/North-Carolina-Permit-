# Chunk 18 — Explicit release-readiness gates for individually reviewed permits

**Date:** November 12, 2026
**Scope:** Existing Wake permit review #1 and Brunswick project review #2. Neither county is approved for live data collection.

## Verified workflow state at start

A post-Chunk-17 refresh commit (`d86afd3f32cb7000b6339ecfe5f576905f970a44`) generated `public/data/review_status.json` after the tests and review compiler executed: **two pending reviews, zero confirmed, zero promoted**. The four established markets retained **3,174** screened permit candidates. This confirms the data-refresh steps ran, but is not independent confirmation of GitHub Pages rendering in a user browser.

## New release-readiness audit

`src/audit_release_readiness.py` reads the manually curated decision ledger, compiled public review statuses, issue manifest, current county research queue and live source status. It **re-runs the original evidence validator**, rejects stale or mismatched compiled output, and fails closed when GIS IDs, source labels or issue references disagree.

For each existing review it reports specifically which requirements block publication:

- Reviewer has not confirmed an actual permitting-portal record
- Official record-specific evidence is missing
- Named reviewer/date not documented
- Permit-issuing authority unknown
- Licensed primary homebuilder / GC unknown
- Duplicate-project review unresolved
- Record identity, issue date, issued status and ground-up construction attestations incomplete
- **County/source not approved for live collection**
- **Separate manual release authorization missing**

The final two gates remain in force even if the evidence checklist is complete. A human-curated `confirmed` review is **not** equivalent to an approved lead or a jurisdiction-wide collector release.

## Source and data integrity

The audit refuses to produce an approved preview if:
- A reviewed record or matching GitHub issue is missing, duplicated or has a changed GIS OBJECTID
- The current review status disagrees with the manually committed ledger
- A review contains a generic permit portal URL falsely presented as record-specific evidence
- Wake or Brunswick unexpectedly appears with qualifying production permit counts
- Any compiled status claims existing lead promotion

The only output is `public/data/release_readiness.json`, with explicit blockers and non-promotion status. It does not update `permits.json`, builder rankings, RSS, source-configuration flags or GitHub issues. No code path approves new markets.

## Dashboard

The separate **County research queue — NOT published leads** displays review state and, when the audit is available, the top three plain-language release blockers. A link to the complete audit is included. The dashboard's existing permit totals and exports remain unaffected.

## Validation

`tests/test_chunk18.py` adds seven synthetic/offline tests covering pending cases, stale status, source/reference mismatch, unexpected county activation, a fully documented synthetic confirmation that still remains held, rejected generic official portal home URLs and no collector write path.

The automated workflow executes the release-readiness audit **after** `src/compile_reviews.py` and before committing refreshed data.

## Observed permit-specific evidence

- Wake permit `RBPR-183204-2026`, GIS record `128361`: still awaiting official portal record confirmation and the actual issuing authority, not simply planning-jurisdiction classification.
- Brunswick project `701942`, GIS record `284255`: primary GC/homebuilder not established in the county GIS `SubContractor` field, and official portal project detail awaits direct review.

No automatic system here can declare either source verified merely from another GIS query. These records remain held.

## Next checkpoint

Validate the workflow run and inspect `public/data/release_readiness.json` for the two pending reviews and their blockers. Verify nothing in the data totals changed. The next substantive release prerequisite is independent portal evidence recorded in the existing GitHub issues—not another GIS recheck.

## Confirmed automated outcome — 2026-11-12T21:29:36.179578+00:00

GitHub Actions reached the refreshed-data commit `5b9fdf4d455479462177b99826c620cd3e147263` after executing the test suite, collection, curated-review compilation and release audit. The generated `public/data/release_readiness.json` reports:

- Research records audited: **2**
- Pending/follow-up/rejected: **2**
- Evidence-complete for review: **0**
- Automatically promotable permits: **0**
- New live source approvals: **0**

Both Wake OBJECTID 128361 and Brunswick OBJECTID 284255 are pending, each with explicit missing-evidence and approval gates. Both have `included_in_sales_leads=false` and `release_status=held_research_only`.

The active collector last refreshed at `2026-11-12T21:29:07.373966+00:00` and still reports **3174** screened candidates across the original four areas. No Wake or Brunswick records were promoted.

Seven new offline tests in `tests/test_chunk18.py` ran in the successful data-refresh workflow; they cover rejection of stale statuses, inconsistent identities, unsafe portal home URLs, unexpected county enablement and a synthetic evidence-complete decision that remains blocked. Independent browser inspection of the latest GitHub Pages deployment and actual county permit-detail pages is still outstanding.

**Checkpoint decision:** Keep both counties research-only. No release approved.
