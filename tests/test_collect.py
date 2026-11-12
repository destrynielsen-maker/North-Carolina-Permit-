"""Offline qualification and ArcGIS pagination contract tests (synthetic records)."""
import datetime as dt
import importlib.util
import pathlib
import unittest
from unittest.mock import patch

path = pathlib.Path(__file__).parents[1] / 'src' / 'collect.py'
spec = importlib.util.spec_from_file_location('nc_collect', path)
nc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nc)
TODAY = dt.date(2026, 11, 12)
R = nc.SOURCES[0]
N = nc.SOURCES[1]
M = nc.SOURCES[2]
G = next(s for s in nc.SOURCES if s['id'] == 'greensboro')


def make(source, **overrides):
    a = {
        source['number']: 'TEST-0001', source['date']: '2026-11-10',
        source['status']: 'Issued', source['type_fields'][0]: 'Residential',
        source['work_fields'][0]: 'New Construction',
        source['description_fields'][0]: 'Construct new single-family dwelling',
        source['valuation']: 450000,
    }
    a.update(overrides)
    return a


class QualificationTests(unittest.TestCase):
    def test_raleigh_new_single_family(self):
        p = nc.normalize(make(R, contractorcompanyname='Sample Builder LLC', originaladdress1='123 TEST ST'), R, TODAY)
        self.assertEqual(p['category'], 'Single Family')
        self.assertEqual(p['contractor'], 'Sample Builder LLC')
        self.assertEqual(p['issued_date'], '2026-11-10')

    def test_nhc_multifamily_and_local_fields(self):
        p = nc.normalize(make(N, PERMIT_TYPE='NHC Residential Building', WORK_CLASS='New',
                              DESCRIPTION='New six-unit apartment building', GENERAL_CONTRACTOR='Mock Build',
                              NUMBER=40, STREET='DEMO', TYPE='RD'), N, TODAY)
        self.assertEqual(p['category'], 'Multifamily')
        self.assertEqual(p['address'], '40 DEMO RD')

    def test_mecklenburg_commercial_without_builder(self):
        p = nc.normalize(make(M, permittype='Commercial', worktype='New Construction',
                              projdesc='New warehouse', projadd='TEST AVE', bldgcost=990000), M, TODAY)
        self.assertEqual(p['category'], 'Commercial')
        self.assertEqual(p['contractor'], '')

    def test_mecklenburg_new_bldg_detached_qualifies(self):
        p = nc.normalize(make(M, permittype='One/Two Family New Bldg',
                              typeofbldg='R3 RESIDENTIAL - SINGLE FAMILY',
                              usdcdesc='101 - One Family Detached', worktype='',
                              constrtype='5B WOOD FRAME/UNPROTECTED',
                              permitdesc='Build a new detached house'), M, TODAY)
        self.assertEqual(p['category'], 'Single Family')

    def test_mecklenburg_new_bldg_apartments_qualify(self):
        p = nc.normalize(make(M, permittype='Commercial New Bldg',
                              typeofbldg='R2 RESIDENTIAL - MULTIPLE FAMILY',
                              usdcdesc='105 - 5 or More Family Apartments',
                              worktype='', constrtype='5A WOOD FRAME/PROTECTED',
                              permitdesc='New residential apartment building'), M, TODAY)
        self.assertEqual(p['category'], 'Multifamily')

    def test_mecklenburg_new_bldg_alteration_excluded(self):
        p = nc.normalize(make(M, permittype='One/Two Family New Bldg',
                              typeofbldg='R3 RESIDENTIAL',
                              usdcdesc='434 - Res Dwelling (Alteration, Repair)',
                              worktype='', permitdesc='Replace existing kitchen'), M, TODAY)
        self.assertIsNone(p)

    def test_mecklenburg_existing_bldg_does_not_qualify(self):
        p = nc.normalize(make(M, permittype='One/Two Family Existing Bldg',
                              typeofbldg='R3 RESIDENTIAL',
                              usdcdesc='101 - One Family Detached',
                              worktype='', permitdesc='Existing residence'), M, TODAY)
        self.assertIsNone(p)

    def test_greensboro_new_single_family_with_contractor(self):
        p = nc.normalize(make(G, PermitNum=123456, IssuedDate='2026-11-10',
                              StatusCurrent='Issued', ApplicationType='New Construction',
                              OccupancyDesc='Single Family Detached', Description='Construct new home',
                              Contractor='Example Homebuilders', TotalCost=310000,
                              FullAddress='10 TEST DR'), G, TODAY)
        self.assertEqual(p['category'], 'Single Family')
        self.assertEqual(p['contractor'], 'Example Homebuilders')
        self.assertEqual(p['valuation'], 310000)

    def test_greensboro_remodel_is_not_accepted(self):
        self.assertIsNone(nc.normalize(make(G, ApplicationType='Alteration',
                       Description='Remodel existing residence'), G, TODAY))

    def test_on_hold_stop_work_revoked_are_excluded(self):
        for status in ('On Hold', 'Stop Work Order', 'Revoked'):
            with self.subTest(status=status):
                self.assertIsNone(nc.normalize(make(R, statuscurrent=status), R, TODAY))

    def test_builder_key_case_punctuation_and_license_decorations(self):
        self.assertEqual(nc.builder_key('Stanley Martin Homes, LLC'),
                         nc.builder_key('STANLEY MARTIN HOMES LLC'))
        self.assertEqual(nc.builder_key('PULTE HOME COMPANY LLC (B) (LIC# 19311)'),
                         nc.builder_key('Pulte Home Company LLC'))
        self.assertNotEqual(nc.builder_key('CLAYTON PROPERTIES GROUP INC'),
                            nc.builder_key('CLAYTON PROPERTIES INC'))
        self.assertNotEqual(nc.builder_key('D R HORTON INC'),
                            nc.builder_key('D.R. Horton, Inc. T/A Emerald Homes'))

    def test_cross_source_permit_number_collision_is_audit_only(self):
        a = {'jurisdiction': 'Raleigh', 'permit_number': 'ABC-123',
             'issued_date': '2026-11-02', 'address': '7 Example St'}
        b = {'jurisdiction': 'Wake County', 'permit_number': 'abc-123',
             'issued_date': '2026-11-02', 'address': '7 Example St'}
        c = {'jurisdiction': 'Wake County', 'permit_number': 'ABC-123',
             'issued_date': '2026-11-03', 'address': '7 Example St'}
        x = nc.cross_source_number_collisions([a, b, c])
        self.assertEqual(x[0]['same_number'], 2)
        self.assertEqual(x[0]['same_number_and_issued_date'], 1)
        self.assertEqual(len([a,b,c]), 3)

    def test_same_address_different_permit_is_not_a_collision(self):
        a = {'jurisdiction': 'Raleigh', 'permit_number': 'A-5',
             'issued_date': '2026-11-02', 'address': '7 Example St'}
        b = {'jurisdiction': 'Wake County', 'permit_number': 'B-9',
             'issued_date': '2026-11-02', 'address': '7 Example St'}
        self.assertEqual(nc.cross_source_number_collisions([a, b]), [])

    def test_rankings_use_recent_90_and_category_breakdown(self):
        p = [
          {'contractor':'Acme Builders LLC','issued_date':'2026-11-11','category':'Single Family',
           'jurisdiction':'Greensboro','valuation':200000},
          {'contractor':'ACME BUILDERS, LLC','issued_date':'2026-08-24','category':'Multifamily',
           'jurisdiction':'Raleigh','valuation':800000},
          {'contractor':'Beta Homes','issued_date':'2026-01-01','category':'Single Family',
           'jurisdiction':'Raleigh','valuation':120000},
        ]
        rows=nc.build_builder_rankings(p,TODAY)
        self.assertEqual(set(rows[0]['aliases']),{'ACME BUILDERS, LLC','Acme Builders LLC'})
        self.assertEqual(rows[0]['rank'],1)
        self.assertEqual(rows[0]['issued_last_30_days'],1)
        self.assertEqual(rows[0]['issued_last_90_days'],2)
        self.assertEqual(rows[0]['categories']['Multifamily'],1)
        self.assertEqual(rows[0]['permit_count'],2)
        self.assertEqual(rows[0]['valuation'],1000000)
        self.assertEqual(rows[0]['jurisdictions'],['Greensboro','Raleigh'])

    def test_rankings_exclude_missing_contractor_and_old_date(self):
        rows=nc.build_builder_rankings([
            {'contractor':'','issued_date':'2026-11-10','category':'Single Family'},
            {'contractor':'Old','issued_date':'2021-01-01','category':'Single Family'},
        ],TODAY)
        self.assertEqual(rows,[])

    def test_qa_samples_choose_one_each_category_and_remain_unverified(self):
        original=[make(R, permitnum=f'SAMPLE-{i}',
                     proposedworkdescription=desc,
                     permittypemapped=cat, workclassmapped='New',
                     issueddate='2026-11-10') for i,(cat,desc) in enumerate([
                         ('Residential','New detached single family home'),
                         ('Commercial','New warehouse'),
                         ('Residential','New apartment building'),
                         ('Residential','New detached single family home')],1)]
        rows=[nc.normalize(x,R,TODAY) for x in original]
        self.assertTrue(all(rows))
        q=nc.manual_qa_samples(rows,[R],per_source=3)
        self.assertEqual(len(q),3)
        self.assertEqual(set(x['category'] for x in q),
                         {'Single Family','Commercial','Multifamily'})
        self.assertTrue(all(x['verification_status']=='manual_review_required' for x in q))
        self.assertTrue(all('query?' in x['source_query_url'] for x in q))

    def test_qa_samples_mark_retained_source_and_escaping(self):
        p=nc.normalize(make(R,permitnum="A'B",issueddate='2026-11-10'),R,TODAY)
        q=nc.manual_qa_samples([p],[R],failed={'Raleigh'})
        self.assertEqual(q[0]['collection_state'],'retained_from_previous_run')
        self.assertIn('A%27%27B',q[0]['source_query_url'])

    def test_applied_without_issued_date_excluded(self):
        a = make(R, issueddate=None, applieddate='2026-11-10')
        self.assertIsNone(nc.normalize(a, R, TODAY))

    def test_pending_excluded_even_with_issued_date(self):
        self.assertIsNone(nc.normalize(make(R, statuscurrent='Pending'), R, TODAY))

    def test_voided_excluded(self):
        self.assertIsNone(nc.normalize(make(N, PERMIT_STATUS='Voided'), N, TODAY))

    def test_trade_only_excluded_when_notes_say_new(self):
        self.assertIsNone(nc.normalize(make(N, PERMIT_TYPE='NHC Residential Mechanical Gas Piping'), N, TODAY))

    def test_renovation_excluded(self):
        self.assertIsNone(nc.normalize(make(M, worktype='Renovation', projdesc='Repair old kitchen'), M, TODAY))

    def test_remodel_new_construction_wording_excluded(self):
        self.assertIsNone(nc.normalize(make(R, proposedworkdescription='Remodel near new construction'), R, TODAY))

    def test_ambiguous_new_without_category_excluded(self):
        self.assertIsNone(nc.normalize(make(R, permittypemapped='Miscellaneous', workclassmapped='New', proposedworkdescription='New item'), R, TODAY))

    def test_future_and_old_excluded(self):
        self.assertIsNone(nc.normalize(make(R, issueddate='2026-11-20'), R, TODAY))
        self.assertIsNone(nc.normalize(make(R, issueddate='2024-01-01'), R, TODAY))

    def test_arcgis_epoch_date(self):
        epoch = int(dt.datetime(2026, 11, 10, tzinfo=dt.timezone.utc).timestamp() * 1000)
        self.assertEqual(nc.issue_date(epoch), dt.date(2026, 11, 10))

    def test_work_class_detected_when_permit_type_generic(self):
        p = nc.normalize(make(R, permittypemapped='Residential', workclassmapped='New',
                              proposedworkdescription='New single family'), R, TODAY)
        self.assertEqual(p['category'], 'Single Family')


class ApiTests(unittest.TestCase):
    def test_schema_missing_issue_date_errors(self):
        info = {'fields': [{'name': x, 'type': 'esriFieldTypeString'} for x in
                            ['permitnum', 'statuscurrent', 'estprojectcost', 'permittypemapped', 'workclassmapped']],
                'objectIdField': 'OBJECTID', 'capabilities': 'Query'}
        with self.assertRaisesRegex(RuntimeError, 'issueddate'):
            nc.check_schema(info, R)

    def test_query_paged_by_issued_date_not_object_id(self):
        fields = [{'name': x, 'type': 'esriFieldTypeString'} for x in
                  ['permitnum', 'issueddate', 'statuscurrent', 'estprojectcost', 'permittypemapped', 'workclassmapped']]
        fields.append({'name': 'OBJECTID', 'type': 'esriFieldTypeOID'})
        requests = []

        def fake_get(url, params):
            requests.append((url, params))
            if url == R['url']:
                return {'fields': fields, 'objectIdField': 'OBJECTID', 'capabilities': 'Query', 'maxRecordCount': 2}
            if params['resultOffset'] == 0:
                return {'features': [{'attributes': make(R)}] * 2, 'exceededTransferLimit': True}
            return {'features': []}

        with patch.object(nc, 'get', side_effect=fake_get):
            rows, scanned = nc.collect(R, TODAY)
        self.assertEqual(scanned, 2)
        self.assertEqual(len(rows), 2)
        self.assertTrue(requests[1][1]['orderByFields'].startswith('issueddate DESC'))
        self.assertIn("DATE '2026-05-16'", requests[1][1]['where'])
        self.assertEqual(requests[2][1]['resultOffset'], 2)

    def test_diagnostics_count_reasons_without_rejected_addresses(self):
        info = {'fields': [{'name': x} for x in
                ['PermitNum', 'IssuedDate', 'StatusCurrent', 'TotalCost', 'ApplicationType']],
                'objectIdField': 'OBJECTID', 'capabilities': 'Query', 'maxRecordCount': 10}
        records = [make(G, ApplicationType='New Construction', OccupancyDesc='Single Family',
                        Description='New single-family home'),
                   make(G, PermitNum=99002, IssuedDate=None, Description='New single-family home',
                        FullAddress='DO NOT EXPOSE ADDRESS')]
        def fake_get(url, params):
            return info if url == G['url'] else {'features': [{'attributes': a} for a in records]}
        diag = {}
        with patch.object(nc, 'get', side_effect=fake_get):
            rows, scanned = nc.collect(G, TODAY, diagnostics=diag)
        self.assertEqual((len(rows), scanned), (1, 2))
        self.assertEqual(diag['rejection_reasons']['missing_issued_date'], 1)
        self.assertNotIn('DO NOT EXPOSE ADDRESS', str(diag))

    def test_query_error_fails_closed(self):
        info = {'fields': [{'name': x} for x in
                           ['permitnum', 'issueddate', 'statuscurrent', 'estprojectcost', 'permittypemapped', 'workclassmapped']],
                'objectIdField': 'OBJECTID', 'capabilities': 'Query', 'maxRecordCount': 2}
        with patch.object(nc, 'get', side_effect=[info, {'error': {'message': 'invalid SQL'}}]):
            with self.assertRaisesRegex(RuntimeError, 'invalid SQL'):
                nc.collect(R, TODAY)


if __name__ == '__main__':
    unittest.main()
