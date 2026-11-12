# Chunk 7 — QA queue, builder rankings and source investigation

Date: November 12, 2026. Status: code and first generated outputs verified; agency-level permit detail checks remain pending.

## Live collection baseline

| Jurisdiction | Screened permits |
|---|---:|
| Raleigh | 781 |
| New Hanover County | 813 |
| Mecklenburg County / Charlotte | 701 |
| Greensboro | 879 |
| **Total** | **3,174** |

These counts are screened permit candidates, not distinct projects or independently verified sales leads.

## Manual permit QA queue

The public/data/qa_samples.json output includes 24 review items (six per active market), chosen first across available categories and then by newest issue date. Each item includes its permit number, date, status, category, contractor where available, valuation and a link to query the issuing agency's GIS service. Every item is labeled manual_review_required. Source links and existing GIS extracts are not independent human verification.

## Builder ranking improvements

The public/data/builder_rankings.json output ranks screened activity over the latest 90 days, using 30 days and total screened permits as tiebreakers. It contains category breakdown, total value, average value, issue date, aliases and jurisdictions. The dashboard shows the top 20 groups. It does not attribute missing builders or conflate similar legal entities.

First collected ranking: 378 builder groups, led by the following 90-day counts:

| Builder | 90-day screened permits | 30-day screened permits |
|---|---:|---:|
| Clayton Properties Group Inc (license 81396) | 67 | 21 |
| Meritage Homes of the Carolinas, Inc. | 62 | 36 |
| D R Horton, Inc | 46 | 24 |
| Stanley Martin Homes LLC | 42 | 10 |
| True Homes, LLC | 38 | 18 |

## Investigated but not enabled

The latest read-only source_probes.json was checked at 2026-11-12T19:12:29Z.

| County | Observed government schema | Gating reason |
|---|---|---|
| Wake | 25 fields, with authoritative ISSUE_DATE typed as a date, PERMIT_NUMBER, PERMIT_STATUS, WORK_CLASS, DESCRIPTION and CONTRACTOR | No confirmed jurisdiction/agency overlap with Raleigh, so leave disabled |
| Brunswick | 20 fields; DateIssued is string; permit and project status, jurisdiction, description and SubContractor | Need live date-format/permit-class evidence; do not interpret SubContractor as the GC |
| Cabarrus | 19 fields in plan-review layer; filing and application-status dates but no issue date | Need a different authoritative issued-building-permit service |
| Johnston | Official permit search by work type and date, with contractor and cost | No validated machine-readable interface yet |

Source links: https://github.com/destrynielsen-maker/North-Carolina-Permit-/blob/main/docs/SOURCE_DIRECTORY.md

## QA status

- 35 synthetic/offline unit tests passed.
- First automated builder ranking and manual sample files observed in repository.
- All three new GIS source schemas were fetched and analyzed by the workflow; no permits from these sources were promoted.
- Actual agency-level spot-check pass count is zero, pending review, so the global live_verified flag remains false.
- Source and permit feeds remain separate; duplicates are not removed solely by matching addresses.

## Next checkpoint

Official permit detail verification; staged Wake overlap sampling (with no lead publication); validation of Brunswick text issue dates; and a search for issued-building-permit data from Cabarrus and Johnston.
