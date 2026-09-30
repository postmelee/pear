#!/usr/bin/env python3
"""Finite native PE-arena prerequisites, never Wine or game qualification.

Reuse Wine's reviewed native signing and direct-child supervisor. All generated
code is fixed original fixture code. Raw identities and crashes stay task-local.
Run only after review; this command signs and executes the restricted fixture.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import errno
import hashlib
import json
import os
from pathlib import Path
import plistlib
import selectors
import subprocess
import signal
import sys
import time
import uuid

import run_fixtures as base
import signing
from common import Error, decode_json, load_json, need, read_relative, relative, sha256
from toolchain import inspect_macho, inspect_closure, inspect_sdk, native_tool, MACH_ARM64

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / 'tests/wine/fixtures/pe_arena_native.c'
MODES = ('lifecycle', 'protected-write', 'retired-call', 'data-exec', 'writer-exec')
POLICIES = {'thread-jit': MODES, 'page-wx': (*MODES[:-1], 'preparation-exec')}
VARIANTS = ('original-claims', 'allow-jit')
BOUNDS = {'grace_ms': 500, 'terminate_ms': 1000, 'kill_ms': 3000, 'drain_ms': 500}
CASE_SECONDS = 20
CRASH_SECONDS = 15
CRASH_LIMIT = 4 * 1024 * 1024
COUNTS = {'publications': 6, 'preparation_failures': 1, 'compatible_reuses': 5,
          'reuse_rounds': 4, 'leaf_calls': 22, 'mutator_calls': 22,
          'ordinary_data_writes': 22, 'busy_retirement_rejections': 10,
          'exhaustion_rejections': 5, 'incompatible_reuse_rejections': 1,
          'stale_lease_rejections': 2}


PRODUCER_FILES = tuple('tools/wine/' + name for name in
    ('pe_arena_probe.py', 'run_fixtures.py', 'signing.py', 'common.py', 'toolchain.py', 'prepare.py')) + (
    'host/probe/provisioned_probe.py', 'host/probe/hardened_baseline.py', 'tools/sources/validate_inventory.py')
SOURCE_FILES = ('tests/wine/fixtures/pe_arena_native.c', 'tests/wine/fixtures/api_launch.c',
                'tests/wine/fixtures/sentinel.c')
LOCK_FILE = 'runtime/wine/toolchain.json'


def producers():
    return {name: sha256(REPO / name) for name in PRODUCER_FILES}


def snapshot_inputs(output):
    """Retain exactly the bytes compiled or used to assess authorization."""
    inputs = {}
    for name in (*PRODUCER_FILES, *SOURCE_FILES, LOCK_FILE):
        data = read_relative(REPO, name, 4 * 1024 * 1024)
        target = output / 'inputs' / name
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with target.open('xb') as stream:
            stream.write(data)
        inputs[name] = hashlib.sha256(data).hexdigest()
    return inputs


def validate_inputs(output, inputs):
    for name, digest in inputs.items():
        need(sha256(REPO / name) == digest and sha256(output / 'inputs' / name) == digest,
             'arena_input_changed')


def records(raw, *, partial=False):
    need(isinstance(raw, bytes) and len(raw) <= base.STREAM_LIMIT + 1, 'arena_output_limit')
    lines = raw.splitlines(keepends=True)
    if lines and not lines[-1].endswith(b'\n'):
        need(partial, 'arena_truncated_record')
        lines.pop()
    values = [decode_json(line, 32768) for line in lines]
    need(len(values) <= 1024 and all(isinstance(row, dict) for row in values), 'arena_record_shape')
    return values


def unique_event(rows, event):
    matches = [row for row in rows if row.get('event') == event]
    need(len(matches) == 1, 'arena_missing_or_duplicate_' + event)
    return matches[0]


def require_fields(row, expected, code):
    need(all(type(row.get(key)) is type(value) and row[key] == value
             for key, value in expected.items()), code)


def validate_policy(policy, mode=None):
    need(type(policy) is str and policy in POLICIES, 'arena_unknown_policy')
    if mode is not None:
        need(type(mode) is str and mode in POLICIES[policy], 'arena_policy_mode_mismatch')


def validate_ready(rows, identity, nonce, mode, *, before_release=False, policy='thread-jit'):
    validate_policy(policy, mode)
    need(rows and rows[0].get('record_kind') == 'pear_bootstrap_helper', 'arena_missing_helper')
    child = type('ObservedChild', (), {'identity': identity})()
    base.validate_helper(rows[0], 'pear_bootstrap_helper', child)
    observations = rows[1:]
    for row in observations:
        need(row.get('version') == 1 and type(row.get('version')) is int and
             row.get('record_kind') == 'pear_pe_arena_probe' and row.get('mode') == mode and
             row.get('policy') == policy,
             'arena_record_scope')
    need([row.get('event') for row in observations[:4]] ==
         ['begin', 'identity', 'geometry', 'ready'], 'arena_prelude_order')
    if before_release:
        need(len(observations) == 4, 'arena_operation_before_release')
    require_fields(unique_event(observations, 'begin'), {
        'diagnostic_only': True, 'runtime_qualified': False, 'single_threaded': True,
        'mapping_bytes': 196608, 'interior_bytes': 131072, 'slot_bytes': 65536,
        'slot_capacity': 2, 'guest_page_bytes': 4096, 'reuse_rounds': 4,
        'private_vm_flags': False}, 'arena_begin_contract')
    observed = unique_event(observations, 'identity')
    fields = {'pid': 'pid', 'parent_pid': 'ppid', 'start_seconds': 'start_sec',
              'start_microseconds': 'start_usec'}
    need(all(type(observed.get(key)) is int and observed[key] == identity[value]
             for key, value in fields.items()) and observed.get('nonce') == nonce,
         'arena_identity_mismatch')
    geometry = unique_event(observations, 'geometry')
    expected = {'user_page': 4096, 'user_errno': 0, 'vm_page': 4096, 'kernel_page': 16384,
                'kernel_result': 0, 'port_release_result': 0, 'cpu_type': MACH_ARM64,
                'translation_query_result': 0, 'translation_query_errno': 0,
                'translation_query_size': 4, 'translation_value': 0, 'accepted': True}
    need(all(type(geometry.get(key)) is type(value) and geometry[key] == value
             for key, value in expected.items()), 'arena_geometry_failed')
    require_fields(unique_event(observations, 'ready'), {'nonce': nonce,
        'restricted_operations_started': False, 'timeout_ms': 10000}, 'arena_ready_contract')
    return observations


def parse_crash(data):
    need(len(data) <= CRASH_LIMIT, 'arena_crash_size_limit')
    try:
        # Apple .ips files contain a header JSON value followed by the report.
        decoder = json.JSONDecoder()
        text = data.decode('utf-8')
        header, end = decoder.raw_decode(text)
        report, tail = decoder.raw_decode(text[end:].lstrip())
        need(not text[end:].lstrip()[tail:].strip(), 'arena_crash_trailing_data')
        need(isinstance(header, dict) and isinstance(report, dict), 'arena_crash_shape')
    except (UnicodeError, ValueError, RecursionError):
        raise Error('arena_crash_invalid') from None
    return report


def crash_identity(report, result, binary):
    """Bind one private OS report to the observed child and signed native image."""
    identity = result['processes']['probe']['identity']
    need(report.get('pid') == identity['pid'] and type(report.get('pid')) is int,
         'arena_crash_pid_mismatch')
    try:
        started = datetime.strptime(report['procLaunch'], '%Y-%m-%d %H:%M:%S.%f %z').timestamp()
    except (KeyError, TypeError, ValueError):
        raise Error('arena_crash_birth_missing') from None
    birth = identity['start_sec'] + identity['start_usec'] / 1000000
    need(abs(started - birth) <= 0.002, 'arena_crash_birth_mismatch')
    need(report.get('procName') == binary['name'] and
         isinstance(report.get('procPath'), str) and
         report['procPath'].endswith('/Contents/MacOS/' + binary['name']), 'arena_crash_path_mismatch')
    need(report.get('cpuType') == 'ARM-64' and report.get('translated') is False,
         'arena_crash_architecture')
    images = report.get('usedImages')
    need(isinstance(images, list), 'arena_crash_images_missing')
    matches = [row for row in images if isinstance(row, dict) and
               str(row.get('uuid', '')).replace('-', '').lower() == binary['uuid'] and
               row.get('name') == binary['name'] and row.get('arch') == 'arm64']
    need(len(matches) == 1, 'arena_crash_image_mismatch')


def crash_matches(report, result, armed, binary):
    """A signal alone never establishes the intended negative control."""
    validate_policy(result.get('policy'), result.get('mode'))
    need(armed.get('policy') == result['policy'] and armed.get('mode') == result['mode'],
         'arena_crash_policy_mismatch')
    crash_identity(report, result, binary)
    code = result['processes']['probe']['exit_code']
    need(code in (-signal.SIGBUS, -signal.SIGSEGV), 'arena_fault_exit_unexpected')
    exception, termination = report.get('exception', {}), report.get('termination', {})
    need(isinstance(exception, dict) and isinstance(termination, dict), 'arena_crash_exception_shape')
    expected_signal = 'SIGBUS' if code == -signal.SIGBUS else 'SIGSEGV'
    need(exception.get('type') == 'EXC_BAD_ACCESS' and exception.get('signal') == expected_signal and
         termination.get('namespace') == 'SIGNAL' and termination.get('code') == -code,
         'arena_crash_exception_mismatch')
    raw_codes = exception.get('rawCodes')
    need(isinstance(raw_codes, list) and len(raw_codes) == 2 and
         all(type(value) is int for value in raw_codes) and raw_codes[0] in (1, 2),
         'arena_crash_fault_code')
    threads, index = report.get('threads'), report.get('faultingThread')
    need(isinstance(threads, list) and type(index) is int and 0 <= index < len(threads),
         'arena_crash_thread_missing')
    need(isinstance(threads[index], dict), 'arena_crash_thread_shape')
    state = threads[index].get('threadState', {})
    need(isinstance(state, dict) and all(isinstance(state.get(key), dict) for key in ('pc', 'far', 'esr')),
         'arena_crash_register_shape')
    need(state.get('flavor') == 'ARM_THREAD_STATE64', 'arena_crash_thread_architecture')
    pc = state.get('pc', {}).get('value')
    far = state.get('far', {}).get('value')
    need(type(pc) is int and type(far) is int and far == raw_codes[1], 'arena_crash_fault_address')
    for value, key in ((pc, 'pc'), (far, 'address')):
        lo, hi = armed.get('expected_' + key + '_min'), armed.get('expected_' + key + '_max')
        need(type(lo) is int and type(hi) is int and 0 < lo < hi and lo <= value < hi,
             'arena_crash_' + key + '_mismatch')
    esr = state.get('esr', {}).get('value')
    need(type(esr) is int, 'arena_crash_esr_missing')
    ec = esr >> 26
    if result['mode'] == 'protected-write':
        image = next(row for row in report['usedImages'] if isinstance(row, dict) and
                     str(row.get('uuid', '')).replace('-', '').lower() == binary['uuid'])
        image_base, image_size = image.get('base'), image.get('size')
        need(type(image_base) is int and type(image_size) is int and image_base > 0 and
             image_size > 0 and image_base <= pc < image_base + image_size,
             'arena_crash_writer_outside_signed_image')
        need(ec in (0x24, 0x25) and esr & 0x40, 'arena_crash_not_write_fault')
    else:
        need(ec in (0x20, 0x21), 'arena_crash_not_instruction_fault')
    return {'matched': True, 'signal': expected_signal, 'fault_pc': pc, 'fault_address': far,
            'process_birth_matched': True, 'signed_image_uuid_matched': True}


def cleanup_role(session, role):
    """Every role receives cleanup even when observation or a prior cleanup raises."""
    try:
        result = session.cleanup((role,), BOUNDS)
    except BaseException as exc:
        result = {'complete': False, 'errors': [{'code': 'arena_cleanup_exception',
                  'type': type(exc).__name__}], 'emergency': None}
    child = session.children.get(role)
    if child is not None and not child.reaped:
        # Keep the original failure even if terminal direct-child cleanup works.
        result['complete'] = False
        try:
            session.observer.signal_owned(child, signal.SIGKILL)
        except BaseException:
            pass
        try:
            result['emergency'] = session.emergency_reap(child)
        except BaseException as secondary:
            result.setdefault('errors', []).append({'code': 'arena_emergency_cleanup_exception',
                                                     'type': type(secondary).__name__})
    return result


def finish_session(session, sentinel_control):
    cleanup = cleanup_role(session, 'probe')
    survived = False
    try:
        child = session.children.get('sentinel')
        if child is not None:
            session.observer.refresh()
            survived = not child.exited and session.observer.identity(child.pid) == child.identity
            if survived:
                os.write(sentinel_control, b'Q')
                deadline = time.monotonic() + 2
                while not child.exited and time.monotonic() < deadline:
                    session.pump()
    except BaseException:
        survived = False
    finally:
        if sentinel_control is not None:
            try:
                os.close(sentinel_control)
            except OSError:
                survived = False
        sentinel_cleanup = cleanup_role(session, 'sentinel')
    try:
        logs = session.finish_logs(BOUNDS['drain_ms'])
    except BaseException as exc:
        logs = []
        session.failure = 'arena_log_finalization_' + type(exc).__name__
        for item in session.streams.values():
            try:
                item['stream'].close()
            except BaseException:
                pass
        for resource in (session.selector, session.observer):
            try:
                resource.close()
            except BaseException:
                pass
    return cleanup, sentinel_cleanup, survived, logs


def validate_supervision(result, raw):
    need(result['outcome'] == 'exited' and result['error'] is None and
         result['stream_error'] is None, 'arena_supervision_failed')
    need(result['cleanup'].get('complete') and result['sentinel_cleanup'].get('complete') and
         result['sentinel_survived'], 'arena_cleanup_or_sentinel_failed')
    for role in ('probe', 'sentinel'):
        child = result['processes'][role]
        need(child['reaped'] and not child['fork_seen'] and child['identity'] is not None,
             'arena_child_observation_failed')
    need(raw[('probe', 'stderr')] == b'', 'arena_unexpected_stderr')
    sentinel = records(raw[('sentinel', 'stdout')])
    child = type('ObservedChild', (), {'identity': result['processes']['sentinel']['identity']})()
    need(len(sentinel) == 2, 'arena_sentinel_records')
    base.validate_helper(sentinel[0], 'pear_sentinel_ready', child)
    need(sentinel[1] == {'version': 1, 'record_kind': 'pear_sentinel_done', 'signal': 0, 'command': 81}
         and result['processes']['sentinel']['exit_code'] == 0 and raw[('sentinel', 'stderr')] == b'',
         'arena_sentinel_changed')


def collect_crash(result, binary, output, crash_directory=None):
    directory = crash_directory or Path.home() / 'Library/Logs/DiagnosticReports'
    if not directory.is_dir():
        return None
    deadline = time.monotonic() + CRASH_SECONDS
    rows = result.get('observations', [])
    armed = unique_event(rows, 'fault_armed')
    while True:
        for path in sorted(directory.glob(binary['name'] + '-*.ips'))[-32:]:
            try:
                data = read_relative(directory, path.name, CRASH_LIMIT)
                report = parse_crash(data)
                crash_identity(report, result, binary)
            except (Error, OSError, KeyError, TypeError):
                continue
            try:
                assessment = crash_matches(report, result, armed, binary)
            except (Error, KeyError, TypeError) as exc:
                assessment = {'matched': False, 'error': getattr(exc, 'code', 'arena_crash_shape')}
            with (output / 'crash.ips').open('xb') as stream:
                stream.write(data)
            return {'path': 'crash.ips', 'sha256': hashlib.sha256(data).hexdigest(), **assessment}
        if time.monotonic() >= deadline:
            return None
        time.sleep(0.25)


def first_native_failure(rows, mode, policy='thread-jit'):
    """Add a bounded diagnostic explanation without changing the acceptance gate.

    Expected rollback injection and admission rejection are successful controls.
    Only well-typed explicit failures of known native operations are summarized;
    raw records remain available when a malformed observation cannot be named.
    """
    schemas = {
        'protection_failure': ('mprotect', {
            'slot': (0, 1), 'generation': (0, 64), 'page': (0, 15),
            'protection': (0, 7), 'result': (-1, -1), 'errno': (1, 4095)},
            {'state': ('reserved', 'preparing', 'published', 'failed', 'retired')}),
        'allocation': ('mmap', {'requested_bytes': (1, 196608),
            'jit_mapping_attempts': (1, 1), 'result': (-1, -1), 'errno': (1, 4095)}, {}),
        'data_hole': ('mmap', {'slot': (0, 1), 'generation': (1, 64), 'page': (0, 15),
            'bytes': (4096, 4096), 'result': (-1, -1), 'errno': (1, 4095)}, {}),
        'region': ('mach_vm_region', {'mach_result': (0, 65535), 'port_release_result': (0, 65535),
            'requested_bytes': (1, 196608), 'current_protection': (0, 7),
            'maximum_protection': (0, 7), 'expected_protection': (0, 7)},
            {'phase': ('allocation', 'slot_page', 'ordinary_4k', 'data_exec_target',
                       'code_write_page', 'preparation_fault_page')}),
        'cleanup': ('munmap', {'original_mapping_bytes': (196608, 196608),
            'result': (-1, -1), 'errno': (1, 4095), 'prior_exit_code': (0, 255)}, {}),
        'leaf_return': ('fixed_code_return', {'slot': (0, 1), 'generation': (1, 64),
            'page': (0, 15), 'value': (0, 0xffffffff), 'expected': (0, 0xffffffff)}, {}),
        'mutator_return': ('fixed_code_return', {'slot': (0, 1), 'generation': (1, 64),
            'page': (0, 15), 'value': (0, 0xffffffff), 'data_value': (0, 0xffffffff),
            'expected': (0, 0xffffffff)}, {}),
        'preparation_fault_ready': ('fixed_code_return', {'slot': (0, 0), 'generation': (7, 7),
            'peer_slot': (1, 1), 'peer_generation': (1, 1), 'peer_leaf_value': (0, 0xffffffff),
            'peer_leaf_expected': (42, 42)}, {'state': ('preparing',)}),
        'unexpected_fault_return': ('fault_control', {'value': (0, 0xffffffff)}, {}),
        'fault_not_delivered': ('fault_control', {}, {}),
        'result': ('fixture_exit', {'exit_code': (1, 255)}, {}),
    }
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or type(row.get('version')) is not int or row['version'] != 1 or \
           row.get('record_kind') != 'pear_pe_arena_probe' or row.get('mode') != mode or row.get('policy') != policy:
            continue
        event = row.get('event')
        if type(event) is not str or event not in schemas:
            continue
        operation, integers, enums = schemas[event]
        marker = {'region': 'accepted', 'leaf_return': 'matched',
                  'mutator_return': 'matched', 'preparation_fault_ready': 'accepted', 'result': 'passed'}.get(event)
        if marker and row.get(marker) is not False:
            continue
        if event == 'fault_not_delivered' and row.get('unexpected') is not True:
            continue
        if not all(type(row.get(key)) is int and low <= row[key] <= high
                   for key, (low, high) in integers.items()):
            continue
        if not all(type(row.get(key)) is str and row[key] in values for key, values in enums.items()):
            continue
        result = {'record_index': index, 'event': event, 'operation': operation, 'policy': policy,
                  **{key: row[key] for key in (*integers, *enums)}}
        if 'errno' in result:
            result['errno_name'] = errno.errorcode.get(result['errno'], 'UNKNOWN')
        return result
    return None


def run_case(variant, mode, binary, paths, output, *, policy='thread-jit', session_factory=base.Session):
    validate_policy(policy, mode)
    output.mkdir(mode=0o700)
    home = output / 'home'; home.mkdir(mode=0o700)
    (home / 'tmp').mkdir(mode=0o700)
    env = {'PATH': '/usr/bin:/bin', 'HOME': str(home), 'TMPDIR': str(home / 'tmp'),
           'LANG': 'C', 'LC_ALL': 'C'}
    nonce = uuid.uuid4().hex
    session = session_factory(output)
    fds = set()
    outcome, error, observations = 'not_started', None, []
    sentinel_control = None
    started = time.monotonic()
    try:
        read_fd, sentinel_control = os.pipe(); fds.add(read_fd)
        sentinel = session.launch('sentinel', [str(paths['sentinel']), str(read_fd)], env,
                                  pass_fds=(read_fd,))
        os.close(read_fd); fds.remove(read_fd)
        need(session.wait_for(lambda: b'\n' in session.streams[('sentinel', 'stdout')]['data'], 5),
             'arena_sentinel_start_timeout')
        base.validate_helper(base.parse_lines(session, 'sentinel')[0], 'pear_sentinel_ready', sentinel)
        read_fd, control = os.pipe(); fds.update((read_fd, control))
        env.update(PEAR_ARENA_NONCE=nonce, PEAR_ARENA_CONTROL_FD=str(read_fd))
        probe = session.launch('probe', [str(paths['helper']), '--exec-4k', binary['path'], mode, policy], env,
                               pass_fds=(read_fd,), allowed_paths=(paths['helper'], binary['path']))
        os.close(read_fd); fds.remove(read_fd)
        def ready():
            rows = records(bytes(session.streams[('probe', 'stdout')]['data']), partial=True)
            return any(row.get('event') == 'ready' for row in rows) or probe.exited
        need(session.wait_for(ready, 5) and not probe.exited, 'arena_ready_timeout_or_exit')
        rows = records(bytes(session.streams[('probe', 'stdout')]['data']), partial=True)
        validate_ready(rows, probe.identity, nonce, mode, before_release=True, policy=policy)
        need(session.observer.identity(probe.pid) == probe.identity and
             session.observer.executable(probe.pid) == binary['path'], 'arena_pre_release_identity')
        os.write(control, b'G'); os.close(control); fds.remove(control)
        need(session.wait_for(lambda: probe.exited, CASE_SECONDS), 'arena_case_timeout')
        outcome = 'exited'
    except BaseException as exc:
        outcome = 'interrupted' if isinstance(exc, (KeyboardInterrupt, SystemExit)) else 'error'
        error = getattr(exc, 'code', 'arena_' + type(exc).__name__)
    finally:
        for descriptor in fds:
            try:
                os.close(descriptor)
            except OSError:
                pass
        cleanup, sentinel_cleanup, survived, logs = finish_session(session, sentinel_control)
    raw = {(role, channel): bytes(item['data']) for (role, channel), item in session.streams.items()}
    result = {'schema_version': 1, 'record_kind': 'pear_pe_arena_case', 'variant': variant, 'mode': mode, 'policy': policy,
              'nonce': nonce, 'outcome': outcome, 'error': error, 'stream_error': session.failure,
              'elapsed_ms': round((time.monotonic() - started) * 1000), 'cleanup': cleanup,
              'sentinel_cleanup': sentinel_cleanup, 'sentinel_survived': survived, 'logs': logs,
              'processes': {role: {'identity': child.identity, 'exit_code': child.exit_code,
                  'reaped': child.reaped, 'fork_seen': child.fork_seen,
                  'setup_error': child.setup_error, 'emergency_cleanup': child.emergency_cleanup}
                  for role, child in session.children.items()},
              'passed': False, 'qualification': False, 'wine_execution': False,
              'runtime_qualified': False, 'game_qualified': False, 'crash': None, 'native_failure': None}
    try:
        validate_supervision(result, raw)
        observations = validate_ready(records(raw[('probe', 'stdout')]),
                                      result['processes']['probe']['identity'], nonce, mode, policy=policy)
        result['observations'] = observations
        result['native_failure'] = first_native_failure(observations, mode, policy)
        validate_lifecycle(observations, mode, result['processes']['probe']['exit_code'], policy=policy)
        if mode != 'lifecycle':
            result['crash'] = collect_crash(result, binary, output)
            need(result['crash'] is not None, 'arena_fault_unconfirmed')
            need(result['crash'].get('matched') is True, result['crash'].get('error', 'arena_fault_mismatch'))
        result['passed'] = True
        result['assessment_error'] = None
    except (Error, KeyError, TypeError, ValueError) as exc:
        result['assessment_error'] = getattr(exc, 'code', 'arena_assessment_shape')
    result['observations'] = observations
    base.write_new(output / 'case.json', result)
    return result


def expected_lifecycle(mode, policy='thread-jit'):
    """Independent finite observation contract, including real return values.

    The reviewed scenario is A/A, then slot 0 reuses B/A/B/A while slot 1
    remains A. Expected records describe externally observable results; a
    producer's summary alone cannot replace any required operation record.
    """
    validate_policy(policy, mode)
    rows = []
    def emit(event, **fields):
        rows.append({'event': event, 'policy': policy, **fields})
    def region(phase, size, protection):
        emit('region', phase=phase, mach_result=0, port_release_result=0,
             requested_bytes=size, region_bytes=size, covers_range=True,
             exact_required=True, current_protection=protection,
             expected_protection=protection, accepted=True)
    def protections(slot, generation, state, ordinary, ever, code=0, data=0):
        emit('slot_protections', slot=slot, generation=generation, state=state,
             pages_checked=16, published=bool(code), code_mask=code, data_mask=data,
             ordinary_backing_mask=ordinary, ever_code_mask=ever, accepted=True,
             code_protection=(7 if policy == 'thread-jit' else 5) if code else 0)
    def prepare(slot, generation, layout, old_ordinary, ever, reused):
        data, code = (10, 5) if layout == 'A' else (42, 21)
        emit('preparation', slot=slot, generation=generation, layout=layout,
             reused_slot=reused, inject_failure=False)
        for page in (1, 3, 5):
            if not data & (1 << page):
                continue
            if not old_ordinary & (1 << page):
                emit('data_hole', slot=slot, generation=generation, page=page,
                     bytes=4096, map_jit=False, exact_owned_subrange=True, result=0, errno=0)
            region('ordinary_4k', 4096, 3)
        emit('code_write_ready', slot=slot, generation=generation, layout=layout,
             code_mask=code, code_protection=7 if policy == 'thread-jit' else 3,
             pages_checked=2 if layout == 'A' else 3, accepted=True)
        ordinary, ever = old_ordinary | data, ever | code
        protections(slot, generation, 'published', ordinary, ever, code, data)
        emit('publication', slot=slot, generation=generation, layout=layout,
             native_writer_closed=True, cache_invalidated=True, code_mask=code,
             data_mask=data, ordinary_backing_mask=ordinary, ever_code_mask=ever,
             code_protection=7 if policy == 'thread-jit' else 5,
             pthread_jit_toggle_used=policy == 'thread-jit')
    def exercise(slot, generation, layout):
        emit('retirement_rejected', slot=slot, generation=generation, reason='active_lease',
             active_leases=1, published_preserved=True)
        for page in range(4 if layout == 'A' else 6):
            if page % 2 == 0:
                answer = 42 if layout == 'A' else 84
                emit('leaf_return', slot=slot, generation=generation, page=page,
                     value=answer, expected=answer, matched=True)
            else:
                answer = 100 * slot + 10 * generation + page + 1
                emit('mutator_return', slot=slot, generation=generation, page=page,
                     value=answer, data_value=answer, expected=answer,
                     sentinel_preserved=True, matched=True)
    def exhaust(generation, ordinary, ever, layout):
        code, data = (5, 10) if layout == 'A' else (21, 42)
        protections(0, generation, 'published', ordinary, ever, code, data)
        protections(1, 1, 'published', 10, 5, 5, 10)
        emit('allocation_rejected', reason='slot_capacity', capacity=2, available=0,
             additional_mapping_attempts=0, published_slots_preserved=True,
             request_submitted=True, admission_result=1, slot_metadata_preserved=True)
    def retire(slot, generation, ordinary, ever):
        protections(slot, generation, 'published', ordinary, ever)
        emit('retirement', slot=slot, generation=generation, active_leases=0,
             all_pages_inaccessible=True, backing_retained=True, reusable=True)
    emit('released', poll_result=1, poll_errno=0, read_bytes=1, read_errno=0,
         close_errno=0, accepted=True)
    emit('prerequisites', jit_write_protection_supported=1, fixed_assembler_reference_matches=True)
    emit('allocation', requested_bytes=196608, jit_mapping_attempts=1, initial_protection=0, result=0, errno=0)
    emit('alignment', interior_bytes=131072, interior_alignment=65536,
         mapping_extent_fits=True, interior_fits=True, aligned=True, allocation_attempts=1)
    region('allocation', 196608, 0)
    protections(0, 0, 'reserved', 0, 0)
    protections(1, 0, 'reserved', 0, 0)
    emit('preparation', slot=0, generation=1, layout='A', reused_slot=False, inject_failure=True)
    emit('data_hole', slot=0, generation=1, page=1, bytes=4096, map_jit=False,
         exact_owned_subrange=True, result=0, errno=0)
    region('ordinary_4k', 4096, 3)
    emit('injected_preparation_failure', slot=0, generation=1, new_holes=1,
         ordinary_backing_mask=2, code_published=False)
    protections(0, 1, 'failed', 2, 0)
    emit('rollback', slot=0, generation=1, backing_retained=True,
         all_pages_inaccessible=True, reusable=True)
    prepare(0, 2, 'A', 2, 0, True)
    prepare(1, 1, 'A', 0, 0, False)
    exercise(0, 2, 'A'); exercise(1, 1, 'A'); exhaust(2, 10, 5, 'A')
    retire(0, 2, 10, 5)
    emit('lease_rejected', slot=0, requested_generation=2, current_generation=2,
         state='retired', active_leases=0)
    protections(0, 2, 'retired', 10, 5)
    emit('reuse_rejected', slot=0, layout='C', reason='ordinary_page_requested_as_code',
         page=1, generation_preserved=True, backing_preserved=True, permissions_preserved=True)
    for number, layout in enumerate(('B', 'A', 'B', 'A')):
        generation = number + 3
        prepare(0, generation, layout, 10 if number == 0 else 42, 5 if number == 0 else 21, True)
        exercise(0, generation, layout); exercise(1, 1, 'A'); exhaust(generation, 42, 21, layout)
        if number == 0:
            emit('lease_rejected', slot=0, requested_generation=2, current_generation=3,
                 state='published', active_leases=0)
        emit('reuse', round=number, slot=0, layout=layout, generation=generation,
             same_owned_address=True, peer_generation_preserved=True, remaining_jit_backing_preserved=True)
        if number < 3:
            retire(0, generation, 42, 21)
    emit('lifecycle_summary', **COUNTS, passed=True, retirements=4, slot0_generation=6,
         slot1_generation=1, active_leases=0, published_slots=2, slot0_ordinary_mask=42,
         slot1_ordinary_mask=10, retained_unused_ordinary_pages=1, jit_mapping_attempts=1,
         diagnostic_only=True, runtime_qualified=False)
    if mode == 'lifecycle':
        retire(0, 6, 42, 21); retire(1, 1, 10, 5)
        emit('all_retired', slots=2, active_leases=0, retirements=6, backing_retained_until_final_unmap=True)
        emit('cleanup', original_mapping_bytes=196608, result=0, errno=0, prior_exit_code=0)
        emit('result', exit_code=0, passed=True, diagnostic_only=True, runtime_qualified=False)
    else:
        if mode == 'retired-call':
            retire(0, 6, 42, 21)
        elif mode == 'data-exec':
            region('data_exec_target', 4096, 3)
        elif mode == 'preparation-exec':
            retire(0, 6, 42, 21)
            emit('preparation', slot=0, generation=7, layout='A', reused_slot=True, inject_failure=False)
            protections(1, 1, 'published', 10, 5, 5, 10)
            emit('preparation_fault_ready', slot=0, generation=7, state='preparing',
                 target_page=0, target_protection=3, target_pages_checked=16,
                 peer_slot=1, peer_generation=1, peer_pages_checked=16, peer_leaf_value=42,
                 peer_leaf_expected=42, peer_leaf_matched=True, peer_lease_released=True,
                 published=False, accepted=True)
        emit('fault_armed', control=mode, slot=0, generation=7 if mode == 'preparation-exec' else 6,
             state='retired' if mode == 'retired-call' else
                   'preparing' if mode == 'preparation-exec' else 'published',
             access='write' if mode == 'protected-write' else 'execute',
             lifecycle_passed=True, writer_mode_requested_next=mode == 'writer-exec',
             expected_outcome='os_fault')
    return rows


def validate_lifecycle(rows, mode, exit_code, *, policy='thread-jit'):
    validate_policy(policy, mode)
    need(all(row.get('policy') == policy for row in rows), 'arena_lifecycle_policy_mismatch')
    expected = expected_lifecycle(mode, policy)
    actual = rows[4:]
    need(len(actual) == len(expected), 'arena_lifecycle_record_count')
    for row, contract in zip(actual, expected):
        require_fields(row, contract, 'arena_lifecycle_observation_' + contract['event'])
        if row['event'] == 'region':
            maximum = row.get('maximum_protection')
            need(type(maximum) is int and maximum & row['expected_protection'] == row['expected_protection'],
                 'arena_region_maximum_protection')
        if row['event'] == 'alignment':
            prefix = row.get('prefix_bytes')
            need(type(prefix) is int and 0 <= prefix < 65536 and prefix % 4096 == 0,
                 'arena_alignment_prefix')
    if mode == 'lifecycle':
        need(type(exit_code) is int and exit_code == 0, 'arena_lifecycle_exit')
    else:
        armed = actual[-1]
        for key in ('pc', 'address'):
            lo, hi = armed.get('expected_' + key + '_min'), armed.get('expected_' + key + '_max')
            need(type(lo) is int and type(hi) is int and 0 < lo < (1 << 64) - 4 and
                 lo % 4 == 0 and hi == lo + 4, 'arena_fault_range')
        if mode != 'protected-write':
            need(armed['expected_pc_min'] == armed['expected_address_min'], 'arena_instruction_target')
        need(exit_code in (-signal.SIGBUS, -signal.SIGSEGV), 'arena_fault_exit_unexpected')


def compile_native(arguments, output, label, events):
    """Bound an ordinary trusted compiler group; retain PID until pipe drain.

    Reuses signing._native's pipe/ownership pattern without broadening its
    Apple-security-tool allowlist. This function never starts a fixture.
    """
    event = {'operation': label, 'arguments': arguments}
    events.append(event)
    selector = selectors.DefaultSelector()
    buffers = [bytearray(), bytearray()]
    process = None
    failed = None
    cleanup_error = None
    try:
        process = subprocess.Popen(['/usr/bin/arch', '-arm64', *arguments], cwd=output,
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'LANG': 'C', 'LC_ALL': 'C',
                 'HOME': str(output), 'TMPDIR': str(output)}, start_new_session=True)
        deadline = time.monotonic() + 60
        for index, pipe in enumerate((process.stdout, process.stderr)):
            os.set_blocking(pipe.fileno(), False)
            selector.register(pipe, selectors.EVENT_READ, index)
        while selector.get_map():
            need(time.monotonic() < deadline, 'arena_compile_timeout')
            for key, _ in selector.select(min(0.05, max(0, deadline - time.monotonic()))):
                data = os.read(key.fd, 65536)
                if not data:
                    selector.unregister(key.fileobj)
                    continue
                remaining = base.STREAM_LIMIT + 1 - len(buffers[key.data])
                buffers[key.data].extend(data[:remaining])
                need(len(data) <= remaining and len(buffers[key.data]) <= base.STREAM_LIMIT,
                     'arena_compile_output_limit')
        process.wait(timeout=max(0.01, deadline - time.monotonic()))
        need(process.returncode == 0, 'arena_compile_failed')
    except BaseException as exc:
        failed = getattr(exc, 'code', 'arena_compile_' + type(exc).__name__)
        raise
    finally:
        if process is not None and process.returncode is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except BaseException:
                cleanup_error = 'arena_compile_signal_failed'
            try:
                process.wait(timeout=5)
            except BaseException:
                cleanup_error = 'arena_compile_reap_failed'
        for resource in (selector, *(() if process is None else (process.stdout, process.stderr))):
            try:
                resource.close()
            except BaseException:
                cleanup_error = cleanup_error or 'arena_compile_pipe_close_failed'
        event.update(exit_code=None if process is None else process.returncode,
                     failure=failed, cleanup_failure=cleanup_error)
        for channel, data in zip(('stdout', 'stderr'), buffers):
            path = output / (label + '.' + channel + '.log')
            try:
                with path.open('xb') as stream:
                    stream.write(data)
                event[channel] = {'path': path.name, 'bytes': len(data), 'sha256': sha256(path)}
            except OSError:
                event[channel] = {'write_error': True}
        if failed is None:
            need(cleanup_error is None, cleanup_error or 'arena_compile_cleanup_failed')


def prepare_binaries(output, local_input, events):
    local = signing._local_input(local_input)
    auth = signing._authorization(local['profile_path'], signing.BUNDLE_ID, events)
    lock = load_json(output / 'inputs' / LOCK_FILE)
    clang = native_tool(lock, 'clang')
    native_tool(lock, 'codesign')
    sdk = inspect_sdk(lock)
    toolchain = {'lock_sha256': sha256(output / 'inputs' / LOCK_FILE),
                 'clang': {'path': str(clang), 'sha256': sha256(clang.resolve())}, 'sdk': sdk}
    # These helpers retain the ordinary ARM64 build flags used by build.py.
    paths, helper_records = {}, {}
    for role, filename in (('helper', 'api_launch.c'), ('sentinel', 'sentinel.c')):
        unsigned = output / ('unsigned-' + role)
        source = output / 'inputs/tests/wine/fixtures' / filename
        command = [str(clang), '-arch', 'arm64', '-isysroot', sdk['path'],
                   '-std=c11', '-Wall', '-Wextra', '-Werror', str(source), '-o', str(unsigned)]
        compile_native(command, output, 'compile.' + role, events)
        main = output / role
        main.write_bytes(read_relative(output, unsigned.name, 16 * 1024 * 1024)); main.chmod(0o755)
        signing._native(['/usr/bin/codesign', '--force', '--sign', auth['identity'], '--options', 'runtime',
                         '--timestamp=none', str(main)], 'arena.sign.' + role, events)
        signature = signing._signature(main, {}, auth['claims'][signing.TEAM_ID], role, events)
        signing.verify_code_origin(unsigned, main)
        need(inspect_macho(main)['architectures'] == [MACH_ARM64], 'arena_helper_not_arm64')
        paths[role] = main
        helper_records[role] = {'sha256': sha256(main), 'unsigned_sha256': sha256(unsigned),
            'source_sha256': sha256(source), 'signature': signature,
            'closure': inspect_closure(main, output), 'compile_arguments': command}
    name = 'pear-arena-' + uuid.uuid4().hex[:12]
    info = {'CFBundleIdentifier': signing.BUNDLE_ID, 'CFBundleExecutable': name,
            'CFBundleName': 'Pear PE arena prerequisite', 'CFBundlePackageType': 'APPL',
            'CFBundleVersion': '1', 'LSMinimumSystemVersion': '26.5'}
    info_path = output / 'Info.plist'; info_path.write_bytes(plistlib.dumps(info))
    unsigned = output / 'unsigned-probe'
    command = [str(clang), '-arch', 'arm64', '-isysroot', sdk['path'], '-std=c11', '-O1',
               '-Wall', '-Wextra', '-Werror',
               '-Wl,-x86_64_layout_emulation,-segalign,0x1000,-pagezero_size,0x10000',
               '-Wl,-sectcreate,__TEXT,__info_plist,' + str(info_path),
               str(output / 'inputs' / SOURCE_FILES[0]), '-o', str(unsigned)]
    compile_native(command, output, 'compile.probe', events)
    need(inspect_macho(unsigned)['architectures'] == [MACH_ARM64], 'arena_compiler_target')
    binaries = {}
    for variant in VARIANTS:
        contents = output / variant / 'ArenaProbe.app/Contents'
        main = contents / 'MacOS' / name; main.parent.mkdir(parents=True, mode=0o700)
        main.write_bytes(read_relative(output, unsigned.name, 16 * 1024 * 1024)); main.chmod(0o755)
        (contents / 'Info.plist').write_bytes(plistlib.dumps(info))
        (contents / 'embedded.provisionprofile').write_bytes(auth['profile_bytes'])
        claims = dict(auth['claims'])
        if variant == 'allow-jit':
            claims[signing.PROFILE.BASELINE.ALLOW_JIT] = True
        claims_path = output / variant / 'claims.plist'; claims_path.write_bytes(plistlib.dumps(claims))
        signing._native(['/usr/bin/codesign', '--force', '--sign', auth['identity'], '--options', 'runtime',
                        '--timestamp=none', '--pagesize', '4096', '--entitlements', str(claims_path),
                        '--identifier', signing.BUNDLE_ID, str(contents.parent)], 'arena.sign.' + variant, events)
        signature = signing._signature(main, claims, auth['claims'][signing.TEAM_ID], variant, events)
        signing._signature(contents.parent, claims, auth['claims'][signing.TEAM_ID], variant + '.bundle', events)
        signing.verify_code_origin(unsigned, main)
        binaries[variant] = {'path': str(main.resolve()), 'name': name, 'sha256': sha256(main),
                            'uuid': base.bound_macho_uuid(main, sha256(main)), 'claims': claims,
                            'signature': signature, 'unsigned_sha256': sha256(unsigned),
                            'closure': inspect_closure(main, contents.parent)}
    need(sha256(clang.resolve()) == toolchain['clang']['sha256'] and inspect_sdk(lock) == sdk,
         'arena_compiler_or_sdk_changed')
    return binaries, paths, auth, helper_records, command, toolchain


def run(local_input, output, require_empty, *, policy='thread-jit'):
    validate_policy(policy)
    need(require_empty, 'arena_require_empty')
    # Claim the output once before expensive validation/signing. Never overwrite a prior run.
    output = base.create_output(output)
    events = []
    report = {'schema_version': 1, 'record_kind': 'pear_pe_arena_prerequisite',
              'status': 'failed', 'policy': policy, 'native_prerequisite_passed': False, 'qualification': False,
              'wine_execution': False, 'runtime_qualified': False, 'game_qualified': False,
              'source_sha256': sha256(SOURCE), 'producer_sha256': producers(), 'events': events,
              'cases': [], 'bounds': {'case_seconds': CASE_SECONDS, 'crash_seconds': CRASH_SECONDS,
                  'stream_bytes': base.STREAM_LIMIT, **BOUNDS}}
    try:
        report['inputs'] = snapshot_inputs(output)
        validate_inputs(output, report['inputs'])
        binaries, paths, auth, helper_records, command, toolchain = prepare_binaries(output, local_input, events)
        report.update(binaries=binaries, compile_arguments=command, profile_checks=auth['checks'],
                      helpers=helper_records, toolchain=toolchain,
                      helper_sha256={key: sha256(path) for key, path in paths.items()})
        cases = [('original-claims', 'lifecycle')] + [('allow-jit', mode) for mode in POLICIES[policy]]
        for variant, mode in cases:
            binary = binaries[variant]
            validate_inputs(output, report['inputs'])
            need(report['source_sha256'] == sha256(SOURCE) and report['producer_sha256'] == producers(),
                 'arena_producer_changed')
            for role, path in paths.items():
                need(sha256(path) == report['helper_sha256'][role], 'arena_helper_changed')
                signing._signature(path, {}, auth['claims'][signing.TEAM_ID],
                                   'pre.' + role + '.' + variant + '.' + mode, events)
            need(sha256(Path(binary['path'])) == binary['sha256'], 'arena_binary_changed')
            signing._signature(Path(binary['path']), binary['claims'], auth['claims'][signing.TEAM_ID],
                               'pre.' + variant + '.' + mode, events)
            row = run_case(variant, mode, binary, paths, output / (variant + '-' + mode), policy=policy)
            report['cases'].append(row)
            print(json.dumps({'variant': variant, 'mode': mode, 'policy': policy, 'passed': row['passed'],
                              'assessment_error': row['assessment_error'], 'native_failure': row['native_failure'],
                              'probe_exit_code': row['processes'].get('probe', {}).get('exit_code')}), flush=True)
            if row['error'] is not None or not row['cleanup'].get('complete'):
                raise Error('arena_supervision_stopped')
        validate_inputs(output, report['inputs'])
        for role, path in paths.items():
            need(sha256(path) == report['helper_sha256'][role], 'arena_helper_changed')
            signing._signature(path, {}, auth['claims'][signing.TEAM_ID], 'post.' + role, events)
        for variant, binary in binaries.items():
            need(sha256(Path(binary['path'])) == binary['sha256'], 'arena_binary_changed')
            signing._signature(Path(binary['path']), binary['claims'], auth['claims'][signing.TEAM_ID],
                               'post.' + variant, events)
        need(report['source_sha256'] == sha256(SOURCE) and report['producer_sha256'] == producers(),
             'arena_producer_changed')
        qualified = ([row['mode'] for row in report['cases'] if row['variant'] == 'allow-jit'] == list(POLICIES[policy]) and
                     all(row['policy'] == policy for row in report['cases']) and
                     all(row['passed'] for row in report['cases'] if row['variant'] == 'allow-jit'))
        report['native_prerequisite_passed'] = qualified
        report['status'] = 'passed' if qualified else 'failed'
    except BaseException as exc:
        report['error'] = getattr(exc, 'code', 'arena_' + type(exc).__name__)
    finally:
        base.write_new(output / 'report.json', report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy', choices=tuple(POLICIES), default='thread-jit',
                        help='Select one native prerequisite policy; thread-jit remains the default.')
    parser.add_argument('--local-input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--require-empty', action='store_true')
    args = parser.parse_args(argv)
    try:
        result = run(args.local_input, args.output, args.require_empty, policy=args.policy)
    except (Error, OSError) as exc:
        print(json.dumps({'status': 'failed', 'error': getattr(exc, 'code', 'arena_os_error')}))
        return 1
    print(json.dumps({'status': result['status'], 'policy': result['policy'], 'native_prerequisite_passed': result['native_prerequisite_passed'],
                      'wine_execution': False, 'runtime_qualified': False}))
    return 0 if result['native_prerequisite_passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
