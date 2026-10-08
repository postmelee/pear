#!/usr/bin/env python3
"""Private full-FEX construction proposal; compilation only, no initialization.

This separate component constructor preserves all historical producer/source
identities. Only root may admit actual serial commands after reviewing this draft.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import shutil
import stat
import sys

if __package__:
    from . import memory_fex_check as verifier, memory_wine_build as monitor, build as original
    from .common import Error, REPO, need, operation_output, write_json, sha256, load_json
else:
    # The sibling tools.py is a module, so remove this executable directory
    # before importing the repository's top-level tools namespace.
    script_directory=Path(__file__).resolve().parent
    sys.path[:]=[entry for entry in sys.path if Path(entry or os.getcwd()).resolve()!=script_directory]
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
    from tools.fex import memory_fex_check as verifier, memory_wine_build as monitor, build as original
    from tools.fex.common import Error, REPO, need, operation_output, write_json, sha256, load_json

MAX_GROWTH=2*1024**3
RESERVE_FREE=2*1024**3
MINIMUM_FREE=8*1024**3


def observed_error(exc):
    value={'code':getattr(exc,'code',type(exc).__name__),'exception_type':type(exc).__name__}
    if isinstance(exc,OSError):value['native_error']={'domain':'errno','code':exc.errno}
    elif type(getattr(exc,'native_error',None)) is dict:value['native_error']=dict(exc.native_error)
    return value


def preserve_failure(root,value,exc):
    value.update(passed=False,primary_error=observed_error(exc))
    try:write_json(root/'failure.json',value)
    except BaseException as failure:
        # Never replace the original observed source/tool/storage failure.
        try:exc.failure_record_error=observed_error(failure)
        except (AttributeError,TypeError):pass


def snapshot(root,paths):
    directory=root/'inputs';directory.mkdir(mode=0o700);rows=[];total=0
    for i,path in enumerate(paths):
        raw,_=verifier.regular_bytes(path.parent,path.name,8*1024**2)
        total+=len(raw);need(total<=128*1024**2,'fex_memory_snapshot_total')
        name=f'inputs/{i:04d}.bin'
        with (root/name).open('xb') as out:out.write(raw)
        (root/name).chmod(0o600)
        rows.append({'source':str(path),'copy':name,'sha256':verifier.H(raw),'size_bytes':len(raw)})
    return rows


def copy_source(origin,destination,rows):
    """Fresh regular-only current bytes; never copies prior object/build trees."""
    destination.mkdir(mode=0o700)
    for row in rows:
        raw,mode=verifier.regular_bytes(origin,row['path'],verifier.MAX_SOURCE_FILE)
        need(len(raw)==row['size_bytes'] and verifier.H(raw)==row['sha256'] and mode==row['mode'],
             'fex_memory_copy_origin_changed')
        target=destination.joinpath(*verifier.relative(row['path']))
        target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        with target.open('xb') as out:out.write(raw)
        target.chmod(mode)
    need(verifier.source_inventory(destination)==rows,'fex_memory_copy_inventory')


def resource_gate(root,max_growth,reserve):
    need(type(max_growth) is int and 512*1024**2<=max_growth<=8*1024**3
         and type(reserve) is int and 2*1024**3<=reserve<=8*1024**3,'fex_memory_resource_bounds')
    observed=monitor.storage_size(root);free=shutil.disk_usage(root).free
    need(observed<=max_growth and free>=reserve,'fex_memory_resource_exhausted')
    return observed,free


def construct(baseline,projection,derivatives,wine_build,output,*,max_growth=MAX_GROWTH,
              reserve_free=RESERVE_FREE,repo=REPO,source_helper):
    root=operation_output(output,repo_root=repo,require_empty=True)
    value={'schema_version':1,'record_kind':'fex_memory_modules_build','scope':'fex_component',
        'phase':'input_admission','commands':[],'passed':False,'modules_built_not_loaded':False,
        'qualification':dict(verifier.QUALIFICATION),**dict.fromkeys(verifier.FALSE_FLAGS,False)}
    try:
        for path in (baseline,projection,derivatives,wine_build):
            need(Path(path).is_absolute() and Path(path).resolve(strict=True)==Path(path),
                 'fex_memory_input_root_alias')
        # Original full proof is admitted on its original source/output only.
        old=original.verify_build(Path(baseline))
        derived,projection_ref=verifier.projection_gate(projection,baseline,derivatives,source_helper=source_helper)
        wire,wire_ref=verifier.wire_gate(wine_build)
        value['bindings']={'baseline':{'root':str(baseline),'sha256':verifier.BASE_BUILD_SHA},
            'projection':projection_ref,'derivatives':{'root':str(derivatives),'sha256':verifier.GRAPH_SHA},
            'wine_build':wire_ref}
        value['producer_sha256']={p:sha256(Path(repo)/p) for p in verifier.LOCAL_PRODUCERS}
        value['phase']='storage_admission'
        before=shutil.disk_usage(root).free
        need(before>=MINIMUM_FREE,'fex_memory_build_disk_admission')
        resource_gate(root,max_growth,reserve_free)
        value['resources']={'minimum_free_bytes':MINIMUM_FREE,'max_growth_bytes':max_growth,
            'reserve_free_bytes':reserve_free,'free_before_bytes':before,'owned_after_bytes':0,
            'free_after_bytes':before,'parallel_jobs':1,'peak_observation':'unknown',
            'owned_bytes_scope':'regular_payload_excluding_control_records_v1'}
        value['phase']='input_snapshot'
        value['input_snapshots']=snapshot(root,verifier.snapshot_sources(repo,baseline,projection,
                                                                       derivatives,wine_build,old,source_helper=source_helper))
        value['phase']='source_copy'
        copy_source(Path(projection)/'source',root/'source',derived['source_files'])
        value['materialized_source']=write_json(root/'materialized-source.json',{
            'schema_version':1,'record_kind':'fex_memory_materialized_source','scope':'fex_component',
            'files':derived['source_files']})
        (root/'wire/wine').mkdir(parents=True,mode=0o700)
        with (root/'wire/wine/pear_fex_memory.h').open('xb') as out:out.write(wire)
        (root/'wire/wine/pear_fex_memory.h').chmod(0o644)
        value['wire']={'path':'wire/wine/pear_fex_memory.h','sha256':verifier.H(wire),'size_bytes':len(wire)}
        value['source_interfaces']=verifier.prepare.source_interfaces(root/'source')
        need(len(value['source_interfaces']['services'])==8 and
             [len(m['exports']) for m in value['source_interfaces']['modules']]==[20,23],
             'fex_memory_source_abi_changed')
        for name in ('fixtures','install'):(root/name).mkdir(mode=0o700)
        lock=load_json(old['bindings']['toolchain']['path'])
        config=original.validate_config(load_json(old['bindings']['config']['path']),old['bindings']['inputs']['sha256'])
        features=original.host_metadata(Path(old['bindings']['host_metadata']['path']));cross=old['cross']
        recipe=verifier.recipe(root,old['bindings']['tools']['path'],lock,features,config,cross)
        environment=original.complete_environment(lock,cross)
        # HOME is omitted, never replaced. Existing explicit SDK/deployment/PATH
        # policy is retained; no source script or arbitrary caller command runs.
        for ident,argv in recipe.items():
            value['phase']=ident;resource_gate(root,max_growth,reserve_free)
            timeout=3600 if ident.endswith('.build') and not ident.startswith('native') else 600
            monitor.execute(root,ident,argv,str(root),environment,timeout,value['commands'],max_growth,reserve_free)
        for name in ('libarm64ecfex.so','libwow64fex.so'):
            raw,mode=verifier.regular_bytes(root,'native/'+name,64*1024**2)
            with (root/'install'/name).open('xb') as out:out.write(raw)
            (root/'install'/name).chmod(mode)
        value['phase']='artifact_replay'
        value['artifacts'],value['module_proofs']=verifier.inspect_modules(root,cross,features,config,baseline)
        files=verifier.output_inventory(root)
        value['output_manifest']=write_json(root/'output-files.json',{'schema_version':1,
            'record_kind':'fex_memory_output_files','scope':'fex_component','files':files})
        owned,free=resource_gate(root,max_growth,reserve_free)
        need(owned+16*1024**2<=max_growth,'fex_memory_control_record_budget')
        value['resources'].update(owned_after_bytes=sum(row['size_bytes'] for row in files),free_after_bytes=free)
        need(value['producer_sha256']=={p:sha256(Path(repo)/p) for p in verifier.LOCAL_PRODUCERS},
             'fex_memory_producer_changed_during_build')
        value.update(modules_built_not_loaded=True,passed=True)
        value.pop('phase')
        write_successful_build_record(root,value)
        verifier.verify_build(root,repo)
        return value
    except BaseException as exc:
        preserve_failure(root,value,exc);raise


def write_successful_build_record(root,value):
    # Serialize/roundtrip completely before creating the fixed owned record.
    # A failed scope, byte/node bound or grammar leaves build.json absent.
    raw=verifier.encoded_successful_build_record(value)
    with (Path(root)/'build.json').open('xb') as stream:stream.write(raw)
    (Path(root)/'build.json').chmod(0o600)
    observed,written=verifier.successful_build_record_bytes(root)
    need(written==raw and observed==value,'fex_memory_written_receipt_changed')
    return {'path':'build.json','sha256':verifier.H(raw)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','projection','derivatives','wine-build','output','source-helper'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--jobs',type=int,choices=(1,),default=1)
    parser.add_argument('--max-growth-bytes',type=int,default=MAX_GROWTH)
    parser.add_argument('--reserve-free-bytes',type=int,default=RESERVE_FREE)
    parser.add_argument('--require-empty',action='store_true',required=True);args=parser.parse_args()
    try:
        construct(*(Path(getattr(args,k)).absolute() for k in ('baseline','projection','derivatives','wine_build','output')),
            max_growth=args.max_growth_bytes,reserve_free=args.reserve_free_bytes,source_helper=args.source_helper)
        print('PASS: full modules built, not loaded; source runtime/metadata/initialization unqualified');return 0
    except (Error,OSError,ValueError,KeyError,IndexError,UnicodeError) as exc:
        print('FAIL: '+getattr(exc,'code',type(exc).__name__),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
