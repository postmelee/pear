#!/usr/bin/env python3
"""Bounded first-dispatch observation using Pear's existing owned supervisor.

This records actual outcomes. It does not promote a component to qualified
runtime support or treat a native-fixture assessor as a guest execution proof.
"""
from pathlib import Path
import argparse,fcntl,hashlib,json,os,re,shutil,stat,subprocess,sys,time,uuid
if not __package__:
    here=Path(__file__).resolve().parent
    sys.path[:]=[p for p in sys.path if Path(p or os.getcwd()).resolve()!=here]
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.fex.common import REPO,need
from tools.fex import memory_wine_runtime as signing,memory_wine_run as supervisor
H=lambda raw:hashlib.sha256(raw).hexdigest()

def prefix_inventory(root):
    # Wine drive names contain colons and have two intentional symlinks; the
    # signed bundle inventory has a different, stricter path vocabulary.
    rows=[]
    for path in sorted(root.rglob('*')):
        rel=str(path.relative_to(root));info=path.lstat()
        if stat.S_ISLNK(info.st_mode):
            target=os.readlink(path)
            need((rel,target) in {('dosdevices/c:','../drive_c'),('dosdevices/z:','/')},'integration_prefix_link')
            rows.append({'path':rel,'kind':'link','target':target})
        elif stat.S_ISREG(info.st_mode):
            rows.append({'path':rel,'kind':'file','size':info.st_size,'mode':stat.S_IMODE(info.st_mode),'sha256':H(path.read_bytes())})
        else:
            need(stat.S_ISDIR(info.st_mode),'integration_prefix_special_file')
            rows.append({'path':rel,'kind':'directory','mode':stat.S_IMODE(info.st_mode)})
    return rows

def admission(runtime,value,output,reuse):
    helpers,_=signing.signing_helpers(reuse);reader=helpers.legacy(REPO)
    need(reader.inventory(runtime/signing.BUNDLE)==value['bundle_inventory'],'integration_bundle_changed')
    authorization=json.loads((runtime/'authorization.json').read_text())
    need(H((runtime/'authorization.json').read_bytes())==value['authorization_sha256'],'integration_authorization_changed')
    output.mkdir(mode=0o700)
    commands=[]
    current,private,raw=helpers.capture_authorization(authorization['original_ref']['path'],output,reader,commands)
    need(current['capture']['sha256']==authorization['capture']['sha256'] and current['claims']==authorization['claims'],
         'integration_current_profile_changed')
    recipe=helpers.profile_recipe(output)
    for i,row in enumerate(value['native_images']):
        recipe+=helpers.signature_recipe(runtime/row['path'],'current.'+str(i),output)
    recipe+=helpers.signature_recipe(runtime/signing.BUNDLE,'current.bundle',output)
    for ident,args in recipe[len(helpers.profile_recipe(output)):]:helpers.native(args,output,ident,commands)
    logs=helpers.verify_commands(output,commands,recipe)
    for i,row in enumerate(value['native_images']):
        restricted=row['path']==signing.MAIN;ident='current.'+str(i)
        observed=helpers.signature_from_logs(logs,ident,current['claims'] if restricted else {},private,reader,
                     signing.BUNDLE_ID if restricted else signing.BUNDLE_ID+'.native.'+str(i))
        need(observed==row['signature'],'integration_signature_changed')
        helpers.signer_leaf(output,ident,private,raw)
    helpers.signature_from_logs(logs,'current.bundle',current['claims'],private,reader,signing.BUNDLE_ID)
    helpers.signer_leaf(output,'current.bundle',private,raw)
    (output/'control.json').write_text(json.dumps({'passed':True,'runtime_sha256':H((runtime/'runtime.json').read_bytes()),'commands':commands},indent=2)+'\n')

def run(runtime,output,reuse,prefix_template=None):
    runtime=Path(runtime).resolve(strict=True);reuse=Path(reuse).resolve(strict=True);output=Path(output).absolute()
    need(output.parent==REPO/'.build/task5' and not output.exists(),'integration_fresh_run')
    value=json.loads((runtime/'runtime.json').read_text());need(value['passed'] is True,'integration_runtime_not_prepared')
    output.mkdir(mode=0o700);(output/'producer.py').write_bytes(Path(__file__).read_bytes())
    print('current authorization',flush=True);admission(runtime,value,output/'before',reuse)
    work=output/'run';work.mkdir();prefix=work/'prefix'
    prefix_origin=None
    if prefix_template:
        template=Path(prefix_template).resolve(strict=True)
        need(template.parent==REPO/'.build/task5','integration_prefix_scope')
        raw=(template/'control.json').read_bytes();prepared=json.loads(raw)
        need(prepared['scope']=='private_synthetic_initialized_prefix' and
             prepared['runtime_sha256']==H((runtime/'runtime.json').read_bytes()),'integration_prefix_pair')
        origin=Path(prepared['source_case'])
        need(origin==REPO/'.build/task5/integration-run16/case.json' and
             H(origin.read_bytes())==prepared['source_case_sha256'],'integration_prefix_origin')
        need(prefix_inventory(template/'prefix')==prepared['inventory'],'integration_prefix_changed')
        inf=runtime/signing.PAYLOAD/'share/wine/wine.inf'
        need((template/'prefix/.update-timestamp').read_text().strip()==str(int(inf.stat().st_mtime)),
             'integration_prefix_update_required')
        need(shutil.disk_usage(REPO).free>=2*1024**3,'integration_warm_prefix_storage')
        subprocess.run(['/bin/cp','-cRp',str(template/'prefix'),str(prefix)],check=True,timeout=30)
        need(prefix_inventory(prefix)==prepared['inventory'],'integration_prefix_clone_changed')
        prefix_origin={'control_sha256':H(raw),'cold_prefix_initialization':False,
                       'method':'independent APFS clone of completed synthetic prefix, current FEX DLL overlaid'}
    else:
        need(shutil.disk_usage(REPO).free>=4*1024**3,'integration_cold_prefix_storage')
        prefix.mkdir(mode=0o700)
    for p in (work/'work',work/'work/tmp'):p.mkdir(mode=0o700)
    result={'scope':'fex_component','kind':'first_x64_dispatch_observation','passed':False,'runtime_sha256':H((runtime/'runtime.json').read_bytes()),
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
    for key in ('runtime','output','reuse'):p.add_argument('--'+key,required=True)
    p.add_argument('--prefix-template')
    args=p.parse_args()
    with open('/private/tmp/pear-native-compilation.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        run(args.runtime,args.output,args.reuse,args.prefix_template)
