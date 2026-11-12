"""Chunk 14 research queue revalidation tests, no network."""
import datetime as dt
import importlib.util
import pathlib
import sys
import unittest

SRC=pathlib.Path(__file__).resolve().parents[1]/'src'
sys.path.insert(0,str(SRC))
spec=importlib.util.spec_from_file_location('validate_chunk14',SRC/'validate_chunk14.py')
v=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


class Chunk14Tests(unittest.TestCase):
    def wake_candidate(self):
        return {'gis_object_id':128361,
                'permit_number':'RBPR-183204-2026','issued_date':'2026-11-10',
                'work_class':'New One- and Two-Family Dwelling',
                'contractor_as_listed_unverified':'',
                'reference_label':'Permit RBPR-183204-2026'}
    def brunswick_candidate(self):
        return {'gis_object_id':284255,'permit_number':'1000',
                'project_number':'701942','issued_date':'2026-11-10',
                'permit_type':'NEW HOME','address':'6402 TEST DR',
                'reported_jurisdiction':'BRUNSWICK COUNTY',
                'reference_label':'Project 701942'}

    def test_exact_wake_object_id_with_matching_source_is_not_verified(self):
        def mock(url, query):
            self.assertEqual(url,v.WAKE_URL)
            self.assertEqual(query['where'],'OBJECTID = 128361')
            return [{'attributes':{'OBJECTID':128361,
                   'PERMIT_NUMBER':'RBPR-183204-2026',
                   'ISSUE_DATE':int(dt.datetime(2026,11,10,tzinfo=dt.timezone.utc).timestamp()*1000),
                   'WORK_CLASS':'New One- and Two-Family Dwelling',
                   'CONTRACTOR':'','PERMIT_STATUS':'Issued'}}]
        r=v.recheck_one('wake',self.wake_candidate(),mock)
        self.assertEqual(r['state'],'same_source_consistent')
        self.assertTrue(r['checks']['issued_date_matches'])
        self.assertFalse(r['independently_verified'])
        self.assertFalse(r['included_in_sales_leads'])

    def test_brunswick_repeated_permit_field_is_safe_with_unique_object_id(self):
        def mock(url,query):
            self.assertEqual(query['where'],'OBJECTID = 284255')
            return [{'attributes':{'OBJECTID':284255,'PermitNumber':'1000',
                  'ProjectNumber':'701942','DateIssued':'2026-11-10T00:00:00',
                  'PermitType':'NEW HOME','PermitStatus':'Active',
                  'ParcelAddress':'6402 TEST DR','Jurisdiction':'BRUNSWICK COUNTY'}}]
        r=v.recheck_one('brunswick',self.brunswick_candidate(),mock)
        self.assertEqual(r['state'],'same_source_consistent')
        self.assertTrue(r['checks']['project_number_matches'])
        self.assertFalse(r['prime_builder_verified'])

    def test_changed_project_number_does_not_pass(self):
        def mock(_url,_query):
            return [{'attributes':{'OBJECTID':284255,'PermitNumber':'1000',
                 'ProjectNumber':'999999','DateIssued':'2026-11-10',
                 'PermitType':'NEW HOME','PermitStatus':'Active',
                 'ParcelAddress':'6402 TEST DR','Jurisdiction':'BRUNSWICK COUNTY'}}]
        r=v.recheck_one('brunswick',self.brunswick_candidate(),mock)
        self.assertEqual(r['state'],'same_source_changed')
        self.assertIn('project_number_matches',r['failed_check_names'])
        self.assertFalse(r['included_in_sales_leads'])

    def test_missing_source_row_cannot_pass(self):
        r=v.recheck_one('wake',self.wake_candidate(),lambda *_:[])
        self.assertEqual(r['state'],'missing_or_multiple_current_features')
        self.assertFalse(r['independently_verified'])

    def test_invalid_ids_fail_closed_without_query(self):
        def fail(*args):
            raise AssertionError('should never reach network')
        for oid in ('128361',None,-1,0,True):
            c=dict(self.wake_candidate(),gis_object_id=oid)
            self.assertEqual(v.recheck_one('wake',c,fail)['state'],
                             'invalid_source_or_object_id')

    def test_validation_of_both_counties_never_promotes(self):
        q={'sources':{
            'wake':{'candidates':[self.wake_candidate()]},
            'brunswick':{'candidates':[self.brunswick_candidate()]},
        }}
        def fake(url,query):
            raise RuntimeError('municipal service outage')
        r=v.validate_queue(q,fake)
        self.assertEqual(r['records_attempted'],2)
        self.assertEqual(r['independently_verified_count'],0)
        self.assertEqual(r['state_counts']['gis_recheck_error'],2)
        self.assertFalse(r['enabled_for_collection'])


if __name__=='__main__':
    unittest.main()
