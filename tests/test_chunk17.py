"""Chunk 17 review-decision safety tests; no municipal network calls."""
import copy
import datetime as dt
import importlib.util
import json
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('nc_reviews',ROOT/'src'/'compile_reviews.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ReviewDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decisions=json.loads((ROOT/'reviews/decisions.json').read_text(encoding='utf-8'))
        cls.manifest=json.loads((ROOT/'public/data/verification_issues.json').read_text(encoding='utf-8'))
        cls.queue=json.loads((ROOT/'public/data/chunk13_review_queue.json').read_text(encoding='utf-8'))

    def compile(self, doc):
        return m.validate_and_compile(doc,self.manifest,self.queue,dt.date(2026,11,12))

    def test_real_records_start_pending_and_never_publish(self):
        data=self.compile(copy.deepcopy(self.decisions))
        self.assertEqual(data['counts']['pending'],2)
        self.assertEqual(data['counts']['confirmed'],0)
        self.assertEqual(data['auto_promoted_leads'],0)
        self.assertTrue(all(not x['included_in_sales_leads'] for x in data['reviews']))
        self.assertTrue(all(x['release_status']=='held_research_only' for x in data['reviews']))

    def test_confirmation_without_independent_evidence_is_rejected(self):
        doc=copy.deepcopy(self.decisions)
        doc['decisions'][0]['decision']='confirmed'
        with self.assertRaisesRegex(ValueError,'Confirmed review missing'):
            self.compile(doc)

    def test_confirmation_requirements_cannot_be_bypassed_by_issue_closure(self):
        doc=copy.deepcopy(self.decisions)
        doc['decisions'][0]['decision']='confirmed'
        doc['decisions'][0]['reviewer']='curator'
        doc['decisions'][0]['reviewed_on']='2026-11-12'
        doc['decisions'][0]['official_evidence_url']='https://wakecountync-energovpub.tylerhost.net/apps/selfservice'
        doc['decisions'][0]['official_record_reference']='RBPR-183204-2026'
        doc['decisions'][0]['issuer']='Town'
        doc['decisions'][0]['licensed_prime_builder']='Builder'
        doc['decisions'][0]['duplicate_disposition']='unresolved'
        for field in m.BOOLEAN_CHECKS:
            doc['decisions'][0][field]=True
        with self.assertRaisesRegex(ValueError,'resolved no-match duplicate check'):
            self.compile(doc)
        doc['decisions'][0]['duplicate_disposition']='no_match'
        with self.assertRaisesRegex(ValueError,'record-specific official evidence URL'):
            self.compile(doc)

    def test_human_attested_evidence_still_does_not_promote(self):
        doc=copy.deepcopy(self.decisions)
        d=doc['decisions'][0]
        d.update({
            'decision':'confirmed',
            'reviewer':'Test Reviewer',
            'reviewed_on':'2026-11-12',
            'official_evidence_url':'https://wakecountync-energovpub.tylerhost.net/apps/selfservice#/permit/EXAMPLE',
            'official_record_reference':'RBPR-183204-2026',
            'issuer':'Municipal Issuer - synthetic',
            'licensed_prime_builder':'Synthetic Builder LLC',
            'duplicate_disposition':'no_match',
        })
        for field in m.BOOLEAN_CHECKS:
            d[field]=True
        data=self.compile(doc)
        self.assertEqual(data['counts']['confirmed'],1)
        self.assertEqual(data['auto_promoted_leads'],0)
        self.assertFalse(data['reviews'][1]['included_in_sales_leads'])
        self.assertTrue(all(x['release_status']=='held_research_only' for x in data['reviews']))

    def test_unknown_or_mismatched_object_id_and_issue_cannot_publish(self):
        doc=copy.deepcopy(self.decisions)
        doc['decisions'][0]['gis_object_id']=999999
        with self.assertRaisesRegex(ValueError,'does not match'):
            self.compile(doc)
        doc=copy.deepcopy(self.decisions)
        doc['decisions'][1]['issue_number']=1
        with self.assertRaisesRegex(ValueError,'Issue number mismatch'):
            self.compile(doc)

    def test_duplicate_decision_and_missing_review_are_errors(self):
        doc=copy.deepcopy(self.decisions)
        doc['decisions'].append(copy.deepcopy(doc['decisions'][0]))
        with self.assertRaisesRegex(ValueError,'Duplicate review decision'):
            self.compile(doc)
        doc=copy.deepcopy(self.decisions)
        doc['decisions']=doc['decisions'][:1]
        with self.assertRaisesRegex(ValueError,'correspond exactly'):
            self.compile(doc)

    def test_official_evidence_host_and_direct_route_required(self):
        self.assertFalse(m.official_record_evidence_url('https://github.com/owner/repo/issues/1','wake'))
        self.assertFalse(m.official_record_evidence_url('https://maps.wake.gov/arcgis/rest/services/x','wake'))
        self.assertFalse(m.official_record_evidence_url('https://wakecountync-energovpub.tylerhost.net/apps/selfservice#/search','wake'))
        self.assertFalse(m.official_record_evidence_url('https://bcpp.brunswickcountync.gov/','brunswick'))
        self.assertTrue(m.official_record_evidence_url('https://apps.brunsco.net/bcms/permits/detail?project=701942','brunswick'))

    def test_invalid_date_and_rejected_state_require_evidence(self):
        doc=copy.deepcopy(self.decisions)
        row=doc['decisions'][0]
        row.update({'decision':'rejected','reason':''})
        with self.assertRaisesRegex(ValueError,'needs a reason'):
            self.compile(doc)
        row['reason']='Not a new home'
        self.assertEqual(self.compile(doc)['counts']['rejected'],1)

    def test_reviews_compiler_has_no_automatic_lead_write_path(self):
        src=(ROOT/'src/compile_reviews.py').read_text(encoding='utf-8')
        self.assertIn("OUTPUT_FILE = ROOT / 'public' / 'data' / 'review_status.json'",src)
        self.assertNotIn("ROOT / 'public' / 'data' / 'permits.json'",src)
        self.assertNotIn('mcp__GitHub__',src)


if __name__=='__main__':
    unittest.main()
