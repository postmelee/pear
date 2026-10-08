# SPDX-License-Identifier: MIT
"""Build the translator data-address correction over admitted #6 FEX sources."""
from pathlib import Path
import argparse
import fcntl
import shutil
import subprocess
from tools.dxmt.translated_inputs import REPO,admit,read,save,digest,fact,fresh,check_files
from tools.cpu.fex_build import inventory
from tools.fex import memory_wine_build as monitor
from tools.wine.common import need,encoded
PATCH=REPO/'runtime/fex/patches/graphics/0003-high-private-allocations.patch'

def build(inputs,output):
    inputs=Path(inputs).resolve();v=admit(inputs);base=Path(v['cpu']);prior=read(base/'build.json');output=fresh(output)
    result=dict(kind='translated_graphics_fex_build',passed=False,input_ref=fact(inputs/'inputs.json'),
                base_ref=fact(base/'build.json'),patch_ref=fact(PATCH),series_ref=fact(PATCH.with_suffix('.json')),commands=[])
    def run(ident,argv,env=None,timeout=600):
        print(ident,flush=True)
        monitor.execute(output,ident,argv,str(output),env or {'PATH':'/usr/bin:/bin','LC_ALL':'C'},timeout,result['commands'],8*1024**3,4*1024**3)
    try:
        need(shutil.disk_usage(REPO).free>=8*1024**3,'translated_fex_storage')
        for name in ('source','wire'):
            run('clone-'+name,['/bin/cp','-cRp',str(base/name),str(output/name)])
            need(inventory(base/name)==inventory(output/name),'translated_fex_clone_changed')
        series=read(PATCH.with_suffix('.json'))
        for r in series['files']:need(digest((output/'source'/r['path']).read_bytes())==r['before'],'translated_fex_preimage')
        run('patch-check',['/usr/bin/patch','--dry-run','-d',str(output/'source'),'-p1','-i',str(PATCH)])
        run('patch',['/usr/bin/patch','-d',str(output/'source'),'-p1','-i',str(PATCH)])
        for r in series['files']:need(digest((output/'source'/r['path']).read_bytes())==r['after'],'translated_fex_postimage')
        sources=dict(source=inventory(output/'source'),wire=inventory(output/'wire'));save(output/'source-files.json',sources)
        for ident in ('arm64ec.configure','arm64ec.build','strip'):
            if ident=='strip':shutil.copyfile(output/'pe/arm64ec/Bin/libarm64ecfex.dll',output/'deployment.dll')
            c=next(c for c in prior['commands'] if c['id']==ident)
            argv=[s.replace(str(base),str(output)) for s in c['argv']]
            env={k:s.replace(str(base),str(output)) for k,s in (c['environment'] or {}).items()}
            run(ident,argv,env,1200)
        need(sources==dict(source=inventory(output/'source'),wire=inventory(output/'wire')),'translated_fex_source_changed')
        result.update(passed=True,source_manifest=fact(output/'source-files.json'),artifact=fact(output/'deployment.dll'),producer=fact(Path(__file__)))
    finally:save(output/'build.json',result);(output/'producer.py').write_bytes(Path(__file__).read_bytes())
    print('FEX data-address correction built',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('inputs','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args()
    with open('/private/tmp/pear-native-compilation.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);build(a.inputs,a.output)

def admit_build(root):
    v=read(root/'build.json')
    need(v['kind']=='translated_graphics_fex_build' and v['passed'] is True,'translated_fex_incomplete')
    for name in ('input_ref','base_ref','patch_ref','series_ref','source_manifest','artifact'):
        need(fact(v[name]['path'])==v[name],'translated_fex_binding_changed')
    need(digest((root/'producer.py').read_bytes())==v['producer']['sha256'],'translated_fex_build_producer')
    need(v['patch_ref']['path']==str(PATCH),'translated_fex_patch_selection')
    need([c['id'] for c in v['commands']]==['clone-source','clone-wire','patch-check','patch','arm64ec.configure','arm64ec.build','strip'],'translated_fex_commands')
    for c in v['commands']:
        need(c['status']=='completed' and c['exit_code']==0 and c['error_code'] is None,'translated_fex_command_failed')
        check_files(root,list(c['logs'].values()))
    need(read(root/'source-files.json')==dict(source=inventory(root/'source'),wire=inventory(root/'wire')),'translated_fex_source_changed')
    return v
