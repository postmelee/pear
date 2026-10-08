# SPDX-License-Identifier: MIT
"""Reuse the original two CPU boundary oracles affected by graphics callbacks."""
from pathlib import Path
from tools.dxmt.translated_inputs import REPO,read,save,fact,need
from tools.dxmt.translated_regression import observe,remove_prefix
from tools.dxmt.translated_run import run
from tools.cpu import results

def boundaries(runtime,cpu,reuse,output,name,seed=None,verify_only=False):
    manifest_path=REPO/'tests/cpu/corpus.json';manifest=results.read(manifest_path)
    build=cpu/'.build/task6/native-build3';reference=cpu/'.build/task6/native-results3'
    built=results.read(build/'build.json');results.admit_build(manifest,manifest_path.read_bytes(),built,build)
    native=results.read(reference/'results.json');expected=results.assess_records(manifest,(build/'build.json').read_bytes(),native,'native')
    for row in native['cases']:
        for stream in ('stdout','stderr'):
            raw=(reference/(row['id']+'.'+stream)).read_bytes();need(results.digest(raw)==row[stream+'_sha256'],'present_cpu_reference_bytes')
        need([results.decode(line) for line in (reference/(row['id']+'.stdout')).read_bytes().splitlines() if line.strip()]==row['events'],'present_cpu_reference_events')
    value=read(runtime/'runtime.json');rows=[]
    for name_id in ('api-callback','abi-state'):
        fixture=next(c for c in built['cases'] if c['id']==name_id);folder=REPO/'.build/task8'/('cpu-'+name+'-'+name_id)
        if not folder.exists():
            need(not verify_only,'present_cpu_missing');run(runtime,folder,reuse,name_id,seed=seed)
        row,evidence=observe(folder,runtime,value,fixture)
        actual=results.boundary_result(next(c for c in manifest['boundaries'] if c['id']==name_id),row)
        need(actual['status']=='passed' and expected[name_id]['status']=='passed' and actual['values']==expected[name_id]['values'],'present_cpu_boundary_mismatch')
        rows.append(dict(id=name_id,status='passed',run_ref=fact(folder/'case.json'),evidence=evidence))
        if not verify_only:remove_prefix(folder)
    result=dict(passed=True,scope='two_original_cpu_boundaries',runtime_ref=fact(runtime/'runtime.json'),build_ref=fact(build/'build.json'),reference_ref=fact(reference/'results.json'),cases=rows,
                producer=fact(Path(__file__)),readers=[fact(REPO/p) for p in ('tools/cpu/compare.py','tools/cpu/results.py','tools/dxmt/translated_regression.py')],cpu_repo=str(cpu),run_name=name)
    if not verify_only:save(output,result)
    else:need(read(output)==result,'present_cpu_replay_changed')
    return result
