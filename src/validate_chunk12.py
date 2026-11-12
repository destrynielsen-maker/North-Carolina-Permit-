"""Chunk 12: public link integrity and Brunswick prime-builder source audit.

Bounded read-only GIS calls. Never guess record-specific replacement links.
No Wake or Brunswick permits are added to live sales leads.
"""
from __future__ import annotations
from collections import Counter
import datetime as dt
import json
import pathlib
import re
from urllib.parse import urlsplit

from collect import OUT, get
from validate_chunk10 import WAKE_URL, BRUNSWICK_URL, get_features, BRUNSWICK_NEW_HOME_TYPES

WAKE_LIMIT = 32
BRUNSWICK_LIMIT = 30
OLD_WAKE_HOST = 'energovcitizenaccess.tylertech.com'
NEW_WAKE_HOST = 'wakecountync-energovpub.tylerhost.net'
OFFICIAL_WAKE_PORTAL = 'https://wakecountync-energovpub.tylerhost.net/apps/selfservice'
OFFICIAL_BRUNSWICK_PORTAL = 'https://bcpp.brunswickcountync.gov/'
OFFICIAL_BRUNSWICK_SEARCH = 'https://apps.brunsco.net/bcms/dashboard/'


def wake_link_signature(value):
    """Summarize URL routing, never emitting a permit ID or private query value."""
    if not isinstance(value, str) or len(value) > 4096:
        return {'state': 'missing_or_invalid'}
    try:
        url = urlsplit(value.strip())
        if url.scheme.lower() != 'https' or not url.hostname or url.username or url.password:
            return {'state': 'missing_or_invalid'}
        host = url.hostname.lower()
        if host not in (OLD_WAKE_HOST, NEW_WAKE_HOST):
            return {'state': 'unexpected_host'}
        # Only use static route markers: no path suffixes or fragments that
        # may contain permit IDs or personally identifying information.
        fragment_first = url.fragment.lstrip('/').split('/', 1)[0].split('?', 1)[0].lower()
        fragment_route = fragment_first if fragment_first in (
            'permit', 'permits', 'view', 'search', 'home', 'dashboard', 'inspection',
            'inspections', 'mywork', 'case', 'record') else 'other_or_none'
        return {
            'state': 'legacy_host' if host == OLD_WAKE_HOST else 'current_host',
            'host': host,
            'has_fragment': bool(url.fragment),
            'fragment_first_route': fragment_route,
            'has_query_string': bool(url.query),
            'has_later_fragment_path_segments': '/' in url.fragment.lstrip('/'),
        }
    except ValueError:
        return {'state': 'missing_or_invalid'}


def wake_link_pilot(request=get_features):
    rows = request(WAKE_URL, {
        'where': ("ISSUE_DATE IS NOT NULL AND PERMIT_STATUS = 'Issued' "
                  "AND WORK_CLASS = 'New One- and Two-Family Dwelling'"),
        'outFields': 'PERMIT_NUMBER,ISSUE_DATE,LINK',
        'returnGeometry': 'false',
        'orderByFields': 'ISSUE_DATE DESC',
        'resultRecordCount': WAKE_LIMIT,
    })
    signatures = [wake_link_signature(row.get('attributes',{}).get('LINK'))
                  for row in rows[:WAKE_LIMIT]]
    states = Counter(x['state'] for x in signatures)
    first_routes = Counter(x.get('fragment_first_route','missing')
                           for x in signatures)
    legacy_record_like = sum(
        x.get('state') == 'legacy_host'
        and x.get('fragment_first_route') in ('permit','permits','view','record','case')
        and x.get('has_later_fragment_path_segments',False)
        for x in signatures)
    return {
        'state': 'sampled_no_promotion',
        'sample_size': min(len(rows), WAKE_LIMIT),
        'link_states': dict(sorted(states.items())),
        'fragment_route_classes': dict(sorted(first_routes.items())),
        'legacy_links_appearing_record_specific': legacy_record_like,
        'old_gis_link_host': OLD_WAKE_HOST,
        'current_official_search_portal': OFFICIAL_WAKE_PORTAL,
        'deep_links_verified_at_new_portal': 0,
        'link_policy': ('Never substitute the new portal host into a legacy record-specific '
                        'URL without a tested direct-link translation. Use current official '
                        'search portal and permit number for manual lookup until verified.'),
        'enabled_for_collection': False,
    }


def brunswick_builder_field_pilot(metadata_request=get,
                                 request=get_features):
    layer = metadata_request(BRUNSWICK_URL, {'f':'json'})
    if layer.get('error'):
        raise RuntimeError('Brunswick GIS schema unavailable: '+str(layer['error'])[:160])
    fields = layer.get('fields')
    if not isinstance(fields, list) or not fields:
        raise RuntimeError('Brunswick GIS schema missing fields')
    names = {str(field.get('name','')) for field in fields}
    gc_candidates = sorted(name for name in names
                           if re.search(r'contractor|builder',name,re.I)
                           and not re.search(r'subcontractor|sub_contractor',name,re.I))
    types = ','.join("'"+t.replace("'","''")+"'" for t in BRUNSWICK_NEW_HOME_TYPES)
    rows = request(BRUNSWICK_URL, {
        'where': "ProjectType = 'Residential' AND PermitStatus = 'Active' "
                 "AND PermitType IN ("+types+") AND DateIssued IS NOT NULL",
        'outFields': 'PermitNumber,ProjectNumber,DateIssued,SubContractor,PermitType',
        'returnGeometry':'false',
        'orderByFields':'DateIssued DESC',
        'resultRecordCount':BRUNSWICK_LIMIT,
    })
    subcontractor_count = sum(
        bool(str(r.get('attributes',{}).get('SubContractor') or '').strip())
        for r in rows[:BRUNSWICK_LIMIT])
    return {
        'state': 'sampled_no_promotion',
        'sample_size': min(len(rows),BRUNSWICK_LIMIT),
        'gis_fields_count': len(fields),
        'gis_subcontractor_field_present': 'SubContractor' in names,
        'independent_gc_or_builder_field_candidates': gc_candidates,
        'nonblank_subcontractor_fields': subcontractor_count,
        'verified_prime_builder_names': 0,
        'official_permit_portal': OFFICIAL_BRUNSWICK_PORTAL,
        'official_public_permit_search': OFFICIAL_BRUNSWICK_SEARCH,
        'interpretation': ('The available GIS layer has no independently verified prime-builder '
                           'assignment. SubContractor cannot be used as a general contractor. '
                           'A browser/account-dependent portal may require manual review.'),
        'enabled_for_collection': False,
    }


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report = {
        'checked_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'policy': 'Read-only URL-pattern and GC-field validation; no source activated',
        'independent_permit_verification': False,
        'pilots': {},
    }
    for name,fn in [('wake_link_integrity',wake_link_pilot),
                    ('brunswick_gc_fields',brunswick_builder_field_pilot)]:
        try:
            report['pilots'][name]=fn()
        except Exception as exc:
            report['pilots'][name]={
                'state':'probe_error','detail':str(exc)[:200],
                'enabled_for_collection':False,
            }
    (OUT/'chunk12_validation.json').write_text(
        json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v['state'] for k,v in report['pilots'].items()}))

if __name__ == '__main__':
    main()
