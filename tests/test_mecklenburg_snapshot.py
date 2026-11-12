"""Mecklenburg commercial open-data snapshot guardrails, all offline."""
import datetime as dt
import importlib.util
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

SRC=pathlib.Path(__file__).resolve().parents[1]/'src/collect.py'
spec=importlib.util.spec_from_file_location('nc_snapshot_collect',SRC)
nc=importlib.util.module_from_spec(spec)
spec.loader.exec_module(nc)


def fake_meck(number):
    return {
      'id':'mecklenburg:'+number,'permit_number':number,
      'jurisdiction':'Mecklenburg County / Charlotte',
      'issued_date':'2026-11-10','category':'Single Family',
      'score':75,'contractor':'','valuation':400000,
      'address':'111 SAMPLE AVE','description':'New dwelling',
      'status':'Issued','source_url':nc.SOURCES[2]['url'],
      'source_record_url':nc.SOURCES[2]['url']+'/query?f=pjson',
      'verification':'screened public record — not independently verified'
    }


class MecklenburgSnapshotTests(unittest.TestCase):
    def test_meck_live_polling_is_disabled_by_configuration(self):
        market=next(s for s in nc.SOURCES if s['id']=='mecklenburg')
        self.assertFalse(market['enabled'])
        self.assertTrue(market['snapshot_only'])
        self.assertEqual(market['snapshot_as_of_utc'],
                         '2026-11-12T22:34:56.402783+00:00')

    def test_preserved_snapshot_carries_provenance_without_modifying_original(self):
        original=fake_meck('B1001')
        other={'id':'raleigh:A','jurisdiction':'Raleigh'}
        result=nc.preserve_historic_mecklenburg([original,other], '2026-11-12T22:34:56Z')
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]['id'],'mecklenburg:B1001')
        self.assertEqual(result[0]['collection_mode'],'historic_snapshot')
        self.assertEqual(result[0]['snapshot_as_of_utc'],'2026-11-12T22:34:56Z')
        self.assertIn('not refreshed',result[0]['verification'])
        self.assertNotIn('collection_mode',original)

    def test_snapshot_only_market_never_calls_gis_and_stays_out_of_rss(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=pathlib.Path(temp)
            data=[fake_meck('B1001'),fake_meck('B1002')]
            (folder/'permits.json').write_text(json.dumps(data),encoding='utf-8')
            queried=[]
            def safe_collect(source,**kwargs):
                queried.append(source['id'])
                if source['id']=='mecklenburg':
                    raise AssertionError('commercial live Mecklenburg API must never be queried')
                return [],0
            feeds={}
            def capture_feed(title,records,filename):
                feeds[filename]=list(records)
            with patch.object(nc,'OUT',folder),patch.object(nc,'collect',side_effect=safe_collect),patch.object(nc,'rss',side_effect=capture_feed):
                nc.main()
            self.assertNotIn('mecklenburg',queried)
            archived=json.loads((folder/'mecklenburg_snapshot.json').read_text())
            self.assertEqual(len(archived),2)
            self.assertTrue(all(x['collection_mode']=='historic_snapshot' for x in archived))
            output=json.loads((folder/'permits.json').read_text())
            self.assertEqual(len(output),2)
            health=json.loads((folder/'sources.json').read_text())
            market=next(x for x in health['sources'] if x['name']=='Mecklenburg County / Charlotte')
            self.assertEqual(market['scanned'],0)
            self.assertEqual(market['qualified'],0)
            self.assertEqual(market['archived_count'],2)
            self.assertIn('live API polling disabled',market['state'])
            self.assertIn('all.xml',feeds)
            self.assertEqual(feeds['all.xml'],[])
            self.assertTrue(all(not rows for rows in feeds.values()))
            rank=json.loads((folder/'builder_rankings.json').read_text())
            self.assertEqual(rank['builders'],[])
            coverage=json.loads((folder/'sales_field_coverage.json').read_text())
            meck=next(row for row in coverage['sources'] if row['jurisdiction']=='Mecklenburg County / Charlotte')
            self.assertEqual(meck['historical_snapshot_count'],2)

    def test_dashboard_defaults_to_current_and_dates_historic_charlotte(self):
        page=(pathlib.Path(__file__).resolve().parents[1]/'public/index.html').read_text()
        self.assertIn('id="freshness"',page)
        self.assertIn('<option value="current">Current collections</option>',page)
        self.assertIn('id="archived"',page)
        self.assertIn('p.collection_mode==="historic_snapshot"',page)
        self.assertIn('snapshot_as_of_utc',page)
        self.assertIn('sourceLink.href=isHistoric?"https://maps.mecklenburgcountync.gov/openmapping/data.html"',page)
        self.assertIn('"snapshot_as_of_utc"',page)

    def test_archived_detail_page_excludes_live_gis_navigation(self):
        page=(pathlib.Path(__file__).resolve().parents[1]/'public/permit.html').read_text()
        self.assertIn('var historic=p.collection_mode==="historic_snapshot"',page)
        self.assertIn('HISTORIC SNAPSHOT',page)
        self.assertIn('if(historic){',page)
        self.assertIn('Mecklenburg open-data downloads',page)
        self.assertIn('Official county permit search (manual)',page)
        self.assertIn('addLink("Official city permit",official,true);',page)
        self.assertIn('if(historic){',page)

    def test_standalone_frozen_archive_is_not_overwritten_on_later_runs(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=pathlib.Path(temp)
            old=[fake_meck('B1001')]
            (folder/'permits.json').write_text(json.dumps(old),encoding='utf-8')
            def empty_collect(_source,**_kwargs):
                return [],0
            with patch.object(nc,'OUT',folder),patch.object(nc,'collect',side_effect=empty_collect),patch.object(nc,'rss'):
                nc.main()
                frozen=(folder/'mecklenburg_snapshot.json').read_text()
                (folder/'permits.json').write_text(json.dumps([fake_meck('B9999')]),encoding='utf-8')
                nc.main()
            self.assertEqual((folder/'mecklenburg_snapshot.json').read_text(),frozen)
            output=json.loads((folder/'permits.json').read_text())
            self.assertEqual([x['id'] for x in output],['mecklenburg:B1001'])


if __name__=='__main__':
    unittest.main()
