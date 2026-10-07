#!/usr/bin/env python3
"""Build an isolated development Wine/FEX pair; never execute Wine here."""
from pathlib import Path
import argparse,fcntl,hashlib,json,os,plistlib,shutil,sys
if not __package__:
    here=Path(__file__).resolve().parent
    sys.path[:]=[p for p in sys.path if Path(p or os.getcwd()).resolve()!=here]
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.fex.common import REPO,need,relative
from tools.fex import memory_wine_runtime as reuse,byte_readers
H=lambda b:hashlib.sha256(b).hexdigest()

def prepare(base,paired,fex,linked,fixture,helper,profile,signing_source,output):
    paths=[Path(x).resolve(strict=True) for x in (base,paired,fex,linked,fixture,helper,signing_source)]
    base,paired,fex,linked,fixture,helper,signing_source=paths
    root=Path(output).absolute()
    need(root.parent==REPO/'.build/task5' and not root.exists(),'integration_fresh_output')
    # Preparation only clones/signs the bundle. Cold and initialized-prefix
    # execution have separate storage gates in integration_run.py.
    need(shutil.disk_usage(REPO).free>=5*1024**3//2,'integration_storage')
    expected={'paired':'5e4ab7c106939179b50a128f00da1f9cdc2cf981d6ec9a1cef88f6b43aad2c25',
              'fex':'9d4e431ee002099fde7c681327747cbfe653b33eae222dc0152e489dd9d1d304',
              'linked':'8581ae239b641b38f450e33f45ede8dcc38ea5df0ea1c275e8f1e5f5977be6e0',
              'fixture':'ee83588eb43d0a6cb7c0c4e8618c682f36cb631efa00eaecd97720c482d82547'}
    linked_digest=H((linked/'control.json').read_bytes())
    need(linked_digest in {expected['linked'],
         '076351b567bd8603495f3da36472fdd957aac246a1407022c7dfb7da9eb628c0',
         '03fca84ffa0db3f923bd4da1019593154c4a911db84a4bfa831b0b728d36705f',
         'fd6d264ddb7c5585e01be4e81a71c25ef726215c1b6305286e94d63eda42b00d',
         '5998bfa7663144c46d14e50e00ee525d6e9353192c1cac583dcbb5558a6711b5',
         'e68a1d2b06ac2e6a3e94b52394f81d445ca4f80af776943cb95d14ac3472698d'},
         'integration_linked_receipt')
    expected['linked']=linked_digest
    fixture_digest=H((fixture/'control.json').read_bytes())
    need(fixture_digest in {expected['fixture'],
         '36ee3f0424b61a5e5bd9150ed1ed3075f48229563bcbef7b32a0d82c60357234'},
         'integration_fixture_receipt')
    expected['fixture']=fixture_digest
    records={}
    for name,path in [('paired',paired/'control.json'),('fex',fex/'build.json'),('linked',linked/'control.json'),('fixture',fixture/'control.json')]:
        raw=path.read_bytes();need(H(raw)==expected[name],'integration_component_receipt');records[name]=json.loads(raw)
    base_record=json.loads((base/'build.json').read_text())
    raw=(base/'installed-files.json').read_bytes();need(H(raw)==base_record['artifacts_manifest']['sha256'],'integration_baseline_manifest')
    inventory=json.loads(raw);root.mkdir(mode=0o700)
    helpers,_=reuse.signing_helpers(signing_source);reader=helpers.legacy(REPO)
    commands=[];authorization_commands=[];ledger=[];copies=[]
    value={'scope':'fex_component','kind':'integrated_development_runtime','passed':False,
           'wine_execution':False,'guest_execution':False,'input_receipts':expected,
           'baseline_build_sha256':H((base/'build.json').read_bytes()),'commands':commands,
           'test_instrumentation':records['linked'].get('test_instrumentation')}
    try:
        authorization,private,raw_profile=helpers.capture_authorization(profile,root,reader,authorization_commands)
        sources={};selected={}
        for row in inventory['files']:
            sources[row['path']]=(base/'install',row['path'],row['sha256'],row['mode'])
        for row in records['paired']['outputs']:
            target=reuse.NTDLL if row['path'].endswith('.so') else reuse.NTDLL_PE
            sources[target]=(paired,row['path'],row['sha256'],0o755)
        dll=next(r for r in records['linked']['outputs'] if r['path']=='deployment.dll')
        sources['lib/wine/aarch64-windows/xtajit64.dll']=(linked,dll['path'],dll['sha256'],0o755)
        unix=next(r for r in records['fex']['artifacts'] if r['path']=='install/libarm64ecfex.so')
        sources['lib/wine/aarch64-unix/libarm64ecfex.so']=(fex,unix['path'],unix['sha256'],0o755)
        sources['libexec/pear-fex-integration/first-dispatch.exe']=(fixture,'first-dispatch.exe',records['fixture']['pe_sha256'],0o755)
        sources['libexec/pear-fex-memory/owner-launch']=(helper.parent,helper.name,H(helper.read_bytes()),0o755)
        for target,(origin,path,digest,mode) in sorted(sources.items()):
            destination=reuse.MAIN if target==reuse.LOADER else reuse.PAYLOAD+'/'+target
            raw=(origin/path).read_bytes();need(H(raw)==digest,'integration_artifact_changed')
            row={'runtime_path':destination,'sha256':digest,'size_bytes':len(raw),'mode':mode,
                 'origin':{'role':'integration-input','path':path,'sha256':digest},'origin_root':str(origin)}
            copies.append(reuse.copy_payload(root,row,origin,origin,helpers,prefer_clone=True));ledger.append(row)
        for row in inventory['symlinks']:
            relative(row['path']);path=root/reuse.PAYLOAD/row['path'];path.parent.mkdir(parents=True,exist_ok=True)
            need(not path.exists() and not path.is_symlink(),'integration_link_collision');path.symlink_to(row['target'])
        path=root/reuse.PAYLOAD/reuse.LOADER;path.parent.mkdir(parents=True,exist_ok=True);path.symlink_to(os.path.relpath(root/reuse.MAIN,path.parent))
        path=root/reuse.NTDLL_ALIAS;path.symlink_to(os.path.relpath(root/reuse.PAYLOAD/reuse.NTDLL,path.parent))
        helpers.stage3.write_bytes(root,reuse.BUNDLE+'/Contents/embedded.provisionprofile',raw_profile,0o600)
        helpers.stage3.write_bytes(root,reuse.BUNDLE+'/Contents/Info.plist',plistlib.dumps(reuse.INFO),0o644)
        helpers.stage3.write_bytes(root,'authorized-entitlements.plist',plistlib.dumps(authorization['claims']),0o600)
        images=[];closures=[]
        for row in ledger:
            p=root/row['runtime_path']
            with p.open('rb') as stream:magic=stream.read(4)
            if magic!=b'\xcf\xfa\xed\xfe':continue
            info=byte_readers.inspect_macho(p);need(info['architectures']==[byte_readers.MACH_ARM64],'integration_host_architecture')
            closure=byte_readers.inspect_closure(p,root/reuse.BUNDLE)
            need(all(v['architectures']==[byte_readers.MACH_ARM64] for v in closure),'integration_dependency_architecture')
            closures.append({'path':row['runtime_path'],'images':closure})
            images.append({'path':row['runtime_path'],'sha256':row['sha256'],'size_bytes':row['size_bytes'],
                           'origin':row['origin'],'code_origin':{'scope':'macho_signature_fields_only','verified':True},'signature':None})
        print('signing',len(images),'ARM64 images',flush=True)
        for ident,args in helpers.signing_recipe(root,images,private['identity']):helpers.native(args,root,ident,commands)
        for row in images:
            p=root/row['path'];source=next(r for r in ledger if r['runtime_path']==row['path'])
            reader.verify_code_origin(Path(source['origin_root'])/source['origin']['path'],p)
            row.update(sha256=H(p.read_bytes()),size_bytes=p.stat().st_size)
        logs=helpers.verify_commands(root,commands,helpers.signing_recipe(root,images,private['identity']))
        signed=helpers.signatures_from_logs(root,images,logs,authorization['claims'],private,reader,raw_profile)
        points=reuse.entrypoints();points['fixture_pe']=reuse.PAYLOAD+'/libexec/pear-fex-integration/first-dispatch.exe'
        value.update(passed=True,entrypoints=points,native_images=signed,dependency_closure=closures,
                     baseline_loader_capacity=base_record['arena_capacity'],bundle_inventory=reader.inventory(root/reuse.BUNDLE),
                     source_ledger=ledger,copies=copies,authorization_sha256=H((root/'authorization.json').read_bytes()),
                     memory_profile={'scope':'first_dispatch_estimate_not_measurement','additional_bookkeeping_budget_bytes':16*1024**2,
                       'single_jit_virtual_bytes':1588985856,'owner_fixed_bound_bytes':262144,
                       'wine_protection_leaf_bytes':1048576,'wine_leaf_coverage_bytes':4294967296,
                       'bitmap_virtual_bytes_upper_bound':4294967296,
                       'expected_additional_protection_leaves_at_most':4,'view_block_headroom_bytes':2097152,
                       'bitmap_touched_backing_headroom_bytes':262144,'remaining_headroom_includes_stack_and_alignment':True,
                       'ordinary_engine_allocations_included':False,'actual_cost_observed':False},
                     execution_authorized_by_this_record=False)
        print(json.dumps({'passed':True,'native_images':len(signed),'guest_execution':False}))
    except BaseException as error:value['error']=str(error);raise
    finally:
        (root/'runtime.json').write_text(json.dumps(value,indent=2)+'\n')
        (root/'producer.py').write_bytes(Path(__file__).read_bytes())

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('base','paired','fex','linked','fixture','helper','profile','signing-source','output'):p.add_argument('--'+key,required=True)
    args=p.parse_args()
    with open('/private/tmp/pear-native-compilation.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        prepare(args.base,args.paired,args.fex,args.linked,args.fixture,args.helper,args.profile,args.signing_source,args.output)
