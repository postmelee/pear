# SPDX-License-Identifier: MIT
"""Pair repaired FEX with the current graphics candidate and exact failure PEs."""
from pathlib import Path
import argparse,copy,fcntl,plistlib,shutil,subprocess
from tools.dxmt.translated_inputs import REPO,read,save,fact,fresh,digest,need
from tools.dxmt.translated_present_runtime import admit as admit_parent
from tools.dxmt.translated_repair_build import admit as admit_build
from tools.fex import memory_wine_runtime as signing,byte_readers
TRANSLATOR=signing.PAYLOAD+'/lib/wine/aarch64-windows/xtajit64.dll'
ORIGINALS={'rendering-original':('render-build1','rendering.exe','32b5d3d68804a2ad627f6e53e0b456474929a3f024ccbcea736bbb3c8e1de0d0','40f5c39a5cabe5b5ac6f7833b2c17d09707cb0880c7e37ada915b022243ed1f1'),
 'presentation-original':('present-build1','presentation.exe','75df86a6eae999dce6cb9e72c3ceb743ff2da0be7a8e21b67e83225c94dabb07','d0f2049d6a0efd982c51bbd2abcb25e6ed7c226136b038fb16599968c0e66b86')}

def originals():
    result={}
    for key,(folder,exe,source_sha,pe_sha) in ORIGINALS.items():
        root=REPO/'.build/task8'/folder;v=read(root/'build.json');artifact=fact(root/exe);source=fact(root/'fixture-source.cpp')
        need(v['passed'] and artifact==v['artifact'] and artifact['sha256']==pe_sha and source['sha256']==source_sha==v['sources'][0]['sha256'],'repair_original_changed')
        result[key]=dict(build_ref=fact(root/'build.json'),artifact=artifact,source_snapshot=source,path=signing.PAYLOAD+'/libexec/pear-graphics/'+key+'.exe')
    return result

def projection(parent,runtime,old,new,reader,build,fixtures):
    before={r['path']:r for r in old['bundle_inventory']};after={r['path']:r for r in reader.inventory(runtime/signing.BUNDLE)}
    extra={r['path'][len(signing.BUNDLE)+1:] for r in fixtures.values()};need(set(after)==set(before)|extra,'repair_inventory')
    native={r['path'][len(signing.BUNDLE)+1:] for r in old['native_images']}
    translator=TRANSLATOR[len(signing.BUNDLE)+1:];changed=[]
    for p,row in before.items():
        if row==after[p]:continue
        need(row['kind']=='file' and after[p]['kind']=='file','repair_file_type')
        if p in native:reader.verify_code_origin(parent/signing.BUNDLE/p,runtime/signing.BUNDLE/p)
        elif p==translator:need((runtime/TRANSLATOR).read_bytes()==Path(build['artifact']['path']).read_bytes(),'repair_translator_bytes')
        else:need(p=='Contents/_CodeSignature/CodeResources','repair_other_payload_changed')
        changed.append(p)
    need(translator in changed,'repair_translator_unchanged')
    need([r['path'] for r in old['native_images']]==[r['path'] for r in new['native_images']],'repair_native_set')
    return dict(changed_files=changed,changed_guest_component='xtajit64.dll',native_host_code_unchanged=True,cpu_code_unchanged=False,added_original_fixtures=sorted(extra))

def admit(runtime):
    v=read(runtime/'runtime.json');o=v['unaligned_repair_overlay']
    need(v['passed'] and o['producer']==fact(Path(__file__)),'repair_runtime_producer')
    for key in ('parent_ref','build_ref'):need(fact(o[key]['path'])==o[key],'repair_runtime_reference')
    parent=Path(o['parent_ref']['path']).parent;old=admit_parent(parent);build=admit_build(Path(o['build_ref']['path']).parent);fixtures=originals()
    need(o['originals']==fixtures and v['presentation_overlay']==old['presentation_overlay'] and v['rendering_overlay']==old['rendering_overlay'],'repair_history_changed')
    helpers,_=signing.signing_helpers(Path(old['graphics_repo']));reader=helpers.legacy(REPO)
    need(reader.inventory(runtime/signing.BUNDLE)==v['bundle_inventory'],'repair_payload_changed')
    for row in v['dependency_closure']:
        need(byte_readers.inspect_closure(runtime/row['path'],runtime/signing.BUNDLE)==row['images'],'repair_closure_changed')
        need(all(i['architectures']==[byte_readers.MACH_ARM64] for i in row['images']),'repair_architecture')
    for key,r in fixtures.items():
        need((runtime/r['path']).read_bytes()==Path(r['artifact']['path']).read_bytes() and v['fixtures'][key]==dict(path=r['path'],sha256=r['artifact']['sha256']),'repair_original_payload')
    need(projection(parent,runtime,old,v,reader,build,fixtures)==o['projection'],'repair_projection_changed')
    return v

def prepare(parent,build,output):
    old=admit_parent(parent);b=admit_build(build);fixtures=originals();need(shutil.disk_usage(REPO).free>=4*1024**3,'repair_runtime_storage');out=fresh(output)
    v=copy.deepcopy(old);v.update(passed=False,commands=[])
    helpers,_=signing.signing_helpers(Path(old['graphics_repo']));reader=helpers.legacy(REPO)
    try:
        subprocess.run(['/bin/cp','-cRp',str(parent/signing.BUNDLE),str(out/signing.BUNDLE)],check=True,timeout=60)
        shutil.copy2(b['artifact']['path'],out/TRANSLATOR)
        for r in fixtures.values():shutil.copy2(r['artifact']['path'],out/r['path'])
        auth=read(parent/'authorization.json');commands=[]
        authorization,private,raw=helpers.capture_authorization(auth['original_ref']['path'],out,reader,commands)
        need(raw==(out/signing.BUNDLE/'Contents/embedded.provisionprofile').read_bytes(),'repair_profile_changed')
        (out/'authorized-entitlements.plist').write_bytes(plistlib.dumps(authorization['claims']));(out/'authorized-entitlements.plist').chmod(0o600)
        images=copy.deepcopy(old['native_images'])
        for r in images:r['origin']=fact(parent/r['path']);r['signature']=None
        recipe=helpers.signing_recipe(out,images,private['identity']);print('signing CPU-repair candidate',flush=True)
        for ident,args in recipe:helpers.native(args,out,ident,v['commands'])
        for r in images:
            reader.verify_code_origin(Path(r['origin']['path']),out/r['path']);r.update(sha256=digest((out/r['path']).read_bytes()),size_bytes=(out/r['path']).stat().st_size)
        logs=helpers.verify_commands(out,v['commands'],recipe)
        v['native_images']=helpers.signatures_from_logs(out,images,logs,authorization['claims'],private,reader,raw)
        v['bundle_inventory']=reader.inventory(out/signing.BUNDLE)
        v['dependency_closure']=[dict(path=r['path'],images=byte_readers.inspect_closure(out/r['path'],out/signing.BUNDLE)) for r in v['native_images']]
        for key,r in fixtures.items():v['fixtures'][key]=dict(path=r['path'],sha256=r['artifact']['sha256'])
        v['authorization_sha256']=digest((out/'authorization.json').read_bytes())
        v['source_ledger']=[dict(runtime_path=signing.BUNDLE+'/'+r['path'],origin=fact(parent/signing.BUNDLE/r['path'])) for r in old['bundle_inventory'] if r['kind']=='file']
        for r in v['source_ledger']:
            if r['runtime_path']==TRANSLATOR:r['origin']=b['artifact']
        v['source_ledger'] += [dict(runtime_path=r['path'],origin=r['artifact']) for r in fixtures.values()]
        v['unaligned_repair_overlay']=dict(parent_ref=fact(parent/'runtime.json'),build_ref=fact(build/'build.json'),originals=fixtures,producer=fact(Path(__file__)),projection=projection(parent,out,old,v,reader,b,fixtures))
        v['passed']=True
    finally:save(out/'runtime.json',v);(out/'repair-producer.py').write_bytes(Path(__file__).read_bytes())
    admit(out);print('CPU-repair candidate ready; recovery and regressions unverified',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('parent','build','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args()
    with open('/private/tmp/pear-native-compilation.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);prepare(a.parent.resolve(),a.build.resolve(),a.output)
