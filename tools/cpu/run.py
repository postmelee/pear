#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Run one bounded CPU corpus sequentially; remove only completed owned prefixes."""
from pathlib import Path
import argparse
import fcntl
import json
import shutil
import sys

if not __package__:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.cpu.corpus import REPO
from tools.cpu.results import read,decode,digest,require,admit_build,case_result,boundary_result
from tools.cpu.pear_run import run
from tools.cpu.compare import observe_pear


def execute(runtime, build_root, reuse, output, name):
    require(output.parent==REPO/'.build/task6' and not output.exists(),'fresh_index')
    require(name.isalnum(),'run_name')
    manifest_path=REPO/'tests/cpu/corpus.json';manifest=read(manifest_path)
    built=read(build_root/'build.json');build_raw=(build_root/'build.json').read_bytes()
    admit_build(manifest,manifest_path.read_bytes(),built,build_root)
    value=read(runtime/'runtime.json')
    require(value['cpu_build_sha256']==digest(build_raw),'runtime_build')
    result=dict(complete=False,build_sha256=digest(build_raw),runtime=str(runtime),signing_source=str(reuse),cases=[])
    try:
        for fixture in built['cases']:
            folder=REPO/'.build/task6'/('cpu-'+name+'-'+fixture['id'])
            if not folder.exists():
                run(runtime,folder,reuse,fixture['id'])
            # Resume only an unchanged, fully observed success/feature refusal.
            # Faults, partial directories and missing records are never skipped.
            observed,_=observe_pear(folder,runtime,value,fixture)
            asm=next((c for c in manifest['cases'] if c['id']==fixture['id']),None)
            if asm: case_result(asm,observed,built['manifest_sha256'])
            else: boundary_result(next(c for c in manifest['boundaries'] if c['id']==fixture['id']),observed)
            # The unchanged supervisor has already reaped owned processes and
            # proved sentinel survival. Preserve observations, remove only this
            # completed synthetic prefix; no credentials or game data exist.
            require(read(folder/'case.json',limit=64*1024*1024)['cleanup']['complete'],'cleanup_incomplete')
            prefix=folder/'run/prefix'
            if prefix.exists():
                require(prefix.is_dir() and not prefix.is_symlink(),'prefix_scope')
                shutil.rmtree(prefix)
            else:
                require(read(folder/'prefix-retention.json')['removed'] is True,'missing_prefix_retention')
            (folder/'prefix-retention.json').write_text(json.dumps(dict(removed=True,reason='completed_owned_synthetic_prefix',case_sha256=digest((folder/'case.json').read_bytes())))+'\n')
            result['cases'].append(dict(id=fixture['id'],path=str(folder)))
    finally:
        result['complete']=len(result['cases'])==len(built['cases'])
        output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('runtime','build','reuse','output'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--name',required=True);a=p.parse_args()
    with open('/private/tmp/pear-native-compilation.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        execute(a.runtime.resolve(),a.build.resolve(),a.reuse.resolve(),a.output.absolute(),a.name)
