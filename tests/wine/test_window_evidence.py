"""Synthetic source-shaped window timelines; these tests do not execute Cocoa.

Only signed fixture byte inspection is mocked. The evidence and rejection gates
are real; source-shaped values are independent of the native event emitter.
"""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/wine'))
from common import Error
import window_evidence as w

RUNTIME = Path('/private/synthetic-runtime')
PE_BASE, DRIVER_PE_BASE, NATIVE_BASE = 0x180000000, 0x190000000, 0x100000000
TEB, WINE_TID, MAIN_TID, NATIVE_PID, WINDOWS_TID = 0x120000, 789, 456, 123, 64
FACTS = {'fixture': {'image_size': 65536, 'original_base': 0x140000000, 'rva': 0x1000, 'sha256': '1'*64},
         'control': {'image_size': 131072, 'original_base': 0x150000000, 'rva': 0x2000, 'sha256': '2'*64},
         'native_sha256': '3'*64, 'native_path': 'lib/wine/aarch64-unix/winemac.so', 'native_offset': 0x3000}


def envelope(event, **fields):
    return dict(version=1, role='loader', event=event, nonce='a'*32, pid=NATIVE_PID, ppid=12,
                generation=1, start_sec=1, start_usec=2, identity_error=0, **fields)


def fixture(turns=1):
    rows = [dict(version=1, record_kind='pear_window_identity', module_base=PE_BASE, wndproc=PE_BASE+0x1000,
        guest_teb=TEB, guest_tid=WINDOWS_TID, native_pid=NATIVE_PID, driver_module=DRIVER_PE_BASE,
        driver_control=DRIVER_PE_BASE+0x2000, cycles=20)]
    events = [envelope('stage3_pe_continue')]
    for base, facts in ((PE_BASE, FACTS['fixture']), (DRIVER_PE_BASE, FACTS['control'])):
        events.append(envelope('arena_publish', base=base, size=facts['image_size'], original_base=facts['original_base']))
    sequence = 0
    def event(cycle, phase, value, *, main=None, window=None):
        nonlocal sequence
        sequence += 1
        main = int(phase in (1,3,4,7,10,13,17,18)) if main is None else main
        head = dict(seq=sequence, cycle=cycle, phase=phase)
        events.append(envelope('stage5_window', **head, part=1, hwnd=0x100+cycle if cycle else 0,
            window=(0x160000 + cycle*16 if cycle else 0) if window is None else window,
            token=0x53350000+cycle if cycle else 0))
        events.append(envelope('stage5_window', **head, part=2, thread_id=MAIN_TID if main else WINE_TID,
            main=main, mode=0, value=value))
        if phase == 0:
            events.append(envelope('stage5_window', **head, part=3, driver_base=NATIVE_BASE,
                driver_entry=NATIVE_BASE+0x3000, teb=TEB, native_tid=WINDOWS_TID))
    event(0,0,0)
    events.append(envelope('stage5_window_images'))
    for index, path in enumerate((str(RUNTIME/FACTS['native_path']),
        '/System/Library/Frameworks/AppKit.framework/Versions/C/AppKit',
        '/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation')):
        events.append(envelope('image', index=index, path=path))
    events.append(envelope('images_end', count=3))
    for cycle in range(1,21):
        token=0x53350000+cycle
        rows.append(dict(version=1, record_kind='pear_window_cycle', cycle=cycle, hwnd=0x100+cycle,
            token=token, guest_teb=TEB, guest_tid=WINDOWS_TID, nccreate=1, create=1, app_messages=1,
            reentries=1, sysclose=1, close=1, destroy=1, ncdestroy=1, late_callbacks=0, title_checks=1,
            hwnd_gone=1, drain_complete=1, callback_result=token^0x13579bdf))
        # Native posting occurs before that DRAIN's main-thread barrier; AppKit
        # consumes the wake later. A fresh barrier is required for completion.
        count = turns if isinstance(turns, int) else turns[cycle - 1]
        for phase in range(1, 12):
            event(cycle, phase, {1:0x170000, 5:0x8351, 8:token^0x13579bdf}.get(phase, 0))
        if count == 1:
            event(cycle, 12, 0)  # The mandatory first wake still follows early deallocation.
        for ordinal in range(1, count + 1):
            wake = (0x505335 << 24) | (cycle << 8) | ordinal
            event(cycle, 17, wake)
            event(cycle, 13, ordinal)
            event(cycle, 14, (ordinal << 4) | 15)
            event(cycle, 18, wake)
        if count > 1:
            event(cycle, 12, 0)
        event(cycle, 13, count + 1)
        event(cycle, 14, ((count + 1) << 4) | 15)
        event(cycle, 15, 1)
    event(0,19,15)
    event(0,16,20)
    events.append(envelope('stage3_guest_exit',exit_code=0))
    rows.append(dict(version=1,record_kind='pear_window_result',passed=1,error_step=0,error_code=0,cycles=20,
        app_messages=20,reentries=20,closes=20,destroys=20,ncdestroys=20,late_callbacks=0,
        class_registered=1,class_unregistered=1,native_final=1,cleanup_complete=1))
    result={'case':{'id':'window'},'events':{'loader':events,'server':[]},
            'processes':{'loader':{'identity':{'pid':NATIVE_PID}}}}
    signed={'authorization_scope':'development_windows_mac_driver_fixtures'}
    dynamic={'dynamic_supported':True,'root':{'reservations':0},'processes':[{'reservations':0}]}
    return rows,result,signed,dynamic


def part(result,cycle,phase,number,occurrence=-1):
    return [row for row in result['events']['loader'] if row['event']=='stage5_window' and
            row['cycle']==cycle and row['phase']==phase and row['part']==number][occurrence]


class WindowEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.rows,self.result,self.signed,self.dynamic=fixture()
        patcher=patch.object(w,'fixture_facts',return_value=copy.deepcopy(FACTS))
        self.facts=patcher.start();self.addCleanup(patcher.stop)

    def assess(self):
        return w.assess(self.rows,self.result,RUNTIME,self.signed,self.dynamic)

    def reject(self,code=None):
        with self.assertRaises(Error) as raised:self.assess()
        if code:self.assertEqual(raised.exception.code,code)

    def test_finite_complete_timeline_is_address_free(self):
        result=self.assess()
        self.assertEqual(result['cycles'],20)
        self.assertEqual(result['native_anchor_parts'],767)
        self.assertEqual(result['main_thread_barriers'],40)
        self.assertEqual(result['deallocated_windows'],20)
        self.assertEqual(result['observed_late_callbacks'],0)
        self.assertEqual(result['fixture_sha256'],'1'*64)
        for private in ('module_base','wndproc','driver_base','driver_control','hwnd','window','guest_teb',
                        'guest_tid','native_pid','nonce','/private','0x'):
            self.assertNotIn('"'+private+'"',json.dumps(result))
        self.facts.assert_called_once_with(RUNTIME,self.signed)

    def test_flat_uint64_decoder_rejects_duplicate_bool_float_overflow_nested(self):
        valid=json.dumps(self.rows[0]).encode()
        self.assertEqual(w.decode_stdout_row(valid),self.rows[0])
        variants=[valid.replace(b'"cycles": 20',b'"cycles": true'),
                  valid.replace(b'"cycles": 20',b'"cycles": 20.0'),
                  valid.replace(b'"cycles": 20',b'"cycles": -1'),
                  valid.replace(b'"cycles": 20',b'"cycles": 18446744073709551616'),
                  valid.replace(b'"cycles": 20',b'"cycles": {"cycles": 20}'),
                  valid.replace(b'"cycles": 20',b'"cycles": 20,"cycles":20'),b' '*3073]
        for data in variants:
            with self.subTest(data=data[-60:]),self.assertRaises(Error):w.decode_stdout_row(data)

    def test_missing_or_extra_lifetime_output_rejected(self):
        for index in (0,1,20,21):
            old=self.rows;self.rows=old[:index]+old[index+1:]
            self.reject();self.rows=old
        self.rows.insert(2,copy.deepcopy(self.rows[1]));self.reject()

    def test_guest_failure_late_callback_and_bad_return_rejected(self):
        for field,value in (('destroy',0),('late_callbacks',1),('callback_result',0),('drain_complete',0),('guest_tid',65)):
            old=self.rows[1][field];self.rows[1][field]=value
            with self.subTest(field=field):self.reject()
            self.rows[1][field]=old
        self.rows[-1]['class_unregistered']=0;self.reject()

    def test_callback_and_driver_pe_export_addresses_are_source_bound(self):
        for key in ('wndproc','driver_control'):
            self.rows[0][key]+=4
            with self.subTest(key=key):self.reject('window_guest_control_binding')
            self.rows[0][key]-=4
        self.rows[0]['module_base']+=65536;self.rows[0]['wndproc']+=65536
        self.reject('window_executed_image_binding')

    def test_both_pe_images_must_be_live_through_native_control_lifetime(self):
        for base in (PE_BASE,DRIVER_PE_BASE):
            saved=copy.deepcopy(self.result)
            raw=self.result['events']['loader']
            published=next(row for row in raw if row['event']=='arena_publish' and row['base']==base)
            raw.remove(published)
            raw.insert(raw.index(part(self.result,1,1,1)),published)
            with self.subTest(base=base,mutation='late_publication'):
                self.reject('window_executed_image_lifetime')
            self.result=copy.deepcopy(saved)
            raw=self.result['events']['loader']
            raw.insert(raw.index(part(self.result,1,1,1)),envelope('arena_retire',base=base))
            with self.subTest(base=base,mutation='early_retirement'):
                self.reject('window_executed_image_lifetime')
            self.result=saved
        raw=self.result['events']['loader']
        raw.insert(-1,envelope('arena_retire',base=DRIVER_PE_BASE))
        self.assertEqual(self.assess()['cycles'],20)

    def test_wrong_native_symbol_or_guest_thread_binding_rejected(self):
        for key in ('driver_entry','teb','native_tid'):
            row=part(self.result,0,0,3);old=row[key];row[key]+=4
            with self.subTest(key=key):self.reject('window_native_control_binding')
            row[key]=old

    def test_native_parts_cannot_be_missing_repeated_reordered_or_boolean(self):
        raw=self.result['events']['loader']
        for change in ('missing','duplicate','order','bool'):
            saved=copy.deepcopy(raw)
            row=part(self.result,1,5,2);index=raw.index(row)
            if change=='missing':raw.pop(index)
            elif change=='duplicate':raw.insert(index,copy.deepcopy(row))
            elif change=='order':raw[index-1],raw[index]=raw[index],raw[index-1]
            else:row['main']=False
            with self.subTest(change=change):self.reject()
            raw[:]=saved

    def test_main_thread_and_wine_callback_thread_are_distinct(self):
        for cycle,phase,field,value in ((1,3,'main',0),(1,6,'main',1),(2,3,'thread_id',999),(1,12,'thread_id',888),(1,6,'mode',1)):
            row=part(self.result,cycle,phase,2);old=row[field];row[field]=value
            with self.subTest(phase=phase,field=field):self.reject()
            row[field]=old

    def test_pointer_reuse_after_complete_previous_lifetime_is_accepted(self):
        for row in self.result['events']['loader']:
            if row['event']=='stage5_window' and row['cycle'] and row['part']==1:row['window']=0x160000
        self.assertEqual(self.assess()['deallocated_windows'],20)

    def test_title_observation_may_precede_reentry_record(self):
        raw=self.result['events']['loader'];index=raw.index(part(self.result,1,6,1))
        raw[index:index+4]=raw[index+2:index+4]+raw[index:index+2]
        for row in raw:
            if row['event']=='stage5_window' and row['cycle']==1:
                if row['phase']==7:row['seq']-=1
                elif row['phase']==6:row['seq']+=1
        self.assertEqual(self.assess()['callback_reentries'],20)

    def test_deallocation_may_occur_on_cocoa_main_thread(self):
        row=part(self.result,1,12,2);row['main']=1;row['thread_id']=MAIN_TID
        self.assertEqual(self.assess()['deallocated_windows'],20)

    def test_generation_or_object_mismatch_cannot_borrow_another_lifetime(self):
        for key,value in (('token',0x53350002),('hwnd',0x102),('window',0x160020)):
            row=part(self.result,1,4,1);old=row[key];row[key]=value
            with self.subTest(key=key):self.reject('window_lifetime_identity')
            row[key]=old

    def test_draining_and_deallocation_are_required(self):
        for phase in (12,13,14,15,17,18):
            old=copy.deepcopy(self.result)
            self.result['events']['loader']=[row for row in self.result['events']['loader'] if
                not(row['event']=='stage5_window' and row['cycle']==20 and row['phase']==phase)]
            with self.subTest(phase=phase):self.reject()
            self.result=old
        part(self.result,1,14,2)['value']=16;self.reject('window_teardown_barrier_order')

    def test_final_drain_must_observe_empty_queue(self):
        part(self.result,20,14,2)['value']=16
        self.reject('window_teardown_barrier_order')

    def test_pending_nonempty_drain_can_retry_before_empty_completion(self):
        raw=self.result['events']['loader']
        index=raw.index(part(self.result,1,15,1))
        retry=[copy.deepcopy(part(self.result,1,phase,n)) for phase in (13,14) for n in (1,2)]
        part(self.result,1,14,2)['value']=40
        retry[1]['value']=3
        retry[3]['value']=63
        raw[index:index]=retry
        sequence=0
        for row in raw:
            if row['event']=='stage5_window':
                if row['part']==1:sequence+=1
                row['seq']=sequence
        value=self.assess()
        self.assertEqual(value['native_anchor_parts'],771)
        self.assertEqual(value['event_drains'],41)

    def test_intermediate_queue_identity_failure_cannot_retry_to_success(self):
        raw=self.result['events']['loader']
        index=raw.index(part(self.result,1,15,1))
        retry=[copy.deepcopy(part(self.result,1,phase,n)) for phase in (13,14) for n in (1,2)]
        # The FD, array and frame may all be idle, but the wrong owner queue is
        # an immediate native failure and cannot be repaired by a later sample.
        part(self.result,1,14,2)['value']=39
        retry[1]['value']=3
        retry[3]['value']=63
        raw[index:index]=retry
        self.renumber();self.reject('window_teardown_barrier_order')

    def test_each_idle_fact_is_required_at_completion_and_final_sample(self):
        for cycle,phase in ((1,14),(0,19)):
            row=part(self.result,cycle,phase,2);original=row['value']
            for flag in (1,2,4,8):
                row['value']=original & ~flag
                with self.subTest(cycle=cycle,flag=flag):self.reject()
            row['value']=original

    def test_wake_tag_thread_and_exactly_one_consumption_are_required(self):
        for phase in (17,18):
            row=part(self.result,1,phase,2);original=copy.deepcopy(row)
            for field,value in (('value',0),('main',0),('thread_id',WINE_TID)):
                row[field]=value
                with self.subTest(phase=phase,field=field):self.reject()
                row.update(original)
        raw=self.result['events']['loader']
        index=raw.index(part(self.result,1,18,1))
        raw[index:index]=[copy.deepcopy(part(self.result,1,18,n)) for n in (1,2)]
        self.renumber();self.reject('window_lifetime_coverage')

    def renumber(self):
        sequence=0
        for row in self.result['events']['loader']:
            if row['event']=='stage5_window':
                if row['part']==1:sequence+=1
                row['seq']=sequence

    def test_last_main_barrier_must_follow_consumed_event(self):
        raw=self.result['events']['loader']
        turn=[part(self.result,1,18,n) for n in (1,2)]
        for row in turn:raw.remove(row)
        index=raw.index(part(self.result,1,14,1))
        raw[index:index]=turn
        self.renumber();self.reject('window_teardown_barrier_order')

    def test_deallocation_must_precede_qualifying_drain(self):
        raw=self.result['events']['loader']
        dealloc=[part(self.result,1,12,n) for n in (1,2)]
        for row in dealloc:raw.remove(row)
        index=raw.index(part(self.result,1,15,1));raw[index:index]=dealloc
        # The native observer holds its lock from the drain event through
        # completion, so deallocation cannot first arrive between these rows.
        self.renumber();self.reject('window_teardown_barrier_order')

    def test_deallocation_can_follow_consumed_event(self):
        raw=self.result['events']['loader']
        dealloc=[part(self.result,1,12,n) for n in (1,2)]
        for row in dealloc:raw.remove(row)
        index=raw.index(part(self.result,1,13,1));raw[index:index]=dealloc
        self.renumber();self.assertEqual(self.assess()['appkit_event_turns'],20)

    def test_two_and_eight_paced_turns_preserve_twenty_guest_callbacks(self):
        for count in (2, 8):
            with self.subTest(turns=count):
                self.rows,self.result,self.signed,self.dynamic=fixture(count)
                value=self.assess()
                self.assertEqual(value['appkit_event_turns'],20*count)
                self.assertEqual(value['event_drains'],20*(count+1))
                self.assertEqual(value['native_anchor_parts'],527+4*20*(2*count+1))
                for key in ('cocoa_close_events','application_messages','callback_reentries','deallocated_windows'):
                    self.assertEqual(value[key],20)
        self.rows[1]['app_messages']=8
        self.reject('window_cycle_failed')

    def test_maximum_successful_pacing_fits_finite_part_envelope(self):
        self.rows,self.result,self.signed,self.dynamic=fixture(99)
        value=self.assess()
        self.assertEqual(value['event_drains'],2000)
        self.assertEqual(value['appkit_event_turns'],1980)
        self.assertEqual(value['native_anchor_parts'],16447)
        events,parts=w.native_parts(self.result['events']['loader'])
        self.assertEqual(events[-1]['seq'],8223)
        self.assertLess(parts,w.MAX_NATIVE_PARTS)
        from common import decode_json
        wake=part(self.result,20,18,2)
        self.assertEqual(decode_json(json.dumps(wake).encode())['value'],
                         (0x505335<<24)|(20<<8)|99)
        self.assertLess(wake['value'],2**53)

    def test_attempted_turn_and_drain_bounds_remain_finite(self):
        for count in (100,101):
            self.rows,self.result,self.signed,self.dynamic=fixture([count]+[1]*19)
            with self.subTest(turns=count):self.reject('window_lifetime_coverage')
        with self.assertRaisesRegex(Error,'window_native_part_count'):
            w.native_parts([{'event':'stage5_window'}]*(w.MAX_NATIVE_PARTS+1))

    def test_turn_identity_rejects_wrong_tag_cycle_zero_skip_and_replay(self):
        self.rows,self.result,self.signed,self.dynamic=fixture(2)
        original=copy.deepcopy(self.result)
        for value in (0,0x505335,(0x505335<<24)|(2<<8)|2,
                      (0x505334<<24)|(1<<8)|2,(0x505335<<24)|(1<<8),
                      (0x505335<<24)|(1<<8)|1,(0x505335<<24)|(1<<8)|3,
                      (0x505335<<24)|(1<<8)|101):
            for phase in (17,18):part(self.result,1,phase,2)['value']=value
            with self.subTest(value=value):self.reject('window_appkit_turn_order')
            self.result=copy.deepcopy(original)

    def test_second_post_cannot_precede_first_consumption(self):
        self.rows,self.result,self.signed,self.dynamic=fixture(2)
        raw=self.result['events']['loader']
        posted=[part(self.result,1,17,n) for n in (1,2)]
        for row in posted:raw.remove(row)
        index=raw.index(part(self.result,1,18,1,0));raw[index:index]=posted
        self.renumber();self.reject('window_appkit_turn_order')

    def test_duplicate_consumption_cannot_replace_a_missing_later_turn(self):
        self.rows,self.result,self.signed,self.dynamic=fixture(2)
        for number in (1,2):
            later=part(self.result,1,18,number)
            earlier=part(self.result,1,18,number,0)
            if number==2:later['value']=earlier['value']
        self.reject('window_appkit_turn_order')

    def test_later_post_after_deallocation_is_rejected(self):
        self.rows,self.result,self.signed,self.dynamic=fixture(2)
        raw=self.result['events']['loader']
        dealloc=[part(self.result,1,12,n) for n in (1,2)]
        for row in dealloc:raw.remove(row)
        index=raw.index(part(self.result,1,17,1));raw[index:index]=dealloc
        self.renumber();self.reject('window_appkit_posting_barrier')

    def test_first_post_must_follow_discard_even_with_early_deallocation(self):
        raw=self.result['events']['loader']
        posted=[part(self.result,1,17,n) for n in (1,2)]
        for row in posted:raw.remove(row)
        index=raw.index(part(self.result,1,11,1));raw[index:index]=posted
        self.renumber();self.reject('window_appkit_turn_order')

    def test_mandatory_first_post_cannot_be_delayed_until_a_later_drain(self):
        raw=self.result['events']['loader']
        initial=[copy.deepcopy(part(self.result,1,phase,n,0)) for phase in (13,14) for n in (1,2)]
        for row in raw:
            if row['event']=='stage5_window' and row['cycle']==1 and row['part']==2:
                if row['phase']==13:row['value']+=1
                if row['phase']==14:row['value']+=16
        index=raw.index(part(self.result,1,17,1));raw[index:index]=initial
        self.renumber();self.reject('window_appkit_posting_barrier')

    def test_each_consumption_must_follow_its_posting_main_barrier(self):
        self.rows,self.result,self.signed,self.dynamic=fixture(2)
        raw=self.result['events']['loader']
        consumed=[part(self.result,1,18,n,0) for n in (1,2)]
        for row in consumed:raw.remove(row)
        index=raw.index(part(self.result,1,13,1,0));raw[index:index]=consumed
        self.renumber();self.reject('window_appkit_posting_barrier')

    def test_next_post_cannot_precede_previous_owner_drain(self):
        self.rows,self.result,self.signed,self.dynamic=fixture(2)
        raw=self.result['events']['loader']
        moved=[part(self.result,1,18,n,0) for n in (1,2)] + [part(self.result,1,17,n) for n in (1,2)]
        for row in moved:raw.remove(row)
        index=raw.index(part(self.result,1,14,1,0));raw[index:index]=moved
        self.renumber();self.reject('window_appkit_posting_barrier')

    def test_latest_not_first_consumption_must_precede_final_barrier(self):
        self.rows,self.result,self.signed,self.dynamic=fixture(2)
        raw=self.result['events']['loader']
        consumed=[part(self.result,1,18,n) for n in (1,2)]
        for row in consumed:raw.remove(row)
        index=raw.index(part(self.result,1,14,1));raw[index:index]=consumed
        self.renumber();self.reject('window_teardown_barrier_order')

    def test_later_turns_retain_thread_mode_and_owned_lifetime_checks(self):
        self.rows,self.result,self.signed,self.dynamic=fixture(2)
        for phase in (17,18):
            for field,value in (('main',0),('thread_id',WINE_TID),('mode',1)):
                row=part(self.result,1,phase,2);old=row[field];row[field]=value
                with self.subTest(phase=phase,field=field):self.reject()
                row[field]=old
        raw=self.result['events']['loader']
        posted=[part(self.result,1,17,n) for n in (1,2)]
        for row in posted:raw.remove(row)
        index=raw.index(part(self.result,1,15,2))+1;raw[index:index]=posted
        self.renumber();self.reject('window_lifetime_order')

    def test_exit_cannot_split_native_phase_parts(self):
        raw=self.result['events']['loader']
        exit_row=raw.pop()
        raw.insert(raw.index(part(self.result,0,16,2)),exit_row)
        self.reject('window_native_part_interleaving')

    def test_global_phase_cannot_be_inserted_inside_window_lifetime(self):
        raw=self.result['events']['loader']
        index=raw.index(part(self.result,1,6,1))
        extra=[copy.deepcopy(part(self.result,1,5,n)) for n in (1,2)]
        for row in extra:row['phase']=16
        raw[index:index]=extra
        sequence=0
        for row in raw:
            if row['event']=='stage5_window':
                if row['part']==1:sequence+=1
                row['seq']=sequence
        self.reject('window_lifetime_order')

    def test_creation_retain_prevents_deallocation_before_discard(self):
        raw=self.result['events']['loader']
        index=raw.index(part(self.result,1,11,1))
        raw[index:index+4]=raw[index+2:index+4]+raw[index:index+2]
        sequence=0
        for row in raw:
            if row['event']=='stage5_window':
                if row['part']==1:sequence+=1
                row['seq']=sequence
        self.reject('window_callback_lifecycle_order')

    def test_native_failed_operation_cannot_pass_on_guest_counters(self):
        part(self.result,1,11,2)['value']=1;self.reject('window_native_operation_failed')

    def test_native_driver_and_cocoa_frameworks_must_be_in_late_snapshot(self):
        raw=self.result['events']['loader']
        for index in range(3):
            row=next(row for row in raw if row['event']=='image' and row['index']==index)
            old=row['path'];row['path']='/System/Library/Frameworks/Other.framework/Other'
            with self.subTest(index=index):self.reject()
            row['path']=old

    def test_snapshot_and_process_exit_cannot_precede_initialization_or_final(self):
        raw=self.result['events']['loader'];row=raw.pop();raw.insert(-2,row)
        self.reject('window_exit_before_teardown')

    def test_scope_and_dynamic_operations_remain_fail_closed(self):
        self.dynamic['root']['reservations']=1;self.reject('window_dynamic_scope')
        self.dynamic['root']['reservations']=0
        self.signed['authorization_scope']='development_windows_thread_memory_exception_fixtures'
        self.reject('window_authorization_scope')

    def test_native_event_cannot_appear_in_regression_or_descendant(self):
        self.result['case']['id']='api';self.reject('window_native_scope')
        self.result['case']['id']='window'
        self.result['events']['process-01']=[copy.deepcopy(part(self.result,1,3,1))]
        self.reject('window_native_scope')


if __name__=='__main__':unittest.main()
