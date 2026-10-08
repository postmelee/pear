"""Real native API checks and parser negatives; no activation or game execution."""
import hashlib
import json
import os
from pathlib import Path
import selectors
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import build as manager_build
from support import REPO, experiment_build, experiment_cases


class FoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = (REPO / os.environ.get('PEAR_MANAGER_BUILD', '.build/task9/stage1')).resolve()
        cls.binary = cls.build / 'bin/foundation'
        metadata = json.loads((cls.build / 'build.json').read_bytes())
        if experiment_build.digest(cls.binary) != metadata['binaries']['foundation']['sha256']:
            raise AssertionError('native output does not match build receipt')
        for name,digest in metadata['sources'].items():
            if experiment_build.digest(REPO / name) != digest: raise AssertionError('stale build input: '+name)
        if metadata['binaries']['foundation']['slices'] != 'arm64': raise AssertionError('non-native fixture')
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.addCleanup(self.tmp.cleanup)
    def invoke(self, *args, data=None):
        result = subprocess.run([str(self.binary),*map(str,args)],input=data,capture_output=True,timeout=5)
        self.assertLessEqual(len(result.stdout)+len(result.stderr),16384)
        return result
    def test_build_output_refuses_other_tasks_and_parent_traversal(self):
        for path in (Path('.build/task3/prototypes'), Path('.build/task9'), Path('.build/task9/../other'), Path('/tmp/task9')):
            with self.subTest(path=path), self.assertRaises(ValueError): manager_build.checked_output(path)
    def test_build_output_refuses_symlink_and_preserves_existing_data(self):
        (self.root/'.build/task9').mkdir(parents=True)
        destination=self.root/'outside';destination.mkdir();(destination/'keep').write_bytes(b'preserve')
        (self.root/'.build/task9/stage1').symlink_to(destination,target_is_directory=True)
        with patch.object(manager_build,'REPO',self.root), self.assertRaises(ValueError):
            manager_build.checked_output(Path('.build/task9/stage1'))
        self.assertEqual((destination/'keep').read_bytes(),b'preserve')
    def test_streaming_hash_empty_split_and_multichunk(self):
        for data in (b'', b'abc', bytes(range(256))*12345):
            with self.subTest(size=len(data)):
                path=self.root/'payload'; path.write_bytes(data)
                result=self.invoke('hash',path,len(data))
                self.assertEqual(result.returncode,0,result.stdout)
                self.assertEqual(json.loads(result.stdout),{'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
    def test_hash_limits_missing_symlink_and_nonregular_keep_numeric_error(self):
        path=self.root/'payload'; path.write_bytes(b'abc')
        link=self.root/'alias'; link.symlink_to('payload')
        for candidate,limit in ((path,2),(self.root/'missing',10),(link,10),(self.root,10)):
            with self.subTest(path=candidate.name):
                result=self.invoke('hash',candidate,limit)
                self.assertEqual(result.returncode,1)
                message=json.loads(result.stdout)
                self.assertEqual(message['reason'],'native_failure')
                self.assertIsInstance(message['native_error'],int)
                self.assertNotIn(str(self.root).encode(),result.stdout)
    def test_staging_is_unique_private_and_beneath_parent(self):
        names=[]
        for _ in range(2):
            result=self.invoke('stage',self.root)
            self.assertEqual(result.returncode,0)
            name=result.stdout.decode().strip(); names.append(name)
            self.assertTrue(name.startswith('stage.'))
            self.assertNotIn('/',name)
            self.assertEqual(stat.S_IMODE((self.root/name).stat().st_mode),0o700)
        self.assertNotEqual(*names)
    def test_staging_rejects_symlink_parent(self):
        link=self.root/'alias'; link.symlink_to(self.root,target_is_directory=True)
        self.assertEqual(self.invoke('stage',link).returncode,1)
        self.assertEqual(list(self.root.iterdir()),[link])
    def test_identity_and_bad_pid(self):
        result=self.invoke('identity'); self.assertEqual(result.returncode,0)
        self.assertGreater(json.loads(result.stdout)['seconds'],0)
        bad=self.invoke('identity',-1);self.assertEqual(bad.returncode,1)
        self.assertIsInstance(json.loads(bad.stdout)['native_error'],int)
    def test_closed_diagnostic(self):
        value=json.loads(self.invoke('diagnostic').stdout)
        self.assertEqual(set(value),{'diagnostic_version','phase','reason','native_error'})
        self.assertEqual(value['reason'],'native_failure')
    def test_parser_valid_unicode_and_boundary_integer(self):
        for data in (b'{}',b'null',b'[9007199254740991,-9007199254740991]',b'{"s":"\\uD83C\\uDF50"}', '{"s":"Unicode-λ-🍐"}'.encode()):
            with self.subTest(data=data): self.assertEqual(self.invoke('parse',data=data).returncode,0)
    def test_parser_rejects_malformed_bounds_and_redacts(self):
        secret=b'private-token-do-not-export'
        cases=[b'{"x":1,"x":2}',b'{"x":1,"\\u0078":2}',b'\xff',b'\xef\xbb\xbf{}',
               b'1.0',b'1e1',b'NaN',b'9007199254740992',b'"\\ud800"',b'"line\\nfeed"',
               b'['*34+b'0'+b']'*34,b'['+b'0,'*8192+b'0]',b'"'+b'x'*2049+b'"',
               b'{"'+b'x'*97+b'":0}',b' '*262145,b'{"secret":"'+secret+b'",}']
        for index,data in enumerate(cases):
            with self.subTest(case=index):
                result=self.invoke('parse',data=data)
                self.assertEqual(result.returncode,1)
                self.assertEqual(json.loads(result.stdout)['reason'],'invalid_input')
                self.assertNotIn(secret,result.stdout)
    def holder(self,path,mode):
        process=subprocess.Popen([str(self.binary),'lock',str(path),mode],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        def cleanup():
            if process.poll() is None: process.kill()
            process.communicate(timeout=2)
        self.addCleanup(cleanup)
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout,selectors.EVENT_READ)
            self.assertTrue(selector.select(3),'lock holder did not become ready')
        self.assertEqual(process.stdout.readline(),b'locked\n')
        return process
    def test_exclusive_contention_advisory_write_and_release(self):
        path=self.root/'lease';path.write_bytes(b'original')
        owner=self.holder(path,'exclusive-hold')
        self.assertEqual(self.invoke('lock',path,'exclusive').stdout,b'busy\n')
        self.assertEqual(self.invoke('lock',path,'shared').stdout,b'busy\n')
        path.write_bytes(b'arbitrary writer succeeds')
        self.assertEqual(path.read_bytes(),b'arbitrary writer succeeds')
        owner.communicate(b'x',timeout=2);self.assertEqual(owner.returncode,0)
        self.assertEqual(self.invoke('lock',path,'exclusive-drop').stdout,b'locked\n')
        self.assertEqual(self.invoke('lock',path,'exclusive').stdout,b'locked\n')
    def test_shared_lease_and_process_death_release(self):
        path=self.root/'lease';path.touch()
        owner=self.holder(path,'shared-hold')
        self.assertEqual(self.invoke('lock',path,'shared').stdout,b'locked\n')
        self.assertEqual(self.invoke('lock',path,'exclusive').stdout,b'busy\n')
        owner.kill();owner.communicate(timeout=2)
        self.assertEqual(self.invoke('lock',path,'exclusive').stdout,b'locked\n')
        # A released advisory lease is deliberately not asserted to mean cleanup.
if __name__ == '__main__': unittest.main()
