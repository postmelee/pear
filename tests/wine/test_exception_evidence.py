"""Synthetic Stage 4 observation rejection tests; no real Wine or signal execution.

Only fixture_facts is mocked. Values encode the original fixture's public
constants and finite flow, while field lists select the declared wire shape.
Linked-byte/section and actual native-process checks require separate tests.
"""
import copy
from pathlib import Path
import signal
import struct
import sys
import unittest
from unittest.mock import patch

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'tools/wine/common.py').is_file())
sys.path.insert(0,str(ROOT/'tools/wine'))
import exception_evidence as e
from common import Error

BASE=0x180000000
NATIVE=0x200000000
MAIN_TEB=0x300000000
TEBS=(0x300010000,0x300020000)
REGION=0x500000000
ORDINARY=0x500010000
DYNAMIC=0x500020000
CHILD_REGION=0x600000000
CHILD_TEB=0x700000000
ACCESS=0xc0000005


def facts():
    return {'rvas':{'pear_guest_spin_begin':0x1000,'pear_guest_spin_end':0x1008,
            'pear_fault_read_pc':0x1100,'pear_fault_read_recovery':0x1104,
            'pear_fault_write_pc':0x1200,'pear_fault_write_recovery':0x1204,'PearDynamicCall':0x1300},
            'image_size':0x10000,'original_base':0x140000000,'native_offsets':[0x2000,0x2010],
            'fixture_sha256':'a'*64,'native_sha256':'b'*64}


def row(record_kind,**fields):
    return {'version':1,'record_kind':record_kind,**dict.fromkeys(e.FIELDS[record_kind],0),**fields}


def fault(kind,sequence,target,*,fatal=False):
    software=kind==1
    operation=int(kind==3)
    pc=BASE+(0x1200 if operation else 0x1100)
    code=0xe0424401 if software else 0x80000001 if kind==4 else ACCESS
    return row('pear_stage4_child_fault' if fatal else 'pear_exception_event',sequence=sequence,
        kind=kind,expected_code=code,operation=operation,address=0 if software else target,
        fault_pc=0 if software else pc,recovery_pc=0 if software else pc+4,
        teb=CHILD_TEB if fatal else MAIN_TEB,first_count=1,second_count=1,order=12,
        code=code,fault_address=0 if software else target,context_pc=BASE+0x1400 if software else pc,
        access_kind=operation,context_x18=CHILD_TEB if fatal else MAIN_TEB,context_x19=0 if software else 0x3456789a,
        context_sp=0x400010000,exception_pc=BASE+0x1400 if software else pc,continued=int(not fatal),
        context_x0=0 if software else target,context_flags=0x20400007 if software else 0x400017,exception_flags=0,
        parameters=0 if software else 2,module_base=BASE)


def baseline_rows():
    result=[]
    for slot,phase in ((0,1),(1,2),(0,3)):
        guest=phase!=2;pc=BASE+0x1000 if guest else NATIVE+0x2004
        result.append(row('pear_signal_event',slot=slot,phase=phase,module_base=BASE,teb=TEBS[slot],
            native_tid=201+slot,ntdll_base=NATIVE,guest_begin=BASE+0x1000,guest_end=BASE+0x1008,
            host_begin=NATIVE+0x2000,host_end=NATIVE+0x2010,before_count=1,after_count=1,
            signal=int(signal.SIGUSR1),entry_mode=int(guest),handler_mode=0,return_mode=int(guest),
            before_pc=pc,after_pc=pc,before_x18=TEBS[slot] if guest else 0,
            after_x18=TEBS[slot] if guest else 0,before_x19=0x3456789a+slot if guest else 0,
            after_x19=0x3456789a+slot if guest else 0,before_sp=0x400001000,after_sp=0x400001000))
    result.append(row('pear_suspend_result',slot=0,suspend_previous=0,resume_previous=1,context_ok=1,
        context_flags=0x400017,context_pc=BASE+0x1000,context_sp=0x400001000,context_x18=TEBS[0],
        context_x19=0x3456789a,stack_low=0x400000000,stack_high=0x400010000,passed=1))
    for slot in (0,1):
        result.append(row('pear_thread_event',slot=slot,teb=TEBS[slot],tid=201+slot,tls_value=0x7300+slot,
            checks=5 if slot==0 else 4,registered=1,init_seen=1,init_tls_matches=1,
            native_tid=201+slot,native_teb=TEBS[slot],native_exit_seen=1))
    result.extend([fault(1,1,0),row('pear_exception_region',base=REGION,size=4096,offset=37),
        fault(2,2,REGION+37),row('pear_exception_cleanup',released=1,operation_error=0),row('pear_memory_region',base=ORDINARY,size=12288,page_bytes=4096,
        middle_offset=4096,allocation_protect=1),fault(3,3,ORDINARY+4096),
        fault(4,4,ORDINARY+4096),fault(2,5,ORDINARY+4096)])
    for ordinal,value,word in ((1,42,0x52800540),(2,84,0x52800a80)):
        hashed=14695981039346656037
        for byte in struct.pack('<II',word,0xd65f03c0):hashed=((hashed^byte)*1099511628211)&(2**64-1)
        result.append(row('pear_dynamic_call',ordinal=ordinal,base=DYNAMIC,bytes=8,word0=word,
                          word1=0xd65f03c0,hash=hashed,value=value))
    result.append(row('pear_memory_result',error_step=0,error_code=0,queries=22,sentinel_checks=4,
        zero_bytes=28672,access_faults=2,guard_faults=1,ordinary_commits=2,ordinary_protects=3,
        ordinary_decommits=1,ordinary_releases=1,dynamic_reserves=2,dynamic_commits=3,dynamic_protects=3,
        dynamic_decommits=1,dynamic_releases=2,flushes=2,code_calls=2,first_value=42,second_value=84,
        reuse_checks=1,negative_controls=3))
    result.append(row('pear_stage4_child_ready',guest_pid=300,native_pid=124,teb=CHILD_TEB,
        module_base=BASE,fault_pc=BASE+0x1100,recovery_pc=BASE+0x1104,address=CHILD_REGION+53,
        expected_code=ACCESS,region_base=CHILD_REGION,region_size=4096,region_offset=53))
    result.append(fault(5,1,CHILD_REGION+53,fatal=True))
    result.append(row('pear_stage4_child_result',guest_pid=300,exit_code=ACCESS,wait_result=0,
        exit_query=1,thread_closed=1,process_closed=1,expected_code=ACCESS))
    result.append(row('pear_stage4_result',passed=1,error_step=0,win32_error=0,workers=2,signals=2,
        suspends=1,injected_errors=2,workers_cleaned=1,exceptions_status=0,memory_status=0,
        handlers_removed=1,child_passed=1,module_base=BASE,main_teb=MAIN_TEB,native_pid=123))
    return result



def native_anchors():
    """Encode the native producer's independently fixed 4/8-part schema."""
    base={'version':1,'role':'loader','nonce':'a'*32,'pid':123,'ppid':12,
          'generation':1,'start_sec':1,'start_usec':2,'identity_error':0}
    anchors=[]
    register_parts=(('teb','native_tid','ntdll_base'),('guest_begin','guest_end','host_begin'),
                    ('host_end','init_seen','init_host_mode'),('init_tls_matches',))
    signal_parts=(('teb','native_tid','ntdll_base'),('guest_begin','guest_end','host_begin'),
                  ('host_end','before_count','after_count'),('signal','entry_mode','handler_mode'),
                  ('return_mode','before_pc','after_pc'),('before_x18','after_x18','before_x19'),
                  ('after_x19','before_sp','after_sp'),('error',))
    for slot in (0,1):
        values={'teb':TEBS[slot],'native_tid':201+slot,'ntdll_base':NATIVE,
                'guest_begin':BASE+0x1000,'guest_end':BASE+0x1008,
                'host_begin':NATIVE+0x2000,'host_end':NATIVE+0x2010,
                'init_seen':1,'init_host_mode':0,'init_tls_matches':1}
        for part,names in enumerate(register_parts):
            anchors.append({**base,'event':'stage4_thread_register','slot':slot,'part':part,
                            **{name:values[name] for name in names}})
    # Independent baseline creation keeps later PE-row mutations from changing
    # native observations and proves the cross-stream comparison is effective.
    for captured in (r for r in baseline_rows() if r['record_kind']=='pear_signal_event'):
        for part,names in enumerate(signal_parts):
            anchors.append({**base,'event':'stage4_signal','slot':captured['slot'],
                            'phase':captured['phase'],'part':part,
                            **{name:captured[name] for name in names}})
    for slot in (0,1):
        anchors.append({**base,'event':'stage4_thread_exit','slot':slot,'teb':TEBS[slot],
                        'native_tid':201+slot,'exit_mode':0})
    return anchors

def result():
    publication={'event':'arena_publish','base':BASE,'size':0x10000,'original_base':0x140000000}
    owners=[{'event':'dynamic_budget'}]
    def reserve(generation):
        owners.append({'event':'dynamic_reserve','slot':0,'slot_generation':generation,'base':DYNAMIC,'size':4096})
    def protection(generation,operation,vprot):
        owners.append({'event':'dynamic_protect','slot':0,'slot_generation':generation,'operation':operation,
                       'vprot':vprot,'offset':0,'size':4096})
    def decommit(generation):
        owners.append({'event':'dynamic_decommit','slot':0,'slot_generation':generation,'offset':0,'size':4096})
    def release(generation):
        owners.append({'event':'dynamic_release','slot':0,'slot_generation':generation,'base':DYNAMIC,'size':4096})
    reserve(1);protection(1,'commit',35);protection(1,'protect',37);protection(1,'protect',35)
    protection(1,'protect',37);decommit(1);protection(1,'commit',35);decommit(1);release(1)
    reserve(2);protection(2,'commit',35);decommit(2);release(2)
    return {'case':{'id':'threads'},'processes':{'loader':{'identity':{'pid':123}}},
            'events':{'loader':[copy.deepcopy(publication),{'event':'stage3_pe_continue'},*native_anchors(),*owners],
                      'child-1':[copy.deepcopy(publication),{'event':'stage3_process_exit','exit_code':ACCESS-2**32}]},
            'registrations':[{'role':'loader','identity':{'pid':123}},
                             {'role':'child-1','identity':{'pid':124},'exit_code':5}],
            'pre_cleanup':{'processes':{'child-1':{'exited':True}}}}


def dynamic():
    return {'root':{'reservations':2,'commits':3,'protects':3,'decommits':3,'releases':2,
            'compatible_reuses':1,'committed_pages':3,'decommitted_pages':3,
            'executable_publications':2,'writable_transitions':4,'live_allocations_at_last_observation':0}}


def select(rows,kind,index=0):return [r for r in rows if r['record_kind']==kind][index]


class ExceptionEvidenceTests(unittest.TestCase):
    def assess(self,rows=None,observed=None,owner=None):
        with patch.object(e,'fixture_facts',return_value=facts()):
            return e.assess(baseline_rows() if rows is None else rows,
                result() if observed is None else observed,Path('/synthetic-runtime'),{},
                dynamic() if owner is None else owner)

    def test_complete_semantic_baseline_and_public_scope(self):
        summary,allowed=self.assess()
        self.assertEqual(summary['workers'],2)
        self.assertEqual(summary['controlled_windows_exit'],ACCESS)
        self.assertEqual(allowed,{'child-1':{'native_exit':5,'windows_exit':ACCESS,'native_reported_status':ACCESS-2**32}})
        for name in ('main_teb','native_pid','module_base','fault_pc','context_sp'):
            self.assertNotIn("'"+name+"':",repr(summary))

    def test_numeric_boolean_cannot_forge_success(self):
        for kind,key in [('pear_stage4_result','passed'),('pear_thread_event','registered'),
                         ('pear_signal_event','before_count'),('pear_stage4_child_result','exit_query')]:
            rows=baseline_rows();select(rows,kind)[key]=True
            with self.subTest(kind=kind),self.assertRaises(Error):self.assess(rows)

    def test_missing_duplicate_or_unexpected_record_rejected(self):
        original=baseline_rows()
        for index in range(len(original)):
            rows=copy.deepcopy(original);rows.pop(index)
            with self.subTest(index=index),self.assertRaises(Error):self.assess(rows)
        rows=baseline_rows();rows[0]=copy.deepcopy(rows[1])
        with self.assertRaises(Error):self.assess(rows)
        rows=baseline_rows();rows[0]['unknown']=0
        with self.assertRaises(Error):self.assess(rows)

    def test_fault_pc_and_recovery_bind_actual_export_rvas(self):
        for field in ('fault_pc','recovery_pc','context_pc','exception_pc'):
            rows=baseline_rows();select(rows,'pear_exception_event',1)[field]+=4
            with self.subTest(field=field),self.assertRaises(Error):self.assess(rows)
        rows=baseline_rows();item=select(rows,'pear_exception_event',1)
        for key in ('fault_pc','context_pc','exception_pc','recovery_pc'):item[key]+=16
        with self.assertRaises(Error):self.assess(rows)

    def test_region_offsets_and_access_type_cannot_move(self):
        for kind,key,value in [('pear_exception_region','offset',38),('pear_memory_region','middle_offset',0),
                               ('pear_stage4_child_ready','region_size',8192),('pear_stage4_child_ready','region_offset',54)]:
            rows=baseline_rows();select(rows,kind)[key]=value
            with self.subTest(kind=kind,key=key),self.assertRaises(Error):self.assess(rows)
        for key in ('address','fault_address','context_x0','access_kind'):
            rows=baseline_rows();select(rows,'pear_exception_event',2)[key]+=1
            with self.subTest(key=key),self.assertRaises(Error):self.assess(rows)

    def test_context_marker_and_required_flags_are_checked(self):
        for key,value in [('context_x18',MAIN_TEB+16),('context_x19',0),('context_sp',0x400010001),
                          ('context_flags',0x400007),('exception_flags',1),('parameters',1),('continued',0)]:
            rows=baseline_rows();select(rows,'pear_exception_event',1)[key]=value
            with self.subTest(key=key),self.assertRaises(Error):self.assess(rows)

    def test_handler_order_is_observed_not_just_final_success(self):
        for key,value in [('first_count',2),('second_count',0),('order',21),('code',0),('expected_code',0),('error',1)]:
            rows=baseline_rows();select(rows,'pear_exception_event',1)[key]=value
            with self.subTest(key=key),self.assertRaises(Error):self.assess(rows)

    def test_software_raise_context_accepts_callee_nonvolatile_register(self):
        for captured_x19 in (0, 0x123456789abcdef0):
            rows=baseline_rows();software=select(rows,'pear_exception_event')
            software['context_x19']=captured_x19
            software['context_flags']=0x20400007
            with self.subTest(captured_x19=captured_x19):
                summary,_=self.assess(rows)
                self.assertEqual(summary['software_exceptions'],1)

    def test_software_raise_must_preserve_its_matching_caller_pcs(self):
        for field in ('context_pc','exception_pc'):
            rows=baseline_rows();select(rows,'pear_exception_event')[field]+=4
            with self.subTest(field=field),self.assertRaisesRegex(Error,'stage4_software_exception_context'):
                self.assess(rows)

    def test_software_raise_requires_source_correct_context_flags(self):
        for flags in (0x400007, 0x20400017, 0x2040000f, (1<<63)|0x20400007):
            rows=baseline_rows();select(rows,'pear_exception_event')['context_flags']=flags
            with self.subTest(flags=flags),self.assertRaisesRegex(Error,'stage4_software_exception_context'):
                self.assess(rows)

    def test_owned_region_lifetime_order_cannot_be_rearranged(self):
        # Each adjacent swap preserves counts, addresses and fault sequence
        # fields while violating a real allocation/fault/cleanup dependency.
        lifetime=(('pear_exception_event',0),('pear_exception_region',0),
                  ('pear_exception_event',1),('pear_exception_cleanup',0),
                  ('pear_memory_region',0),('pear_exception_event',2),
                  ('pear_exception_event',3),('pear_exception_event',4),('pear_memory_result',0))
        for before,after in zip(lifetime,lifetime[1:]):
            rows=baseline_rows()
            left=rows.index(select(rows,*before));right=rows.index(select(rows,*after))
            rows[left],rows[right]=rows[right],rows[left]
            with self.subTest(before=before,after=after),self.assertRaises(Error):
                self.assess(rows)

    def test_controlled_child_record_order_requires_actual_fault_before_result(self):
        lifecycle=('pear_memory_result','pear_stage4_child_ready',
                   'pear_stage4_child_fault','pear_stage4_child_result')
        for before,after in zip(lifecycle,lifecycle[1:]):
            rows=baseline_rows()
            left=rows.index(select(rows,before));right=rows.index(select(rows,after))
            rows[left],rows[right]=rows[right],rows[left]
            with self.subTest(before=before,after=after),self.assertRaisesRegex(Error,'stage4_child_record_order'):
                self.assess(rows)

    def test_worker_teb_tid_and_native_start_exit_are_distinct(self):
        for key,value in [('teb',TEBS[0]),('tid',201),('native_teb',TEBS[0]),('native_tid',201),
                          ('native_exit_seen',0),('native_exit_mode',1),('init_host_mode',1),('init_tls_matches',0)]:
            rows=baseline_rows();select(rows,'pear_thread_event',1)[key]=value
            with self.subTest(key=key),self.assertRaises(Error):self.assess(rows)

    def test_signal_boundaries_and_preserved_context_are_required(self):
        for key,value in [('guest_begin',BASE+0x1004),('host_begin',NATIVE+0x2004),
                          ('before_pc',NATIVE+0x2010),('after_pc',NATIVE+0x2008),('before_count',2),
                          ('handler_mode',1),('entry_mode',1),('return_mode',1),('send_status',1)]:
            rows=baseline_rows();select(rows,'pear_signal_event',1)[key]=value
            with self.subTest(key=key),self.assertRaises(Error):self.assess(rows)
        rows=baseline_rows();select(rows,'pear_signal_event')['before_x19']=0
        with self.assertRaises(Error):self.assess(rows)

    def test_suspend_context_cannot_relabel_other_thread_or_stack(self):
        for key,value in [('slot',1),('suspend_previous',1),('resume_previous',0),('context_x18',TEBS[1]),
                          ('context_pc',BASE+0x1008),('context_sp',0x400020000),('context_flags',0x400007),
                          ('context_flags',0x80000000|0x400017),('stack_low',0x400002000),('passed',0)]:
            rows=baseline_rows();select(rows,'pear_suspend_result')[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(Error):self.assess(rows)

    def test_child_must_match_registered_native_pid_and_terminated_process(self):
        observed=result();observed['registrations']=observed['registrations'][:1]
        with self.assertRaises(Error):self.assess(observed=observed)
        rows=baseline_rows();select(rows,'pear_stage4_child_ready')['native_pid']=123
        with self.assertRaises(Error):self.assess(rows)
        for mutate in ('exit_code','alive','wrong_status','missing_exit'):
            observed=result()
            if mutate=='exit_code':observed['registrations'][1]['exit_code']=-11
            if mutate=='alive':observed['pre_cleanup']['processes']['child-1']['exited']=False
            if mutate=='wrong_status':observed['events']['child-1'][1]['exit_code']=-11
            if mutate=='missing_exit':observed['events']['child-1'].pop()
            with self.subTest(mutate=mutate),self.assertRaises(Error):self.assess(observed=observed)

    def test_child_fatal_exception_keeps_uncontinued_context(self):
        for key,value in [('continued',1),('kind',2),('code',0x80000001),('recovery_pc',BASE+0x1108),
                          ('context_x0',CHILD_REGION+54)]:
            rows=baseline_rows();select(rows,'pear_stage4_child_fault')[key]=value
            with self.subTest(key=key),self.assertRaises(Error):self.assess(rows)

    def test_image_observation_must_match_base_size_and_original_base(self):
        for role in ('loader','child-1'):
            for key in ('base','size','original_base'):
                observed=result();observed['events'][role][0][key]+=65536
                with self.subTest(role=role,key=key),self.assertRaises(Error):self.assess(observed=observed)

    def test_dynamic_words_hash_result_and_owner_address_are_bound(self):
        for key in ('word0','word1','hash','value','bytes','base'):
            rows=baseline_rows();select(rows,'pear_dynamic_call')[key]+=1
            with self.subTest(key=key),self.assertRaises(Error):self.assess(rows)
        observed=result();next(r for r in observed['events']['loader'] if r['event']=='dynamic_reserve')['base']+=65536
        with self.assertRaises(Error):self.assess(observed=observed)

    def test_native_dynamic_counts_cannot_be_lower_than_guest_claims(self):
        for key in ('reservations','commits','protects','decommits','releases','compatible_reuses',
                    'executable_publications','writable_transitions'):
            owner=dynamic();owner['root'][key]-=1
            with self.subTest(key=key),self.assertRaises(Error):self.assess(owner=owner)


    def test_coordinated_guest_native_window_shift_rejected_by_native_anchors(self):
        rows=baseline_rows()
        for item in rows:
            if item['record_kind']=='pear_signal_event':
                for key in ('ntdll_base','host_begin','host_end'):item[key]+=65536
                if item['phase']==2:
                    for key in ('before_pc','after_pc'):item[key]+=65536
        with self.assertRaises(Error):self.assess(rows)

    def test_each_native_anchor_part_is_required_and_cannot_repeat(self):
        original=result()
        indices=[i for i,r in enumerate(original['events']['loader'])
                 if r['event'] in ('stage4_thread_register','stage4_signal','stage4_thread_exit')]
        self.assertEqual(len(indices),34)
        for index in indices:
            observed=copy.deepcopy(original);observed['events']['loader'].pop(index)
            with self.subTest(missing=index),self.assertRaises(Error):self.assess(observed=observed)
        for event in ('stage4_thread_register','stage4_signal','stage4_thread_exit'):
            observed=result();selected=next(r for r in observed['events']['loader'] if r['event']==event)
            observed['events']['loader'].append(copy.deepcopy(selected))
            with self.subTest(duplicate=event),self.assertRaises(Error):self.assess(observed=observed)

    def test_native_part_order_and_schema_are_not_reassembled_permissively(self):
        for event in ('stage4_thread_register','stage4_signal'):
            observed=result();values=observed['events']['loader']
            indices=[i for i,r in enumerate(values) if r['event']==event]
            values[indices[0]],values[indices[1]]=values[indices[1]],values[indices[0]]
            with self.subTest(event=event),self.assertRaises(Error):self.assess(observed=observed)
        for key,value in [('slot',2),('slot',True),('part',True),('phase',4),('version',True),('alien_field',1)]:
            observed=result();item=next(r for r in observed['events']['loader'] if r['event']=='stage4_signal')
            item[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(Error):self.assess(observed=observed)

    def test_native_lifecycle_cannot_end_before_signal_capture(self):
        observed=result();values=observed['events']['loader']
        exits=[r for r in values if r['event']=='stage4_thread_exit']
        values[:]=[r for r in values if r['event']!='stage4_thread_exit']
        values[2:2]=exits
        with self.assertRaises(Error):self.assess(observed=observed)
        observed=result();values=observed['events']['loader']
        signals=[r for r in values if r['event']=='stage4_signal']
        indices=[i for i,r in enumerate(values) if r['event']=='stage4_signal']
        # All individual part orders remain correct, but the two completed
        # captures are reversed relative to the declared fixture phases.
        replacement=signals[8:16]+signals[:8]+signals[16:]
        for index,item in zip(indices,replacement):values[index]=item
        with self.assertRaises(Error):self.assess(observed=observed)

    def test_concurrent_register_parts_and_unordered_worker_exits_are_valid(self):
        observed=result();values=observed['events']['loader']
        indices=[i for i,r in enumerate(values) if r['event']=='stage4_thread_register']
        original=[values[i] for i in indices]
        interleaved=[row for pair in zip(original[:4],original[4:]) for row in pair]
        for index,item in zip(indices,interleaved):values[index]=item
        exits=[i for i,r in enumerate(values) if r['event']=='stage4_thread_exit']
        values[exits[0]],values[exits[1]]=values[exits[1]],values[exits[0]]
        self.assess(observed=observed)

    def test_native_exit_requires_integer_version_slot_and_matching_worker(self):
        for key,value in [('slot',True),('version',True),('teb',TEBS[1]),('native_tid',202),('exit_mode',1)]:
            observed=result();item=next(r for r in observed['events']['loader'] if r['event']=='stage4_thread_exit')
            item[key]=value
            with self.subTest(key=key),self.assertRaises(Error):self.assess(observed=observed)

    def test_native_anchors_cannot_appear_in_other_process_or_suite(self):
        for target in ('child-1','server'):
            observed=result();observed['events'].setdefault(target,[]).append(native_anchors()[0])
            with self.subTest(target=target),self.assertRaises(Error):e.validate_native_scope(observed)
        for suite in ('api','abi'):
            observed=result();observed['case']['id']=suite
            with self.subTest(suite=suite),self.assertRaises(Error):e.validate_native_scope(observed)

    def test_cleanup_failure_or_forged_release_is_not_hidden_by_final_pass(self):
        for key,value in [('released',0),('released',True),('operation_error',1)]:
            rows=baseline_rows();select(rows,'pear_exception_cleanup')[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(Error):self.assess(rows)


if __name__=='__main__':unittest.main()
