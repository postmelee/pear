#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Execute only the admitted CPU PEs on actual native Windows x64."""
from pathlib import Path
import argparse
import ctypes
import json
import os
import platform
import subprocess
import sys
import time

if not __package__:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.cpu.results import read,decode,digest,require,admit_build,assess_records


def native_host():
    require(sys.platform=='win32','requires_windows_reference')
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.GetCurrentProcess.restype=ctypes.c_void_p
    k.IsWow64Process2.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_ushort),ctypes.POINTER(ctypes.c_ushort)]
    process,native=ctypes.c_ushort(),ctypes.c_ushort()
    require(k.IsWow64Process2(k.GetCurrentProcess(),ctypes.byref(process),ctypes.byref(native)),'architecture_query')
    require(process.value==0 and native.value==0x8664 and ctypes.sizeof(ctypes.c_void_p)==8,'requires_native_x64')
    return dict(native_machine=native.value,process_machine=process.value,pointer_bits=64,
                system=platform.platform(),processor=platform.processor(),python=sys.version,
                image={key:os.environ.get(key) for key in ['ImageOS','ImageVersion','RUNNER_ARCH','GITHUB_SHA','GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT']})


def run(build_root, manifest_path, output):
    host=native_host()
    manifest=read(manifest_path);build_raw=(build_root/'build.json').read_bytes();build=decode(build_raw)
    admit_build(manifest,manifest_path.read_bytes(),build,build_root)
    require(not output.exists(),'output_exists');output.mkdir(parents=True)
    result=dict(scope='cpu_native_results',complete=False,completed_count=0,build_sha256=digest(build_raw),host=host,cases=[],cpu_qualified=False)
    try:
        for row in build['cases']:
            exe=(build_root/row['path']).resolve()
            require(digest(exe.read_bytes())==row['sha256'],'binary_changed_before_run')
            stdout=output/(row['id']+'.stdout');stderr=output/(row['id']+'.stderr')
            outcome='exited';start=time.monotonic()
            with stdout.open('xb') as out,stderr.open('xb') as err:
                child=subprocess.Popen([str(exe)],cwd=output,stdout=out,stderr=err,stdin=subprocess.DEVNULL)
                while child.poll() is None:
                    if time.monotonic()-start>30 or stdout.stat().st_size+stderr.stat().st_size>1024*1024:
                        outcome='timeout_or_output_limit';child.kill();child.wait(timeout=10);break
                    time.sleep(.05)
            raw=stdout.read_bytes()
            events=[];parse_error=False
            try:
                events=[decode(line) for line in raw.splitlines() if line.strip()]
            except (ValueError,UnicodeError): parse_error=True
            result['cases'].append(dict(id=row['id'],binary_sha256=row['sha256'],exit_code=child.returncode,
                outcome='malformed_output' if parse_error else outcome,events=events,
                stdout_sha256=digest(raw),stderr_sha256=digest(stderr.read_bytes()),elapsed_ms=round((time.monotonic()-start)*1000)))
            result['completed_count']+=1
        result['complete']=True
        checked=assess_records(manifest,build_raw,result,'native')
        result['passed']=all(r['status']=='passed' for r in checked.values())
        result['coverage']=checked
    finally:
        (output/'results.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return 0 if result.get('passed') else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('build','manifest','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();sys.exit(run(a.build,a.manifest,a.output))
