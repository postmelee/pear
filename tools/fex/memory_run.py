#!/usr/bin/env python3
"""Run only the two original finite owner contracts under current admission.

The source-qualified Wine EC route and FEX integration are separate gates.
This runner never starts Wine, initializes FEX or launches a game.
"""
import argparse
from pathlib import Path
import os
import plistlib
import re
import sys
import uuid
if __package__:
    from .common import REPO, Error, need, load_json, sha256, write_json, operation_output, read_relative, decode_json
else:
    from common import REPO, Error, need, load_json, sha256, write_json, operation_output, read_relative, decode_json
if __package__:
    from .memory_check import verify_build, ARTIFACTS
else:
    from memory_check import verify_build, ARTIFACTS
if __package__:
    from .memory_reuse import wine_namespace
    from .memory_sign import PRODUCERS as signing_producers
else:
    from memory_reuse import wine_namespace
    from memory_sign import PRODUCERS as signing_producers

if __package__:
    from . import memory_resume_checks as atomic_checks
else:
    import memory_resume_checks as atomic_checks

BOUNDS = {'grace_ms': 3000, 'terminate_ms': 2000, 'kill_ms': 5000, 'drain_ms': 1000}
PRODUCERS = ('tools/fex/memory_run.py', 'tools/fex/memory_resume_checks.py', 'tools/fex/memory_check.py', 'tools/fex/memory_reuse.py',
             'tools/wine/signing.py', 'tools/wine/run_fixtures.py', 'host/probe/provisioned_probe.py',
             'host/probe/hardened_baseline.py')


def validate_ready(row, child, nonce):
    import re
    need(isinstance(row, dict) and type(row.get('version')) is int and row['version'] == 1
         and row.get('record_kind') == 'pear_fex_memory_admission' and row.get('event') == 'ready',
         'memory_admission_record')
    need(isinstance(nonce, str) and re.fullmatch('[0-9a-f]{32}', nonce) is not None,
         'memory_admission_nonce')
    expected = {'pid': child.identity['pid'], 'parent_pid': child.identity['ppid'],
                'start_seconds': child.identity['start_sec'], 'start_microseconds': child.identity['start_usec'],
                'nonce': nonce, 'user_page': 4096, 'vm_page': 4096, 'kernel_page': 16384,
                'translation_result': 0, 'translation_errno': 0, 'translation_value': 0,
                'translation_size': 4, 'user_page_errno': 0, 'kernel_page_result': 0,
                'host_port_release_result': 0, 'cpu_type': 0x100000c, 'jit_supported': 1,
                'geometry_accepted': True, 'restricted_operations_started': False,
                'checked_ec': False, 'wine_view_registration': False}
    need(set(row) == {'version', 'record_kind', 'event'} | set(expected), 'memory_admission_fields')
    need(all(type(row.get(key)) is type(value) and row[key] == value for key, value in expected.items()),
         'memory_admission_geometry_or_identity')


def validate_result(rows, name):
    import re
    from collections import Counter
    need(name in ('pear-fex-memory', 'pear-fex-cooperative'), 'memory_fixture_name')
    need(isinstance(rows, list) and 3 <= len(rows) <= 4096 and all(isinstance(r, dict) for r in rows),
         'memory_fixture_rows')
    header = {'version', 'record_kind'}
    fixture_keys = header | {'scope', 'sequence', 'event', 'control', 'opcode', 'returned_status', 'status',
        'requested_state', 'operation_offset', 'operation_size', 'allocation_id', 'generation', 'extent_offset',
        'extent_size', 'write_epoch', 'executor_id', 'continuation_id', 'executor_state', 'lifecycle', 'protection',
        'capabilities', 'native_error_domain', 'native_error_code'}
    cooperative_keys = header | {'sequence', 'event', 'actor', 'control', 'opcode', 'returned_status', 'status',
        'executor_id', 'continuation_id', 'executor_state', 'write_epoch', 'native_error_domain', 'native_error_code'}
    helper_keys = header | {'pid', 'ppid', 'start_sec', 'start_usec', 'cpu_type', 'translation_value',
        'query_errno', 'user_page', 'vm_page', 'kernel_page', 'kernel_error'}
    native_count_keys = {'owner_calls', 'refusals', 'allocations', 'retirements', 'publications', 'owned_code_calls',
        'protection_observations', 'patch_rounds', 'fragmentation_controls', 'continuation_controls'}
    coop_count_keys = {'owned_workers', 'workers_joined', 'schedules', 'timeout_controls', 'writes', 'handoffs',
        'owned_leaf_calls', 'wire_poll_calls', 'condition_cleanup', 'mutex_cleanup', 'trace_cleanup'}
    scope_false = {'checked_ec', 'fex_initialization', 'translated_guest_execution', 'game_execution'}
    native_complete_keys = header | {'scope', 'sequence', 'event', 'passed'} | native_count_keys | scope_false
    coop_complete_keys = header | {'sequence', 'event', 'passed', 'wine_view_registration'} | coop_count_keys | scope_false
    admission_init_keys = header | {'event', 'status', 'native_error_domain', 'native_error_code',
        'checked_ec', 'wine_view_registration'}
    admission_finish_keys = header | {'event', 'observed_regions', 'native_owned_code_execution',
        'native_arm64_pe_execution', 'wine_view_registration', 'exit_code'} | scope_false
    sequence = Counter()
    calls = []
    helpers, admissions, initializations, suites, finishes, completions = [], [], [], [], [], []
    thread_events = {'thread_create': [], 'thread_join': []}
    for row in rows:
        need(type(row.get('version')) is int and row['version'] == 1, 'memory_fixture_record_header')
        kind, event = row.get('record_kind'), row.get('event')
        need(event not in ('failed_control', 'failure', 'join_incomplete'), 'memory_fixture_control_failed')
        if kind == 'pear_bootstrap_helper':
            need(set(row) == helper_keys, 'memory_fixture_helper_fields')
            need(all(type(row[k]) is int for k in helper_keys - header), 'memory_fixture_helper_types')
            need(row['pid'] > 0 and row['ppid'] > 0 and row['start_sec'] > 0 and 0 <= row['start_usec'] < 1000000
                 and row['cpu_type'] == 0x100000c and row['translation_value'] == row['query_errno'] == row['kernel_error'] == 0
                 and row['user_page'] == row['vm_page'] and row['user_page'] in (4096, 16384)
                 and row['kernel_page'] == 16384, 'memory_fixture_helper_observation')
            helpers.append(row)
        elif kind == 'pear_fex_memory_admission':
            if event == 'ready': admissions.append(row)
            elif event == 'initialize':
                need(set(row) == admission_init_keys and type(row['status']) is int and row['status'] == 0
                     and type(row['native_error_domain']) is int and row['native_error_domain'] == 0
                     and type(row['native_error_code']) is int and row['native_error_code'] == 0,
                     'memory_fixture_initialize')
                initializations.append(row)
            elif event == 'finish':
                need(set(row) == admission_finish_keys and type(row['exit_code']) is int and row['exit_code'] == 0
                     and row['native_owned_code_execution'] is True and row['native_arm64_pe_execution'] is False
                     and type(row['observed_regions']) is int and row['observed_regions'] > 0,
                     'memory_fixture_finish')
                finishes.append(row)
            else: need(False, 'memory_fixture_admission_event')
        elif kind in ('pear_fex_memory_fixture', 'pear_fex_memory_cooperative'):
            need(type(row.get('sequence')) is int and row['sequence'] == sequence[kind] + 1,
                 'memory_fixture_sequence')
            sequence[kind] += 1
            if kind == 'pear_fex_memory_fixture':
                need(row.get('scope') == 'native_owner', 'memory_fixture_scope')
            if event == 'owner_call':
                need(set(row) == (fixture_keys if kind == 'pear_fex_memory_fixture' else cooperative_keys),
                     'memory_fixture_call_fields')
                integer_fields = (set(row) - header - {'event', 'scope', 'control', 'operation_offset', 'operation_size'})
                need(all(type(row[k]) is int for k in integer_fields), 'memory_fixture_call_types')
                need(isinstance(row['control'], str) and re.fullmatch('[a-z][a-z0-9_]{0,95}', row['control']) is not None,
                     'memory_fixture_control_name')
                need(row['status'] == row['returned_status'] and row['status'] in range(9)
                     and row['native_error_domain'] in range(4) and -(1 << 31) <= row['native_error_code'] < (1 << 31)
                     and (row['native_error_domain'] or not row['native_error_code'])
                     and (row['status'] or not (row['native_error_domain'] or row['native_error_code'])),
                     'memory_fixture_call_status')
                need(row['opcode'] in range(1, 16) and row['executor_state'] in range(6)
                     and all(0 <= row[k] <= 2**53-1 for k in integer_fields - {'native_error_code'}),
                     'memory_fixture_call_values')
                facts = {'executor_id', 'continuation_id', 'executor_state', 'write_epoch'}
                if kind == 'pear_fex_memory_fixture':
                    need(row['requested_state'] in range(6) and row['lifecycle'] in range(6)
                         and row['protection'] in range(3) and not row['capabilities'] & ~7,
                         'memory_fixture_call_enums')
                    need(all(isinstance(row[k], str) and re.fullmatch('[0-9a-f]{16}', row[k]) is not None
                             for k in ('operation_offset', 'operation_size')), 'memory_fixture_operation_range')
                    facts |= {'allocation_id', 'generation', 'extent_offset', 'extent_size', 'lifecycle', 'protection', 'capabilities'}
                else:
                    need(row['actor'] in range(4), 'memory_fixture_actor')
                if row['status']: need(all(row[k] == 0 for k in facts), 'memory_fixture_refusal_facts')
                calls.append(row)
            elif kind == 'pear_fex_memory_fixture' and event == 'suite_complete':
                need(set(row) == native_complete_keys and row['passed'] is True, 'memory_fixture_suite_terminal')
                suites.append(row)
            elif kind == 'pear_fex_memory_cooperative' and event in thread_events:
                need(set(row) == header | {'sequence', 'event', 'actor', 'native_error_code'}
                     and type(row['actor']) is int and row['actor'] in range(4)
                     and type(row['native_error_code']) is int and row['native_error_code'] == 0,
                     'memory_cooperative_thread_event')
                thread_events[event].append(row)
            elif kind == 'pear_fex_memory_cooperative' and event == 'complete':
                need(set(row) == coop_complete_keys and row['passed'] is True, 'memory_cooperative_terminal')
                completions.append(row)
            else: need(False, 'memory_fixture_event')
        else: need(False, 'memory_fixture_record_kind')
        for key in ('checked_ec', 'wine_view_registration', 'fex_initialization', 'translated_guest_execution', 'game_execution'):
            if key in row: need(row[key] is False, 'memory_fixture_overclaim')
    need(len(helpers) == len(admissions) == 1 and rows[0] is helpers[0] and rows[1] is admissions[0],
         'memory_fixture_admission_order')
    helper = helpers[0]
    child = type('RecordedIdentity', (), {'identity': {'pid': helper['pid'], 'ppid': helper['ppid'],
        'start_sec': helper['start_sec'], 'start_usec': helper['start_usec']}})()
    validate_ready(admissions[0], child, admissions[0].get('nonce'))
    fixture_calls = [r for r in calls if r['record_kind'] == 'pear_fex_memory_fixture']
    cooperative_calls = [r for r in calls if r['record_kind'] == 'pear_fex_memory_cooperative']
    controls = Counter(r['control'] for r in fixture_calls)
    if name == 'pear-fex-memory':
        need(not cooperative_calls and not completions and len(initializations) == len(suites) == len(finishes) == 1
             and rows[2] is initializations[0] and rows[-2] is suites[0] and rows[-1] is finishes[0],
             'memory_fixture_terminal_order')
        terminal = suites[0]
        expected = {'owner_calls': len(calls), 'refusals': sum(r['status'] != 0 for r in calls),
            'allocations': 103, 'retirements': 103, 'publications': 40, 'owned_code_calls': 73,
            'protection_observations': 83, 'patch_rounds': 32, 'fragmentation_controls': 1, 'continuation_controls': 2}
        need(all(type(terminal.get(k)) is int and terminal[k] == v for k, v in expected.items()),
             'memory_fixture_suite_counts')
        counted = {'reserve_extent': 103, 'retire_extent': 103, 'begin_two_page_write': 39, 'publish_two_pages': 39,
            'enter_owned_leaf': 73, 'exit_to_native_gate': 73, 'begin_cross_page_instruction_pair': 1,
            'publish_cross_page_instruction_pair': 1, 'pin_saved_source_resume': 1,
            'admit_finite_saved_resume': 127, 'discard_owned_saved_resume': 127,
            'release_original_pin_epoch': 1, 'continuation_capacity_preserves_old_pins': 1,
            'begin_unpublished_abort_control': 1, 'abort_unpublished_window': 1}
        counted.update({'register_actual_native_executor': 1, 'query_current_token': 103,
            'mixed_extent_query_unavailable': 112, 'enter_before_source_continuation': 1,
            'direct_owned_handoff_to_native': 1, 'poll_existing_owned_handoff': 1, 'unregister_actual_native_executor': 1})
        refusal_status = {'version_mismatch': 2, 'record_size_mismatch': 1, 'unknown_opcode': 1,
            'unknown_flags': 1, 'reserved_word': 1, 'reserved_word64': 1, 'foreign_owner': 6,
            'stale_generation': 6, 'foreign_allocation': 6, 'offset_alias': 6, 'extent_alias': 6,
            'unselected_role': 1, 'native_fixture_cannot_select_arm64ec_role': 3, 'wrapped_write_range': 1,
            'source_guard_write': 1, 'empty_write': 1, 'ordinary_exit_cannot_drop_saved_resume': 1,
            'nested_handoff_refused': 1, 'poll_requires_original_pin_epoch': 1, 'poll_requires_exact_resume_offset': 1,
            'poll_requires_existing_continuation': 1, 'unregister_cannot_drop_saved_resume': 1,
            'retirement_keeps_saved_generation': 3, 'continuation_capacity_preserves_old_pins': 4,
            'new_epoch_cannot_release_original_pin': 1, 'duplicate_retirement': 6,
            'shared_capacity_exhausted': 4, 'fragmented_free_bytes_refused': 4, 'dispatcher_capacity_exhausted': 4}
        counted.update({control: 1 for control in refusal_status})
        atomic_counts, atomic_refusals, atomic_opcodes = atomic_checks.controls('native_owner')
        counted.update(atomic_counts)
        refusal_status.update(atomic_refusals)
        need(controls == counted, 'memory_fixture_control_counts')
        opcode_by_control = dict.fromkeys(counted, 6)
        opcode_by_control.update({'register_actual_native_executor': 7, 'reserve_extent': 1,
            'begin_two_page_write': 2, 'publish_two_pages': 3, 'enter_owned_leaf': 8,
            'exit_to_native_gate': 9, 'begin_cross_page_instruction_pair': 2,
            'publish_cross_page_instruction_pair': 3, 'enter_before_source_continuation': 8,
            'pin_saved_source_resume': 10, 'direct_owned_handoff_to_native': 13,
            'admit_finite_saved_resume': 10, 'discard_owned_saved_resume': 11,
            'release_original_pin_epoch': 11, 'begin_unpublished_abort_control': 2,
            'abort_unpublished_window': 4, 'retire_extent': 5,
            'unregister_actual_native_executor': 12, 'unknown_opcode': 15,
            'native_fixture_cannot_select_arm64ec_role': 7, 'wrapped_write_range': 2,
            'source_guard_write': 2, 'empty_write': 2, 'ordinary_exit_cannot_drop_saved_resume': 9,
            'nested_handoff_refused': 13, 'poll_existing_owned_handoff': 13, 'poll_requires_original_pin_epoch': 13,
            'poll_requires_exact_resume_offset': 13, 'poll_requires_existing_continuation': 13,
            'unregister_cannot_drop_saved_resume': 12,
            'retirement_keeps_saved_generation': 5, 'continuation_capacity_preserves_old_pins': 10,
            'new_epoch_cannot_release_original_pin': 11, 'duplicate_retirement': 5,
            'shared_capacity_exhausted': 1, 'fragmented_free_bytes_refused': 1,
            'dispatcher_capacity_exhausted': 1})
        opcode_by_control.update(atomic_opcodes)
        atomic_checks.validate(fixture_calls, need, scope='native_owner')
        for row in fixture_calls:
            expected_status = 3 if row['control'] == 'mixed_extent_query_unavailable' else refusal_status.get(row['control'], 0)
            need(row['status'] == expected_status and row['opcode'] == opcode_by_control[row['control']],
                 'memory_fixture_control_status_or_opcode')
        need(sum(r['opcode'] == 10 and r['status'] == 0 for r in calls) == 128,
             'memory_fixture_source_pin_admission')
    else:
        need(not suites and not finishes and not initializations and len(completions) == 1
             and rows[-1] is completions[0], 'memory_cooperative_terminal_order')
        terminal = completions[0]
        expected = {'owned_workers': 4, 'workers_joined': 4, 'schedules': 32, 'timeout_controls': 2,
            'writes': 30, 'handoffs': 96, 'owned_leaf_calls': 96, 'condition_cleanup': 0, 'mutex_cleanup': 0, 'trace_cleanup': 0}
        need(all(type(terminal.get(k)) is int and terminal[k] == v for k, v in expected.items()),
             'memory_cooperative_counts')
        need(all(len(items) == 4 and {r['actor'] for r in items} == set(range(4)) for items in thread_events.values()),
             'memory_cooperative_worker_ownership')
        coop_controls = Counter(r['control'] for r in cooperative_calls)
        need(type(terminal['wire_poll_calls']) is int and 96 <= terminal['wire_poll_calls'] <= 3072
             and terminal['wire_poll_calls'] == coop_controls['poll_existing_source_descriptor'],
             'memory_cooperative_wire_poll_count')
        expected_controls = {'register_owned_worker': 4, 'unregister_owned_worker': 4,
            'enter_source_leaf': 96, 'handoff_to_compiled_native_gate': 96,
            'discard_saved_resume_original_epoch': 96, 'active_participant_timeout': 1,
            'native_pin_without_park_timeout': 1, 'cooperative_writer_admission': 30,
            'publish_after_native_park_ack': 30, 'poll_existing_source_descriptor': terminal['wire_poll_calls']}
        need(coop_controls == expected_controls, 'memory_cooperative_control_counts')
        for r in cooperative_calls:
            timed = r['control'] in ('active_participant_timeout', 'native_pin_without_park_timeout')
            need(r['status'] == (5 if timed else 0), 'memory_cooperative_control_status')
        operation = {'register_owned_worker': (7, 1), 'unregister_owned_worker': (12, 5),
            'enter_source_leaf': (8, 2), 'handoff_to_compiled_native_gate': (13, 3),
            'discard_saved_resume_original_epoch': (11, 1), 'active_participant_timeout': (2, 0),
            'native_pin_without_park_timeout': (2, 0), 'cooperative_writer_admission': (2, 1),
            'publish_after_native_park_ack': (3, 1), 'poll_existing_source_descriptor': (13, 3)}
        for row in cooperative_calls:
            opcode, state = operation[row['control']]
            need(row['opcode'] == opcode and row['executor_state'] == state, 'memory_cooperative_state_transition')
            if row['control'] in ('enter_source_leaf', 'handoff_to_compiled_native_gate', 'discard_saved_resume_original_epoch', 'poll_existing_source_descriptor'):
                need(row['actor'] in (0, 1, 2), 'memory_cooperative_reader_role')
            elif row['control'] not in ('register_owned_worker', 'unregister_owned_worker'):
                need(row['actor'] == 3, 'memory_cooperative_writer_role')
        need(all(sum(r['actor'] == actor and r['control'] == control for r in cooperative_calls) == 32
                 for actor in (0, 1, 2) for control in ('enter_source_leaf', 'handoff_to_compiled_native_gate',
                                                       'discard_saved_resume_original_epoch')),
             'memory_cooperative_reader_schedules')
        need(controls == {'setup_register': 1, 'reserve_extent': 1, 'query_current_token': 1,
            'begin_two_page_write': 1, 'publish_two_pages': 1, 'setup_unregister': 1,
            'cleanup_register_after_worker_join': 1, 'mixed_extent_query_unavailable': 1,
            'retire_extent': 1, 'cleanup_unregister_after_retirement': 1}, 'memory_cooperative_setup_cleanup')
        setup_operations = {'setup_register': 7, 'reserve_extent': 1, 'query_current_token': 6,
            'begin_two_page_write': 2, 'publish_two_pages': 3, 'setup_unregister': 12,
            'cleanup_register_after_worker_join': 7, 'mixed_extent_query_unavailable': 6,
            'retire_extent': 5, 'cleanup_unregister_after_retirement': 12}
        need(all(r['opcode'] == setup_operations[r['control']] and
                 r['status'] == (3 if r['control'] == 'mixed_extent_query_unavailable' else 0)
                 for r in fixture_calls), 'memory_cooperative_setup_cleanup_result')
    return {'owner_calls': len(calls), 'controlled_refusals': sum(r['status'] != 0 for r in calls), 'terminal': terminal}


def verify_signed(root, signing, events):
    root = operation_output(root, require_empty=False, create=False)
    value = load_json(root / 'signing.json')
    need(type(value['schema_version']) is int and value['schema_version'] == 1 and
         value['record_kind'] == 'fex_memory_prototype_signing' and value['scope'] == 'finite_native_owner',
         'memory_signing_header')
    need(value['passed'] is True and value['native_execution'] is False and value['runtime_eligible'] is False,
         'memory_signing_scope')
    build = Path(value['build_ref']['path'])
    need(sha256(build / 'build.json') == value['build_ref']['sha256'], 'memory_signed_build_changed')
    verify_build(build)
    need(set(value['producers']) == set(signing_producers), 'memory_signing_producer_set')
    for name, expected in value['producers'].items():
        need(sha256(REPO / name) == expected and sha256(root / 'producers' / name) == expected,
             'memory_signing_producer_changed')
    first = root / value['artifacts'][0]['path']
    profile = first.parent.parent / 'embedded.provisionprofile'
    auth = signing._authorization(profile, signing.BUNDLE_ID, events)
    need(auth['profile_sha256'] == value['authorization']['profile_sha256'] and
         auth['identity'] == value['authorization']['identity'], 'memory_current_authorization_changed')
    claims = signing.loader_claims(auth, 'page-wx')
    need(claims == value['loader_claims'], 'memory_current_claims_changed')
    need([row['name'] for row in value['artifacts']] == list(ARTIFACTS), 'memory_signing_artifact_set')
    for index, row in enumerate(value['artifacts']):
        need(set(row) == {'name', 'path', 'sha256', 'unsigned_sha256', 'signature', 'code_origin'},
             'memory_signing_artifact_fields')
        expected_path = (row['name'] + '.app/Contents/MacOS/' + row['name'] if index < 2
                         else 'helpers/' + row['name'])
        need(row['path'] == expected_path and row['unsigned_sha256'] == sha256(build / 'unsigned' / row['name']),
             'memory_signing_artifact_origin')
        target = root / row['path']
        need(sha256(target) == row['sha256'], 'memory_signed_artifact_changed')
        if index < 2:
            candidate = target.parent.parent / 'embedded.provisionprofile'
            need(sha256(candidate) == auth['profile_sha256'], 'memory_individual_profile_changed')
            info = plistlib.loads(read_relative(target.parent.parent, 'Info.plist', 32768))
            need(info == {'CFBundleIdentifier': signing.BUNDLE_ID, 'CFBundleExecutable': row['name'],
                          'CFBundleName': row['name'], 'CFBundlePackageType': 'APPL', 'CFBundleVersion': '1'},
                 'memory_signed_bundle_changed')
        _, metadata = signing._native(['/usr/bin/codesign', '--display', '--verbose=4', str(target)],
                                       'current.' + row['name'] + '.identifier', events)
        expected_id = signing.BUNDLE_ID if index < 2 else signing.BUNDLE_ID + '.finite.' + row['name']
        need(re.findall(r'^Identifier=([^\r\n]+)$', metadata.decode('utf-8'), re.M) == [expected_id],
             'memory_signed_identifier_changed')
        actual = signing._signature(target, claims if index < 2 else {}, auth['claims'][signing.TEAM_ID],
                                    'current.' + row['name'], events)
        need(actual == row['signature'] and
             signing.verify_code_origin(build / 'unsigned' / row['name'], target) == row['code_origin'],
             'memory_current_signature_or_source_changed')
    return value


def run_case(name, signed_root, signed, root, toolkit):
    root.mkdir(mode=0o700)
    paths = {row['name']: str(signed_root / row['path']) for row in signed['artifacts']}
    nonce = uuid.uuid4().hex
    env = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'LANG': 'C', 'LC_ALL': 'C',
           'TMPDIR': str(root), 'PEAR_FEX_MEMORY_NONCE': nonce}
    session = toolkit.Session(root)
    result = {'name': name, 'nonce': nonce, 'environment': env.copy(), 'admitted': False,
              'passed': False, 'failure': None, 'processes': {}, 'observations': {}}
    sentinel_read, sentinel_write = os.pipe()
    control_read, control_write = os.pipe()
    try:
        sentinel = session.launch('sentinel', [paths['sentinel'], str(sentinel_read)], env,
                                  pass_fds=(sentinel_read,))
        os.close(sentinel_read); sentinel_read = None
        need(session.wait_for(lambda: b'\n' in session.streams[('sentinel', 'stdout')]['data'], 5),
             'memory_sentinel_ready_timeout')
        toolkit.validate_helper(toolkit.parse_lines(session, 'sentinel')[0], 'pear_sentinel_ready', sentinel)
        env['PEAR_FEX_MEMORY_CONTROL_FD'] = str(control_read)
        child = session.launch('owner', [paths['api-launch'], '--exec-4k', paths[name], '--finite-owner'], env,
                               pass_fds=(control_read,), allowed_paths=[paths['api-launch'], paths[name]])
        os.close(control_read); control_read = None
        def ready():
            return b'"event":"ready"' in session.streams[('owner', 'stdout')]['data']
        need(session.wait_for(ready, 8), 'memory_admission_timeout')
        rows = toolkit.parse_lines(session, 'owner')
        helper, ready_row = rows[0], rows[-1]
        toolkit.validate_helper(helper, 'pear_bootstrap_helper', child)
        validate_ready(ready_row, child, nonce)
        result['admission'] = ready_row
        selected = next(row for row in signed['artifacts'] if row['name'] == name)
        need(sha256(Path(paths[name])) == selected['sha256'], 'memory_admission_code_changed')
        need(session.observer.identity(child.pid) == child.identity and
             session.observer.executable(child.pid) == paths[name], 'memory_current_owned_executable')
        os.write(control_write, b'G'); os.close(control_write); control_write = None
        result['admitted'] = True
        need(session.wait_for(lambda: child.exited, 30), 'memory_finite_execution_timeout')
        session.pump(0)
        need(not child.fork_seen and not session.observer.group_members(child), 'memory_unexpected_descendant')
        need(not sentinel.exited and session.observer.identity(sentinel.pid) == sentinel.identity,
             'memory_sentinel_survival')
        os.write(sentinel_write, b'Q'); os.close(sentinel_write); sentinel_write = None
        need(session.wait_for(lambda: sentinel.exited, 5), 'memory_sentinel_shutdown_timeout')
    except (Error, toolkit.Error, OSError, ValueError, KeyError) as error:
        result['failure'] = getattr(error, 'code', type(error).__name__)
    finally:
        for descriptor in [sentinel_read, sentinel_write, control_read, control_write]:
            if descriptor is not None:
                os.close(descriptor)
        result['cleanup'] = session.cleanup(['owner', 'sentinel'], BOUNDS, allow_interrupt=False)
        result['logs'] = session.finish_logs(BOUNDS['drain_ms'])
        result['session_failure'] = session.failure
        for role, child in session.children.items():
            result['processes'][role] = {'identity': child.identity, 'exit_code': child.exit_code,
                'reaped': child.reaped, 'fork_seen': child.fork_seen, 'allowed_paths': sorted(child.allowed_paths)}
    # Preserve the actual primary fixture failure even when its exit is nonzero.
    try:
        observed = [decode_json(line, 32768) for line in read_relative(root, 'owner.stdout.log', 2 * 1024**2).splitlines()]
        result['fixture_failures'] = [row for row in observed if row.get('event') in
            ('failed_control', 'failure', 'join_incomplete')]
    except (Error, OSError, ValueError, KeyError) as error:
        result['observation_error'] = getattr(error, 'code', type(error).__name__)
    if not result['failure']:
        try:
            need(not result.get('fixture_failures') and not result.get('observation_error'), 'memory_fixture_control_failed')
            need(result['cleanup']['complete'] and not result['session_failure'] and
                 all(row['exit_code'] == 0 for row in result['processes'].values()), 'memory_owned_exit_or_cleanup')
            rows = [decode_json(line, 32768) for line in read_relative(root, 'owner.stdout.log', 2 * 1024**2).splitlines()]
            result['observations'] = validate_result(rows, name)
            sentinel_rows = [decode_json(line, 32768) for line in read_relative(root, 'sentinel.stdout.log').splitlines()]
            need(len(sentinel_rows) == 2 and sentinel_rows[1].get('signal') == 0 and
                 sentinel_rows[1].get('command') == 81, 'memory_sentinel_terminal')
            result['passed'] = True
        except (Error, OSError, ValueError, KeyError) as error:
            result['failure'] = getattr(error, 'code', type(error).__name__)
    write_json(root / 'run.json', result)
    return result


def run(signed_root, output):
    signed_root = Path(signed_root).absolute()
    root = operation_output(output, require_empty=True)
    value = {'schema_version': 1, 'record_kind': 'fex_memory_prototype_runs',
             'scope': 'finite_native_owner', 'signing_ref': {'path': str(signed_root), 'sha256': sha256(signed_root / 'signing.json')},
             'producers': {}, 'signature_operations': [], 'stream_limit_bytes': 2 * 1024**2,
             'cases': [], 'passed': False, 'native_fixture_execution': False,
             'checked_ec': False, 'fex_initialization': False, 'translated_guest_execution': False,
             'game_qualified': False, 'stage3_complete': False, 'runtime_eligible': False}
    with wine_namespace() as (signing, toolkit):
        try:
            toolkit.STREAM_LIMIT = value['stream_limit_bytes']
            for name in PRODUCERS:
                path = root / 'producers' / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(read_relative(REPO, name))
                value['producers'][name] = sha256(path)
            signed = verify_signed(signed_root, signing, value['signature_operations'])
            for name in ARTIFACTS[:2]:
                result = run_case(name, signed_root, signed, root / name, toolkit)
                value['cases'].append({'path': name + '/run.json', 'sha256': sha256(root / name / 'run.json'),
                                       'passed': result['passed'], 'failure': result['failure']})
                need(result['passed'], result['failure'] or 'memory_prototype_failed')
            value['passed'] = True
            value['native_fixture_execution'] = True
            write_json(root / 'runs.json', value)
            return value
        except (Error, signing.Error, toolkit.Error, OSError, ValueError, KeyError, ImportError) as error:
            value['error'] = getattr(error, 'code', type(error).__name__)
            write_json(root / 'failed.json', value)
            raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--signed', required=True); p.add_argument('--output', required=True)
    p.add_argument('--require-empty', action='store_true', required=True)
    args = p.parse_args()
    try:
        run(args.signed, args.output)
        print('Finite native owner contracts passed; Wine EC and full FEX Stage 3 remain unqualified.')
        return 0
    except Exception as error:
        print(getattr(error, 'code', type(error).__name__), file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
