"""Chunk 11 read-only pilot contracts, all source responses are synthetic."""
import datetime as dt
import importlib.util
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
spec=importlib.util.spec_from_file_location('chunk11',ROOT/'src'/'validate_chunk11.py')
v=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

class Chunk11Tests(unittest.TestCase):
    def test_municipal_issuer_evidence_is_not_automatic_approval(self):
        self.assertEqual(v.evidence_bucket('KNIGHTDALE'),
                         'town_issuance_guidance_but_permit_unverified')
        self.assertEqual(v.evidence_bucket('ROLESVILLE'),
                         'town_issuance_guidance_but_permit_unverified')
        self.assertEqual(v.evidence_bucket('WENDELL'),
                         'shared_permitting_process_needs_review')
        self.assertEqual(v.evidence_bucket('ZEBULON'),
                         'shared_permitting_process_needs_review')
        self.assertEqual(v.evidence_bucket('RALEIGH'),'raleigh_planning_area_hold')
        self.assertEqual(v.evidence_bucket('no_matching_polygon'),
                         'unknown_planning_area_hold')

    def test_link_host_does_not_retain_user_identifiers(self):
        self.assertEqual(v.web_host('https://wakecountync-energovpub.tylerhost.net/Apps/Permit/123?key=SECRET'),
                         'wakecountync-energovpub.tylerhost.net')
        self.assertEqual(v.web_host('javascript:alert(1)'), '')
        self.assertEqual(v.web_host('http://example.test/permit'), '')
        self.assertEqual(v.web_host(None), '')

    def test_wake_pilot_only_aggregates_and_never_promotes(self):
        rows=[
          {'attributes':{'LINK':'https://wake.example.org/1?person=alice'},
           'geometry':{'x':2100000,'y':750000}},
          {'attributes':{'LINK':'https://wake.example.org/2?person=bob'},
           'geometry':{'x':2100100,'y':750100}},
          {'attributes':{},'geometry':None},
        ]
        def boundaries(url,params):
            return [{'attributes':{'JURISDICTION':'KNIGHTDALE' if '2100000' in params['geometry'] else 'RALEIGH'}}]
        result=v.wake_roles_pilot(lambda *_:rows,boundaries)
        self.assertEqual(result['sample_size'],3)
        self.assertEqual(result['planning_jurisdiction_counts']['KNIGHTDALE'],1)
        self.assertEqual(result['authority_evidence_buckets']['raleigh_planning_area_hold'],1)
        self.assertEqual(result['authority_evidence_buckets']['unknown_planning_area_hold'],1)
        self.assertEqual(result['safe_permit_link_hosts'],{'wake.example.org':2})
        self.assertNotIn('alice',str(result))
        self.assertFalse(result['enabled_for_collection'])
        self.assertFalse(result['all_permits_independently_verified'])

    def test_brunswick_counts_subcontractors_but_zero_verified_prime_builders(self):
        rows=[
          {'attributes':{'PermitNumber':'A-1','ProjectNumber':'P-1',
                         'SubContractor':'Electrical Co','DateIssued':'2026-11-10',
                         'Jurisdiction':'BRUNSWICK COUNTY'}},
          {'attributes':{'PermitNumber':'A-2','ProjectNumber':'P-2',
                         'SubContractor':'','DateIssued':'2099-02-12',
                         'Jurisdiction':'NAVASSA'}},
        ]
        result=v.brunswick_prime_builder_pilot(lambda *_:rows,dt.date(2026,11,12))
        self.assertEqual(result['sample_size'],2)
        self.assertEqual(result['recent_issue_dates'],1)
        self.assertEqual(result['future_dates'],1)
        self.assertEqual(result['nonblank_subcontractor_fields'],1)
        self.assertEqual(result['nonblank_project_numbers'],2)
        self.assertEqual(result['confirmed_prime_contractors'],0)
        self.assertEqual(result['prime_contractor_mapping'],'not_established')
        self.assertFalse(result['enabled_for_collection'])

    def test_brunswick_empty_sample_stays_held(self):
        result=v.brunswick_prime_builder_pilot(lambda *_:[],dt.date(2026,11,12))
        self.assertEqual(result['sample_size'],0)
        self.assertEqual(result['confirmed_prime_contractors'],0)
        self.assertFalse(result['enabled_for_collection'])

if __name__=='__main__':
    unittest.main()
