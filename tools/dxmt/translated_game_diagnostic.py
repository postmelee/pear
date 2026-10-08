#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Private, bounded owned-game startup diagnosis using the existing #8 protocol.

No Steam credentials, app-id override, API stub or game qualification. The signed
runtime is admitted unchanged; proprietary inputs remain outside its fixtures.
"""
from pathlib import Path
import argparse,fcntl,hashlib,json,os,re,shutil,sys,time,uuid
if not __package__:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.fex.common import REPO,need
from tools.fex import memory_wine_runtime as signing,memory_wine_run as supervisor
from tools.fex.integration_run import admission
METAL_ENV = {'MTL_DEBUG_LAYER': '1', 'MTL_DEBUG_LAYER_ERROR_MODE': 'assert',
             'MTL_DEBUG_LAYER_WARNING_MODE': 'nslog', 'MTL_SHADER_VALIDATION': '1',
             'MTL_SHADER_VALIDATION_FAIL_MODE': 'zerofill',
             'MTL_SHADER_VALIDATION_REPORT_TO_STDERR': '1'}
from tools.dxmt.translated_inputs import fact, read
H=lambda raw:hashlib.sha256(raw).hexdigest()

def game_copy(source,snapshot,destination):
    import subprocess
    value=read(snapshot)
    need(value['app_id']==3405340 or str(value['app_id'])=='3405340','game_app_identity')
    rows=[r for d in value['platforms']['windows'] for r in d['files'] if not r['flags'] & 64]
    need(len(rows)==69,'game_manifest_file_count')
    destination.mkdir(mode=0o700);facts=[]
    for row in rows:
        rel=Path(row['path'])
        need(not rel.is_absolute() and '..' not in rel.parts,'game_manifest_path')
        path=source/rel
        need(path.resolve().is_relative_to(source) and not path.is_symlink(),'game_source_alias')
        raw=path.read_bytes()
        need(len(raw)==row['size'] and hashlib.sha1(raw).hexdigest()==row['sha1'],'game_manifest_changed')
        target=destination/rel;target.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run(['/bin/cp','-c',str(path),str(target)],check=True,timeout=30)
        need(target.read_bytes()==raw,'game_clone_changed');facts.append(fact(path))
    return facts


def run(runtime,output,reuse,game,snapshot,seed):
    import subprocess
    from tools.dxmt.translated_surface_runtime import admit as admit_surface
    from tools.dxmt.translated_check import device
    from tools.fex.integration_run import prefix_inventory
    runtime=Path(runtime).resolve(strict=True);reuse=Path(reuse).resolve(strict=True)
    output=Path(output).absolute();game=Path(game).resolve(strict=True)
    need(output.parent==REPO/'.build/task8' and not output.exists(),'integration_fresh_run')
    value=admit_surface(runtime)
    need(shutil.disk_usage(REPO).free>=5*1024**3,'game_diagnostic_storage')
    output.mkdir(mode=0o700);(output/'producer.py').write_bytes(Path(__file__).read_bytes())
    source_files=game_copy(game,Path(snapshot).resolve(strict=True),output/'game')
    print('current authorization',flush=True);admission(runtime,value,output/'before',reuse)
    work=output/'run';work.mkdir();prefix=work/'prefix'
    seed=Path(seed).resolve(strict=True);device(seed,runtime)
    template=seed/'run/prefix';inventory=prefix_inventory(template)
    inf=runtime/signing.PAYLOAD/'share/wine/wine.inf'
    need((template/'.update-timestamp').read_text().strip()==str(int(inf.stat().st_mtime)),'game_prefix_update')
    subprocess.run(['/bin/cp','-cRp',str(template),str(prefix)],check=True,timeout=30)
    need(prefix_inventory(prefix)==inventory,'game_prefix_clone')
    # Only the synthetic prefix is cloned. No authenticated Steam state or saves.
    for p in (work/'work',work/'work/tmp',work/'home'):p.mkdir(mode=0o700)
    result=dict(scope='owned_megabonk_startup_diagnostic',kind='game_startup_observation',
                diagnostic_only=True,game_qualified=False,guest_execution_qualified=False,
                runtime_sha256=H((runtime/'runtime.json').read_bytes()),
                source_files=source_files,snapshot_ref=fact(snapshot),
                prefix_origin=dict(seed_ref=fact(seed/'case.json'),inventory=inventory),
                steam_account_flow='unperformed; normal game Steam checks retained')
    with supervisor.supervision(reuse) as (life,helpers):
        nonce=uuid.uuid4().hex;packet=supervisor.assessment_packet(value)
        session=helpers.api.APISession(work,runtime,packet,nonce,suite='api-abi',case_id='first-dispatch')
        env=supervisor.environment(work/'work',prefix,nonce,str(work/'home'))
        env['WINEDEBUG']='-all,+loaddll,+seh,+module'
        env.update(METAL_ENV)
        env['PEAR_METAL_PIPELINE_OBSERVE']='1'
        paths={k:runtime/v for k,v in value['entrypoints'].items()}
        read_fd=control=None;error=None;outcome='not_started';start=time.monotonic();deadline=start+120
        remaining=lambda cap:max(0,min(cap,deadline-time.monotonic()))
        launches=[]
        def launch(role,args,environment,**kwargs):
            child=session.launch(role,args,environment,**kwargs)
            launches.append({'role':role,'argv':args,'environment':environment,'pid':child.pid});return child
        print('starting owned Megabonk diagnostic (120 second bound)',flush=True)
        try:
            graphical=helpers.api.graphical_session()
            need(graphical=={'status':0,'available':True},'translated_graphical_session')
            result['graphical_session']=graphical
            read_fd,control=os.pipe()
            sentinel=launch('sentinel',[str(paths['sentinel']),str(read_fd)],env,pass_fds=(read_fd,))
            os.close(read_fd);read_fd=None
            need(session.wait_for(lambda:b'\n' in session.streams[('sentinel','stdout')]['data'],remaining(5)),'integration_sentinel_start')
            helpers.base.validate_helper(helpers.base.parse_lines(session,'sentinel')[0],'pear_sentinel_ready',sentinel)
            server=launch('server',[str(paths['server']),'-f','-p'],env,event_pipe=True)
            need(session.wait_for(lambda:any(r.get('event')=='server_ready' for r in session.events['server']) or server.exited,remaining(30)) and not server.exited,'integration_server_start')
            loader_env={**env,'PEAR_STAGE3_CONTROL':session.endpoint,'PEAR_WINE_ABI_FIXTURE':'1',
                        'PEAR_BOOTSTRAP_SERVER_PID':str(server.pid),'WINEDLLOVERRIDES':'d3d11,dxgi,d3d10core,winemetal=b;mscoree='}
            session.output=work/'work'
            try:loader=launch('loader',[str(paths['bootstrap_helper']),'--exec-4k',str(paths['loader']),str(output/'game/Megabonk.exe'),'-force-d3d11','-screen-fullscreen','0','-screen-width','960','-screen-height','540','-logFile',str(output/'Player.log')],loader_env,allowed_paths=[paths['bootstrap_helper'],paths['loader']])
            finally:session.output=work
            # A definitive owner refusal identifies a failed startup. Stop
            # waiting for the known failing unwind path; retain the exact log
            # and use the same owned cleanup/sentinel/authorization checks.
            refusal=None
            def finished():
                nonlocal refusal
                stream=session.streams.get(('loader','stderr'),{})
                match=re.search(rb'Pear FEX init (?:ECGate\.(?:enter|fill|exit)|GuestSyscall\.exit): status=(?!00000000)[0-9a-fA-F]{8} domain=\d+ code=-?\d+',
                                bytes(stream.get('data',b''))[-65536:])
                if match: refusal=match.group().decode('ascii')
                if not match:
                    guard=re.search(rb'[^\n]*(?:Pear source guard refused|Pear FEX assertion:)[^\n]*',bytes(stream.get('data',b''))[-65536:])
                    if guard: refusal=guard.group().decode('utf-8',errors='replace')
                return loader.exited or refusal is not None
            completed=session.wait_for(finished,remaining(120))
            outcome='owner_refused' if refusal else 'exited' if completed else 'timeout'
            result['observed_owner_refusal']=refusal
        except BaseException as exc:error={'type':type(exc).__name__,'code':getattr(exc,'code',str(exc))};outcome='error'
        finally:
            before,cleanup,sentinel_cleanup,logs,survived,cleanup_errors=life.cleanup_session(session,control,read_fd,work)
        result.update(outcome=outcome,error=error,stream_error=session.failure,events=session.events,logs=logs,
                      cleanup=cleanup,sentinel_cleanup=sentinel_cleanup,sentinel_survived=survived,cleanup_errors=cleanup_errors,
                      pre_cleanup=before,elapsed_ms=round((time.monotonic()-start)*1000),launches=launches,
                      registrations=list(session.observer.registrations.values()),signal_observations=session.observer.signal_observations,
                      processes={role:{'identity':child.identity,'exit_code':child.exit_code,'reaped':child.reaped,'allowed_paths':sorted(child.allowed_paths)} for role,child in session.children.items()})
        (output/'case.json').write_text(json.dumps(result,indent=2)+'\n')
    print('execution ended; verifying unchanged authorization',flush=True)
    admission(runtime,value,output/'after',reuse)
    result['authorization_before_after_passed']=True
    (output/'case.json').write_text(json.dumps(result,indent=2)+'\n')
    result['original_files_unchanged']=all(fact(row['path'])==row for row in source_files)
    result['runtime_unchanged']=H((runtime/'runtime.json').read_bytes())==result['runtime_sha256']
    (output/'case.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('outcome','error','original_files_unchanged','runtime_unchanged','game_qualified')}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('runtime','output','reuse','game','snapshot','seed'):p.add_argument('--'+key,required=True)
    a=p.parse_args()
    with open('/private/tmp/pear-native-compilation.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        run(a.runtime,a.output,a.reuse,a.game,a.snapshot,a.seed)
