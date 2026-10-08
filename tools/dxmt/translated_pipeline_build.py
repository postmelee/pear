# SPDX-License-Identifier: MIT
"""Compile only native winemetal pipeline-state observation; reuse pinned archives."""
from pathlib import Path
import argparse,json,shlex,shutil,subprocess
from tools.dxmt.translated_inputs import REPO,read,save,fact,fresh,digest,need,check_files
from tools.dxmt.translated_runtime import admit_build
PATCH=REPO/'runtime/dxmt/patches/0002-pipeline-validation-observation.patch'
SOURCE='src/winemetal/unix/winemetal_unix.c'

def admit(root):
    v=read(root/'build.json');need(v['kind']=='translated_pipeline_observation_build' and v['passed'],'pipeline_build_incomplete')
    for row in [v['base_ref'],v['patch_ref'],v['source_ref'],v['artifact'],v['producer']]+v['dependencies']:
        need(fact(row['path'])==row,'pipeline_build_changed')
    need(v['patch_ref']['path']==str(PATCH),'pipeline_patch_selection')
    for c in v['commands']:
        need(c['exit_code']==0,'pipeline_build_command');check_files(root,c['logs'])
    need([c['id'] for c in v['commands']]==['compile','link'],'pipeline_recipe')
    return v

def build(parent,output):
    _,inputs=admit_build(parent);base=Path(inputs['graphics']);objects=base/'dxmt/objects';source=base/'dxmt/source'
    receipt=read(base/'build.json');check_files(source,receipt['source']['dxmt']['after_files'])
    output=fresh(output);need(shutil.disk_usage(REPO).free>=4*1024**3,'pipeline_storage')
    subprocess.run(['/bin/cp','-cRp',str(source),str(output/'source')],check=True,timeout=60)
    subprocess.run(['/usr/bin/patch','-F','0','-d',str(output/'source'),'-p1','-i',str(PATCH)],check=True,capture_output=True,timeout=10)
    value=dict(kind='translated_pipeline_observation_build',passed=False,base_ref=fact(base/'build.json'),
               patch_ref=fact(PATCH),source_ref=fact(output/'source'/SOURCE),commands=[],dependencies=[],producer=fact(Path(__file__)))
    dependencies={}
    def dep(p):
        p=p.resolve();dependencies[str(p)]=fact(p)
    commands=json.loads((objects/'compile_commands.json').read_text());c=next(c for c in commands if c['file'].endswith('winemetal_unix.c'))
    args=shlex.split(c['command'])
    for flag,path in [('-o',output/'winemetal_unix.o'),('-MF',output/'compile.d'),('-MQ',output/'winemetal_unix.o'),('-c',output/'source'/SOURCE)]:args[args.index(flag)+1]=str(path)
    # All generated headers, static archives and tool bytes remain explicit inputs.
    dep(Path(args[2]));dep(objects/'compile_commands.json');dep(objects/'build.ninja')
    ninja=(objects/'build.ninja').read_text();line=next(x for x in ninja.splitlines() if x.startswith('build src/winemetal/unix/winemetal.so:'))
    lines=ninja.splitlines();linkargs=shlex.split(lines[lines.index(line)+1].split(' = ',1)[1].replace('$ ', ' '))
    link=['/usr/bin/arch','-arm64',str(Path(args[2]).with_name('clang++')),'-o',str(output/'winemetal.so'),str(output/'winemetal_unix.o'),'src/winemetal/unix/winemetal.so.p/cache.c.o',*linkargs]
    dep(Path(link[2]));dep(objects/'src/winemetal/unix/winemetal.so.p/cache.c.o')
    for a in linkargs:
        p=Path(a)
        if not a.startswith('-') and (objects/p).is_file():dep(objects/p)
    llvm=Path(inputs['graphics_repo'])/'.build/task7/stage2-llvm5/install/lib'
    for a in linkargs:
        if a.startswith('-lLLVM'):dep(llvm/('lib'+a[2:]+'.a'))
    try:
        for ident,argv in [('compile',args),('link',link)]:
            print(ident,flush=True);p=subprocess.run(argv,cwd=objects,capture_output=True,timeout=120)
            logs=[]
            for k in ('stdout','stderr'):
                path=output/(ident+'.'+k);path.write_bytes(getattr(p,k));f=fact(path);logs.append({**f,'path':path.name})
            value['commands'].append(dict(id=ident,argv=argv,cwd=str(objects),exit_code=p.returncode,logs=logs))
            need(p.returncode==0,'pipeline_'+ident+'_failed')
        # Clang emits escaped make paths. Parse only its declared input list.
        deps=(output/'compile.d').read_text().replace('\\\n','')
        for token in shlex.split(deps.split(': ',1)[1]):dep(objects/token)
        value.update(passed=True,dependencies=list(dependencies.values()),artifact=fact(output/'winemetal.so'))
    finally:save(output/'build.json',value);(output/'producer.py').write_bytes(Path(__file__).read_bytes())
    admit(output);print('native pipeline observation built',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('parent','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();build(a.parent.resolve(),a.output)
