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
- A newer pilot run has now completed; see the confirmed follow-up results below.

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

## Confirmed updated pilot at 2026-11-12 20:01:13 UTC

**Pipeline:** GitHub Actions committed a fresh `chunk8_validation.json` report at collection commit `bee1f2362b9cb39b267a64a4b6a79d97127b413a` after the test fix and date-ordering changes.

**Wake:** newest 100 rows have issue dates November 4–10, 2026, and all statuses `Issued`. They contain 99 distinct permit numbers, **one repeated permit ID row and zero blank IDs**, with **zero exact matches** against the 781 screened Raleigh permit IDs. This is not an exhaustive duplicate check. The full set of 25 fields now shows `DISTRICT`, `X`, `Y`, `PIN` and `LINK`, but **no explicit issuing jurisdiction**. Mailing-city fields describe mailing addresses and must not be used as project jurisdiction. Need a government planning-jurisdiction boundary test and official record review before enabling.

**Brunswick:** with the new `DateIssued DESC` sampling, 100 records are ISO-like strings and all parseable; 98 are dated in the preceding 365 days. **96 have status Active, 2 Legacy, 2 Void.** The sample includes an anomalous **2099-02-12** issue date—future-dated records must be rejected. Dominant permit types are RE-INSPECTION FEE (12), INC MECH (12), ELECTRICAL (8), ZONING PERMIT (7), TEMPORARY ELECTRICAL POWER (6), COMMERCIAL FLOODPLAIN BUILDING (5), INC MECH-GAS (5), CHANGE OUT MECHANICAL (5), INCLUDED ELECTRICAL (5) and T-POLE (4). This feed is **not yet appropriate to publish as newly issued ground-up building permits**. Also, `SubContractor` is not a general contractor source.

**Existing four markets:** the earlier eight exact record-level GIS rechecks were all consistent, but independent portal verification is still 0. Total previously collected candidate permits: **3,174** (Raleigh 781, New Hanover 813, Mecklenburg 701, Greensboro 879).

**Release decision:** Do not enable Wake or Brunswick in the live lead dashboard in Chunk 9. No unverified candidate or future-dated permit was added from these feeds. The next chunk should validate a Wake geospatial issuing-jurisdiction rule and seek a dedicated Brunswick new-home construction report/source with genuine contractor information.
