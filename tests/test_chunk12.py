"""Chunk 12 link-integrity and builder-evidence tests, with no network."""
import importlib.util
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
spec=importlib.util.spec_from_file_location('chunk12',ROOT/'src'/'validate_chunk12.py')
v=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


class Chunk12Tests(unittest.TestCase):
    def test_legacy_wake_url_signature_redacts_record_and_query(self):
        url=('https://energovcitizenaccess.tylertech.com/WakeCountyNC/'
             'SelfService#/permit/12345?email=example@secret.test')
        out=v.wake_link_signature(url)
        self.assertEqual(out['state'],'legacy_host')
        self.assertEqual(out['fragment_first_route'],'permit')
        self.assertTrue(out['has_later_fragment_path_segments'])
        self.assertNotIn('12345',str(out))
        self.assertNotIn('secret',str(out))

    def test_current_wake_url_must_not_infer_verified_deep_link(self):
        url='https://wakecountync-energovpub.tylerhost.net/apps/selfservice#/search'
        out=v.wake_link_signature(url)
        self.assertEqual(out['state'],'current_host')
        self.assertEqual(out['fragment_first_route'],'search')
        self.assertFalse(out['has_later_fragment_path_segments'])

    def test_reject_external_or_unsafe_link_values(self):
        for candidate in (None, '', 'javascript:alert(1)', 'http://example.org/1',
                          'https://outsider.example.com/permit/123',
                          'https://user:pass@energovcitizenaccess.tylertech.com/x'):
            with self.subTest(candidate=candidate):
                self.assertNotIn(v.wake_link_signature(candidate).get('state'),
                                 ('legacy_host','current_host'))

    def test_wake_probe_counts_legacy_without_rewriting(self):
        rows=[
          {'attributes':{'PERMIT_NUMBER':'P-1',
            'LINK':'https://energovcitizenaccess.tylertech.com/WakeCountyNC/SelfService#/permit/P-1'}},
          {'attributes':{'PERMIT_NUMBER':'P-2',
            'LINK':'https://energovcitizenaccess.tylertech.com/WakeCountyNC/SelfService#/permit/P-2'}},
          {'attributes':{'PERMIT_NUMBER':'P-3',
            'LINK':'https://wakecountync-energovpub.tylerhost.net/apps/selfservice#/home'}},
        ]
        out=v.wake_link_pilot(lambda *_:rows)
        self.assertEqual(out['sample_size'],3)
        self.assertEqual(out['link_states']['legacy_host'],2)
        self.assertEqual(out['legacy_links_appearing_record_specific'],2)
        self.assertEqual(out['deep_links_verified_at_new_portal'],0)
        self.assertFalse(out['enabled_for_collection'])
        self.assertNotIn('P-1',str(out))

    def test_brunswick_subcontractor_is_not_builder(self):
        fields=[{'name':'PermitNumber'},{'name':'DateIssued'},
                {'name':'SubContractor'},{'name':'PermitStatus'}]
        rows=[{'attributes':{'SubContractor':'Trade One'}},
              {'attributes':{'SubContractor':'Trade Two'}},
              {'attributes':{'SubContractor':''}}]
        out=v.brunswick_builder_field_pilot(
            lambda *_:{'fields':fields},lambda *_:rows)
        self.assertEqual(out['sample_size'],3)
        self.assertEqual(out['gis_fields_count'],4)
        self.assertEqual(out['nonblank_subcontractor_fields'],2)
        self.assertEqual(out['independent_gc_or_builder_field_candidates'],[])
        self.assertEqual(out['verified_prime_builder_names'],0)
        self.assertFalse(out['enabled_for_collection'])
        self.assertNotIn('Trade One',str(out))

    def test_brunswick_unverified_gc_like_field_is_not_promoted(self):
        fields=[{'name':'SubContractor'},{'name':'GeneralContractor'}]
        out=v.brunswick_builder_field_pilot(lambda *_:{'fields':fields},
                                             lambda *_:[])
        self.assertEqual(out['independent_gc_or_builder_field_candidates'],
                         ['GeneralContractor'])
        self.assertEqual(out['verified_prime_builder_names'],0)
        self.assertFalse(out['enabled_for_collection'])

    def test_missing_brunswick_schema_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError,'missing fields'):
            v.brunswick_builder_field_pilot(lambda *_:{'fields':[]},lambda *_:[])


if __name__=='__main__':
    unittest.main()
