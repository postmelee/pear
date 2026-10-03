#!/usr/bin/env python3
"""Run/replay a finite source-bound ordinary ARM64 Wine memory-owner fixture.

Original Pear orchestration; exact reviewed Wine process/image readers and
Task #7 cleanup functions are captured without executing their CLI entrypoints.
No FEX initializer, translated guest, raw fault control or production EC role.
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
from contextlib import contextmanager
import importlib.util
import os
from pathlib import Path
import re
import signal
import struct
import sys
import time
from types import SimpleNamespace
import uuid

if __package__:
    from .common import (REPO, Error, need, relative, read_relative, decode_json,
                         load_json, encoded, sha256, digest_bytes, write_json, operation_output)
    from . import memory_wine_runtime as materializer, memory_wine_build as builder
    from . import memory_wine_bitmap as bitmap_policy
else:
    from common import (REPO, Error, need, relative, read_relative, decode_json,
                        load_json, encoded, sha256, digest_bytes, write_json, operation_output)
    import memory_wine_runtime as materializer
    import memory_wine_build as builder
    import memory_wine_bitmap as bitmap_policy

if __package__:
    from . import memory_resume_checks as atomic_checks
else:
    import memory_resume_checks as atomic_checks

SCOPE = 'finite_ordinary_arm64_wine_memory_owner'
BOUNDS = {'grace_ms':3000, 'terminate_ms':2000, 'kill_ms':5000, 'drain_ms':1000}
TIMEOUT_MS = 180000
STREAM_LIMIT = 2 * 1024**2
WINE_HELPERS = ('common','prepare','toolchain','modules','abi_review',
                'dynamic_evidence','exception_evidence','run_fixtures','api_runner')
REUSE_PATH = 'tools/dxmt/run_pairing.py'
REUSE_SHA = '038adc9355892d853dce2886f06dbeab3c073e14d343bf10aa4effc968ee6402'
REUSE_FUNCTIONS = ('local','wine_helpers','integer','failure_detail','finish_capture',
                   'cleanup_session','launch_recipes','validate_launches')
FALSE_FLAGS = ('fex_initialization','hybrid_execution','translated_guest_execution',
               'arm64ec_role_qualified','ec_registration_qualified','runtime_qualified',
               'game_qualified','distribution_qualified','stage3_complete','runtime_eligible')
PRODUCERS = tuple(sorted(set(materializer.PRODUCERS) |
    {'tools/fex/memory_wine_run.py', 'tools/fex/memory_run.py', 'tools/fex/memory_resume_checks.py', 'tools/fex/memory_wine_bitmap.py'} |
    {'tools/wine/' + name + '.py' for name in WINE_HELPERS}))


def fields(value, names, kind=None):
    need(type(value) is dict and set(value) == set(names), 'memory_wine_run_fields')
    if kind:
        need(type(value['schema_version']) is int and value['schema_version'] == 1
             and value['record_kind'] == kind, 'memory_wine_run_kind')


def same(left,right,code):
    need(encoded(left) == encoded(right),code)


def integer(value,low=0,high=2**53-1):
    return type(value) is int and low <= value <= high


def producers(repo=REPO):
    return {name:digest_bytes(read_relative(repo,name)) for name in PRODUCERS}


@contextmanager
def supervision(reuse_root, repo=REPO, expected=None):
    """Capture reviewed bodies; isolate/restores all historical import names.

    Only the private toolkit's declared stream limit changes. Source functions,
    production globals, original native-only parser and all old CLIs stay intact.
    """
    raw = read_relative(Path(reuse_root),REUSE_PATH,2*1024**2)
    need(digest_bytes(raw) == REUSE_SHA,'memory_wine_supervisor_pin')
    namespace = {'ast':ast,'importlib':importlib,'sys':sys,'Path':Path,'SimpleNamespace':SimpleNamespace,
        'REPO':Path(repo),'WINE_HELPERS':WINE_HELPERS,'Error':Error,'need':need,'relative':relative,
        'read_relative':read_relative,'decode_json':decode_json,'digest':digest_bytes,'encoded':encoded,
        'fields':fields,'os':os,'time':time,'signal':signal,'BOUNDS':BOUNDS,'write_new':write_json}
    nodes=[node for node in ast.parse(raw).body if isinstance(node,ast.FunctionDef)
           and node.name in REUSE_FUNCTIONS]
    need(len(nodes)==len(REUSE_FUNCTIONS) and all(not node.decorator_list or
         node.name=='wine_helpers' and len(node.decorator_list)==1 and
         isinstance(node.decorator_list[0],ast.Name) and node.decorator_list[0].id=='contextmanager'
         for node in nodes),'memory_wine_supervisor_functions')
    namespace['contextmanager']=contextmanager
    exec(compile(ast.Module(body=nodes,type_ignores=[]),REUSE_PATH,'exec'),namespace)
    with namespace['wine_helpers'](repo,expected) as helpers:
        helpers.base.STREAM_LIMIT=STREAM_LIMIT
        yield SimpleNamespace(**namespace), helpers


def environment(work,prefix,nonce,home):
    need(type(nonce) is str and re.fullmatch('[0-9a-f]{32}',nonce) is not None,'memory_wine_nonce')
    need(home is None or type(home) is str and home.startswith('/') and '\0' not in home,
         'memory_wine_home')
    value={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','TMPDIR':str(work/'tmp'),
        'WINEPREFIX':str(prefix),'WINEDEBUG':'-all','PEAR_BOOTSTRAP_NONCE':nonce,
        'PEAR_BOOTSTRAP_GENERATION':'0'}
    if home is not None:value['HOME']=home
    return value


def loader_environment(base,endpoint,server_pid,nonce):
    path=Path(endpoint)
    need(path.parent.parent==Path('/private/tmp') and '..' not in path.parts
         and path.name=='control' and path.parent.name.startswith('pear-stage3-')
         and integer(server_pid,2,2**31-1),'memory_wine_control_scope')
    return {**base,'PEAR_STAGE3_CONTROL':endpoint,'PEAR_WINE_ABI_FIXTURE':'1',
        'PEAR_BOOTSTRAP_SERVER_PID':str(server_pid),'WINEDLLOVERRIDES':'mscoree=',
        'PEAR_FEX_MEMORY_FIXTURE_NONCE':nonce}


def assessment_packet(value):
    return {'entrypoints':{'loader':value['entrypoints']['loader'], 'server':value['entrypoints']['server'],
             'ntdll':value['entrypoints']['ntdll_native']},
            'native_images':value['native_images'],'code_publication_policy':'page-wx',
            'arena_capacity':value['baseline_loader_capacity']}


def verify_logs(root,result):
    observed={};total=0
    need(type(result['logs']) is list and 6<=len(result['logs'])<=70,'memory_wine_log_count')
    for row in result['logs']:
        fields(row,('role','channel','path','sha256','bytes','observed_bytes','eof','write_error'))
        need(type(row['role']) is str and re.fullmatch('(loader|server|sentinel|process-[0-9]{2})',row['role'])
             and row['channel'] in ('stdout','stderr','events'),'memory_wine_log_role')
        key=(row['role'],row['channel'])
        need(key not in observed and row['path']=='.'.join(key)+'.log','memory_wine_log_set')
        raw=read_relative(root,row['path'],STREAM_LIMIT)
        need(integer(row['bytes'],0,STREAM_LIMIT) and integer(row['observed_bytes'],0,STREAM_LIMIT)
             and row['bytes']==row['observed_bytes']==len(raw) and row['eof'] is True
             and row['write_error'] is None and digest_bytes(raw)==row['sha256'],'memory_wine_log_changed')
        if row['channel']=='events':
            need(not raw or raw.endswith(b'\n'),'memory_wine_event_truncation');total+=len(raw)
        observed[key]=raw
    wanted={(role,channel) for role in ('loader','server','sentinel') for channel in ('stdout','stderr')}
    wanted|={(role,'events') for role in result['events']}
    need(set(observed)==wanted and total<=32*1024**2,'memory_wine_log_coverage')
    return observed


def json_lines(raw,limit=4096):
    need(type(raw) is bytes and 0<len(raw)<=STREAM_LIMIT and raw.endswith(b'\n'),'memory_wine_stdout_bound')
    lines=raw.splitlines(keepends=True)
    need(len(lines)<=limit and all(line.endswith(b'\n') and len(line)<=32768 for line in lines),
         'memory_wine_stdout_shape')
    return [decode_json(line,32768) for line in lines]


def suite_contract():
    """Closed finite original fixture cases, independently checked in Wine scope.

    Reuse decision: retain the source fixture and its reviewed control counts,
    but do not project fabricated native-admission rows into memory_run's parser.
    """
    counts={'reserve_extent':103,'retire_extent':103,'begin_two_page_write':39,'publish_two_pages':39,
        'enter_owned_leaf':73,'exit_to_native_gate':73,'begin_cross_page_instruction_pair':1,
        'publish_cross_page_instruction_pair':1,'enter_before_source_continuation':1,
        'pin_saved_source_resume':1,'direct_owned_handoff_to_native':1,'poll_existing_owned_handoff':1,
        'admit_finite_saved_resume':127,'discard_owned_saved_resume':127,'release_original_pin_epoch':1,
        'begin_unpublished_abort_control':1,'abort_unpublished_window':1,
        'register_actual_native_executor':1,'query_current_token':103,'mixed_extent_query_unavailable':112,
        'unregister_actual_native_executor':1}
    refusals={'version_mismatch':2,'record_size_mismatch':1,'unknown_opcode':1,'unknown_flags':1,
        'reserved_word':1,'reserved_word64':1,'foreign_owner':6,'stale_generation':6,'foreign_allocation':6,
        'offset_alias':6,'extent_alias':6,'unselected_role':1,'native_fixture_cannot_select_arm64ec_role':3,
        'wrapped_write_range':1,'source_guard_write':1,'empty_write':1,'ordinary_exit_cannot_drop_saved_resume':1,
        'nested_handoff_refused':1,'poll_requires_original_pin_epoch':1,'poll_requires_exact_resume_offset':1,
        'poll_requires_existing_continuation':1,'unregister_cannot_drop_saved_resume':1,
        'retirement_keeps_saved_generation':3,'continuation_capacity_preserves_old_pins':4,
        'new_epoch_cannot_release_original_pin':1,'duplicate_retirement':6,'shared_capacity_exhausted':4,
        'fragmented_free_bytes_refused':4,'dispatcher_capacity_exhausted':4}
    counts.update(dict.fromkeys(refusals,1))
    opcodes=dict.fromkeys(counts,6)
    opcodes.update({'register_actual_native_executor':7,'reserve_extent':1,'begin_two_page_write':2,
        'publish_two_pages':3,'enter_owned_leaf':8,'exit_to_native_gate':9,'begin_cross_page_instruction_pair':2,
        'publish_cross_page_instruction_pair':3,'enter_before_source_continuation':8,'pin_saved_source_resume':10,
        'direct_owned_handoff_to_native':13,'poll_existing_owned_handoff':13,'admit_finite_saved_resume':10,
        'discard_owned_saved_resume':11,'release_original_pin_epoch':11,'begin_unpublished_abort_control':2,
        'abort_unpublished_window':4,'retire_extent':5,'unregister_actual_native_executor':12,'unknown_opcode':15,
        'native_fixture_cannot_select_arm64ec_role':7,'wrapped_write_range':2,'source_guard_write':2,'empty_write':2,
        'ordinary_exit_cannot_drop_saved_resume':9,'nested_handoff_refused':13,'poll_requires_original_pin_epoch':13,
        'poll_requires_exact_resume_offset':13,'poll_requires_existing_continuation':13,
        'unregister_cannot_drop_saved_resume':12,'retirement_keeps_saved_generation':5,
        'continuation_capacity_preserves_old_pins':10,'new_epoch_cannot_release_original_pin':11,
        'duplicate_retirement':5,'shared_capacity_exhausted':1,'fragmented_free_bytes_refused':1,
        'dispatcher_capacity_exhausted':1})
    atomic_counts, atomic_refusals, atomic_opcodes = atomic_checks.controls('wine_owner')
    counts.update(atomic_counts); refusals.update(atomic_refusals); opcodes.update(atomic_opcodes)
    return counts,refusals,opcodes


def bootstrap_observation(row,child,helper):
    fields(row,('version','record_kind','pid','ppid','start_sec','start_usec','cpu_type',
        'translation_value','query_errno','user_page','vm_page','kernel_page','kernel_error'))
    need(integer(row['version'],1,1) and row['record_kind']=='pear_bootstrap_helper'
         and all(type(row[k]) is int and row[k]==v for k,v in child.identity.items())
         and integer(row['user_page']) and row['user_page'] in (4096,16384),'memory_wine_bootstrap_identity')
    helper.base.native_snapshot(row,row['user_page'])


def owner_output(raw,child,helper):
    rows=json_lines(raw);need(len(rows)>6,'memory_wine_fixture_count')
    bootstrap_observation(rows[0],child,helper)
    for row,(control,opcode) in zip(rows[1:4],[('register_readiness_native_executor',7),
        ('query_readiness_native_owner',6),('unregister_readiness_native_executor',12)]):
        wanted={'version':1,'record_kind':'pear_fex_memory_wine','event':'readiness_call','control':control,
                'opcode':opcode,'returned_status':0,'status':0,'native_error_domain':0,'native_error_code':0}
        same(row,wanted,'memory_wine_readiness')
    calls=rows[4:-2];counted,refusals,opcodes=suite_contract();counts=Counter()
    keys={'version','record_kind','scope','sequence','event','control','opcode','returned_status','status',
        'requested_state','operation_offset','operation_size','allocation_id','generation','extent_offset',
        'extent_size','write_epoch','executor_id','continuation_id','executor_state','lifecycle','protection',
        'capabilities','native_error_domain','native_error_code'}
    for sequence,row in enumerate(calls,1):
        fields(row,keys)
        need(row['record_kind']=='pear_fex_memory_fixture' and row['scope']=='wine_owner'
             and row['event']=='owner_call' and integer(row['version'],1,1)
             and integer(row['sequence'],sequence,sequence),'memory_wine_call_order')
        need(type(row['control']) is str and row['control'] in counted,'memory_wine_control')
        numbers=keys-{'record_kind','scope','event','control','operation_offset','operation_size'}
        need(all(integer(row[k],-2**31 if k=='native_error_code' else 0,
             2**31-1 if k=='native_error_code' else 2**53-1) for k in numbers),'memory_wine_call_type')
        need(all(type(row[k]) is str and re.fullmatch('[0-9a-f]{16}',row[k]) for k in
             ('operation_offset','operation_size')),'memory_wine_range_encoding')
        status=3 if row['control']=='mixed_extent_query_unavailable' else refusals.get(row['control'],0)
        need(row['status']==row['returned_status']==status and row['opcode']==opcodes[row['control']]
             and row['requested_state'] in range(6) and row['executor_state'] in range(6)
             and row['lifecycle'] in range(6) and row['protection'] in range(3)
             and row['capabilities'] & ~7 == 0 and row['native_error_domain'] in range(4)
             and (row['native_error_domain'] or row['native_error_code']==0)
             and (status or row['native_error_domain']==row['native_error_code']==0),'memory_wine_call_status')
        if status:
            need(all(row[k]==0 for k in ('allocation_id','generation','extent_offset','extent_size','write_epoch',
                 'executor_id','continuation_id','executor_state','lifecycle','protection','capabilities')),
                 'memory_wine_refusal_facts')
        counts[row['control']]+=1
    need(counts==counted,'memory_wine_control_counts')
    atomic_checks.validate(calls, need, scope='wine_owner')
    terminal={'version':1,'record_kind':'pear_fex_memory_fixture','scope':'wine_owner',
        'sequence':len(calls)+1,'event':'suite_complete','passed':True,'checked_ec':False,
        'owner_calls':len(calls),'refusals':sum(row['status']!=0 for row in calls),'allocations':103,
        'retirements':103,'publications':40,'owned_code_calls':73,'protection_observations':83,
        'patch_rounds':32,'fragmentation_controls':1,'continuation_controls':2,
        'fex_initialization':False,'translated_guest_execution':False,'game_execution':False}
    same(rows[-2],terminal,'memory_wine_suite_terminal')
    finish=rows[-1]
    fields(finish,('version','record_kind','event','native_arm64_pe_execution','virtual_query_observations',
        'checked_ec','ec_registration_exercised','wine_view_registration','fex_initialization',
        'translated_guest_execution','game_execution','exit_code'))
    wanted={'version':1,'record_kind':'pear_fex_memory_wine','event':'finish','native_arm64_pe_execution':True,
        'checked_ec':False,'ec_registration_exercised':False,'wine_view_registration':True,
        'fex_initialization':False,'translated_guest_execution':False,'game_execution':False,'exit_code':0}
    same({k:v for k,v in finish.items() if k!='virtual_query_observations'},wanted,'memory_wine_finish')
    need(integer(finish['virtual_query_observations'],83,100000),'memory_wine_virtual_query_count')
    shared=sum(row['control']=='reserve_extent' and row['status']==0 and row['extent_size']>=16777216
               for row in calls)
    need(shared==38,'memory_wine_shared_reservation_count')
    return {'readiness_calls':3,**{k:terminal[k] for k in ('owner_calls','refusals','allocations','retirements',
        'publications','owned_code_calls','protection_observations','patch_rounds','fragmentation_controls',
        'continuation_controls')},'virtual_query_observations':finish['virtual_query_observations'],
        'shared_reservation_count':shared,'wine_view_registration_observed':True,'checked_ec':False,
        'arm64ec_role_qualified':False,'fex_initialization':False}


def bitmap_output(raw,expected):
    need(type(raw) is bytes and len(raw)<=STREAM_LIMIT and integer(expected,1,128),'memory_wine_bitmap_bound')
    try:
        pairs,diagnostics=bitmap_policy.parse_stream(raw,expected)
    except bitmap_policy.Refused as exc:
        raise Error('memory_wine_bitmap_diagnostic_'+str(exc)) from exc
    for pair in pairs:
        row=pair['bitmap']
        need(all(row[k] is True for k in ('set_observed','clear_observed','restoration_observed',
             'none_before','none_after','actual_peb_bitmap','restoration_attempted'))
             and row['hybrid_classification'] is False and integer(row['error_domain'],0,0)
             and integer(row['error_code'],0,0),'memory_wine_bitmap_failed')
    return {'self_tests':len(pairs),'actual_peb_bitmap_observed':True,'set_read_clear_read_observed':True,
        'none_before_and_after_observed':True,'source_view_and_bitmap_restoration_observed':True,
        'diagnostic_self_tests':len(pairs),
        'diagnostic_rows_sha256':digest_bytes(encoded([pair['diagnostic'] for pair in pairs])),
        'hybrid_classification':False,'arm64ec_role_qualified':False}, diagnostics


def apiset_defaults(data):
    """Read Wine's actual ARM64 PE .apiset v6 table; never infer from filenames."""
    need(type(data) is bytes and 64<=len(data)<=64*1024**2,'memory_wine_apiset_bytes')
    def uint(fmt,at):
        need(0<=at and at+struct.calcsize('<'+fmt)<=len(data),'memory_wine_apiset_pe_bound')
        return struct.unpack_from('<'+fmt,data,at)[0]
    need(data[:2]==b'MZ','memory_wine_apiset_pe_header')
    at=uint('I',60);opt=at+24;count=uint('H',at+6);size=uint('H',at+20)
    need(at>=64 and data[at:at+4]==b'PE\0\0' and uint('H',at+4)==0xaa64
         and uint('H',opt)==0x20b and size>=240 and 1<=count<=96,'memory_wine_apiset_pe_header')
    sections=[]
    for i in range(count):
        p=opt+size+i*40;need(p+40<=len(data),'memory_wine_apiset_section_bound')
        if data[p:p+8].rstrip(b'\0')==b'.apiset':
            virtual=uint('I',p+8);span=uint('I',p+16);offset=uint('I',p+20)
            need(28<=virtual<=span and offset+span<=len(data),'memory_wine_apiset_section_bound')
            sections.append(data[offset:offset+virtual])
    need(len(sections)==1,'memory_wine_apiset_section')
    blob=sections[0]
    version,length,flags,entries,entry_offset,hash_offset,factor=struct.unpack_from('<7I',blob)
    need(version==6 and flags==0 and 28<=length<=len(blob) and 0<entries<=4096
         and entry_offset==28 and entry_offset+entries*24<=length
         and hash_offset+entries*8<=length and factor>0,'memory_wine_apiset_header')
    def words(at,count):
        need(0<=at and at+count*4<=length,'memory_wine_apiset_table_bound')
        return struct.unpack_from('<'+str(count)+'I',blob,at)
    def text(at,span):
        need(span>0 and span%2==0 and at>=28 and at+span<=length,'memory_wine_apiset_string_bound')
        try: value=blob[at:at+span].decode('utf-16-le')
        except UnicodeError: raise Error('memory_wine_apiset_string') from None
        need(re.fullmatch('[a-z0-9._-]+',value) is not None,'memory_wine_apiset_string')
        return value
    mapping={};expected_hash=[]
    for i in range(entries):
        flag,nameoff,namelen,hashed,valoff,valcount=words(entry_offset+i*24,6)
        need(flag==1 and hashed>0 and hashed%2==0 and hashed<=namelen and 0<valcount<=64,
             'memory_wine_apiset_entry')
        name=text(nameoff,namelen);need(name not in mapping,'memory_wine_apiset_duplicate')
        targets=[]
        for j in range(valcount):
            vf,selectoroff,selectorlen,targetoff,targetlen=words(valoff+j*20,5)
            need(vf==0 and bool(selectoroff)==bool(selectorlen) and bool(targetoff)==bool(targetlen),
                 'memory_wine_apiset_value')
            selector=text(selectoroff,selectorlen) if selectorlen else None
            target=text(targetoff,targetlen) if targetlen else None
            targets.append((selector,target))
        defaults=[target for selector,target in targets if selector is None]
        need(len(defaults)<=1,'memory_wine_apiset_default_duplicate')
        mapping[name+'.dll']=defaults[0] if defaults else None
        h=0
        for c in name[:hashed//2]:h=(h*factor+ord(c))&0xffffffff
        expected_hash.append((h,i))
    hashes=[words(hash_offset+i*8,2) for i in range(entries)]
    need(sorted(hashes)==sorted(expected_hash) and all(hashes[i][0]<=hashes[i+1][0] for i in range(entries-1)),
         'memory_wine_apiset_hash_index')
    return mapping


class BaselinePEMetadata:
    """Bounded baseline metadata only; no delayed loader or generic admission."""
    def __init__(self,data):
        need(type(data) is bytes and 64<=len(data)<=64*1024**2,'memory_wine_crt_pe_bytes')
        self.data=data
        at=self.number('I',60);self.opt=at+24
        count=self.number('H',at+6);size=self.number('H',at+20)
        need(at>=64 and data[:2]==b'MZ' and data[at:at+4]==b'PE\0\0'
             and self.number('H',at+4)==0xaa64 and self.number('H',self.opt)==0x20b
             and self.number('H',at+22)&0x2000 and self.number('I',self.opt+108)==16
             and size>=240 and 1<=count<=96,'memory_wine_crt_baseline_arm64_dll')
        self.base=self.number('Q',self.opt+24);self.image_size=self.number('I',self.opt+56);self.sections=[]
        for i in range(count):
            p=self.opt+size+i*40
            span,rva,raw_size,raw,flags=[self.number('I',p+n) for n in (8,12,16,20,36)]
            need(raw+raw_size<=len(data) and rva+span<=2**32,'memory_wine_crt_pe_section')
            self.sections.append((rva,min(span,raw_size),raw,flags))
    def number(self,fmt,at):
        need(type(at) is int and 0<=at and at+struct.calcsize('<'+fmt)<=len(self.data),'memory_wine_crt_pe_bound')
        return struct.unpack_from('<'+fmt,self.data,at)[0]
    def mapped(self,rva,size):
        need(type(rva) is int and type(size) is int and rva>0 and size>0 and rva+size<=self.image_size,'memory_wine_crt_rva')
        found=[(raw+rva-base,flags) for base,span,raw,flags in self.sections
               if rva>=base and rva-base+size<=span]
        need(len(found)==1,'memory_wine_crt_rva');return found[0]
    def word(self,rva):return self.number('Q',self.mapped(rva,8)[0])
    def string(self,rva,limit=512):
        at,_=self.mapped(rva,1);end=self.data.find(b'\0',at,min(len(self.data),at+limit))
        need(end>at,'memory_wine_crt_string');self.mapped(rva,end-at+1)
        try:value=self.data[at:end].decode('ascii')
        except UnicodeError:raise Error('memory_wine_crt_string') from None
        need(all(33<=ord(c)<=126 for c in value),'memory_wine_crt_string');return value
    def directory(self,index):return self.number('I',self.opt+112+index*8),self.number('I',self.opt+116+index*8)
    def selected_export(self,name):
        rva,size=self.directory(0);need(rva and rva+size<=2**32 and 40<=size<=1024**2,'memory_wine_crt_export_directory')
        self.mapped(rva,size);p,_=self.mapped(rva,40)
        base=self.number('I',p+16);count=self.number('I',p+20);names=self.number('I',p+24)
        need(0<names<=count<=65536,'memory_wine_crt_export_counts')
        addresses,_=self.mapped(self.number('I',p+28),count*4)
        table,_=self.mapped(self.number('I',p+32),names*4)
        ordinals,_=self.mapped(self.number('I',p+36),names*2)
        selected=[];seen=set()
        for i in range(names):
            actual=self.string(self.number('I',table+4*i))
            need(actual not in seen,'memory_wine_crt_export_duplicate');seen.add(actual)
            index=self.number('H',ordinals+2*i);need(index<count,'memory_wine_crt_export_ordinal')
            if actual!=name:continue
            target=self.number('I',addresses+4*index);need(target,'memory_wine_crt_export_zero')
            if rva<=target<rva+size:
                forward=self.string(target);need(target+len(forward)+1<=rva+size,'memory_wine_crt_forwarder_bound')
                selected.append({'name':name,'ordinal':base+index,'target_kind':'forwarder','forwarder':forward})
            else:
                _,flags=self.mapped(target,4)
                need(target%4==0 and flags&0x20000000,'memory_wine_crt_export_non_executable')
                selected.append({'name':name,'ordinal':base+index,'target_kind':'executable_source_export','forwarder':None})
        need(len(selected)==1,'memory_wine_crt_selected_export_missing');return selected[0]


def ucrt_delay_table(raw):
    """Only the pinned source's two DLLs/three named RVA delay descriptors."""
    pe=BaselinePEMetadata(raw);rva,size=pe.directory(13)
    need(rva%8==0 and size==96 and pe.base>0 and pe.base+pe.image_size<2**64
         and 0<pe.image_size<2**32,'memory_wine_ucrt_delay_directory')
    at,_=pe.mapped(rva,size);wanted=[('advapi32.dll',['SystemFunction036']),
                                  ('user32.dll',['GetActiveWindow','MessageBoxIndirectW'])]
    observations=[];ranges=[(rva,size)]
    def exclusive(start,span):
        pe.mapped(start,span)
        need(all(start+span<=b or b+s<=start for b,s in ranges),'memory_wine_ucrt_delay_slot_alias')
        ranges.append((start,span))
    for i,(module,symbols) in enumerate(wanted):
        attrs,name,handle,iat,int_,bound,unload,timestamp=struct.unpack_from('<8I',raw,at+i*32)
        need(attrs==1 and bound==unload==timestamp==0 and pe.string(name,128)==module,
             'memory_wine_ucrt_delay_descriptor')
        need(handle%8==iat%8==int_%8==0 and pe.word(handle)==0
             and pe.mapped(handle,8)[1]&0x80000000 and pe.mapped(iat,8*(len(symbols)+1))[1]&0x80000000,
             'memory_wine_ucrt_delay_mutable_slots')
        exclusive(name,len(module)+1)
        found=[]
        for j,symbol in enumerate(symbols):
            entry=pe.word(int_+8*j)
            need(0<entry<2**32 and entry%2==0,'memory_wine_ucrt_delay_named_thunk')
            hint=pe.number('H',pe.mapped(entry,2)[0]);actual=pe.string(entry+2)
            need(actual==symbol and hint==0,'memory_wine_ucrt_delay_symbol')
            exclusive(entry,2+len(symbol)+1)
            target=pe.word(iat+8*j)
            need(pe.base>0 and pe.base<=target<pe.base+2**32,'memory_wine_ucrt_delay_thunk_va')
            code=target-pe.base
            need(code%4==0 and code+4<=pe.image_size and pe.mapped(code,4)[1]&0x20000000,'memory_wine_ucrt_delay_thunk_non_executable')
            found.append(symbol)
        need(pe.word(int_+8*len(symbols))==0 and pe.word(iat+8*len(symbols))==0,
             'memory_wine_ucrt_delay_thunk_terminator')
        for start,span in [(handle,8),(iat,8*(len(symbols)+1)),(int_,8*(len(symbols)+1))]:
            exclusive(start,span)
        observations.append({'module':module,'symbols':found,'attributes':attrs,
            'module_handle_zero':True,'int_terminated':True,'iat_terminated':True,
            'initial_iat_executable_thunks_observed':True,'bound_unload_timestamp_zero':True})
    need(raw[at+64:at+96]==b'\0'*32,'memory_wine_ucrt_delay_descriptor_terminator')
    return {'descriptor_count':2,'named_thunk_count':3,'table_bytes':96,
        'table_sha256':digest_bytes(raw[at:at+size]),'imports':observations,'execution':False}


def ucrt_delay_closure(runtime,value,by_name,payload):
    """Selected baseline UCRT imports/export route; other dependencies unperformed."""
    table=ucrt_delay_table(payload(by_name['ucrtbase.dll']))
    built_root=Path(value['build_ref']['path']);source_rows=[]
    specs={
      'dlls/ucrtbase/Makefile.in':['DELAYIMPORTS = advapi32 user32'],
      'dlls/advapi32/advapi32.spec':['@ stdcall SystemFunction036(ptr long) cryptbase.SystemFunction036'],
      'dlls/user32/user32.spec':['@ stdcall GetActiveWindow()','@ stdcall MessageBoxIndirectW(ptr)'],
      'dlls/cryptbase/cryptbase.spec':['@ stdcall SystemFunction036(ptr long)'],
      'include/ntsecapi.h':['#define RtlGenRandom                    SystemFunction036']}
    for path,lines in specs.items():
        raw=read_relative(built_root,'source/'+path,2*1024**2)
        for line in lines:need(raw.splitlines().count(line.encode())==1,'memory_wine_ucrt_delay_source_spec')
        if path=='dlls/ucrtbase/Makefile.in':
            need([line.strip() for line in raw.splitlines() if line.strip().startswith(b'DELAYIMPORTS')]
                 ==[b'DELAYIMPORTS = advapi32 user32'],'memory_wine_ucrt_delay_source_spec')
        source_rows.append({'path':path,'sha256':digest_bytes(raw)})
    # Byte-bind the inspected fallback/generator source without claiming its
    # functions executed or all their transitive dependencies were resolved.
    for path in ('dlls/msvcrt/misc.c','dlls/msvcrt/exit.c','dlls/cryptbase/cryptbase_main.c',
                 'dlls/user32/input.c','dlls/user32/msgbox.c','tools/winebuild/import.c','dlls/ntdll/loader.c'):
        raw=read_relative(built_root,'source/'+path,2*1024**2)
        source_rows.append({'path':path,'sha256':digest_bytes(raw)})
    providers=[];exports=[]
    for module,names in [('advapi32.dll',['SystemFunction036']),('cryptbase.dll',['SystemFunction036']),
                         ('user32.dll',['GetActiveWindow','MessageBoxIndirectW'])]:
        need(module in by_name,'memory_wine_ucrt_delay_provider_missing');row=by_name[module]
        need(row.get('machine')==0xaa64 and row.get('classification')=='ordinary_arm64_image'
             and row.get('load_admission')=='unperformed' and row.get('execution_performed') is False,
             'memory_wine_ucrt_delay_provider_selection')
        raw=payload(row);pe=BaselinePEMetadata(raw)
        selected=[pe.selected_export(name) for name in names]
        for export in selected:
            need(export['forwarder']==('cryptbase.SystemFunction036' if module=='advapi32.dll' else None),
                 'memory_wine_ucrt_delay_forwarder_target')
        providers.append({'name':module,'path':row['path'],'sha256':row['sha256'],'size_bytes':row['size_bytes'],
            'other_delay_directory_present':pe.directory(13)!=(0,0),
            'other_eager_delay_symbol_resolution':'unperformed'})
        exports.append({'module':module,'selected_exports':selected})
    return {'scope':'source_selected_ucrt_delay_module_and_export_bytes','table':table,
        'providers':providers,'selected_exports':exports,'source_files':source_rows,
        'all_provider_dependency_and_symbol_resolution':'unperformed','execution':False}



def crt_closure(runtime,value):
    """Finite fixture's imported module/default-APIset provider byte closure.

    This does not claim all PE named/ordinal/forwarder symbols are resolved;
    actual ordinary execution is a separate gate. The full verified overlay is
    mandatory and its source-built KernelBase/NTDLL providers stay byte-bound.
    """
    rows=value['pe_images'];need(type(rows) is list and rows,'memory_wine_crt_pe_inventory')
    by_name={}
    for row in rows:
        name=Path(row['path']).name.lower()
        if '/aarch64-windows/' in row['path']:
            need(name not in by_name,'memory_wine_crt_duplicate_image');by_name[name]=row
    required=('apisetschema.dll','ucrtbase.dll','kernel32.dll','kernelbase.dll','ntdll.dll')
    need(all(name in by_name for name in required),'memory_wine_crt_missing_provider')
    def payload(row):
        raw=read_relative(runtime,row['path'],64*1024**2)
        need(digest_bytes(raw)==row['sha256'] and len(raw)==row['size_bytes'],'memory_wine_crt_image_changed')
        return raw
    fixture=next((r for r in rows if r['path']==value['entrypoints']['fixture_pe']),None)
    need(fixture is not None and fixture.get('machine')==0xaa64
         and fixture.get('classification')=='ordinary_arm64_image'
         and fixture.get('load_admission')=='unperformed' and fixture.get('execution_performed') is False,
         'memory_wine_crt_fixture_image')
    imports=builder.pe_facts(payload(fixture),False)['imports']
    need(imports and 'kernel32.dll' in imports and all(name=='kernel32.dll' or
         re.fullmatch('api-ms-win-crt-[a-z0-9-]+-l1-1-0.dll',name) for name in imports),
         'memory_wine_crt_fixture_imports')
    apisets=apiset_defaults(payload(by_name['apisetschema.dll']))
    mappings=[]
    for name in imports:
        target=name if name=='kernel32.dll' else apisets.get(name)
        need(target==('kernel32.dll' if name=='kernel32.dll' else 'ucrtbase.dll'),
             'memory_wine_crt_default_target')
        mappings.append({'import':name,'default_provider':target})
    built_root=Path(value['build_ref']['path'])
    source=read_relative(built_root,'source/dlls/apisetschema/apisetschema.spec',2*1024**2)
    for row in mappings:
        if row['import']!='kernel32.dll':
            line=('apiset '+row['import'][:-4]+' = '+row['default_provider']).encode()
            need(source.splitlines().count(line)==1,'memory_wine_crt_source_mapping')
    providers=[];delay=None
    for name in required:
        row=by_name[name]
        need(row.get('machine')==0xaa64 and row.get('classification')=='ordinary_arm64_image'
             and row.get('load_admission')=='unperformed' and row.get('execution_performed') is False,
             'memory_wine_crt_provider_selection')
        raw=payload(row)
        if name=='ucrtbase.dll' and BaselinePEMetadata(raw).directory(13)!=(0,0):
            delay=ucrt_delay_closure(runtime,value,by_name,payload)
        else:
            facts=builder.pe_facts(raw,True)
            need(facts['machine']==0xaa64 and facts['delay_imports'] is False,'memory_wine_crt_provider_architecture')
        providers.append({'name':name,'path':row['path'],'sha256':row['sha256'],'size_bytes':row['size_bytes']})
    return {'scope':'finite_fixture_import_module_and_default_apiset_provider_bytes',
        'imports':mappings,'providers':providers,'source_api_spec_sha256':digest_bytes(source),
        'ucrt_delay_import_closure':delay,
        'complete_named_ordinal_forwarder_symbol_resolution':'unperformed','execution':False}


def arena_observations(result,value):
    """Observe source-extended reservation without rewriting old arena evidence."""
    limits=value['baseline_loader_capacity']['limits'];rows=[]
    for role,events in result['events'].items():
        reserves=[row for row in events if row['event']=='arena_reserve']
        executes=any(row['event']=='stage3_pe_continue' for row in events)
        need(len(reserves)==int(executes),'memory_wine_arena_reservation_count')
        for row in reserves:
            base=row.get('mapping_base');interior=row.get('interior_base')
            need(integer(base,1,2**64-1) and integer(interior,1,2**64-1)
                 and base%4096==0 and interior%65536==0 and base<=interior<base+65536
                 and integer(row.get('mapping_bytes'),1588985856,1588985856)
                 and integer(row.get('interior_bytes'),limits['interior_bytes'],limits['interior_bytes'])
                 and integer(row.get('page_bytes'),4096,4096)
                 and integer(row.get('max_slots'),limits['max_slots'],limits['max_slots'])
                 and base+row['mapping_bytes']<2**64,'memory_wine_arena_reservation_geometry')
            rows.append({'role':role,'mapping_bytes':row['mapping_bytes'],'baseline_interior_bytes':row['interior_bytes'],
                'page_bytes':4096,'max_slots':row['max_slots'],'scope':'source_extended_single_mapping_reservation'})
    need(rows,'memory_wine_arena_unobserved')
    # The byte-bound current header asserts this exact supplement geometry;
    # preserved legacy PAGES/TOTAL arrays do not grow with the new VA window.
    header=read_relative(Path(value['build_ref']['path']),'source/dlls/ntdll/unix/pear_pe_arena.h',32768)
    need(header.count(b'_Static_assert(PEAR_ARENA_MAPPING_BYTES == UINT64_C(1588985856)')==1,
         'memory_wine_arena_source_geometry')
    return rows


CASE_FIELDS=('schema_version','record_kind','case','nonce','prefix','outcome','primary_error',
    'stream_error','elapsed_ms','inherited_home','base_environment','loader_environment','events','logs',
    'cleanup','sentinel_cleanup','sentinel_survived','registrations','pre_cleanup','signal_observations',
    'processes','launches','cleanup_errors','ordinary_arm64_pe_execution_performed','passed',*FALSE_FLAGS)


def assess_case(result,raw,runtime,value,helpers,life):
    fields(result,CASE_FIELDS,'fex_memory_wine_case')
    same(result['case'],{'id':'memory-owner','timeout_ms':TIMEOUT_MS,'expected_exit':0},'memory_wine_case_scope')
    need(result['passed'] is False and result['primary_error'] is None and result['stream_error'] is None
         and result['cleanup_errors']==[] and result['outcome']=='exited'
         and result['ordinary_arm64_pe_execution_performed'] is True
         and all(result[key] is False for key in FALSE_FLAGS),'memory_wine_case_failed')
    need(set(result['processes'])=={'loader','server','sentinel'},'memory_wine_process_coverage')
    identities=[row['identity'] for row in result['processes'].values()]
    need(all(type(row) is dict and set(row)=={'pid','ppid','start_sec','start_usec'}
         and all(type(v) is int for v in row.values()) and row['pid']>1 and row['ppid']>1
         and row['start_sec']>0 and 0<=row['start_usec']<1000000 for row in identities)
         and len({row['pid'] for row in identities})==3 and len({row['ppid'] for row in identities})==1,
         'memory_wine_process_identity')
    life.validate_launches(result,runtime,value)
    for role,process in result['processes'].items():
        fields(process,('identity','allowed_paths','exit_code','reaped'))
        path=str((runtime/value['entrypoints'][role]).resolve())
        expected=sorted([path,str((runtime/value['entrypoints']['bootstrap_helper']).resolve())] if role=='loader' else [path])
        need(process['allowed_paths']==expected and process['reaped'] is True and type(process['exit_code']) is int,
             'memory_wine_process_paths_or_exit')
    need(result['processes']['loader']['exit_code']==0,'memory_wine_fixture_exit')
    for name,roles in [('cleanup',{'loader','server'}),('sentinel_cleanup',{'sentinel'})]:
        row=result[name];fields(row,('signals','errors','observation_gap','reaped','complete'))
        need(row['complete'] is True and row['errors']==[] and row['observation_gap'] is False
             and type(row['reaped']) is dict and set(row['reaped'])==roles
             and all(v is True for v in row['reaped'].values()),'memory_wine_cleanup_failed')
        need(type(row['signals']) is list and len(row['signals'])<=6
             and all(type(item) is dict and set(item)=={'role','signal'} and item['role'] in roles
                 and type(item['signal']) is int and item['signal'] in (int(signal.SIGINT),int(signal.SIGTERM),int(signal.SIGKILL))
                 for item in row['signals']),'memory_wine_cleanup_signal')
    need(result['sentinel_survived'] is True and result['sentinel_cleanup']['signals']==[]
         and result['processes']['sentinel']['exit_code']==0,'memory_wine_sentinel_lost')
    sentinel=json_lines(raw[('sentinel','stdout')],2)
    need(len(sentinel)==2 and sentinel[1]=={'version':1,'record_kind':'pear_sentinel_done','signal':0,'command':81},
         'memory_wine_sentinel_output')
    helpers.base.validate_helper(sentinel[0],'pear_sentinel_ready',SimpleNamespace(identity=result['processes']['sentinel']['identity']))
    need(raw[('sentinel','stderr')]==b'','memory_wine_sentinel_diagnostics')
    for role,rows in result['events'].items():
        need(type(rows) is list and all(type(row) is dict and integer(row.get('version'),1,1)
             for row in rows),'memory_wine_event_version')
        same([decode_json(line,32768) for line in raw[(role,'events')].splitlines()],rows,'memory_wine_event_log_changed')
    code=result['processes']['server']['exit_code']
    need(code==0 or code in (-int(signal.SIGINT),-int(signal.SIGTERM),-int(signal.SIGKILL))
         and any(row['role']=='server' and row['signal']==-code for row in result['cleanup']['signals']),
         'memory_wine_server_native_failure')
    need(not any(row['event'] in helpers.api.STAGE4_EVENTS|helpers.api.STAGE5_EVENTS for rows in
         result['events'].values() for row in rows),'memory_wine_unselected_native_control')
    need(not any(row['event'] in ('arena_failure','dynamic_failure') for rows in result['events'].values()
         for row in rows),'memory_wine_source_publication_failure')
    helpers.api.validate_duration(result['elapsed_ms'],TIMEOUT_MS,BOUNDS)
    count=helpers.assess_native(result,runtime,assessment_packet(value))
    need(count>=2,'memory_wine_prefix_initialization_unobserved')
    helpers.api.assess_descendant_exits(result)
    observations=owner_output(raw[('loader','stdout')],SimpleNamespace(identity=result['processes']['loader']['identity']),helpers)
    bitmap,diagnostics=bitmap_output(raw[('loader','stderr')],observations['shared_reservation_count'])
    return {'ordinary_arm64_pe_execution_performed':True,'generated_finite_owned_leaf_execution_performed':True,
        'registered_pe_process_count':count,'memory_owner':observations,'bitmap':bitmap,
        'arena_reservations':arena_observations(result,value),
        'diagnostics':{'loader_stderr':{'sha256':digest_bytes(diagnostics),'size_bytes':len(diagnostics),
                      'review':'unperformed'},'server_stderr':{'sha256':digest_bytes(raw[('server','stderr')]),
                      'size_bytes':len(raw[('server','stderr')]),'review':'unperformed'}},**dict.fromkeys(FALSE_FLAGS,False)}


def failure_detail(exc,default='memory_wine_run_failed'):
    value={'code':getattr(exc,'code',default),'exception_type':type(exc).__name__}
    if isinstance(exc,OSError):value['native_error']={'domain':'errno','code':exc.errno}
    elif isinstance(getattr(exc,'native_error',None),dict):value['native_error']=dict(exc.native_error)
    for field in ('observed_primary','observed_source_failures','failure_record_error'):
        if hasattr(exc,field):value[field]=getattr(exc,field)
    return value


def source_failures(stdout,stderr):
    """Keep actual unexpected source errors distinct from assessment/cleanup.

    A malformed log is preserved raw and reported as parse-unavailable; no
    invented owner failure, success, native errno or allocation identity appears.
    """
    result={'observations':[],'parse_error':None,
        'bitmap_diagnostics':bitmap_policy.observe_failed_prefix(stderr)}
    try:
        counted,refusals,_=suite_contract()
        for row in json_lines(stdout):
            if row.get('event') in ('failed_control','failure'):
                result['observations'].append(row)
            elif row.get('event') in ('readiness_call','owner_call'):
                wanted=3 if row.get('control')=='mixed_extent_query_unavailable' else refusals.get(row.get('control'),0)
                if row.get('status')!=wanted:result['observations'].append(row)
            elif row.get('event')=='suite_complete' and row.get('passed') is not True:
                result['observations'].append(row)
            elif row.get('event')=='finish' and row.get('exit_code')!=0:
                result['observations'].append(row)
    except Exception as exc:result['parse_error']=failure_detail(exc,'memory_wine_failure_parse_unavailable')
    try:
        for line in stderr.splitlines():
            if line.startswith(b'PEAR_FEX_BITMAP '):
                row=decode_json(line[len(b'PEAR_FEX_BITMAP '):],2048)
                if row.get('error_domain') or row.get('error_code') or row.get('restoration_observed') is not True:
                    result['observations'].append({'record_kind':'pear_fex_bitmap_failure',**row})
            elif line.startswith(b'{') and b'pear_fex_memory_launch_failure' in line:
                result['observations'].append(decode_json(line,32768))
    except Exception as exc:
        detail=failure_detail(exc,'memory_wine_stderr_parse_unavailable')
        if result['parse_error'] is None:result['parse_error']=detail
        else:result['secondary_parse_error']=detail
    return result


def require_no_source_failure(value):
    """Assessment only: complete source/raw-stream qualification happens first.

    The prefix observation object never qualifies a count or runtime. Its
    parser refusal blocks the assessment without changing the primary error.
    """
    fields(value,('observations','parse_error','bitmap_diagnostics'))
    diagnostic=value['bitmap_diagnostics']
    fields(diagnostic,('scope','completed_count_qualified','observations','parse_error'))
    need(value['observations']==[] and value['parse_error'] is None
         and diagnostic['scope']=='partial_bitmap_diagnostics'
         and diagnostic['completed_count_qualified'] is False
         and type(diagnostic['observations']) is list
         and diagnostic['parse_error'] is None,'memory_wine_source_failed')


def install_spawn_capture(helpers):
    """Record genuine Popen OSError before the immutable launch converts it.

    The proxy changes only this captured/restored run_fixtures namespace. It
    delegates identical arguments once and never retries or alters subprocess.
    """
    original=helpers.base.subprocess
    captured=[]
    def popen(*args,**kwargs):
        try:return original.Popen(*args,**kwargs)
        except OSError as exc:
            captured.append({'domain':'errno','code':exc.errno,'exception_type':type(exc).__name__})
            raise
    namespace=dict(vars(original));namespace['Popen']=popen
    helpers.base.subprocess=SimpleNamespace(**namespace)
    return captured,original


def write_case_record(path,value,primary=None,source_observations=None):
    try:return write_json(path,value)
    except BaseException as recording:
        if primary is None:
            if source_observations is not None:recording.observed_source_failures=source_observations
            raise
        # Preserve the actual earlier operation; record storage failed afterward.
        error=Error(primary['code']);error.observed_primary=primary
        error.failure_record_error=failure_detail(recording,'memory_wine_case_record_write')
        if source_observations is not None:error.observed_source_failures=source_observations
        raise error from recording


def run_case(runtime,value,output,helpers,life):
    for path in (output/'prefix',output/'work',output/'work/tmp'):path.mkdir(mode=0o700)
    prefix=output/'prefix';prefix_info=helpers.base.prefix_identity(prefix)
    nonce=uuid.uuid4().hex;home=os.environ.get('HOME')
    env=environment(output/'work',prefix,nonce,home)
    paths={key:runtime.joinpath(*relative(path)) for key,path in value['entrypoints'].items()}
    start=time.monotonic();deadline=start+TIMEOUT_MS/1000
    remaining=lambda cap:max(0,min(cap,deadline-time.monotonic()))
    session=helpers.api.APISession(output,runtime,assessment_packet(value),nonce,suite='api-abi',case_id='memory-owner')
    spawn_errors,original_process=install_spawn_capture(helpers)
    read_fd,control=None,None;primary,outcome=None,'not_started';loader_env=None;launches=[]
    def launch(role,argv,selected_env,**kwargs):
        row={'role':role,'argv':argv,'environment':dict(selected_env),'pid':None,'started':None};launches.append(row)
        child=session.launch(role,argv,selected_env,**kwargs)
        row.update({'pid':child.pid,'started':True});return child
    try:
        read_fd,control=os.pipe()
        sentinel=launch('sentinel',[str(paths['sentinel']),str(read_fd)],env,pass_fds=(read_fd,))
        os.close(read_fd);read_fd=None
        need(session.wait_for(lambda:b'\n' in session.streams[('sentinel','stdout')]['data'],remaining(5)),
             'memory_wine_sentinel_start')
        helpers.base.validate_helper(helpers.base.parse_lines(session,'sentinel')[0],'pear_sentinel_ready',sentinel)
        server=launch('server',[str(paths['server']),'-f','-p'],env,event_pipe=True)
        need(session.wait_for(lambda:any(row.get('event')=='server_ready' for row in session.events['server'])
             or server.exited,remaining(30)) and not server.exited,'memory_wine_server_start')
        loader_env=loader_environment(env,session.endpoint,server.pid,nonce)
        session.output=output/'work'
        try:
            loader=launch('loader',[str(paths['bootstrap_helper']),'--exec-4k',str(paths['loader']),str(paths['fixture_pe'])],
                loader_env,allowed_paths=[paths['bootstrap_helper'],paths['loader']])
        finally:session.output=output
        outcome='exited' if session.wait_for(lambda:loader.exited,remaining(TIMEOUT_MS/1000)) else 'timeout'
        if outcome=='timeout':primary={'code':'memory_wine_execution_timeout','exception_type':'Timeout'}
    except KeyboardInterrupt as exc:primary,outcome=failure_detail(exc,'memory_wine_interrupted'),'interrupted'
    except Exception as exc:primary,outcome=failure_detail(exc),'error'
    finally:
        try:
            before,cleanup,sentinel_cleanup,logs,survived,cleanup_errors=life.cleanup_session(session,control,read_fd,output)
        finally:helpers.base.subprocess=original_process
    if spawn_errors:
        if primary is None:primary={'code':'memory_wine_unclassified_spawn_failure','exception_type':'ObservedSpawnFailure'}
        primary['spawn_errors']=spawn_errors
    executed=False
    # stage3_pe_continue occurs before PE load and cannot establish execution.
    # A finite source fixture output proves its ordinary ARM64 main ran; full
    # native/source/image admission and completion remain separate assessment.
    try:
        for line in bytes(session.streams.get(('loader','stdout'),{}).get('data',b'')).splitlines():
            row=decode_json(line,32768)
            if (type(row) is dict and integer(row.get('version'),1,1) and row.get('record_kind')=='pear_fex_memory_wine'
                and row.get('event') in ('readiness_call','finish')):
                executed=True
    except Exception:
        pass  # A malformed/truncated source stream remains unavailable.

    result={'schema_version':1,'record_kind':'fex_memory_wine_case',
        'case':{'id':'memory-owner','timeout_ms':TIMEOUT_MS,'expected_exit':0},'nonce':nonce,'prefix':prefix_info,
        'outcome':outcome,'primary_error':primary,'stream_error':session.failure,
        'elapsed_ms':round((time.monotonic()-start)*1000),'inherited_home':home,'base_environment':env,
        'loader_environment':loader_env,'events':session.events,'logs':logs,'cleanup':cleanup,
        'sentinel_cleanup':sentinel_cleanup,'sentinel_survived':survived,'registrations':list(session.observer.registrations.values()),
        'pre_cleanup':before,'signal_observations':session.observer.signal_observations,'launches':launches,
        'cleanup_errors':cleanup_errors,'processes':{role:{'identity':child.identity,'allowed_paths':sorted(child.allowed_paths),
        'exit_code':child.exit_code,'reaped':child.reaped} for role,child in session.children.items()},
        'ordinary_arm64_pe_execution_performed':True if executed else (None if any(row['role']=='loader' for row in launches) else False),
        'passed':False,**dict.fromkeys(FALSE_FLAGS,False)}
    write_case_record(output/'case.json',result,primary)
    failures={'observations':[],'parse_error':None}
    try:
        failures=source_failures(read_relative(output,'loader.stdout.log',STREAM_LIMIT),
                                 read_relative(output,'loader.stderr.log',STREAM_LIMIT))
    except Exception as exc:failures['parse_error']=failure_detail(exc,'memory_wine_failure_parse_unavailable')
    write_case_record(output/'source-failures.json',failures,primary,failures)
    try:
        actual=assess_case(result,verify_logs(output,result),runtime,value,helpers,life)
        require_no_source_failure(failures)
    except Exception as exc:
        write_case_record(output/'assessment.json',{'passed':False,'primary_error':primary,
            'assessment_error':failure_detail(exc),'source_failures_ref':{'path':'source-failures.json',
            'sha256':sha256(output/'source-failures.json')},'cleanup_errors':cleanup_errors},
            primary or failure_detail(exc),failures)
        raise Error(primary['code'] if primary else getattr(exc,'code','memory_wine_assessment_failed')) from exc
    write_case_record(output/'assessment.json',{'passed':True,'error':None,'observations':actual})
    return actual


def snapshot(root,record,repo):
    for path,expected in record.items():
        raw=read_relative(repo,path);need(digest_bytes(raw)==expected,'memory_wine_producer_changed')
        target=root/'producers'/path;target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        with target.open('xb') as stream:stream.write(raw)
    same(record,producers(repo),'memory_wine_producer_changed')


def run(runtime_root,output,supervisor_reuse_root,repo=REPO):
    runtime_root=operation_output(runtime_root,repo_root=repo,require_empty=False,create=False)
    root=operation_output(output,repo_root=repo,require_empty=True)
    base={'schema_version':1,'record_kind':'fex_memory_wine_run','scope':SCOPE,
        'runtime_ref':{'path':str(runtime_root),'sha256':None},
        'admission_ref':None,'supervision_reuse':{'root':str(Path(supervisor_reuse_root).absolute()),
        'path':REUSE_PATH,'sha256':REUSE_SHA,'selected_functions':list(REUSE_FUNCTIONS),
        'scope':'owned_process_supervision_and_cleanup_only'},'producers':{},'bounds':BOUNDS,
        'timeout_ms':TIMEOUT_MS,'stream_limit_bytes':STREAM_LIMIT,'passed':False,**dict.fromkeys(FALSE_FLAGS,False)}
    phase='preparation'
    try:
        base['runtime_ref']['sha256']=sha256(runtime_root/'runtime.json')
        supervisor_reuse_root=builder.real_directory(supervisor_reuse_root)
        raw=read_relative(Path(supervisor_reuse_root),REUSE_PATH,2*1024**2)
        need(digest_bytes(raw)==REUSE_SHA,'memory_wine_supervisor_pin')
        path=root/'inputs/run_pairing.py';path.parent.mkdir(mode=0o700)
        with path.open('xb') as stream:stream.write(raw)
        base['producers']=producers(repo);snapshot(root,base['producers'],repo)
        phase='current_apple_admission'
        value,admission_root=materializer.admit_runtime(runtime_root,repo=repo)
        base['admission_ref']={'path':str(admission_root),'sha256':sha256(admission_root/'admission.json')}
        phase='crt_provider_closure';base['crt_closure']=crt_closure(runtime_root,value)
        phase='finite_ordinary_pe_execution'
        with supervision(supervisor_reuse_root,repo,base['producers']) as (life,helpers):
            observations=run_case(runtime_root,value,root,helpers,life)
        phase='post_execution_pure_replay'
        materializer.verify_admission(runtime_root,admission_root,repo=repo)
        repeated,_,_=materializer.verify_structural(runtime_root,repo=repo)
        same(repeated,value,'memory_wine_runtime_changed');same(base['producers'],producers(repo),'memory_wine_producer_changed')
        same(base['crt_closure'],crt_closure(runtime_root,value),'memory_wine_crt_closure_changed')
        base.update({'passed':True,'case_ref':{'path':'case.json','sha256':sha256(root/'case.json')},
            'assessment_ref':{'path':'assessment.json','sha256':sha256(root/'assessment.json')},
            'source_failures_ref':{'path':'source-failures.json','sha256':sha256(root/'source-failures.json')},
            'ordinary_arm64_pe_execution_performed':True,'generated_finite_owned_leaf_execution_performed':True,
            'diagnostics_review':'unperformed'})
        write_json(root/'run.json',base)
        same(verify_run(root,repo),observations,'memory_wine_final_replay')
        return base
    except BaseException as exc:
        try:
            write_json(root/'failure.json',{'schema_version':1,'record_kind':'fex_memory_wine_run_failure',
                'scope':SCOPE,'phase':phase,'primary_error':failure_detail(exc),
                'runtime_ref':base['runtime_ref'],'admission_ref':base['admission_ref'],
                'producers':base['producers'],'passed':False,**dict.fromkeys(FALSE_FLAGS,False)})
        except BaseException as recording_error:
            # A disk/write failure must not replace the actual primary operation.
            latest=failure_detail(recording_error,'memory_wine_failure_record_write')
            if hasattr(exc,'failure_record_error'):
                exc.failure_record_error={'first':exc.failure_record_error,'final_failure_record':latest}
            else:exc.failure_record_error=latest
        raise


def verify_run(output,repo=REPO):
    """Pure replay: no Apple command, process observer construction or execution."""
    root=operation_output(output,repo_root=repo,require_empty=False,create=False)
    need(not (root/'failure.json').exists(),'memory_wine_failed_run')
    record=load_json(root/'run.json')
    fields(record,('schema_version','record_kind','scope','runtime_ref','admission_ref','supervision_reuse',
        'producers','bounds','timeout_ms','stream_limit_bytes','passed','crt_closure','case_ref','assessment_ref',
        'source_failures_ref','ordinary_arm64_pe_execution_performed','generated_finite_owned_leaf_execution_performed',
        'diagnostics_review',*FALSE_FLAGS),'fex_memory_wine_run')
    need(record['scope']==SCOPE and record['passed'] is True and record['ordinary_arm64_pe_execution_performed'] is True
         and record['generated_finite_owned_leaf_execution_performed'] is True and record['diagnostics_review']=='unperformed'
         and all(record[k] is False for k in FALSE_FLAGS),'memory_wine_run_scope')
    same(record['bounds'],BOUNDS,'memory_wine_run_bounds')
    need(integer(record['timeout_ms'],TIMEOUT_MS,TIMEOUT_MS) and integer(record['stream_limit_bytes'],STREAM_LIMIT,STREAM_LIMIT),
         'memory_wine_run_bounds')
    same(record['producers'],producers(repo),'memory_wine_producers_changed')
    for path,digest in record['producers'].items():
        need(digest_bytes(read_relative(root,'producers/'+path))==digest,'memory_wine_producer_snapshot_changed')
    fields(record['supervision_reuse'],('root','path','sha256','selected_functions','scope'))
    reuse_root=builder.real_directory(record['supervision_reuse']['root'])
    same(record['supervision_reuse'],{'root':str(reuse_root),'path':REUSE_PATH,'sha256':REUSE_SHA,
        'selected_functions':list(REUSE_FUNCTIONS),'scope':'owned_process_supervision_and_cleanup_only'},
        'memory_wine_supervisor_scope')
    need(digest_bytes(read_relative(root,'inputs/run_pairing.py'))==REUSE_SHA,'memory_wine_supervisor_snapshot_changed')
    fields(record['runtime_ref'],('path','sha256'));fields(record['admission_ref'],('path','sha256'))
    runtime=operation_output(record['runtime_ref']['path'],repo_root=repo,require_empty=False,create=False)
    need(sha256(runtime/'runtime.json')==record['runtime_ref']['sha256'],'memory_wine_runtime_ref_changed')
    admission=Path(record['admission_ref']['path'])
    materializer.verify_admission(runtime,admission,repo=repo)
    need(sha256(admission/'admission.json')==record['admission_ref']['sha256'],'memory_wine_admission_changed')
    value,_,_=materializer.verify_structural(runtime,repo=repo)
    same(record['crt_closure'],crt_closure(runtime,value),'memory_wine_crt_closure_changed')
    for key,path in (('case_ref','case.json'),('assessment_ref','assessment.json'),('source_failures_ref','source-failures.json')):
        fields(record[key],('path','sha256'))
        need(record[key]['path']==path and sha256(root/path)==record[key]['sha256'],'memory_wine_receipt_changed')
    result=decode_json(read_relative(root,'case.json',16*1024**2),16*1024**2,max_nodes=1000000)
    fields(result,CASE_FIELDS,'fex_memory_wine_case')
    info=builder.real_directory(root/'prefix').stat();fields(result['prefix'],('device','inode','namespace'))
    namespace=str(Path('/private/tmp')/('.wine-'+str(os.getuid()))/f'server-{info.st_dev:x}-{info.st_ino:x}')
    same(result['prefix'],{'device':info.st_dev,'inode':info.st_ino,'namespace':namespace},'memory_wine_prefix_changed')
    env=environment(root/'work',root/'prefix',result['nonce'],result['inherited_home'])
    need(result['inherited_home']==os.environ.get('HOME'),'memory_wine_inherited_home_changed')
    same(result['base_environment'],env,'memory_wine_environment_changed')
    need(type(result['loader_environment']) is dict,'memory_wine_loader_environment')
    same(result['loader_environment'],loader_environment(env,result['loader_environment'].get('PEAR_STAGE3_CONTROL',''),
        result['processes']['server']['identity']['pid'],result['nonce']),'memory_wine_loader_environment_changed')
    with supervision(reuse_root,repo,record['producers']) as (life,helpers):
        raw=verify_logs(root,result)
        actual=assess_case(result,raw,runtime,value,helpers,life)
    failure=source_failures(raw[('loader','stdout')],raw[('loader','stderr')])
    require_no_source_failure(failure)
    same(load_json(root/'source-failures.json'),failure,'memory_wine_source_failure_changed')
    same(load_json(root/'assessment.json'),{'passed':True,'error':None,'observations':actual},'memory_wine_assessment_changed')
    return actual


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime');parser.add_argument('--output',required=True)
    parser.add_argument('--supervisor-reuse-root');parser.add_argument('--require-empty',action='store_true')
    parser.add_argument('--verify',action='store_true');args=parser.parse_args(argv)
    try:
        if args.verify:
            need(args.runtime is None and args.supervisor_reuse_root is None and not args.require_empty,'memory_wine_verify_arguments')
            value=verify_run(args.output)
        else:
            need(args.runtime is not None and args.supervisor_reuse_root is not None and args.require_empty,'memory_wine_run_arguments')
            value=run(args.runtime,args.output,args.supervisor_reuse_root)
        print(encoded({'passed':True,'ordinary_arm64_pe_execution_performed':True,'fex_initialization':False,
            'hybrid_execution':False,'runtime_eligible':False,'stage3_complete':False}).decode(),end='');return 0
    except (Error,OSError,ValueError,KeyError,TypeError,KeyboardInterrupt) as exc:
        print(encoded({'passed':False,'error':failure_detail(exc),'runtime_eligible':False,'stage3_complete':False}).decode(),end='')
        return 1


if __name__=='__main__':raise SystemExit(main())
