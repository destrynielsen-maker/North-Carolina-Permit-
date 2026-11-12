"""Chunk 15: safe manual permit-verification workflow checks.

No network calls. These assert that a human review draft cannot silently
promote Wake or Brunswick research records into the live permit dataset.
"""
import json
import pathlib
import re
import unittest
from urllib.parse import parse_qs, urlsplit

ROOT = pathlib.Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / 'public' / 'index.html'
QUEUE = ROOT / 'public' / 'data' / 'chunk13_review_queue.json'


class Chunk15Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dashboard = DASHBOARD.read_text(encoding='utf-8')
        cls.queue = json.loads(QUEUE.read_text(encoding='utf-8'))

    def test_review_control_creates_a_draft_not_an_approval(self):
        page = self.dashboard
        self.assertIn('function verificationIssueUrl(p)', page)
        self.assertIn('new URLSearchParams({title:issueTitle,body:evidence})', page)
        self.assertIn('/issues/new?', page)
        self.assertIn('Start verification', page)
        self.assertIn('MANUAL REVIEW REQUIRED', page)
        self.assertIn('No issue automatically enables a county or promotes leads', page)
        self.assertNotIn('github.com/repos/', page)
        self.assertNotIn('issues.create(', page)

    def test_issue_template_contains_evidence_and_release_gates(self):
        page = self.dashboard
        for phrase in (
            'GIS feature OBJECTID:',
            'Recorded issue date:',
            'GIS lookup:',
            'Official portal search:',
            'Locate the SAME permit or project in the official permitting portal',
            'Verify original issue date, current status and new-construction type',
            'Identify the actual permit issuing authority',
            'Verify licensed prime builder / GC and role',
            'Check for duplicate project or building permits',
            'Official record URL:',
            'Outcome: Needs review / Verified / Excluded',
        ):
            self.assertIn(phrase, page)

    def test_queue_records_are_not_in_sales_leads(self):
        report = self.queue
        self.assertFalse(report['independently_verified'])
        self.assertFalse(report['included_in_sales_leads'])
        for name in ('wake', 'brunswick'):
            source = report['sources'][name]
            self.assertFalse(source['enabled_for_collection'])
            for record in source['candidates']:
                self.assertFalse(record['included_in_sales_leads'])
                self.assertEqual(record['record_verification'], 'manual_portal_review_required')
                self.assertIsInstance(record['gis_object_id'], int)
        self.assertTrue(all(item.get('prime_builder') is None
                            for item in report['sources']['brunswick']['candidates']))

    def test_exact_source_lookups_use_object_id_not_ambiguous_permit_number(self):
        for source in self.queue['sources'].values():
            for record in source['candidates']:
                url = record['exact_gis_query_url']
                params = parse_qs(urlsplit(url).query)
                self.assertEqual(params.get('where'), ['OBJECTID = ' + str(record['gis_object_id'])])
                self.assertEqual(params.get('returnGeometry'), ['false'])
                self.assertEqual(params.get('outFields'), ['*'])

    def test_no_current_portal_deep_link_is_claimed_as_verified(self):
        page = self.dashboard
        self.assertIn('These Wake and Brunswick candidates are excluded from the live permit totals', page)
        self.assertIn('prefilled GitHub issue', page)
        self.assertIn('Official portal search:', page)
        for record in self.queue['sources']['wake']['candidates']:
            self.assertEqual(record['issuer_verification'], 'unknown_issuer_review_required')
            self.assertEqual(record['legacy_link_state'], 'legacy_host')


if __name__ == '__main__':
    unittest.main()
