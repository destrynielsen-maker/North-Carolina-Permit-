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
