"""Read-only metadata probes for North Carolina jurisdictions NOT approved for leads.

Does not collect or publish permit records; does not enable any source automatically.
"""
from __future__ import annotations
import datetime as dt
import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'public' / 'data' / 'source_probes.json'
TARGETS = [
    {
        'id': 'wake', 'name': 'Wake County',
        'url': 'https://maps.wake.gov/arcgis/rest/services/Inspections/Building_Permits/MapServer/0',
        'hold_reason': 'Must verify issue date, issuing jurisdiction and overlap with Raleigh',
    },
    {
        'id': 'brunswick', 'name': 'Brunswick County',
        'url': 'https://services1.arcgis.com/W6gamXPYQeLXrdAd/arcgis/rest/services/Permit_Locations/FeatureServer/0',
        'hold_reason': 'DateIssued is a string; verify date formatting and issued vs active records before collecting',
    },
    {
        'id': 'cabarrus', 'name': 'Cabarrus County',
        'url': 'https://location.cabarruscounty.us/arcgisservices/rest/services/Current_Accela_Permits/Plan_Reviews/MapServer/0',
        'hold_reason': 'Current plan-review layer exposes filing/status dates, not established permit issue date',
    },
]


def inspect_metadata(info, target):
    if 'error' in info:
        raise RuntimeError('ArcGIS error: ' + str(info['error'])[:150])
    fields = info.get('fields')
    if not isinstance(fields, list) or not fields:
        raise RuntimeError('ArcGIS layer returned no field metadata')
    dates = [f for f in fields if re.search(r'issu(?:e|ed)|dateissued', f.get('name', ''), re.I)]
    interesting = [f['name'] for f in fields if re.search(
        r'permit|case|juris|issu|status|work|contract|applic|file.*date|sub.?type|descrip',
        f.get('name',''), re.I)]
    return {
        'id': target['id'], 'name': target['name'], 'url': target['url'],
        'state': 'schema_read', 'field_count': len(fields),
        'field_names': [f['name'] for f in fields],
        'issue_date_candidates': [{'name':f['name'], 'type':f.get('type','')}
                                  for f in dates],
        'interesting_fields': interesting[:75],
        'supports_query': 'Query' in str(info.get('capabilities','')) or
                          'Query' in info.get('supportedOperations', []),
        'hold_reason': target['hold_reason'],
        'enabled_for_collection': False,
    }


def fetch_metadata(target):
    url = target['url'] + '?f=json'
    with urllib.request.urlopen(urllib.request.Request(
            url, headers={'User-Agent':'NCConstructionIntelligence/0.4 schema-probe'}),
            timeout=25) as resp:
        return json.load(resp)


def main():
    results = []
    for target in TARGETS:
        try:
            results.append(inspect_metadata(fetch_metadata(target), target))
        except Exception as exc:
            results.append({'id':target['id'], 'name':target['name'],
                            'url':target['url'], 'state':'probe_error',
                            'reason':str(exc)[:240],
                            'hold_reason':target['hold_reason'],
                            'enabled_for_collection':False})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        'checked_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'note':'Metadata-only investigation; no permit records; no source enabled automatically',
        'sources':results,
    },indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'probes':[{k:x[k] for k in ('id','state')}
                                for x in results]}))


if __name__=='__main__':
    main()
