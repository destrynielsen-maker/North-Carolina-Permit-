import importlib.util
import pathlib
import unittest
from unittest.mock import patch

path=pathlib.Path(__file__).parents[1]/'src'/'probe_sources.py'
spec=importlib.util.spec_from_file_location('nc_probes',path)
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

class ProbeTests(unittest.TestCase):
    def test_brunswick_dateissued_is_string_not_auto_enabled(self):
        out=p.inspect_metadata({'fields':[
            {'name':'PermitNumber','type':'esriFieldTypeString'},
            {'name':'DateIssued','type':'esriFieldTypeString'}],
            'capabilities':'Query'},p.TARGETS[1])
        self.assertEqual(out['issue_date_candidates'],[
            {'name':'DateIssued','type':'esriFieldTypeString'}])
        self.assertFalse(out['enabled_for_collection'])

    def test_cabarrus_filing_date_is_not_issuance(self):
        out=p.inspect_metadata({'fields':[
            {'name':'B1_FILE_DD','type':'esriFieldTypeDate'},
            {'name':'B1_APPL_STATUS_DATE','type':'esriFieldTypeDate'}]},p.TARGETS[2])
        self.assertEqual(out['issue_date_candidates'],[])
        self.assertFalse(out['enabled_for_collection'])

    def test_wake_issue_field_discovers_type_without_promoting(self):
        out=p.inspect_metadata({'fields':[
            {'name':'IssuedDate','type':'esriFieldTypeDate'}]},p.TARGETS[0])
        self.assertEqual(out['issue_date_candidates'][0]['name'],'IssuedDate')
        self.assertFalse(out['enabled_for_collection'])

    def test_empty_metadata_errors(self):
        with self.assertRaisesRegex(RuntimeError,'no field metadata'):
            p.inspect_metadata({'fields':[]},p.TARGETS[0])

if __name__=='__main__':
    unittest.main()
