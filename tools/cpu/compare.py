#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compare exact native/translated fixtures after admitting owned-run evidence."""
from pathlib import Path
import argparse
import json
import sys

if not __package__:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.cpu.results import read,decode,digest,require,admit_build,assess_records,case_result,boundary_result
from tools.cpu.corpus import REPO
from tools.fex import memory_wine_runtime as signing


def observe_pear(run, runtime, runtime_value, fixture):
    record=read(run/'case.json',limit=64*1024*1024);runtime_hash=digest((runtime/'runtime.json').read_bytes())
    require(record['kind']=='cpu_corpus_observation' and record['runtime_sha256']==runtime_hash,'run_runtime')
    require(record['fixture_id']==fixture['id'] and record['fixture_sha256']==fixture['sha256'],'run_fixture')
    require(record['outcome']=='exited' and not record['error'] and not record['stream_error'] and
            not record['cleanup_errors'] and record['cleanup']['complete'] and record['sentinel_survived'] and
            record['authorization_before_after_passed'],'execution_boundary')
    require(digest((run/'producer.py').read_bytes())==digest((REPO/'tools/cpu/pear_run.py').read_bytes()),'run_producer')
    for side in ('before','after'):
        control=read(run/side/'control.json')
        require(control['passed'] is True and control['runtime_sha256']==runtime_hash,'authorization_pair')
    events=[event for rows in record['events'].values() for event in rows]
    translated=[r for r in events if 'translation_value' in r]
    images=[r for r in events if r.get('event')=='image']
    require(translated and all(r['translation_value']==0 and r['translation_error']==0 and r['cpu_type']==16777228 for r in translated),'translated_host_process')
    require(images and all(r['cpu_type']==16777228 for r in images),'non_arm64_image')
    selected=runtime_value['fixtures'][fixture['id']]
    require(selected['sha256']==fixture['sha256'] and digest((runtime/selected['path']).read_bytes())==fixture['sha256'],'runtime_binary')
    launch=next(r for r in record['launches'] if r['role']=='loader')
    require(launch['argv'][-1]==str(runtime/selected['path']),'different_fixture_launched')
    raw=(run/'run/loader.stdout.log').read_bytes()
    require(len(raw)<=1024*1024,'guest_output_bound')
    stream=next(r for r in record['logs'] if r['role']=='loader' and r['channel']=='stdout')
    require(stream['sha256']==digest(raw) and stream['bytes']==len(raw) and stream['eof'] and not stream['write_error'],'guest_log_changed')
    parsed=[decode(line) for line in raw.splitlines() if line.strip()]
    require(parsed and parsed[0].get('record_kind')=='pear_bootstrap_helper','bootstrap_record')
    helper=parsed.pop(0);identity=record['processes']['loader']['identity']
    require(helper.get('version')==1 and helper.get('cpu_type')==16777228 and
            helper.get('translation_value')==0 and helper.get('query_errno')==0 and
            all(helper.get(k)==identity[k] for k in ('pid','ppid','start_sec','start_usec')),'bootstrap_identity')
    result=dict(id=fixture['id'],binary_sha256=fixture['sha256'],exit_code=record['processes']['loader']['exit_code'],
                outcome=record['outcome'],events=parsed)
    evidence=dict(case_sha256=digest((run/'case.json').read_bytes()),runtime_sha256=runtime_hash,
                  translation_observations=len(translated),arm64_image_events=len(images),
                  authorization_before_after=True,cleanup_complete=True,sentinel_survived=True,
                  late_load_coverage_complete=False)
    return result,evidence


def compare(manifest_path, build_root, reference, candidate_path, output):
    manifest=read(manifest_path);build_raw=(build_root/'build.json').read_bytes();built=decode(build_raw)
    admit_build(manifest,manifest_path.read_bytes(),built,build_root)
    native=read(reference/'results.json');expected=assess_records(manifest,build_raw,native,'native')
    # Check immutable observation bytes, not only summary fields.
    for row in native['cases']:
        for stream in ('stdout','stderr'):
            require(digest((reference/(row['id']+'.'+stream)).read_bytes())==row[stream+'_sha256'],'reference_log_changed')
        require([decode(line) for line in (reference/(row['id']+'.stdout')).read_bytes().splitlines() if line.strip()]==row['events'],'reference_events_changed')
    index=read(candidate_path);runtime=Path(index['runtime']).resolve(strict=True)
    require(index['complete'] is True and index['build_sha256']==digest(build_raw),'candidate_incomplete')
    require([r['id'] for r in index['cases']]==[r['id'] for r in built['cases']],'candidate_case_set')
    value=read(runtime/'runtime.json')
    require(value['passed'] is True and value['kind']=='cpu_corpus_development_runtime' and
            not value.get('diagnostic_only') and value['cpu_build_sha256']==digest(build_raw),'runtime_build')
    if 'cpu_correction' in value:
        from tools.cpu.fex_build import admit_correction
        # The old runtime also names its #5 smoke fixture. The component
        # reconstruction receipt binds only the three Wine/FEX identities;
        # current #6 fixtures are checked separately against the native build.
        pair={k:value['baseline_input_receipts'][k] for k in ('fex','linked','paired')}
        require(admit_correction(Path(value['cpu_correction']['path']),pair)==value['cpu_correction'],'correction_runtime')
    require(digest((runtime/'producer.py').read_bytes())==digest((REPO/'tools/cpu/runtime.py').read_bytes()),'runtime_producer')
    helpers,_=signing.signing_helpers(Path(index['signing_source']));reader=helpers.legacy(REPO)
    require(reader.inventory(runtime/signing.BUNDLE)==value['bundle_inventory'],'runtime_bundle_changed')
    cases={c['id']:c for c in manifest['cases']};boundaries={c['id']:c for c in manifest['boundaries']}
    results=[]
    for fixture,ref in zip(built['cases'],index['cases']):
        run=Path(ref['path']).resolve(strict=True)
        require(run.parent==REPO/'.build/task6','foreign_run')
        row,evidence=observe_pear(run,runtime,value,fixture)
        c=cases.get(row['id'])
        actual=case_result(c,row,built['manifest_sha256']) if c else boundary_result(boundaries[row['id']],row)
        reference_case=expected[row['id']]
        if actual['status']=='unavailable':
            status='unsupported_not_exposed'
        else:
            require(reference_case['status']=='passed','reference_unavailable_for_exposed_case')
            require(actual['values']==reference_case['values'],'native_mismatch')
            status='passed'
        results.append(dict(id=row['id'],status=status,evidence=evidence))
    require(not output.exists(),'output_exists');output.mkdir()
    result=dict(scope='finite_cpu_native_pear_comparison',passed=True,build_sha256=digest(build_raw),
                reference_sha256=digest((reference/'results.json').read_bytes()),cases=results,
                cpu_qualified=False,stage2_complete=False,game_execution=False)
    (output/'comparison.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(passed=True,cases=len(results),unsupported=[r['id'] for r in results if r['status']!='passed'])))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('manifest','reference','candidate','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--build',type=Path)
    a=p.parse_args()
    if read(a.candidate).get('scope')=='ordering_candidate':
        from tools.cpu.ordering import compare as ordering_compare
        require(read(a.manifest)==read(REPO/'tests/cpu/corpus.json'),'ordering_corpus_contract')
        ordering_compare(a.reference,a.candidate,a.output)
    else:
        require(a.build is not None,'cpu_build_required')
        compare(a.manifest,a.build,a.reference,a.candidate,a.output)
