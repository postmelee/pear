#!/usr/bin/env python3
"""Reconstruct the final Wine variants and run finite native suites serially.

No existing Wine output is reused as a build input. A separate fresh native build
is comparison evidence only; the historical build remains context. Tool-cache reuse and actual development signing
are revalidated by the existing owners. The independent reproduction verifier
must pass before these observations can be published as complete.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import time

from common import Error, REPO, encoded, need


def actions(paths, *, inputs, toolchain_lock, config, source_cache, tools, local_signing):
    """Return serial operations using existing tools; constructing this list is inert."""
    import abi_review
    import arena_reproduction
    import build
    import modules
    import prepare
    import reproduction_evidence as evidence
    import run_fixtures
    import signing
    import toolchain
    import unsigned_compare

    def exit_success(result):
        need(type(result) is int and result == 0, 'reproduction_step_failed')

    def suite(name, output):
        result = run_fixtures.run(name, paths['signed'], output, True)
        need(result.get('passed') is True, 'reproduction_suite_failed')

    def prerequisite():
        result = arena_reproduction.run(local_signing, paths['native_arena'])
        need(result.get('gate_passed') is True, 'reproduction_native_arena_failed')

    def compare():
        result = unsigned_compare.compare_unsigned(paths['native_reference_build'], paths['native_build'])
        # Preserve the entire failed comparison, including unexplained bytes.
        toolchain.write_new(paths['unsigned_compare'], result)
        need(result.get('gate_passed') is True, 'reproduction_unsigned_difference_unexplained')

    return [
        ('prepare_inputs', lambda: prepare.prepare(inputs, source_cache,
            paths['inputs'].relative_to(REPO).as_posix())),
        ('toolchain_check', lambda: exit_success(toolchain.check(toolchain_lock, tools,
            REPO / 'tests/wine/fixtures', paths['toolchain_check'], paths['inputs'], config))),
        ('native_arena', prerequisite),
        ('native_reference_build', lambda: exit_success(build.build('arm64', paths['inputs'], tools,
            paths['native_reference_build'], 4))),
        ('native_reference_modules', lambda: exit_success(modules.create_inventory(paths['native_reference_build'],
            paths['native_reference_build'] / 'modules.json'))),
        ('native_build', lambda: exit_success(build.build('arm64', paths['inputs'], tools,
            paths['native_build'], 4))),
        ('native_modules', lambda: exit_success(modules.create_inventory(paths['native_build'],
            paths['native_build'] / 'modules.json'))),
        ('native_abi', lambda: toolchain.write_new(paths['native_build'] / 'abi-review.json',
            abi_review.inspect_build(paths['native_build']))),
        ('companion_build', lambda: exit_success(build.build('arm64ec-build', paths['inputs'], tools,
            paths['companion_build'], 4))),
        ('companion_modules', lambda: exit_success(modules.create_inventory(paths['companion_build'],
            paths['companion_build'] / 'modules.json'))),
        ('unsigned_compare', compare),
        ('signing', lambda: signing.prepare(paths['native_build'], local_signing, paths['signed'], True)),
        ('bootstrap', lambda: suite('bootstrap', paths['bootstrap'])),
        ('mac_driver', lambda: suite('mac-driver', paths['mac_driver'])),
    ]


def execute(start, paths, steps):
    """Stop at the first failed operation and retain explicit unperformed steps."""
    import reproduction_evidence as evidence
    need(tuple(name for name, _ in steps) == tuple(evidence.OPERATIONS), 'reproduction_operation_order')
    operations, failure = [], None
    # Relative elapsed nanoseconds stay within the bounded JSON integer domain
    # even on a host with a long system uptime. They are not wall-clock dates.
    origin = time.monotonic_ns()
    for name, action in steps:
        if failure is not None:
            operations.append(evidence.operation_result(start, name, 'unperformed'))
            continue
        print(encoded({'step': name, 'status': 'running'}).decode().strip(), flush=True)
        started = time.monotonic_ns() - origin + 1
        try:
            # This also detects source/input drift before the next mutating step.
            need(evidence.load_start(paths['root']) == start, 'reproduction_start_changed')
            action()
            row = evidence.operation_result(start, name, 'passed',
                started_ns=started, finished_ns=time.monotonic_ns() - origin + 1)
        except KeyboardInterrupt:
            failure = 'reproduction_interrupted'
        except (Error, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
            failure = exc.code if isinstance(exc, Error) else 'reproduction_operation_failed'
        if failure is not None:
            row = evidence.operation_result(start, name, 'failed', error=failure,
                started_ns=started, finished_ns=time.monotonic_ns() - origin + 1)
        operations.append(row)
        print(encoded({'step': name, 'status': row['status']}).decode().strip(), flush=True)
    evidence.write_terminal(paths['root'], start, operations, error=failure)
    return 0 if failure is None else 3


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('inputs', 'toolchain', 'config', 'source-cache', 'tools', 'local-signing', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--require-empty', action='store_true', required=True)
    args = parser.parse_args(argv)
    try:
        import build
        import reproduction_evidence as evidence
        # Existing owners read these approved records directly, so reject a CLI
        # alias or alternate record rather than appearing to honor one.
        for value, key in ((args.inputs, 'inputs'), (args.toolchain, 'toolchain'), (args.config, 'config')):
            need(value == build.RECORDS[key], 'reproduction_record_selection')
        paths = evidence.layout(args.output)
        start = evidence.create_start(paths['root'], source_cache=args.source_cache,
            tools=args.tools, local_signing=args.local_signing, jobs=4)
        steps = actions(paths, inputs=args.inputs, toolchain_lock=REPO / args.toolchain,
            config=REPO / args.config, source_cache=start['source_cache'],
            tools=REPO / start['tool_cache']['path'],
            local_signing=REPO / start['local_signing']['path'])
        code = execute(start, paths, steps)
        print(encoded({'record_kind': 'wine_reproduction_execution',
            'operations_completed': code == 0, 'independent_verification_required': True,
            'game_execution': False, 'distribution_qualified': False}).decode(), end='')
        return code
    except (Error, OSError, ValueError, KeyError, TypeError) as exc:
        print(encoded({'record_kind': 'wine_reproduction_execution', 'operations_completed': False,
            'error': exc.code if isinstance(exc, Error) else 'reproduction_preflight_failed'}).decode(), end='')
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
