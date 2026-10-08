"""All 55 original IDs through current native admission/supervision, plus EOF/burst."""
import json
import unittest
from case_adapter import Cases,CORPUS,REPO
MAPPING=json.loads((REPO/'tests/manager/case_mapping.json').read_bytes())['cases']
EXTRA=[{**CORPUS['cases'][0],'id':name,'mode':name} for name in ('early_eof','final_burst','detached_helper')]
EXTRA += [{**CORPUS['cases'][0],'id':'v2_success','mode':'success','schema_version':2},{**CORPUS['cases'][0],'id':'v2_unsupported_setting','mode':'success','schema_version':2,'mutation':'unsupported_operations'}]
class SupervisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases=Cases(EXTRA)
    @classmethod
    def tearDownClass(cls):cls.cases.close()
    def check(self,name,expected):
        value=self.cases.execute(name)
        if value['phase']=='admission':
            classification='ineligible' if value['returncode']==3 else 'invalid_contract';self.assertEqual(classification,expected,value)
            self.assertFalse(list((value['work']/'state/prefix').glob('*.json')));return
        result=value['result'];self.assertEqual(result['classification'],expected,value);self.assertTrue(value['sentinel_survived'],value);self.assertTrue(value['identities_gone'],value);self.assertIsNone(value['peer_error'],value)
        spawn=expected not in ('invalid_contract','ineligible','observer_not_ready','spawn_failed')
        self.assertEqual(result['spawned'],spawn,value);self.assertEqual(result['reaped'],spawn,value);self.assertEqual(result['cleanup'],'passed' if spawn else 'not_started',value)
        if spawn:
            self.assertGreaterEqual(value['trace_count'],1,value)
            self.assertLessEqual(result['stdout_bytes'],1048576);self.assertLessEqual(result['stderr_bytes'],1048576)
        if expected in ('success','observer_gap'):self.assertEqual(result['exit_code'],0,value);self.assertIsNone(result['signal'])
        if expected=='nonzero_exit':self.assertEqual(result['exit_code'],7)
        if expected=='signal_exit':self.assertEqual(result['signal'],15)
        if name=='descendant_pipe':self.assertGreaterEqual(value['trace_count'],2)
        if name=='malformed_child':self.assertEqual(result['stdout_bytes'],9)
        if expected=='success':self.assertTrue(result['observation_complete']);self.assertEqual(json.loads((value['work']/'.pear-journal.json').read_bytes())['state'],'clean')
        self.assertEqual(value['returncode'],0 if expected=='success' else 3 if expected in ('ineligible','observer_not_ready') else 4,value)
    def test_v2_empty_operations_launch(self):self.check('v2_success','success')
    def test_v2_setting_prepares_and_launches(self):self.check('v2_unsupported_setting','success')
    def test_detached_helper_scope_refuses_clean_journal(self):
        value=self.cases.execute('detached_helper','detached_helper');r=value['result']
        self.assertEqual(r['classification'],'cleanup_failed',value)
        self.assertTrue(r['reaped']);self.assertFalse(r['observation_complete'])
        self.assertEqual(value['trace_count'],2);self.assertTrue(value['identities_gone'])
        self.assertTrue(value['sentinel_survived']);self.assertIsNone(value['peer_error'])
        self.assertNotEqual(json.loads((value['work']/'.pear-journal.json').read_bytes())['state'],'clean')
    def test_all_original_ids_are_mapped_once(self):self.assertEqual(sorted(x['original_id'] for x in MAPPING),sorted(c['id'] for c in CORPUS['cases']))
    def test_early_eof_does_not_spin_or_wait_forever(self):self.check('early_eof','success')
    def test_final_burst_is_fully_counted_before_reap(self):self.check('final_burst','success')
for mapping in MAPPING:
    def test(self,m=mapping):self.check(m['original_id'],m['native_expected'])
    setattr(SupervisionTests,'test_original_'+mapping['original_id'],test)
