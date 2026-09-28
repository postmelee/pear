"""Independent common corpus for the native fixture managers; no runtime qualification."""
import argparse
import hashlib
import io
import json
import os
import re
import selectors
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time

REPO = Path(__file__).resolve().parents[2]
EXPERIMENT = REPO / 'experiments/manager'
sys.path.insert(0, str(REPO / 'tests/contracts'))
from fixture_factory import build_fixture, encoded, rewrite


def sha(data):
    return hashlib.sha256(data).hexdigest()


def create_bundle(root, build_root, case):
    """Create only self-owned executable/source and synthetic evidence under a fresh root."""
    root, build_root = Path(root), Path(build_root)
    fixture = build_fixture(root)
    # Discard unused synthetic observations. Only four records participate in this experiment.
    for name in list(fixture['paths']):
        if name not in ['lock', 'artifact', 'profile', 'request']:
            (root / fixture['paths'].pop(name)).unlink()
            fixture['records'].pop(name)
            fixture['refs'].pop(name)
    for name in ['runtime', 'prefix', 'saves', 'cache', 'logs']:
        (root / 'state' / name).mkdir(parents=True)
    child = root / 'blobs/fixture-child'
    shutil.copy2(build_root / 'bin/fixture-child', child)
    child_hash = sha(child.read_bytes())
    def blob(path, data, scope):
        (root / path).write_bytes(data)
        return {'ref_type':'blob','path':path,'digest':{'algorithm':'sha256','scope':scope,'value':sha(data)}}
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w', format=tarfile.USTAR_FORMAT) as archive:
        for name in ['child.c', 'native_bridge.c', 'native_bridge.h']:
            data = (EXPERIMENT / 'fixtures' / name).read_bytes()
            info = tarfile.TarInfo(name); info.size=len(data); info.mode=0o644; info.mtime=0
            archive.addfile(info, io.BytesIO(data))
    source = blob('blobs/source.tar', buffer.getvalue(), 'source_archive_bytes')
    metadata = json.loads((build_root / 'build.json').read_bytes())
    config = blob('blobs/build-config.json', encoded({'fixture_only':True,'target':'arm64-apple-macosx26.0','flags':['-O2','-std=c11','-Wall','-Wextra','-Werror'],'source_sha256':source['digest']['value'],'output_sha256':child_hash}), 'build_configuration_bytes')
    payload = {'ref_type':'blob','path':'blobs/fixture-child','digest':{'algorithm':'sha256','scope':'file_bytes','value':child_hash}}
    def lock(v):
        c=v['components'][0]
        c['source']['content']=source; c['source']['reason']='Deterministic tar of the self-owned C fixture and bridge.'
        c['build_context']['configuration']=config; c['build_context']['targets']=[{'role':'host','format':'mach_o','architecture':'arm64','triple':'arm64-apple-macosx26.0'}]
        c['build_context']['reason']='Owned C fixture compiled locally; not an upstream runtime.'
        v['toolchains'][0]['version']=re.search(r'clang version ([0-9.]+)', metadata['toolchains']['clang']).group(1)
        v['toolchains'][0]['sdk']=metadata['toolchains']['sdk']
    rewrite(root,fixture,'lock',lock)
    def artifact(v):
        v['files'][0].update(content=payload,format='mach_o')
        v['signing']['payload_digests']=[child_hash]
    rewrite(root,fixture,'artifact',artifact)
    def profile(v):
        v['executable']['path']='fixture.exe'; v['operations']=[]
        v['arguments']=[case['mode']]
        if case['mode']=='args': v['arguments'] += ['value with spaces','Unicode-λ-🍐']
        v['environment']=[{'key':'PEAR_FIXTURE_VALUE','value':'allowed'}] if case['mode']=='environment' else []
    rewrite(root,fixture,'profile',profile)
    apply_mutation(root,fixture,case['mutation'])
    return child_hash


def apply_mutation(root, fixture, mutation):
    if not mutation: return
    request=root / 'records/request.json'
    def edit(name, fn, sync=True): rewrite(root,fixture,name,fn,sync_cache=sync)
    def set_field(name, key, value): edit(name,lambda v:v.__setitem__(key,value))
    if mutation=='not_executable': (root/'blobs/fixture-child').chmod(0o600)
    elif mutation=='duplicate_key': request.write_bytes(request.read_bytes().replace(b'"schema_version": 1',b'"schema_version": 1, "schema_version": 1',1))
    elif mutation=='invalid_utf8': request.write_bytes(b'\xff'+request.read_bytes())
    elif mutation=='bom': request.write_bytes(b'\xef\xbb\xbf'+request.read_bytes())
    elif mutation in ['float','nonfinite','large_integer']:
        token={'float':b'1.0','nonfinite':b'NaN','large_integer':b'9007199254740992'}[mutation]
        request.write_bytes(request.read_bytes().replace(b'"schema_version": 1',b'"schema_version": '+token,1))
    elif mutation in ['percent_path','tilde_path']:
        target='blobs/terms%.txt' if mutation=='percent_path' else '~terms.txt'
        (root/target).write_bytes((root/'blobs/terms.txt').read_bytes())
        edit('lock',lambda v:v['components'][0]['terms']['references'][0].__setitem__('path',target))
    elif mutation=='oversize_reason': edit('lock',lambda v:v['compatibility_family'].__setitem__('reason','x'*2049))
    elif mutation=='oversize_key': set_field('request','x'*97,True)
    elif mutation=='control_string': edit('lock',lambda v:v['compatibility_family'].__setitem__('reason','contains\ncontrol'))
    elif mutation=='nested_duplicate_key': request.write_bytes(request.read_bytes().replace(b'"runtime": "state/runtime"',b'"runtime": "state/runtime", "runtim\\u0065": "state/runtime"',1))
    elif mutation=='boolean_version': set_field('request','schema_version',True)
    elif mutation=='unknown_version': set_field('request','schema_version',2)
    elif mutation=='unknown_kind': set_field('request','record_kind','future_kind')
    elif mutation=='unknown_field': set_field('request','unrecognized',True)
    elif mutation=='bad_digest':
        data=json.loads(request.read_bytes()); data['artifact']['digest']['value']='0'*64;request.write_bytes(encoded(data))
    elif mutation=='wrong_ref_kind': edit('request',lambda v:v['artifact'].__setitem__('record_kind','runtime_lock'))
    elif mutation=='family_mismatch': set_field('artifact','compatibility_family','other-family')
    elif mutation=='cache_mismatch': edit('request',lambda v:v['cache_identity'].__setitem__('lock_digest','0'*64),False)
    elif mutation=='missing_entry': set_field('request','entry_file_id','missing')
    elif mutation in ['path_traversal','absolute_path']: edit('request',lambda v:v['artifact'].__setitem__('path','../records/artifact.json' if mutation=='path_traversal' else str(root/'records/artifact.json')))
    elif mutation in ['blob_symlink','record_symlink']:
        path=root/('blobs/fixture-child' if mutation=='blob_symlink' else 'records/artifact.json'); target=path.with_suffix('.owned-target');path.rename(target);path.symlink_to(target.name)
    elif mutation=='state_symlink':
        path=root/'state/prefix';path.rmdir();path.symlink_to('saves',target_is_directory=True)
    elif mutation=='blob_fifo':
        path=root/'blobs/fixture-child';path.unlink();os.mkfifo(path)
    elif mutation=='record_too_large': request.write_bytes(request.read_bytes()+b' '*(256*1024))
    elif mutation=='deep_json': request.write_bytes(b'['*40+b'0'+b']'*40)
    elif mutation in ['source_bytes_changed','build_bytes_changed','terms_bytes_changed','payload_changed']:
        path=root/'blobs'/dict(source_bytes_changed='source.tar',build_bytes_changed='build-config.json',terms_bytes_changed='terms.txt',payload_changed='fixture-child')[mutation]
        with path.open('ab') as file:file.write(b'changed')
    elif mutation=='blob_hardlink':
        (root/'blobs/terms-alias.txt').hardlink_to(root/'blobs/terms.txt')
        edit('lock',lambda v:v['components'][0]['terms']['references'].append({**v['components'][0]['terms']['references'][0],'path':'blobs/terms-alias.txt'}))
    elif mutation=='overlapping_roots': edit('request',lambda v:v['roots'].__setitem__('cache','state/prefix'))
    elif mutation=='untrusted_executable_digest': pass # Independent caller trust pin is changed at invocation.
    elif mutation=='unsupported_operations': edit('profile',lambda v:v.__setitem__('operations',[{'operation':'set_setting','root':'prefix','path':'config/options.json','key':'fixture_flag','value':True}]))
    elif mutation=='unknown_source': edit('lock',lambda v:v['components'][0]['source'].update(status='unknown',url=None,immutable_ref=None,content=None,reason='Unobserved fixture source.'))
    elif mutation=='research_context':
        for name in fixture['paths']: set_field(name,'record_context','research')
    elif mutation=='wrong_purpose': set_field('request','purpose','qualification_run')
    else: raise ValueError('unknown case mutation')


def oracle_result(python, root, context):
    command=[str(python),str(REPO/'tests/contracts/validate.py'),'--bundle-root',str(root),'--entry','records/request.json','--context',context,'--purpose','fixture_launch']
    run=subprocess.run(command,capture_output=True,timeout=10)
    result=json.loads(run.stdout)
    if run.returncode not in [0,1,3] or run.stderr: raise ValueError('oracle execution failed')
    return result


def disappeared(build_root, trace):
    value=json.loads(trace.read_bytes())
    if set(value)!={'pid','pgid','started_sec','started_usec','native'} or value['native'] is not True: return False
    if not all(type(value[k]) is int and value[k]>0 for k in ['pid','pgid','started_sec']): return False
    deadline=time.monotonic()+2
    while time.monotonic()<deadline:
        check=subprocess.run([str(build_root/'bin/fixture-child'),'--probe-identity',str(value['pid']),str(value['started_sec']),str(value['started_usec'])],capture_output=True,timeout=2)
        if check.returncode==0: return True
        if check.returncode!=1: return False
        time.sleep(.02)
    return False


RESULT_KEYS={'experiment_version','candidate','fixture_only','runtime_eligible','host_architecture','translated','classification','spawned','reaped','cleanup','exit_code','signal','stdout_bytes','stderr_bytes'}

def check_result(result, case, returncode):
    errors=[]
    expected=case['expected']
    if type(result.get('experiment_version')) is not int or result['experiment_version']!=1:errors.append('result_version')
    if set(result)!=RESULT_KEYS: errors.append('result_shape')
    if result.get('classification')!=expected: errors.append('classification')
    expected_code=0 if expected=='success' else 1 if expected=='invalid_contract' else 3 if expected in ['ineligible','observer_not_ready'] else 4
    if returncode!=expected_code: errors.append('exit_status')
    if result.get('fixture_only') is not True or result.get('runtime_eligible') is not False:errors.append('fixture_scope')
    if result.get('host_architecture')!='arm64' or result.get('translated') is not False:errors.append('native_host')
    spawn=expected not in ['invalid_contract','ineligible','observer_not_ready','spawn_failed']
    if result.get('spawned') is not spawn or result.get('reaped') is not spawn or result.get('cleanup')!=('passed' if spawn else 'not_started'):errors.append('lifecycle')
    if expected in ['success','observer_gap','child_output_invalid'] and (type(result.get('exit_code')) is not int or result['exit_code']!=0 or result.get('signal') is not None):errors.append('normal_exit_identity')
    if expected=='nonzero_exit' and result.get('exit_code')!=7:errors.append('nonzero_identity')
    if expected=='signal_exit' and result.get('signal')!=signal.SIGTERM:errors.append('signal_identity')
    for field in ['stdout_bytes','stderr_bytes']:
        if type(result.get(field)) is not int or not 0<=result[field]<=1024*1024:errors.append('output_count')
    return errors


def verify_build(build_root):
    metadata=json.loads((build_root/'build.json').read_bytes())
    if metadata.get('fixture_only') is not True or metadata.get('runtime_eligible') is not False:
        raise ValueError('incorrect build scope')
    for name in ['fixture-child','rust-manager','swift-manager']:
        if sha((build_root/'bin'/name).read_bytes())!=metadata['binaries'][name]['sha256']:
            raise ValueError('binary changed since build')
    current=set()
    for language in ['fixtures','rust','swift']:
        for source in (EXPERIMENT/language).rglob('*'):
            if not source.is_file() or any(part.startswith('.') or part=='__pycache__' for part in source.relative_to(EXPERIMENT).parts):continue
            if source.name=='cases.json':continue
            current.add(str(source.relative_to(REPO)))
            if metadata['sources'].get(str(source.relative_to(REPO)))!=sha(source.read_bytes()):
                raise ValueError('native source changed; rebuild before case execution')
    recorded={path for path in metadata['sources'] if any(path.startswith('experiments/manager/'+language+'/') for language in ['fixtures','rust','swift']) and path!='experiments/manager/fixtures/cases.json'}
    if current!=recorded:raise ValueError('native source file set changed; rebuild before case execution')
    return metadata


def capture_bounded(process, timeout):
    """Bound harness capture too; preserve the unreaped leader until signaling."""
    buffers={process.stdout:bytearray(),process.stderr:bytearray()}
    failure=None;deadline=time.monotonic()+timeout
    with selectors.DefaultSelector() as selector:
        for stream in buffers:selector.register(stream,selectors.EVENT_READ)
        while selector.get_map() and failure is None:
            remaining=deadline-time.monotonic()
            if remaining<=0:failure='outer_deadline';break
            for key,_ in selector.select(min(.1,remaining)):
                data=os.read(key.fileobj.fileno(),8192)
                if not data:selector.unregister(key.fileobj);continue
                current=buffers[key.fileobj]
                current.extend(data[:max(0,16385-len(current))])
                if len(current)>16384:failure='outer_output_limit';break
        if failure:
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            except PermissionError:process.kill()
        try:process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill();process.wait(timeout=2);failure='outer_deadline'
    for stream in buffers:stream.close()
    return bytes(buffers[process.stdout]),bytes(buffers[process.stderr]),failure


def run_cases(build_root, python, only=None):
    build_root=build_root.resolve(); python=python.absolute()
    verify_build(build_root)
    corpus=json.loads((EXPERIMENT/'fixtures/cases.json').read_bytes())
    selected=[c for c in corpus['cases'] if not only or c['id']==only]
    if not selected: raise ValueError('no matching case')
    work=Path(tempfile.mkdtemp(prefix='cases-',dir=build_root)).resolve()
    sentinel=subprocess.Popen([str(build_root/'bin/fixture-child'),'sentinel'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    results=[]
    try:
        for index,case in enumerate(selected):
            for candidate in (['rust','swift'] if index%2==0 else ['swift','rust']):
                root=work/(case['id']+'-'+candidate)
                fixture_hash=create_bundle(root,build_root,case)
                oracle=oracle_result(python,root,case['oracle_context'])
                errors=[]
                if case['oracle']=='invalid' and oracle['record_valid']:errors.append('oracle_expected_invalid')
                if case['oracle']=='eligible' and not oracle['eligible']:errors.append('oracle_expected_eligible')
                if case['oracle']=='ineligible' and (not oracle['record_valid'] or oracle['eligible']):errors.append('oracle_expected_ineligible')
                if case['oracle']=='valid' and not oracle['record_valid']:errors.append('oracle_expected_valid')
                args=[str(build_root/'bin'/f'{candidate}-manager'),'--bundle-root',str(root),'--entry','records/request.json','--fixture-sha256','0'*64 if case['mutation']=='untrusted_executable_digest' else fixture_hash,'--timeout-ms',str(case['timeout_ms']),'--output-limit',str(corpus['output_limit']),'--observer-ready','yes' if case['observer_ready'] else 'no','--observer-gap','yes' if case['observer_gap'] else 'no']
                started=time.monotonic()
                process=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={**os.environ,'PEAR_SECRET_SENTINEL':'PRIVATE_FIXTURE_MARKER_93c8'},start_new_session=True)
                stdout,stderr,capture_failure=capture_bounded(process,corpus['outer_deadline_seconds'])
                if capture_failure:errors.append(capture_failure)
                elapsed=time.monotonic()-started
                if len(stdout)>16384 or stderr or b'PRIVATE_FIXTURE_MARKER_93c8' in stdout or str(root).encode() in stdout: errors.append('privacy_or_output_bound')
                try: result=json.loads(stdout); errors+=check_result(result,case,process.returncode)
                except (ValueError,TypeError): result={};errors.append('invalid_result_json')
                if result.get('candidate')!=candidate:errors.append('candidate_identity')
                traces=list((root/'state/prefix').glob('*.json')) if not (root/'state/prefix').is_symlink() else []
                if result.get('spawned') and case['expected']!='output_limit' and not any(p.name=='child.json' for p in traces):errors.append('missing_child_observation')
                if case['mode']=='descendant_pipe' and not any(p.name=='descendant.json' for p in traces):errors.append('missing_descendant_observation')
                if not result.get('spawned') and traces:errors.append('unexpected_execution')
                for trace in traces:
                    if not disappeared(build_root,trace):errors.append('owned_identity_remains_or_unverified')
                alive=sentinel.poll() is None
                if not alive:errors.append('unrelated_sentinel_exited')
                row={'case':case['id'],'candidate':candidate,'passed':not errors,'errors':errors,'result':result,'oracle':oracle,'observed_trace_count':len(traces),'owned_identities_gone':bool(traces) and not any(e=='owned_identity_remains_or_unverified' for e in errors),'unrelated_sentinel_alive':alive,'bounded_completion':elapsed<corpus['outer_deadline_seconds']}
                results.append(row)
                print(json.dumps({'case':case['id'],'candidate':candidate,'passed':not errors,'errors':errors}),flush=True)
        report={'version':1,'fixture_only':True,'runtime_eligible':False,'case_count':len(selected),'execution_count':len(results),'passed':all(r['passed'] for r in results),'results':results,'trace_scope':'Direct-child reaping reported by each candidate; child and descendant creation identities independently disappear. Grandchild reaping belongs to the OS. No module collector or game observation.'}
        report['corpus_sha256']=sha((EXPERIMENT/'fixtures/cases.json').read_bytes())
        report['build_metadata_sha256']=sha((build_root/'build.json').read_bytes())
        report['harness_sha256']=sha(Path(__file__).read_bytes())
        serialized=json.dumps(report,indent=2)+'\n'
        (work/'results.json').write_text(serialized)
        (build_root/'case-results.json').write_text(serialized)
        return report
    finally:
        if sentinel.poll() is None: sentinel.terminate()
        sentinel.wait(timeout=3)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-root',type=Path,required=True)
    parser.add_argument('--oracle',type=Path,required=True)
    select=parser.add_mutually_exclusive_group(required=True)
    select.add_argument('--all',action='store_true');select.add_argument('--case')
    args=parser.parse_args()
    try: return 0 if run_cases(args.build_root,args.oracle,args.case)['passed'] else 1
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:
        print(json.dumps({'passed':False,'harness_error':type(error).__name__}));return 1

if __name__=='__main__': sys.exit(main())
