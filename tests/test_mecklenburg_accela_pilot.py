"""Offline Accela building-permit discovery tests. No external requests."""
import datetime as dt
import importlib.util
import pathlib
import sys
import unittest

SRC=pathlib.Path(__file__).resolve().parents[1]/'src'
sys.path.insert(0,str(SRC))
spec=importlib.util.spec_from_file_location('nc_accela_pilot',SRC/'probe_mecklenburg_accela.py')
a=importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
TODAY=dt.date(2026,11,12)
FIELDS=[{'name':x} for x in a.REQUIRED_FIELDS]
METADATA={'fields':FIELDS}


def example(**extras):
    row={
        'OBJECTID':52, 'casenumber':'RES-NEW-26-004012',
        'casestatus':'Issued',
        'permitissued':int(dt.datetime(2026,11,10,tzinfo=dt.timezone.utc).timestamp()*1000),
        'description':'New single-family dwelling',
        'typeofwork':'New Construction',
        'comres':'Residential','address':'1 TEST DR',
        'contractorsname':'Builder LLC',
        'contractorsphone':'704-555-0101',
        'ownerbuilder':'N',
        'jobvaluation':'300000',
    }
    row.update(extras)
    return {'attributes':row}


class AccelaPilotTests(unittest.TestCase):
    def test_official_accela_source_has_explicit_contractor_fields(self):
        self.assertEqual(a.ACCELA_URL,
            'https://services3.arcgis.com/hPs600I3X0RTaaaq/arcgis/rest/services/Accela_Building_Permits/FeatureServer/0')
        self.assertIn('contractorsname',a.REQUIRED_FIELDS)
        self.assertIn('contractorsphone',a.REQUIRED_FIELDS)
        self.assertIn('permitissued',a.REQUIRED_FIELDS)

    def test_new_home_candidate_kept_outside_live_permits(self):
        record=a.eligible_candidate(example()['attributes'],TODAY)
        self.assertEqual(record['case_number'],'RES-NEW-26-004012')
        self.assertEqual(record['contractor_as_published_unverified'],'Builder LLC')
        self.assertEqual(record['contractor_phone_as_published'],'704-555-0101')
        self.assertEqual(record['category_screened'],'Single Family')
        self.assertFalse(record['included_in_sales_leads'])
        self.assertIn('OBJECTID+%3D+52',record['source_record_url'])

    def test_applied_void_and_trade_only_do_not_pass(self):
        for changes in ({'casestatus':'Pending'},
                        {'casestatus':'Void'},
                        {'typeofwork':'Electrical','description':'New HVAC work',
                         'casenumber':'ELEC-NEW-26-0011'},
                        {'permitissued':None}):
            with self.subTest(changes=changes):
                self.assertIsNone(a.eligible_candidate(example(**changes)['attributes'],TODAY))

    def test_commercial_and_townhome_types_not_mislabeled(self):
        commercial=example(casenumber='COM-NEW-26-0120',
                           description='New warehouse',comres='Commercial')
        self.assertEqual(a.classify(commercial['attributes']),'Commercial')
        multi=example(description='New townhome building',comres='Residential')
        self.assertEqual(a.classify(multi['attributes']),'Multifamily')

    def test_public_phone_is_optional_and_invalid_is_hidden(self):
        record=a.eligible_candidate(example(contractorsphone='not a phone')['attributes'],TODAY)
        self.assertEqual(record['contractor_phone_as_published'],'')
        self.assertEqual(record['contractor_as_published_unverified'],'Builder LLC')

    def test_no_fake_contractor_if_missing(self):
        record=a.eligible_candidate(example(contractorsname='',contractorsphone='')['attributes'],TODAY)
        self.assertEqual(record['contractor_as_published_unverified'],'')
        self.assertEqual(record['contractor_phone_as_published'],'')
        self.assertFalse(record['included_in_sales_leads'])

    def test_future_issued_date_and_missing_object_id_excluded(self):
        future=example(permitissued=int(dt.datetime(2027,1,10,tzinfo=dt.timezone.utc).timestamp()*1000))
        self.assertIsNone(a.eligible_candidate(future['attributes'],TODAY))
        self.assertIsNone(a.eligible_candidate(example(OBJECTID=None)['attributes'],TODAY))

    def test_summary_is_read_only_and_exact_case_comparison_only(self):
        past=[{'jurisdiction':a.OLD_MARKET,'permit_number':'RES-NEW-26-004012'},
              {'jurisdiction':a.OLD_MARKET,'permit_number':'B-OTHER'}]
        s=a.summarize(METADATA,[example()],past,TODAY)
        self.assertEqual(s['sample_size'],1)
        self.assertEqual(s['screened_new_building_records'],1)
        self.assertEqual(s['screened_with_contractor_name'],1)
        self.assertEqual(s['screened_case_numbers_matching_existing_mecklenburg'],1)
        self.assertEqual(s['new_permits_added_to_live'],0)
        self.assertFalse(s['enabled_for_collection'])

    def test_missing_required_contractor_schema_is_blocking(self):
        metadata={'fields':[{'name':'casenumber'},{'name':'permitissued'}]}
        with self.assertRaisesRegex(RuntimeError,'schema missing'):
            a.summarize(metadata,[example()],[],TODAY)

    def test_unqualified_rows_not_exported_as_research(self):
        s=a.summarize(METADATA,[
            example(casestatus='Void'),
            example(casenumber='ELEC-NEW-26-1001',description='New electrical service',
                    typeofwork='Electrical'),
        ],[],TODAY)
        self.assertEqual(s['screened_new_building_records'],0)
        self.assertEqual(s['research_records'],[])


if __name__=='__main__':
    unittest.main()
