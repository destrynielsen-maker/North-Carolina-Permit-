"""Chunk 17: compile explicitly curated permit review decisions.

Review decisions must come from a human after official portal inspection.
Passing this validator is not an independent permit verification and never
writes, augments or promotes records to permits.json, builder data or RSS.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
from urllib.parse import urlsplit

ROOT = pathlib.Path(__file__).resolve().parents[1]
DECISIONS_FILE = ROOT / 'reviews' / 'decisions.json'
ISSUES_FILE = ROOT / 'public' / 'data' / 'verification_issues.json'
QUEUE_FILE = ROOT / 'public' / 'data' / 'chunk13_review_queue.json'
OUTPUT_FILE = ROOT / 'public' / 'data' / 'review_status.json'

DECISIONS = frozenset(('pending', 'needs_follow_up', 'confirmed', 'rejected'))
DUPLICATE_STATES = frozenset(('unreviewed', 'no_match', 'confirmed_duplicate', 'unresolved'))
PORTAL_HOSTS = {
    'wake': frozenset(('wakecountync-energovpub.tylerhost.net', 'wake.gov', 'www.wake.gov')),
    'brunswick': frozenset((
        'bcpp.brunswickcountync.gov', 'apps.brunsco.net',
        'brunswickcountync.gov', 'www.brunswickcountync.gov'
    )),
}
BOOLEAN_CHECKS = (
    'permit_id_confirmed', 'issued_date_confirmed',
    'status_confirmed', 'new_construction_confirmed',
    'reviewer_attests_portal_record_match'
)


def official_record_evidence_url(url, source):
    """A candidate official record URL, NOT an automated verification."""
    if not isinstance(url, str) or len(url) > 2048:
        return False
    try:
        u = urlsplit(url.strip())
        if (u.scheme != 'https' or not u.hostname or u.port not in (None, 443)
                or u.username or u.password or u.hostname.lower() not in PORTAL_HOSTS.get(source, ())):
            return False
    except ValueError:
        return False
    if u.fragment.lower().startswith(('/search', '/home', '/dashboard')):
        return False
    # A generic portal home/search route, even with no query, is not evidence.
    if source == 'wake' and u.hostname.lower() == 'wakecountync-energovpub.tylerhost.net':
        if u.path.rstrip('/').lower() == '/apps/selfservice':
            return bool(u.fragment and (
                u.fragment.lower().startswith('/permit/') or
                u.fragment.lower().startswith('/record/')
            ))
    if source == 'brunswick' and u.hostname.lower() == 'bcpp.brunswickcountync.gov':
        if u.path in ('/', '', '/login', '/search'):
            return False
    if u.path in ('/', '', '/search'):
        return False
    # For other official files/pages, a record-specific URL still needs
    # human attestation of the exact permit match.
    return bool(u.query or u.fragment or len(u.path.strip('/').split('/')) >= 2)


def validate_and_compile(decisions_document, manifest, queue, today=None):
    today = today or dt.datetime.now(dt.timezone.utc).date()
    errors = []
    if decisions_document.get('schema_version') != 1:
        errors.append('Unsupported review schema version')
    items = decisions_document.get('decisions')
    if not isinstance(items, list):
        raise ValueError('review decisions must be a list')
    manifest_entries = manifest.get('entries', [])
    if not isinstance(manifest_entries, list):
        raise ValueError('issue manifest entries must be a list')
    index = {}
    for issue in manifest_entries:
        key = (issue.get('source'), issue.get('gis_object_id'))
        if key in index:
            errors.append('Duplicate issue-manifest record: '+str(key))
        index[key] = issue

    queue_index = {
        (source, row.get('gis_object_id')): row
        for source, bundle in queue.get('sources', {}).items()
        for row in bundle.get('candidates', [])
    }

    seen = set()
    reviews = []
    for row in items:
        if not isinstance(row, dict):
            errors.append('Review entry must be an object')
            continue
        source, oid = row.get('source'), row.get('gis_object_id')
        key = (source, oid)
        if source not in PORTAL_HOSTS or type(oid) is not int or oid <= 0:
            errors.append('Unknown source or invalid GIS object id')
            continue
        if key in seen:
            errors.append('Duplicate review decision: '+str(key))
            continue
        seen.add(key)
        issue = index.get(key)
        candidate = queue_index.get(key)
        if not issue or not candidate:
            errors.append('Review does not match the issue manifest and current research queue: '+str(key))
            continue
        if row.get('issue_number') != issue.get('issue_number'):
            errors.append('Issue number mismatch: '+str(key))
        decision = row.get('decision')
        if decision not in DECISIONS:
            errors.append('Invalid decision state: '+str(key))
            continue
        duplicate = row.get('duplicate_disposition')
        if duplicate not in DUPLICATE_STATES:
            errors.append('Invalid duplicate disposition: '+str(key))
        for flag in BOOLEAN_CHECKS:
            if type(row.get(flag)) is not bool:
                errors.append('Review flag '+flag+' must be boolean: '+str(key))
        if row.get('included_in_sales_leads') is True:
            errors.append('Review cannot promote leads: '+str(key))

        if decision in ('needs_follow_up', 'rejected') and not str(row.get('reason') or '').strip():
            errors.append('Review decision needs a reason: '+str(key))

        if decision == 'confirmed':
            missing = [
                label for label in ('reviewer','reviewed_on','official_evidence_url',
                                    'official_record_reference','issuer','licensed_prime_builder')
                if not str(row.get(label) or '').strip()
            ]
            if missing:
                errors.append('Confirmed review missing: '+','.join(missing)+' '+str(key))
            if any(row.get(flag) is not True for flag in BOOLEAN_CHECKS):
                errors.append('Confirmed review missing individual attestations: '+str(key))
            if duplicate != 'no_match':
                errors.append('Confirmed review needs resolved no-match duplicate check: '+str(key))
            if not official_record_evidence_url(row.get('official_evidence_url'), source):
                errors.append('Confirmed review requires record-specific official evidence URL: '+str(key))
            reviewed_on = row.get('reviewed_on')
            try:
                d = dt.date.fromisoformat(reviewed_on)
                if d > today:
                    errors.append('Review date in future: '+str(key))
            except (TypeError, ValueError):
                errors.append('Review date invalid: '+str(key))
            # A human "confirmed" decision remains outside sales leads until
            # a separate, explicit release process exists and is authorized.
        reviews.append({
            'source': source, 'gis_object_id': oid,
            'reference_label': candidate.get('reference_label') or candidate.get('permit_number'),
            'decision': decision, 'issue_url': issue['issue_url'],
            'evidence_recorded': decision == 'confirmed',
            'independently_verified_by_automation': False,
            'release_status': 'held_research_only',
            'included_in_sales_leads': False,
        })
    # Current two issue-backed reviews must be represented; missing one
    # should not silently show it as reviewed, or remove its pending status.
    if seen != set(index):
        errors.append('Review decisions must correspond exactly to the issue manifest')
    if errors:
        raise ValueError('; '.join(errors))
    reviews.sort(key=lambda x: (x['source'], x['gis_object_id']))
    counts = {name: sum(x['decision'] == name for x in reviews) for name in sorted(DECISIONS)}
    return {
        'schema_version': 1,
        'meaning': ('Human-curated review state only. Confirmed means reviewer documented '
                    'evidence, not an automated verification or published lead.'),
        'counts': counts,
        'auto_promoted_leads': 0,
        'new_sources_enabled': 0,
        'reviews': reviews,
    }


def main():
    decisions = json.loads(DECISIONS_FILE.read_text(encoding='utf-8'))
    manifest = json.loads(ISSUES_FILE.read_text(encoding='utf-8'))
    queue = json.loads(QUEUE_FILE.read_text(encoding='utf-8'))
    compiled = validate_and_compile(decisions, manifest, queue)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(compiled, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'status': 'compiled review states; no lead promotion',
                      'counts': compiled['counts'],
                      'promoted': compiled['auto_promoted_leads']}))


if __name__ == '__main__':
    main()
