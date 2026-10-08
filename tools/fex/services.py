#!/usr/bin/env python3
"""Run only the signed ordinary-native FEX service fixture; never initialize FEX."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import sys
import time
if __package__:
    from .common import REPO, Error, need, load_json, read_relative, record, sha256, operation_output, bounded_command, write_json, decode_json
    from . import sign_services
    from .build import verify_build
else:
    from common import REPO, Error, need, load_json, read_relative, record, sha256, operation_output, bounded_command, write_json, decode_json
    import sign_services
    from build import verify_build

ENV={'PATH':'/usr/bin:/bin:/usr/sbin:/sbin','LC_ALL':'C'}
FALSE_FLAGS=('restricted_operations','fex_initialization','jit_execution','pe_execution','guest_execution','runtime_qualified','distribution_qualified')
UNSUPPORTED=-1073741637
PRODUCERS=('tools/fex/services.py','tools/fex/common.py','tools/fex/build.py','tools/fex/sign_services.py','tools/wine/common.py','host/probe/provisioned_probe.py','host/probe/hardened_baseline.py')
ROLES={'arm64ec':'libarm64ecfex.so','wow64':'libwow64fex.so'}
OBS_FIELDS={'schema_version','record_kind','scope','service_count','cache_line_bytes','pid','mapping_controls','policy_controls','owned_workers','workers_joined','software_tso_required','hardware_tso_status','kernel_control_status','linux_advice_status','vma_naming_status','stats_status','descriptor_cleanup','restricted_operations','fex_initialization','jit_execution','pe_execution','guest_execution','passed'}


def fields(value,expected,code):
    need(isinstance(value,dict) and set(value)==set(expected),code)


def observation(raw,cache_line_bytes,*,policy_controls=20):
    need(type(policy_controls) is int and policy_controls in (20,26),'service_policy_profile')
    value=record(decode_json(raw),'fex_native_service_observation')
    fields(value,OBS_FIELDS,'service_observation_fields')
    need(value['scope']=='fex_component' and value['passed'] is True,'service_observation_failed')
    for name,expected in (('service_count',8),('mapping_controls',7),('policy_controls',policy_controls),('owned_workers',2),('workers_joined',2),('cache_line_bytes',cache_line_bytes)):
        need(type(value[name]) is int and value[name]==expected,'service_observation_contract')
    need(type(value['pid']) is int and 0<value['pid']<=0x7fffffff,'service_observation_pid')
    need(value['software_tso_required'] is True and value['descriptor_cleanup'] is True,'service_fallback_or_cleanup')
    for name in ('hardware_tso_status','kernel_control_status','linux_advice_status','vma_naming_status','stats_status'):
        need(type(value[name]) is int and value[name]==UNSUPPORTED,'service_optional_control_overclaim')
    need(all(value[name] is False for name in FALSE_FLAGS if name in value),'service_observation_runtime_overclaim')
    return value


def recipe(root,authorization):
    auth=Path(authorization)
    return {role:['/usr/bin/arch','-arm64',str(auth/sign_services.MAIN),
           str(auth/sign_services.BUNDLE/'Contents/Resources/native'/name),str(Path(root)/'owned'/role)]
           for role,name in ROLES.items()}


def command_rows(root,rows,expected):
    need(isinstance(rows,list) and len(rows)==len(expected),'service_command_closure')
    stdout={};seen=set()
    for row in rows:
        fields(row,('id','argv','cwd','environment','returncode','elapsed_ms','status','logs'),'service_command_fields')
        ident=row['id'];need(ident in expected and ident not in seen,'service_command_closure');seen.add(ident)
        need(row['argv']==expected[ident] and row['cwd']==str(root) and row['environment']==ENV
             and type(row['returncode']) is int and row['returncode']==0 and row['status']=='completed'
             and type(row['elapsed_ms']) is int and row['elapsed_ms']>=0,'service_command_recipe')
        fields(row['logs'],('stdout','stderr'),'service_log_closure')
        for stream,ref in row['logs'].items():
            fields(ref,('path','sha256','size_bytes'),'service_log_fields')
            need(ref['path']=='logs/'+ident+'/'+stream+'.bin' and type(ref['size_bytes']) is int and 0<=ref['size_bytes']<=65536,'service_log_path')
            raw=read_relative(root,ref['path'],65536)
            need(len(raw)==ref['size_bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],'service_log_changed')
            if stream=='stdout':stdout[ident]=raw
            else:need(raw==b'','unexpected_service_diagnostic')
    return stdout


def producers():return {path:sha256(REPO/path) for path in PRODUCERS}


def verify_services(root):
    """Pure byte/log replay; current authorization is rechecked by run, not replay."""
    root=operation_output(root,require_empty=False,create=False)
    need(not (root/'services-failed.json').exists(),'failed_service_fixture')
    value=record(load_json(root/'services.json'),'fex_darwin_services')
    fields(value,('schema_version','record_kind','scope','authorization_ref','preflight_ref','build_ref','producer_sha256','signed_inventory','commands','observations','native_services_executed','owned_directories_empty','passed',*FALSE_FLAGS),'service_record_fields')
    need(value['scope']=='fex_component' and value['passed'] is True and value['native_services_executed'] is True
         and value['owned_directories_empty'] is True and all(value[name] is False for name in FALSE_FLAGS),'service_record_scope')
    need(value['producer_sha256']==producers(),'service_producer_changed')
    for name,file in (('authorization_ref','authorization.json'),('preflight_ref','preflight.json'),('build_ref','build.json')):
        ref=value[name];fields(ref,('path','sha256'),'service_reference_fields')
        need(sha256(Path(ref['path'])/file)==ref['sha256'],'service_prerequisite_changed')
    authorization=Path(value['authorization_ref']['path']);build_root=Path(value['build_ref']['path'])
    auth=sign_services.validate_authorization_record(authorization)
    need(auth['build_ref']==value['build_ref'] and auth['bundle_inventory']==value['signed_inventory'],'service_authorization_binding')
    built=verify_build(build_root)
    preflight=record(load_json(Path(value['preflight_ref']['path'])/'preflight.json'),'fex_service_preflight')
    need(preflight['authorization_sha256']==value['authorization_ref']['sha256'] and preflight['restricted_operations'] is False,'service_preflight_binding')
    # The signer owns strict current signature/private grant replay. This helper
    # never synthesizes authorization from a successful fixture exit.
    sign_services.validate_preflight_record(Path(value['preflight_ref']['path']),authorization)
    raw=command_rows(root,value['commands'],recipe(root,authorization))
    actual={role:observation(raw[role],built['host_features']['cache_line_bytes']) for role in ROLES}
    need(actual==value['observations'],'service_result_changed')
    for role in ROLES:
        path=root/'owned'/role
        need(path.is_dir() and not path.is_symlink() and not any(path.iterdir()),'service_owned_cleanup_changed')
    need(set(p.name for p in (root/'owned').iterdir())==set(ROLES),'service_owned_directory_closure')
    return value


def run_command(root,role,argv,rows):
    logs=Path(root)/'logs'/role;logs.mkdir(parents=True)
    started=time.monotonic()
    row={'id':role,'argv':argv,'cwd':str(root),'environment':ENV,'returncode':None,'elapsed_ms':0,'status':'unperformed','logs':{}}
    try:
        result=bounded_command(argv,cwd=root,output_dir=logs,timeout=30,max_output=65536,env=ENV)
        row.update(returncode=result['returncode'],elapsed_ms=result['elapsed_ms'],status=result['status'])
    except (Error,OSError) as error:
        row.update(elapsed_ms=int((time.monotonic()-started)*1000),status='failed',error=getattr(error,'code',type(error).__name__))
        raise
    finally:
        for stream in ('stdout','stderr'):
            path=logs/(stream+'.bin')
            if path.exists():row['logs'][stream]={'path':path.relative_to(root).as_posix(),'sha256':sha256(path),'size_bytes':path.stat().st_size}
        rows.append(row)
    need(result['returncode']==0 and result['stderr']==b'','native_service_command_failed:'+role)
    return result


def run(authorization,output):
    root=operation_output(output)
    value={'schema_version':1,'record_kind':'fex_darwin_services','scope':'fex_component','commands':[],
           'observations':{},'native_services_executed':False,'owned_directories_empty':False,'passed':False,**dict.fromkeys(FALSE_FLAGS,False)}
    try:
        auth_root=operation_output(authorization,require_empty=False,create=False)
        auth,preflight=sign_services.validate_authorization(auth_root)
        built=verify_build(Path(auth['build_ref']['path']))
        value.update(authorization_ref={'path':str(auth_root),'sha256':sha256(auth_root/'authorization.json')},
                     preflight_ref={'path':str(preflight),'sha256':sha256(preflight/'preflight.json')},
                     build_ref=auth['build_ref'],producer_sha256=producers(),signed_inventory=auth['bundle_inventory'])
        (root/'owned').mkdir()
        for role,argv in recipe(root,auth_root).items():
            owned=root/'owned'/role;owned.mkdir(mode=0o700)
            result=run_command(root,role,argv,value['commands'])
            value['observations'][role]=observation(result['stdout'],built['host_features']['cache_line_bytes'])
            need(not any(owned.iterdir()),'native_service_owned_cleanup_failed:'+role)
        need(sign_services.inventory(auth_root)==value['signed_inventory'],'service_signed_inventory_changed_during_run')
        value.update(native_services_executed=True,owned_directories_empty=True,passed=True)
        write_json(root/'services.json',value);verify_services(root)
        return value
    except (Error,OSError,ValueError,KeyError,IndexError,UnicodeError,AttributeError) as error:
        value.update(passed=False,error=getattr(error,'code',type(error).__name__))
        write_json(root/'services-failed.json',value);raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('run',));parser.add_argument('--authorization',required=True)
    parser.add_argument('--output',required=True);parser.add_argument('--require-empty',action='store_true',required=True)
    args=parser.parse_args()
    try:
        run(args.authorization,args.output)
        print('PASS: signed ordinary-native Darwin service fixtures; FEX/PE/JIT/guest execution unperformed');return 0
    except (Error,OSError,ValueError,KeyError,IndexError,UnicodeError,AttributeError) as error:
        print('FAIL: '+getattr(error,'code',type(error).__name__),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
