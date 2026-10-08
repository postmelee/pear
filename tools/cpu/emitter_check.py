#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check actual emitter fixups in NX host memory, with a test allocator adapter."""
from pathlib import Path
import argparse,sys
import subprocess,json,hashlib
R=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
S=a.source.resolve();O=a.output.absolute()
series=json.loads((R/'runtime/fex/patches/cpu/series.json').read_text())
for row in series['files']:
    if hashlib.sha256((S/row['path']).read_bytes()).hexdigest()!=row['after']:raise SystemExit('corrected source identity required')
O.mkdir()
shim=O/'shim/FEXCore/Utils';shim.mkdir(parents=True)
(shim/'AllocatorHooks.h').write_text('#pragma once\n#include <cstddef>\nnamespace FEXCore::Allocator { void* aligned_alloc(size_t,size_t); void aligned_free(void*); }\n')
argv=['/usr/bin/arch','-arm64','/usr/bin/clang++','-std=c++20','-O1','-DPEAR_FEX_MEMORY_OWNER=1','-DFMT_HEADER_ONLY=1','-I'+str(O/'shim')]+['-I'+str(S/p) for p in ('CodeEmitter','FEXCore/include','FEXHeaderUtils','External/fmt/include')]+[str(R/'tests/cpu/emitter_labels.cpp'),'-o',str(O/'emitter-control')]
r=subprocess.run(argv,capture_output=True);(O/'compile.log').write_bytes(r.stdout+r.stderr)
record={'compile_argv':argv,'compile_exit':r.returncode,'runs':[],'scope':'native_source_header_control_with_host_allocator_adapter','guest_execution':False}
if r.returncode==0:
 for args,expected in [([],0),(['private-into-direct'],97)]:
  run=subprocess.run(['/usr/bin/arch','-arm64',str(O/'emitter-control')]+args,capture_output=True)
  record['runs'].append({'args':args,'exit_code':run.returncode,'expected_exit':expected,'stdout':run.stdout.decode(),'stderr':run.stderr.decode()})
record['passed']=r.returncode==0 and all(x['exit_code']==x['expected_exit'] for x in record['runs'])
record['inputs']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [R/'tests/cpu/emitter_labels.cpp',S/'CodeEmitter/CodeEmitter/Emitter.h',shim/'AllocatorHooks.h']}
(O/'control.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'passed':record['passed'],'compile_exit':record['compile_exit'],'runs':[{'args':x['args'],'exit_code':x['exit_code']} for x in record['runs']]}));raise SystemExit(0 if record['passed'] else 1)
