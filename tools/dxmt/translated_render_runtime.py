# SPDX-License-Identifier: MIT
"""Add one fixture to the Stage 1 bundle, preserving every runtime code byte."""
from pathlib import Path
import argparse
import copy
import fcntl
import plistlib
import shutil
import subprocess
from tools.dxmt.translated_inputs import REPO,read,save,digest,fact,fresh,need
from tools.dxmt.translated_render_build import admit as admit_fixture
from tools.dxmt.translated_runtime import admit_build
from tools.fex import memory_wine_runtime as signing,byte_readers

FIXTURE=signing.PAYLOAD+'/libexec/pear-graphics/rendering.exe'
BRIDGE=signing.PAYLOAD+'/lib/wine/aarch64-unix/winemetal.so'

def projection(parent,output,old,new,reader,pipeline=None):
    before={r['path']:r for r in old['bundle_inventory']}
    after={r['path']:r for r in reader.inventory(output/signing.BUNDLE)}
    added=FIXTURE[len(signing.BUNDLE)+1:]
    need(set(after)==set(before)|{added},'render_overlay_inventory')
    native={r['path'][len(signing.BUNDLE)+1:] for r in old['native_images']}
    changed=[]
    for path,row in before.items():
        if row==after[path]:continue
        need(row['kind']=='file' and after[path]['kind']=='file','render_overlay_type')
        if path in native:
            origin=Path(pipeline['artifact']['path']) if pipeline and signing.BUNDLE+'/'+path==BRIDGE else parent/signing.BUNDLE/path
            reader.verify_code_origin(origin,output/signing.BUNDLE/path)
        else:need(path=='Contents/_CodeSignature/CodeResources','render_nonfixture_changed')
        changed.append(path)
    need(len(old['native_images'])==len(new['native_images']) and
         [r['path'] for r in old['native_images']]==[r['path'] for r in new['native_images']], 'render_native_set')
    return dict(only_new_payload=added,changed_files=changed,native_code_unchanged=pipeline is None,
                cpu_code_unchanged=True,pipeline_observation_only=pipeline is not None)

def admit(runtime):
    v=read(runtime/'runtime.json');overlay=v['rendering_overlay']
    need(v['passed'] and overlay['producer_sha256']==digest(Path(__file__).read_bytes()),'render_runtime_producer')
    for key in ('parent_ref','build_ref','stage1_ref'):
        need(fact(overlay[key]['path'])==overlay[key],'render_overlay_reference')
    parent=Path(overlay['parent_ref']['path']).parent;old=read(parent/'runtime.json')
    need('rendering_overlay' not in old and old['passed'] and not old.get('diagnostic_only'),'render_parent_scope')
    stage=read(overlay['stage1_ref']['path'])
    need(stage['passed'] and stage['stage']==1 and stage['runtime_ref']==overlay['parent_ref'],'render_stage1_parent')
    build=admit_fixture(Path(overlay['build_ref']['path']).parent)
    need(build['parent_build']==v['build_ref']==old['build_ref'],'render_build_pair')
    helpers,_=signing.signing_helpers(Path(old['graphics_repo']));reader=helpers.legacy(REPO)
    need(reader.inventory(parent/signing.BUNDLE)==old['bundle_inventory'],'render_parent_bytes')
    need(reader.inventory(runtime/signing.BUNDLE)==v['bundle_inventory'],'render_overlay_bytes')
    for row in v['dependency_closure']:
        need(byte_readers.inspect_closure(runtime/row['path'],runtime/signing.BUNDLE)==row['images'],'render_native_closure_changed')
        need(all(i['architectures']==[byte_readers.MACH_ARM64] for i in row['images']),'render_native_architecture')
    need((runtime/FIXTURE).read_bytes()==Path(build['artifact']['path']).read_bytes(),'render_fixture_bytes')
    pipeline=None
    if 'pipeline_build_ref' in overlay:
        ref=overlay['pipeline_build_ref'];need(fact(ref['path'])==ref,'render_pipeline_ref')
        from tools.dxmt.translated_pipeline_build import admit as admit_pipeline
        pipeline=admit_pipeline(Path(ref['path']).parent)
    need(projection(parent,runtime,old,v,reader,pipeline)==overlay['projection'],'render_projection_changed')
    return v

def prepare(parent,build,stage1,output,pipeline_root=None):
    fixture=admit_fixture(build);old=read(parent/'runtime.json')
    need(old['passed'] and not old.get('diagnostic_only') and 'rendering_overlay' not in old,'render_parent_scope')
    need(old['producer_sha256']==digest((REPO/'tools/dxmt/translated_runtime.py').read_bytes()),'render_parent_producer')
    need(fixture['parent_build']==old['build_ref'],'render_parent_build')
    admit_build(Path(old['build_ref']['path']).parent)
    stage=read(stage1);need(stage['passed'] and stage['stage']==1 and stage['runtime_ref']==fact(parent/'runtime.json'),'render_stage1_pair')
    helpers,_=signing.signing_helpers(Path(old['graphics_repo']));reader=helpers.legacy(REPO)
    need(reader.inventory(parent/signing.BUNDLE)==old['bundle_inventory'],'render_parent_changed')
    need(shutil.disk_usage(REPO).free>=4*1024**3,'render_runtime_storage');output=fresh(output)
    v=copy.deepcopy(old);v.update(passed=False,commands=[])
    pipeline=None
    if pipeline_root:
        from tools.dxmt.translated_pipeline_build import admit as admit_pipeline
        pipeline=admit_pipeline(pipeline_root)
    try:
        subprocess.run(['/bin/cp','-cRp',str(parent/signing.BUNDLE),str(output/signing.BUNDLE)],check=True,timeout=60)
        shutil.copy2(fixture['artifact']['path'],output/FIXTURE)
        if pipeline:shutil.copy2(pipeline['artifact']['path'],output/BRIDGE)
        auth=read(parent/'authorization.json');auth_commands=[]
        authorization,private,raw=helpers.capture_authorization(auth['original_ref']['path'],output,reader,auth_commands)
        need(raw==(output/signing.BUNDLE/'Contents/embedded.provisionprofile').read_bytes(),'render_profile_changed')
        (output/'authorized-entitlements.plist').write_bytes(plistlib.dumps(authorization['claims']))
        (output/'authorized-entitlements.plist').chmod(0o600)
        images=copy.deepcopy(old['native_images'])
        for row in images:
            origin=Path(pipeline['artifact']['path']) if pipeline and row['path']==BRIDGE else parent/row['path']
            row['origin']=fact(origin);row['signature']=None
        recipe=helpers.signing_recipe(output,images,private['identity'])
        print('signing fixture-only overlay',flush=True)
        for ident,args in recipe:helpers.native(args,output,ident,v['commands'])
        for row in images:
            reader.verify_code_origin(Path(row['origin']['path']),output/row['path'])
            row.update(sha256=digest((output/row['path']).read_bytes()),size_bytes=(output/row['path']).stat().st_size)
        logs=helpers.verify_commands(output,v['commands'],recipe)
        v['native_images']=helpers.signatures_from_logs(output,images,logs,authorization['claims'],private,reader,raw)
        v['bundle_inventory']=reader.inventory(output/signing.BUNDLE)
        v['dependency_closure']=[dict(path=r['path'],images=byte_readers.inspect_closure(output/r['path'],output/signing.BUNDLE)) for r in v['native_images']]
        v['fixtures']['rendering']=dict(path=FIXTURE,sha256=fixture['artifact']['sha256'])
        v['authorization_sha256']=digest((output/'authorization.json').read_bytes())
        v['source_ledger']=[dict(runtime_path=signing.BUNDLE+'/'+r['path'],origin=fact(parent/signing.BUNDLE/r['path']))
                            for r in old['bundle_inventory'] if r['kind']=='file']
        if pipeline:
            for row in v['source_ledger']:
                if row['runtime_path']==BRIDGE:row['origin']=pipeline['artifact']
        v['source_ledger'].append(dict(runtime_path=FIXTURE,origin=fixture['artifact']))
        v['rendering_overlay']=dict(parent_ref=fact(parent/'runtime.json'),build_ref=fact(build/'build.json'),
            stage1_ref=fact(stage1),producer_sha256=digest(Path(__file__).read_bytes()),
            projection=projection(parent,output,old,v,reader,pipeline))
        if pipeline:v['rendering_overlay']['pipeline_build_ref']=fact(pipeline_root/'build.json')
        v['passed']=True
    finally:save(output/'runtime.json',v);(output/'render-producer.py').write_bytes(Path(__file__).read_bytes())
    admit(output);print('signed rendering candidate; CPU core unchanged',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('parent','build','stage1','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--pipeline-build',type=Path)
    a=p.parse_args()
    with open('/private/tmp/pear-native-compilation.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);prepare(a.parent.resolve(),a.build.resolve(),a.stage1.resolve(),a.output,a.pipeline_build.resolve() if a.pipeline_build else None)
