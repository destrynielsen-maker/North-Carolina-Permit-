"""Read-only Mecklenburg Accela building-permit discovery and contractor pilot.

Uses the official Accela Building Permits FeatureServer layer. This is a
candidate-discovery probe only; no live permit, builder, score, ranking or RSS
output is mutated. An explicit county record and source match are still needed
before promotion into a sales lead.
"""
from __future__ import annotations

from collections import Counter
import datetime as dt
import json
import pathlib
import re
import urllib.parse

from collect import OUT, BAD_STATUS, BLOCKED, NEW_BUILD, issue_date, get

ACCELA_URL = ('https://services3.arcgis.com/hPs600I3X0RTaaaq/arcgis/rest/'
              'services/Accela_Building_Permits/FeatureServer/0')
OLD_MARKET = 'Mecklenburg County / Charlotte'
SAMPLE_LIMIT = 250
CANDIDATE_LIMIT = 12

REQUIRED_FIELDS = frozenset({
    'objectid','casenumber','casestatus','description','permitissued',
    'address','comres','typeofwork','contractorsname','contractorsphone',
    'jobvaluation','ownerbuilder',
})
NEW_CASE_PREFIX = re.compile(r'^(?:RES|COM|BLD|BLDG)[-_](?:NEW|NB)[-_]', re.I)
SAFE_PHONE = re.compile(r'^[+()0-9 .-]{7,25}$')
EXPLICIT_NEW_WORK = re.compile(r'^new\s+(?:residential|commercial|building|construction|single.?family|multi.?family)', re.I)
CONFLICTING_EXISTING = re.compile(
    r'\b(remodel|renovat\w*|tenant improvement|existing building|'
    r'alteration of existing|addition to existing|reroof|re-roof)\b',re.I
)



def clean(a, name, size=220):
    v = next((x for k,x in a.items() if k.lower()==name.lower()), None)
    return str(v).strip()[:size] if v not in (None,'') else ''


def classify(a):
    """Prefer explicit county new-building class without accepting trade-only."""
    number=clean(a,'casenumber')
    typ=clean(a,'typeofwork')
    description=clean(a,'description',500)
    explicit=bool(EXPLICIT_NEW_WORK.search(typ))
    if BLOCKED.search(typ):
        return None
    if explicit:
        if CONFLICTING_EXISTING.search(description):
            return None
    elif BLOCKED.search(description):
        return None
    if not (explicit or NEW_CASE_PREFIX.match(number) or
            NEW_BUILD.search(' '.join((typ,description)))):
        return None
    residential=clean(a,'comres').lower()
    mix=(' '.join((typ,description))).lower()
    if re.search(r'\b(townhome|townhouse|multi.?family|apartments?|duplex|triplex|condo)\b',mix):
        return 'Multifamily'
    if re.search(r'\b(commercial|industrial|warehouse|office|retail|hotel|restaurant)\b',mix) or (
        residential in ('commercial','com','c') or number.upper().startswith('COM-')
    ):
        return 'Commercial'
    if re.search(r'\b(single.?family|sfr|detached|new home|new dwelling|new house)\b',mix):
        return 'Single Family'
    if residential in ('residential','res','r','single family') or number.upper().startswith('RES-'):
        return 'Residential — type review'
    return None


def current_status(a):
    return clean(a,'casestatus',80)


def eligible_candidate(a, today):
    ident = clean(a,'casenumber',110)
    oid = a.get('OBJECTID')
    date = issue_date(a.get('permitissued'))
    if not ident or type(oid) is not int or oid <= 0:
        return None
    if not date or (today-date).days < 0 or (today-date).days > 365:
        return None
    status=current_status(a)
    if BAD_STATUS.search(status):
        return None
    cat=classify(a)
    if not cat:
        return None
    contractor=clean(a,'contractorsname')
    phone=clean(a,'contractorsphone',30)
    if phone and not SAFE_PHONE.fullmatch(phone):
        phone=''
    url=ACCELA_URL + '/query?' + urllib.parse.urlencode({
        'f':'pjson','where':f'OBJECTID = {oid}','outFields':'*',
        'returnGeometry':'false',
    })
    return {
        'id':'mecklenburg_accela:'+ident,
        'case_number': ident,'gis_object_id':oid,
        'issued_date':date.isoformat(),
        'category_screened':cat,
        'status_as_published':status,
        'address_as_published':clean(a,'address',250),
        'contractor_as_published_unverified':contractor,
        'contractor_phone_as_published':phone,
        'owner_builder_flag_as_published':clean(a,'ownerbuilder',40),
        'source_record_url':url,
        'record_verification':'agency_record_review_required',
        'builder_role_verification':'not_independently_verified',
        'included_in_sales_leads':False,
    }


def summarize(metadata, features, previous, today=None):
    today=today or dt.datetime.now(dt.timezone.utc).date()
    if 'error' in metadata:
        raise RuntimeError('Official Accela schema error: '+str(metadata['error'])[:160])
    fields = {str(f.get('name','')).lower() for f in metadata.get('fields',[])}
    missing=REQUIRED_FIELDS-fields
    if missing:
        raise RuntimeError('Accela schema missing required fields: '+','.join(sorted(missing)))
    if not isinstance(features,list):
        raise RuntimeError('Official Accela data returned no features list')
    previous_meck={str(p.get('permit_number') or '').strip().upper()
                   for p in previous if p.get('jurisdiction')==OLD_MARKET}
    statuses=Counter()
    work=Counter()
    source_rows=[]
    eligible=[]
    missing_issued=0
    for feature in features[:SAMPLE_LIMIT]:
        a=feature.get('attributes') or {}
        if not isinstance(a,dict):
            continue
        source_rows.append(a)
        statuses[current_status(a) or '(blank)']+=1
        work[clean(a,'typeofwork') or '(blank)']+=1
        if issue_date(a.get('permitissued')) is None:
            missing_issued+=1
        record=eligible_candidate(a,today)
        if record:
            eligible.append(record)
    match_count=sum(p['case_number'].strip().upper() in previous_meck for p in eligible)
    contractor_count=sum(bool(x['contractor_as_published_unverified']) for x in eligible)
    phone_count=sum(bool(x['contractor_phone_as_published']) for x in eligible)
    seen=set()
    duplicates=0
    for record in eligible:
        if record['case_number'] in seen:
            duplicates+=1
        seen.add(record['case_number'])
    return {
        'state':'sampled_no_promotion',
        'layer':ACCELA_URL,
        'sample_size':len(source_rows),
        'required_schema_fields_confirmed':True,
        'sample_statuses':dict(statuses.most_common(15)),
        'sample_work_types':dict(work.most_common(15)),
        'sample_rows_missing_issue_date':missing_issued,
        'screened_new_building_records':len(eligible),
        'screened_with_contractor_name':contractor_count,
        'screened_with_contractor_phone':phone_count,
        'screened_case_numbers_matching_existing_mecklenburg':match_count,
        'existing_mecklenburg_reference_count':len(previous_meck),
        'sample_repeated_case_number_rows':duplicates,
        'note':('Bounded newest-row sample, not complete source coverage. '
                'Zero exact case-number collisions does not establish zero '
                'project overlap. Contractor identity is official source text '
                'but has not been validated against the individual permit.'),
        'research_records':eligible[:CANDIDATE_LIMIT],
        'enabled_for_collection':False,
        'new_permits_added_to_live':0,
    }


def run():
    OUT.mkdir(parents=True,exist_ok=True)
    report={
        'checked_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'policy':'Read-only current Accela source; no live permit or builder publication',
        'independently_verified':False,
    }
    try:
        metadata=get(ACCELA_URL,{'f':'json'})
        result=get(ACCELA_URL+'/query',{
            'f':'json',
            'where':'permitissued IS NOT NULL',
            'outFields':'OBJECTID,casenumber,casestatus,description,permitissued,address,comres,typeofwork,contractorsname,contractorsphone,jobvaluation,ownerbuilder',
            'returnGeometry':'false',
            'orderByFields':'permitissued DESC,OBJECTID DESC',
            'resultRecordCount':SAMPLE_LIMIT,
        })
        if 'error' in result:
            raise RuntimeError('Accela query error: '+str(result['error'])[:170])
        previous=json.loads((OUT/'permits.json').read_text(encoding='utf-8'))
        report['pilot']=summarize(metadata,result.get('features'),previous)
    except Exception as exc:
        report['pilot']={
            'state':'probe_error','error':str(exc)[:230],
            'enabled_for_collection':False,'new_permits_added_to_live':0,
        }
    (OUT/'mecklenburg_accela_pilot.json').write_text(
        json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report['pilot'].items()
                      if k in ('state','sample_size','screened_new_building_records',
                               'screened_with_contractor_name','screened_with_contractor_phone',
                               'screened_case_numbers_matching_existing_mecklenburg','error')}))


if __name__=='__main__':
    run()
