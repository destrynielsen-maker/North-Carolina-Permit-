"""Chunk 8 bounded pilot/record-recheck unit tests. No network calls."""
import importlib.util
import pathlib
import sys
import unittest
from unittest.mock import patch

SRC=pathlib.Path(__file__).parents[1]/'src'
sys.path.insert(0,str(SRC))
spec=importlib.util.spec_from_file_location('validate_chunk8',SRC/'validate_chunk8.py')
v=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


class Chunk8Tests(unittest.TestCase):
    def test_brunswick_date_formats_are_not_assumed(self):
        self.assertEqual(v.date_format('11/10/2026'),'MM/DD/YYYY')
        self.assertEqual(v.date_format('2026-11-10'),'YYYY-MM-DD')
        self.assertEqual(v.date_format('Nov 10 2026'),'other')
        self.assertEqual(v.date_format(None),'blank')

    def test_wake_pilot_is_capped_and_does_not_promote(self):
        fields={k:'esriFieldTypeString' for k in
                ('permit_number','permit_status','permit_type','work_class')}
        fields['issue_date']='esriFieldTypeDate'
        sample=[
          {'PERMIT_NUMBER':'WAKE-01','PERMIT_STATUS':'Issued','WORK_CLASS':'New'},
          {'PERMIT_NUMBER':'RALEIGH-01','PERMIT_STATUS':'Issued','WORK_CLASS':'New'}]
        with patch.object(v,'metadata',return_value=fields), patch.object(v,'query_page',return_value=sample) as query:
            result=v.wake_overlap_sample([{'permit_number':'RALEIGH-01','jurisdiction':'Raleigh'}])
        self.assertEqual(result['state'],'sampled_no_promotion')
        self.assertFalse(result['enabled_for_collection'])
        self.assertEqual(result['exact_matches_against_screened_raleigh'],1)
        self.assertEqual(result['sample_size'],2)
        self.assertLessEqual(query.call_args.kwargs['limit'],v.MAX_SAMPLE)

    def test_wake_wrong_issue_date_type_rejects(self):
        data={k:'esriFieldTypeString' for k in
              ('permit_number','issue_date','permit_status','permit_type','work_class')}
        with patch.object(v,'metadata',return_value=data):
            with self.assertRaisesRegex(RuntimeError,'date'):
                v.wake_overlap_sample([])

    def test_brunswick_samples_do_not_infer_prime_contractor(self):
        fields={k:'esriFieldTypeString' for k in
                ('permitnumber','dateissued','permitstatus','permittype','jurisdiction')}
        sample=[{'PermitNumber':'A1','DateIssued':'11/01/2026',
                 'PermitStatus':'Issued','Jurisdiction':'Leland','PermitType':'New House'},
                {'PermitNumber':'A2','DateIssued':'unknown',
                 'PermitStatus':'Applied','Jurisdiction':'Brunswick','PermitType':'Building'}]
        with patch.object(v,'metadata',return_value=fields),patch.object(v,'query_page',return_value=sample):
            out=v.brunswick_date_sample()
        self.assertFalse(out['enabled_for_collection'])
        self.assertEqual(out['sample_size'],2)
        self.assertEqual(out['parseable_by_current_issued_date_parser'],1)
        self.assertNotIn('contractor',str(out).lower())

    def test_qa_recheck_matches_current_record_but_not_independently_verified(self):
        item={'id':'raleigh:TEST-01','jurisdiction':'Raleigh','permit_number':'TEST-01',
              'issued_date':'2026-11-09','category':'Single Family','address':'10 TEST ST',
              'contractor':'ACME','status':'Issued'}
        current={'permit_number':'TEST-01','issued_date':'2026-11-09',
                 'category':'Single Family','address':'10 TEST ST',
                 'contractor':'ACME','status':'Issued'}
        with patch.object(v,'metadata',return_value={'permitnum':'esriFieldTypeString'}), \
             patch.object(v,'query_page',return_value=[{'permitnum':'TEST-01'}]), \
             patch.object(v,'normalize',return_value=current):
            out=v.recheck_qa_records([item])
        self.assertEqual(out[0]['state'],'source_requery_consistent')
        self.assertFalse(out[0]['independently_verified'])
        self.assertEqual(out[0]['review_kind'],'official_source_requery_not_independent_portal')

    def test_qa_recheck_error_cannot_pass(self):
        item={'id':'raleigh:TEST','jurisdiction':'Raleigh','permit_number':'TEST'}
        with patch.object(v,'metadata',side_effect=RuntimeError('source blocked')):
            out=v.recheck_qa_records([item])
        self.assertEqual(out[0]['state'],'query_error')


if __name__=='__main__':
    unittest.main()
