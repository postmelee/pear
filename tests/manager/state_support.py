"""Shared owned media/profile harness; original source/capture helpers stay intact."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import unittest
from case_adapter import Cases,CORPUS,BUILD,BINARY,REPO,experiment_cases
from synthetic_peer import Peer

def inventory(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file() and not p.is_symlink()}

def setting(value,key='fixture_flag',path='config/options.json'):
    return {'operation':'set_setting','root':'prefix','path':path,'key':key,'value':value}

def cases():
    entries=[]
    for letter in ['a','b']:
        entries.append({**CORPUS['cases'][0],'id':letter,'mode':'state','schema_version':2,'profile_file':f'profiles/fixtures/{letter}.json','roots':{name:f'state/{name}-{letter}' for name in ['runtime','prefix','saves','cache','logs']}})
    for name,change in [
        ('unknown_saves',lambda v:v.update(save_paths=[],save_inventory_status={'status':'unknown','reason':'Owned negative control.'})),
        ('empty_saves',lambda v:v.update(save_paths=[])),
        ('unknown_setting',lambda v:v.update(operations=[setting(2,key='dxmt_log_level')])),
        ('unsupported_path',lambda v:v.update(operations=[setting(True,path='elsewhere/options.json')])),
        ('duplicate_setting',lambda v:v.update(operations=[setting(True),setting(False)])),
        ('reserved_env',lambda v:v.update(environment=[{'key':'WINEPREFIX','value':'private'}])),
        ('unknown_family',lambda v:v.update(compatibility_family=None)),
    ]:entries.append({**entries[0],'id':name,'profile_change':change})
    entries.append({**entries[0],'id':'overlap','roots':{name:'state/same' for name in ['runtime','prefix','saves','cache','logs']}})
    entries.append({**entries[0],'id':'a_next','entry_binary':'fixture-entry-next'})
    return entries

class StateTestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        entries=cases();cls.cases=Cases(entries,only=[c['id'] for c in entries]);cls.runtime_before=inventory(cls.cases.mount);cls.image_before=hashlib.sha256(cls.cases.image.read_bytes()).hexdigest()
    @classmethod
    def tearDownClass(cls):
        after=inventory(cls.cases.mount);image=hashlib.sha256(cls.cases.image.read_bytes()).hexdigest()
        cls.cases.results.append({'id':'runtime_preservation','before':cls.runtime_before,'after':after,'image_before':cls.image_before,'image_after':image})
        cls.cases.close()
        if after!=cls.runtime_before or image!=cls.image_before:raise AssertionError('runtime bytes changed')
    def setUp(self):
        self.state,self.default=self.cases.state();self.live=[];self.peers=[]
        self.sentinel=subprocess.Popen([str(BUILD/'bin/fixture-child'),'sentinel'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    def tearDown(self):
        alive=self.sentinel.poll() is None
        for peer in self.peers:peer.release_ready.set()
        for process in self.live:
            if process.poll() is None:process.kill()
            process.communicate(timeout=5)
        for peer in self.peers:peer.close()
        if self.sentinel.poll() is None:self.sentinel.kill()
        self.sentinel.wait(timeout=3);self.assertTrue(alive,'unrelated sentinel must survive')
    def preserved(self,root,before):
        after=inventory(root);self.assertEqual(after,before)
        digest=lambda value:hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
        self.cases.results.append({'id':self.id().split('.')[-1],'preserved_root':str(root.relative_to(self.state)),'file_count':len(before),'before_inventory_sha256':digest(before),'after_inventory_sha256':digest(after)})
    def cli(self,command,letter='a',id='a',**extra):
        args=[str(BINARY),command,'--state-root',str(self.state)]
        options={'context-id':id} if command=='status' else {'context-id':id,'profile':'records/profile.json','policy':str(self.cases.entries[letter]['policy'])}
        options.update(extra)
        for key,value in options.items():
            if value is not None:args.extend(['--'+key,str(value)])
        p=subprocess.run(args,capture_output=True,timeout=10)
        self.assertEqual(p.stderr,b'');self.assertLess(len(p.stdout),8192)
        result=json.loads(p.stdout);self.cases.results.append({'id':self.id().split('.')[-1],'command':command,'returncode':p.returncode,'result':result})
        return p.returncode,result
    def activate(self,letter='a'):
        p=self.cases.activate(letter,self.state,prepare=False);self.assertEqual(p.returncode,0,p.stdout)
    def prepare(self,letter='a',id=None):
        self.activate(letter);code,result=self.cli('prepare',letter,id or letter);self.assertEqual(code,0,result)
        return self.state/'contexts'/(id or letter)
    def spawn(self,letter='a',id=None,mode='normal'):
        id=id or letter;peer=Peer(mode);peer.work=self.state/'contexts'/id;peer.start();self.peers.append(peer)
        p=subprocess.Popen([str(BINARY),'launch','--state-root',str(self.state),'--request','records/request.json','--policy',str(self.cases.entries[letter]['policy']),'--context-id',id,'--observer-fd',str(peer.client.fileno())],stdout=subprocess.PIPE,stderr=subprocess.PIPE,pass_fds=(peer.client.fileno(),),start_new_session=True,env={**os.environ,'PEAR_SECRET_SENTINEL':'PRIVATE_FIXTURE_MARKER_93c8'})
        peer.client.close();self.live.append(p);return p,peer
    def finish(self,p,peer,letter='a',id=None,success=True):
        out,err,failure=experiment_cases.capture_bounded(p,10);self.assertIsNone(failure);self.assertEqual(err,b'');self.assertNotIn(b'PRIVATE_FIXTURE_MARKER_93c8',out)
        result=json.loads(out)
        if success:
            self.assertEqual(p.returncode,0,result);self.assertTrue(result['reaped']);self.assertTrue(result['observation_complete']);self.assertEqual(result['cleanup'],'passed')
            trace=self.state/'contexts'/(id or letter)/self.cases.entries[letter]['case']['roots']['prefix']/'identity.json';self.assertTrue(experiment_cases.disappeared(BUILD,trace));self.assertIsNone(peer.error)
        self.cases.results.append({'id':self.id().split('.')[-1],'command':'launch','result':result});return result
