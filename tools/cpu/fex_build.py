#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build the Stage 2 CPU correction over an admitted, immutable #5 source tree."""
from pathlib import Path
import argparse,fcntl,json,os,shutil,subprocess,sys
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.cpu.runtime import admit_pair
from tools.cpu.corpus import REPO,digest
from tools.cpu.results import read
from tools.wine.common import need,encoded
PATCH=Path('runtime/fex/patches/cpu/0001-private-staging-label-references.patch')


def inventory(root):
    rows=[]
    for p in sorted(root.rglob('*')):
        if p.is_symlink():rows.append(dict(path=p.relative_to(root).as_posix(),link=os.readlink(p)))
        elif p.is_file():rows.append(dict(path=p.relative_to(root).as_posix(),sha256=digest(p.read_bytes())))
    return rows


def build(prior,output):
    need(output.parent==REPO/'.build/task6' and not output.exists(),'fresh_cpu_fex_build')
    need(shutil.disk_usage(REPO).free>=4*1024**3,'cpu_fex_storage')
    receipts=admit_pair(prior);base=prior/'.build/task5/stage6-fex1';original=read(base/'build.json')
    output.mkdir(mode=0o700)
    producer=Path(__file__).read_bytes()
    record=dict(kind='cpu_fex_correction_build',passed=False,baseline_receipts=receipts,
        baseline_build_sha256=digest((base/'build.json').read_bytes()),patch_path=str(PATCH),
        patch_sha256=digest((REPO/PATCH).read_bytes()),commands=[],guest_execution=False,
        previous_objects_reused=False,producer_sha256=digest(producer))
    def run(ident,argv,env=None,timeout=600):
        log=output/(ident+'.log')
        with log.open('wb') as stream:
            p=subprocess.run(argv,cwd=output,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=timeout)
        need(log.stat().st_size<=64*1024**2,'cpu_fex_log_bound')
        record['commands'].append(dict(id=ident,argv=argv,environment=env,cwd=str(output),exit_code=p.returncode,log=log.name,log_sha256=digest(log.read_bytes())))
        need(p.returncode==0,'cpu_fex_'+ident+'_failed')
    try:
        for name in ('source','wire'):
            run('clone-'+name,['/bin/cp','-cRp',str(base/name),str(output/name)])
            need(inventory(base/name)==inventory(output/name),'cpu_fex_clone_changed')
        record['baseline_source_inventory_sha256']=digest(encoded(inventory(base/'source')))
        series=read(REPO/PATCH.parent/'series.json')
        need(series['patch']==PATCH.name,'patch_name')
        for row in series['files']:
            need(digest((output/'source'/row['path']).read_bytes())==row['before'],'patch_preimage')
        # git apply from an ignored subdirectory may silently skip every path.
        # Use an explicit non-Git patch root and require all postimage hashes.
        run('patch-check',['/usr/bin/patch','--dry-run','-d',str(output/'source'),'-p1','-i',str(REPO/PATCH)])
        run('patch',['/usr/bin/patch','-d',str(output/'source'),'-p1','-i',str(REPO/PATCH)])
        for row in series['files']:
            need(digest((output/'source'/row['path']).read_bytes())==row['after'],'patch_postimage')
        record['patch_series_sha256']=digest((REPO/PATCH.parent/'series.json').read_bytes())
        sources=dict(source=inventory(output/'source'),wire=inventory(output/'wire'))
        (output/'inputs.json').write_bytes(encoded(sources));record['inputs_sha256']=digest((output/'inputs.json').read_bytes())
        for ident in ('arm64ec.configure','arm64ec.build'):
            row=next(c for c in original['commands'] if c['id']==ident)
            argv=[a.replace(str(base),str(output)) for a in row['argv']]
            env={k:v.replace(str(base),str(output)) for k,v in row['environment'].items()}
            run(ident,argv,env,row['timeout_seconds'])
        binary=output/'pe/arm64ec/Bin/libarm64ecfex.dll';shutil.copyfile(binary,output/'deployment.dll')
        clang=next(c for c in original['commands'] if c['id']=='arm64ec.configure')
        cxx=next(a.split('=',1)[1] for a in clang['argv'] if a.startswith('-DCMAKE_ASM_COMPILER='))
        cxx=str(Path(cxx).parent/'arm64ec-w64-mingw32-clang++')
        strip=Path(cxx).parent/'llvm-strip'
        run('strip',['/usr/bin/arch','-arm64',str(strip),'--strip-debug',str(output/'deployment.dll')])
        need(sources==dict(source=inventory(output/'source'),wire=inventory(output/'wire')),'source_changed_during_build')
        record.update(passed=True,dll_sha256=digest((output/'deployment.dll').read_bytes()),unstripped_sha256=digest(binary.read_bytes()),
                      tools={str(p):digest(p.resolve().read_bytes()) for p in (Path(cxx),strip)})
        print(json.dumps(dict(built=True,dll_sha256=record['dll_sha256'],guest_execution=False)),flush=True)
    finally:
        (output/'build.json').write_bytes(encoded(record));(output/'producer.py').write_bytes(producer)


def admit_correction(root,receipts):
    record=read(root/'build.json')
    need(record['kind']=='cpu_fex_correction_build' and record['passed'] is True and
         record['baseline_receipts']==receipts,'correction_pair')
    need(record['patch_path']==str(PATCH) and record['patch_sha256']==digest((REPO/PATCH).read_bytes()),'correction_patch')
    need(record.get('patch_series_sha256')==digest((REPO/PATCH.parent/'series.json').read_bytes()),'correction_series')
    for row in read(REPO/PATCH.parent/'series.json')['files']:
        need(digest((root/'source'/row['path']).read_bytes())==row['after'],'correction_patch_not_applied')
    need(record['producer_sha256']==digest((root/'producer.py').read_bytes()),'correction_producer_changed')
    need(record['inputs_sha256']==digest((root/'inputs.json').read_bytes()),'correction_inputs_changed')
    need(read(root/'inputs.json',limit=64*1024**2)==dict(source=inventory(root/'source'),wire=inventory(root/'wire')),'correction_source_changed')
    for command in record['commands']:
        need(command['exit_code']==0 and digest((root/command['log']).read_bytes())==command['log_sha256'],'correction_command')
    need([c['id'] for c in record['commands']]==['clone-source','clone-wire','patch-check','patch','arm64ec.configure','arm64ec.build','strip'],'correction_recipe')
    need(digest((root/'deployment.dll').read_bytes())==record['dll_sha256'],'correction_binary_changed')
    return dict(path=str(root),build_sha256=digest((root/'build.json').read_bytes()),dll_sha256=record['dll_sha256'],
                patch_sha256=record['patch_sha256'],source_inputs_sha256=record['inputs_sha256'],
                scope='arm64ec_fex_only',wine_changed=False,wow64_execution=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('prior-repo','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    with open('/private/tmp/pear-native-compilation.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);build(a.prior_repo.resolve(),a.output.absolute())
