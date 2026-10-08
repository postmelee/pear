#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""#8 owned fixture execution adapted from #6 pear_run.py.

Retains the existing authorization, APISession, bootstrap, timeout and cleanup
protocol. Only candidate admission, fixture selection and Metal settings change.
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
from tools.dxmt.translated_inputs import fact, read, admit
from tools.dxmt.translated_runtime import admit_build
H=lambda raw:hashlib.sha256(raw).hexdigest()

def run(runtime,output,reuse,case_id,sync_diagnostic=False,memory_diagnostic=False,seed=None):
    runtime=Path(runtime).resolve(strict=True);reuse=Path(reuse).resolve(strict=True);output=Path(output).absolute()
    need(output.parent==REPO/'.build/task8' and not output.exists(),'integration_fresh_run')
    value=json.loads((runtime/'runtime.json').read_text());need(value['passed'] is True,'integration_runtime_not_prepared')
    need(value['kind']=='translated_graphics_development_runtime' and case_id in value['fixtures'],'cpu_fixture_selection')
    need(fact(value['build_ref']['path'])==value['build_ref'],'translated_build_changed')
    admit_build(Path(value['build_ref']['path']).parent)
    need(value['producer_sha256']==H((REPO/'tools/dxmt/translated_runtime.py').read_bytes()),'translated_runtime_producer')
    if 'owner_correction_ref' in value:
        from tools.dxmt.translated_owner import admit as admit_owner
        need(fact(value['owner_correction_ref']['path'])==value['owner_correction_ref'],'translated_owner_runtime_ref')
        admit_owner(Path(value['owner_correction_ref']['path']).parent)
    if 'fex_correction_ref' in value:
        from tools.dxmt.translated_fex import admit_build as admit_fex
        need(fact(value['fex_correction_ref']['path'])==value['fex_correction_ref'],'translated_fex_runtime_ref')
        admit_fex(Path(value['fex_correction_ref']['path']).parent)
    if 'rendering_overlay' in value:
        from tools.dxmt.translated_render_runtime import admit as admit_rendering
        admit_rendering(runtime)
    need(case_id!='rendering' or 'rendering_overlay' in value,'rendering_runtime_required')
    fixture=value['fixtures'][case_id]
    need(H((runtime/fixture['path']).read_bytes())==fixture['sha256'],'cpu_fixture_changed')
    value['entrypoints']['fixture_pe']=fixture['path']
    output.mkdir(mode=0o700);(output/'producer.py').write_bytes(Path(__file__).read_bytes())
    print('current authorization',flush=True);admission(runtime,value,output/'before',reuse)
    work=output/'run';work.mkdir();prefix=work/'prefix'
    prefix_origin=None
    need(shutil.disk_usage(REPO).free>=4*1024**3,'cpu_cold_prefix_storage')
    if seed:
        import subprocess
        from tools.dxmt.translated_check import device
        from tools.fex.integration_run import prefix_inventory
        seed=Path(seed).resolve(strict=True);device(seed,runtime)
        template=seed/'run/prefix';inventory=prefix_inventory(template)
        inf=runtime/signing.PAYLOAD/'share/wine/wine.inf'
        need((template/'.update-timestamp').read_text().strip()==str(int(inf.stat().st_mtime)),
             'translated_prefix_update')
        subprocess.run(['/bin/cp','-cRp',str(template),str(prefix)],check=True,timeout=30)
        need(prefix_inventory(prefix)==inventory,'translated_prefix_clone')
        prefix_origin={'seed_ref':fact(seed/'case.json'),'inventory':inventory,'cold_prefix_initialization':False}
    else:prefix.mkdir(mode=0o700)
    for p in (work/'work',work/'work/tmp'):p.mkdir(mode=0o700)
    result={'scope':'translated_graphics','kind':'translated_graphics_observation','fixture_id':case_id,'fixture_sha256':fixture['sha256'],'passed':False,'runtime_sha256':H((runtime/'runtime.json').read_bytes()),
            'diagnostic_only':sync_diagnostic or memory_diagnostic or value.get('diagnostic_only',False),'expected_exit':value.get('expected_exit',42),'guest_execution_qualified':False,'stage3_complete':False,'prefix_origin':prefix_origin}
    with supervisor.supervision(reuse) as (life,helpers):
        nonce=uuid.uuid4().hex;packet=supervisor.assessment_packet(value)
        session=helpers.api.APISession(work,runtime,packet,nonce,suite='api-abi',case_id='first-dispatch')
        env=supervisor.environment(work/'work',prefix,nonce,os.environ.get('HOME'))
        env['WINEDEBUG']='-all,+loaddll,+seh,+module'
        env.update(METAL_ENV)
        if case_id=='rendering':
            env.update(PEAR_METAL_PIPELINE_OBSERVE='1',MTL_SHADER_VALIDATION_DUMP_PIPELINES='1',MTL_SHADER_VALIDATION_DEFAULT_STATE='all',
                       MTL_SHADER_VALIDATION_ENABLE_ERROR_REPORTING='1',MTL_SHADER_VALIDATION_GLOBAL_MEMORY='1',
                       MTL_SHADER_VALIDATION_TEXTURE_USAGE='1')
        if sync_diagnostic:env['WINEDEBUG']='-all,+loaddll,+seh,+sync,+thread'
        if memory_diagnostic:env['WINEDEBUG']='-all,+virtual,+module,+seh'
        paths={k:runtime/v for k,v in value['entrypoints'].items()}
        read_fd=control=None;error=None;outcome='not_started';start=time.monotonic();deadline=start+(30 if sync_diagnostic or memory_diagnostic else 180)
        remaining=lambda cap:max(0,min(cap,deadline-time.monotonic()))
        launches=[]
        def launch(role,args,environment,**kwargs):
            child=session.launch(role,args,environment,**kwargs)
            launches.append({'role':role,'argv':args,'environment':environment,'pid':child.pid});return child
        print('starting owned x64 fixture',flush=True)
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
            try:loader=launch('loader',[str(paths['bootstrap_helper']),'--exec-4k',str(paths['loader']),str(paths['fixture_pe'])],loader_env,allowed_paths=[paths['bootstrap_helper'],paths['loader']])
            finally:session.output=work
            # A definitive owner refusal already disproves this fixture. Stop
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
            completed=session.wait_for(finished,remaining(180))
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
    print(json.dumps({'outcome':result['outcome'],'error':result['error'],'loader_exit':result['processes'].get('loader',{}).get('exit_code'),
                      'cleanup_complete':result['cleanup']['complete'],'sentinel_survived':result['sentinel_survived'],'guest_execution_qualified':False}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('runtime','output','reuse','suite'):p.add_argument('--'+key,required=True)
    p.add_argument('--sync-diagnostic',action='store_true')
    p.add_argument('--memory-diagnostic',action='store_true')
    p.add_argument('--seed',type=Path)
    a=p.parse_args()
    with open('/private/tmp/pear-native-compilation.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        run(a.runtime,a.output,a.reuse,a.suite,a.sync_diagnostic,a.memory_diagnostic,a.seed)
