"""Actual UDRO media and native dylib controls; no Wine, Steam, or game execution."""
import copy
import errno
import hashlib
import json
import os
from pathlib import Path
import selectors
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from support import REPO,experiment_cases,experiment_build
sys.path.insert(0,str(REPO/'tests/contracts'))
from fixture_factory import build_fixture,encoded,rewrite
from v2_fixture import upgrade_fixture
BUILD=REPO/os.environ.get('PEAR_MANAGER_BUILD','.build/task9/stage2')
BINARY=BUILD/'bin/pear-manager'
PROBE=BUILD/'bin/activation_probe'

class ActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch=tempfile.TemporaryDirectory(prefix='pear-task9-activation-')
        cls.base=Path(cls.scratch.name).resolve();cls.mounted=[];cls.commands=[];cls.results=[]
        cls.retained=REPO/'.build/task9/runs'/('stage2-'+uuid.uuid4().hex);cls.retained.mkdir(parents=True)
        cls.receipt=json.loads((BUILD/'build.json').read_bytes())
        for path,digest in cls.receipt['sources'].items():
            if experiment_build.digest(REPO/path)!=digest: raise AssertionError('stale source: '+path)
        try:
            cls.payloads={}
            for variant in ('approved','alternate','external','undeclared'):
                work=cls.base/variant;work.mkdir();source=work/'source';f=upgrade_fixture(source,build_fixture(source))
                built=BUILD/'fixtures'/('approved' if variant=='undeclared' else variant)
                shutil.copytree(built,source/'payload')
                def artifact(v):
                    v['files']=[]
                    for name,file_id in [('entry','native-entry'),('lib/libfixture.dylib','native-library')]:
                        if variant=='undeclared' and name.startswith('lib/'):continue
                        v['files'].append({'file_id':file_id,'content':{'ref_type':'blob','path':'payload/'+name,'digest':{'algorithm':'sha256','scope':'file_bytes','value':experiment_build.digest(source/'payload'/name)}},'role':'host','format':'mach_o','architecture':'arm64'})
                    v['signing']['payload_digests']=[x['content']['digest']['value'] for x in v['files']]
                rewrite(source,f,'artifact',artifact);rewrite(source,f,'request',lambda v:v.update(entry_file_id='native-entry'))
                policy=work/'policy.json';policy.write_bytes(encoded(f['policy']));image=work/'payload.dmg'
                cls.tool(['/usr/bin/hdiutil','create','-format','UDRO','-fs','HFS+','-volname','PearTask9Stage2','-srcfolder',str(source),str(image)])
                image.chmod(0o600);ancestor=work/'lookup';ancestor.mkdir();mount=ancestor/'media';mount.mkdir()
                cls.tool(['/usr/bin/hdiutil','attach','-readonly','-nobrowse','-mountpoint',str(mount),str(image)]);cls.mounted.append(mount)
                cls.payloads[variant]={'before_hashes':{name:experiment_build.digest(mount/'payload'/name) for name in ('entry','lib/libfixture.dylib')},'image_sha256':experiment_build.digest(image),'root_identity':{'device':mount.stat().st_dev,'inode':mount.stat().st_ino},'root':mount,'image':image,'policy':policy,'fixture':f,'source':source}
        except BaseException:
            cls.clean();raise
    @classmethod
    def tool(cls,args):
        p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,env={'PATH':'/usr/bin:/bin:/usr/sbin:/sbin','LC_ALL':'C'})
        out,err,failure=experiment_cases.capture_bounded(p,60)
        cls.commands.append({'argv':args,'returncode':p.returncode,'stdout':out.decode(errors='replace'),'stderr':err.decode(errors='replace'),'capture_failure':failure})
        (cls.retained/'commands.json').write_text(json.dumps(cls.commands,indent=2)+'\n')
        if p.returncode or failure:raise AssertionError(('required_media_gate',p.returncode,failure,err))
        return out
    @classmethod
    def clean(cls):
        errors=[]
        inventories=[]
        for variant,payload in getattr(cls,'payloads',{}).items():
            current={name:experiment_build.digest(payload['root']/'payload'/name) for name in ('entry','lib/libfixture.dylib')}
            image=experiment_build.digest(payload['image'])
            inventories.append({'variant':variant,'before':payload['before_hashes'],'after':current,'image_sha256':image,'root_identity':payload['root_identity']})
            if current!=payload['before_hashes'] or image!=payload['image_sha256']:errors.append('owned fixture bytes changed')
        (cls.retained/'inventories.json').write_text(json.dumps(inventories,indent=2)+'\n')
        for mount in reversed(cls.mounted):
            try:cls.tool(['/usr/bin/hdiutil','detach',str(mount)])
            except BaseException as e:errors.append(repr(e))
        (cls.retained/'summary.json').write_text(json.dumps({'task':9,'stage':2,'build_receipt_sha256':experiment_build.digest(BUILD/'build.json'),'results':cls.results,'cleanup_errors':errors,'game_execution':False,'runtime_qualified':False},indent=2)+'\n')
        if errors:raise AssertionError(errors)
        cls.scratch.cleanup()
    @classmethod
    def tearDownClass(cls):cls.clean()
    def setUp(self):
        self.state=self.base/('state-'+uuid.uuid4().hex);self.state.mkdir(mode=0o700)
    def tearDown(self):
        selection=self.state/'selection.json'
        self.results.append({'case':self.id(),'completed':True,'selection_sha256':experiment_build.digest(selection) if selection.is_file() else None,'retained_staging_count':len(list(self.state.glob('stage.*')))})
    def args(self,variant='approved',root=None):
        p=self.payloads[variant]
        return [str(root or p['root']),'records/request.json',str(self.state),str(p['policy'])]
    def activate(self,variant='approved',root=None):
        base,entry,state,policy=self.args(variant,root)
        result=subprocess.run([str(BINARY),'activate','--bundle-root',base,'--entry',entry,'--context','fixture','--state-root',state,'--policy',policy],capture_output=True,timeout=30)
        self.assertLess(len(result.stdout)+len(result.stderr),8192);return result
    def probe(self,variant='approved',mode='execute',boundary='none'):
        p=subprocess.Popen([str(PROBE),*self.args(variant),mode,boundary],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        self.addCleanup(self.stop,p);return p
    def stop(self,p):
        if p.poll() is None:os.killpg(p.pid,signal.SIGKILL)
        p.communicate(timeout=5)
    def ready(self,p,label=b'admitted\n'):
        with selectors.DefaultSelector() as selector:
            selector.register(p.stdout,selectors.EVENT_READ)
            self.assertTrue(selector.select(30),'native admission deadline')
        line=p.stdout.readline();self.assertEqual(line,label)
    def finish(self,p,marker=b'approved!'):
        out,err=p.communicate(b'x',timeout=15);self.assertEqual(p.returncode,0,(out,err));self.assertEqual(out,marker);self.assertEqual(err,b'');self.results.append({'case':self.id(),'native_exit':p.returncode,'observed_marker':out.decode('ascii')})
    def test_actual_readonly_and_internal_dylib_execution(self):
        payload=self.payloads['approved']
        for path in (payload['root']/'payload/entry',payload['root']/'payload/lib/libfixture.dylib'):
            with self.assertRaises(OSError) as caught:path.write_bytes(b'changed')
            self.assertEqual(caught.exception.errno,errno.EROFS);self.results.append({'case':self.id(),'write_target':path.name,'write_errno':caught.exception.errno})
        p=self.probe();self.ready(p);self.finish(p)
    def test_alternate_library_is_an_observable_negative_control(self):
        p=self.probe('alternate');self.ready(p);self.finish(p,b'alternate')
    def test_writable_and_chmod_only_payloads_refuse_without_selection(self):
        p=self.payloads['approved'];source=p['source'];source.chmod(0o555)
        try:
            result=self.activate(root=source);self.assertIn(b'payload_not_readonly',result.stdout);self.assertNotEqual(result.returncode,0);self.assertFalse((self.state/'selection.json').exists())
        finally:source.chmod(0o755)
    def test_external_rpath_and_undeclared_dependency_refuse(self):
        for variant,reason in [('external',b'unsupported_load_path'),('undeclared',b'undeclared_dependency')]:
            result=self.activate(variant);self.assertNotEqual(result.returncode,0,result.stdout);self.assertIn(reason,result.stdout);self.assertFalse((self.state/'selection.json').exists())
    def test_writable_backing_media_permissions_refuse(self):
        image=self.payloads['approved']['image'];image.chmod(0o666)
        try:self.assertIn(b'unowned_or_writable_media',self.activate().stdout)
        finally:image.chmod(0o600)
    def test_atomic_selection_exact_policy_and_payload_identity(self):
        result=self.activate();self.assertEqual(result.returncode,0,result.stdout)
        record=json.loads((self.state/'selection.json').read_bytes());p=self.payloads['approved']
        self.assertEqual(record['root_device'],str(p['root_identity']['device']));self.assertEqual(record['root_inode'],str(p['root_identity']['inode']));self.assertEqual(record['policy_sha256'],experiment_build.digest(p['policy']));self.assertEqual(record['media_sha256'],experiment_build.digest(p['image']));self.assertEqual(record['artifact_sha256'],p['fixture']['refs']['artifact']['digest']['value']);self.assertEqual((self.state/'selection.json').stat().st_mode&0o777,0o600)
    def test_prepublication_failures_preserve_previous_selection(self):
        self.assertEqual(self.activate().returncode,0);before=(self.state/'selection.json').read_bytes()
        for boundary in ('staged','written','durable'):
            with self.subTest(boundary=boundary):
                p=self.probe('alternate','activate',boundary);self.ready(p,(boundary+'\n').encode());out,err=p.communicate(b'x',timeout=15);self.assertNotEqual(p.returncode,0);self.assertIn(b'injected_failure',out);self.assertEqual((self.state/'selection.json').read_bytes(),before)
    def test_prepublication_sigkill_preserves_previous_selection(self):
        self.assertEqual(self.activate().returncode,0);before=(self.state/'selection.json').read_bytes()
        for boundary in ('staged','written','durable'):
            p=self.probe('alternate','activate',boundary);self.ready(p,(boundary+'\n').encode());os.killpg(p.pid,signal.SIGKILL);p.communicate(timeout=5);self.assertEqual((self.state/'selection.json').read_bytes(),before)
    def test_postpublication_failure_reports_uncertain_complete_selection(self):
        self.assertEqual(self.activate().returncode,0)
        p=self.probe('alternate','activate','published');self.ready(p,b'published\n');out,_=p.communicate(b'x',timeout=15);self.assertIn(b'selection_commit_uncertain',out)
        self.assertEqual(json.loads((self.state/'selection.json').read_bytes())['artifact_sha256'],self.payloads['alternate']['fixture']['refs']['artifact']['digest']['value'])
    def test_concurrent_activation_retains_open_version_and_lease(self):
        self.assertEqual(self.activate().returncode,0);p=self.probe();self.ready(p)
        digest=self.payloads['approved']['fixture']['refs']['artifact']['digest']['value'];lease=self.state/('lease-'+digest)
        locked=subprocess.run([str(BUILD/'bin/foundation'),'lock',str(lease),'exclusive'],capture_output=True,timeout=5);self.assertEqual(locked.stdout,b'busy\n')
        self.assertEqual(self.activate('alternate').returncode,0);self.finish(p)
        self.assertEqual(json.loads((self.state/'selection.json').read_bytes())['artifact_sha256'],self.payloads['alternate']['fixture']['refs']['artifact']['digest']['value'])
        released=subprocess.run([str(BUILD/'bin/foundation'),'lock',str(lease),'exclusive-drop'],capture_output=True,timeout=5);self.assertEqual(released.stdout,b'locked\n')
    def test_busy_activation_refuses_and_preserves_old_selection(self):
        self.assertEqual(self.activate().returncode,0);before=(self.state/'selection.json').read_bytes()
        p=self.probe('alternate','activate','durable');self.ready(p,b'durable\n');result=self.activate();self.assertIn(b'state_busy',result.stdout);self.assertEqual((self.state/'selection.json').read_bytes(),before);p.communicate(b'x',timeout=15)
    def test_ancestor_replacement_uses_original_entry_and_library_or_refuses(self):
        selected=self.payloads['approved'];p=self.probe();self.ready(p);ancestor=selected['root'].parent;moved=ancestor.with_name('retained-lookup')
        ancestor.rename(moved);self.mounted[self.mounted.index(selected['root'])]=moved/'media'
        try:
            shutil.copytree(self.payloads['alternate']['source'],ancestor/'media')
            out,err=p.communicate(b'x',timeout=15)
            self.assertNotIn(b'alternate',out);self.assertNotIn(b'alternate',err)
            if p.returncode==0:self.assertEqual(out,b'approved!')
            else:self.assertNotEqual(p.returncode,0)
            self.results.append({'case':'ancestor_replacement_outcome','returncode':p.returncode,'original_marker':out==b'approved!'})
        finally:
            shutil.rmtree(ancestor);moved.rename(ancestor);self.mounted[self.mounted.index(moved/'media')]=selected['root']
    def test_write_space_and_sync_faults_preserve_old_selection_and_errno(self):
        self.assertEqual(self.activate().returncode,0);before=(self.state/'selection.json').read_bytes()
        for boundary,number in [('write-enospc',errno.ENOSPC),('write-eio',errno.EIO),('sync-eio',errno.EIO)]:
            p=self.probe('alternate','activate',boundary);out,err=p.communicate(timeout=15)
            self.assertNotEqual(p.returncode,0);self.assertEqual(json.loads(out)['native_error'],number);self.assertEqual((self.state/'selection.json').read_bytes(),before)
    def test_postpublication_sigkill_leaves_complete_selection(self):
        self.assertEqual(self.activate().returncode,0);p=self.probe('alternate','activate','published');self.ready(p,b'published\n');os.killpg(p.pid,signal.SIGKILL);p.communicate(timeout=5)
        self.assertEqual(json.loads((self.state/'selection.json').read_bytes())['artifact_sha256'],self.payloads['alternate']['fixture']['refs']['artifact']['digest']['value'])
    def test_corrupt_policy_preserves_existing_selection(self):
        self.assertEqual(self.activate().returncode,0);before=(self.state/'selection.json').read_bytes();p=self.payloads['alternate'];policy=p['policy'];old=policy.read_bytes()
        try:
            value=json.loads(old);value['approved_record_digests']=[];policy.write_bytes(encoded(value))
            result=self.activate('alternate');self.assertNotEqual(result.returncode,0);self.assertIn(b'identity_not_trusted',result.stdout);self.assertEqual((self.state/'selection.json').read_bytes(),before)
        finally:policy.write_bytes(old)
    def test_state_private_permission_and_symlink_lock_refusal(self):
        self.state.chmod(0o755)
        try:self.assertIn(b'state_root_not_private',self.activate().stdout)
        finally:self.state.chmod(0o700)
        other=self.base/'unrelated-sentinel';other.write_bytes(b'preserve');(self.state/'activation.lock').symlink_to(other)
        self.assertNotEqual(self.activate().returncode,0);self.assertEqual(other.read_bytes(),b'preserve')
