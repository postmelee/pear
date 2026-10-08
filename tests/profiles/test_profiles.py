"""Actual distinct settings/save use by two generic versioned fixture profiles."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'manager'))
from state_support import StateTestBase,inventory

class ProfileTests(StateTestBase):
    def test_sequential_relaunch_preserves_distinct_settings_and_save_bytes(self):
        roots={letter:self.prepare(letter) for letter in ['a','b']}
        for round in range(2):
            for letter,marker,flag in [('a','alpha',True),('b','beta',False)]:
                other='b' if letter=='a' else 'a';before=inventory(roots[other]);p,peer=self.spawn(letter);self.finish(p,peer,letter)
                self.preserved(roots[other],before)
                record=json.loads((roots[letter]/f'state/prefix-{letter}/last-run.json').read_bytes())
                self.assertEqual((record['marker'],record['setting'],record['previous_save']),(marker,flag,bool(round)))
                self.assertEqual((roots[letter]/f'state/saves-{letter}/{marker}/save.dat').read_bytes(),marker.encode())
                self.cases.results.append({'id':'profile_observation','profile':letter,'round':round,'marker':record['marker'],'setting':record['setting'],'previous_save':record['previous_save']})
    def test_concurrent_contexts_use_their_own_selected_runtime_and_data(self):
        for letter in ['a','b']:self.prepare(letter)
        a,pa=self.spawn('a');b,pb=self.spawn('b')
        self.finish(a,pa,'a');self.finish(b,pb,'b')
        records=[json.loads((self.state/f'contexts/{letter}/state/prefix-{letter}/identity.json').read_bytes()) for letter in ['a','b']]
        start_us=[r['started_sec']*1000000+r['started_usec'] for r in records]
        difference=abs(start_us[0]-start_us[1]);self.assertLess(difference,500000)
        self.cases.results.append({'id':'actual_concurrency','start_difference_usec':difference,'each_successful_child_minimum_lifetime_usec':500000,'overlap_observed':True})
        for letter,marker in [('a','alpha'),('b','beta')]:
            self.assertEqual((self.state/f'contexts/{letter}/state/saves-{letter}/{marker}/save.dat').read_bytes(),marker.encode())
    def test_prepare_updates_only_allowlisted_setting_and_preserves_saves(self):
        root=self.prepare();p,peer=self.spawn();self.finish(p,peer)
        saves=inventory(root/'state/saves-a');path=root/'state/prefix-a/config/options.json';path.write_text('{"fixture_flag":false,"user_note":"preserve"}')
        code,result=self.cli('prepare');self.assertEqual(code,0,result)
        self.assertEqual(json.loads(path.read_bytes()),{'fixture_flag':True,'user_note':'preserve'});self.preserved(root/'state/saves-a',saves)
    def test_changed_setting_refuses_launch_before_child(self):
        root=self.prepare();(root/'state/prefix-a/config/options.json').write_text('{"fixture_flag":false}')
        p,peer=self.spawn();result=self.finish(p,peer,success=False);self.assertFalse(result['spawned']);self.assertNotEqual(p.returncode,0)

    def test_preexisting_unrelated_save_bytes_are_never_replaced(self):
        root=self.prepare();path=root/'state/saves-a/alpha/save.dat';path.write_bytes(b'PREEXISTING_OWNED_SAVE');before=inventory(root/'state/saves-a')
        self.assertEqual(self.cli('prepare')[0],0);self.preserved(root/'state/saves-a',before)
        p,peer=self.spawn();result=self.finish(p,peer,success=False);self.assertEqual(result['classification'],'nonzero_exit');self.assertEqual(result['exit_code'],75);self.assertTrue(result['reaped']);self.preserved(root/'state/saves-a',before)
