# Chunk 9 — recover pilot workflow and evaluate Wake / Brunswick

Date: November 12, 2026. All public records remain screened candidates; no new jurisdiction is enabled.

## Workflow recovery

The initial Chunk 8 validation workflow did not publish `public/data/chunk8_validation.json` because an offline test incorrectly searched for the word "contractor" anywhere in the Brunswick diagnostic output. The diagnostic text explicitly said that no prime contractor was inferred from SubContractor, triggering a false failure.

Fixed the test to check for contractor-assignment **fields**, not words in explanatory warnings. Commit: `951950923b2d57014b847c212d5989b5b2055c1d`. A subsequent GitHub Actions collection commit `afeeaf77c83a12028a4f6dcddc930babf718673f` generated the validation file at **2026-11-12 19:55:26 UTC**, confirming that the pipeline completed collection.

## Wake County pilot — latest confirmed result

- 100 official GIS records sampled, all with status **Issued**.
- 99 distinct permit numbers in sample of 100 rows (could reflect repeated identifier; investigate before counting).
- 0 exact permit number matches against 781 *screened* Raleigh candidates.
- Work classifications include 43 new one-/two-family dwellings, 21 alterations, 8 additions, and smaller trade/accessory categories.
- This is NOT sufficient to certify disjoint city/county boundaries or unique projects. Sample covers a tiny newest-first slice and compares against screened Raleigh permits only.
- Wake remains **disabled**. No count addition or automatic dedupe.

Data catalog: https://catalog.data.gov/dataset/building-permits-ff506

## Brunswick County pilot — initial confirmed result

- 100 records sampled; all have parseable ISO-style date strings.
- 99 records have status **Legacy**; one **Void**. No prime contractor inferred from `SubContractor`.
- This was an **unordered** sample, not evidence of current permit activity.
- Refined the pilot to order by `DateIssued DESC` and report min/max issue dates, count within 365 days, and permit type mix; tests now verify order and date metrics.
- **New sorted pilot results are pending at the time this report was drafted.**

The official Brunswick permit reporting page distinguishes live records (subject to voids and revisions) from monthly archived datasets:
https://brunswickcountync.gov/195/Permit-Reports

## Active-market permit consistency

Eight records were re-queried from the same issuing-agency GIS layers, two per active market. All eight had matching dates, statuses, categories, addresses and contractors. This is *same-source consistency*, not independently authenticated permit detail. `live_verified=false` stays unchanged.

## Additional hardening

- `src/probe_sources.py` now publishes the safe field-name inventory for candidate source layers, so Wake scope/jurisdiction fields can be assessed without enabling the feed.
- No staged permit records enter `permits.json`, the dashboard, RSS or builder rankings.
- 6 pilot tests + prior 38 tests = 44 offline tests. A successful workflow-produced validation file demonstrates the earlier suite passed. Newer sorted-date test/metadata changes require a subsequent workflow run to confirm.

## Next gating decisions

1. Review the sorted Brunswick sample and exclude Legacy/Void status records from all candidate leads.
2. Inspect Wake's complete field inventory for possible issuer/city scope; determine how duplicate permit IDs and Raleigh overlap can be detected reliably.
3. Only then trial a source-specific qualification pass, retaining all new-source records in a quarantine/review file until agency-level sample checks.
4. Keep live totals at the four approved markets (latest previously confirmed 3,174) until the release gates pass.

## Checkpoint limitations

We have not independently opened corresponding municipal permit-detail pages for the eight samples. No individual record has been promoted to verified, and neither Wake nor Brunswick has been enabled.
