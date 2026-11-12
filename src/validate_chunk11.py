"""Chunk 11: agency-role and prime-contractor evidence audit (read-only).

A planning-jurisdiction match is not authoritative proof of permit issuer.
No Wake/Brunswick permits are promoted or linked to named builders here.
"""
from __future__ import annotations

from collections import Counter
import datetime as dt
import json
from urllib.parse import urlsplit

from collect import OUT, issue_date
from validate_chunk10 import (WAKE_URL, BRUNSWICK_URL, get_features,
                              jurisdiction_for_point, BRUNSWICK_NEW_HOME_TYPES)

WAKE_LIMIT = 32
BRUNSWICK_LIMIT = 50
PUBLIC_BRUNSWICK_PORTAL = 'https://bcpp.brunswickcountync.gov/'
PUBLIC_WAKE_PORTAL = 'https://wakecountync-energovpub.tylerhost.net/apps/selfservice'

# Role claims sourced from official municipal pages. Never infer issuer just
# because the point intersects a town's planning jurisdiction.
AGENCY_GUIDANCE = {
    'KNIGHTDALE': {
        'possible_issuer': 'Town of Knightdale',
        'issuer_evidence': 'town_says_it_issues',
        'official_guidance': 'https://www.knightdalenc.gov/development-services/permits-and-inspections/building-permits',
    },
    'ROLESVILLE': {
        'possible_issuer': 'Town of Rolesville',
        'issuer_evidence': 'town_says_it_issues',
        'official_guidance': 'https://www.rolesvillenc.gov/planning/frequently-asked-questions-0',
    },
    'WENDELL': {
        'possible_issuer': 'Town of Wendell / Wake County shared process',
        'issuer_evidence': 'municipal_handling_only',
        'official_guidance': 'https://wildforwendell.com/town/departments-planning-building-permits-8694ea6a09',
    },
    'ZEBULON': {
        'possible_issuer': 'Town of Zebulon / Wake County shared process',
        'issuer_evidence': 'shared_process_requires_record_review',
        'official_guidance': 'https://www.townofzebulon.org/o/planning',
    },
}

def evidence_bucket(planning_name):
    """This is a research tag, not a municipal issuer assignment."""
    if planning_name == 'RALEIGH':
        return 'raleigh_planning_area_hold'
    if planning_name in ('no_matching_polygon', 'missing_or_invalid_point',
                         'ambiguous_multiple_polygons', 'boundary_query_error'):
        return 'unknown_planning_area_hold'
    entry = AGENCY_GUIDANCE.get(planning_name)
    if entry and entry['issuer_evidence'] == 'town_says_it_issues':
        return 'town_issuance_guidance_but_permit_unverified'
    if entry:
        return 'shared_permitting_process_needs_review'
    return 'other_planning_area_needs_review'

def web_host(raw):
    """Hostnames only; never emit raw permit links that may embed identifiers."""
    if not isinstance(raw,str) or len(raw)>4096:
        return ''
    try:
        parsed=urlsplit(raw.strip())
        if parsed.scheme.lower()!='https' or not parsed.hostname:
            return ''
        return parsed.hostname.lower()[:100]
    except ValueError:
        return ''

def wake_roles_pilot(source_request=get_features, boundary_request=get_features):
    args={
        'where': "ISSUE_DATE IS NOT NULL AND PERMIT_STATUS = 'Issued' "
                 "AND WORK_CLASS = 'New One- and Two-Family Dwelling'",
        'outFields': 'PERMIT_NUMBER,ISSUE_DATE,PERMIT_STATUS,WORK_CLASS,LINK',
        'returnGeometry':'true', 'outSR':2264,
        'orderByFields':'ISSUE_DATE DESC', 'resultRecordCount':WAKE_LIMIT,
    }
    rows=source_request(WAKE_URL,args)
    labels=Counter()
    buckets=Counter()
    urls=Counter()
    boundary_errors=0
    for row in rows[:WAKE_LIMIT]:
        try:
            label=jurisdiction_for_point(row.get('geometry'),boundary_request)
        except Exception:
            label='boundary_query_error'
            boundary_errors+=1
        labels[label]+=1
        buckets[evidence_bucket(label)]+=1
        host=web_host(row.get('attributes',{}).get('LINK'))
        if host:
            urls[host]+=1
    return {
        'state':'sampled_no_promotion',
        'sample_size':min(len(rows),WAKE_LIMIT),
        'planning_jurisdiction_counts':dict(sorted(labels.items())),
        'authority_evidence_buckets':dict(sorted(buckets.items())),
        'safe_permit_link_hosts':dict(sorted(urls.items())),
        'boundary_errors':boundary_errors,
        'municipal_guidance':AGENCY_GUIDANCE,
        'official_manual_permit_lookup':PUBLIC_WAKE_PORTAL,
        'all_permits_independently_verified':False,
        'do_not_infer':'No planning area, portal host or shared county inspection proves an individual permit issuer.',
        'enabled_for_collection':False,
    }

def brunswick_prime_builder_pilot(source_request=get_features, today=None):
    today=today or dt.datetime.now(dt.timezone.utc).date()
    types=','.join("'"+x+"'" for x in BRUNSWICK_NEW_HOME_TYPES)
    rows=source_request(BRUNSWICK_URL,{
        'where': "ProjectType = 'Residential' AND PermitStatus = 'Active' "
                 "AND PermitType IN ("+types+") AND DateIssued IS NOT NULL",
        'outFields': ('PermitNumber,ProjectNumber,DateIssued,PermitStatus,'
                      'PermitType,Jurisdiction,SubContractor,ParcelAddress'),
        'returnGeometry':'false','orderByFields':'DateIssued DESC',
        'resultRecordCount':BRUNSWICK_LIMIT,
    })
    subcontractor_nonblank=0
    project_nonblank=0
    permit_nonblank=0
    recent=0
    future=0
    jurisdictions=Counter()
    for item in rows[:BRUNSWICK_LIMIT]:
        a=item.get('attributes',{})
        subcontractor_nonblank+=int(bool(str(a.get('SubContractor') or '').strip()))
        project_nonblank+=int(bool(str(a.get('ProjectNumber') or '').strip()))
        permit_nonblank+=int(bool(str(a.get('PermitNumber') or '').strip()))
        issued=issue_date(a.get('DateIssued'))
        if issued and issued>today:
            future+=1
        if issued and 0<=(today-issued).days<=365:
            recent+=1
        jurisdictions[str(a.get('Jurisdiction') or '(blank)').strip()]+=1
    return {
       'state':'sampled_no_promotion',
       'sample_size':min(len(rows),BRUNSWICK_LIMIT),
       'nonblank_permit_numbers':permit_nonblank,
       'nonblank_project_numbers':project_nonblank,
       'nonblank_subcontractor_fields':subcontractor_nonblank,
       'confirmed_prime_contractors':0,
       'recent_issue_dates':recent, 'future_dates':future,
       'jurisdiction_counts':dict(sorted(jurisdictions.items())),
       'official_manual_permit_lookup':PUBLIC_BRUNSWICK_PORTAL,
       'prime_contractor_mapping':'not_established',
       'warning':'SubContractor is a trade contact field, NOT automatically the GC or builder. Portal detail may require a login and manual review.',
       'enabled_for_collection':False,
    }

def main():
    report={'checked_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'policy':'Read-only permitting role and contractor evidence audit',
            'pilot_sources':{},'independent_permit_verification':False}
    for key,func in [('wake_agency_roles',wake_roles_pilot),
                     ('brunswick_prime_builder',brunswick_prime_builder_pilot)]:
        try:
            report['pilot_sources'][key]=func()
        except Exception as exc:
            report['pilot_sources'][key]={
                'state':'probe_error','error':str(exc)[:220],
                'enabled_for_collection':False}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'chunk11_validation.json').write_text(
        json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v['state'] for k,v in report['pilot_sources'].items()}))

if __name__=='__main__':
    main()
