# SPDX-License-Identifier: MIT
"""Rebuild only two graphics observation objects using admitted retained recipes."""
from pathlib import Path
import argparse,json,os,re,shlex,shutil,subprocess
from tools.dxmt.translated_inputs import REPO,read,save,fact,fresh,digest,need,check_files
from tools.dxmt.translated_runtime import admit_build
from tools.dxmt.translated_pipeline_build import admit as admit_pipeline
PATCHES=['0003-presentation-observation.patch','0004-presentation-registry-observation.patch']

def admit(root):
    v=read(root/'build.json');need(v['passed'] and v['kind']=='translated_presentation_native_build','present_native_incomplete')
    for r in v['references']+v['dependencies']+list(v['artifacts'].values())+[v['producer']]:need(fact(r['path'])==r,'present_native_changed')
    need(v['producer']==fact(Path(__file__)),'present_native_producer')
    for c in v['commands']:need(c['exit_code']==0,'present_native_command');check_files(root,c['logs'])
    need([c['id'] for c in v['commands']]==['metal-compile','metal-link','driver-compile','driver-link'],'present_native_recipe')
    return v

def build(parent,pipeline,output):
    _,inputs=admit_build(parent);pv=admit_pipeline(pipeline);out=fresh(output)
    need(shutil.disk_usage(REPO).free>=4*1024**3,'present_native_storage')
    base=Path(inputs['graphics']);obj=base/'dxmt/objects';old=parent/'objects'
    references=[fact(parent/'build.json'),fact(pipeline/'build.json')]+[fact(REPO/'runtime/dxmt/patches'/p) for p in PATCHES]
    v=dict(kind='translated_presentation_native_build',passed=False,references=references,producer=fact(Path(__file__)),commands=[],dependencies=[],artifacts={})
    deps={}
    def dep(p):
        p=p.resolve();deps[str(p)]=fact(p)
    wine_environment=read(parent/'logs/driver/command.json')['environment']
    dep(parent/'logs/driver/command.json')
    def command(name,args,cwd):
        print(name,flush=True);environment={**os.environ,**{k:wine_environment[k] for k in ('SDKROOT','MACOSX_DEPLOYMENT_TARGET','LC_ALL')}} if name.startswith('driver-') else dict(os.environ)
        result=subprocess.run(args,cwd=cwd,env=environment,capture_output=True,timeout=120)
        logs=[]
        for key in ('stdout','stderr'):
            p=out/(name+'.'+key);p.write_bytes(getattr(result,key));f=fact(p);f['path']=p.name;logs.append(f)
        v['commands'].append(dict(id=name,argv=args,cwd=str(cwd),platform_environment={k:environment.get(k) for k in ('SDKROOT','MACOSX_DEPLOYMENT_TARGET','LC_ALL')},exit_code=result.returncode,logs=logs))
        need(result.returncode==0,'present_native_'+name)
    try:
        subprocess.run(['/bin/cp','-cRp',str(pipeline/'source'),str(out/'metal-source')],check=True,timeout=60)
        subprocess.run(['/usr/bin/patch','-F','0','-p1','-d',str(out/'metal-source'),'-i',references[2]['path']],check=True,capture_output=True,timeout=10)
        # Preserve all source input bytes used by the previous pipeline build.
        for row in pv['dependencies']:dep(Path(row['path']))
        commands=json.loads((obj/'compile_commands.json').read_text());c=next(c for c in commands if c['file'].endswith('winemetal_unix.c'))
        args=shlex.split(c['command']);compiler=Path(args[2]);dep(compiler)
        for flag,p in [('-o',out/'winemetal.o'),('-MF',out/'metal.d'),('-MQ',out/'winemetal.o'),('-c',out/'metal-source/src/winemetal/unix/winemetal_unix.c')]:args[args.index(flag)+1]=str(p)
        command('metal-compile',args,obj)
        previous=next(c for c in pv['commands'] if c['id']=='link');args=list(previous['argv'])
        args[args.index('-o')+1]=str(out/'winemetal.so');args[args.index(str(pipeline/'winemetal_unix.o'))]=str(out/'winemetal.o')
        command('metal-link',args,obj);v['artifacts']['winemetal.so']=fact(out/'winemetal.so')
        for token in shlex.split((out/'metal.d').read_text().replace('\\\n','').split(': ',1)[1]):dep(obj/token)
        # Read and expand only the existing two Makefile recipes; never run make
        # against or mutate the retained Wine object/source tree.
        text=(old/'Makefile').read_text().replace('\\\n','');dep(old/'Makefile')
        variables={k:val for k,val in re.findall(r'^(CC|CFLAGS|LDFLAGS)[ \t]*=[ \t]*(.*)$',text,re.M)}
        def recipe(target):
            m=re.search(r'^'+re.escape(target)+r':[^\n]*\n\t([^\n]+)',text,re.M);need(m is not None,'present_wine_recipe')
            line=m[1].replace('$@',target)
            for k,val in variables.items():line=line.replace('$('+k+')',val)
            need('$(' not in line,'present_wine_recipe_variable');return shlex.split(line)
        src=out/'driver-source/dlls/winemac.drv/pear_metal_bridge.m';src.parent.mkdir(parents=True)
        original=parent/'source/dlls/winemac.drv/pear_metal_bridge.m';dep(original);src.write_bytes(original.read_bytes())
        subprocess.run(['/usr/bin/patch','-F','0','-p1','-d',str(out/'driver-source'),'-i',references[3]['path']],check=True,capture_output=True,timeout=10)
        args=recipe('dlls/winemac.drv/pear_metal_bridge.o');args[args.index('-o')+1]=str(out/'driver.o')
        args[args.index('../source/dlls/winemac.drv/pear_metal_bridge.m')]=str(src)
        args+=['-MMD','-MF',str(out/'driver.d')];dep(Path(args[0]));command('driver-compile',args,old)
        args=recipe('dlls/winemac.drv/winemac.so');args[args.index('-o')+1]=str(out/'winemac.so')
        args[args.index('dlls/winemac.drv/pear_metal_bridge.o')]=str(out/'driver.o')
        for token in args:
            if not token.startswith('-') and (old/token).is_file():dep(old/token)
        command('driver-link',args,old);v['artifacts']['winemac.so']=fact(out/'winemac.so')
        for token in shlex.split((out/'driver.d').read_text().replace('\\\n','').split(': ',1)[1]):dep(old/token)
        # Include the freshly compiled source/header, not just parent hashes.
        for p in (out/'metal-source/src/winemetal/unix').glob('pear_*'):dep(p)
        dep(out/'metal-source/src/winemetal/unix/winemetal_unix.c');dep(src)
        v.update(passed=True,dependencies=list(deps.values()))
    finally:save(out/'build.json',v);(out/'producer.py').write_bytes(Path(__file__).read_bytes())
    admit(out);print('two native observation objects built',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('parent','pipeline','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();build(a.parent.resolve(),a.pipeline.resolve(),a.output)
