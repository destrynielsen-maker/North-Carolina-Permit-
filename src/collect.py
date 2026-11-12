"""North Carolina public permit collector — evidence-first, conservative discovery.

A service's schema may be confirmed from its published REST layer while its live
queries still need validation. Do not equate a screened permit with a certified lead.
"""
from __future__ import annotations

import datetime as dt
from collections import Counter
import json
import pathlib
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'public' / 'data'
MAX_PAGES = 40
DAYS_TO_KEEP = 365

SOURCES = [
    {
        'id': 'raleigh', 'name': 'Raleigh', 'enabled': True,
        'url': 'https://services.arcgis.com/v400IkDOw1ad7Yad/arcgis/rest/services/Building_Permits_Issued_Past_180_Days/FeatureServer/0',
        'date': 'issueddate', 'number': 'permitnum', 'status': 'statuscurrent',
        'type_fields': ['permittypemapped', 'permitclassmapped', 'permitclass', 'permittype', 'censuslanduse', 'occupancyclass'],
        'work_fields': ['workclassmapped', 'workclass'],
        'description_fields': ['proposedworkdescription', 'description', 'perm_comments', 'proposeduse'],
        'contractor': 'contractorcompanyname', 'valuation': 'estprojectcost',
        'address_fields': ['originaladdress1', 'originalcity', 'originalstate'],
        'units': 'housingunitstotal', 'days': 180,
        'validation': 'published field schema confirmed; record-level verification pending',
    },
    {
        'id': 'new_hanover', 'name': 'New Hanover County', 'enabled': True,
        'url': 'https://gisport.nhcgov.com/server/rest/services/Thematic/BuildingPermits/FeatureServer/0',
        'date': 'ISSUE_DATE', 'number': 'PERMIT_NUMBER', 'status': 'PERMIT_STATUS',
        'type_fields': ['PERMIT_TYPE'], 'work_fields': ['WORK_CLASS'],
        'description_fields': ['DESCRIPTION', 'PROJECT'], 'contractor': 'GENERAL_CONTRACTOR',
        'valuation': 'VALUATION', 'address_fields': ['NUMBER', 'STREET', 'TYPE', 'CITY', 'STATE'],
        'units': None, 'days': 365,
        'validation': 'published field schema confirmed; record-level verification pending; monthly refresh',
    },
    {
        'id': 'mecklenburg', 'name': 'Mecklenburg County / Charlotte', 'enabled': False, 'snapshot_only': True,
        'snapshot_as_of_utc': '2026-11-12T22:34:56.402783+00:00',
        'url': 'https://meckgis.mecklenburgcountync.gov/server/rest/services/BuildingPermits/FeatureServer/0',
        'date': 'issuedate', 'number': 'permitnum', 'status': 'permitstat',
        'type_fields': ['permittype', 'typeofbldg', 'occupancy', 'usdcdesc'],
        'work_fields': ['worktype', 'constrtype'],
        'description_fields': ['permitdesc', 'projdesc', 'workdesc'],
        'contractor': None, 'valuation': 'bldgcost', 'address_fields': ['projadd'],
        'units': 'numunits', 'days': 365,
        'reason': 'Historic downloaded/published GIS snapshot only; commercial continuous API use is prohibited by Mecklenburg County reuse policy. Use approved open-data downloads and host our own copy.',
        'validation': 'historic snapshot from the last pre-pause government GIS scan; not refreshed; builder not provided',
    },
    {
        'id': 'greensboro', 'name': 'Greensboro', 'enabled': True,
        'url': 'https://gis.greensboro-nc.gov/arcgis/rest/services/EngineeringInspections/BuildingPermits_MS/MapServer/6',
        'date': 'IssuedDate', 'number': 'PermitNum', 'status': 'StatusCurrent',
        'type_fields': ['ApplicationType', 'OccupancyDesc'],
        'work_fields': ['ApplicationType'],
        'description_fields': ['Description'], 'contractor': 'Contractor',
        'valuation': 'TotalCost', 'address_fields': ['FullAddress', 'City', 'State'],
        'units': 'NumUnits', 'days': 365,
        'validation': 'official issued-date/contractor schema confirmed; live records and screening require review',
    },
    {
        'id': 'wake', 'name': 'Wake County', 'enabled': False,
        'url': 'https://maps.wake.gov/arcgis/rest/services/Inspections/Building_Permits/MapServer/0',
        'reason': 'ISSUE_DATE, PERMIT_NUMBER, PERMIT_STATUS, WORK_CLASS and CONTRACTOR verified in schema; issuer jurisdiction and Raleigh overlap require testing',
    },
    {
        'id': 'durham', 'name': 'Durham', 'enabled': False,
        'url': 'https://webgis2.durhamnc.gov/server/rest/services/CartographicServices/Inspections/MapServer/20',
        'reason': 'active-permit layer has no issue-date field; source not suitable for issued-date leads',
    },
]

BLOCKED = re.compile(
    r'\b(remodel\w*|renovat\w*|addition\w*|alteration\w*|repair\w*|replacement\w*|'
    r'reroof\w*|re-roof\w*|roofing|solar|electrical|plumbing|mechanical|hvac|'
    r'demolition|demolish|signage|sign permit|deck|pool|accessory|adu|'
    r'tenant improvement|tenant finish|tenant upfit|upfit|interior finish|'
    r'change of use|relocation|existing building|trade permit|fire alarm|'
    r'gas piping|changeout|change-out|cell tower)\b', re.I
)
NEW_BUILD = re.compile(
    r'\b(new construction|new building|new residential|new single[ -]?family|'
    r'new dwelling|new home|new residence|new sfr|new commercial|new bldg|'
    r'new multi[ -]?family|new apartment|new townhouse|new townhome|'
    r'ground.?up|construct(?:ion|ing)? (?:a |an )?new|new house|new structure)\b', re.I
)
MULTI = re.compile(r'\b(multi[ -]?family|apartment\w*|duplex|triplex|quadplex|fourplex|townhome\w*|townhouse\w*|condominium\w*)\b', re.I)
COMMERCIAL = re.compile(r'\b(commercial|industrial|warehouse|office|retail|restaurant|hotel|school|mixed[ -]?use|business|factory)\b', re.I)
SINGLE = re.compile(r'\b(single[ -]?family|sfr|residen\w*|dwelling|house|home|detached)\b', re.I)
BAD_STATUS = re.compile(r'\b(void\w*|cancel\w*|withdraw\w*|denied|expired|revoked|pending|applied|not issued|under review|in review|incomplete|on hold|stop work(?: order)?)\b', re.I)


def value(a, key):
    if not key:
        return None
    if key in a:
        return a[key]
    return next((v for k, v in a.items() if k.lower() == key.lower()), None)


def parts(a, keys):
    return ' '.join(str(value(a, k)).strip() for k in keys if value(a, k) not in (None, ''))


def issue_date(v):
    if isinstance(v, (int, float)):
        try:
            return dt.datetime.fromtimestamp(v / 1000 if abs(v) > 1e11 else v, dt.timezone.utc).date()
        except (ValueError, OverflowError, OSError):
            return None
    if not v:
        return None
    s = str(v).strip()
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%dT%H:%M:%S'):
        try:
            if fmt == '%Y-%m-%d':
                return dt.date.fromisoformat(s[:10])
            if fmt == '%Y-%m-%dT%H:%M:%S':
                return dt.datetime.strptime(s[:19], fmt).date()
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def category(a, source):
    typ = parts(a, source['type_fields'])
    work = parts(a, source['work_fields'])
    desc = parts(a, source['description_fields'])
    all_text = ' '.join((typ, work, desc))
    if BLOCKED.search(' '.join((typ, work))) or BLOCKED.search(desc):
        return None
    if not (NEW_BUILD.search(all_text) or re.search(r'\bnew\b', work, re.I)):
        return None
    if MULTI.search(all_text):
        return 'Multifamily'
    if COMMERCIAL.search(all_text):
        return 'Commercial'
    if SINGLE.search(all_text):
        return 'Single Family'
    return None


def builder_key(name):
    """Conservative contractor key: casing, punctuation and license decorations only.

    Keep legal-entity and trading-as details so different companies are not
    silently merged. Do not use fuzzy matching or drop GROUP/CORP words.
    """
    name = str(name or '').strip().upper()
    name = re.sub(r'\s*\(LIC\s*#?\s*\d+\)|\s*\(B\)', ' ', name)
    return re.sub(r'\s+', ' ', re.sub(r'[^A-Z0-9]+', ' ', name)).strip()


def cross_source_number_collisions(permits):
    """Audit only; never merge records automatically from different agencies.

    Same permit number in two feeds does not prove the same issuance. Return
    aggregated pair counts and no permit addresses or owner details.
    """
    from itertools import combinations
    by_number = {}
    for p in permits:
        number = str(p.get('permit_number') or '').strip().upper()
        if number:
            by_number.setdefault(number, []).append(p)
    tally = Counter()
    for records in by_number.values():
        for a, b in combinations(records, 2):
            names = sorted((str(a.get('jurisdiction', '')), str(b.get('jurisdiction', ''))))
            if not names[0] or names[0] == names[1]:
                continue
            key = ' | '.join(names)
            tally[(key, 'same_number')] += 1
            if a.get('issued_date') == b.get('issued_date'):
                tally[(key, 'same_number_and_issued_date')] += 1
    summary = {}
    for (pair, typ), count in tally.items():
        summary.setdefault(pair, {})[typ] = count
    return [{'jurisdictions': pair, 'same_number': v.get('same_number', 0),
             'same_number_and_issued_date': v.get('same_number_and_issued_date', 0)}
            for pair, v in sorted(summary.items())]


def build_builder_rankings(permits, today=None):
    """Rank screened permit counts, not unique construction projects or verified leads."""
    today = today or dt.datetime.now(dt.timezone.utc).date()
    groups = {}
    for p in permits:
        name = str(p.get('contractor') or '').strip()
        key = builder_key(name)
        issued = issue_date(p.get('issued_date'))
        if not key or not issued or not (0 <= (today - issued).days <= DAYS_TO_KEEP):
            continue
        b = groups.setdefault(key, {'builder': name, 'aliases': set(),
                                    'permit_count': 0, 'valuation': 0.0,
                                    'jurisdictions': set(), 'categories': Counter(),
                                    'last_issued_date': '',
                                    'issued_last_30_days': 0,
                                    'issued_last_90_days': 0})
        b['aliases'].add(name)
        b['permit_count'] += 1
        b['valuation'] += float(p.get('valuation') or 0)
        b['jurisdictions'].add(p.get('jurisdiction', ''))
        b['categories'][p.get('category', 'Unclassified')] += 1
        b['last_issued_date'] = max(b['last_issued_date'], issued.isoformat())
        age = (today - issued).days
        b['issued_last_30_days'] += int(age <= 30)
        b['issued_last_90_days'] += int(age <= 90)
    rows = []
    for b in groups.values():
        aliases = sorted(b['aliases'], key=lambda a: (a.casefold(), a))
        rows.append({**b, 'builder': aliases[0], 'aliases': aliases,
                     'jurisdictions': sorted(b['jurisdictions']),
                     'categories': dict(sorted(b['categories'].items())),
                     'valuation': round(b['valuation'], 2),
                     'average_valuation': round(b['valuation'] / b['permit_count'], 2)})
    rows.sort(key=lambda b: (-b['issued_last_90_days'], -b['issued_last_30_days'],
                             -b['permit_count'], b['builder'].casefold()))
    return [dict(b, rank=i+1) for i,b in enumerate(rows)]


def manual_qa_samples(permits, sources, failed=(), per_source=6):
    """Build a deterministic permit-level manual-review queue (never auto-verified)."""
    enabled = {s['name']: s for s in sources if s['enabled']}
    grouped = {}
    for p in permits:
        if p.get('jurisdiction') in enabled:
            grouped.setdefault(p['jurisdiction'], []).append(p)
    queue = []
    for name in sorted(grouped):
        source = enabled[name]
        ranked = sorted(grouped[name],
                        key=lambda p:(p['issued_date'],p.get('score',0),p['permit_number']),
                        reverse=True)
        picked, seen = [], set()
        for kind in ('Single Family', 'Multifamily', 'Commercial'):
            candidate = next((p for p in ranked if p['category']==kind and p['id'] not in seen), None)
            if candidate:
                picked.append(candidate)
                seen.add(candidate['id'])
        for p in ranked:
            if len(picked)>=per_source:
                break
            if p['id'] not in seen:
                picked.append(p)
                seen.add(p['id'])
        for p in picked[:per_source]:
            permit_number = str(p['permit_number']).replace("'", "''")
            where = f"{source['number']} = '{permit_number}'"
            query_url = (source['url'] + '/query?' + urllib.parse.urlencode({
                'f':'json', 'where':where, 'outFields':'*', 'returnGeometry':'false'
            }))
            queue.append({
                'id':p['id'], 'jurisdiction':name,
                'permit_number':p['permit_number'], 'issued_date':p['issued_date'],
                'category':p['category'], 'address':p.get('address',''),
                'contractor':p.get('contractor',''), 'valuation':p.get('valuation',0),
                'status':p.get('status',''), 'source_url':source['url'],
                'source_query_url':query_url, 'permit_detail_url': public_permit_detail_url(source, p['permit_number']),
                'collection_state':'retained_from_previous_run' if name in failed else 'current_scan',
                'verification_status':'manual_review_required',
                'verification_checklist':['confirm permit number in issuing-agency record',
                    'confirm original issue date and current status',
                    'confirm ground-up classification and building use',
                    'confirm site address, contractor and valuation'],
            })
    return queue


def public_permit_detail_url(source, permit_number):
    """Link to an official permit page only for proven permit-detail URL patterns.

    Preserve the GIS source URL for provenance and as a fallback for unsupported
    jurisdictions. Greensboro's permit number must be numeric.
    """
    if source.get('id') != 'greensboro':
        return ''
    number = str(permit_number or '').strip()
    if not re.fullmatch(r'[0-9]{6,12}', number):
        return ''
    return ('https://bisched.greensboro-nc.gov/frmBuildingPermitView.aspx?'
            + urllib.parse.urlencode({'bldgPermitNumber': number}))


def public_record_query_url(source, a):
    """Link a unique GIS feature by layer OBJECTID; keep source_url separately."""
    object_id = value(a, 'OBJECTID')
    if type(object_id) is int and 0 < object_id <= 2147483647:
        return source['url'] + '/query?' + urllib.parse.urlencode({
            'f': 'pjson', 'where': 'OBJECTID = ' + str(object_id),
            'outFields': '*', 'returnGeometry': 'false'})
    return ''


def optional_number(v):
    """Only display genuine finite positive quantitative source values."""
    try:
        number = float(v)
        return number if 0 < number < 1e12 and number == number else None
    except (ValueError, TypeError, OverflowError):
        return None


def source_contact(a, field):
    """Public business-contact field, scoped to explicit agency metadata."""
    raw = value(a, field)
    return str(raw).strip()[:200] if raw not in (None, '') else ''


def normalize(a, source, today=None):
    today = today or dt.datetime.now(dt.timezone.utc).date()
    number = str(value(a, source['number']) or '').strip()
    issued = issue_date(value(a, source['date']))
    if not number or issued is None or not (0 <= (today - issued).days <= DAYS_TO_KEEP):
        return None
    status = str(value(a, source['status']) or '')
    if BAD_STATUS.search(status):
        return None
    kind = category(a, source)
    if kind is None:
        return None
    raw = value(a, source['valuation'])
    try:
        amount = max(0.0, float(str(raw).replace(',', '').replace('$', '')))
    except (ValueError, TypeError):
        amount = 0.0
    contractor = str(value(a, source['contractor']) or '').strip()
    description = parts(a, source['description_fields'])[:500]
    address = parts(a, source['address_fields'])
    age = (today - issued).days
    score = min(100, 35 + (20 if age <= 30 else 10 if age <= 90 else 0)
                + (15 if contractor else 0)
                + (15 if amount >= 500000 else 5 if amount >= 100000 else 0)
                + (10 if kind == 'Multifamily' else 5 if kind == 'Commercial' else 0))
    is_raleigh = source.get('id') == 'raleigh'
    is_new_hanover = source.get('id') == 'new_hanover'
    is_mecklenburg = source.get('id') == 'mecklenburg'
    return {
        'id': source['id'] + ':' + number, 'jurisdiction': source['name'],
        'permit_number': number, 'issued_date': issued.isoformat(), 'category': kind,
        'address': address, 'contractor': contractor, 'description': description,
        'status': status.strip(), 'valuation': amount, 'score': score, 'source_url': source['url'],
        'verification': 'screened government record — not independently verified',
        'permit_detail_url': public_permit_detail_url(source, number),
        'source_record_url': public_record_query_url(source, a),
        'project_name': (
            source_contact(a, 'projectname') if is_raleigh
            else source_contact(a, 'PROJECT') if is_new_hanover
            else source_contact(a, 'projname') if is_mecklenburg
            else ''
        ),
        'project_contact': source_contact(a, 'PROJECT_CONTACT') if is_new_hanover else '',
        'project_number': source_contact(a, 'projnum') if is_mecklenburg else '',
        'subdivision': source_contact(a, 'subdiv') if is_mecklenburg else '',
        'parcel_number': (
            source_contact(a, 'parcelnum') if is_mecklenburg
            else source_contact(a, 'PID') if is_new_hanover
            else ''
        ),
        'tax_jurisdiction': source_contact(a, 'taxjuris') if is_mecklenburg else '',
        'project_phase': source_contact(a, 'projphase') if is_mecklenburg else '',
        'work_class': parts(a, source['work_fields'])[:200],
        'permit_type': parts(a, source['type_fields'])[:200],
        'square_feet': (
            optional_number(value(a, 'totalsqft')) if is_raleigh
            else optional_number(value(a, 'SQUARE_FEET')) if is_new_hanover
            else optional_number(value(a, 'totalsqft')) if is_mecklenburg
            else None
        ),
        'heated_square_feet': optional_number(value(a, 'heatsqft')) if is_mecklenburg else None,
        'unheated_square_feet': optional_number(value(a, 'unheatsqft')) if is_mecklenburg else None,
        'stories': optional_number(value(a, 'numberstories')) if is_raleigh else None,
        'housing_units': optional_number(value(a, source.get('units'))) if source.get('units') else None,
        'contractor_phone': source_contact(a, 'contractorphone') if is_raleigh else '',
        'contractor_email': source_contact(a, 'contractoremail') if is_raleigh else '',
        'contractor_license': source_contact(a, 'contractorlicnum') if is_raleigh else '',
        'contractor_dba': source_contact(a, 'contractordba') if is_raleigh else '',
        'contractor_address': parts(a, [
            'contractoraddress1', 'contractorcity', 'contractorstate', 'contractorzip'
        ])[:260] if is_raleigh else '',
    }


def get(url, params=None):
    if params:
        url += '?' + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={'User-Agent': 'NCConstructionIntelligence/0.2 source-audit'})
    with urllib.request.urlopen(request, timeout=35) as response:
        return json.load(response)


def check_schema(info, source):
    if 'error' in info:
        raise RuntimeError('ArcGIS service error: ' + str(info['error'])[:180])
    fields = {x['name'].lower() for x in info.get('fields', [])}
    required = [source['number'], source['date'], source['status'], source['valuation']]
    required += source['type_fields'][:1] + source['work_fields'][:1]
    missing = [x for x in required if x and x.lower() not in fields]
    if missing:
        raise RuntimeError('Service schema changed / missing fields: ' + ', '.join(missing))
    oid = info.get('objectIdField') or next((f['name'] for f in info['fields'] if f.get('type') == 'esriFieldTypeOID'), None)
    if not oid:
        raise RuntimeError('No object ID field')
    if 'Query' not in info.get('capabilities', ''):
        raise RuntimeError('Service does not advertise Query capability')
    return oid


def rejection_reason(attributes, source, today):
    """Aggregate diagnostics only; never publish raw rejected permit details."""
    if not str(value(attributes, source['number']) or '').strip():
        return 'missing_permit_number'
    issued = issue_date(value(attributes, source['date']))
    if issued is None:
        return 'missing_issued_date'
    if not 0 <= (today - issued).days <= DAYS_TO_KEEP:
        return 'outside_date_window'
    if BAD_STATUS.search(str(value(attributes, source['status']) or '')):
        return 'blocked_status'
    typ = parts(attributes, source['type_fields'])
    work = parts(attributes, source['work_fields'])
    description = parts(attributes, source['description_fields'])
    if BLOCKED.search(' '.join((typ, work))) or BLOCKED.search(description):
        return 'excluded_work_or_trade'
    if not (NEW_BUILD.search(' '.join((typ, work, description))) or re.search(r'\bnew\b', work, re.I)):
        return 'no_explicit_new_construction'
    return 'missing_building_category'


def collect(source, today=None, diagnostics=None):
    """Scan by issue date rather than object ID, with a fixed count and cutoff.

    Pagination cap errors rather than falsely claiming a complete scan.
    """
    today = today or dt.datetime.now(dt.timezone.utc).date()
    info = get(source['url'], {'f': 'json'})
    oid = check_schema(info, source)
    count = min(2000, max(1, int(info.get('maxRecordCount') or 1000)))
    lookback = min(source['days'], DAYS_TO_KEEP)
    cutoff = today - dt.timedelta(days=lookback)
    where = f"{source['date']} IS NOT NULL AND {source['date']} >= DATE '{cutoff.isoformat()}'"
    rows, scanned, offset = [], 0, 0
    work_types, permit_types, statuses, rejected = Counter(), Counter(), Counter(), Counter()

    def finish():
        if diagnostics is not None:
            diagnostics.update({
                'scanned': scanned, 'qualified': len(rows),
                'work_types': dict(work_types.most_common(15)),
                'permit_types': dict(permit_types.most_common(15)),
                'statuses': dict(statuses.most_common(15)),
                'rejection_reasons': dict(rejected.most_common()),
            })
        return rows, scanned
    for _ in range(MAX_PAGES):
        page = get(source['url'] + '/query', {
            'f': 'json', 'where': where, 'outFields': '*', 'returnGeometry': 'false',
            'orderByFields': f"{source['date']} DESC,{oid} DESC", 'resultOffset': offset,
            'resultRecordCount': count,
        })
        if 'error' in page:
            raise RuntimeError('ArcGIS query error: ' + str(page['error'])[:180])
        if 'features' not in page:
            raise RuntimeError('No features key in query response')
        features = page['features']
        scanned += len(features)
        for feature in features:
            attributes = feature.get('attributes', {})
            record = normalize(attributes, source, today)
            if diagnostics is not None:
                work_types[parts(attributes, source['work_fields'])[:100] or '(blank)'] += 1
                permit_types[parts(attributes, source['type_fields'])[:100] or '(blank)'] += 1
                statuses[str(value(attributes, source['status']) or '(blank)')[:80]] += 1
                if not record:
                    rejected[rejection_reason(attributes, source, today)] += 1
            if record:
                rows.append(record)
        offset += len(features)
        if len(features) < count and not page.get('exceededTransferLimit'):
            return finish()
        if len(features) == 0:
            raise RuntimeError('Pagination was truncated without progress')
    raise RuntimeError(f'Pagination cap {MAX_PAGES} reached; incomplete scan ({scanned} records)')


def rss(title, records, path):
    root = ET.Element('rss', version='2.0')
    channel = ET.SubElement(root, 'channel')
    ET.SubElement(channel, 'title').text = title
    ET.SubElement(channel, 'description').text = 'Screened public permits, not verified sales leads; confirm with issuing agency'
    ET.SubElement(channel, 'link').text = 'https://destrynielsen-maker.github.io/North-Carolina-Permit-/'
    for p in sorted(records, key=lambda x: x['issued_date'], reverse=True)[:100]:
        item = ET.SubElement(channel, 'item')
        ET.SubElement(item, 'title').text = f"{p['category']} · {p['jurisdiction']} · {p['permit_number']}"
        ET.SubElement(item, 'description').text = f"{p['address']} | {p['contractor']} | $" + f"{p['valuation']:,.0f} | score {p['score']}"
        ET.SubElement(item, 'guid', isPermaLink='false').text = p['id']
        ET.SubElement(item, 'link').text = p.get('permit_detail_url') or p['source_url']
    (ROOT / 'public' / path).write_bytes(ET.tostring(root, encoding='utf-8', xml_declaration=True))


def sales_field_coverage(permits):
    """Aggregate contact availability; no personal data in the summary."""
    buckets = {}
    keys = ('contractor', 'contractor_phone', 'contractor_email',
            'contractor_license', 'project_name', 'project_number',
            'project_contact', 'subdivision', 'parcel_number',
            'project_phase', 'square_feet', 'heated_square_feet',
            'unheated_square_feet', 'housing_units',
            'source_record_url', 'permit_detail_url')
    for p in permits:
        market = p.get('jurisdiction') or '(unknown)'
        row = buckets.setdefault(market, {'jurisdiction': market, 'screened_permits': 0,
                                           **{k + '_available': 0 for k in keys},
                                           'phone_or_email_available': 0})
        row['screened_permits'] += 1
        for k in keys:
            row[k + '_available'] += int(bool(str(p.get(k) or '').strip()))
        row['phone_or_email_available'] += int(bool(
            str(p.get('contractor_phone') or '').strip()
            or str(p.get('contractor_email') or '').strip()))
    return sorted(buckets.values(), key=lambda r:r['jurisdiction'].casefold())


def preserve_historic_mecklenburg(records, as_of):
    """Freeze already published Mecklenburg candidates, not a new service query.

    Keep the sales permit pages accessible, while forbidding these records
    from current feeds and rankings. The original government fields remain
    as collected; every record gets explicit data provenance.
    """
    preserved=[]
    for record in records:
        if not isinstance(record,dict):
            continue
        if record.get('jurisdiction') != 'Mecklenburg County / Charlotte':
            continue
        if not str(record.get('id') or '').startswith('mecklenburg:'):
            continue
        item=dict(record)
        item['collection_mode']='historic_snapshot'
        item['snapshot_as_of_utc']=as_of
        item['verification']='Historic Mecklenburg government GIS snapshot — not refreshed; verify current permit status with issuer'
        preserved.append(item)
    preserved.sort(key=lambda x:(str(x.get('issued_date') or ''),str(x.get('permit_number') or '')),reverse=True)
    return preserved


def read_json_array(path):
    try:
        raw=json.loads(path.read_text(encoding='utf-8'))
        return raw if isinstance(raw,list) else []
    except (OSError,ValueError,TypeError):
        return []


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    permits, health, diagnostics_by_source = [], [], []
    old = OUT / 'permits.json'
    archived_file=OUT / 'mecklenburg_snapshot.json'
    # Once frozen, the standalone local archive is authoritative. Never
    # rebuild it from new GIS calls or silently replace its contents.
    meck_source=next(x for x in SOURCES if x.get('id')=='mecklenburg')
    if archived_file.exists():
        archived=preserve_historic_mecklenburg(
            read_json_array(archived_file),meck_source['snapshot_as_of_utc'])
    else:
        archived=preserve_historic_mecklenburg(
            read_json_array(old),meck_source['snapshot_as_of_utc'])
        if archived:
            archived_file.write_text(json.dumps(archived,indent=2)+'\\n',encoding='utf-8')
    for source in SOURCES:
        if source.get('snapshot_only'):
            permits.extend(archived)
            health.append({
                'name':source['name'],'source_url':source['url'],
                'state':'historic snapshot - live API polling disabled',
                'detail':source['reason'],
                'scanned':0,'qualified':0,'archived_count':len(archived),
                'snapshot_as_of_utc':source['snapshot_as_of_utc'],
                'collection_mode':'historic_snapshot',
            })
            continue
        if not source['enabled']:
            health.append({'name': source['name'], 'source_url': source['url'],
                           'state': 'paused - not qualified for issued-lead collection',
                           'detail': source['reason'], 'scanned': 0, 'qualified': 0})
            continue
        try:
            source_diag = {}
            records, scanned = collect(source, diagnostics=source_diag)
            diagnostics_by_source.append({'source': source['name'], **source_diag})
            permits.extend(records)
            health.append({'name': source['name'], 'source_url': source['url'],
                           'state': 'collected - sample verification pending',
                           'detail': source['validation'], 'scanned': scanned, 'qualified': len(records)})
        except Exception as exc:
            health.append({'name': source['name'], 'source_url': source['url'],
                           'state': 'error - requires investigation', 'detail': str(exc)[:250],
                           'scanned': 0, 'qualified': 0})
    failed = {h['name'] for h in health if h['state'].startswith('error')}
    if failed and old.exists():
        try:
            for p in json.loads(old.read_text(encoding='utf-8')):
                if p.get('jurisdiction') in failed and issue_date(p.get('issued_date')):
                    if 0 <= (dt.datetime.now(dt.timezone.utc).date() - issue_date(p['issued_date'])).days <= DAYS_TO_KEEP:
                        permits.append(p)
        except (ValueError, KeyError, TypeError):
            pass
    permits = sorted({p['id']: p for p in permits}.values(),
                     key=lambda x: (x['issued_date'], x['score']), reverse=True)
    current_permits=[p for p in permits if p.get('collection_mode')!='historic_snapshot']
    (OUT / 'permits.json').write_text(json.dumps(permits, indent=2) + '\n', encoding='utf-8')
    (OUT / 'sales_field_coverage.json').write_text(json.dumps({
        'note': 'Source-published business contact availability among screened records; not independently verified leads',
        'as_of_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'sources': sales_field_coverage(permits),
    }, indent=2) + '\n', encoding='utf-8')
    (OUT / 'builder_rankings.json').write_text(json.dumps({
        'method': 'Ranked by issued permit candidates in last 90 days, then 30 days, then all screened permits; never unique projects',
        'as_of_utc_date': dt.datetime.now(dt.timezone.utc).date().isoformat(),
        'builders': build_builder_rankings(current_permits),
    }, indent=2) + '\n', encoding='utf-8')
    (OUT / 'qa_samples.json').write_text(json.dumps({
        'method': 'Deterministic category-first and newest-date samples; manually verify with issuing agency',
        'independently_verified': False,
        'records': manual_qa_samples(permits, SOURCES, failed),
    }, indent=2) + '\n', encoding='utf-8')
    collisions = cross_source_number_collisions(permits)
    (OUT / 'overlap_audit.json').write_text(json.dumps({
        'policy': 'Audit only. No cross-agency records removed based solely on addresses or permit numbers.',
        'wake_enabled': any(src['id'] == 'wake' and src['enabled'] for src in SOURCES),
        'cross_source_number_collision_pairs': collisions,
    }, indent=2) + '\n', encoding='utf-8')
    (OUT / 'diagnostics.json').write_text(json.dumps({
        'note': 'Aggregated counts from latest successful scans; no individual rejected records',
        'sources': diagnostics_by_source,
    }, indent=2) + '\n', encoding='utf-8')
    (OUT / 'sources.json').write_text(json.dumps({
        'last_checked_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'live_verified': False, 'coverage_note': 'Partial market coverage; record-level verification pending',
        'sources': health}, indent=2) + '\n', encoding='utf-8')
    builders = {}
    for p in current_permits:
        name = p['contractor'].strip()
        key = builder_key(name)
        if key:
            b = builders.setdefault(key, {'builder': name, 'projects': 0,
                                          'valuation': 0, 'jurisdictions': set(),
                                          'aliases': set()})
            b['projects'] += 1
            b['valuation'] += p['valuation']
            b['jurisdictions'].add(p['jurisdiction'])
            b['aliases'].add(name)
    rolled = []
    for b in builders.values():
        aliases = sorted(b['aliases'], key=lambda name: (name.casefold(), name))
        rolled.append({**b, 'builder': aliases[0], 'aliases': aliases,
                       'jurisdictions': sorted(b['jurisdictions'])})
    (OUT / 'builders.json').write_text(json.dumps(
        sorted(rolled, key=lambda b: (-b['projects'], b['builder'].casefold())),
        indent=2) + '\n', encoding='utf-8')
    for filename, title, condition in [
        ('all.xml', 'NC issued new construction candidates', lambda x: True),
        ('single-family.xml', 'NC single family candidates', lambda x: x['category'] == 'Single Family'),
        ('multifamily.xml', 'NC multifamily candidates', lambda x: x['category'] == 'Multifamily'),
        ('commercial.xml', 'NC commercial candidates', lambda x: x['category'] == 'Commercial'),
        ('top.xml', 'NC top opportunity candidates', lambda x: x['score'] >= 60),
    ]:
        rss(title, [p for p in current_permits if condition(p)], filename)
    print(json.dumps({'current_screened': len(current_permits), 'historic_mecklenburg_snapshot': len(archived), 'sources': health}, indent=2))


if __name__ == '__main__':
    main()
