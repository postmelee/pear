# SPDX-License-Identifier: MIT
"""Sign the combined CPU/DXMT development candidate using existing authorization."""
from pathlib import Path
import argparse
import fcntl
import plistlib
import shutil
import subprocess
from tools.dxmt.translated_inputs import REPO,admit,read,save,digest,fact,fresh,check_files
from tools.wine.common import need
from tools.fex import memory_wine_runtime as signing,byte_readers


def admit_build(build):
    v=read(build/'build.json')
    need(v['kind']=='translated_graphics_build' and v['passed'] is True,'translated_build_incomplete')
    need(fact(v['input_ref']['path'])==v['input_ref'],'translated_build_input_changed')
    inputs=admit(Path(v['input_ref']['path']).parent)
    need(v['producer_sha256']==digest((REPO/'tools/dxmt/translated_build.py').read_bytes()),'translated_build_producer_changed')
    need(fact(v['fixture_source']['path'])==v['fixture_source'],'translated_fixture_source_changed')
    need(digest((build/'source-files.json').read_bytes())==v['source_sha256'],'translated_source_manifest_changed')
    check_files(build,v['artifacts'])
    need([c['id'] for c in v['commands']]==['configure','driver','fixture'],'translated_build_commands')
    for c in v['commands']:
        need(c['status']=='completed' and c['exit_code']==0 and c['error_code'] is None,'translated_build_command_failed')
        check_files(build,list(c['logs'].values()))
    return v,inputs


def prepare(build,output,fex=None,ntdll_diagnostic=None,owner=None):
    bv,inputs=admit_build(build);output=fresh(output)
    fex_record=None
    if fex:
        from tools.dxmt.translated_fex import admit_build as admit_fex
        fex_record=admit_fex(fex)
        need(fex_record['input_ref']==bv['input_ref'],'translated_fex_pair')
    base=Path(inputs['cpu_runtime']);old=read(base/'runtime.json');graphics=Path(inputs['graphics'])
    from tools.dxmt.translated_loader import admit as admit_loader
    loader,loader_record=admit_loader(inputs,build)
    helpers,_=signing.signing_helpers(Path(inputs['graphics_repo']));reader=helpers.legacy(REPO)
    need(reader.inventory(base/signing.BUNDLE)==old['bundle_inventory'],'translated_base_changed')
    value=dict(kind='translated_graphics_development_runtime',passed=False,guest_execution=False,
               runtime_eligible=False,game_qualified=False,build_ref=fact(build/'build.json'),
               prior_runtime_ref=fact(base/'runtime.json'),commands=[],source_ledger=[])
    try:
        need(shutil.disk_usage(REPO).free>=4*1024**3,'translated_runtime_storage')
        subprocess.run(['/bin/cp','-cRp',str(base/signing.BUNDLE),str(output/signing.BUNDLE)],check=True,timeout=60)
        need(reader.inventory(output/signing.BUNDLE)==old['bundle_inventory'],'translated_clone_changed')
        # Record every byte's immediate source, including the corrected FEX DLL.
        sources={signing.BUNDLE+'/'+r['path']:base/(signing.BUNDLE+'/'+r['path'])
                 for r in old['bundle_inventory'] if r['kind']=='file'}
        overlay={
            'lib/wine/aarch64-unix/winemac.so':build/'objects/dlls/winemac.drv/winemac.so',
            'lib/wine/aarch64-windows/winemac.drv':build/'objects/dlls/winemac.drv/aarch64-windows/winemac.drv',
            'lib/wine/aarch64-unix/winemetal.so':graphics/'dxmt/objects/src/winemetal/unix/winemetal.so',
            'libexec/pear-graphics/device.exe':build/'fixtures/device.exe',
            'libexec/pear-graphics/pairing.exe':graphics/'fixtures/pear-metal-pairing-arm64.exe'}
        for component,name in [('d3d11','d3d11'),('dxgi','dxgi'),('d3d10','d3d10core'),('winemetal','winemetal')]:
            overlay['lib/wine/aarch64-windows/'+name+'.dll']=graphics/('dxmt/objects/src/'+component+'/'+name+'.dll')
        from tools.cpu.ordering import admit_ordering_build
        ordering=Path(inputs['cpu_repo'])/'.build/task6/stage3-native-pe3'
        admit_ordering_build(ordering)
        overlay['libexec/pear-cpu/ordering.exe']=ordering/'ordering.exe'
        value['ordering_build_ref']=fact(ordering/'build.json')
        if owner:
            from tools.dxmt.translated_owner import admit as admit_owner
            correction=admit_owner(owner)
            need(correction['base']==fact(build/'build.json'),'translated_owner_pair')
            overlay['lib/wine/aarch64-windows/ntdll.dll']=Path(correction['artifact']['path'])
            value['owner_correction_ref']=fact(owner/'build.json')
        if ntdll_diagnostic:
            diagnostic=read(ntdll_diagnostic/'diagnostic.json')
            need(diagnostic['kind']=='private_ntdll_lock_stack_diagnostic' and diagnostic['passed'] is True and diagnostic['diagnostic_only'] is True,'translated_diagnostic_incomplete')
            need(fact(diagnostic['artifact']['path'])==diagnostic['artifact'],'translated_diagnostic_artifact')
            for command in diagnostic['commands']:
                need(command['status']=='completed' and command['exit_code']==0,'translated_diagnostic_command')
                check_files(ntdll_diagnostic,list(command['logs'].values()))
            overlay['lib/wine/aarch64-windows/ntdll.dll']=Path(diagnostic['artifact']['path'])
            value['diagnostic_only']=True
            value['diagnostic_ref']=fact(ntdll_diagnostic/'diagnostic.json')
        if fex:
            overlay['lib/wine/aarch64-windows/xtajit64.dll']=fex/'deployment.dll'
            value['fex_correction_ref']=fact(fex/'build.json')
        for rel,source in overlay.items():
            target=signing.PAYLOAD+'/'+rel;p=output/target
            need(not p.is_symlink(),'translated_overlay_link');p.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,p);sources[target]=source
        shutil.copy2(loader,output/signing.MAIN);sources[signing.MAIN]=loader
        value['loader_reservation']=loader_record
        auth=read(base/'authorization.json');auth_commands=[]
        authorization,private,raw_profile=helpers.capture_authorization(auth['original_ref']['path'],output,reader,auth_commands)
        need(raw_profile==(output/signing.BUNDLE/'Contents/embedded.provisionprofile').read_bytes(),'translated_profile_changed')
        (output/'authorized-entitlements.plist').write_bytes(plistlib.dumps(authorization['claims']))
        (output/'authorized-entitlements.plist').chmod(0o600)
        images=[];closures=[]
        for rel,source in sorted(sources.items()):
            raw=(output/rel).read_bytes();need(raw==source.read_bytes(),'translated_copy_changed')
            origin=fact(source);value['source_ledger'].append(dict(runtime_path=rel,origin=origin))
            if raw[:4]!=b'\xcf\xfa\xed\xfe':continue
            info=byte_readers.inspect_macho(output/rel)
            need(info['architectures']==[byte_readers.MACH_ARM64],'translated_host_architecture')
            closure=byte_readers.inspect_closure(output/rel,output/signing.BUNDLE)
            need(all(i['architectures']==[byte_readers.MACH_ARM64] for i in closure),'translated_dependency_architecture')
            closures.append(dict(path=rel,images=closure))
            images.append(dict(path=rel,sha256=digest(raw),size_bytes=len(raw),origin=origin,
                               code_origin=dict(scope='macho_signature_fields_only',verified=False),signature=None))
        print('signing',len(images),'ARM64 images',flush=True)
        recipe=helpers.signing_recipe(output,images,private['identity'])
        for ident,args in recipe:helpers.native(args,output,ident,value['commands'])
        for row in images:
            p=output/row['path'];reader.verify_code_origin(sources[row['path']],p)
            row.update(sha256=digest(p.read_bytes()),size_bytes=p.stat().st_size)
            row['code_origin']['verified']=True
        logs=helpers.verify_commands(output,value['commands'],recipe)
        signed=helpers.signatures_from_logs(output,images,logs,authorization['claims'],private,reader,raw_profile)
        points=dict(old['entrypoints']);points['fixture_pe']=signing.PAYLOAD+'/libexec/pear-graphics/device.exe'
        points['winemetal_native']=signing.PAYLOAD+'/lib/wine/aarch64-unix/winemetal.so'
        fixtures=dict(old['fixtures'])
        rel=signing.PAYLOAD+'/libexec/pear-cpu/ordering.exe'
        fixtures['ordering']=dict(path=rel,sha256=digest((output/rel).read_bytes()))
        for name in ('device','pairing'):
            rel=signing.PAYLOAD+'/libexec/pear-graphics/'+name+'.exe'
            fixtures[name]=dict(path=rel,sha256=digest((output/rel).read_bytes()))
        value.update(passed=True,entrypoints=points,fixtures=fixtures,native_images=signed,dependency_closure=closures,
                     baseline_loader_capacity=old['baseline_loader_capacity'],expected_exit=42,
                     bundle_inventory=reader.inventory(output/signing.BUNDLE),authorization_sha256=digest((output/'authorization.json').read_bytes()),
                     graphics_repo=inputs['graphics_repo'],execution_authorized_by_this_record=False,
                     producer_sha256=digest(Path(__file__).read_bytes()))
        print('combined runtime prepared; guest execution unperformed',flush=True)
    except BaseException as error:value['error']=str(error);raise
    finally:
        save(output/'runtime.json',value);(output/'producer.py').write_bytes(Path(__file__).read_bytes())

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('build','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--fex',type=Path)
    p.add_argument('--ntdll-diagnostic',type=Path)
    p.add_argument('--owner',type=Path)
    a=p.parse_args()
    with open('/private/tmp/pear-native-compilation.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);prepare(a.build.resolve(),a.output,a.fex.resolve() if a.fex else None,a.ntdll_diagnostic.resolve() if a.ntdll_diagnostic else None,a.owner.resolve() if a.owner else None)
