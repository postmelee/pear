#!/usr/bin/env python3
"""Two distinct new-recipe unsigned products plus fresh candidate native evidence.

No normalization or reference-native substitution is supported. Construction,
raw comparison and root-reviewed finite native completion have separate receipts.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import importlib.util
import json
import os
import stat
from pathlib import Path
import sys
from types import SimpleNamespace

HERE=Path(__file__).resolve().parent
NATIVE_SOURCE_PIN='7e1eecef67f5fe6281d4ef2d7eeb4f484273dcf10214dfcbc7b64d6eb6c3f041'


def capture_native_source(root):
    # Read and admit exact helper bytes before executing any helper source.
    root=Path(root).absolute()
    if '..'in root.parts:raise ValueError('native_loader_root')
    directory=os.open(root.anchor,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        for part in root.parts[1:]:
            child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=directory)
            os.close(directory);directory=child
        fd=os.open('deterministic_native.py',os.O_RDONLY|os.O_NOFOLLOW,dir_fd=directory)
        try:
            before=os.fstat(fd)
            if not stat.S_ISREG(before.st_mode)or before.st_size>2**20:raise ValueError('native_loader_bound')
            raw=bytearray()
            while len(raw)<=2**20:
                chunk=os.read(fd,min(65536,2**20+1-len(raw)))
                if not chunk:break
                raw.extend(chunk)
            after=os.fstat(fd)
            identity=lambda row:(row.st_dev,row.st_ino,row.st_mode,row.st_size,row.st_mtime_ns,row.st_ctime_ns)
            if identity(before)!=identity(after)or len(raw)!=before.st_size:raise ValueError('native_loader_changed')
        finally:os.close(fd)
    finally:os.close(directory)
    data=bytes(raw)
    if hashlib.sha256(data).hexdigest()!=NATIVE_SOURCE_PIN:raise ValueError('native_loader_source_changed')
    return data


NATIVE_SOURCE=capture_native_source(HERE)
spec=importlib.util.spec_from_file_location('_pear_deterministic_reproduction_native',HERE/'deterministic_native.py')
native=importlib.util.module_from_spec(spec)
exec(compile(NATIVE_SOURCE,str(HERE/'deterministic_native.py'),'exec'),vars(native))
Error,need,same=native.Error,native.need,native.same
KIND='dxmt_deterministic_pairing_reconstruction'
CONSTRUCTION_KIND='dxmt_deterministic_pairing_construction'
SCOPE='two_fresh_same_host_deterministic_graphics_products'
UNPERFORMED=('compiler_rebuild','native_prerequisite_rebuild','second_machine_reproduction',
             'shader_workload','general_renderer','performance','hybrid_execution',
             'translated_guest_execution','game_qualification','distribution_qualification')
FIELDS={'schema_version','record_kind','scope','producers','source_gates','reference_ref','candidate_ref',
 'qualification_ref','source_signature','inventory_refs','comparison_ref','policy',
 'candidate_constructed_by_this_wrapper','native_pairing_evidence','reconstruction_complete',
 'runtime_eligible','game_qualified','distribution_qualified',*UNPERFORMED}
COMPLETE_FIELDS={'schema_version','record_kind','scope','construction_ref','producers','native_evidence',
                 'reconstruction_complete','normalization','runtime_eligible','game_qualified','distribution_qualified',*UNPERFORMED}


def native_adapter(repo,constructor_root):
    need(native.bounded_source(HERE,'deterministic_native.py')==NATIVE_SOURCE,'native_executed_source_changed')
    return native.adapter(repo,constructor_root,executed_native_sha=NATIVE_SOURCE_PIN)


def encoded(value):return native.encoded(value)
def reference(root,file='build.json',limit=8*1024**2,common=None):
    return {'path':str(root),'sha256':native.digest(common.read_relative(root,file,limit))}
def relative_ref(root,ref,common,limit=8*1024**2):
    need(type(ref)is dict and set(ref)=={'path','sha256'},'det_reproduction_ref')
    raw=common.read_relative(root,ref['path'],limit)
    need(native.digest(raw)==ref['sha256'],'det_reproduction_ref_changed')
    return common.decode_json(raw,limit,max_nodes=1000000)
def save(root,name,value,common):
    common.write_new(root/name,value);return {'path':name,'sha256':native.digest(common.read_relative(root,name,8*1024**2))}


def producers(adapter):
    values=adapter.producers()
    values['tools/dxmt/deterministic_reproduce.py']=native.digest(native.bounded_source(HERE,'deterministic_reproduce.py'))
    return dict(sorted(values.items()))
def sources(root,adapter,expected=None):
    current=producers(adapter)
    if expected is None:
        for path,pin in current.items():
            raw=native.bounded_source(HERE,'deterministic_reproduce.py')if path=='tools/dxmt/deterministic_reproduce.py'else adapter.source_read(adapter.repo,path)
            need(native.digest(raw)==pin,'det_reproduction_source_changed')
            adapter.capture.load('tools/dxmt/build.py').write_bytes(root,'producers/'+path,raw)
    else:
        same(current,expected,'det_reproduction_producer_changed')
        for path,pin in current.items():
            need(native.digest(adapter.common.read_relative(root,'producers/'+path))==pin,'det_reproduction_source_snapshot')
        rows=adapter.capture.load('tools/dxmt/tools.py').files(root/'producers')
        need({row['path']for row in rows}==set(current)and all(row['mode']==0o644 for row in rows),'det_reproduction_source_snapshot_set')
    return current


def inventory_functions(adapter):
    # Preserve the entire original full-unsigned-origin derivation unchanged.
    original=adapter.capture.load('tools/dxmt/reproduce.py')
    names=['file_row','selected_tree','complete_inventory']
    nodes=[node for node in ast.parse(adapter.capture.raw['tools/dxmt/reproduce.py']).body
           if isinstance(node,ast.FunctionDef)and node.name in names]
    need(len(nodes)==len(names)and all(not node.decorator_list for node in nodes),'det_reproduction_inventory_source')
    namespace=dict(vars(original))
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'tools/dxmt/reproduce.py','exec'),namespace)
    return namespace['complete_inventory']

def source_signature(value,adapter):
    original=adapter.capture.load('tools/dxmt/reproduce.py')
    base=original.source_signature(value)
    p=value['recipe_policy']
    need(p['normalization']=='none'and p['source_date_epoch']=='0'
         and p['fresh_native_evidence_required']is True,'det_reproduction_recipe')
    # The fixed compilation directory is independently derived by the new reader.
    # This identity compares source/options, never erases product bytes.
    semantic={key:p[key]for key in ['schema_version','source_date_epoch','stable_wine_objects',
        'debug_compilation_directory_flag','source_interface','shader_options','shader_inputs','normalization',
        'raw_product_comparison_required','fresh_native_evidence_required']}
    return native.digest(encoded({'predecessor_source_signature':base,'recipe':semantic,
        'qualification_ref':value['qualification_ref'],'constructor_sources':value['constructor_sources']}))

def views(adapter,left_root,right_root):
    left=adapter.pair.verify_build(left_root,repo=adapter.repo)
    right=adapter.pair.verify_build(right_root,repo=adapter.repo)
    need(Path(left_root)!=Path(right_root),'det_reproduction_same_root')
    for value in (left,right):need(value['record_kind']==adapter.pair.KIND,'det_reproduction_old_build_refused')
    same(left['qualification_ref'],right['qualification_ref'],'det_reproduction_qualification_mixed')
    signature=source_signature(left,adapter)
    need(signature==source_signature(right,adapter),'det_reproduction_source_settings_changed')
    inventory=inventory_functions(adapter)
    before,origin_before=inventory(left_root,left,repo=adapter.repo)
    after,origin_after=inventory(right_root,right,repo=adapter.repo)
    same(origin_before,origin_after,'det_reproduction_origins_changed')
    compare=adapter.capture.load('tools/dxmt/compare.py')
    comparison=compare.compare_entries(before,after)
    return left,right,before,after,origin_before,comparison,signature


def constructor(args,adapter):
    """Root-only optional second build; both root inputs remain explicit."""
    common=adapter.common;root=common.output_directory(args.output,adapter.repo)
    phase='source_capture';current={}
    try:
        current=sources(root,adapter)
        left=common.owned_directory(args.reference,adapter.repo)
        candidate=Path(args.candidate).absolute()
        need(candidate!=left and candidate!=root and left!=root,'det_reproduction_roots')
        if args.construct:
            need(args.artifact and args.qualification and args.require_empty,'det_reproduction_build_arguments')
            phase='candidate_construct'
            adapter.pair.construct(SimpleNamespace(artifact=args.artifact,qualification=args.qualification,
                output=str(candidate),max_growth_bytes=args.max_growth_bytes,reserve_free_bytes=args.reserve_free_bytes,
                require_empty=True),adapter.repo)
        phase='independent_two_product_replay';candidate=common.owned_directory(candidate,adapter.repo)
        left_value,right_value,before,after,origins,comp,signature=views(adapter,left,candidate)
        refs={}
        for ident,entries in [('reference',before),('candidate',after)]:
            refs[ident]=save(root,ident+'-unsigned-files.json',{'schema_version':1,
                'record_kind':'dxmt_unsigned_inventory','entries':entries},common)
        refs['origins']=save(root,'unsigned-origins.json',origins,common)
        comp_ref=save(root,'comparison.json',comp,common)
        phase='strict_raw_comparison';need(comp['raw_equal']is True,'det_reproduction_unsigned_difference')
        value={'schema_version':1,'record_kind':CONSTRUCTION_KIND,'scope':SCOPE,'producers':current,
            'source_gates':{'constructor_kind':adapter.pair.KIND,'inventory_source_sha256':adapter.capture.pins['tools/dxmt/reproduce.py'],
                'comparison_source_sha256':adapter.capture.pins['tools/dxmt/compare.py'],'old_recipe_reference_accepted':False},
            'reference_ref':reference(left,common=common),'candidate_ref':reference(candidate,common=common),
            'qualification_ref':left_value['qualification_ref'],'source_signature':signature,'inventory_refs':refs,
            'comparison_ref':comp_ref,'policy':{'normalization':'none','raw_file_mode_alias_comparison':'exact',
                'fresh_final_candidate_native_evidence_required':True},
            'candidate_constructed_by_this_wrapper':bool(args.construct),'native_pairing_evidence':'unperformed',
            'reconstruction_complete':False,'runtime_eligible':False,'game_qualified':False,'distribution_qualified':False,
            **{key:'unperformed'for key in UNPERFORMED}}
        need(current==producers(adapter),'det_reproduction_source_changed')
        save(root,'construction.json',value,common);verify_construction(root,adapter);return value
    except BaseException as error:
        failure={'schema_version':1,'record_kind':'dxmt_deterministic_reconstruction_failure','phase':phase,
            'error':getattr(error,'code',type(error).__name__),'producers':current,'reconstruction_complete':False,
            'runtime_eligible':False,'game_qualified':False,'distribution_qualified':False}
        if isinstance(error,OSError):failure['native_error']={'domain':'POSIX','code':error.errno}
        elif getattr(error,'native_error',None)is not None:failure['native_error']=error.native_error
        try:save(root,'failed.json',failure,common)
        except BaseException as secondary:error.evidence_error={'type':type(secondary).__name__,'code':getattr(secondary,'errno',None)}
        raise


def verify_construction(root,adapter):
    common=adapter.common;root=common.owned_directory(root,adapter.repo)
    need(not(root/'failed.json').exists(),'det_reproduction_failed_construction')
    construction_raw=common.read_relative(root,'construction.json')
    value=common.decode_json(construction_raw)
    need(type(value)is dict and set(value)==FIELDS and type(value['schema_version'])is int
         and value['schema_version']==1 and value['record_kind']==CONSTRUCTION_KIND and value['scope']==SCOPE,
         'det_reproduction_construction_fields')
    need(type(value['candidate_constructed_by_this_wrapper'])is bool and value['native_pairing_evidence']=='unperformed'
         and value['reconstruction_complete']is False and all(value[key]is False for key in
            ('runtime_eligible','game_qualified','distribution_qualified'))
         and all(value[key]=='unperformed'for key in UNPERFORMED),'det_reproduction_construction_scope')
    sources(root,adapter,value['producers'])
    same(value['source_gates'],{'constructor_kind':adapter.pair.KIND,
        'inventory_source_sha256':adapter.capture.pins['tools/dxmt/reproduce.py'],
        'comparison_source_sha256':adapter.capture.pins['tools/dxmt/compare.py'],'old_recipe_reference_accepted':False},
        'det_reproduction_source_gates_changed')
    same(value['policy'],{'normalization':'none','raw_file_mode_alias_comparison':'exact',
        'fresh_final_candidate_native_evidence_required':True},'det_reproduction_policy_changed')
    roots=[]
    for key in ('reference_ref','candidate_ref'):
        ref=value[key];need(type(ref)is dict and set(ref)=={'path','sha256'},'det_reproduction_build_ref')
        selected=common.owned_directory(ref['path'],adapter.repo)
        same(ref,reference(selected,common=common),'det_reproduction_build_changed');roots.append(selected)
    left,right,before,after,origins,comp,signature=views(adapter,*roots)
    need(signature==value['source_signature'],'det_reproduction_signature_changed')
    same(value['qualification_ref'],left['qualification_ref'],'det_reproduction_qualification_changed')
    need(set(value['inventory_refs'])=={'reference','candidate','origins'},'det_reproduction_inventory_set')
    for ident,entries in [('reference',before),('candidate',after)]:
        ref=value['inventory_refs'][ident];need(ref['path']==ident+'-unsigned-files.json','det_reproduction_inventory_path')
        same(relative_ref(root,ref,common),{'schema_version':1,'record_kind':'dxmt_unsigned_inventory','entries':entries},
             'det_reproduction_inventory_changed')
    need(value['inventory_refs']['origins']['path']=='unsigned-origins.json','det_reproduction_origins_path')
    same(relative_ref(root,value['inventory_refs']['origins'],common),origins,'det_reproduction_origins_changed')
    need(value['comparison_ref']['path']=='comparison.json','det_reproduction_comparison_path')
    same(relative_ref(root,value['comparison_ref'],common),comp,'det_reproduction_comparison_changed')
    need(comp['raw_equal']is True,'det_reproduction_unsigned_difference')
    need(common.read_relative(root,'construction.json')==construction_raw,'det_reproduction_construction_changed')
    for key,selected in zip(('reference_ref','candidate_ref'),roots):
        same(value[key],reference(selected,common=common),'det_reproduction_build_changed')
    same(value['producers'],producers(adapter),'det_reproduction_producer_changed')
    return value


def native_binding(run_root,candidate_ref,adapter):
    common=adapter.common;run_root=common.owned_directory(run_root,adapter.repo)
    raw=common.read_relative(run_root,'run.json');run=common.decode_json(raw)
    need(run['record_kind']==native.KIND_MAP['dxmt_pairing_run'],'det_reproduction_old_native_run_refused')
    runtime_root=common.owned_directory(run['runtime_ref']['path'],adapter.repo)
    runtime_raw=common.read_relative(runtime_root,'runtime.json')
    need(native.digest(runtime_raw)==run['runtime_ref']['sha256'],'det_reproduction_native_runtime_changed')
    runtime=common.decode_json(runtime_raw)
    need(runtime['record_kind']==native.KIND_MAP['dxmt_pairing_runtime'],'det_reproduction_old_native_runtime_refused')
    same(runtime['build_ref'],candidate_ref,'det_reproduction_fresh_candidate_native_required')
    review=common.read_relative(run_root,'diagnostics-review.json',2*1024**2)
    observed=adapter.verify_evidence(run_root)
    need(observed['record_kind']==native.KIND_MAP['dxmt_pairing_native_evidence']
         and observed['scope']==native.SCOPE_MAP['finite_native_metal_api_pairing']
         and observed['finite_native_scope_complete']is True and observed['metal_api_validation']=='reviewed_no_errors'
         and observed['native_pairing_observed']is True and observed['ordinary_arm64_pe_execution_performed']is True
         and all(observed[key]is False for key in ('runtime_eligible','game_qualified','distribution_qualified'))
         and all(observed[key]=='unperformed'for key in ('shader_workload','general_renderer','performance',
            'hybrid_execution','translated_guest_execution','game_qualification','distribution_qualification')),
         'det_reproduction_native_scope')
    need(common.read_relative(run_root,'run.json')==raw
         and common.read_relative(runtime_root,'runtime.json')==runtime_raw
         and common.read_relative(run_root,'diagnostics-review.json',2*1024**2)==review,
         'det_reproduction_native_changed')
    return {'run_ref':{'path':str(run_root),'sha256':native.digest(raw)},'runtime_ref':run['runtime_ref'],
        'diagnostics_review_ref':{'path':'diagnostics-review.json','sha256':native.digest(review)},
        'source_build_ref':candidate_ref,'observations':observed,'origin':'fresh_final_candidate',
        'new_native_execution_performed':True,'permission_transfer':'not_inferred'}


def complete(root,run_root,adapter):
    root=adapter.common.owned_directory(root,adapter.repo);value=verify_construction(root,adapter)
    observed=native_binding(run_root,value['candidate_ref'],adapter)
    result={'schema_version':1,'record_kind':KIND,'scope':SCOPE,
        'construction_ref':{'path':'construction.json','sha256':native.digest(adapter.common.read_relative(root,'construction.json'))},
        'producers':producers(adapter),'native_evidence':observed,'reconstruction_complete':True,
        'normalization':'none','runtime_eligible':False,'game_qualified':False,'distribution_qualified':False,
        **{key:'unperformed'for key in UNPERFORMED}}
    save(root,'reproduction.json',result,adapter.common);return verify(root,adapter)


def verify(root,adapter):
    common=adapter.common;root=common.owned_directory(root,adapter.repo)
    value=common.decode_json(common.read_relative(root,'reproduction.json'))
    need(type(value)is dict and set(value)==COMPLETE_FIELDS and type(value['schema_version'])is int
         and value['schema_version']==1 and value['record_kind']==KIND and value['scope']==SCOPE,
         'det_reproduction_fields')
    need(value['reconstruction_complete']is True and value['normalization']=='none'
         and all(value[key]is False for key in ('runtime_eligible','game_qualified','distribution_qualified'))
         and all(value[key]=='unperformed'for key in UNPERFORMED),'det_reproduction_scope')
    same(value['producers'],producers(adapter),'det_reproduction_producer_changed')
    ref=value['construction_ref'];need(ref['path']=='construction.json','det_reproduction_construction_ref')
    relative_ref(root,ref,common);construction=verify_construction(root,adapter)
    actual=native_binding(value['native_evidence']['run_ref']['path'],construction['candidate_ref'],adapter)
    same(value['native_evidence'],actual,'det_reproduction_native_changed');return value


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',required=True);parser.add_argument('--constructor-root',required=True)
    choices=parser.add_mutually_exclusive_group(required=True)
    for name in ('construct','compare','verify-construction','complete','verify'):choices.add_argument('--'+name,action='store_true')
    parser.add_argument('--artifact');parser.add_argument('--qualification');parser.add_argument('--reference')
    parser.add_argument('--candidate');parser.add_argument('--output',required=True);parser.add_argument('--native-evidence')
    parser.add_argument('--max-growth-bytes',type=int,default=2*1024**3)
    parser.add_argument('--reserve-free-bytes',type=int,default=4*1024**3)
    parser.add_argument('--require-empty',action='store_true');parser.add_argument('--require-complete',action='store_true')
    args=parser.parse_args(argv)
    try:
        with native_adapter(args.repo,args.constructor_root)as adapter:
            if args.construct or args.compare:
                need(args.reference and args.candidate and args.require_empty,'det_reproduction_compare_arguments')
                result=constructor(args,adapter)
            elif args.verify_construction:result=verify_construction(args.output,adapter)
            elif args.complete:
                need(args.native_evidence,'det_reproduction_native_evidence_required')
                result=complete(args.output,args.native_evidence,adapter)
            else:result=verify(args.output,adapter)
            if args.require_complete:need(result.get('reconstruction_complete')is True,'det_reproduction_incomplete')
            print(encoded(result).decode(),end='');return 0
    except Exception as error:
        failure={'reconstruction_complete':False,'runtime_eligible':False,
            'error':getattr(error,'code',type(error).__name__)}
        if isinstance(error,OSError):failure['native_error']={'domain':'POSIX','code':error.errno}
        elif getattr(error,'native_error',None)is not None:failure['native_error']=error.native_error
        print(encoded(failure).decode(),end='',file=sys.stderr)
        return 3 if getattr(error,'code',None)=='det_reproduction_incomplete'else 1


if __name__=='__main__':raise SystemExit(main())
