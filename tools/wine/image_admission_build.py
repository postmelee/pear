# SPDX-License-Identifier: MIT
"""Rebuild two native diagnostic objects; retain all other qualified components."""
from pathlib import Path
import argparse, fcntl, os, re, shlex, shutil, subprocess
from tools.wine.image_admission_inputs import REPO,PATCH,fresh,admit as admit_inputs,checked,fact,read,save,need,digest
from tools.fex import memory_wine_runtime as signing

def admit(root):
    root=Path(root);v=read(root/'build.json')
    need(v['passed'] and v['kind']=='image_admission_build' and v['producer']==fact(Path(__file__)),'image_build_incomplete')
    checked(v['inputs_ref']);admit_inputs(Path(v['inputs_ref']['path']).parent)
    for row in v['dependencies']+[v['artifact'],v['control']]:checked(row)
    for row in v['commands']:
        need(row['exit_code']==0,'image_build_command')
        for r in row['logs']:checked(r)
    need([c['id'] for c in v['commands']]==['control-link','arena-compile','virtual-compile','diagnostic-link'],'image_build_recipe')
    return v

def build(inputs,output):
    v=admit_inputs(inputs);out=fresh(output);base=Path(v['native_build_ref']['path']).parent;obj=base/'objects'
    need(shutil.disk_usage(REPO).free>=4*1024**3,'image_build_storage')
    result=dict(kind='image_admission_build',passed=False,diagnostic_only=True,producer=fact(Path(__file__)),
                inputs_ref=fact(inputs/'inputs.json'),commands=[],dependencies=[])
    deps={}
    def dep(path):
        p=Path(path).resolve(strict=True);deps[str(p)]=fact(p)
    text=(obj/'Makefile').read_text().replace('\\\n','');dep(obj/'Makefile')
    variables=dict(re.findall(r'^(CC|CFLAGS|LDFLAGS)[ \t]*=[ \t]*(.*)$',text,re.M))
    def recipe(target):
        m=re.search(r'^'+re.escape(target)+r':[^\n]*\n\t([^\n]+)',text,re.M);need(m,'image_recipe')
        line=m[1].replace('$@',target)
        for k,val in variables.items():line=line.replace('$('+k+')',val)
        need('$(' not in line,'image_recipe_variables');return shlex.split(line)
    record=read(base/'build.json');env=next(c['environment'] for c in record['commands'] if c['id']=='make');dep(base/'build.json')
    def command(name,args):
        for token in args:
            if not token.startswith('-') and (obj/token).is_file():dep(obj/token)
        print(name,flush=True)
        r=subprocess.run(args,cwd=obj,env=env,capture_output=True,timeout=180)
        logs=[]
        for stream in ('stdout','stderr'):
            p=out/(name+'.'+stream);p.write_bytes(getattr(r,stream));logs.append(fact(p))
        result['commands'].append(dict(id=name,argv=args,cwd=str(obj),environment=env,exit_code=r.returncode,logs=logs))
        need(r.returncode==0,'image_'+name+': '+r.stderr.decode(errors='replace')[-1500:])
    try:
        series=read(PATCH.with_suffix('.json'));need(digest(PATCH.read_bytes())==series['patch_sha256'],'image_patch_identity')
        source=out/'source/dlls/ntdll/unix';source.mkdir(parents=True)
        # Local quoted includes are retained and independently recorded.
        for p in (base/'source/dlls/ntdll/unix').glob('*.h'):
            shutil.copy2(p,source/p.name);dep(p)
        for row in series['changes']:
            p=base/'source'/row['path'];need(digest(p.read_bytes())==row['before_sha256'],'image_patch_preimage')
            target=out/'source'/row['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target);dep(p)
        r=subprocess.run(['/usr/bin/patch','--batch','--forward','-F','0','-p1','-d',str(out/'source'),'-i',str(PATCH)],capture_output=True,timeout=15)
        need(r.returncode==0 and b'offset' not in r.stdout and b'fuzz' not in r.stdout,'image_patch_apply')
        dep(PATCH);dep(PATCH.with_suffix('.json'))
        for row in series['changes']:need(digest((out/'source'/row['path']).read_bytes())==row['after_sha256'],'image_patch_postimage')
        args=recipe('dlls/ntdll/ntdll.so');args[args.index('-o')+1]=str(out/'ntdll-control.so');command('control-link',args)
        old=read(Path(v['runtime_ref']['path']));helpers,_=signing.signing_helpers(Path(old['graphics_repo']));reader=helpers.legacy(REPO)
        reader.verify_code_origin(base/'objects/dlls/ntdll/ntdll.so',out/'ntdll-control.so')
        reader.verify_code_origin(out/'ntdll-control.so',Path(v['runtime_ref']['path']).parent/signing.PAYLOAD/'lib/wine/aarch64-unix/ntdll.so')
        result['control']=fact(out/'ntdll-control.so')
        for file,label in [('pear_pe_arena','arena'),('virtual','virtual')]:
            args=recipe('dlls/ntdll/unix/'+file+'.o');args[args.index('-o')+1]=str(out/(file+'.o'))
            args[args.index('../source/dlls/ntdll/unix/'+file+'.c')]=str(source/(file+'.c'))
            args+=['-MMD','-MF',str(out/(file+'.d'))];command(label+'-compile',args)
            for token in shlex.split((out/(file+'.d')).read_text().replace('\\\n','').split(': ',1)[1]):dep(obj/token)
        args=recipe('dlls/ntdll/ntdll.so');args[args.index('-o')+1]=str(out/'ntdll.so')
        for file in ('pear_pe_arena','virtual'):args[args.index('dlls/ntdll/unix/'+file+'.o')]=str(out/(file+'.o'))
        command('diagnostic-link',args);result['artifact']=fact(out/'ntdll.so')
        result['passed']=True
    finally:
        result['dependencies']=list(deps.values());save(out/'build.json',result);(out/'producer.py').write_bytes(Path(__file__).read_bytes())
    admit(out)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('inputs','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--mode',choices=['diagnostic'],required=True);a=p.parse_args()
    with open('/private/tmp/pear-native-compilation.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);build(a.inputs.resolve(),a.output)
