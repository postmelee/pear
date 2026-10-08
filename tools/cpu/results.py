#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Portable, bounded result parsing shared by native execution and comparison."""
import hashlib
import json
import re
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def decode(raw):
    require(len(raw)<=8*1024*1024, 'record_size')
    def pairs(rows):
        result={}
        for key,value in rows:
            require(key not in result, 'duplicate_key')
            result[key]=value
        return result
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite')))


def read(path):
    path=Path(path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size<=8*1024*1024,'record_file')
    return decode(path.read_bytes())


def hex64(value):
    require(type(value) is str and re.fullmatch(r'0x[0-9a-f]{16}',value),'hex64')
    return int(value,16)


def fixture_ids(manifest):
    return [c['id'] for c in manifest['cases']]+[c['id'] for c in manifest['boundaries'] if c['stage']==2]


def admit_build(manifest, manifest_raw, build, root):
    require(build['scope']=='cpu_pe_build' and build['passed'] is True,'build_status')
    require(build['manifest_sha256']==digest(manifest_raw),'build_manifest')
    ids=fixture_ids(manifest)
    require([r['id'] for r in build['cases']]==ids,'build_case_set')
    for row in build['cases']:
        require(row['path']==row['id']+'.exe' and re.fullmatch('[a-z0-9-]+',row['id']),'binary_path')
        path=root/row['path']
        require(not path.is_symlink() and path.stat().st_size<=8*1024*1024,'binary_size')
        raw=path.read_bytes()
        require(digest(raw)==row['sha256'],'binary_changed')
        require(raw[:2]==b'MZ' and len(raw)>64,'pe_header')
        off=int.from_bytes(raw[60:64],'little')
        require(raw[off:off+6]==b'PE\0\0\x64\x86','pe_machine')
    return ids


def case_result(case, row, manifest_hash):
    require(row['id']==case['id'], 'case_identity')
    events=row['events']
    require(type(events) is list and events, 'missing_events')
    begin=events[0]
    require(begin.get('event')=='begin' and begin.get('id')==case['id'] and begin.get('manifest')==manifest_hash,'begin_identity')
    ecx,edx,xcr0=(hex64(begin[key]) for key in ('cpuid_ecx','cpuid_edx','xcr0'))
    avx=bool(ecx&(1<<28) and ecx&(1<<27) and xcr0&6==6)
    require(type(begin.get('avx')) is bool and begin['avx']==avx,'feature_record')
    require(edx&(1<<26), 'missing_sse2')
    if case['contract']['features'] and not avx:
        require(len(events)==2 and events[1]==dict(event='unavailable',reason='AVX_OSXSAVE_XCR0') and row['exit_code']==77,'feature_refusal')
        return dict(status='unavailable',values=None,reason='AVX_OSXSAVE_XCR0')
    require(row['exit_code']==42 and len(events)==2,'incomplete_case')
    result=events[1]
    require(result.get('event')=='result' and result.get('id')==case['id'] and result.get('matched') is True,'case_result')
    hex64(result['rflags'])
    values=result['values']; expected=case['contract']['expectations']
    require(type(values) is list and len(values)==len(expected),'value_count')
    normalized=[]
    for actual,want,mask in zip(values,expected,case['masks']):
        bits=int(mask['bits'],16)
        require(hex64(actual)&bits==int(want['value'],16)&bits,'golden_mismatch')
        normalized.append(hex64(actual)&bits)
    return dict(status='passed',values=normalized)


def boundary_result(case, row):
    require(row['exit_code']==42, 'boundary_failed')
    if case['id']=='abi-state':
        require(len(row['events'])==1 and row['events'][0].get('event')=='abi_state','abi_record')
        values=row['events'][0]['values']
        expected=[0x1020304050607080+i for i in range(8)]
        for i in range(10): expected.extend([0x1122334455667700+i,0x8877665544332200+i])
        require(type(values) is list and [hex64(v) for v in values]==expected*4,'abi_state_mismatch')
        return dict(status='passed',values=values)
    require(row['events']==[], 'unexpected_boundary_output')
    return dict(status='passed',values=[42])


def assess_records(manifest, build_raw, record, route):
    build=decode(build_raw)
    require(record['scope']=='cpu_'+route+'_results' and record.get('complete') is True,'incomplete_run')
    require(record['build_sha256']==digest(build_raw),'mixed_build')
    ids=fixture_ids(manifest)
    require(build.get('scope')=='cpu_pe_build' and build.get('passed') is True and
            build.get('manifest_sha256')==digest(canonical(manifest)), 'build_contract')
    require([r['id'] for r in build['cases']]==ids, 'build_case_set')
    require([r['id'] for r in record['cases']]==ids and record['completed_count']==len(ids),'missing_case')
    if route=='native':
        host=record['host']
        require(host['native_machine']==0x8664 and host['process_machine']==0 and host['pointer_bits']==64,'reference_not_native_x64')
    else:
        # Pear execution admission is a separate, still-unimplemented adapter.
        # A caller-supplied success flag must never stand in for its evidence.
        raise ValueError('candidate_admission_not_implemented')
    outcomes={}; cases={c['id']:c for c in manifest['cases']}
    boundaries={c['id']:c for c in manifest['boundaries']}
    for row,binary in zip(record['cases'],build['cases']):
        require(row['binary_sha256']==binary['sha256'] and row.get('outcome')=='exited','case_binary_or_outcome')
        c=cases.get(row['id'])
        outcomes[row['id']]=case_result(c,row,build['manifest_sha256']) if c else boundary_result(boundaries[row['id']],row)
    return outcomes
