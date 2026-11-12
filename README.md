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

The [permit refresh workflow](.github/workflows/permits.yml) runs on pushes to `main`, manual dispatch and every six hours at minute 17 UTC. It checks the offline test suite (27 tests as of Chunk 6), queries official services, commits the refreshed data and deploys the `public/` folder.

**Enable Pages:** Repository → **Settings** → **Pages** → **Build and deployment** → **Source: GitHub Actions**. After enabling, use the **Actions** tab to run `North Carolina permit refresh and deploy` if the initial push didn't deploy.

Dashboard URL (after successful deployment): https://destrynielsen-maker.github.io/North-Carolina-Permit-/

Every successful refresh writes `public/data/diagnostics.json`, aggregated work types, permit types, statuses, and rejection reasons to diagnose undercounting. These aggregate diagnostics contain no rejected permit addresses.

Chunk 6 also adds a **non-destructive** `public/data/overlap_audit.json` for exact cross-source permit-number collisions (no automatic merges), and safely consolidates contractor spelling, punctuation and license-label variants in builder rollups while retaining original aliases. Wake County remains disabled until its issuer and duplicate coverage are confirmed.

See [source directory](docs/SOURCE_DIRECTORY.md) and [Chunk 6 checkpoint](docs/CHUNK_6_VALIDATION.md) for government data URLs, validation evidence, and coverage caveats.

## Data quality rules

- Authoritative **issued** date required; never substitute application date.
- Reject pending/canceled/voided, renovations, trade-only and other non-ground-up permits.
- Keep permit identifiers, official source URLs and per-source errors.
- Retain previous successfully collected records if a source fails; mark failed sources accordingly.
- Do not infer builder/contractor where the government feed lacks it.
