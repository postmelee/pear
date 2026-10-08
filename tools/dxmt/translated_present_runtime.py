# SPDX-License-Identifier: MIT
"""Signed Stage 3 overlay; preserve all CPU/PE bytes and original stage receipts."""
from pathlib import Path
import argparse,copy,fcntl,plistlib,shutil,subprocess
from tools.dxmt.translated_inputs import REPO,read,save,fact,fresh,digest,need
from tools.dxmt.translated_render_runtime import admit as admit_parent
from tools.dxmt.translated_present_build import admit as admit_fixture
from tools.dxmt.translated_present_native import admit as admit_native
from tools.fex import memory_wine_runtime as signing,byte_readers
FIXTURE=signing.PAYLOAD+'/libexec/pear-graphics/presentation.exe'
NATIVE={name:signing.PAYLOAD+'/lib/wine/aarch64-unix/'+name for name in ('winemac.so','winemetal.so')}

def projection(parent,output,old,new,reader,native):
    before={r['path']:r for r in old['bundle_inventory']};after={r['path']:r for r in reader.inventory(output/signing.BUNDLE)}
    added=FIXTURE[len(signing.BUNDLE)+1:];need(set(after)==set(before)|{added},'present_overlay_inventory')
    native_paths={r['path'][len(signing.BUNDLE)+1:] for r in old['native_images']};changed=[]
    for path,row in before.items():
        if row==after[path]:continue
        need(row['kind']=='file' and after[path]['kind']=='file','present_overlay_type')
        if path in native_paths:
            key=next((k for k,v in NATIVE.items() if v==signing.BUNDLE+'/'+path),None)
            origin=Path(native['artifacts'][key]['path']) if key else parent/signing.BUNDLE/path
            reader.verify_code_origin(origin,output/signing.BUNDLE/path)
        else:need(path=='Contents/_CodeSignature/CodeResources','present_unexpected_payload_change')
        changed.append(path)
    need([r['path'] for r in old['native_images']]==[r['path'] for r in new['native_images']],'present_native_set')
    return dict(added_fixture=added,changed_files=changed,cpu_code_unchanged=True,graphics_observation_only=True)

def admit(runtime):
    v=read(runtime/'runtime.json');o=v['presentation_overlay']
    need(v['passed'] and o['producer_sha256']==digest(Path(__file__).read_bytes()),'present_runtime_producer')
    for key in ('parent_ref','build_ref','native_ref'):need(fact(o[key]['path'])==o[key],'present_overlay_reference')
    parent=Path(o['parent_ref']['path']).parent;old=admit_parent(parent)
    b=admit_fixture(Path(o['build_ref']['path']).parent);n=admit_native(Path(o['native_ref']['path']).parent)
    need(b['parent_build']==old['build_ref']==v['build_ref'],'present_fixture_parent')
    need(v['rendering_overlay']==old['rendering_overlay'],'present_rendering_history_changed')
    helpers,_=signing.signing_helpers(Path(old['graphics_repo']));reader=helpers.legacy(REPO)
    need(reader.inventory(runtime/signing.BUNDLE)==v['bundle_inventory'],'present_payload_changed')
    need((runtime/FIXTURE).read_bytes()==Path(b['artifact']['path']).read_bytes(),'present_fixture_changed')
    for row in v['dependency_closure']:
        need(byte_readers.inspect_closure(runtime/row['path'],runtime/signing.BUNDLE)==row['images'],'present_closure_changed')
        need(all(i['architectures']==[byte_readers.MACH_ARM64] for i in row['images']),'present_architecture')
    need(projection(parent,runtime,old,v,reader,n)==o['projection'],'present_projection_changed')
    return v

def prepare(parent,build,native,output):
    old=admit_parent(parent);b=admit_fixture(build);n=admit_native(native)
    need(b['parent_build']==old['build_ref'],'present_build_pair');need(shutil.disk_usage(REPO).free>=4*1024**3,'present_storage')
    out=fresh(output);v=copy.deepcopy(old);v.update(passed=False,commands=[])
    helpers,_=signing.signing_helpers(Path(old['graphics_repo']));reader=helpers.legacy(REPO)
    try:
        subprocess.run(['/bin/cp','-cRp',str(parent/signing.BUNDLE),str(out/signing.BUNDLE)],check=True,timeout=60)
        shutil.copy2(b['artifact']['path'],out/FIXTURE)
        for key,path in NATIVE.items():shutil.copy2(n['artifacts'][key]['path'],out/path)
        auth=read(parent/'authorization.json');commands=[]
        authorization,private,raw=helpers.capture_authorization(auth['original_ref']['path'],out,reader,commands)
        need(raw==(out/signing.BUNDLE/'Contents/embedded.provisionprofile').read_bytes(),'present_profile_changed')
        (out/'authorized-entitlements.plist').write_bytes(plistlib.dumps(authorization['claims']));(out/'authorized-entitlements.plist').chmod(0o600)
        images=copy.deepcopy(old['native_images'])
        for row in images:
            key=next((k for k,p in NATIVE.items() if p==row['path']),None)
            row['origin']=n['artifacts'][key] if key else fact(parent/row['path']);row['signature']=None
        recipe=helpers.signing_recipe(out,images,private['identity']);print('signing Stage 3 candidate',flush=True)
        for ident,args in recipe:helpers.native(args,out,ident,v['commands'])
        for row in images:
            reader.verify_code_origin(Path(row['origin']['path']),out/row['path']);row.update(sha256=digest((out/row['path']).read_bytes()),size_bytes=(out/row['path']).stat().st_size)
        logs=helpers.verify_commands(out,v['commands'],recipe)
        v['native_images']=helpers.signatures_from_logs(out,images,logs,authorization['claims'],private,reader,raw)
        v['bundle_inventory']=reader.inventory(out/signing.BUNDLE)
        v['dependency_closure']=[dict(path=r['path'],images=byte_readers.inspect_closure(out/r['path'],out/signing.BUNDLE)) for r in v['native_images']]
        v['fixtures']['presentation']=dict(path=FIXTURE,sha256=b['artifact']['sha256'])
        v['authorization_sha256']=digest((out/'authorization.json').read_bytes())
        v['source_ledger']=[dict(runtime_path=signing.BUNDLE+'/'+r['path'],origin=fact(parent/signing.BUNDLE/r['path'])) for r in old['bundle_inventory'] if r['kind']=='file']
        for row in v['source_ledger']:
            key=next((k for k,p in NATIVE.items() if p==row['runtime_path']),None)
            if key:row['origin']=n['artifacts'][key]
        v['source_ledger'].append(dict(runtime_path=FIXTURE,origin=b['artifact']))
        v['presentation_overlay']=dict(parent_ref=fact(parent/'runtime.json'),build_ref=fact(build/'build.json'),native_ref=fact(native/'build.json'),producer_sha256=digest(Path(__file__).read_bytes()),projection=projection(parent,out,old,v,reader,n))
        v['passed']=True
    finally:save(out/'runtime.json',v);(out/'presentation-producer.py').write_bytes(Path(__file__).read_bytes())
    admit(out);print('Stage 3 signed candidate ready; execution unperformed',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('parent','build','native','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args()
    with open('/private/tmp/pear-native-compilation.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);prepare(a.parent.resolve(),a.build.resolve(),a.native.resolve(),a.output)
