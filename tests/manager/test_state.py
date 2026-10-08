"""Canonical ownership, refusal and preservation-first manual recovery controls."""
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
from state_support import StateTestBase,inventory,BUILD

class StateTests(StateTestBase):
    def test_status_distinguishes_prepared_clean_and_incomplete(self):
        root=self.prepare();self.assertEqual(self.cli('status')[1]['reason'],'context_prepared')
        p,peer=self.spawn();self.finish(p,peer);self.assertEqual(self.cli('status')[1]['reason'],'context_clean')
        journal=root/'.pear-journal.json';value=json.loads(journal.read_bytes());value['state']='cleanup_pending';journal.write_text(json.dumps(value))
        self.assertEqual(self.cli('status')[1]['reason'],'context_incomplete')
        p,peer=self.spawn();self.assertEqual(self.finish(p,peer,success=False)['classification'],'context_incomplete')
    def test_dirty_recovery_allocates_new_context_and_preserves_all_old_bytes(self):
        old=self.prepare();p,peer=self.spawn();self.finish(p,peer)
        journal=old/'.pear-journal.json';value=json.loads(journal.read_bytes());value['state']='running';journal.write_text(json.dumps(value));before=inventory(old)
        code,result=self.cli('recover',id=None,**{'new-context':'fresh'});self.assertEqual(code,0,result);self.preserved(old,before)
        self.assertFalse(list((self.state/'contexts/fresh/state/saves-a').rglob('*.dat')))
        p,peer=self.spawn(id='fresh');self.finish(p,peer,id='fresh');self.preserved(old,before)
        self.assertNotEqual(self.cli('recover',id='a')[0],0)
    def test_select_previous_clean_context_preserves_other_profile(self):
        old=self.prepare();p,peer=self.spawn();self.finish(p,peer);before=inventory(old)
        other=self.prepare('b');other_before=inventory(other)
        code,result=self.cli('recover');self.assertEqual(code,0,result);self.assertEqual(result['reason'],'compatible_context_selected')
        self.preserved(old,before);self.preserved(other,other_before)
        p,peer=self.spawn();self.finish(p,peer);self.preserved(other,other_before)
    def test_wrong_profile_reuse_refuses_without_mutation(self):
        root=self.prepare();before=inventory(root);self.activate('b')
        self.assertNotEqual(self.cli('prepare','b','a')[0],0);self.preserved(root,before)
    def test_same_prefix_launch_and_mutation_are_exclusive(self):
        self.prepare();p,peer=self.spawn(mode='hold_ready');self.assertTrue(peer.hello_seen.wait(3))
        second,other=self.spawn();result=self.finish(second,other,success=False);self.assertEqual(result['classification'],'context_busy')
        self.assertEqual(self.cli('prepare')[1]['reason'],'context_busy');peer.release_ready.set();self.finish(p,peer)
    def test_replaced_lock_after_ready_request_refuses_before_spawn(self):
        root=self.prepare();p,peer=self.spawn(mode='hold_ready');self.assertTrue(peer.hello_seen.wait(3))
        lock=root/'state/prefix-a/.pear-prefix-lease';lock.rename(lock.with_name('old-lease'));lock.touch(mode=0o600);peer.release_ready.set()
        result=self.finish(p,peer,success=False);self.assertFalse(result['spawned']);self.assertEqual(result['classification'],'context_replaced')
        self.assertNotEqual(json.loads((root/'.pear-journal.json').read_bytes())['state'],'clean')
    def test_replaced_context_lock_refuses_even_when_new_inode_is_free(self):
        root=self.prepare();lock=root/'.pear-lease';lock.rename(root/'old-lease');lock.touch(mode=0o600)
        p,peer=self.spawn();self.assertFalse(self.finish(p,peer,success=False)['spawned'])
    def test_symlink_prefix_alias_refuses(self):
        root=self.prepare();prefix=root/'state/prefix-a';prefix.rename(root/'state/original');prefix.symlink_to('original',target_is_directory=True)
        p,peer=self.spawn();self.assertFalse(self.finish(p,peer,success=False)['spawned'])
    def test_hardlinked_cross_root_file_refuses(self):
        root=self.prepare();source=root/'state/prefix-a/config/options.json';os.link(source,root/'state/saves-a/alias')
        before=inventory(root);p,peer=self.spawn();self.assertFalse(self.finish(p,peer,success=False)['spawned']);self.preserved(root,before)
    def test_cache_identity_mismatch_refuses_without_deleting_cache(self):
        root=self.prepare();cache=root/'state/cache-a/.pear-cache.json';value=json.loads(cache.read_bytes());value['abi']='wrong-abi';cache.write_text(json.dumps(value));before=inventory(root)
        p,peer=self.spawn();self.assertFalse(self.finish(p,peer,success=False)['spawned']);self.preserved(root,before)
    def test_missing_cache_identity_refuses(self):
        root=self.prepare();(root/'state/cache-a/.pear-cache.json').unlink();p,peer=self.spawn();self.assertFalse(self.finish(p,peer,success=False)['spawned'])
    def test_wrong_family_metadata_refuses(self):
        root=self.prepare();path=root/'.pear-context.json';value=json.loads(path.read_bytes());value['binding']['family']='other-family';path.write_text(json.dumps(value));before=inventory(root)
        p,peer=self.spawn();self.assertFalse(self.finish(p,peer,success=False)['spawned']);self.preserved(root,before)
    def test_recovery_never_overwrites_existing_context(self):
        root=self.prepare();before=inventory(root);self.assertNotEqual(self.cli('recover',id=None,**{'new-context':'a'})[0],0);self.preserved(root,before)
    def interrupted(self,point,kill):
        old=self.prepare();before=inventory(old)
        p=subprocess.Popen([str(BUILD/'bin/state_probe'),str(self.state),'new',str(self.cases.entries['a']['policy']),point,'fail','owned'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True);self.live.append(p)
        with selectors.DefaultSelector() as selector:
            selector.register(p.stdout,selectors.EVENT_READ);self.assertTrue(selector.select(10))
        self.assertEqual(p.stdout.readline(),(point+'\n').encode())
        if kill:p.send_signal(signal.SIGKILL);out,err=p.communicate(timeout=5);self.assertEqual(p.returncode,-signal.SIGKILL)
        else:out,err=p.communicate(b'x',timeout=5);self.assertNotEqual(p.returncode,0);self.assertEqual(json.loads(out)['native_error'],5)
        self.assertEqual(err,b'');self.preserved(old,before)
        new=self.state/'contexts/new'
        if point=='before_publish':self.assertFalse(new.exists())
        else:
            self.assertTrue(new.is_dir());self.assertEqual(self.cli('status',id='new')[1]['reason'],'context_prepared')
            process,peer=self.spawn(id='new');self.finish(process,peer,id='new')
    def test_kill_before_context_publication(self):self.interrupted('before_publish',True)
    def test_kill_after_context_publication(self):self.interrupted('after_publish',True)
    def test_error_before_context_publication(self):self.interrupted('before_publish',False)
    def test_error_after_context_publication_is_uncertain(self):self.interrupted('after_publish',False)

    def test_replaced_prefix_directory_inode_refuses(self):
        root=self.prepare();prefix=root/'state/prefix-a';prefix.rename(root/'state/old-prefix');prefix.mkdir(mode=0o700)
        before=inventory(root);p,peer=self.spawn();self.assertFalse(self.finish(p,peer,success=False)['spawned']);self.preserved(root,before)
    def test_case_alias_does_not_create_or_select_another_context(self):
        root=self.prepare();before=inventory(root);code,result=self.cli('prepare',id='A');self.assertNotEqual(code,0,result);self.preserved(root,before)
    def test_settings_interruption_preserves_saves_and_leaves_dirty_state(self):
        root=self.prepare();save=root/'state/saves-a/alpha/save.dat';save.write_bytes(b'OWNED_PRESERVE_ME');before=inventory(root/'state/saves-a')
        p=subprocess.Popen([str(BUILD/'bin/state_probe'),str(self.state),'a',str(self.cases.entries['a']['policy']),'settings_written','fail','owned'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True);self.live.append(p)
        with selectors.DefaultSelector() as selector:
            selector.register(p.stdout,selectors.EVENT_READ);self.assertTrue(selector.select(10))
        self.assertEqual(p.stdout.readline(),b'settings_written\n');p.kill();p.communicate(timeout=5)
        self.preserved(root/'state/saves-a',before);self.assertEqual(self.cli('status')[1]['reason'],'context_incomplete')

    def test_previous_compatible_runtime_version_remains_executable(self):
        old=self.prepare();p,peer=self.spawn();self.finish(p,peer);before=inventory(old)
        current=self.prepare('a_next','next');process,observer=self.spawn('a_next','next');self.finish(process,observer,'a_next','next')
        self.assertEqual(json.loads((current/'state/prefix-a/last-run.json').read_bytes())['runtime_variant'],2)
        self.preserved(old,before)
        self.assertEqual(self.cli('recover')[0],0);p,peer=self.spawn();self.finish(p,peer)
        self.assertEqual(json.loads((old/'state/prefix-a/last-run.json').read_bytes())['runtime_variant'],1)
        self.assertEqual((old/'state/saves-a/alpha/save.dat').read_bytes(),b'alpha')
        self.cases.results.append({'id':'previous_runtime','current_variant':2,'recovered_variant':1,'old_save_preserved':True})

for name in ['unknown_saves','empty_saves','unknown_setting','unsupported_path','duplicate_setting','reserved_env','unknown_family','overlap']:
    def test(self,name=name):
        activation=self.cases.activate(name,self.state,prepare=False)
        if activation.returncode==0:code,result=self.cli('prepare',name,'bad');self.assertNotEqual(code,0,result)
        else:self.assertNotEqual(activation.returncode,0)
        self.assertFalse((self.state/'contexts/bad').exists())
    setattr(StateTests,'test_refuses_'+name,test)
