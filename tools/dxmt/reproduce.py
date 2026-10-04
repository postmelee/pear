#!/usr/bin/env python3
"""Fresh same-host graphics reconstruction and strict independent replay.

Historical producers remain unchanged; differences are retained without normalization.
Construction invokes the existing native builder only through its explicit CLI.
Independent replay never signs or executes Wine/Metal or grants permission.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import stat
import sys
import uuid
from types import SimpleNamespace

import compare
from common import (REPO,Error,decode_json,digest,encoded,need,owned_directory,
                    output_directory,read_relative,real_directory,write_new)
import build as stage3
import pairing_build
import pairing_check
import pairing_evidence

OWN_PRODUCERS=('tools/dxmt/reproduce.py','tools/dxmt/compare.py')
REPLAY_SOURCES=('tools/dxmt/pairing_build.py','tools/dxmt/pairing_check.py',
               'tools/dxmt/pairing_evidence.py','tools/dxmt/pairing_runtime.py',
               'tools/dxmt/run_pairing.py','tools/dxmt/build.py',
               'tools/dxmt/inspect.py','tools/dxmt/common.py')
INPUTS=('runtime/dxmt/inputs.json','runtime/dxmt/toolchain.json',
        'runtime/dxmt/build-config.json','runtime/dxmt/patches/series.json',
        'runtime/wine/inputs.json','runtime/wine/toolchain.json',
        'runtime/wine/build-config.json','runtime/wine/patches/series.json')
KIND='dxmt_component_reconstruction'
SCOPE='fresh_graphics_component_same_host_verified_prerequisite_reuse'
BASE_FIELDS={'schema_version','record_kind','scope','producers','input_refs','artifact_ref',
        'reference_ref','candidate_ref','policy','comparison_ref','inventory_refs',
        'source_signature','source_reconstruction_performed',
        'compiler_rebuilt','native_prerequisites_rebuilt','second_machine_reproduction',
        'hybrid_execution_performed','translated_guest_execution_performed',
        'game_qualified','runtime_eligible','distribution_qualified'}
FIELDS=BASE_FIELDS|{'construction_ref','native_evidence','outcome'}
CONSTRUCTION_KIND='dxmt_component_construction'
CONSTRUCTION_FIELDS=BASE_FIELDS|{'native_pairing_evidence','reconstruction_complete'}


def same(left,right,reason):need(encoded(left)==encoded(right),reason)
def reference(root,name='build.json'):
    return {'path':str(root),'sha256':digest(read_relative(root,name,8*1024**2))}
def producers(repo=REPO):
    return {name:digest(read_relative(repo,name))for name in sorted(set(OWN_PRODUCERS+REPLAY_SOURCES))}
def input_refs(repo=REPO):
    return {name:digest(read_relative(repo,name,8*1024**2))for name in INPUTS}
def capture_sources(root,values,repo=REPO):
    for path,expected in values.items():
        raw=read_relative(repo,path,8*1024**2);need(digest(raw)==expected,'reconstruction_source_capture')
        stage3.write_bytes(root,'producers/'+path,raw)
def replay_sources(root,values,repo=REPO):
    need(values==producers(repo),'reconstruction_producer_changed')
    for path,expected in values.items():
        raw=read_relative(root,'producers/'+path,8*1024**2)
        need(digest(raw)==expected and raw==read_relative(repo,path,8*1024**2),'reconstruction_source_capture')

def policy(cap,reserve):
    need(type(cap)is int and 2*1024**3<=cap<=8*1024**3
         and type(reserve)is int and 4*1024**3<=reserve<=16*1024**3,'reconstruction_policy')
    return {'jobs':2,'growth_ceiling_bytes':cap,'reserve_free_bytes':reserve,
            'measured_build_peak_bytes':None,'ceiling_is_peak_measurement':False}
def expected_candidate(root):
    name=root.name+'-candidate';need(len(name)<=96,'reconstruction_candidate_name')
    return root.parent/name

def source_signature(value):
    required=['prior_artifact','role_reference','series_sha256','supplemental_inputs',
              'fixture_sources','producer_files','wine_configuration']
    need(all(key in value for key in required)and set(value.get('source',{}))=={'wine','dxmt'},'reconstruction_source_shape')
    view={key:value[key]for key in required}
    view['source']={name:value['source'][name]['after_files']for name in ['wine','dxmt']}
    return digest(encoded(view))
def verified_pair(root,repo=REPO):
    value=pairing_check.verify_build(root,repo=repo)
    need(value['scope']=='typed_native_metal_pairing'and value['passed']is True
         and all(value[key]is False for key in ['pairing_verified','native_execution','hybrid_execution',
               'translated_guest_execution','game_qualified','runtime_eligible']),'reconstruction_pair_scope')
    return value

def file_row(root,path):
    _,fact=stage3.inspector().file_bytes(root,path)
    return {**fact,'kind':'file'}
def selected_tree(root,paths):
    # Actual directory modes accompany the declared selected file set. It is
    # a finite selected-artifact view, not every intermediate object directory.
    return compare.scan_selected(root,paths)

def complete_inventory(root,built,repo=REPO):
    """Derive every declared unsigned payload from verified actual origins."""
    _,roots,role_ref=stage3.selector(built['role_reference']['path'],repo)
    same(role_ref,built['role_reference'],'reconstruction_wine_roles')
    baseline=pairing_build.source_baseline(roots['native'])
    install=real_directory(baseline['install_root']);need(install==roots['native']/'install','reconstruction_wine_install')
    manifest_ref=baseline['artifacts_manifest'];raw=read_relative(roots['native'],manifest_ref['path'],8*1024**2)
    need(digest(raw)==manifest_ref['sha256'],'reconstruction_wine_manifest')
    entries=compare.check_wine_manifest(compare.scan_tree(install),decode_json(raw,8*1024**2))
    origins={
      'lib/wine/aarch64-unix/winemac.so':pairing_check.REBUILT_DRIVER,
      'lib/wine/aarch64-windows/winemac.drv':pairing_check.REBUILT_PE,
      'lib/wine/aarch64-unix/winemetal.so':'dxmt/install/aarch64-unix/winemetal.so',
      'libexec/pear-dxmt/pairing-arm64.exe':pairing_check.FIXTURE_PE}
    replacements=[{**file_row(root,origin),'path':name}for name,origin in origins.items()]
    result=compare.namespace('wine',compare.overlay_wine(entries,replacements))
    result+=compare.namespace('dxmt',compare.scan_tree(root/'dxmt/install'))
    facts=pairing_check.inspect_pair(root,built,repo=repo)
    compiler=['dxmt/compiler/'+name for name in sorted(stage3.PE_TARGETS)]
    built_paths=[pairing_check.REBUILT_DRIVER,pairing_check.REBUILT_PE,pairing_check.FIXTURE_PE,
                 'dxmt/objects/'+stage3.NATIVE_TARGET]+['dxmt/objects/'+path for path in stage3.PE_TARGETS.values()]
    generated=[row['path']for row in facts['generated_inputs']]
    shader=[row['path']for row in facts['shader_outputs']]+[facts['version_header']['path']]
    need(len(generated)==len(set(generated))and len(shader)==len(set(shader))
         and set(row['path']for row in facts['notices'])<=set(generated),'reconstruction_generated_set')
    result+=compare.namespace('compiler',selected_tree(root,compiler))
    result+=compare.namespace('built',selected_tree(root,built_paths))
    result+=compare.namespace('generated',selected_tree(root/'dxmt',generated))
    result+=compare.namespace('shaders',selected_tree(root/'dxmt',shader))
    result=compare.validate_entries(sorted(result,key=lambda row:row['path']))
    origin_ref={'baseline_root':str(roots['native']),'baseline_build_sha256':reference(roots['native'])['sha256'],
                'baseline_manifest_ref':manifest_ref,'role_reference':role_ref,'replacements':origins,
                'baseline_directory_modes':'actual_current_observation_no_historical_mode_baseline',
                'view_scope':'complete_wine_payload_and_dxmt_install_plus_selected_compiler_built_generated_shader_outputs'}
    return result,origin_ref


def native_binding(run_root,reference_root,candidate_root,comparison,left,right,repo=REPO):
    """Use actual separately reviewed finite run, never reference success alone."""
    run_root=owned_directory(run_root,repo)
    run_raw=read_relative(run_root,'run.json');review_raw=read_relative(run_root,pairing_evidence.REVIEW)
    observed=pairing_evidence.verify_native_evidence(run_root,repo=repo)
    need(observed['finite_native_scope_complete']is True and observed['metal_api_validation']=='reviewed_no_errors'
         and all(observed[key]is False for key in ['runtime_eligible','game_qualified','distribution_qualified']),
         'reconstruction_native_scope')
    run=decode_json(run_raw)
    runtime_root=owned_directory(run['runtime_ref']['path'],repo)
    runtime_raw=read_relative(runtime_root,'runtime.json',8*1024**2)
    need(digest(runtime_raw)==run['runtime_ref']['sha256'],'reconstruction_native_runtime')
    runtime=decode_json(runtime_raw,8*1024**2);bound=runtime['build_ref']
    if bound==reference(candidate_root):
        origin='fresh_final_candidate';new_execution=True
    else:
        need(bound==reference(reference_root)and comparison['raw_equal']is True
             and source_signature(left)==source_signature(right),'reconstruction_native_bytes_not_matching')
        origin='reused_matching_stage4_reference';new_execution=False
    need(read_relative(run_root,'run.json')==run_raw
         and read_relative(run_root,pairing_evidence.REVIEW)==review_raw
         and read_relative(runtime_root,'runtime.json',8*1024**2)==runtime_raw,'reconstruction_native_changed')
    return {'run_ref':{'path':str(run_root),'sha256':digest(run_raw)},'runtime_ref':run['runtime_ref'],
       'diagnostics_review_ref':{'path':str(run_root),'sha256':digest(review_raw)},
       'source_build_ref':bound,'observations':observed,'origin':origin,
       'new_native_execution_performed':new_execution,'permission_transfer':'not_inferred'}


def save_json(root,path,value):
    write_new(root/path,value);return {'path':path,'sha256':digest(read_relative(root,path,8*1024**2))}
def load_ref(root,ref):
    need(type(ref)is dict and set(ref)=={'path','sha256'},'reconstruction_ref_shape')
    raw=read_relative(root,ref['path'],8*1024**2);need(digest(raw)==ref['sha256'],'reconstruction_ref_bytes')
    return decode_json(raw,8*1024**2)
def inventory_record(entries):
    return {'schema_version':1,'record_kind':'dxmt_unsigned_inventory','entries':entries}
def comparison_views(root,left,right):
    before,origin_before=complete_inventory(root[0],left,repo=root[2])
    after,origin_after=complete_inventory(root[1],right,repo=root[2])
    same(origin_before,origin_after,'reconstruction_origin_scope_changed')
    return before,after,origin_before,compare.compare_entries(before,after)

def failure_facts(exc,phase):
    value={'phase':phase,'error':getattr(exc,'code',str(exc)if isinstance(exc,compare.Error)else type(exc).__name__)}
    if isinstance(exc,OSError):value['native_error']={'domain':'POSIX','code':exc.errno}
    elif getattr(exc,'native_error',None)is not None:value['native_error']=exc.native_error
    return value

def construct(args,repo=REPO):
    root=output_directory(args.output,repo);phase='preflight';value={'schema_version':1,'record_kind':CONSTRUCTION_KIND,
          'scope':SCOPE,'passed':False,'source_reconstruction_performed':False,
          'construction_attempted':False,'native_execution_performed':False,'runtime_eligible':False}
    try:
        donor=owned_directory(args.artifact,repo);reference_root=owned_directory(args.reference,repo)
        candidate=expected_candidate(root)
        need(not candidate.exists()and not candidate.is_symlink()and donor!=reference_root
             and root not in [donor,reference_root]and candidate not in [donor,reference_root],'reconstruction_outputs')
        admitted=policy(args.max_growth_bytes,args.reserve_free_bytes)
        snaps=producers(repo);capture_sources(root,snaps,repo);inputs=input_refs(repo)
        value.update(producers=snaps,input_refs=inputs,artifact_ref=reference(donor),
                     reference_ref=reference(reference_root),candidate_path=str(candidate),policy=admitted)
        stage3.verify_build(donor,repo=repo);left=verified_pair(reference_root,repo)
        need(left['prior_artifact']==reference(donor),'reconstruction_original_donor')
        phase='construct';value['construction_attempted']=True
        pairing_build.construct(SimpleNamespace(artifact=str(donor),output=str(candidate),
             max_growth_bytes=admitted['growth_ceiling_bytes'],reserve_free_bytes=admitted['reserve_free_bytes'],require_empty=True))
        value['source_reconstruction_performed']=True
        phase='candidate-replay';right=verified_pair(candidate,repo)
        need(right['prior_artifact']==reference(donor),'reconstruction_candidate_donor')
        need(source_signature(left)==source_signature(right),'reconstruction_source_settings_changed')
        phase='compare';before,after,origins,comp=comparison_views((reference_root,candidate,repo),left,right)
        inventories={'reference':save_json(root,'reference-unsigned-files.json',inventory_record(before)),
                     'candidate':save_json(root,'candidate-unsigned-files.json',inventory_record(after)),
                     'origins':save_json(root,'unsigned-origins.json',origins)}
        comparison_ref=save_json(root,'comparison.json',comp)
        value.update(comparison_ref=comparison_ref,inventory_refs=inventories)
        need(comp['raw_equal']is True,'reconstruction_unsigned_difference')
        constructed={'schema_version':1,'record_kind':CONSTRUCTION_KIND,'scope':SCOPE,'producers':snaps,'input_refs':inputs,
          'artifact_ref':reference(donor),'reference_ref':reference(reference_root),'candidate_ref':reference(candidate),
          'policy':admitted,'comparison_ref':comparison_ref,'inventory_refs':inventories,
          'source_signature':source_signature(right),'native_pairing_evidence':'unperformed','reconstruction_complete':False,
          'source_reconstruction_performed':True,'compiler_rebuilt':False,'native_prerequisites_rebuilt':False,
          'second_machine_reproduction':False,'hybrid_execution_performed':False,
          'translated_guest_execution_performed':False,'game_qualified':False,'runtime_eligible':False,'distribution_qualified':False}
        need(snaps==producers(repo)and inputs==input_refs(repo),'reconstruction_inputs_changed')
        save_json(root,'construction.json',constructed)
        phase='independent-construction-replay';verify_construction(root,repo=repo)
    except Exception as exc:
        value.update(failure_facts(exc,phase))
        try:write_new(root/'failed.json',value)
        except Exception as secondary:
            exc.reconstruction_record_error={'type':type(secondary).__name__,'code':getattr(secondary,'errno',None)}
        raise
    # A completion refusal does not rewrite a successful construction or mark
    # that unsigned build failed. The explicit later finalizer can retry with
    # newly produced candidate-bound native evidence on the same candidate.
    native_root=getattr(args,'native_evidence',None)
    return complete(root,native_root,repo=repo)if native_root is not None else constructed


def replay_common(root,value,repo):
    need(value['source_reconstruction_performed']is True and all(value[key]is False for key in [
        'compiler_rebuilt','native_prerequisites_rebuilt','second_machine_reproduction','hybrid_execution_performed',
        'translated_guest_execution_performed','game_qualified','runtime_eligible','distribution_qualified']),
        'reconstruction_claims')
    replay_sources(root,value['producers'],repo);same(value['input_refs'],input_refs(repo),'reconstruction_inputs_changed')
    same(value['policy'],policy(value['policy']['growth_ceiling_bytes'],value['policy']['reserve_free_bytes']),
         'reconstruction_policy_changed')
    roots={}
    for name in ['artifact','reference','candidate']:
        ref=value[name+'_ref'];need(type(ref)is dict and set(ref)=={'path','sha256'},'reconstruction_build_ref')
        roots[name]=owned_directory(ref['path'],repo);same(ref,reference(roots[name]),'reconstruction_build_ref_changed')
    need(roots['candidate']==expected_candidate(root)and len({root,*roots.values()})==4,'reconstruction_candidate_scope')
    stage3.verify_build(roots['artifact'],repo=repo)
    left=verified_pair(roots['reference'],repo);right=verified_pair(roots['candidate'],repo)
    need(left['prior_artifact']==right['prior_artifact']==value['artifact_ref'],'reconstruction_donor_changed')
    need(source_signature(left)==source_signature(right)==value['source_signature'],'reconstruction_source_changed')
    before,after,origins,comp=comparison_views((roots['reference'],roots['candidate'],repo),left,right)
    need(type(value['inventory_refs'])is dict and set(value['inventory_refs'])=={'reference','candidate','origins'},'reconstruction_inventory_set')
    for key,expected in [('reference',inventory_record(before)),('candidate',inventory_record(after)),('origins',origins)]:
        need(value['inventory_refs'][key]['path']=={'reference':'reference-unsigned-files.json',
            'candidate':'candidate-unsigned-files.json','origins':'unsigned-origins.json'}[key], 'reconstruction_inventory_path')
        same(load_ref(root,value['inventory_refs'][key]),expected,'reconstruction_inventory_changed')
    need(value['comparison_ref']['path']=='comparison.json','reconstruction_comparison_path')
    same(load_ref(root,value['comparison_ref']),comp,'reconstruction_comparison_changed')
    need(comp['raw_equal']is True,'reconstruction_unsigned_difference')
    return roots,left,right,comp


def construction_context(root,repo=REPO):
    root=owned_directory(root,repo);need(not(root/'failed.json').exists(),'failed_reconstruction')
    raw=read_relative(root,'construction.json',8*1024**2);value=decode_json(raw,8*1024**2)
    need(type(value)is dict and set(value)==CONSTRUCTION_FIELDS and type(value['schema_version'])is int
         and value['schema_version']==1 and value['record_kind']==CONSTRUCTION_KIND and value['scope']==SCOPE,
         'construction_record')
    need(value['native_pairing_evidence']=='unperformed'and value['reconstruction_complete']is False,'construction_claims')
    context=replay_common(root,value,repo)
    need(read_relative(root,'construction.json',8*1024**2)==raw,'construction_record_changed')
    replay_sources(root,value['producers'],repo)
    return value,raw,context

def verify_construction(root,repo=REPO):
    return construction_context(root,repo)[0]


def completion_failure(root,exc,phase,construction_ref,native_root):
    parent=root/'completion-failures'
    need(not parent.is_symlink()and(not parent.exists()or parent.is_dir()),'completion_failure_scope')
    parent.mkdir(mode=0o755,exist_ok=True)
    need(len(list(parent.iterdir()))<32,'completion_failure_count')
    attempt=parent/uuid.uuid4().hex;attempt.mkdir(mode=0o755)
    value={'schema_version':1,'record_kind':'dxmt_component_completion_failure','scope':SCOPE,
           'construction_ref':construction_ref,'requested_native_evidence':str(native_root),
           'reconstruction_complete':False,'runtime_eligible':False,**failure_facts(exc,phase)}
    write_new(attempt/'failed.json',value)


def complete(root,native_root,repo=REPO):
    root=owned_directory(root,repo);phase='construction-replay';construction_ref=None
    try:
        need(not(root/'reproduction.json').exists()and not(root/'reproduction.json').is_symlink(),
             'completion_destination_exists')
        constructed,raw,context=construction_context(root,repo)
        construction_ref={'path':'construction.json','sha256':digest(raw)}
        roots,left,right,comp=context;phase='native-evidence'
        native=native_binding(native_root,roots['reference'],roots['candidate'],comp,left,right,repo)
        value={key:constructed[key]for key in BASE_FIELDS}
        value.update(record_kind=KIND,construction_ref=construction_ref,native_evidence=native,
            outcome={'raw_unsigned_equal':True,'reconstruction_complete':True,'finite_native_pairing_bound':True})
        need(read_relative(root,'construction.json',8*1024**2)==raw,'construction_record_changed')
        replay_sources(root,value['producers'],repo);same(value['input_refs'],input_refs(repo),'reconstruction_inputs_changed')
        save_json(root,'reproduction.json',value)
        phase='independent-final-replay';return verify(root,repo=repo)
    except Exception as exc:
        try:completion_failure(root,exc,phase,construction_ref,native_root)
        except Exception as secondary:
            exc.reconstruction_record_error={'type':type(secondary).__name__,'code':getattr(secondary,'errno',None)}
        raise


def verify(root,repo=REPO):
    root=owned_directory(root,repo);need(not(root/'failed.json').exists(),'failed_reconstruction')
    raw=read_relative(root,'reproduction.json',8*1024**2);value=decode_json(raw,8*1024**2)
    need(type(value)is dict and set(value)==FIELDS and type(value['schema_version'])is int
         and value['schema_version']==1 and value['record_kind']==KIND and value['scope']==SCOPE,'reconstruction_record')
    need(value['construction_ref']['path']=='construction.json','completion_construction_path')
    construction_raw=read_relative(root,'construction.json',8*1024**2)
    same(value['construction_ref'],{'path':'construction.json','sha256':digest(construction_raw)},'completion_construction_changed')
    constructed,current_raw,context=construction_context(root,repo)
    need(current_raw==construction_raw,'construction_record_changed')
    expected={key:constructed[key]for key in BASE_FIELDS};expected['record_kind']=KIND
    same({key:value[key]for key in BASE_FIELDS},expected,'completion_construction_facts_changed')
    roots,left,right,comp=context
    saved=value['native_evidence'];need(type(saved)is dict and 'run_ref'in saved,'reconstruction_native_ref')
    native=native_binding(saved['run_ref']['path'],roots['reference'],roots['candidate'],comp,left,right,repo)
    same(saved,native,'reconstruction_native_evidence_changed')
    same(value['outcome'],{'raw_unsigned_equal':True,'reconstruction_complete':True,'finite_native_pairing_bound':True},
         'reconstruction_outcome_changed')
    need(read_relative(root,'reproduction.json',8*1024**2)==raw
         and read_relative(root,'construction.json',8*1024**2)==construction_raw,'reconstruction_record_changed')
    replay_sources(root,value['producers'],repo);return value


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_mutually_exclusive_group();modes.add_argument('--verify',action='store_true');modes.add_argument('--complete',action='store_true')
    parser.add_argument('--output',required=True);parser.add_argument('--require-complete',action='store_true')
    for name in ['artifact','reference','native-evidence']:parser.add_argument('--'+name)
    for name in ['max-growth-bytes','reserve-free-bytes']:parser.add_argument('--'+name,type=int)
    parser.add_argument('--require-empty',action='store_true');args=parser.parse_args(argv)
    construction=[args.artifact,args.reference,args.max_growth_bytes,args.reserve_free_bytes]
    if args.verify:
        if not args.require_complete or args.require_empty or args.native_evidence is not None or any(v is not None for v in construction):
            parser.error('verification requires only --output --verify --require-complete')
    elif args.complete:
        if not args.require_complete or args.require_empty or args.native_evidence is None or any(v is not None for v in construction):
            parser.error('completion requires only --output --complete --native-evidence --require-complete')
    elif args.require_complete or not args.require_empty or any(v is None for v in construction):
        parser.error('construction requires source/reference/storage options and --require-empty; native evidence is optional')
    try:
        value=verify(args.output)if args.verify else complete(args.output,args.native_evidence)if args.complete else construct(args)
        outcome=value.get('outcome',{'raw_unsigned_equal':True,'reconstruction_complete':False,'finite_native_pairing_bound':False})
        print(encoded({'scope':value['scope'],**outcome,'runtime_eligible':False,'game_qualified':False,
             'distribution_qualified':False}).decode(),end='');return 0
    except Exception as exc:
        output={'reconstruction_complete':False,'runtime_eligible':False,**failure_facts(exc,'requested-operation')}
        print(encoded(output).decode(),end='',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
