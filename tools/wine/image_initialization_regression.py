# SPDX-License-Identifier: MIT
"""Reuse the exact CPU/ordering oracles on the corrected #40 candidate."""
from pathlib import Path
import argparse
import ast
import fcntl
import json
import shutil
from tools.dxmt.translated_inputs import REPO, fact, save, need
from tools.cpu import results, compare, ordering
from tools.wine.image_initialization_regression_run import run
from tools.fex import memory_wine_run as supervisor


def observer():
    # Adapt only the record family and producer identity. The immutable #6
    # reader retains every execution, fixture, bootstrap and output assertion.
    source=REPO/'tools/cpu/compare.py'
    tree=ast.parse(source.read_bytes())
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='observe_pear']
    need(len(nodes)==1,'translated_cpu_reader')
    replacements={'cpu_corpus_observation':'translated_graphics_observation',
                  'tools/cpu/pear_run.py':'tools/wine/image_initialization_regression_run.py'}
    for before,after in replacements.items():
        matches=[n for n in ast.walk(nodes[0]) if isinstance(n,ast.Constant) and n.value==before]
        need(len(matches)==1,'translated_cpu_reader_contract')
        matches[0].value=after
    namespace=dict(vars(compare))
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(source),'exec'),namespace)
    return namespace['observe_pear']


def observe(folder,runtime,value,fixture):
    r=results.read(folder/'case.json',limit=64*1024**2)
    need(not r.get('diagnostic_only'),'translated_cpu_diagnostic')
    raw=supervisor.verify_logs(folder/'run',r)
    for role,events in r['events'].items():
        need([results.decode(line) for line in raw[(role,'events')].splitlines()]==events,'translated_cpu_events')
    for key in ('cleanup','sentinel_cleanup'):
        c=r[key]
        need(c['complete'] and not c['errors'] and not c['observation_gap'] and all(c['reaped'].values()),'translated_cpu_cleanup')
    need(r['processes']['sentinel']['exit_code']==0,'translated_cpu_sentinel')
    return observer()(folder,runtime,value,fixture)


def remove_prefix(folder):
    r=results.read(folder/'case.json',limit=64*1024**2)
    need(r['cleanup']['complete'] and r['sentinel_survived'],'translated_prefix_cleanup')
    prefix=folder/'run/prefix'
    record=dict(removed=True,reason='completed_owned_synthetic_prefix',case_ref=fact(folder/'case.json'))
    if prefix.exists():
        need(prefix.is_dir() and not prefix.is_symlink() and folder.parent==REPO/'.build/task40','translated_prefix_scope')
        shutil.rmtree(prefix)
        save(folder/'prefix-retention.json',record)
    else:need(results.read(folder/'prefix-retention.json')==record,'translated_prefix_retention')


def corpus(runtime,cpu,reuse,output,name,seed=None,verify_only=False):
    manifest_path=REPO/'tests/cpu/corpus.json';manifest=results.read(manifest_path)
    build=cpu/'.build/task6/native-build3';reference=cpu/'.build/task6/native-results3'
    built=results.read(build/'build.json');raw_build=(build/'build.json').read_bytes()
    results.admit_build(manifest,manifest_path.read_bytes(),built,build)
    native=results.read(reference/'results.json')
    expected=results.assess_records(manifest,raw_build,native,'native')
    for row in native['cases']:
        for stream in ('stdout','stderr'):
            need(results.digest((reference/(row['id']+'.'+stream)).read_bytes())==row[stream+'_sha256'],'translated_cpu_reference_log')
        need([results.decode(line) for line in (reference/(row['id']+'.stdout')).read_bytes().splitlines() if line.strip()]==row['events'],'translated_cpu_reference_events')
    value=results.read(runtime/'runtime.json')
    result=dict(scope='translated_graphics_cpu_comparison',passed=False,runtime_ref=fact(runtime/'runtime.json'),
                build_ref=fact(build/'build.json'),reference_ref=fact(reference/'results.json'),cases=[],
                readers=[fact(REPO/'tools/cpu'/n) for n in ('compare.py','results.py','adapt.py')],game_qualified=False)
    try:
        for fixture in built['cases']:
            folder=REPO/'.build/task40'/('cpu-'+name+'-'+fixture['id'])
            print('CPU regression: '+fixture['id'],flush=True)
            if not folder.exists():
                need(not verify_only,'translated_missing_cpu_run')
                run(runtime,folder,reuse,fixture['id'],seed=seed)
            row,evidence=observe(folder,runtime,value,fixture)
            case=next((c for c in manifest['cases'] if c['id']==fixture['id']),None)
            actual=results.case_result(case,row,built['manifest_sha256']) if case else results.boundary_result(next(c for c in manifest['boundaries'] if c['id']==fixture['id']),row)
            if actual['status']=='unavailable':status='unsupported_not_exposed'
            else:
                need(expected[row['id']]['status']=='passed' and actual['values']==expected[row['id']]['values'],'translated_cpu_native_mismatch')
                status='passed'
            result['cases'].append(dict(id=row['id'],status=status,run_ref=fact(folder/'case.json'),evidence=evidence))
            if not verify_only:
                remove_prefix(folder)
                save(output,result)
        result['passed']=True
    finally:
        if not verify_only:save(output,result)
    if verify_only:need(results.read(output)==result,'translated_cpu_replay_changed')
    return result


def ordered(runtime,cpu,reuse,output,name,seed=None,verify_only=False):
    build=cpu/'.build/task6/stage3-native-pe3';reference=cpu/'.build/task6/stage3-native-results3/qualification'
    built=ordering.admit_ordering_build(build);value=results.read(runtime/'runtime.json')
    need(value['ordering_build_ref']==fact(build/'build.json'),'translated_ordering_build')
    ref=results.read(reference/'results.json');host=ref['host']
    need(ref['scope']=='ordering_native_reference' and ref['passed'] is True and ref['build_sha256']==results.digest((build/'build.json').read_bytes()),'translated_ordering_reference')
    need(host['native_machine']==0x8664 and host['process_machine']==0 and host['pointer_bits']==64 and host['system'] and host['processor'],'translated_ordering_reference_host')
    for stream in ('stdout','stderr'):
        raw=(reference/stream).read_bytes()
        need(len(raw)<=1024**2 and results.digest(raw)==ref[stream+'_sha256'],'translated_ordering_reference_log')
    expected=ordering.assess([results.decode(line) for line in (reference/'stdout').read_bytes().splitlines() if line.strip()],built['iterations'],built['rounds'],ref['exit_code'])
    need(expected==ref['assessment'],'translated_ordering_reference_assessment')
    folder=REPO/'.build/task40'/('ordering-'+name)
    if not folder.exists():
        need(not verify_only,'translated_missing_ordering_run')
        run(runtime,folder,reuse,'ordering',seed=seed)
    row,evidence=observe(folder,runtime,value,built['cases'][0])
    actual=ordering.assess(row['events'],built['iterations'],built['rounds'],row['exit_code'])
    raw=(folder/'run/loader.stderr.log').read_bytes()
    actual['policy']=ordering.policy_records(raw,actual)
    actual['checked_worker_retirements']=ordering.retirements(raw,len(actual['workers']))
    result=dict(scope='translated_graphics_ordering_comparison',passed=True,runtime_ref=fact(runtime/'runtime.json'),
                build_ref=fact(build/'build.json'),reference_ref=fact(reference/'results.json'),reader=fact(REPO/'tools/cpu/ordering.py'),
                run_ref=fact(folder/'case.json'),reference=expected,candidate=actual,evidence=evidence,game_qualified=False)
    if verify_only:need(results.read(output)==result,'translated_ordering_replay_changed')
    else:save(output,result);remove_prefix(folder)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('runtime','cpu-repo','reuse','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--seed',type=Path)
    p.add_argument('--name',required=True);p.add_argument('--suite',choices=('corpus','ordering'),required=True)
    a=p.parse_args();need(a.name.isalnum(),'translated_regression_name')
    output=a.output.absolute();need(output.parent==REPO/'.build/task40' and not output.exists(),'translated_regression_output')
    with open('/private/tmp/pear-native-compilation.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        (corpus if a.suite=='corpus' else ordered)(a.runtime.resolve(),a.cpu_repo.resolve(),a.reuse.resolve(),output,a.name,a.seed)
