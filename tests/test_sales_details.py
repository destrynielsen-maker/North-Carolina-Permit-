"""Sales-friendly permit detail contracts. Synthetic data, no live network."""
import datetime as dt
import importlib.util
import pathlib
import unittest
from urllib.parse import parse_qs, urlsplit

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('nc_sales_collector',ROOT/'src'/'collect.py')
nc=importlib.util.module_from_spec(spec)
spec.loader.exec_module(nc)
TODAY=dt.date(2026,11,12)
RALEIGH=next(s for s in nc.SOURCES if s['id']=='raleigh')
GREENSBORO=next(s for s in nc.SOURCES if s['id']=='greensboro')
MECK=next(s for s in nc.SOURCES if s['id']=='mecklenburg')


def row(source, **extra):
    data={
        source['number']:'TEST-2026-ABC',source['date']:'2026-11-10',
        source['status']:'Issued',
        source['type_fields'][0]:'Residential - single family',
        source['work_fields'][0]:'New Construction',
        source['description_fields'][0]:'Build new single family residence',
        source['valuation']: 450000.0,
    }
    data.update(extra)
    return data


class SalesDetailTests(unittest.TestCase):
    def test_raleigh_public_business_contact_fields_are_mapped(self):
        data=row(RALEIGH,OBJECTID=91234,contractorcompanyname='EXAMPLE HOMES LLC',
                 contractorphone='919-555-0101',
                 contractoremail='sales@examplehomes.test',
                 contractorlicnum='NC-19483',contractordba='Example Builders',
                 contractoraddress1='5 INDUSTRY RD',contractorcity='RALEIGH',
                 contractorstate='NC',contractorzip='27601',
                 projectname='Village South',totalsqft=3200,numberstories=2,
                 housingunitstotal=1,originaladdress1='12 SAMPLE ST')
        p=nc.normalize(data,RALEIGH,TODAY)
        self.assertEqual(p['project_name'],'Village South')
        self.assertEqual(p['contractor'],'EXAMPLE HOMES LLC')
        self.assertEqual(p['contractor_phone'],'919-555-0101')
        self.assertEqual(p['contractor_email'],'sales@examplehomes.test')
        self.assertEqual(p['contractor_license'],'NC-19483')
        self.assertEqual(p['contractor_dba'],'Example Builders')
        self.assertIn('5 INDUSTRY RD',p['contractor_address'])
        self.assertEqual(p['square_feet'],3200)
        self.assertEqual(p['stories'],2)
        self.assertEqual(p['housing_units'],1)
        self.assertEqual(p['work_class'],'New Construction')
        self.assertEqual(p['permit_detail_url'],'')
        self.assertIn('/query?',p['source_record_url'])
        self.assertEqual(parse_qs(urlsplit(p['source_record_url']).query)['where'],['OBJECTID = 91234'])
        self.assertEqual(p['source_url'],RALEIGH['url'])

    def test_no_contact_data_is_never_fabricated(self):
        p=nc.normalize(row(MECK,projadd='123 TEST AVE',contractorphone='FAKE'),
                       MECK,TODAY)
        self.assertEqual(p['contractor'],'')
        self.assertEqual(p['contractor_phone'],'')
        self.assertEqual(p['contractor_email'],'')
        self.assertIsNone(p['square_feet'])
        self.assertEqual(p['source_record_url'],'')
        self.assertIn('unverified',p['verification'])

    def test_greensboro_official_page_is_separate_from_original_gis(self):
        p=nc.normalize(row(GREENSBORO,PermitNum='202518414',OBJECTID=181231,
                           OccupancyDesc='Single Family',Contractor='House Corp'),
                       GREENSBORO,TODAY)
        self.assertIn('bldgPermitNumber=202518414',p['permit_detail_url'])
        self.assertIn('OBJECTID+%3D+181231',p['source_record_url'])
        self.assertEqual(p['source_url'],GREENSBORO['url'])

    def test_only_real_positive_quantities_display(self):
        for bad in (None,'','not recorded',0,-1,float('nan'),float('inf')):
            with self.subTest(raw=bad):
                self.assertIsNone(nc.optional_number(bad))
        self.assertEqual(nc.optional_number('3200'),3200.0)

    def test_suspicious_object_ids_do_not_form_source_record_urls(self):
        for oid in (None,0,-5,'1 OR 1=1',True,2147483648):
            with self.subTest(oid=oid):
                self.assertEqual(nc.public_record_query_url(RALEIGH,{'OBJECTID':oid}),'')

    def test_contact_coverage_counts_are_aggregate_and_source_scoped(self):
        records=[
            {'jurisdiction':'Raleigh','contractor':'Example LLC',
             'contractor_phone':'9195550100','contractor_email':'sales@example.test',
             'contractor_license':'12345','source_record_url':'https://example.test/gis'},
            {'jurisdiction':'Raleigh','contractor':'Other LLC','contractor_phone':'',
             'contractor_email':'','source_record_url':'https://example.test/gis2'},
            {'jurisdiction':'Mecklenburg County / Charlotte','contractor':'',
             'source_record_url':''},
        ]
        coverage=nc.sales_field_coverage(records)
        self.assertEqual(len(coverage),2)
        r=next(x for x in coverage if x['jurisdiction']=='Raleigh')
        self.assertEqual(r['screened_permits'],2)
        self.assertEqual(r['contractor_available'],2)
        self.assertEqual(r['phone_or_email_available'],1)
        self.assertEqual(r['contractor_email_available'],1)
        self.assertEqual(r['source_record_url_available'],2)
        self.assertNotIn('sales@example.test',str(coverage))
        self.assertNotIn('9195550100',str(coverage))

    def test_sales_detail_page_loads_current_dataset_by_exact_id(self):
        html=(ROOT/'public'/'permit.html').read_text(encoding='utf-8')
        self.assertIn('fetch("data/permits.json"',html)
        self.assertIn('record.id===id',html)
        self.assertIn('new URLSearchParams(location.search).get("id")',html)
        self.assertIn('Original data source',html)
        self.assertIn('Exact GIS record',html)
        self.assertIn('Official city permit',html)
        self.assertIn('contractor_email',html)
        self.assertIn('contractor_phone',html)
        self.assertIn('Copy project summary',html)
        self.assertIn('not independently verified',html.lower())
        self.assertNotIn('innerHTML',html)

    def test_dashboard_primary_link_is_own_detail_page_and_csv_has_url(self):
        html=(ROOT/'public'/'index.html').read_text(encoding='utf-8')
        self.assertIn('function detailUrl(p)',html)
        self.assertIn('a.href=detailUrl(p)',html)
        self.assertIn('permit.html?id=',html)
        self.assertIn('Official source</th>',html)
        self.assertIn('sourceLink.href=p.source_record_url||p.source_url',html)
        self.assertIn('sales_detail_url',html)
        self.assertIn('source_record_url',html)
        self.assertIn('Call "+p.contractor_phone',html)
        self.assertIn('Email builder',html)


if __name__=='__main__':
    unittest.main()
