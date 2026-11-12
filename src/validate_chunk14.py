"""Chunk 14: reproducible same-source rechecks of the research queue.

Never claims independent municipal portal verification and never promotes
Wake or Brunswick candidates into production permit or builder feeds.
"""
from __future__ import annotations

from collections import Counter
import datetime as dt
import json

from collect import OUT, issue_date, value
from validate_chunk10 import WAKE_URL, BRUNSWICK_URL, get_features

FIELDS = {
    'wake': ('OBJECTID', 'PERMIT_NUMBER', 'ISSUE_DATE', 'PERMIT_STATUS',
             'WORK_CLASS', 'CONTRACTOR'),
    'brunswick': ('OBJECTID', 'PermitNumber', 'ProjectNumber', 'DateIssued',
                  'PermitStatus', 'PermitType', 'ParcelAddress', 'Jurisdiction'),
}
LAYERS = {'wake': WAKE_URL, 'brunswick': BRUNSWICK_URL}
MAX_PER_SOURCE = 8


def recheck_one(kind, candidate, query=get_features):
    """Compare a cached queue row to the corresponding current ArcGIS object.

    Only returns which fields match/mismatch, never treats a match as an
    independent portal review. Reused county permit IDs are kept separate.
    """
    oid = candidate.get('gis_object_id')
    result = {
        'source': kind,
        'gis_object_id': oid,
        'reference_label': candidate.get('reference_label', ''),
        'same_source_check': True,
        'independently_verified': False,
        'permit_issuer_verified': False,
        'prime_builder_verified': False,
        'included_in_sales_leads': False,
    }
    if kind not in LAYERS or type(oid) is not int or not 1 <= oid <= 2_147_483_647:
        result['state'] = 'invalid_source_or_object_id'
        return result

    try:
        features = query(LAYERS[kind], {
            'where': 'OBJECTID = ' + str(oid),
            'outFields': ','.join(FIELDS[kind]),
            'f': 'json', 'returnGeometry': 'false', 'resultRecordCount': 2,
        })
        if len(features) != 1:
            result['state'] = 'missing_or_multiple_current_features'
            result['matching_feature_count'] = len(features)
            return result
        attrs = features[0].get('attributes', {})
        if value(attrs, 'OBJECTID') != oid:
            result['state'] = 'object_id_mismatch'
            return result

        checks = {
            'permit_number_matches': str(value(attrs, 'PERMIT_NUMBER' if kind == 'wake' else 'PermitNumber') or '').strip() == str(candidate.get('permit_number') or '').strip(),
            'issued_date_matches': issue_date(value(attrs, 'ISSUE_DATE' if kind == 'wake' else 'DateIssued')) is not None and
                issue_date(value(attrs, 'ISSUE_DATE' if kind == 'wake' else 'DateIssued')).isoformat() == candidate.get('issued_date'),
        }
        if kind == 'wake':
            checks['work_class_matches'] = str(value(attrs, 'WORK_CLASS') or '').strip() == str(candidate.get('work_class') or '').strip()
            checks['contractor_matches'] = str(value(attrs, 'CONTRACTOR') or '').strip() == str(candidate.get('contractor_as_listed_unverified') or '').strip()
            checks['status_is_issued'] = str(value(attrs, 'PERMIT_STATUS') or '').strip().lower() == 'issued'
        else:
            checks['project_number_matches'] = str(value(attrs, 'ProjectNumber') or '').strip() == str(candidate.get('project_number') or '').strip()
            checks['permit_type_matches'] = str(value(attrs, 'PermitType') or '').strip() == str(candidate.get('permit_type') or '').strip()
            checks['address_matches'] = str(value(attrs, 'ParcelAddress') or '').strip() == str(candidate.get('address') or '').strip()
            checks['jurisdiction_matches'] = str(value(attrs, 'Jurisdiction') or '').strip() == str(candidate.get('reported_jurisdiction') or '').strip()
            checks['status_is_active'] = str(value(attrs, 'PermitStatus') or '').strip().lower() == 'active'
        result['checks'] = checks
        result['state'] = 'same_source_consistent' if all(checks.values()) else 'same_source_changed'
        result['failed_check_names'] = [key for key, good in checks.items() if not good]
    except Exception as exc:
        result['state'] = 'gis_recheck_error'
        result['error'] = str(exc)[:180]
    return result


def validate_queue(report, query=get_features):
    """Never grant verification or promote source, even on 100% GIS agreement."""
    outcomes=[]
    for kind in ('wake','brunswick'):
        candidates=report.get('sources',{}).get(kind,{}).get('candidates',[])
        for candidate in candidates[:MAX_PER_SOURCE]:
            outcomes.append(recheck_one(kind,candidate,query))
    summary=Counter(r['state'] for r in outcomes)
    return {
        'state': 'source_requery_audit_no_promotion',
        'records_attempted':len(outcomes),
        'same_source_consistent_count':summary.get('same_source_consistent',0),
        'state_counts':dict(sorted(summary.items())),
        'independently_verified_count':0,
        'enabled_for_collection':False,
        'record_checks':outcomes,
    }


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    output={
        'checked_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'scope':'Exact current GIS object-ID rechecks of disabled-county queue only',
        'policy':('A same-source GIS recheck is not independent permit-portal '
                  'verification and never approves a new source.'),
        'independently_verified':False,
        'new_leads_promoted':0,
    }
    try:
        queue=json.loads((OUT/'chunk13_review_queue.json').read_text(encoding='utf-8'))
        output['results']=validate_queue(queue)
    except Exception as exc:
        output['results']={
            'state':'source_requery_error_no_promotion','error':str(exc)[:220],
            'independently_verified_count':0,'enabled_for_collection':False,
        }
    (OUT/'chunk14_validation.json').write_text(
        json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({
        'result':output['results'].get('state'),
        'records_attempted':output['results'].get('records_attempted',0),
        'same_source_consistent_count':output['results'].get('same_source_consistent_count',0),
        'new_leads_promoted':output['new_leads_promoted'],
    }))


if __name__=='__main__':
    main()
