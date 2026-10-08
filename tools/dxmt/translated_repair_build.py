# SPDX-License-Identifier: MIT
"""Build the approved delivered scalar-unaligned repair over the final FEX source."""
from pathlib import Path
import argparse,fcntl,shutil
from tools.dxmt.translated_inputs import REPO,read,save,digest,fact,fresh,check_files,need
from tools.dxmt.translated_fex import admit_build as admit_parent
from tools.cpu.fex_build import inventory
from tools.fex import memory_wine_build as monitor
PATCH=REPO/'runtime/fex/patches/graphics/0004-delivered-unaligned-repair.patch'

def build(parent,output):
    prior=admit_parent(parent);out=fresh(output)
    v=dict(kind='translated_unaligned_repair_build',passed=False,parent_ref=fact(parent/'build.json'),patch_ref=fact(PATCH),series_ref=fact(PATCH.with_suffix('.json')),commands=[],producer=fact(Path(__file__)))
    def run(ident,args,env=None,timeout=600):
        print(ident,flush=True);monitor.execute(out,ident,args,str(out),env or {'PATH':'/usr/bin:/bin','LC_ALL':'C'},timeout,v['commands'],8*1024**3,4*1024**3)
    try:
        need(shutil.disk_usage(REPO).free>=8*1024**3,'repair_build_storage')
        for name in ('source','wire'):
            run('clone-'+name,['/bin/cp','-cRp',str(parent/name),str(out/name)])
            need(inventory(parent/name)==inventory(out/name),'repair_clone_changed')
        series=read(PATCH.with_suffix('.json'))
        for r in series['files']:need(digest((out/'source'/r['path']).read_bytes())==r['before'],'repair_preimage')
        run('patch-check',['/usr/bin/patch','-F','0','--dry-run','-d',str(out/'source'),'-p1','-i',str(PATCH)])
        run('patch',['/usr/bin/patch','-F','0','-d',str(out/'source'),'-p1','-i',str(PATCH)])
        for r in series['files']:need(digest((out/'source'/r['path']).read_bytes())==r['after'],'repair_postimage')
        sources=dict(source=inventory(out/'source'),wire=inventory(out/'wire'));save(out/'source-files.json',sources)
        for ident in ('arm64ec.configure','arm64ec.build','strip'):
            if ident=='strip':shutil.copyfile(out/'pe/arm64ec/Bin/libarm64ecfex.dll',out/'deployment.dll')
            c=next(c for c in prior['commands'] if c['id']==ident)
            args=[s.replace(str(parent),str(out)) for s in c['argv']]
            env={k:s.replace(str(parent),str(out)) for k,s in (c['environment'] or {}).items()}
            run(ident,args,env,1200)
        need(sources==dict(source=inventory(out/'source'),wire=inventory(out/'wire')),'repair_source_changed')
        v.update(passed=True,source_manifest=fact(out/'source-files.json'),artifact=fact(out/'deployment.dll'))
    finally:save(out/'build.json',v);(out/'producer.py').write_bytes(Path(__file__).read_bytes())
    admit(out);print('repair built; delivered recovery unverified',flush=True)

def admit(root):
    v=read(root/'build.json');need(v['passed'] and v['kind']=='translated_unaligned_repair_build','repair_build_incomplete')
    for key in ('parent_ref','patch_ref','series_ref','source_manifest','artifact','producer'):need(fact(v[key]['path'])==v[key],'repair_build_changed')
    need(v['producer']==fact(Path(__file__)) and v['patch_ref']==fact(PATCH),'repair_producer')
    for c in v['commands']:
        need(c['status']=='completed' and c['exit_code']==0 and c['error_code'] is None,'repair_command')
        check_files(root,list(c['logs'].values()))
    need(read(root/'source-files.json')==dict(source=inventory(root/'source'),wire=inventory(root/'wire')),'repair_sources')
    return v

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('parent','output'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args()
    with open('/private/tmp/pear-native-compilation.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);build(a.parent.resolve(),a.output)
