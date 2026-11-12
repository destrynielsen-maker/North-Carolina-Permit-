"""Chunk 8: read-only, bounded official GIS rechecks and disabled-source pilot.

No source is enabled. Never publishes candidate permits from Wake/Brunswick.
Re-querying the same official feed is a consistency check, NOT independent
municipal permit-detail verification.
"""
from __future__ import annotations
from collections import Counter
import datetime as dt
import json
import pathlib
import re
from collect import SOURCES, OUT, get, normalize, issue_date, value

MAX_SAMPLE = 100
TODAY = lambda: dt.datetime.now(dt.timezone.utc).date()
PROBES = {
 'wake': ('https://maps.wake.gov/arcgis/rest/services/Inspections/Building_Permits/MapServer/0',
          'ISSUE_DATE'),
 'brunswick': ('https://services1.arcgis.com/W6gamXPYQeLXrdAd/arcgis/rest/services/Permit_Locations/FeatureServer/0',
               'DateIssued'),
}


def query_page(url, where, fields, limit=MAX_SAMPLE, order=None):
    args = {'f':'json','where':where,'outFields':','.join(fields),
            'returnGeometry':'false','resultRecordCount':min(limit,MAX_SAMPLE)}
    if order:
        args['orderByFields']=order
    reply=get(url+'/query',args)
    if 'error' in reply:
        raise RuntimeError('Official ArcGIS error: '+str(reply['error'])[:160])
    if not isinstance(reply.get('features'),list):
        raise RuntimeError('Official ArcGIS returned no feature list')
    return [x.get('attributes',{}) for x in reply['features']]


def metadata(url):
    info=get(url,{'f':'json'})
    if 'error' in info:
        raise RuntimeError('Official ArcGIS metadata error: '+str(info['error'])[:160])
    if not isinstance(info.get('fields'), list):
        raise RuntimeError('Official ArcGIS metadata missing fields')
    return {str(f['name']).lower():f.get('type') for f in info['fields']}


def date_format(raw):
    if raw in (None,''):
        return 'blank'
    value_=str(raw).strip()
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}',value_):
        return 'YYYY-MM-DD'
    if re.fullmatch(r'\d{1,2}/\d{1,2}/\d{4}',value_):
        return 'MM/DD/YYYY'
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}[T ].*',value_):
        return 'ISO datetime'
    if re.fullmatch(r'\d{8}',value_):
        return 'YYYYMMDD'
    return 'other'


def wake_overlap_sample(raleigh, limit=MAX_SAMPLE):
    url,date=PROBES['wake']
    fields=metadata(url)
    required=('permit_number','issue_date','permit_status','permit_type','work_class')
    absent=[f for f in required if f not in fields]
    if absent:
        raise RuntimeError('Wake missing required fields: '+','.join(absent))
    if fields['issue_date']!='esriFieldTypeDate':
        raise RuntimeError('Wake issue date no longer a native ArcGIS date')
    raw=query_page(url,'ISSUE_DATE IS NOT NULL',
                   ['PERMIT_NUMBER','ISSUE_DATE','PERMIT_STATUS','PERMIT_TYPE','WORK_CLASS'],
                   limit=limit,order='ISSUE_DATE DESC')
    raleigh_nums={str(p.get('permit_number','')).strip().upper()
                  for p in raleigh if p.get('jurisdiction')=='Raleigh'}
    numbers=[str(value(a,'PERMIT_NUMBER') or '').strip().upper() for a in raw]
    number_counts=Counter(n for n in numbers if n)
    blank_permit_numbers=sum(not n for n in numbers)
    duplicate_rows=sum(count-1 for count in number_counts.values() if count>1)
    dates=[issue_date(value(a,'ISSUE_DATE')) for a in raw]
    valid_dates=[d for d in dates if d is not None]
    collisions=sorted(set(number_counts)&raleigh_nums)
    states=Counter(str(value(a,'PERMIT_STATUS') or '(blank)').strip()[:70] for a in raw)
    types=Counter(str(value(a,'WORK_CLASS') or '(blank)').strip()[:70] for a in raw)
    return {
      'state':'sampled_no_promotion','sample_size':len(raw),
      'issue_date_type':fields['issue_date'],
      'distinct_permit_numbers':len(number_counts),
      'blank_permit_numbers':blank_permit_numbers,
      'repeated_permit_number_rows':duplicate_rows,
      'sample_issue_date_min':min(valid_dates).isoformat() if valid_dates else None,
      'sample_issue_date_max':max(valid_dates).isoformat() if valid_dates else None,
      'exact_matches_against_screened_raleigh':len(collisions),
      'raleigh_screened_reference_count':len(raleigh_nums),
      'top_statuses':dict(states.most_common(10)),
      'top_work_classes':dict(types.most_common(10)),
      'limitation':'Sample is limited to the newest returned Wake rows and only screened Raleigh IDs; zero matches does not prove feeds do not overlap. Issuing-jurisdiction detail is still required.',
      'enabled_for_collection':False,
    }


def brunswick_date_sample(limit=MAX_SAMPLE):
    url,_=PROBES['brunswick']
    fields=metadata(url)
    required=('permitnumber','dateissued','permitstatus','permittype','jurisdiction')
    absent=[f for f in required if f not in fields]
    if absent:
        raise RuntimeError('Brunswick missing fields: '+','.join(absent))
    raw=query_page(url,"DateIssued IS NOT NULL",
                   ['PermitNumber','DateIssued','PermitStatus','PermitType','Jurisdiction'],
                   limit=limit,order='DateIssued DESC')
    formats=Counter(date_format(value(a,'DateIssued')) for a in raw)
    dates=[issue_date(value(a,'DateIssued')) for a in raw]
    valid_dates=[d for d in dates if d is not None]
    good=len(valid_dates)
    current=TODAY()
    recent=sum(0 <= (current-d).days <= 365 for d in valid_dates)
    statuses=Counter(str(value(a,'PermitStatus') or '(blank)').strip()[:70] for a in raw)
    jurisdictions=Counter(str(value(a,'Jurisdiction') or '(blank)').strip()[:70] for a in raw)
    permit_types=Counter(str(value(a,'PermitType') or '(blank)').strip()[:70] for a in raw)
    return {
     'state':'sampled_no_promotion','sample_size':len(raw),
     'date_field_type':fields['dateissued'],
     'date_formats':dict(formats),
     'parseable_by_current_issued_date_parser':good,
     'sample_order':'DateIssued DESC (lexical; assumes ISO-like strings)',
     'sample_issued_date_min':min(valid_dates).isoformat() if valid_dates else None,
     'sample_issued_date_max':max(valid_dates).isoformat() if valid_dates else None,
     'sample_issued_in_last_365_days':recent,
     'top_permit_types':dict(permit_types.most_common(10)),
     'top_statuses':dict(statuses.most_common(10)),
     'top_jurisdictions':dict(jurisdictions.most_common(10)),
     'limitation':'Issue-date strings, permit status and government scope require record verification before publishing; no prime contractor is inferred from SubContractor.',
     'enabled_for_collection':False,
    }


def recheck_qa_records(queue, per_market=2):
    source_by_name={s['name']:s for s in SOURCES if s.get('enabled')}
    seen=Counter()
    output=[]
    for p in queue:
        name=p.get('jurisdiction')
        if name not in source_by_name or seen[name]>=per_market:
            continue
        seen[name]+=1
        source=source_by_name[name]
        ident=str(p.get('permit_number') or '')
        result={'id':p['id'],'jurisdiction':name,'permit_number':ident,
                'review_kind':'official_source_requery_not_independent_portal',
                'independently_verified':False}
        try:
            fields=metadata(source['url'])
            key=source['number']
            if key.lower() not in fields:
                raise RuntimeError('Permit identifier field is absent from current schema')
            fieldtype=fields[key.lower()] or ''
            if fieldtype in ('esriFieldTypeInteger','esriFieldTypeSmallInteger','esriFieldTypeOID','esriFieldTypeDouble'):
                if not re.fullmatch(r'\d+',ident):
                    raise RuntimeError('Permit identifier not numeric for source field type')
                clause=key+' = '+ident
            else:
                clause=key+" = '"+ident.replace("'","''")+"'"
            rows=query_page(source['url'],clause,['*'],limit=3)
            actual=[a for a in rows if str(value(a,key) or '').strip()==ident]
            if len(actual)!=1:
                result['state']='not_single_record_match'
                result['matches']=len(actual)
            else:
                current=normalize(actual[0],source,TODAY())
                if current is None:
                    result['state']='no_longer_qualifies'
                else:
                    checks={
                     'date_matches':current['issued_date']==p.get('issued_date'),
                     'category_matches':current['category']==p.get('category'),
                     'address_matches':current['address'].strip()==str(p.get('address') or '').strip(),
                     'contractor_matches':current['contractor'].strip()==str(p.get('contractor') or '').strip(),
                     'status_matches':current['status'].strip()==str(p.get('status') or '').strip(),
                    }
                    result['checks']=checks
                    result['state']='source_requery_consistent' if all(checks.values()) else 'source_requery_changed'
        except Exception as exc:
            result['state']='query_error'
            result['error']=str(exc)[:180]
        output.append(result)
    return output


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    try:
        permits=json.loads((OUT/'permits.json').read_text())
    except (ValueError,FileNotFoundError):
        permits=[]
    try:
        queue=json.loads((OUT/'qa_samples.json').read_text()).get('records',[])
    except (ValueError,FileNotFoundError):
        queue=[]
    report={'checked_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'policy':'Read-only sample and consistency checks. No disabled-source records enter the published leads.',
            'independently_verified':False,'pilot_sources':{},'source_record_rechecks':[]}
    for key,fn in [('wake',lambda:wake_overlap_sample(permits)),
                   ('brunswick',brunswick_date_sample)]:
        try:
            report['pilot_sources'][key]=fn()
        except Exception as exc:
            report['pilot_sources'][key]={'state':'probe_error','error':str(exc)[:200],
                                         'enabled_for_collection':False}
    report['source_record_rechecks']=recheck_qa_records(queue,per_market=2)
    (OUT/'chunk8_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'pilot_states':{k:v['state'] for k,v in report['pilot_sources'].items()},
                      'rechecks':Counter(x['state'] for x in report['source_record_rechecks'])}))


if __name__=='__main__':
    main()
