"""Chunk 16 tests: real GitHub review issue links never imply permit verification."""
import json
import pathlib
import re
import unittest
from urllib.parse import urlsplit

ROOT=pathlib.Path(__file__).resolve().parents[1]
QUEUE=ROOT/'public/data/chunk13_review_queue.json'
ISSUES=ROOT/'public/data/verification_issues.json'
DASHBOARD=ROOT/'public/index.html'


class Chunk16Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.queue=json.loads(QUEUE.read_text(encoding='utf-8'))
        cls.manifest=json.loads(ISSUES.read_text(encoding='utf-8'))
        cls.dashboard=DASHBOARD.read_text(encoding='utf-8')

    def test_existing_issues_match_exact_research_object_ids(self):
        entries=self.manifest['entries']
        self.assertEqual(len(entries),2)
        self.assertEqual({e['source'] for e in entries},{'wake','brunswick'})
        for e in entries:
            candidates=self.queue['sources'][e['source']]['candidates']
            matches=[p for p in candidates if p['gis_object_id']==e['gis_object_id']]
            self.assertEqual(len(matches),1)
            self.assertEqual(matches[0]['permit_number'],e['permit_number'])
            if e['source']=='brunswick':
                self.assertEqual(matches[0]['project_number'],e['project_number'])

    def test_review_manifest_is_not_an_approval_and_links_are_safe(self):
        for e in self.manifest['entries']:
            self.assertEqual(e['verification_status'],'manual_review_required')
            self.assertFalse(e['included_in_sales_leads'])
            u=urlsplit(e['issue_url'])
            self.assertEqual(u.scheme,'https')
            self.assertEqual(u.hostname,'github.com')
            self.assertRegex(u.path,r'^/destrynielsen-maker/North-Carolina-Permit-/issues/[1-9][0-9]*$')
            self.assertEqual(u.query,'')
            self.assertEqual(u.fragment,'')
            self.assertEqual(int(u.path.rsplit('/',1)[1]),e['issue_number'])

    def test_dashboard_reuses_existing_issues_and_leaves_draft_fallback(self):
        page=self.dashboard
        for phrase in (
            'data/verification_issues.json',
            'issueLookup[item.source+":"+item.gis_object_id]',
            'issueLookup[key+":"+p.gis_object_id]',
            'linkedIssue?linkedIssue.url:verificationIssueUrl(p)',
            'Open review #',
            'Start verification',
            'No issue automatically enables a county or promotes leads',
        ):
            self.assertIn(phrase,page)

    def test_research_queue_stays_outside_live_leads(self):
        self.assertFalse(self.queue['independently_verified'])
        self.assertFalse(self.queue['included_in_sales_leads'])
        for source in self.queue['sources'].values():
            self.assertFalse(source['enabled_for_collection'])
            self.assertTrue(all(not r['included_in_sales_leads'] for r in source['candidates']))


if __name__=='__main__':
    unittest.main()
