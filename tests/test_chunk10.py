"""Chunk 10 tests: synthetic, no live network access."""
import datetime as dt
import importlib.util
import pathlib
import sys
import unittest
from unittest.mock import patch

SRC = pathlib.Path(__file__).parents[1] / 'src'
sys.path.insert(0, str(SRC))
spec = importlib.util.spec_from_file_location('nc_chunk10', SRC / 'validate_chunk10.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Chunk10Tests(unittest.TestCase):
    def test_uses_official_planning_boundaries(self):
        calls = []
        def mock_boundary(url, params):
            calls.append((url, params))
            return [{'attributes':{'JURISDICTION':'RALEIGH','PLAN_JURIS':'RA'}}]
        name = m.jurisdiction_for_point({'x':2100000,'y':750000}, mock_boundary)
        self.assertEqual(name,'RALEIGH')
        self.assertEqual(calls[0][0],m.BOUNDARY_URL)
        self.assertEqual(calls[0][1]['inSR'],2264)
        self.assertEqual(calls[0][1]['spatialRel'],'esriSpatialRelIntersects')

    def test_missing_or_outside_polygon_is_unknown_not_county(self):
        self.assertEqual(m.jurisdiction_for_point(None),'missing_or_invalid_point')
        self.assertEqual(m.jurisdiction_for_point({'x':-78,'y':36}),
                         'missing_or_invalid_point')
        self.assertEqual(m.jurisdiction_for_point({'x':2100000,'y':750000},
                         lambda *_:[]),'no_matching_polygon')

    def test_conflicting_boundary_polygons_are_ambiguous(self):
        result = m.jurisdiction_for_point({'x':2100000,'y':750000},
                  lambda *_:[{'attributes':{'JURISDICTION':'RALEIGH'}},
                             {'attributes':{'JURISDICTION':'CARY'}}])
        self.assertEqual(result,'ambiguous_multiple_polygons')

    def test_wake_spatial_pilot_quarantines_all_records(self):
        source = [
            {'geometry':{'x':2100000,'y':750000},'attributes':{}},
            {'geometry':{'x':2100100,'y':750100},'attributes':{}},
            {'geometry':None,'attributes':{}},
        ]
        def mock_boundary(_url,params):
            return [{'attributes':{'JURISDICTION':
                       'RALEIGH' if '2100000' in params['geometry'] else 'CARY'}}]
        result = m.wake_planning_pilot(lambda *_:source,mock_boundary)
        self.assertEqual(result['sample_size'],3)
        self.assertEqual(result['raleigh_planning_area_count'],1)
        self.assertEqual(result['other_named_planning_areas_count'],1)
        self.assertEqual(result['unknown_or_error_count'],1)
        self.assertFalse(result['enabled_for_collection'])

    def test_wake_boundary_failure_does_not_approve(self):
        def fail(*args):
            raise RuntimeError('server error')
        result = m.wake_planning_pilot(
            lambda *_:[{'geometry':{'x':2100000,'y':750000}}],
            fail)
        self.assertEqual(result['boundary_query_errors'],1)
        self.assertEqual(result['raleigh_planning_area_count'],0)
        self.assertFalse(result['enabled_for_collection'])

    def test_brunswick_filtered_issued_new_home_and_future_guard(self):
        today = dt.date(2026,11,12)
        sample = [
            {'attributes':{'DateIssued':'2026-11-10T12:00:00',
                           'PermitType':'NEW HOME','Jurisdiction':'BRUNSWICK COUNTY'}},
            {'attributes':{'DateIssued':'2099-02-12T00:00:00',
                           'PermitType':'TOWNHOME','Jurisdiction':'LELAND'}},
            {'attributes':{'DateIssued':'n/a',
                           'PermitType':'RESIDENTIAL MODULAR','Jurisdiction':'LELAND'}},
            {'attributes':{'DateIssued':'2024-01-01T00:00:00',
                           'PermitType':'NEW HOME','Jurisdiction':'BRUNSWICK COUNTY'}}
        ]
        args = []
        def source(url,params):
            args.append(params)
            return sample
        result = m.brunswick_new_home_pilot(source,today)
        self.assertEqual(result['parseable_recent_not_future'],1)
        self.assertEqual(result['future_dated'],1)
        self.assertEqual(result['unparseable'],1)
        self.assertEqual(result['older_than_year'],1)
        self.assertFalse(result['enabled_for_collection'])
        self.assertIn('NEW HOME',args[0]['where'])
        self.assertIn('ProjectType',args[0]['where'])
        self.assertIn('PermitStatus',args[0]['where'])
        self.assertLessEqual(args[0]['resultRecordCount'],m.BRUNSWICK_LIMIT)

    def test_brunswick_empty_sample_is_not_approval(self):
        result = m.brunswick_new_home_pilot(lambda *_:[],dt.date(2026,11,12))
        self.assertEqual(result['sample_size'],0)
        self.assertFalse(result['enabled_for_collection'])


if __name__ == '__main__':
    unittest.main()
