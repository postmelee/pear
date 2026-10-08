#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Finite two-worker ordering calibration, exact PE build and strict assessment."""
from pathlib import Path
import argparse
import json
import re
import subprocess
import sys
import time
if not __package__:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.cpu.corpus import REPO
from tools.cpu.results import read, decode, digest, require, canonical
SOURCES=('tests/cpu/ordering.c','tests/cpu/ordering.asm')

def assess(events,iterations,rounds,exit_code):
    require(exit_code==42,'ordering_exit')
    require(type(events) is list and len(events)==rounds+1,'ordering_incomplete')
    require(events[-1]==dict(event='ordering_complete',rounds=rounds,iterations=iterations),'ordering_final')
    workers=[];coordinator=None
    for index,event in enumerate(events[:-1]):
        require(event.get('event')=='ordering_round' and event.get('round')==index and
                event.get('iterations')==iterations and event.get('joined')==2 and event.get('tls_ok') is True,'ordering_round')
        ids=event.get('workers');main=event.get('coordinator')
        require(type(main) is int and main>0 and type(ids) is list and len(ids)==2 and
                all(type(t) is int and t>0 and t!=main for t in ids) and ids[0]!=ids[1],'ordering_workers')
        require(coordinator in (None,main),'ordering_coordinator_changed');coordinator=main
        counts=event.get('counts')
        require(type(counts) is list and len(counts)==4,'ordering_modes')
        for buckets in counts:
            require(type(buckets) is list and len(buckets)==4 and
                    all(type(n) is int and n>=0 for n in buckets) and sum(buckets)==iterations,'ordering_counts')
        require(counts[0][2:]==[0,0],'locked_outcome')
        require(counts[1][2]==0,'message_passing_forbidden')
        # Plain store-buffer 00 is architecturally allowed; no occurrence quota.
        require(counts[3][0]==0,'fenced_store_buffer_forbidden')
        workers.extend(ids)
    return dict(passed=True,rounds=rounds,iterations_per_mode=iterations,
                measured_pairs=4*rounds*iterations,workers=workers,coordinator=coordinator,
                simultaneous_participants=3,universal_ordering_proof=False)

def policy_records(raw,assessment):
    require(len(raw)<=64*1024**2,'policy_log_bound')
    pattern=rb'Pear CPU (?:policy state=([0-9a-f]+) scalar=(true|false|1|0) vector=(true|false|1|0) memcpy=(true|false|1|0)|thread tid=([0-9]+) state=([0-9a-f]+))'
    pending={};observed=[]
    for match in re.finditer(pattern,raw):
        state,scalar,vector,memcpy,tid,mapped=match.groups()
        if state:
            require(state not in pending,'duplicate_live_policy_state')
            require(all(v in (b'true',b'1') for v in (scalar,vector,memcpy)),'software_policy_disabled')
            pending[state]=(True,True,True)
        else:
            require(mapped in pending,'thread_without_policy')
            pending.pop(mapped)
            observed.append(dict(tid=int(tid),scalar=True,vector=True,memcpy=True))
    require(not pending,'unpublished_policy_state')
    available=[o['tid'] for o in observed]
    for tid in [assessment['coordinator']]+assessment['workers']:
        require(tid in available,'worker_policy_missing');available.remove(tid)
    return observed

def build(output,nasm,clang,iterations,rounds):
    require(type(iterations) is int and 1<=iterations<=4096 and type(rounds) is int and 1<=rounds<=4,'ordering_budget')
    require(not output.exists(),'output_exists');output.mkdir(parents=True)
    commands=[];prefix=['/usr/bin/arch','-arm64'] if sys.platform=='darwin' else []
    def run(args):
        result=subprocess.run(prefix+[str(x) for x in args],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
        require(len(result.stdout)<=1024*1024,'build_output_bound')
        log=f'command-{len(commands)}.log';(output/log).write_bytes(result.stdout)
        commands.append(dict(argv=prefix+[str(x) for x in args],exit_code=result.returncode,log=log,sha256=digest(result.stdout)))
        require(result.returncode==0,'ordering_build_failed')
        return result.stdout.decode(errors='replace').strip()
    record=dict(scope='cpu_ordering_build',passed=False,iterations=iterations,rounds=rounds,commands=commands,cases=[])
    try:
        record['tools']={name:dict(sha256=digest(path.read_bytes()),version=run([path,flag])) for name,path,flag in [('nasm',nasm,'-v'),('clang',clang,'--version')]}
        record['sources']={p:digest((REPO/p).read_bytes()) for p in SOURCES}
        copy=output/'corresponding-source';copy.mkdir()
        for path in SOURCES: (copy/Path(path).name).write_bytes((REPO/path).read_bytes())
        obj=output/'ordering.obj';exe=output/'ordering.exe'
        run([nasm,'-f','win64',copy/'ordering.asm','-o',obj])
        run([clang,'--target=x86_64-w64-windows-gnu','-O2','-ffreestanding','-fno-builtin','-fno-stack-protector',
             '-fms-extensions','-std=c11','-nostdlib','-Wl,--entry,pear_first_dispatch','-Wl,--subsystem,console',
             '-Wl,--no-insert-timestamp',f'-DPEAR_ITERATIONS={iterations}',f'-DPEAR_ROUNDS={rounds}',
             copy/'ordering.c',obj,'-lkernel32','-lntdll','-o',exe])
        record['cases']=[dict(id='ordering',path='ordering.exe',sha256=digest(exe.read_bytes()))]
        record['passed']=True
    finally:
        (output/'build.json').write_bytes(canonical(record));(output/'producer.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(dict(built=True,iterations=iterations,rounds=rounds,guest_execution=False)))

def admit_ordering_build(root):
    record=read(root/'build.json')
    require(record['scope']=='cpu_ordering_build' and record['passed'] is True,'ordering_build_status')
    require(type(record['iterations']) is int and 1<=record['iterations']<=4096 and
            type(record['rounds']) is int and 1<=record['rounds']<=4,'ordering_budget')
    require(record['sources']=={p:digest((REPO/p).read_bytes()) for p in SOURCES},'ordering_sources_changed')
    for p in SOURCES:
        require(digest((root/'corresponding-source'/Path(p).name).read_bytes())==record['sources'][p],'ordering_copy_changed')
    require(len(record['cases'])==1,'ordering_case_set')
    fixture=record['cases'][0]
    require(fixture['id']=='ordering' and fixture['path']=='ordering.exe','ordering_case_identity')
    raw=(root/'ordering.exe').read_bytes();require(len(raw)<=8*1024**2 and digest(raw)==fixture['sha256'],'ordering_pe_changed')
    off=int.from_bytes(raw[60:64],'little');require(raw[:2]==b'MZ' and raw[off:off+6]==b'PE\0\0\x64\x86','ordering_pe_machine')
    require(len(record['commands'])==4,'ordering_build_recipe')
    for command in record['commands']:
        require(command['exit_code']==0 and digest((root/command['log']).read_bytes())==command['sha256'],'ordering_build_command')
    return record

def native(build_root,output):
    from tools.cpu.native_run import native_host
    require(not output.exists(),'output_exists');output.mkdir(parents=True)
    result=dict(scope='ordering_native_reference',passed=False)
    try:
        built=admit_ordering_build(build_root);result['host']=native_host()
        result['build_sha256']=digest((build_root/'build.json').read_bytes())
        stdout=output/'stdout';stderr=output/'stderr';start=time.monotonic()
        with stdout.open('xb') as out,stderr.open('xb') as err:
            child=subprocess.Popen([str((build_root/'ordering.exe').resolve())],cwd=output,stdin=subprocess.DEVNULL,stdout=out,stderr=err)
            try:
                while child.poll() is None:
                    require(time.monotonic()-start<120 and stdout.stat().st_size+stderr.stat().st_size<=1024*1024,'native_execution_bound')
                    time.sleep(.05)
            finally:
                if child.poll() is None:child.kill();child.wait(timeout=10)
        result.update(exit_code=child.returncode,elapsed_ms=round((time.monotonic()-start)*1000),
                      stdout_sha256=digest(stdout.read_bytes()),stderr_sha256=digest(stderr.read_bytes()))
        events=[decode(line) for line in stdout.read_bytes().splitlines() if line.strip()]
        result['assessment']=assess(events,built['iterations'],built['rounds'],child.returncode)
        result['passed']=True
    finally:
        (output/'results.json').write_bytes(canonical(result))
    print(json.dumps(result))

def observe(build_root,runtime,run):
    from tools.cpu.compare import observe_pear
    built=admit_ordering_build(build_root);value=read(runtime/'runtime.json')
    require(value['cpu_build_sha256']==digest((build_root/'build.json').read_bytes()),'ordering_runtime_build')
    require('cpu_correction' in value,'ordering_policy_runtime_missing')
    from tools.cpu.fex_build import admit_correction
    correction=Path(value['cpu_correction']['path'])
    pair={k:value['baseline_input_receipts'][k] for k in ('fex','linked','paired')}
    require(admit_correction(correction,pair)==value['cpu_correction'],'ordering_correction_changed')
    require('policy_patch_sha256' in read(correction/'build.json'),'ordering_policy_patch_missing')
    row,evidence=observe_pear(run,runtime,value,built['cases'][0])
    actual=assess(row['events'],built['iterations'],built['rounds'],row['exit_code'])
    raw=(run/'run/loader.stderr.log').read_bytes();record=read(run/'case.json',limit=64*1024**2)
    stream=next(r for r in record['logs'] if r['role']=='loader' and r['channel']=='stderr')
    require(stream['sha256']==digest(raw) and stream['bytes']==len(raw) and stream['eof'] and not stream['write_error'],'policy_log_changed')
    actual['policy']=policy_records(raw,actual);actual['evidence']=evidence
    actual['elapsed_ms']=record['elapsed_ms']
    return actual

def compare(reference,candidate,output):
    from tools.fex import memory_wine_runtime as signing
    index=read(candidate)
    require(index.get('scope')=='ordering_candidate','ordering_candidate_scope')
    build_root=Path(index['build']).resolve(strict=True);runtime=Path(index['runtime']).resolve(strict=True)
    run=Path(index['run']).resolve(strict=True);reuse=Path(index['signing_source']).resolve(strict=True)
    require(run.parent==REPO/'.build/task6','foreign_ordering_run')
    built=admit_ordering_build(build_root);build_hash=digest((build_root/'build.json').read_bytes())
    ref=read(reference/'results.json');host=ref['host']
    require(ref['scope']=='ordering_native_reference' and ref['passed'] is True and ref['build_sha256']==build_hash,'ordering_reference_identity')
    require(host['native_machine']==0x8664 and host['process_machine']==0 and host['pointer_bits']==64 and
            host['system'] and host['processor'],'ordering_reference_architecture')
    for stream in ('stdout','stderr'):
        raw=(reference/stream).read_bytes()
        require(len(raw)<=1024*1024 and digest(raw)==ref[stream+'_sha256'],'ordering_reference_log')
    events=[decode(line) for line in (reference/'stdout').read_bytes().splitlines() if line.strip()]
    expected=assess(events,built['iterations'],built['rounds'],ref['exit_code'])
    require(expected==ref['assessment'],'ordering_reference_assessment')
    value=read(runtime/'runtime.json')
    require(value['passed'] is True and not value.get('diagnostic_only'),'ordering_runtime_status')
    require(digest((runtime/'producer.py').read_bytes())==digest((REPO/'tools/cpu/runtime.py').read_bytes()),'ordering_runtime_producer')
    helpers,_=signing.signing_helpers(reuse);reader=helpers.legacy(REPO)
    require(reader.inventory(runtime/signing.BUNDLE)==value['bundle_inventory'],'ordering_bundle_changed')
    actual=observe(build_root,runtime,run)
    # Scheduling changes frequencies and IDs. Both exact-PE executions must
    # satisfy the same counts and forbidden conditions, not identical buckets.
    require(not output.exists(),'output_exists');output.mkdir()
    result=dict(scope='finite_ordering_comparison',passed=True,build_sha256=build_hash,
                reference_sha256=digest((reference/'results.json').read_bytes()),
                reference=expected,candidate=actual,cpu_qualified=False,game_execution=False)
    (output/'comparison.json').write_bytes(canonical(result))
    print(json.dumps(dict(passed=True,measured_pairs=actual['measured_pairs'],workers=len(actual['workers']))))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    b=sub.add_parser('build')
    for key in ('output','nasm','clang'):b.add_argument('--'+key,type=Path,required=True)
    b.add_argument('--iterations',type=int,required=True);b.add_argument('--rounds',type=int,required=True)
    n=sub.add_parser('native')
    for key in ('build','output'):n.add_argument('--'+key,type=Path,required=True)
    o=sub.add_parser('observe')
    for key in ('build','runtime','run'):o.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args()
    if a.command=='build':build(a.output.absolute(),a.nasm.resolve(),a.clang.resolve(),a.iterations,a.rounds)
    elif a.command=='native':native(a.build.resolve(),a.output.absolute())
    else:print(json.dumps(observe(a.build.resolve(),a.runtime.resolve(),a.run.resolve()),indent=2))
