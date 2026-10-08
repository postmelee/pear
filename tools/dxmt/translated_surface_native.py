# SPDX-License-Identifier: MIT
"""Rebuild the approved managed surface bridge and source-matched DXMT consumer."""
from pathlib import Path
import argparse,fcntl,os,re,shlex,shutil,subprocess
from tools.dxmt.translated_inputs import REPO,read,save,fact,fresh,need,check_files
from tools.dxmt.translated_present_native import admit as admit_parent
from tools.dxmt.translated_runtime import admit_build
PATCHES=['0005-managed-window-surface.patch','0006-managed-window-consumer.patch','0007-managed-surface-controls.patch','0008-surface-consumer-controls.patch']

def admit(root):
    v=read(root/'build.json');need(v['passed'] and v['kind']=='translated_surface_native_build','surface_native_incomplete')
    need(v['producer']==fact(Path(__file__)),'surface_native_producer')
    for r in v['references']+v['dependencies']+list(v['artifacts'].values()):need(fact(r['path'])==r,'surface_native_changed')
    admit_parent(Path(v['references'][0]['path']).parent)
    for c in v['commands']:need(c['exit_code']==0,'surface_native_command');check_files(root,c['logs'])
    need([c['id'] for c in v['commands']]==['metal-compile','metal-link','bridge-compile','window-compile','pairing-compile','win32u-compile','win32u-link','driver-link'],'surface_native_recipe')
    return v

def build(parent,wine,output):
    pv=admit_parent(parent);_,inputs=admit_build(wine);out=fresh(output)
    need(shutil.disk_usage(REPO).free>=4*1024**3,'surface_native_storage')
    obj=Path(inputs['graphics'])/'dxmt/objects';old=wine/'objects'
    refs=[fact(parent/'build.json'),fact(wine/'build.json')]+[fact(REPO/'runtime/dxmt/patches'/p) for p in PATCHES]
    v=dict(kind='translated_surface_native_build',passed=False,producer=fact(Path(__file__)),references=refs,dependencies=[],commands=[],artifacts={})
    deps={r['path']:r for r in pv['dependencies']}
    def dep(p):
        p=p.resolve();deps[str(p)]=fact(p)
    environment=read(wine/'logs/driver/command.json')['environment'];dep(wine/'logs/driver/command.json')
    def command(name,args,cwd):
        print(name,flush=True);env=dict(os.environ)
        if not name.startswith('metal-'):env.update({k:environment[k] for k in ('SDKROOT','MACOSX_DEPLOYMENT_TARGET','LC_ALL')})
        r=subprocess.run(args,cwd=cwd,env=env,capture_output=True,timeout=120);logs=[]
        for key in ('stdout','stderr'):
            p=out/(name+'.'+key);p.write_bytes(getattr(r,key));f=fact(p);f['path']=p.name;logs.append(f)
        v['commands'].append(dict(id=name,argv=args,cwd=str(cwd),exit_code=r.returncode,logs=logs,platform_environment={k:env.get(k) for k in ('SDKROOT','MACOSX_DEPLOYMENT_TARGET','LC_ALL')}))
        need(r.returncode==0,'surface_native_'+name)
    try:
        subprocess.run(['/bin/cp','-cRp',str(parent/'metal-source'),str(out/'metal-source')],check=True,timeout=60)
        subprocess.run(['/usr/bin/patch','-F','0','-p1','-d',str(out/'metal-source'),'-i',refs[3]['path']],capture_output=True,check=True,timeout=10)
        subprocess.run(['/usr/bin/patch','-F','0','-p1','-d',str(out/'metal-source'),'-i',refs[5]['path']],capture_output=True,check=True,timeout=10)
        args=list(pv['commands'][0]['argv'])
        for flag,path in [('-o',out/'metal.o'),('-MF',out/'metal.d'),('-MQ',out/'metal.o'),('-c',out/'metal-source/src/winemetal/unix/winemetal_unix.c')]:args[args.index(flag)+1]=str(path)
        command('metal-compile',args,obj)
        args=list(pv['commands'][1]['argv']);args[args.index('-o')+1]=str(out/'winemetal.so');args[args.index(str(parent/'winemetal.o'))]=str(out/'metal.o')
        command('metal-link',args,obj);v['artifacts']['winemetal.so']=fact(out/'winemetal.so')
        src=out/'driver-source/dlls/winemac.drv';src.parent.mkdir(parents=True)
        subprocess.run(['/bin/cp','-cRp',str(wine/'source/dlls/winemac.drv'),str(src)],check=True,timeout=60)
        (out/'driver-source/dlls/win32u').mkdir()
        shutil.copy2(wine/'source/dlls/win32u/window.c',out/'driver-source/dlls/win32u/window.c')
        shutil.copy2(parent/'driver-source/dlls/winemac.drv/pear_metal_bridge.m',src/'pear_metal_bridge.m')
        subprocess.run(['/usr/bin/patch','-F','0','-p1','-d',str(out/'driver-source'),'-i',refs[2]['path']],capture_output=True,check=True,timeout=10)
        subprocess.run(['/usr/bin/patch','-F','0','-p1','-d',str(out/'driver-source'),'-i',refs[4]['path']],capture_output=True,check=True,timeout=10)
        text=(old/'Makefile').read_text().replace('\\\n','');dep(old/'Makefile')
        variables={k:val for k,val in re.findall(r'^(CC|CFLAGS|LDFLAGS)[ \t]*=[ \t]*(.*)$',text,re.M)}
        def recipe(target):
            m=re.search(r'^'+re.escape(target)+r':[^\n]*\n\t([^\n]+)',text,re.M);need(m is not None,'surface_wine_recipe')
            line=m[1].replace('$@',target)
            for k,val in variables.items():line=line.replace('$('+k+')',val)
            need('$(' not in line,'surface_wine_recipe_variable');return shlex.split(line)
        for name,file in [('bridge','pear_metal_bridge.m'),('window','window.c'),('pairing','pear_metal_pairing.m')]:
            args=recipe('dlls/winemac.drv/'+file.rsplit('.',1)[0]+'.o');args[args.index('-o')+1]=str(out/(name+'.o'))
            args[args.index('../source/dlls/winemac.drv/'+file)]=str(src/file)
            args+=['-MMD','-MF',str(out/(name+'.d'))];dep(Path(args[0]));command(name+'-compile',args,old)
        args=recipe('dlls/win32u/window.o');args[args.index('-o')+1]=str(out/'win32u-window.o')
        args[args.index('../source/dlls/win32u/window.c')]=str(out/'driver-source/dlls/win32u/window.c')
        args+=['-MMD','-MF',str(out/'win32u.d')];command('win32u-compile',args,old)
        args=recipe('dlls/win32u/win32u.so');args[args.index('-o')+1]=str(out/'win32u.so')
        args[args.index('dlls/win32u/window.o')]=str(out/'win32u-window.o')
        for token in args:
            if not token.startswith('-') and (old/token).is_file():dep(old/token)
        command('win32u-link',args,old);v['artifacts']['win32u.so']=fact(out/'win32u.so')
        args=recipe('dlls/winemac.drv/winemac.so');args[args.index('-o')+1]=str(out/'winemac.so')
        for name,file in [('bridge','pear_metal_bridge'),('window','window'),('pairing','pear_metal_pairing')]:args[args.index('dlls/winemac.drv/'+file+'.o')]=str(out/(name+'.o'))
        for token in args:
            if not token.startswith('-') and (old/token).is_file():dep(old/token)
        args[args.index('dlls/win32u/win32u.so')]=str(out/'win32u.so')
        command('driver-link',args,old);v['artifacts']['winemac.so']=fact(out/'winemac.so')
        for name,cwd in [('metal',obj),('bridge',old),('window',old),('pairing',old),('win32u',old)]:
            for token in shlex.split((out/(name+'.d')).read_text().replace('\\\n','').split(': ',1)[1]):dep(cwd/token)
        v.update(passed=True,dependencies=list(deps.values()))
    finally:save(out/'build.json',v);(out/'producer.py').write_bytes(Path(__file__).read_bytes())
    admit(out);print('managed surface native build complete',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('parent','wine','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args()
    with open('/private/tmp/pear-native-compilation.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);build(a.parent.resolve(),a.wine.resolve(),a.output)
