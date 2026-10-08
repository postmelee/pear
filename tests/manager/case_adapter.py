"""Task #9 glue around the preserved #3 producer, mutations, capture and identities."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tarfile
import tempfile
import time
import uuid
from support import REPO,experiment_build,experiment_cases
from fixture_factory import encoded,rewrite
from synthetic_peer import Peer
from v2_fixture import upgrade_fixture
BUILD=REPO/os.environ.get('PEAR_MANAGER_BUILD','.build/task9/stage3')
BINARY=BUILD/'bin/pear-manager'
CORPUS=json.loads((REPO/'experiments/manager/fixtures/cases.json').read_bytes())

def reconstruct(root):
    records={p.stem:json.loads(p.read_bytes()) for p in (root/'records').glob('*.json')}
    refs={name:{'ref_type':'record','path':'records/'+name+'.json','record_kind':r['record_kind'],'schema_version':r['schema_version'],'digest':{'algorithm':'sha256','scope':'exact_utf8_file_bytes','value':experiment_build.digest(root/'records'/ (name+'.json'))}} for name,r in records.items()}
    return {'records':records,'refs':refs,'paths':{k:r['path'] for k,r in refs.items()},'policy':{'approved_record_digests':[]}}
def policy(fixture):
    return {'policy_version':1,'approved_record_digests':[r['digest']['value'] for r in fixture['refs'].values()],'trusted_reviewers':[],'required_checks':[],'required_processes':[],'required_host_modules':[],'required_guest_modules':[],'module_expectations':[],'host':fixture['records']['request']['configuration']['host'],'allowed_signing_scopes':['development'],'max_age_days':30}
class Cases:
    def __init__(self,extra=(),only=None):
        self.tmp=tempfile.TemporaryDirectory(prefix='pear-task9-supervision-');self.root=Path(self.tmp.name).resolve();self.source=self.root/'source';self.source.mkdir();self.mount=self.root/'media';self.mount.mkdir();self.image=self.root/'payload.dmg';self.mounted=False;self.entries={};self.commands=[];self.results=[]
        self.retained=REPO/'.build/task9/runs'/('stage3-'+uuid.uuid4().hex);self.retained.mkdir(parents=True)
        self.build_receipt=json.loads((BUILD/'build.json').read_bytes())
        for path,digest in self.build_receipt['sources'].items():
            if experiment_build.digest(REPO/path)!=digest:raise AssertionError('stale build source '+path)
        factory=self.root/'factory';(factory/'bin').mkdir(parents=True);shutil.copy2(BUILD/'bin/fixture-entry',factory/'bin/fixture-child');shutil.copy2(BUILD/'build.json',factory/'build.json')
        for case in [c for c in [*CORPUS['cases'],*extra] if only is None or c['id'] in only]:
            shutil.copy2(BUILD/'bin'/case.get('entry_binary','fixture-entry'),factory/'bin/fixture-child')
            name=case['id'];source=self.source/name;clean={**case,'mutation':None};experiment_cases.create_bundle(source,factory,clean);f=reconstruct(source)
            original=(source/'blobs/source.tar').read_bytes();buffer=io.BytesIO(original)
            with tarfile.open(fileobj=buffer,mode='a') as tar:
                for relative,archive_name in [('tests/manager/fixtures/supervision_entry.c','supervision_entry.c'),('tests/manager/fixtures/state.c','state.c'),('manager/native/bridge.c','manager_bridge.c'),('manager/native/bridge.h','manager_bridge.h')]:
                    data=(REPO/relative).read_bytes();info=tarfile.TarInfo(archive_name);info.size=len(data);info.mtime=0;info.mode=0o644;tar.addfile(info,io.BytesIO(data))
            (source/'blobs/source.tar').write_bytes(buffer.getvalue());rewrite(source,f,'lock',lambda v:v['components'][0]['source']['content']['digest'].update(value=experiment_build.digest(source/'blobs/source.tar')))
            config_path=source/'blobs/build-config.json';config=json.loads(config_path.read_bytes());config.update(entry_variant=case.get('entry_binary','fixture-entry'),source_sha256=experiment_build.digest(source/'blobs/source.tar'),wrapper_sha256=experiment_build.digest(REPO/'tests/manager/fixtures/supervision_entry.c'),manager_bridge_sha256=experiment_build.digest(REPO/'manager/native/bridge.c'));config_path.write_bytes(encoded(config));rewrite(source,f,'lock',lambda v:v['components'][0]['build_context']['configuration']['digest'].update(value=experiment_build.digest(config_path)))
            experiment_cases.apply_mutation(source,f,case['mutation'])
            if case.get('schema_version')==2:upgrade_fixture(source,f);f=reconstruct(source)
            if case.get('profile_file'):
                public=json.loads((REPO/case['profile_file']).read_bytes())
                rewrite(source,f,'profile',lambda value:value.update(public))
            if case.get('profile_change'):rewrite(source,f,'profile',case['profile_change'])
            if case.get('roots'):
                rewrite(source,f,'request',lambda value:value.update(roots=case['roots']))
                for path in case['roots'].values():(source/path).mkdir(parents=True,exist_ok=True)
            selected=policy(f)
            if case['mutation']=='untrusted_executable_digest':selected['approved_record_digests']=[]
            policy_path=self.root/(name+'-policy.json');policy_path.write_bytes(encoded(selected))
            # Invalid/nonregular inputs must refuse before media admission. Keep these
            # originals writable rather than copying a FIFO into an image creator.
            result=subprocess.run([str(BINARY),'inspect','--bundle-root',str(source),'--entry','records/request.json','--context',case['oracle_context']],capture_output=True,timeout=10)
            valid=json.loads(result.stdout).get('record_valid')
            if not valid:
                invalid=self.root/('invalid-'+name);source.rename(invalid);source=invalid
            self.entries[name]={'case':case,'source':source,'root':self.mount/name if valid else source,'policy':policy_path,'valid':valid}
        self.tool(['/usr/bin/hdiutil','create','-format','UDRO','-fs','HFS+','-volname','PearTask9Stage3','-srcfolder',str(self.source),str(self.image)]);self.image.chmod(0o600)
        self.tool(['/usr/bin/hdiutil','attach','-readonly','-nobrowse','-mountpoint',str(self.mount),str(self.image)]);self.mounted=True
    def tool(self,args):
        p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True);out,err,failure=experiment_cases.capture_bounded(p,60)
        self.commands.append({'argv':args,'returncode':p.returncode,'capture_failure':failure,'stdout':out.decode(errors='replace'),'stderr':err.decode(errors='replace')});(self.retained/'commands.json').write_text(json.dumps(self.commands,indent=2)+'\n')
        if p.returncode or failure:raise AssertionError((p.returncode,failure,err))
    def close(self):
        if self.mounted:self.tool(['/usr/bin/hdiutil','detach',str(self.mount)]);self.mounted=False
        (self.retained/'results.json').write_text(json.dumps({'build_receipt_sha256':experiment_build.digest(BUILD/'build.json'),'corpus_sha256':experiment_build.digest(REPO/'experiments/manager/fixtures/cases.json'),'results':self.results},indent=2)+'\n');self.tmp.cleanup()
    def state(self):
        state=self.root/('state-'+uuid.uuid4().hex);state.mkdir(mode=0o700);work=state/'contexts/default';pass
        return state,work
    def activate(self,name,state,prepare=True):
        item=self.entries[name]
        result=subprocess.run([str(BINARY),'activate','--bundle-root',str(item['root']),'--entry','records/request.json','--context',item['case']['oracle_context'],'--state-root',str(state),'--policy',str(item['policy'])],capture_output=True,timeout=10)
        if result.returncode==0 and prepare and not (state/'contexts/default/.pear-context.json').exists():
            result=subprocess.run([str(BINARY),'prepare','--state-root',str(state),'--profile','records/profile.json','--context-id','default','--policy',str(item['policy'])],capture_output=True,timeout=10)
        return result
    def spawn(self,name,state,peer,timeout=None):
        item=self.entries[name];fd=peer.client.fileno();peer.work=state/'contexts/default';peer.start()
        args=[str(BINARY),'launch','--state-root',str(state),'--request','records/request.json','--policy',str(item['policy']),'--context-id','default','--observer-fd',str(fd),'--timeout-ms',str(timeout or item['case']['timeout_ms']),'--output-limit','4096']
        p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,pass_fds=(fd,),start_new_session=True,env={**os.environ,'PEAR_SECRET_SENTINEL':'PRIVATE_FIXTURE_MARKER_93c8'});peer.client.close();return p
    def execute(self,name,peer_mode=None):
        state,work=self.state();item=self.entries[name];case=item['case'];activation=self.activate(name,state)
        if activation.returncode:
            result={'phase':'admission','returncode':activation.returncode,'result':json.loads(activation.stdout)};self.results.append({'id':name,**result});return {**result,'work':work,'state':state}
        mode=peer_mode or ('silent' if not case['observer_ready'] else 'gap' if case['observer_gap'] else 'normal');peer=Peer(mode)
        sentinel=subprocess.Popen([str(BUILD/'bin/fixture-child'),'sentinel'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            p=self.spawn(name,state,peer);started=time.monotonic();out,err,failure=experiment_cases.capture_bounded(p,CORPUS['outer_deadline_seconds'])
            sentinel_survived=sentinel.poll() is None
            if failure:raise AssertionError(('outer_watchdog',name,failure))
            if err or b'PRIVATE_FIXTURE_MARKER_93c8' in out or len(out)>8192:raise AssertionError('private/unbounded output')
            result=json.loads(out);traces=list((work/'state/prefix').glob('*.json'));gone=all(experiment_cases.disappeared(BUILD,t) for t in traces)
            value={'phase':'supervision','returncode':p.returncode,'result':result,'elapsed_seconds':time.monotonic()-started,'sentinel_survived':sentinel_survived,'trace_count':len(traces),'identities_gone':gone,'peer_error':peer.error,'work':work,'state':state}
            self.results.append({'id':name,**{k:v for k,v in value.items() if k not in ('work','state')}});return value
        finally:
            peer.close()
            if sentinel.poll() is None:sentinel.kill()
            sentinel.wait(timeout=3)
