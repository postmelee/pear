# SPDX-License-Identifier: MIT
"""Build only the original x64 presentation fixture against admitted Stage 1 tools."""
from pathlib import Path
import argparse
import os
import subprocess
from tools.dxmt.translated_inputs import REPO,read,save,digest,fact,fresh,need
from tools.dxmt.translated_runtime import admit_build

SOURCES=['tests/dxmt/translated_presentation_frames.cpp']
def admit(root):
    v=read(root/'build.json')
    need(v['kind']=='translated_presentation_frames_build' and v['passed'] is True,'present_build_incomplete')
    need(v['producer_sha256']==digest(Path(__file__).read_bytes()),'present_build_producer')
    for r in v['sources']+[v['artifact'],v['compiler']]+v['logs']:
        need(fact(r['path'])==r,'present_build_input_changed')
    need(v['exit_code']==0,'present_build_failed')
    need(fact(v['parent_build']['path'])==v['parent_build'],'present_parent_build_changed')
    admit_build(Path(v['parent_build']['path']).parent)
    return v

def build(parent,output):
    _,inputs=admit_build(parent);output=fresh(output)
    compiler=Path(inputs['tools'])/'llvm-mingw/bin/x86_64-w64-mingw32-clang++'
    args=['/usr/bin/arch','-arm64',str(compiler),'-O2','-std=c++17','-static','-I',str(output),
          str(REPO/SOURCES[0]),'-o',str(output/'presentation-frames.exe'),'-ldxguid','-luser32']
    value=dict(kind='translated_presentation_frames_build',passed=False,parent_build=fact(parent/'build.json'),
               sources=[fact(REPO/s) for s in SOURCES],compiler=fact(compiler.resolve()),argv=args,
               producer_sha256=digest(Path(__file__).read_bytes()))
    result=subprocess.run(args,cwd=output,env={**os.environ,'LC_ALL':'C'},capture_output=True,timeout=120)
    for stream in ('stdout','stderr'):(output/(stream+'.log')).write_bytes(getattr(result,stream))
    value.update(exit_code=result.returncode,logs=[fact(output/(s+'.log')) for s in ('stdout','stderr')])
    if result.returncode==0:value.update(passed=True,artifact=fact(output/'presentation-frames.exe'))
    save(output/'build.json',value);(output/'producer.py').write_bytes(Path(__file__).read_bytes())
    print(result.stderr.decode(errors='replace'));need(value['passed'],'present_compile_failed')
    print('x64 presentation fixture built; guest execution unperformed')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('parent','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();build(a.parent.resolve(),a.output)
