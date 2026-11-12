"""Chunk 13: read-only, permit-number review queue for disabled counties.

This is a research aid, NOT a lead collector. No permit in this output is
independently verified or promoted into permits.json or builder rankings.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
from urllib.parse import urlencode

from collect import OUT, issue_date, value
from validate_chunk10 import WAKE_URL, BRUNSWICK_URL, get_features
from validate_chunk12 import wake_link_signature, OFFICIAL_WAKE_PORTAL, OFFICIAL_BRUNSWICK_PORTAL

WAKE_SAMPLE_LIMIT = 8
BRUNSWICK_SAMPLE_LIMIT = 8
ALLOWED_ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,69}$')


def official_gis_lookup(layer, object_id):
    """Lookup a unique GIS object ID, not a potentially repeated permit number.

    ArcGIS OBJECTID is unique within the current published layer. It may
    change if the layer is republished, so the portal ID is also retained.
    """
    if layer not in (WAKE_URL, BRUNSWICK_URL):
        return ''
    if type(object_id) is not int or not 1 <= object_id <= 2_147_483_647:
        return ''
    params = {
        'f': 'pjson', 'where': f'OBJECTID = {object_id}',
        'outFields': '*', 'returnGeometry': 'false',
    }
    return layer + '/query?' + urlencode(params)


def wake_review_rows(request=get_features, today=None):
    today = today or dt.datetime.now(dt.timezone.utc).date()
    rows = request(WAKE_URL, {
        'where': "ISSUE_DATE IS NOT NULL AND PERMIT_STATUS = 'Issued' "
                 "AND WORK_CLASS = 'New One- and Two-Family Dwelling'",
        'outFields': 'OBJECTID,PERMIT_NUMBER,ISSUE_DATE,PERMIT_STATUS,WORK_CLASS,CONTRACTOR,LINK',
        'returnGeometry': 'false',
        'orderByFields': 'ISSUE_DATE DESC',
        'resultRecordCount': WAKE_SAMPLE_LIMIT,
    })
    result = []
    for r in rows[:WAKE_SAMPLE_LIMIT]:
        a = r.get('attributes') or {}
        ident = str(value(a, 'PERMIT_NUMBER') or '').strip()
        when = issue_date(value(a, 'ISSUE_DATE'))
        link = official_gis_lookup(WAKE_URL, value(a, 'OBJECTID'))
        if not when or not (0 <= (today - when).days <= 365) or not link:
            continue
        signature = wake_link_signature(value(a, 'LINK'))
        result.append({
            'source': 'Wake County', 'permit_number': ident,
            'issued_date': when.isoformat(),
            'work_class': str(value(a, 'WORK_CLASS') or ''),
            'contractor_as_listed_unverified': str(value(a, 'CONTRACTOR') or '').strip()[:160],
            'exact_gis_query_url': link, 'gis_object_id': value(a, 'OBJECTID'),
            'official_portal_search': OFFICIAL_WAKE_PORTAL.rstrip('/') + '#/search',
            'legacy_link_state': signature.get('state', 'missing_or_invalid'),
            'legacy_link_route': signature.get('fragment_first_route','other_or_none'),
            'record_verification': 'manual_portal_review_required',
            'issuer_verification': 'unknown_issuer_review_required',
            'included_in_sales_leads': False,
        })
    return result


def brunswick_review_rows(request=get_features, today=None):
    today = today or dt.datetime.now(dt.timezone.utc).date()
    rows = request(BRUNSWICK_URL, {
        'where': ("ProjectType = 'Residential' AND PermitStatus = 'Active' "
                  "AND PermitType IN ('NEW HOME','RESIDENTIAL MODULAR','TOWNHOME') "
                  "AND DateIssued IS NOT NULL"),
        'outFields': ('OBJECTID,PermitNumber,ProjectNumber,DateIssued,PermitStatus,'
                      'PermitType,ParcelAddress,Jurisdiction'),
        'returnGeometry': 'false',
        'orderByFields': 'DateIssued DESC',
        'resultRecordCount': BRUNSWICK_SAMPLE_LIMIT,
    })
    result = []
    for r in rows[:BRUNSWICK_SAMPLE_LIMIT]:
        a = r.get('attributes') or {}
        ident = str(value(a, 'PermitNumber') or '').strip()
        when = issue_date(value(a, 'DateIssued'))
        link = official_gis_lookup(BRUNSWICK_URL, value(a, 'OBJECTID'))
        if not when or not (0 <= (today - when).days <= 365) or not link:
            continue
        result.append({
            'source': 'Brunswick County', 'permit_number': ident,
            'project_number': str(value(a, 'ProjectNumber') or '').strip()[:80],
            'issued_date': when.isoformat(),
            'permit_type': str(value(a, 'PermitType') or '').strip()[:100],
            'address': str(value(a, 'ParcelAddress') or '').strip()[:160],
            'reported_jurisdiction': str(value(a, 'Jurisdiction') or '').strip()[:100],
            'exact_gis_query_url': link, 'gis_object_id': value(a, 'OBJECTID'),
            'official_portal_search': OFFICIAL_BRUNSWICK_PORTAL,
            'prime_builder': None,
            'prime_builder_verification': 'not_available_from_this_gis_layer',
            'record_verification': 'manual_portal_review_required',
            'included_in_sales_leads': False,
        })
    return result


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = {
        'created_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'purpose': 'Research-only review queue; permits are not audited sales leads.',
        'policy': ('Only government GIS exact-record queries and published portal search links. '
                   'No inferred redirect, issuer, or prime builder. '
                   'Do not include these records in permit totals.'),
        'independently_verified': False,
        'included_in_sales_leads': False,
        'sources': {},
    }
    for name, method in [('wake', wake_review_rows),
                         ('brunswick', brunswick_review_rows)]:
        try:
            candidates = method()
            data['sources'][name] = {
                'state': 'review_queue_ready',
                'count': len(candidates),
                'candidates': candidates,
                'enabled_for_collection': False,
            }
        except Exception as exc:
            data['sources'][name] = {
                'state': 'source_query_error', 'count': 0, 'candidates': [],
                'error': str(exc)[:200], 'enabled_for_collection': False,
            }
    (OUT / 'chunk13_review_queue.json').write_text(
        json.dumps(data, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: (v['state'], v['count']) for k,v in data['sources'].items()}))


if __name__ == '__main__':
    main()
