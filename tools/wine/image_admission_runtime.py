# SPDX-License-Identifier: MIT
"""Sign one diagnostic ntdll overlay without changing the retained #8 candidate."""
from pathlib import Path
import argparse, copy, fcntl, plistlib, shutil, subprocess
from tools.wine.image_admission_inputs import REPO,admit as admit_inputs,baseline,fresh,checked,fact,read,save,need,digest
from tools.wine.image_admission_build import admit as admit_build
from tools.fex import memory_wine_runtime as signing,byte_readers
TARGET=signing.PAYLOAD+'/lib/wine/aarch64-unix/ntdll.so'

def projection(parent,root,old,new,reader,build):
    before={r['path']:r for r in old['bundle_inventory']};after={r['path']:r for r in reader.inventory(root/signing.BUNDLE)}
    need(set(before)==set(after),'image_overlay_paths');native={r['path'][len(signing.BUNDLE)+1:] for r in old['native_images']}
    changed=[]
    for p,row in before.items():
        if row==after[p]:continue
        need(row['kind']==after[p]['kind']=='file','image_overlay_type')
        if p in native:
            origin=Path(build['artifact']['path']) if signing.BUNDLE+'/'+p==TARGET else parent/signing.BUNDLE/p
            reader.verify_code_origin(origin,root/signing.BUNDLE/p)
        else:need(p=='Contents/_CodeSignature/CodeResources','image_unexpected_change')
        changed.append(p)
    need([r['path'] for r in new['native_images']]==[r['path'] for r in old['native_images']],'image_native_set')
    need(TARGET[len(signing.BUNDLE)+1:] in changed,'image_diagnostic_missing')
    return dict(changed_files=changed,code_change='ntdll.so admission diagnostics only',game_qualified=False)

def admit(root):
    root=Path(root);v=read(root/'runtime.json');o=v['image_admission_overlay']
    need(v['passed'] and v['diagnostic_only'] and o['producer']==fact(Path(__file__)),'image_runtime_producer')
    for k in ('inputs_ref','build_ref','parent_ref'):checked(o[k])
    inputs=admit_inputs(Path(o['inputs_ref']['path']).parent);b=admit_build(Path(o['build_ref']['path']).parent)
    need(o['parent_ref']==inputs['runtime_ref'] and b['inputs_ref']==o['inputs_ref'],'image_runtime_inputs')
    parent=Path(o['parent_ref']['path']).parent;old=read(parent/'runtime.json')
    helpers,_=signing.signing_helpers(Path(old['graphics_repo']));reader=helpers.legacy(REPO)
    need(v['bundle_inventory']==reader.inventory(root/signing.BUNDLE),'image_payload_changed')
    for key in ('fixtures','entrypoints','managed_surface_overlay','unaligned_repair_overlay','presentation_overlay','rendering_overlay'):
        need(v[key]==old[key],'image_history_changed')
    for row in v['dependency_closure']:
        need(byte_readers.inspect_closure(root/row['path'],root/signing.BUNDLE)==row['images'],'image_closure_changed')
        need(all(x['architectures']==[byte_readers.MACH_ARM64] for x in row['images']),'image_not_arm64')
    need(projection(parent,root,old,v,reader,b)==o['projection'],'image_projection_changed')
    return v

def prepare(inputs,build,output):
    i=admit_inputs(inputs);b=admit_build(build);parent=Path(i['runtime_ref']['path']).parent
    baseline(Path(i['baseline_repo']));old=read(parent/'runtime.json');out=fresh(output)
    need(shutil.disk_usage(REPO).free>=4*1024**3,'image_runtime_storage')
    v=copy.deepcopy(old);v.update(passed=False,diagnostic_only=True,commands=[])
    helpers,_=signing.signing_helpers(Path(old['graphics_repo']));reader=helpers.legacy(REPO)
    try:
        subprocess.run(['/bin/cp','-cRp',str(parent/signing.BUNDLE),str(out/signing.BUNDLE)],check=True,timeout=60)
        shutil.copy2(b['artifact']['path'],out/TARGET)
        auth=read(parent/'authorization.json');commands=[]
        authorization,private,raw=helpers.capture_authorization(auth['original_ref']['path'],out,reader,commands)
        need(raw==(out/signing.BUNDLE/'Contents/embedded.provisionprofile').read_bytes(),'image_profile_changed')
        (out/'authorized-entitlements.plist').write_bytes(plistlib.dumps(authorization['claims']));(out/'authorized-entitlements.plist').chmod(0o600)
        images=copy.deepcopy(old['native_images'])
        for row in images:row['origin']=b['artifact'] if row['path']==TARGET else fact(parent/row['path']);row['signature']=None
        recipe=helpers.signing_recipe(out,images,private['identity']);print('signing diagnostic candidate',flush=True)
        for ident,args in recipe:helpers.native(args,out,ident,v['commands'])
        for row in images:
            reader.verify_code_origin(Path(row['origin']['path']),out/row['path']);row.update(sha256=digest((out/row['path']).read_bytes()),size_bytes=(out/row['path']).stat().st_size)
        logs=helpers.verify_commands(out,v['commands'],recipe)
        v['native_images']=helpers.signatures_from_logs(out,images,logs,authorization['claims'],private,reader,raw)
        v['bundle_inventory']=reader.inventory(out/signing.BUNDLE)
        v['dependency_closure']=[dict(path=r['path'],images=byte_readers.inspect_closure(out/r['path'],out/signing.BUNDLE)) for r in v['native_images']]
        v['authorization_sha256']=digest((out/'authorization.json').read_bytes())
        v['source_ledger']=[dict(runtime_path=signing.BUNDLE+'/'+r['path'],origin=b['artifact'] if signing.BUNDLE+'/'+r['path']==TARGET else fact(parent/signing.BUNDLE/r['path'])) for r in old['bundle_inventory'] if r['kind']=='file']
        v['image_admission_overlay']=dict(inputs_ref=fact(inputs/'inputs.json'),build_ref=fact(build/'build.json'),parent_ref=i['runtime_ref'],producer=fact(Path(__file__)),projection=projection(parent,out,old,v,reader,b))
        v['passed']=True
    finally:save(out/'runtime.json',v);(out/'producer.py').write_bytes(Path(__file__).read_bytes())
    admit(out);print('diagnostic candidate signed; execution unperformed',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('inputs','build','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args()
    with open('/private/tmp/pear-native-compilation.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);prepare(a.inputs.resolve(),a.build.resolve(),a.output)
