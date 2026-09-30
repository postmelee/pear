"""Mutation checks for actual native owner record semantics; no Wine execution."""
import copy
from pathlib import Path
import sys
import unittest

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / 'tools/wine'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Error
import dynamic_evidence as d

MAPPING = 0x100001000
INTERIOR = 0x100010000
IMAGE_BYTES = 0x200000
BASE = INTERIOR + IMAGE_BYTES


def envelope(event, **fields):
    return {'event': event, 'version': 1, 'role': 'loader', 'nonce': 'a' * 32,
            'pid': 123, 'ppid': 12, 'start_sec': 1, 'start_usec': 2,
            'identity_error': 0, 'generation': 1, **fields}


def signed(dynamic=True):
    capacity = {'policy': 'page-wx', 'wine_execution': False, 'header_sha256': 'b' * 64,
                'limits': {'alignment': 65536, 'page_bytes': 4096, 'interior_bytes': IMAGE_BYTES,
                           'max_slots': 64, 'max_image_bytes': 65536}}
    if dynamic:
        capacity['dynamic_limits'] = dict(d.LIMITS)
    return {'code_publication_policy': 'page-wx', 'arena_capacity': capacity}


def renumber(rows):
    sequence = 0
    for row in rows:
        if row['event'].startswith('dynamic_'):
            sequence += 1
            row['dynamic_sequence'] = sequence
    return rows


def rows(operations=True):
    result = [envelope('stage3_pe_continue'),
              envelope('arena_reserve', mapping_base=MAPPING, interior_base=INTERIOR,
              mapping_bytes=IMAGE_BYTES + d.LIMITS['bytes'] + 65536,
              interior_bytes=IMAGE_BYTES, page_bytes=4096, max_slots=64),
              envelope('dynamic_budget', policy='page-wx', dynamic_sequence=1, policy_version=1,
                       base=BASE, **d.LIMITS), envelope('arena_publish')]
    def event(name, **fields):
        result.append(envelope(name, policy='page-wx', dynamic_sequence=0, **fields))
    def reserve(generation):
        event('dynamic_reserve', slot=0, slot_generation=generation, base=BASE, size=4096, capacity=65536)
    def protect(generation, operation, protection):
        event('dynamic_protect', operation=operation, slot=0, slot_generation=generation,
              offset=0, size=4096, vprot=protection, unix_protection=d.PROTECTIONS[protection],
              committed_pages=1, protection_verified=True)
    def decommit(generation):
        event('dynamic_decommit', slot=0, slot_generation=generation, offset=0, size=4096,
              zeroed_pages=1, protection_verified=True)
    def release(generation):
        event('dynamic_release', slot=0, slot_generation=generation, base=BASE, size=4096,
              capacity=65536, protection_verified=True)
    if operations:
        reserve(1);protect(1,'commit',35);protect(1,'protect',37);protect(1,'protect',35)
        protect(1,'protect',37);decommit(1);protect(1,'commit',35);decommit(1);release(1)
        reserve(2);protect(2,'commit',35);decommit(2);release(2)
    result.append(envelope('stage3_guest_exit', exit_code=0))
    return renumber(result)


def case(events=None, kind='threads'):
    return {'case': {'id': kind}, 'events': {'loader': rows() if events is None else events,
                                            'child-1': rows(False), 'server': [envelope('server_ready')]}}


def select(events, name, ordinal=0):
    return [r for r in events if r['event'] == name][ordinal]


class DynamicEvidenceTests(unittest.TestCase):
    def reject(self, events=None, runtime=None, kind='threads'):
        with self.assertRaises(Error):
            d.assess_events(case(events, kind), signed() if runtime is None else runtime)

    def test_complete_source_shaped_timeline_is_address_free(self):
        observation = d.assess_events(case(), signed())
        root = observation['root']
        expected = {'reservations':2, 'commits':3, 'protects':3, 'decommits':3, 'releases':2,
                    'compatible_reuses':1, 'committed_pages':3, 'decommitted_pages':3,
                    'executable_publications':2, 'writable_transitions':4}
        self.assertEqual({key: root[key] for key in d.COUNT_FIELDS}, expected)
        self.assertEqual(root['live_allocations_at_last_observation'], 0)
        self.assertEqual(len(observation['processes']), 2)
        for forbidden in ('base', 'pid', 'nonce', 'slot_generation', 'start_sec'):
            self.assertNotIn("'"+forbidden+"':", repr(observation))

    def test_api_abi_regressions_require_only_budgets(self):
        for kind in ('api','abi'):
            value=d.assess_events(case(rows(False),kind),signed())
            self.assertEqual(value['root']['reservations'],0)

    def test_legacy_source_capacity_preserves_no_dynamic_shape(self):
        record=case([],kind='api')
        record['events']={'loader':[envelope('stage3_pe_continue')]}
        self.assertFalse(d.assess_events(record,signed(False))['dynamic_supported'])
        self.assertEqual(d.validate_budget([],signed(False)['arena_capacity'],None),0)

    def test_legacy_capacity_rejects_every_dynamic_event(self):
        for name in (*d.DYNAMIC_EVENTS,'dynamic_undocumented'):
            with self.subTest(name=name), self.assertRaises(Error):
                d.validate_budget([envelope(name)],signed(False)['arena_capacity'],None)
        self.reject(runtime=signed(False))

    def test_missing_budget_in_any_pe_process_rejected(self):
        record=case();record['events']['child-1']=[envelope('stage3_pe_continue')]
        with self.assertRaises(Error):d.assess_events(record,signed())

    def test_non_pe_process_or_server_cannot_own_dynamic_events(self):
        for role in ('server','intermediate'):
            record=case();record['events'][role]=rows(False) if role=='server' else [select(rows(False), 'dynamic_budget')]
            with self.subTest(role=role),self.assertRaises(Error):d.assess_events(record,signed())

    def test_bootstrap_handoff_precedes_lazy_arena_initialization(self):
        # The native bootstrap marker permits PE mapping; it is not guest entry.
        events = rows(False)
        self.assertEqual([row['event'] for row in events[:4]],
                         ['stage3_pe_continue', 'arena_reserve', 'dynamic_budget', 'arena_publish'])
        self.assertEqual(d.assess_events(case(events, 'api'), signed())['root']['reservations'], 0)
        for name, position in [('stage3_pe_continue', 1), ('stage3_pe_continue', 2),
                               ('dynamic_budget', 0), ('dynamic_budget', 1),
                               ('dynamic_budget', 3), ('arena_publish', 2)]:
            value = rows()
            item = select(value, name)
            value.remove(item)
            value.insert(position, item)
            with self.subTest(name=name, position=position):
                self.reject(value)
        for name in ('stage3_pe_continue', 'arena_publish'):
            value = rows()
            value.remove(select(value, name))
            with self.subTest(missing=name):
                self.reject(value)
        value = rows()
        value.insert(0, envelope('stage3_pe_continue'))
        self.reject(value)
        value = rows()
        value.insert(2, envelope('arena_retire'))
        self.reject(value)

    def test_budget_limits_and_tail_geometry_cannot_be_relabelled(self):
        for key,value in [('bytes',0),('slots',True),('slot_bytes',4096),('base',INTERIOR),
                          ('base',BASE+65536),('policy_version',2)]:
            events=rows();select(events,'dynamic_budget')[key]=value
            with self.subTest(key=key,value=value):self.reject(events)
        runtime=signed();runtime['arena_capacity']['dynamic_limits']['bytes']+=65536;self.reject(runtime=runtime)

    def test_mapping_bounds_and_overflow_rejected(self):
        for key,value in [('mapping_bytes',IMAGE_BYTES+65536),('mapping_base',0),
                          ('mapping_base',MAPPING+1),('interior_base',MAPPING+131072),
                          ('interior_bytes',IMAGE_BYTES+65536)]:
            events=rows();select(events,'arena_reserve')[key]=value
            with self.subTest(key=key):self.reject(events)
        events=rows();select(events,'arena_reserve')['mapping_base']=2**64-4096;self.reject(events)

    def test_unknown_fields_sequence_and_failure_do_not_pass(self):
        for key,value in [('dynamic_sequence',0),('dynamic_sequence',True),('generation',0),
                          ('policy','thread-jit'),('extra_unsupported',1)]:
            events=rows();select(events,'dynamic_reserve')[key]=value
            with self.subTest(key=key):self.reject(events)
        for name in ('dynamic_failure','dynamic_unknown'):
            events=rows();select(events,'dynamic_protect')['event']=name;self.reject(events)

    def test_budget_cannot_be_duplicated(self):
        events=rows();events.insert(3,copy.deepcopy(select(events,'dynamic_budget')));renumber(events);self.reject(events)

    def test_slot_generation_and_fixed_address_are_owned(self):
        for key,value in [('slot',8),('slot',True),('slot_generation',0),('slot_generation',2),
                          ('slot_generation',2**64),('base',BASE+65536),('capacity',4096),
                          ('size',65537),('size',0),('size',4097)]:
            events=rows();select(events,'dynamic_reserve')[key]=value
            with self.subTest(key=key,value=value):self.reject(events)

    def test_reuse_requires_previous_release_and_successor_generation(self):
        events=rows();select(events,'dynamic_reserve',1)['slot_generation']=3;self.reject(events)
        events=rows();first=copy.deepcopy(select(events,'dynamic_reserve'));events.insert(5,first)
        renumber(events);self.reject(events)
        events=rows();select(events,'dynamic_reserve',1)['base']+=65536;self.reject(events)

    def test_operations_cannot_refer_to_inactive_or_stale_slots(self):
        for key,value in [('slot',1),('slot_generation',2),('slot_generation',True)]:
            events=rows();select(events,'dynamic_protect')[key]=value
            with self.subTest(key=key):self.reject(events)

    def test_protect_requires_previously_committed_pages(self):
        events=rows();events.remove(select(events,'dynamic_protect'));renumber(events);self.reject(events)
        events=rows();select(events,'dynamic_protect',4)['operation']='protect';self.reject(events)

    def test_protection_and_range_are_not_inferred_from_success_flags(self):
        for key,value in [('offset',1),('offset',4096),('size',8192),('size',0),
                          ('vprot',39),('vprot',True),('vprot',34),('unix_protection',7),
                          ('unix_protection',True),('committed_pages',2),
                          ('protection_verified',1),('operation','rewrite')]:
            events=rows();select(events,'dynamic_protect')[key]=value
            with self.subTest(key=key,value=value):self.reject(events)

    def test_decommit_count_and_range_must_match_actual_pages(self):
        for key,value in [('offset',4096),('size',1),('zeroed_pages',0),
                          ('zeroed_pages',True),('protection_verified',False)]:
            events=rows();select(events,'dynamic_decommit')[key]=value
            with self.subTest(key=key):self.reject(events)

    def test_release_requires_immediate_full_revoke(self):
        events=rows();events.remove(select(events,'dynamic_decommit',1));renumber(events);self.reject(events)
        for key,value in [('base',BASE+65536),('size',8192),('capacity',4096),('slot_generation',2)]:
            events=rows();select(events,'dynamic_release')[key]=value
            with self.subTest(key=key):self.reject(events)

    def test_omitted_final_release_is_not_complete(self):
        events=rows();events.remove(select(events,'dynamic_release',1));renumber(events);self.reject(events)

    def test_operations_must_be_in_root_thread_case_guest_window(self):
        self.reject(rows(),kind='api');self.reject(rows(),kind='abi')
        record=case();record['events']['child-1']=rows()
        with self.assertRaises(Error):d.assess_events(record,signed())
        for position in (0, 2, 3):
            events=rows();event=select(events,'dynamic_reserve');events.remove(event);events.insert(position,event)
            with self.subTest(position=position):self.reject(events)
        events=rows();exit_row=events.pop();events.insert(5,exit_row);self.reject(events)

    def test_missing_native_dynamic_work_cannot_satisfy_thread_case(self):
        self.reject(rows(False))

    def test_committed_noaccess_is_distinct_from_decommitted(self):
        events=rows();item=select(events,'dynamic_protect');item['vprot']=32;item['unix_protection']=0
        observation=d.assess_events(case(events),signed())
        self.assertEqual(observation['root']['protects'],3)

    def test_three_page_allocation_tracks_middle_page_independently(self):
        events=rows()
        for event in events:
            if event['event'] in ('dynamic_reserve','dynamic_release'):event['size']=12288
            elif event['event']=='dynamic_protect':
                if event['operation']=='commit':event['size']=12288;event['committed_pages']=3
                else:event['offset']=4096
            elif event['event']=='dynamic_decommit':event['size']=12288;event['zeroed_pages']=3
        observation=d.assess_events(case(events),signed())
        self.assertEqual(observation['root']['decommitted_pages'],9)
        # A subsequent protect on an uncommitted neighboring page must fail.
        select(events,'dynamic_protect')['size']=4096
        select(events,'dynamic_protect')['committed_pages']=1
        self.reject(events)


if __name__=='__main__':unittest.main()
