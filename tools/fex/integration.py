#!/usr/bin/env python3
"""Build changed Wine integration units from pinned inputs; never run a guest.

Reuse the existing exact patch reader and recorded Wine compiler commands.
This is an incremental compile check, not a fresh runtime reconstruction.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys

if not __package__:
    script_directory=Path(__file__).resolve().parent
    sys.path[:]=[entry for entry in sys.path if Path(entry or os.getcwd()).resolve()!=script_directory]
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.fex.build import apply_hunks, patch_sections
from tools.fex.common import REPO, need, relative

H = lambda raw: hashlib.sha256(raw).hexdigest()
PATCHES = REPO/'runtime/fex/patches/integration'


def derive(wine_build):
    wine_build=Path(wine_build).resolve(strict=True)
    manifest=json.loads((PATCHES/'series.json').read_text())
    need(H((wine_build/'build.json').read_bytes())==manifest['base_wine_build_sha256'],
         'integration_base_changed')
    changed={}
    for patch in manifest['patches']:
        relative(patch['file'])
        raw=(PATCHES/patch['file']).read_bytes()
        need(H(raw)==patch['sha256'],'integration_patch_changed')
        sections=patch_sections(raw)
        need(set(sections)=={r['path'] for r in patch['sources']},'integration_patch_closure')
        for row in patch['sources']:
            relative(row['path'])
            before=changed[row['path']] if row['path'] in changed else (wine_build/'source'/row['path']).read_bytes()
            need(H(before)==row['preimage_sha256'],'integration_source_changed')
            after=apply_hunks(before,sections[row['path']],row['path'])
            need(H(after)==row['postimage_sha256'] and len(after)==row['postimage_bytes'],
                 'integration_derived_source_changed')
            changed[row['path']]=after
    return changed


def compile_units(wine_build, output):
    wine_build=Path(wine_build).resolve(strict=True)
    output=Path(output).absolute()
    need(output.is_relative_to(REPO/'.build/task5') and not output.exists(), 'integration_fresh_output')
    need(output.parent.resolve(strict=True)==output.parent,'integration_output_alias')
    changed=derive(wine_build)
    output.mkdir(mode=0o700)
    value={'scope':'fex_component','kind':'changed_wine_integration_units',
           'passed':False,'wine_execution':False,'guest_execution':False,'commands':[],
           'patch_series_sha256':H((PATCHES/'series.json').read_bytes()),
           'base_build_sha256':H((wine_build/'build.json').read_bytes())}
    for rel,raw in changed.items():
        p=output/'source'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    lines=(wine_build/'logs/ntdll/stdout.bin').read_text().replace('\\\n','').splitlines()
    try:
        for rel in sorted(changed):
            if not rel.endswith('.c'):continue
            source='../source/'+rel
            commands=[shlex.split(line) for line in lines if ' -c ' in line and source in line]
            commands=[args for args in commands if source in args]
            need(len(commands)==1,'integration_compile_recipe')
            args=commands[0]
            if not Path(args[0]).is_file():
                inspection=json.loads((REPO/'.build/task5/stage3-fex-modules14/logs/arm64ec.inspect/command.json').read_text())
                args[0]=str(Path(inspection['argv'][2]).with_name('clang'))
            need(Path(args[0]).is_absolute() and Path(args[0]).is_file(),'integration_compiler_missing')
            if '/unix/' not in rel:
                args[args.index('-target')+1]='arm64ec-windows'
                args.insert(1,'-I'+str(output/'source/dlls/ntdll'))
                args.insert(1,'-I'+str(wine_build/'source/dlls/ntdll'))
            target=output/(Path(rel).stem+'.o')
            args[args.index('-o')+1]=str(target)
            args[args.index(source)]=str(output/'source'/rel)
            # Other Wine internal headers remain the pinned source/objects.
            args.insert(1,'-I'+str(wine_build/'source/dlls/ntdll/unix'))
            args.insert(1,'-I'+str(output/'source/dlls/ntdll'))
            args=['/usr/bin/arch','-arm64']+args
            env={**os.environ,'LC_ALL':'C','MACOSX_DEPLOYMENT_TARGET':'26.5'}
            result=subprocess.run(args,cwd=wine_build/'objects',env=env,capture_output=True,timeout=90)
            need(len(result.stdout)+len(result.stderr)<=2*1024**2,'integration_compile_output_limit')
            (output/(Path(rel).stem+'.stdout')).write_bytes(result.stdout)
            (output/(Path(rel).stem+'.stderr')).write_bytes(result.stderr)
            row={'source':rel,'source_sha256':H(changed[rel]),'argv':args,'exit_code':result.returncode,
                 'compiler_sha256':H(Path(args[2]).read_bytes()),'stderr_sha256':H(result.stderr)}
            if target.exists():row['object_sha256']=H(target.read_bytes())
            value['commands'].append(row)
            need(result.returncode==0,'integration_compile_failed')
        # No input changes are tolerated between compilation and the receipt.
        need(derive(wine_build)==changed,'integration_inputs_changed_during_compile')
        value['passed']=True
    except BaseException as error:
        value['error']=getattr(error,'code',type(error).__name__)
        raise
    finally:
        (output/'control.json').write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({'passed':True,'compiled_units':len(value['commands']),'guest_execution':False}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wine-build',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    compile_units(args.wine_build,args.output)
