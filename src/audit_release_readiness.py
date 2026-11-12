"""Chunk 18: audit reviewed permits against explicit release gates.

Produces an explanatory READ-ONLY release-readiness report. Nothing in this
module writes to permits.json, builder rankings, feeds, source enablement or
GitHub review issues. Even a manually 'confirmed' review stays on hold.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW_LEDGER = ROOT / 'reviews' / 'decisions.json'
REVIEW_STATUS = ROOT / 'public' / 'data' / 'review_status.json'
ISSUES = ROOT / 'public' / 'data' / 'verification_issues.json'
QUEUE = ROOT / 'public' / 'data' / 'chunk13_review_queue.json'
SOURCES = ROOT / 'public' / 'data' / 'sources.json'
OUTPUT = ROOT / 'public' / 'data' / 'release_readiness.json'

# These source keys deliberately have NO automatic approval route.
RESEARCH_ONLY = frozenset({'wake', 'brunswick'})
FLAGS = ('permit_id_confirmed', 'issued_date_confirmed', 'status_confirmed',
         'new_construction_confirmed', 'reviewer_attests_portal_record_match')


def audit_readiness(ledger, statuses, issue_manifest, queue, sources):
    """Fail closed on stale/mismatched source IDs and curated status data."""
    entries = ledger.get('decisions', [])
    published = statuses.get('reviews', [])
    issue_entries = issue_manifest.get('entries', [])
    if not isinstance(entries, list) or not isinstance(published, list) or not isinstance(issue_entries, list):
        raise ValueError('Review inputs must be lists')

    def index_unique(rows, name):
        index = {}
        for r in rows:
            if not isinstance(r, dict):
                raise ValueError(name + ' includes an invalid entry')
            k = (r.get('source'), r.get('gis_object_id'))
            if k in index or k[0] not in RESEARCH_ONLY or type(k[1]) is not int or k[1] < 1:
                raise ValueError(name + ' contains duplicated or invalid GIS identity')
            index[k] = r
        return index

    d = index_unique(entries, 'curated decisions')
    p = index_unique(published, 'compiled statuses')
    m = index_unique(issue_entries, 'issue manifest')
    q = index_unique([
        dict(record, source=source)
        for source, bundle in queue.get('sources', {}).items()
        if source in RESEARCH_ONLY
        for record in bundle.get('candidates', [])
    ], 'research queue')

    if set(d) != set(p) or set(d) != set(m) or not set(d).issubset(set(q)):
        raise ValueError('Stale or mismatched curated review, manifest, or research queue')

    # A county listed as active in the production collector would demand
    # an explicit re-audit of the exclusion policy, not silent continuation.
    for source in sources.get('sources', []):
        if source.get('name') in ('Wake County', 'Brunswick County') and (
            source.get('qualified', 0) != 0 or
            str(source.get('state', '')).lower().startswith('collected')
        ):
            raise ValueError('Research-only county unexpectedly present in production')

    if statuses.get('auto_promoted_leads') != 0 or statuses.get('new_sources_enabled') != 0:
        raise ValueError('Compiled statuses unexpectedly authorize promotion')

    result = []
    for k in sorted(d):
        review = d[k]
        state = p[k]
        issue = m[k]
        original = q[k]
        if (state.get('decision') != review.get('decision') or
                state.get('issue_url') != issue.get('issue_url') or
                review.get('issue_number') != issue.get('issue_number') or
                issue.get('permit_number') != original.get('permit_number') or
                (k[0] == 'brunswick' and issue.get('project_number') != original.get('project_number')) or
                state.get('included_in_sales_leads') is not False or
                state.get('release_status') != 'held_research_only'):
            raise ValueError('Review status, issue and research record disagree: ' + str(k))

        blockers = []
        if review.get('decision') != 'confirmed':
            blockers.append('review_not_confirmed')
        if not review.get('official_evidence_url'):
            blockers.append('official_record_evidence_missing')
        if not review.get('reviewer') or not review.get('reviewed_on'):
            blockers.append('named_human_review_missing')
        if not review.get('issuer'):
            blockers.append('issuing_authority_unverified')
        if not review.get('licensed_prime_builder'):
            blockers.append('licensed_prime_builder_unverified')
        if review.get('duplicate_disposition') != 'no_match':
            blockers.append('duplicate_check_unresolved')
        if any(review.get(flag) is not True for flag in FLAGS):
            blockers.append('portal_identity_and_issuance_attestations_incomplete')

        # These two gates are intentionally outside the ledger/compiled
        # statuses. Evidence may be complete, but still needs release approval.
        blockers.append('source_not_approved_for_live_collection')
        blockers.append('separate_manual_release_authorization_required')

        result.append({
            'source': k[0],
            'gis_object_id': k[1],
            'reference_label': original.get('reference_label'),
            'issue_url': issue.get('issue_url'),
            'curated_decision': review.get('decision'),
            'evidence_complete_for_review': (
                review.get('decision') == 'confirmed'
                and len(blockers) == 2),
            'blocked_reasons': blockers,
            'release_status': 'held_research_only',
            'included_in_sales_leads': False,
        })
    counts = {
        'research_records_audited': len(result),
        'pending_or_followup_or_rejected': sum(x['curated_decision'] != 'confirmed' for x in result),
        'evidence_complete_for_review': sum(x['evidence_complete_for_review'] for x in result),
        'eligible_for_automatic_promotion': 0,
        'new_live_sources_approved': 0,
    }
    return {
        'schema_version': 1,
        'generated_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'scope': 'Wake and Brunswick manual review gating; no changes to production permits',
        'policy': 'Only explicitly authorized future releases may change published leads. Compiled review state never does.',
        'counts': counts,
        'reviews': result,
    }


def main():
    def read(path):
        return json.loads(path.read_text(encoding='utf-8'))
    output = audit_readiness(
        read(REVIEW_LEDGER), read(REVIEW_STATUS), read(ISSUES),
        read(QUEUE), read(SOURCES))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(output['counts']))


if __name__ == '__main__':
    main()
