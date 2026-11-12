# Chunk 8 — staged official-source rechecks and Wake/Brunswick pilots

**Date:** November 12, 2026
**Status:** Pilot and 6 synthetic tests committed; live pilot results and a subsequent successful Actions run are not yet confirmed at this checkpoint.

## Scope

- Existing enabled collectors (Raleigh, New Hanover County, Mecklenburg, Greensboro) remain unchanged.
- Current published baseline: 3,174 screened permits across four collection areas, with record-level issuance verification still pending.
- **No Wake or Brunswick records are promoted** into `permits.json`, builder rankings, lead RSS or dashboard totals.

## What the new script does

The new `src/validate_chunk8.py` performs bounded, read-only official GIS queries and creates `public/data/chunk8_validation.json` on a successful run.

1. **Wake County pilot:** queries up to 100 rows with issue dates, records status and work-class distributions and counts exact permit-number matches against the existing screened Raleigh candidates. This is **not full overlap detection** and is not evidence that unincorporated Wake and City of Raleigh are disjoint.
2. **Brunswick County pilot:** samples up to 100 nonblank `DateIssued` values, reports detected string formats, parseability, statuses and jurisdiction labels. Does not interpret `SubContractor` as the general contractor.
3. **Four-market consistency review:** re-queries up to two current public QA samples from each active jurisdiction by exact permit number against its agency GIS layer. Records match/changed/failed checks for date, category, address, contractor and status. This is a **same-source consistency check**, not independent validation against a different municipal permitting interface.

All pilot errors are recorded, rather than silently enabling a source or declaring a permit verified. No individual Wake/Brunswick permit rows are published.

## Evidence and limits

- The previous `public/data/source_probes.json` confirmed `ISSUE_DATE` is a native date field in Wake's GIS layer and `DateIssued` a text field in Brunswick.
- Greensboro's public Building Inspection Scheduler supports an individual permit-number URL format, but a newly issued record was not independently readable through the browser used for this checkpoint. No status change to verified is justified.
- The official Wake County catalog documents nightly geocoding and notes that some legacy records may be incomplete: https://catalog.data.gov/dataset/building-permits-ff506 .
- The public GitHub workflow was changed to execute the read-only pilot after collection and metadata probes, before committing refreshed data. Six new unit tests cover date formats, source gating, overlap detection, and recheck non-verification.

## Release gates

Wake: need exact issuance jurisdiction, source coverage, duplicate evidence beyond a bounded sample and reviewed building-work classifications.

Brunswick: need actual issue-date values and status semantics, a legitimate primary builder source, and independently checked sample new-build records.

**Do not set `live_verified=true` merely because a same-source re-query matched the cached record.**

The first results should appear in `public/data/chunk8_validation.json` after the revised workflow successfully executes. If absent, inspect Actions logs; don't infer a successful run from committed code.
