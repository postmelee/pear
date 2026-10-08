# SPDX-License-Identifier: MIT
"""Build only the admitted PE owner caller-check correction."""
from pathlib import Path
import argparse,fcntl,tempfile,subprocess,shutil
from tools.dxmt.translated_inputs import REPO,read,save,fact,fresh,digest,check_files
from tools.dxmt.translated_runtime import admit_build
from tools.fex import memory_wine_build as monitor
from tools.wine.common import need
PATCH=REPO/'runtime/wine/patches/0005-fex-caller-without-loader-lock.patch'

def build(base,output):
    bv,inputs=admit_build(base);root=fresh(output)
    r=dict(kind='translated_owner_build',passed=False,base=fact(base/'build.json'),patch=fact(PATCH),
           series=fact(PATCH.with_suffix('.json')),commands=[])
    def run(name,args,cwd,env,timeout=600):
        print(name,flush=True);monitor.execute(root,name,args,str(cwd),env,timeout,r['commands'],8*1024**3,4*1024**3)
    try:
        need(shutil.disk_usage(REPO).free>=8*1024**3,'translated_owner_storage')
        subprocess.run(['/bin/cp','-cRp',str(base/'source'),str(root/'source')],check=True,timeout=60)
        series=read(PATCH.with_suffix('.json'));path=root/'source'/series['path']
        need(digest(path.read_bytes())==series['before'],'translated_owner_preimage')
        env0={'PATH':'/usr/bin:/bin','LC_ALL':'C'}
        run('patch',['/usr/bin/patch','-d',str(root/'source'),'-p1','-i',str(PATCH)],root,env0)
        need(digest(path.read_bytes())==series['after'],'translated_owner_postimage')
        manifest=read(base/'source-files.json')
        for row in manifest['files']:
            if row['path']==series['path']:row.update(sha256=digest(path.read_bytes()),size_bytes=path.stat().st_size)
        with monitor.wine_readers() as (_,wb):need(wb.inventory(root/'source')==manifest,'translated_owner_source')
        save(root/'source-files.json',manifest)
        for name in ('objects','tmp'):(root/name).mkdir()
        alias=Path(tempfile.mkdtemp(prefix='pear-graphics-owner-',dir='/private/tmp'))
        (alias/'workspace').symlink_to(root);(alias/'tools').symlink_to(Path(inputs['tools']))
        c=bv['commands'][0];oldalias=str(Path(c['cwd']).parents[1]);env={k:v.replace(oldalias,str(alias)) for k,v in c['environment'].items() if k!='PWD'}
        run('configure',[a.replace(oldalias,str(alias)) for a in c['argv']],alias/'workspace/objects',env)
        run('ntdll',['/usr/bin/arch','-arm64','/Applications/Xcode.app/Contents/Developer/usr/bin/make','-j2','dlls/ntdll/aarch64-windows/ntdll.dll'],alias/'workspace/objects',env)
        with monitor.wine_readers() as (_,wb):need(wb.inventory(root/'source')==manifest,'translated_owner_source_after')
        r.update(passed=True,artifact=fact(root/'objects/dlls/ntdll/aarch64-windows/ntdll.dll'),alias=str(alias),source_manifest=fact(root/'source-files.json'))
    finally:save(root/'build.json',r);(root/'producer.py').write_bytes(Path(__file__).read_bytes())

def admit(root):
    v=read(root/'build.json');need(v['kind']=='translated_owner_build' and v['passed'] is True,'translated_owner_incomplete')
    for k in ('base','patch','series','artifact','source_manifest'):need(fact(v[k]['path'])==v[k],'translated_owner_changed')
    need(v['patch']['path']==str(PATCH),'translated_owner_patch')
    for c in v['commands']:
        need(c['status']=='completed' and c['exit_code']==0 and c['error_code'] is None,'translated_owner_command')
        check_files(root,list(c['logs'].values()))
    need([c['id'] for c in v['commands']]==['patch','configure','ntdll'],'translated_owner_commands')
    return v

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('build','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args()
    with open('/private/tmp/pear-native-compilation.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);build(a.build.resolve(),a.output)
