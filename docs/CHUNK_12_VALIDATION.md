# Chunk 12 — Wake permit links and Brunswick builder attribution

Date: November 12, 2026

## Goal and non-promotion rule

Improve the usefulness of source links, but **do not** invent record-specific URL transformations or misidentify subcontractors as the prime contractor. Wake and Brunswick remain disabled in the live permit collector. Existing screened permit count is 3,174 across Raleigh, New Hanover, Mecklenburg and Greensboro; individual records still require issuing-agency validation.

## Wake: official portal migration

The Wake GIS `LINK` field in the Chunk 11 sample used `energovcitizenaccess.tylertech.com` for all 32 sampled records. The government's newer 2026 portal instructions point to:

- Current Wake portal: https://wakecountync-energovpub.tylerhost.net/apps/selfservice
- Official Wake January 2026 login guide: https://s3.us-west-1.amazonaws.com/wakegov.com.if-us-west-1/s3fs-public/documents/2026-01/logging_in_as_a_registered_user.pdf

The current portal has public-record search, but **a matching new record-specific deep-link route has not been verified**. Rewriting the old host into a new host is not a valid substitution until a real permit link has been opened and confirmed.

`src/validate_chunk12.py` requests a bounded sample of 32 recently issued Wake new-home records with their `LINK` field. It safely reports host and fragment-route categories without publishing actual record IDs or URL query values. It keeps `deep_links_verified_at_new_portal=0` unless separate verification is performed.

**User-facing change:** the North Carolina dashboard now offers the official current Wake public permit search, while original source provenance remains unchanged. This is not a direct-permit link.

## Brunswick: builder evidence

Official County permit and spatial records:

- County Permit Reports / filtered Residential New Home data: https://brunswickcountync.gov/195/Permit-Reports
- Brunswick Permit Portal: https://bcpp.brunswickcountync.gov/
- County-linked public permit search: https://apps.brunsco.net/bcms/dashboard/

The available official Permit Locations GIS schema has `SubContractor` and permit/project IDs, but no verified general-contractor or prime-builder field. Third-party commercial websites describe additional contractor data; **do not assume that their data is a public official GIS attribute or mix it into the current unverified dataset.**

`src/validate_chunk12.py` verifies source fields and samples at most 30 active new residential records. It counts nonblank `SubContractor` values, but never treats those values as homebuilders. It publishes no contractor names. It does not access credential-gated endpoints.

**User-facing change:** the dashboard links to Brunswick's official permit portal and county report page as research tools, without adding Brunswick permits to the lead count.

## Tests and release gates

`tests/test_chunk12.py` adds seven synthetic tests:
- Legacy and current Wake URL classification
- Redaction of permit IDs and URL query information
- Rejecting unsafe/external URLs
- No automatic deep-link migration
- Brunswick field evidence and zero prime-builder attribution
- Fail-closed behavior for unavailable metadata

GitHub Actions runs the script after previous collection and validations, generating `public/data/chunk12_validation.json` when successful.

**Enable Wake only after** independent official record-level link verification and an issuing-jurisdiction and Raleigh-overlap rule. **Enable Brunswick builder attribution only after** an official primary contractor field/record is identified and verified for sample permits. Until then the new source outputs are evidence-only.

## Next checkpoint

Inspect the new output for Wake route structures. If record-specific legacy routes are present, attempt a tiny manual browser validation in the *official current portal*, without guessing URL translations. For Brunswick, explore the official public permit search UI for prime contractor fields; document whether usable without authentication. Neither can be promoted without successful record QA.
