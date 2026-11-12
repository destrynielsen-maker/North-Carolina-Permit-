"""Chunk 18: fail-closed release readiness checks; all samples synthetic."""
import copy
import datetime as dt
import importlib.util
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
spec = importlib.util.spec_from_file_location('nc_release_audit',ROOT/'src/audit_release_readiness.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
from compile_reviews import validate_and_compile


class ReleaseReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decisions = json.loads((ROOT/'reviews/decisions.json').read_text())
        cls.status = json.loads((ROOT/'public/data/review_status.json').read_text())
        cls.manifest = json.loads((ROOT/'public/data/verification_issues.json').read_text())
        cls.queue = json.loads((ROOT/'public/data/chunk13_review_queue.json').read_text())
        cls.sources = json.loads((ROOT/'public/data/sources.json').read_text())

    def run_audit(self, ledger=None, status=None, manifest=None, queue=None, sources=None):
        return audit.audit_readiness(
            ledger if ledger is not None else self.decisions,
            status if status is not None else self.status,
            manifest if manifest is not None else self.manifest,
            queue if queue is not None else self.queue,
            sources if sources is not None else self.sources,
        )

    def test_pending_records_are_blocked_for_specific_reasons(self):
        out = self.run_audit()
        self.assertEqual(out['counts']['research_records_audited'],2)
        self.assertEqual(out['counts']['evidence_complete_for_review'],0)
        self.assertEqual(out['counts']['eligible_for_automatic_promotion'],0)
        self.assertEqual({x['source'] for x in out['reviews']},{'wake','brunswick'})
        for r in out['reviews']:
            self.assertEqual(r['release_status'],'held_research_only')
            self.assertFalse(r['included_in_sales_leads'])
            self.assertIn('review_not_confirmed',r['blocked_reasons'])
            self.assertIn('licensed_prime_builder_unverified',r['blocked_reasons'])
            self.assertIn('source_not_approved_for_live_collection',r['blocked_reasons'])
            self.assertIn('separate_manual_release_authorization_required',r['blocked_reasons'])

    def test_stale_compiled_status_is_rejected(self):
        bogus=copy.deepcopy(self.status)
        bogus['reviews'][0]['decision']='confirmed'
        with self.assertRaisesRegex(ValueError,'stale or inconsistent'):
            self.run_audit(status=bogus)

    def test_changed_permit_reference_is_rejected(self):
        bogus=copy.deepcopy(self.manifest)
        bogus['entries'][0]['permit_number']='DIFFERENT'
        with self.assertRaisesRegex(ValueError,'disagree'):
            self.run_audit(manifest=bogus)

    def test_unexpected_live_county_activation_fails_closed(self):
        changed=copy.deepcopy(self.sources)
        for s in changed['sources']:
            if s['name']=='Wake County':
                s.update({'qualified':12,'state':'collected - sample verification pending'})
        with self.assertRaisesRegex(ValueError,'unexpectedly present in production'):
            self.run_audit(sources=changed)

    def test_valid_human_confirmation_remains_held_not_live(self):
        edited=copy.deepcopy(self.decisions)
        d=edited['decisions'][0]
        d.update({
            'decision':'confirmed','reviewer':'Test reviewer',
            'reviewed_on':'2026-11-12',
            'official_evidence_url':'https://wakecountync-energovpub.tylerhost.net/apps/selfservice#/permit/SYNTHETIC',
            'official_record_reference':'RBPR-183204-2026',
            'issuer':'Synthetic authority','licensed_prime_builder':'Synthetic homebuilder',
            'duplicate_disposition':'no_match'
        })
        for flag in ('permit_id_confirmed','issued_date_confirmed','status_confirmed',
                     'new_construction_confirmed','reviewer_attests_portal_record_match'):
            d[flag]=True
        compiled=validate_and_compile(edited,self.manifest,self.queue,dt.date(2026,11,12))
        out=self.run_audit(ledger=edited,status=compiled)
        self.assertEqual(out['counts']['evidence_complete_for_review'],1)
        self.assertEqual(out['counts']['eligible_for_automatic_promotion'],0)
        self.assertTrue(out['reviews'][1]['evidence_complete_for_review'])
        self.assertEqual(out['reviews'][1]['blocked_reasons'],[
            'source_not_approved_for_live_collection',
            'separate_manual_release_authorization_required'
        ])

    def test_fake_portal_homepage_is_not_valid_confirmation(self):
        edited=copy.deepcopy(self.decisions)
        d=edited['decisions'][0]
        d.update({'decision':'confirmed',
                  'reviewer':'Test reviewer','reviewed_on':'2026-11-12',
                  'official_evidence_url':'https://wakecountync-energovpub.tylerhost.net/apps/selfservice',
                  'official_record_reference':'RBPR-183204-2026',
                  'issuer':'Test','licensed_prime_builder':'Test Builder',
                  'duplicate_disposition':'no_match'})
        for flag in ('permit_id_confirmed','issued_date_confirmed','status_confirmed',
                     'new_construction_confirmed','reviewer_attests_portal_record_match'):
            d[flag]=True
        bogus_status=copy.deepcopy(self.status)
        bogus_status['reviews'][1]['decision']='confirmed'
        with self.assertRaisesRegex(ValueError,'record-specific official evidence URL'):
            self.run_audit(ledger=edited,status=bogus_status)

    def test_compiler_writes_only_separate_readiness_report(self):
        source=(ROOT/'src/audit_release_readiness.py').read_text()
        self.assertIn("'release_readiness.json'",source)
        self.assertNotIn("ROOT / 'public' / 'data' / 'permits.json'",source)
        self.assertNotIn('auto_promoted_leads = 1',source)


if __name__=='__main__':
    unittest.main()
