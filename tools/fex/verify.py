#!/usr/bin/env python3
"""Replay actual Stage 1 source/tool/compile receipts without running guest code."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
if __package__:
    from .common import Error, REPO, load_json, need, operation_output, record, relative, sha256
    from .prepare import verify_prepared
    from .tools import verify_tools, wine_readers
    from .check import FALSE_FLAGS, MACHINES, archive_machines, inspect_fixture_arm64ec, pe_facts, verify_cross, verify_wine_roles, validate_config, command_recipe, environment_contract, link_contributions
else:
    from common import Error, REPO, load_json, need, operation_output, record, relative, sha256
    from prepare import verify_prepared
    from tools import verify_tools, wine_readers
    from check import FALSE_FLAGS, MACHINES, archive_machines, inspect_fixture_arm64ec, pe_facts, verify_cross, verify_wine_roles, validate_config, command_recipe, environment_contract, link_contributions


def verify_command_receipts(data,root,prepared,tc,lock,config):
    recipe=command_recipe(root,prepared,tc,lock)
    required_commands=set(recipe)
    observed=set()
    for row in data['commands']:
        need(row['id'] not in observed and row['id'] in recipe and row['exit_code']==0,
             'duplicate_or_failed_capability_command')
        observed.add(row['id'])
        need(row['argv']==recipe[row['id']], 'capability_command_recipe_mismatch')
        need(row['environment']==environment_contract(tc,lock,config), 'capability_environment_mismatch')
        need(type(row['elapsed_ms']) is int and row['elapsed_ms']>=0,'invalid_command_duration')
        need(set(row['logs'])=={'stdout','stderr'},'incomplete_capability_logs')
        for stream,ref in row['logs'].items():
            need(ref['path']==f"logs/{row['id']}/{stream}.bin",'capability_log_path_mismatch')
            p=root.joinpath(*relative(ref['path']))
            need(0<=ref['size_bytes']<=512*1024 and p.stat().st_size==ref['size_bytes']
                 and sha256(p)==ref['sha256'],'capability_log_changed')
    need(observed==required_commands,'incomplete_capability_commands')



def verify_checks(rows, facts):
    expected=[{'id':'input-and-tool-closure','status':'passed','required':True}]
    for target in MACHINES:
        expected.append({'id':target+'-cxx20-layout-static-link','status':'passed','required':True,
                         'pe_facts':facts[target],'pe_execution':False})
    expected.append({'id':'static-runtime-member-inventory','status':'passed','required':True})
    need(rows==expected,'required_check_evidence_mismatch')
    return expected


def verify_stage1(root):
    root=operation_output(root,require_empty=False,create=False)
    data=record(load_json(root/'capabilities.json'),'fex_stage1_capabilities')
    need(data.get('scope')=='fex_component','wrong_evidence_scope')
    need(data.get('passed') is True,'required_capability_not_passed')
    need(all(data.get(name) is False for name in FALSE_FLAGS),'stage1_runtime_overclaim')
    bindings=data['bindings']
    for name in ('inputs','config','toolchain','wine_roles'):
        need(sha256(Path(bindings[name]['path']))==bindings[name]['sha256'],'bound_input_changed')
    prepared=Path(bindings['prepared']['path'])
    need(sha256(prepared/'prepared.json')==bindings['prepared']['sha256'],'prepared_receipt_changed')
    sources=verify_prepared(prepared,expected_inputs_sha256=bindings['inputs']['sha256'])
    tool_root=Path(bindings['tools']['path'])
    need(sha256(tool_root/'prepared.json')==bindings['tools']['sha256'],'tool_receipt_changed')
    verify_tools(tool_root,Path(bindings['toolchain']['path']))
    roles,actual=verify_wine_roles(Path(bindings['wine_roles']['path']))
    need(actual==data['wine_roles'],'wine_role_observation_changed')
    lock=record(load_json(bindings['toolchain']['path']),'fex_toolchain')
    config=validate_config(load_json(bindings['config']['path']),bindings['inputs']['sha256'])
    need(data.get('link_probe_scope')=='standalone_default_crt_static_prerequisites'
         and data.get('fex_custom_crt_link')=='unperformed','custom_crt_link_overclaim')
    need(set(data['link_contributions'])==set(MACHINES),'incomplete_link_contributions')
    tc=Path(bindings['cross_tools']['path'])
    need(verify_cross(lock,tc,Path(bindings['cross_tools']['archive']))==data['cross_toolchain'],'cross_observation_changed')
    need(set(data['producer_sha256'])=={str(p.relative_to(REPO)) for p in (REPO/'tools/fex').glob('*.py')},'incomplete_producer_binding')
    for path,digest in data['producer_sha256'].items():
        need(sha256(REPO.joinpath(*relative(path)))==digest,'capability_producer_changed')
    expected_fixture_names={'language.cpp','layout.cpp','declarations.cpp','static-runtime.cpp'}
    need(set(data['fixtures'])==expected_fixture_names,'incomplete_capability_fixtures')
    for name,digest in data['fixtures'].items():
        need(sha256(REPO/'tests/fex/capabilities'/name)==digest,'capability_fixture_changed')
    expected_kinds={'native-layout.obj':'native_layout_object'}
    for target in MACHINES:
        expected_kinds.update({target+'/'+name+'.obj':'coff_object' for name in ('language','layout','declarations')})
        expected_kinds.update({target+'/static-runtime.obj':'static_runtime_object',target+'/ntdll-ex.a':'source_import_archive',
                               target+'/pear-fex-capability.dll':'capability_dll',target+'/link.map':'link_map'})
    rows=data['artifacts'];seen=set()
    for row in rows:
        need(row['path'] not in seen,'duplicate_capability_artifact');seen.add(row['path'])
        need(row['path'] in expected_kinds and row['kind']==expected_kinds[row['path']],'capability_artifact_role_mismatch')
        p=root.joinpath(*relative(row['path']))
        need(p.stat().st_size==row['size_bytes'] and sha256(p)==row['sha256'],'capability_artifact_changed')
        if row['kind']=='coff_object':
            need(wine_readers().coff_machine(p)==row['machine'],'capability_object_evidence_mismatch')
        elif row['kind']=='capability_dll':
            facts=pe_facts(p)
            if facts['outer_machine']==0x8664:
                facts['arm64ec_metadata']=inspect_fixture_arm64ec(p)
            need(all(row.get(key)==value for key,value in facts.items()),'capability_pe_evidence_mismatch')
        elif row['kind']=='native_layout_object':
            need(wine_readers().inspect_macho(p)['architectures']==[0x100000c],'native_layout_not_arm64')
    expected={'native-layout.obj'}
    for target in MACHINES:
        expected.update(target+'/'+name for name in ('language.obj','layout.obj','declarations.obj','static-runtime.obj','ntdll-ex.a','pear-fex-capability.dll','link.map'))
    need(seen==expected==set(expected_kinds),'incomplete_capability_artifacts')
    verify_command_receipts(data,root,prepared,tc,lock,config)
    cross=next(r for r in data['commands'] if r['id']=='cross.version')
    need(b'clang version 23.1.1' in (root/cross['logs']['stdout']['path']).read_bytes(),'cross_version_replay_mismatch')
    current_facts={}
    for target,machine in MACHINES.items():
        need(link_contributions(root/target/'link.map')==data['link_contributions'][target],'link_contribution_changed')
        row=next(r for r in data['commands'] if r['id']==target+'.pe-inspect')
        text=(root/row['logs']['stdout']['path']).read_text()
        need('pear_fex_static_runtime' in text and 'NtYieldExecution' in text and 'ntdll.dll' in text,'missing_real_import_export')
        need(not any(name in text.lower() for name in ('libc++.dll','libc++abi.dll','libunwind.dll')),'unexpected_dynamic_cpp_runtime')
        for name in ('language','layout','declarations','static-runtime'):
            need(wine_readers().coff_machine(root/target/(name+'.obj'))==machine,'target_object_mismatch')
        facts=pe_facts(root/target/'pear-fex-capability.dll')
        need(facts['outer_machine']==(0x8664 if target=='arm64ec' else 0xaa64),'target_dll_mismatch')
        if target=='arm64ec':
            need(facts['chpe_metadata_pointer']>0,'missing_arm64ec_metadata')
            facts['arm64ec_metadata']=inspect_fixture_arm64ec(root/target/'pear-fex-capability.dll')
        current_facts[target]=facts
    verify_checks(data['checks'],current_facts)
    need(set(data['static_libraries'])=={'libc++.a','libc++abi.a','libunwind.a','builtins'},'incomplete_static_runtime_libraries')
    for name in ('libc++.a','libc++abi.a','libunwind.a'):
        need(archive_machines(tc/'aarch64-w64-mingw32/lib'/name)==data['static_libraries'][name],'static_runtime_observation_changed')
    row=next(r for r in data['commands'] if r['id']=='builtins.path')
    builtin=Path((root/row['logs']['stdout']['path']).read_text().strip())
    need(builtin.resolve().is_relative_to(tc.resolve()),'builtins_outside_toolchain')
    need(archive_machines(builtin)==data['static_libraries']['builtins'],'builtins_observation_changed')
    return data,sources


def public_observation(root):
    data,sources=verify_stage1(root)
    return {'schema_version':1,'record_kind':'fex_stage1_observations','scope':'fex_component','capabilities_sha256':sha256(Path(root)/'capabilities.json'),'input_sha256':data['bindings']['inputs']['sha256'],'config_sha256':data['bindings']['config']['sha256'],'toolchain_sha256':data['bindings']['toolchain']['sha256'],'checks':[{'id':r['id'],'status':r['status'],'required':r['required'],**({'pe_facts':r['pe_facts'],'pe_execution':False} if 'pe_facts' in r else {})} for r in data['checks']],'fixture_sha256':data['fixtures'],'source_components':[{'id':r['id'],'commit':r['commit'],'tree':r['tree'],'file_count':r['file_count'],'total_bytes':r['total_bytes']} for r in sources['components']],'artifact_count':len(data['artifacts']),'command_count':len(data['commands']),'static_runtime_libraries':data['static_libraries'],'link_contributions':data['link_contributions'],'link_probe_scope':data['link_probe_scope'],'fex_custom_crt_link':data['fex_custom_crt_link'],'evidence_scope':'source-inspection-and-compile-link-only','stage1_passed':True,**dict.fromkeys(FALSE_FLAGS,False)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('stage1',))
    parser.add_argument('--root',required=True)
    parser.add_argument('--require-complete',action='store_true',required=True)
    args=parser.parse_args()
    try:
        data,_=verify_stage1(Path(args.root))
        print(f"PASS: independently replayed {len(data['checks'])} required checks, {len(data['artifacts'])} compile-only artifacts; no FEX dispatch")
        return 0
    except (Error,OSError,ValueError,KeyError,StopIteration) as exc:
        code=getattr(exc,'code',type(exc).__name__)
        print('FAIL: '+code,file=sys.stderr)
        return 3 if code=='required_capability_not_passed' else 1
if __name__=='__main__':raise SystemExit(main())
