# SPDX-License-Identifier: MIT
"""Construct only the combined Wine graphics driver and a bounded x64 fixture."""
from pathlib import Path
import argparse
import fcntl
import json
import re
import shutil
import subprocess
import tempfile
from tools.dxmt.translated_inputs import REPO,admit,read,save,digest,fact,fresh,check_files
from tools.wine.common import need,relative,read_relative
from tools.fex import memory_wine_build as monitor,memory_wine_runtime as signing

TARGETS=['dlls/winemac.drv/winemac.so','dlls/winemac.drv/aarch64-windows/winemac.drv']
def patches(source):
    series=read(REPO/'runtime/dxmt/patches/series.json');patch=series['patches'][0]
    namespace=dict(need=need,relative=relative,re=re)
    signing.selected((REPO/'tools/dxmt/pairing_source.py').read_bytes(),('patch_sections','apply_hunks'),namespace,'reviewed exact graphics patch reader')
    raw=(REPO/'runtime/dxmt/patches'/patch['path']).read_bytes();need(digest(raw)==patch['sha256'],'translated_patch_changed')
    sections=namespace['patch_sections'](raw)
    need(set(sections)=={r['path'] for r in patch['changes']},'translated_patch_closure')
    result={}
    for row in patch['changes']:
        p=source/row['path'];before=p.read_bytes() if p.exists() else None
        need((digest(before) if before is not None else None)==row['before_sha256'],'translated_patch_preimage')
        after=namespace['apply_hunks'](before,sections[row['path']],row['path'])
        need(digest(after)==row['after_sha256'],'translated_patch_postimage');result[row['path']]=after
    return result

def build(inputs,output):
    v=admit(inputs);output=fresh(output);old=Path(v['wine']);tools=Path(v['tools'])
    result=dict(kind='translated_graphics_build',passed=False,input_ref=fact(inputs/'inputs.json'),commands=[],guest_execution=False)
    def run(name,args,cwd,env,timeout=600):
        print(name,flush=True);monitor.execute(output,name,args,str(cwd),env,timeout,result['commands'],8*1024**3,4*1024**3)
    try:
        need(shutil.disk_usage(REPO).free>=12*1024**3,'translated_build_storage')
        modified=patches(old/'source');manifest=read(old/'source-files.json')
        known={r['path'] for r in manifest['files']}
        for row in manifest['files']:
            if row['path'] in modified:row.update(sha256=digest(modified[row['path']]),size_bytes=len(modified[row['path']]))
        for path,raw in modified.items():
            if path not in known:
                manifest['files'].append(dict(path=path,sha256=digest(raw),size_bytes=len(raw),mode=0o644,kind='data'))
        manifest['files'].sort(key=lambda r:r['path'])
        monitor.copy_inventory(old/'source',output/'source',manifest,modified)
        save(output/'source-files.json',manifest)
        for name in ('objects','tmp','fixtures'):(output/name).mkdir()
        alias=Path(tempfile.mkdtemp(prefix='pear-graphics-',dir='/private/tmp'))
        (alias/'workspace').symlink_to(output,target_is_directory=True);(alias/'tools').symlink_to(tools,target_is_directory=True)
        result['alias']=str(alias);oldcmd=read(old/'logs/configure/command.json')
        oldalias=Path(oldcmd['cwd']).parent.parent if 'cwd' in oldcmd else Path(oldcmd['environment']['PWD']).parent.parent
        # The recorded configure cwd uses <alias>/workspace/objects.
        oldalias=Path(oldcmd['environment']['PWD']).parents[1]
        env={k:val.replace(str(oldalias),str(alias)) for k,val in oldcmd['environment'].items() if k!='PWD'}
        args=[a.replace(str(oldalias),str(alias)) for a in oldcmd['argv']]
        run('configure',args,alias/'workspace/objects',env)
        make='/Applications/Xcode.app/Contents/Developer/usr/bin/make'
        run('driver',['/usr/bin/arch','-arm64',make,'-j2',*TARGETS],alias/'workspace/objects',env,3600)
        clang=tools/'llvm-mingw/bin/x86_64-w64-mingw32-clang++'
        run('fixture',['/usr/bin/arch','-arm64',str(clang),'-O2','-std=c++17','-static','-o',str(output/'fixtures/device.exe'),str(REPO/'tests/dxmt/translated.cpp'),'-ldxguid'],output,env)
        artifacts=[dict(path='objects/'+p,**{k:x for k,x in fact(output/'objects'/p).items() if k!='path'}) for p in TARGETS]
        artifacts.append(dict(path='fixtures/device.exe',**{k:x for k,x in fact(output/'fixtures/device.exe').items() if k!='path'}))
        with monitor.wine_readers() as (_,wb):need(wb.inventory(output/'source')==manifest,'translated_source_after_build')
        result.update(passed=True,artifacts=artifacts,source_sha256=digest((output/'source-files.json').read_bytes()),
                      fixture_source=fact(REPO/'tests/dxmt/translated.cpp'),producer_sha256=digest(Path(__file__).read_bytes()))
    finally:save(output/'build.json',result)
    print(json.dumps(dict(passed=True,artifacts=len(artifacts))),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('inputs','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args()
    with open('/private/tmp/pear-native-compilation.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);build(a.inputs.resolve(),a.output)
