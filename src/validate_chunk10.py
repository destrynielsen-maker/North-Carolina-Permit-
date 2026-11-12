"""Chunk 10: bounded, read-only GIS jurisdiction and new-home permit probes.

Absolutely no new permits are promoted. All outputs are aggregate statistics.
The polygon is a *planning* authority boundary, not proof of permit issuer.
"""
from __future__ import annotations

from collections import Counter
import datetime as dt
import json
import math
from pathlib import Path

from collect import OUT, get, issue_date

WAKE_URL = 'https://maps.wake.gov/arcgis/rest/services/Inspections/Building_Permits/MapServer/0'
BOUNDARY_URL = 'https://maps.wake.gov/arcgis/rest/services/Jurisdictions/Jurisdictions/MapServer/1'
BRUNSWICK_URL = 'https://services1.arcgis.com/W6gamXPYQeLXrdAd/arcgis/rest/services/Permit_Locations/FeatureServer/0'
WAKE_LIMIT = 20
BRUNSWICK_LIMIT = 100
BRUNSWICK_NEW_HOME_TYPES = ('NEW HOME', 'RESIDENTIAL MODULAR', 'TOWNHOME')


def get_features(url, params):
    result = get(url + '/query', {'f': 'json', **params})
    if result.get('error'):
        raise RuntimeError('ArcGIS query failed: ' + str(result['error'])[:160])
    if not isinstance(result.get('features'), list):
        raise RuntimeError('ArcGIS query returned no features array')
    return result['features']


def valid_state_plane_point(geometry):
    if not isinstance(geometry, dict):
        return False
    x, y = geometry.get('x'), geometry.get('y')
    return (isinstance(x, (int, float)) and isinstance(y, (int, float))
            and math.isfinite(x) and math.isfinite(y)
            and 1800000 <= x <= 2400000 and 500000 <= y <= 950000)


def jurisdiction_for_point(geometry, boundary_request=get_features):
    """Resolve only a single unambiguous planning-jurisdiction polygon.

    A municipality's planning boundary is NOT its building-permit issuer.
    Missing or multiple polygon matches remain unknown.
    """
    if not valid_state_plane_point(geometry):
        return 'missing_or_invalid_point'
    feature_rows = boundary_request(BOUNDARY_URL, {
        'where': '1=1',
        'geometry': json.dumps({
            'x': geometry['x'], 'y': geometry['y'],
            'spatialReference': {'wkid': 2264}}),
        'geometryType': 'esriGeometryPoint',
        'spatialRel': 'esriSpatialRelIntersects',
        'inSR': 2264,
        'outFields': 'JURISDICTION,PLAN_JURIS',
        'returnGeometry': 'false',
        'resultRecordCount': 5,
    })
    values = {str(x.get('attributes', {}).get('JURISDICTION') or '').strip().upper()
              for x in feature_rows}
    values.discard('')
    return next(iter(values)) if len(values) == 1 else (
        'no_matching_polygon' if not values else 'ambiguous_multiple_polygons')


def wake_planning_pilot(source_request=get_features, boundary_request=get_features):
    """Sample a narrowly scoped Wake work class; NOT a countywide analysis."""
    rows = source_request(WAKE_URL, {
        'where': "ISSUE_DATE IS NOT NULL AND PERMIT_STATUS = 'Issued' "
                 "AND WORK_CLASS = 'New One- and Two-Family Dwelling'",
        'outFields': 'PERMIT_NUMBER,ISSUE_DATE,PERMIT_STATUS,WORK_CLASS',
        'returnGeometry': 'true', 'outSR': 2264,
        'orderByFields': 'ISSUE_DATE DESC',
        'resultRecordCount': WAKE_LIMIT,
    })
    jurisdictions = Counter()
    errors = 0
    for row in rows[:WAKE_LIMIT]:
        try:
            name = jurisdiction_for_point(row.get('geometry'), boundary_request)
        except Exception:
            name = 'boundary_query_error'
            errors += 1
        jurisdictions[name] += 1
    raleigh = jurisdictions.get('RALEIGH', 0)
    non_raleigh = sum(n for label, n in jurisdictions.items()
                      if label not in {'RALEIGH', 'missing_or_invalid_point',
                                      'no_matching_polygon', 'ambiguous_multiple_polygons',
                                      'boundary_query_error'})
    return {
        'state': 'sampled_no_promotion', 'sample_size': min(len(rows), WAKE_LIMIT),
        'work_class_filter': 'New One- and Two-Family Dwelling',
        'boundary_url': BOUNDARY_URL,
        'boundary_spatial_reference_wkid': 2264,
        'planning_jurisdiction_counts': dict(sorted(jurisdictions.items())),
        'raleigh_planning_area_count': raleigh,
        'other_named_planning_areas_count': non_raleigh,
        'unknown_or_error_count': sum(jurisdictions[k] for k in
            ('missing_or_invalid_point','no_matching_polygon',
             'ambiguous_multiple_polygons','boundary_query_error')),
        'boundary_query_errors': errors,
        'boundary_interpretation': (
            'Planning jurisdiction includes ETJ and is not proof of permitting agency. '
            'No polygon match is NOT proof of an unincorporated county permit. '
            'Only a bounded new-dwelling sample was checked.'
        ),
        'enabled_for_collection': False,
    }


def brunswick_new_home_pilot(source_request=get_features, today=None):
    """Use exactly the county's published residential-new-home filter."""
    today = today or dt.datetime.now(dt.timezone.utc).date()
    types = ','.join("'" + t.replace("'", "''") + "'" for t in BRUNSWICK_NEW_HOME_TYPES)
    rows = source_request(BRUNSWICK_URL, {
        'where': ("ProjectType = 'Residential' AND PermitStatus = 'Active' "
                  "AND PermitType IN (" + types + ") AND DateIssued IS NOT NULL"),
        'outFields': 'PermitNumber,DateIssued,PermitStatus,PermitType,ProjectType,Jurisdiction',
        'returnGeometry': 'false',
        'orderByFields': 'DateIssued DESC',
        'resultRecordCount': BRUNSWICK_LIMIT,
    })
    valid, future, unparseable, stale = 0, 0, 0, 0
    dates, types_seen, jurisdictions = [], Counter(), Counter()
    for feature in rows[:BRUNSWICK_LIMIT]:
        a = feature.get('attributes', {})
        issued = issue_date(a.get('DateIssued'))
        if issued is None:
            unparseable += 1
        elif issued > today:
            future += 1
        elif (today-issued).days > 365:
            stale += 1
        else:
            valid += 1
            dates.append(issued)
        types_seen[str(a.get('PermitType') or '(blank)').strip()] += 1
        jurisdictions[str(a.get('Jurisdiction') or '(blank)').strip()] += 1
    return {
        'state':'sampled_no_promotion', 'sample_size':min(len(rows),BRUNSWICK_LIMIT),
        'filtered_types':list(BRUNSWICK_NEW_HOME_TYPES),
        'filtered_status':'Active',
        'parseable_recent_not_future':valid,
        'future_dated':future, 'unparseable':unparseable, 'older_than_year':stale,
        'recent_date_min':min(dates).isoformat() if dates else None,
        'recent_date_max':max(dates).isoformat() if dates else None,
        'permit_type_counts':dict(sorted(types_seen.items())),
        'jurisdiction_counts':dict(sorted(jurisdictions.items())),
        'limitation':'Pre-filtered candidates only: no verified general contractor, no permit-detail audit, no live promotion.',
        'enabled_for_collection':False,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {
        'checked_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'policy':'Read-only spatial/new-home pilots; no new source feeds enabled',
        'independent_permit_verification':False,
        'pilots':{}
    }
    for name, func in (('wake_planning_boundary',wake_planning_pilot),
                       ('brunswick_new_home',brunswick_new_home_pilot)):
        try:
            report['pilots'][name] = func()
        except Exception as exc:
            report['pilots'][name] = {
                'state':'probe_error', 'error':str(exc)[:200],
                'enabled_for_collection':False,
            }
    (OUT / 'chunk10_validation.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k:v.get('state') for k,v in report['pilots'].items()}))


if __name__ == '__main__':
    main()
