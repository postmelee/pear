#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""#6 case selection using #5's unchanged authorization/owned process protocol.

Adapted from integration_run.py at 7214388252229277497da9c9466db8b8df637ada50f284cf04f3a9603272ab84:
only task output scope and source-bound fixture selection change; warm-prefix
support is deliberately omitted. No new process or signing protocol.
"""
from pathlib import Path
import argparse,fcntl,hashlib,json,os,re,shutil,sys,time,uuid
if not __package__:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.fex.common import REPO,need
from tools.fex import memory_wine_runtime as signing,memory_wine_run as supervisor
from tools.fex.integration_run import admission
H=lambda raw:hashlib.sha256(raw).hexdigest()

def run(runtime,output,reuse,case_id):
    runtime=Path(runtime).resolve(strict=True);reuse=Path(reuse).resolve(strict=True);output=Path(output).absolute()
    need(output.parent==REPO/'.build/task6' and not output.exists(),'integration_fresh_run')
    value=json.loads((runtime/'runtime.json').read_text());need(value['passed'] is True,'integration_runtime_not_prepared')
    need(value['kind']=='cpu_corpus_development_runtime' and case_id in value['fixtures'],'cpu_fixture_selection')
    fixture=value['fixtures'][case_id]
    need(H((runtime/fixture['path']).read_bytes())==fixture['sha256'],'cpu_fixture_changed')
    value['entrypoints']['fixture_pe']=fixture['path']
    output.mkdir(mode=0o700);(output/'producer.py').write_bytes(Path(__file__).read_bytes())
    print('current authorization',flush=True);admission(runtime,value,output/'before',reuse)
    work=output/'run';work.mkdir();prefix=work/'prefix'
    prefix_origin=None
    need(shutil.disk_usage(REPO).free>=4*1024**3,'cpu_cold_prefix_storage')
    prefix.mkdir(mode=0o700)
    for p in (work/'work',work/'work/tmp'):p.mkdir(mode=0o700)
    result={'scope':'fex_component','kind':'cpu_corpus_observation','fixture_id':case_id,'fixture_sha256':fixture['sha256'],'passed':False,'runtime_sha256':H((runtime/'runtime.json').read_bytes()),
            'expected_exit':value.get('expected_exit',42),'guest_execution_qualified':False,'stage3_complete':False,'prefix_origin':prefix_origin}
    with supervisor.supervision(reuse) as (life,helpers):
        nonce=uuid.uuid4().hex;packet=supervisor.assessment_packet(value)
        session=helpers.api.APISession(work,runtime,packet,nonce,suite='api-abi',case_id='first-dispatch')
        env=supervisor.environment(work/'work',prefix,nonce,os.environ.get('HOME'))
        env['WINEDEBUG']='-all,+loaddll,+seh,+module'
        paths={k:runtime/v for k,v in value['entrypoints'].items()}
        read_fd=control=None;error=None;outcome='not_started';start=time.monotonic();deadline=start+180
        remaining=lambda cap:max(0,min(cap,deadline-time.monotonic()))
        launches=[]
        def launch(role,args,environment,**kwargs):
            child=session.launch(role,args,environment,**kwargs)
            launches.append({'role':role,'argv':args,'environment':environment,'pid':child.pid});return child
        print('starting owned x64 fixture',flush=True)
        try:
            read_fd,control=os.pipe()
            sentinel=launch('sentinel',[str(paths['sentinel']),str(read_fd)],env,pass_fds=(read_fd,))
            os.close(read_fd);read_fd=None
            need(session.wait_for(lambda:b'\n' in session.streams[('sentinel','stdout')]['data'],remaining(5)),'integration_sentinel_start')
            helpers.base.validate_helper(helpers.base.parse_lines(session,'sentinel')[0],'pear_sentinel_ready',sentinel)
            server=launch('server',[str(paths['server']),'-f','-p'],env,event_pipe=True)
            need(session.wait_for(lambda:any(r.get('event')=='server_ready' for r in session.events['server']) or server.exited,remaining(30)) and not server.exited,'integration_server_start')
            loader_env={**env,'PEAR_STAGE3_CONTROL':session.endpoint,'PEAR_WINE_ABI_FIXTURE':'1',
                        'PEAR_BOOTSTRAP_SERVER_PID':str(server.pid),'WINEDLLOVERRIDES':'mscoree='}
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
    for key in ('runtime','output','reuse','case'):p.add_argument('--'+key,required=True)
    a=p.parse_args()
    with open('/private/tmp/pear-native-compilation.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        run(a.runtime,a.output,a.reuse,a.case)
