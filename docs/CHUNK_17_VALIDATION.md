# Chunk 17 — Controlled review decisions and evidence gate

**Date:** November 12, 2026  
**Release status:** Research-only review system. No new permit feed or sales leads are activated.

## Why this system exists

The previous Wake and Brunswick batches passed exact GIS consistency checks, but those checks re-read the same source. Neither the actual Wake issuing authority nor Brunswick's licensed prime builder has been confirmed in its separate public permit portal.

A GitHub issue marked complete is also not proof of permit issuance. This project must prevent a checkbox, closed issue, or URL from silently approving a contractor or adding permits to the sales dashboard.

## New source of truth

`reviews/decisions.json` contains one manually curated record for each issue-backed sample:

| Source | GIS OBJECTID | Issue | Decision |
|---|---:|---|---|
| Wake | 128361 | [#1](https://github.com/destrynielsen-maker/North-Carolina-Permit-/issues/1) | pending |
| Brunswick | 284255 | [#2](https://github.com/destrynielsen-maker/North-Carolina-Permit-/issues/2) | pending |

The allowed human review decisions are `pending`, `needs_follow_up`, `rejected`, and `confirmed`. A confirmed decision means a reviewer has documented supporting evidence and attested it matches the individual government permit; it does **not** mean the system has independently inspected a JavaScript-based permit portal.

A reviewer must manually edit and commit the decision file. **GitHub issue state and comments do not automatically change it.**

## Confirmation requirements

A `confirmed` entry must provide:

- Human reviewer and review date, not a future date
- An official **record-specific** evidence URL from the proper county domain, not a generic portal homepage/search, GitHub issue, or the same ArcGIS service
- The official record/permit reference
- The actual issuing authority and identified licensed primary GC/homebuilder
- Explicit human attestations for matching permit identity, issue date, issued status, ground-up work classification, and that the county portal record was inspected
- A resolved **no-match** duplicate review across the relevant sources

If any required evidence is missing, `src/compile_reviews.py` fails with an error. Rejected and follow-up decisions require a reason. The compiler also checks exact GIS IDs, issue numbers, allowed states, types, and duplicate decision entries.

## Publication protection

The workflow runs `python src/compile_reviews.py` after regenerating the current research queue. Its only output is `public/data/review_status.json`: a concise public status per reviewed GIS record.

Regardless of a decision—including `confirmed`—the compiler publishes:

- `release_status: held_research_only`
- `included_in_sales_leads: false`
- `auto_promoted_leads: 0`
- `new_sources_enabled: 0`

It never writes to `public/data/permits.json`, builder rankings, or RSS feeds. Actual sales-feed promotion would require a separate, explicitly authorized and independently reviewed release step that is not implemented here.

## Dashboard

The research queue displays the curated status alongside the GIS consistency result. The current two issues should show **Pending — not verified**. Missing/unlisted records show **Not reviewed — held**.

Other possible messages are **Follow-up required — held**, **Rejected — held**, and **Evidence documented — held**. The last is deliberately *not* a sales approval.

## Test and verification checklist

- [ ] GitHub Actions runs the unit suite and review compiler
- [ ] `public/data/review_status.json` exists and reports 2 pending, 0 confirmed, 0 promoted
- [ ] Existing research queue stays eight Wake and eight Brunswick records; neither source enabled
- [ ] Production screened candidate count remains 3,174
- [ ] Actual independent portal verification remains 0 until a human review provides evidence

The new `tests/test_chunk17.py` covers pending states, missing evidence, official URLs, issue/object mismatch, duplicate decisions, synthetic human evidence, and no automatic lead promotion.

## Next checkpoint

Use the [Wake permit review](https://github.com/destrynielsen-maker/North-Carolina-Permit-/issues/1) and [Brunswick project review](https://github.com/destrynielsen-maker/North-Carolina-Permit-/issues/2) to collect real official evidence. Once available, manually update the curated review file and check whether a separate, jurisdiction-specific release process is justified. Do not turn on a whole county from one reviewed record.
