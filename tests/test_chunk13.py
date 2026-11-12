"""Chunk 13 research-only permit lookup tests (no network)."""
import datetime as dt
import importlib.util
import pathlib
import sys
import unittest

SRC=pathlib.Path(__file__).resolve().parents[1]/'src'
sys.path.insert(0,str(SRC))
spec=importlib.util.spec_from_file_location('chunk13',SRC/'review_chunk13.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
TODAY=dt.date(2026,11,12)

class Chunk13Tests(unittest.TestCase):
    def test_unique_object_id_query_is_official_and_precise(self):
        url=m.official_gis_lookup(m.WAKE_URL,123456)
        self.assertIn('/query?',url)
        self.assertIn('OBJECTID+%3D+123456',url)
        self.assertIn('returnGeometry=false',url)
        self.assertNotIn('PERMIT_NUMBER',url)
        self.assertNotEqual(url,m.WAKE_URL)

    def test_reject_untrusted_layers_and_non_numeric_object_ids(self):
        self.assertEqual(m.official_gis_lookup('https://wrong.example.com/x',123),'')
        for ident in ("X' OR 1=1", '../file', '', 'A/123', '#foo', True, 0, -1):
            with self.subTest(ident=ident):
                self.assertEqual(m.official_gis_lookup(m.WAKE_URL,ident),'')

    def test_wake_requires_valid_issue_date_and_remains_unverified(self):
        rows=[
          {'attributes':{'OBJECTID':1234,'PERMIT_NUMBER':'W-1001','ISSUE_DATE':1794355200000,
              'WORK_CLASS':'New One- and Two-Family Dwelling',
              'CONTRACTOR':'Test Homes','LINK':'https://energovcitizenaccess.tylertech.com/WakeCountyNC/SelfService#/permit/abc'}},
          {'attributes':{'OBJECTID':1235,'PERMIT_NUMBER':'BAD','ISSUE_DATE':None}},
        ]
        out=m.wake_review_rows(lambda *_:rows,TODAY)
        self.assertEqual(len(out),1)
        self.assertEqual(out[0]['contractor_as_listed_unverified'],'Test Homes')
        self.assertEqual(out[0]['gis_object_id'],1234)
        self.assertIn('OBJECTID+%3D+1234',out[0]['exact_gis_query_url'])
        self.assertEqual(out[0]['legacy_link_route'],'permit')
        self.assertTrue(out[0]['official_portal_search'].startswith('https://wakecountync-'))
        self.assertFalse(out[0]['included_in_sales_leads'])
        self.assertNotIn('legacy_link_url',out[0])
        self.assertNotIn('issuer',out[0])

    def test_brunswick_never_infers_general_contractor_from_trade_contact(self):
        rows=[
          {'attributes':{'OBJECTID':4567,'PermitNumber':'B-1001','ProjectNumber':'P-1001',
              'DateIssued':'2026-11-10T10:00:00',
              'PermitType':'NEW HOME','ParcelAddress':'100 TEST DR',
              'SubContractor':'Electrician LLC','Jurisdiction':'BRUNSWICK COUNTY'}},
          {'attributes':{'OBJECTID':4568,'PermitNumber':'B-1002','DateIssued':'2099-11-10',
              'PermitType':'NEW HOME'}}
        ]
        out=m.brunswick_review_rows(lambda *_:rows,TODAY)
        self.assertEqual(len(out),1)
        self.assertIsNone(out[0]['prime_builder'])
        self.assertIn('OBJECTID+%3D+4567',out[0]['exact_gis_query_url'])
        self.assertNotIn('Electrician LLC',str(out))
        self.assertIn('100 TEST DR',out[0]['address'])
        self.assertFalse(out[0]['included_in_sales_leads'])

    def test_brunswick_duplicate_permit_numbers_use_project_reference(self):
        sample=[
            {'permit_number':'1000','project_number':'701942','gis_object_id':284255},
            {'permit_number':'1000','project_number':'701212','gis_object_id':283852},
            {'permit_number':'1000','project_number':'702962','gis_object_id':284686},
        ]
        audit=m.annotate_review_identifiers(sample,'brunswick')
        self.assertEqual(audit['permit_numbers_reused_in_sample'],1)
        self.assertEqual(audit['project_numbers_reused_in_sample'],0)
        self.assertEqual(sample[0]['reference_label'],'Project 701942')
        self.assertTrue(all(r['permit_number_reused_in_sample'] for r in sample))
        self.assertTrue(all(r['reference_kind']=='project_number_not_globally_verified' for r in sample))

    def test_repeated_project_number_falls_back_to_exact_gis_id(self):
        sample=[
            {'permit_number':'1000','project_number':'200','gis_object_id':91},
            {'permit_number':'1000','project_number':'200','gis_object_id':92},
        ]
        audit=m.annotate_review_identifiers(sample,'brunswick')
        self.assertEqual(audit['project_numbers_reused_in_sample'],1)
        self.assertTrue(all(r['reference_kind']=='gis_object_id' for r in sample))
        self.assertEqual(sample[0]['reference_label'],'GIS record 91')

    def test_wake_duplicate_number_is_flagged_without_promotion(self):
        sample=[
            {'permit_number':'A-1','gis_object_id':3},
            {'permit_number':'A-1','gis_object_id':4},
            {'permit_number':'B-2','gis_object_id':5},
        ]
        m.annotate_review_identifiers(sample,'wake')
        self.assertEqual(sample[0]['reference_label'],'GIS record 3')
        self.assertEqual(sample[2]['reference_label'],'Permit B-2')
        self.assertTrue(sample[1]['permit_number_reused_in_sample'])

    def test_queue_is_bounded_and_uses_exact_types(self):
        calls=[]
        def wake_req(url,args):
            calls.append((url,args))
            return []
        def brunswick_req(url,args):
            calls.append((url,args))
            return []
        self.assertEqual(m.wake_review_rows(wake_req,TODAY),[])
        self.assertEqual(m.brunswick_review_rows(brunswick_req,TODAY),[])
        self.assertEqual(calls[0][1]['resultRecordCount'],8)
        self.assertEqual(calls[1][1]['resultRecordCount'],8)
        self.assertIn('Issued',calls[0][1]['where'])
        self.assertIn('NEW HOME',calls[1][1]['where'])
        self.assertIn('Residential',calls[1][1]['where'])

if __name__=='__main__':
    unittest.main()
