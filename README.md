# North Carolina Construction Intelligence

Public permit-intelligence dashboard for screened **newly issued** single-family, multifamily, and commercial construction opportunities.

## Current market coverage

| Jurisdiction | Status | Note |
|---|---|---|
| Raleigh | Collector configured | Issued-past-180-days GIS service |
| New Hanover County | Collector configured | Published issue-date/work-class schema; GIS monthly refresh |
| Mecklenburg County / Charlotte | Collector configured | Contractor not exposed in selected GIS layer |
| Greensboro | Collecting | 879 screened candidates from the November 12 refresh |
| Wake County | Paused | Need to validate schema and Raleigh overlap |
| Durham | Paused | Existing active permit layer lacks issue dates |

**Records are screened candidates**, not individually verified permits or statewide coverage. The scheduled collector has produced screened results for Raleigh, New Hanover County, Mecklenburg and Greensboro. Record-level issuance and classification verification remains pending.

## Local development

```bash
python -m unittest discover -s tests -v
python src/collect.py
python -m http.server --directory public 8000
```

## GitHub Actions / Pages

The [permit refresh workflow](.github/workflows/permits.yml) runs on pushes to `main`, manual dispatch and every six hours at minute 17 UTC. It checks the offline test suite, queries official collection services, probes disabled source metadata without adding permit records, commits the refreshed data and deploys the `public/` folder.

**Enable Pages:** Repository → **Settings** → **Pages** → **Build and deployment** → **Source: GitHub Actions**. After enabling, use the **Actions** tab to run `North Carolina permit refresh and deploy` if the initial push didn't deploy.

Dashboard URL (after successful deployment): https://destrynielsen-maker.github.io/North-Carolina-Permit-/

Every successful refresh writes `public/data/diagnostics.json`, aggregated work types, permit types, statuses, and rejection reasons to diagnose undercounting. These aggregate diagnostics contain no rejected permit addresses.

Chunk 6 also adds a **non-destructive** `public/data/overlap_audit.json` for exact cross-source permit-number collisions (no automatic merges), and safely consolidates contractor spelling, punctuation and license-label variants in builder rollups while retaining original aliases. Wake County remains disabled until its issuer and duplicate coverage are confirmed.

Chunk 7 generates **[time-window builder rankings](public/data/builder_rankings.json)** (ranked by screened issued permits in the last 90/30 days, with aliases, category mix and average valuation), a **[24-permit manual QA queue](public/data/qa_samples.json)** with source-level query links, and **[read-only source schema probes](public/data/source_probes.json)** for Wake, Brunswick and Cabarrus once the next workflow run completes. The QA samples are **not independently verified**. The dashboard includes a top-20 builder leaderboard.

See [source directory](docs/SOURCE_DIRECTORY.md) and [Chunk 7 checkpoint](docs/CHUNK_7_VALIDATION.md) for government data URLs, verification evidence, and coverage caveats.

## Official permit-detail links

For Greensboro, the permit number in the dashboard now opens the city's public **Building Permit Query** page at `https://bisched.greensboro-nc.gov/frmBuildingPermitView.aspx?bldgPermitNumber=<PermitNum>`. This pattern is documented by publicly accessible city permit pages; individual new permit pages still need to be spot-checked in a browser. The original ArcGIS layer remains as `source_url` for provenance. Other jurisdictions continue linking to their published source unless a supported direct-permit URL format is verified.

RSS items, CSV exports and the QA queue also use or expose the Greensboro direct-link field after a successful data refresh.

## Chunk 10 — staged jurisdiction and new-home research

The new `src/validate_chunk10.py` reads a bounded sample of Wake issued new-dwelling permits and queries the official Wake planning-jurisdiction polygons for Raleigh ETJ overlap evidence. Separately, it samples the county's own Brunswick Residential New Home permit categories while rejecting future and unparseable dates. Results are aggregate-only and should appear in `public/data/chunk10_validation.json` after a successful workflow run.

**No Wake or Brunswick records are promoted automatically.** Planning jurisdiction is not proof of building-permit issuer, and Brunswick's source does not expose a verified prime contractor. Details and release gates: [Chunk 10 checkpoint](docs/CHUNK_10_VALIDATION.md).

## Chunk 12 — Wake record links and Brunswick builder attribution

Wake's GIS permit links reference an older EnerGov host, while current county instructions use `https://wakecountync-energovpub.tylerhost.net/apps/selfservice`. The project **does not** rewrite old permit-specific URLs without independently verifying the corresponding record. The dashboard now links to the current official public search.

Brunswick's mapped source exposes `SubContractor`, not a confirmed prime/general contractor. Do not add those names to builder rankings. The dashboard now links to the official Brunswick portal and new-home permit reports for manual research.

The [Chunk 12 validation report](docs/CHUNK_12_VALIDATION.md) describes the safeguards. A read-only `public/data/chunk12_validation.json` report will summarize Wake URL shapes (without permit IDs) and Brunswick GIS field evidence after a successful workflow refresh.

## Chunk 13 — research-only permit review

The dashboard includes a separate **County research queue — NOT published leads** table. It shows a bounded set of Wake and Brunswick candidate permit numbers with government GIS exact-permit queries plus the current official public search sites. It does not convert older Wake links into unverified new portal deep links or assign Brunswick subcontractors as primary homebuilders.

The queue is created in `public/data/chunk13_review_queue.json` by `src/review_chunk13.py` when the workflow runs successfully. All rows have `included_in_sales_leads=false` and require separate manual issuer, date and prime-builder verification. The active dashboard and RSS continue to use the existing four verified-for-collection (not individually audited) GIS sources. See [Chunk 13 notes](docs/CHUNK_13_VALIDATION.md).

## Chunk 15 — manual verification issue drafts

The **Start verification** links in the County Research Queue open a prefilled GitHub issue draft with exact official GIS feature evidence, the county's public portal search, and a reviewer checklist for actual issuer and prime builder. This is a **human-only** workflow: no issue submission, lead approval, source activation or record promotion happens automatically.

Details, limitations and release criteria are in [Chunk 15 validation](docs/CHUNK_15_VALIDATION.md). Wake and Brunswick remain research-only.

## Chunk 17 — evidence-gated human review decisions

The [manual decision ledger](reviews/decisions.json) starts with both issue-backed Wake and Brunswick records marked **pending**. Its [validation rules](src/compile_reviews.py) reject unsupported confirmation claims, including missing official record-specific evidence, issuing authority, licensed primary GC, reviewer attestations, or duplicate resolution.

GitHub Actions generates `public/data/review_status.json`. The dashboard shows these curated review states separately from GIS consistency. **No review decision automatically enables a county or publishes leads**, including a human-marked `confirmed` decision. The workflow deliberately holds every reviewed record for a separate, future explicit release decision. Details: [Chunk 17 validation](docs/CHUNK_17_VALIDATION.md).

## Chunk 18 — release-readiness audit

The [release-readiness report](public/data/release_readiness.json) lists evidence and source-approval blockers for the manually reviewed Wake and Brunswick permits. It is generated by [src/audit_release_readiness.py](src/audit_release_readiness.py) after the curated review compiler, and uses a **fail-closed** check against source records, GitHub issue IDs and evidence rules.

**No review confirmation automatically approves a lead or enables a county**. The dashboard displays the blocked reasons in its separate research queue. See [Chunk 18 checkpoint](docs/CHUNK_18_VALIDATION.md).

## Sales-ready permit details

The **Construction opportunities** table now opens our own consistent, mobile-friendly [permit detail page](public/permit.html) for each permit. It displays the site, project scope, issuance date, value, builder and official contact details (when published), followed by an **Official Permit** link when supported and a separate **Original government GIS source** link.

The collector preserves Raleigh's publicly listed contractor phone, email, license, doing-business-as, business address, project name, square footage, stories and housing units. Other jurisdictions retain their available fields without guessing missing business contacts. CSV exports now include a direct link to the formatted permit, official permit-detail URL, government record URL and business contacts when available.

The primary view is **our own permit.html**, not a generic ArcGIS layer; the agency link remains as provenance. [Implementation and source-field coverage](docs/SALES_PERMIT_DETAILS_V1.md).

## Sales rollout — field completeness and CI diagnostics

The detailed sales view now supports official **Raleigh** contractor phone/email/license/address, **New Hanover** project name/square footage and a distinctly labeled project contact, plus **Mecklenburg/Charlotte** project name and project number. Missing fields stay unavailable; a project contact must not be presumed to be a general contractor.

The [sales contact coverage report](public/data/sales_field_coverage.json) is generated on a successful permit refresh and reports counts of records with source-published contact and project details, grouped by jurisdiction. The [CI test diagnostics](public/data/ci_test_status.json) records test pass/fail results even when tests block collection. In case of a failed run, see the failing test name and correct it before relying on new data. Details: [sales rollout checkpoint](docs/SALES_DETAIL_ROLLOUT_CHUNK2.md).

## Data quality rules

- Authoritative **issued** date required; never substitute application date.
- Reject pending/canceled/voided, renovations, trade-only and other non-ground-up permits.
- Keep permit identifiers, official source URLs and per-source errors.
- Retain previous successfully collected records if a source fails; mark failed sources accordingly.
- Do not infer builder/contractor where the government feed lacks it.
