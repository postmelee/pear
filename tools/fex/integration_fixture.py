#!/usr/bin/env python3
"""Compile original Pear fixtures for fresh CPU integration; never execute them."""
from pathlib import Path
import argparse
import json
import subprocess
import struct
import sys
if not __package__:
    here = Path(__file__).resolve().parent
    sys.path[:] = [p for p in sys.path if Path(p or '.').resolve() != here]
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.fex.common import REPO, need, sha256
from tools.fex.reconstruct import save

CASES = ('api', 'thread', 'invalidation', 'exception', 'context', 'native-owner')


def recipe(case, compiler, wire, output):
    need(case in CASES, 'integration_fixture_case')
    if case == 'native-owner':
        sources = [REPO / 'tests/fex/memory' / name for name in ('wine_owner.c', 'fixture_suite.c')]
        args = ['--target=aarch64-w64-windows-gnu', '-std=c11', '-O1', '-static',
                '-I' + str(wire), '-I' + str(REPO / 'tests/fex/memory')]
        libraries = ['-lkernel32']
    else:
        sources = [REPO / 'tests/fex' / ('guest_' + case + '.c')]
        args = ['--target=x86_64-w64-windows-gnu', '-O2', '-ffreestanding', '-fno-builtin',
                '-std=c11', '-nostdlib', '-Wl,--entry,pear_first_dispatch', '-Wl,--subsystem,console']
        libraries = ['-lntdll'] if case == 'api' else ['-lkernel32', '-lntdll']
    return ['/usr/bin/arch', '-arm64', str(compiler), *args, *map(str, sources),
            *libraries, '-o', str(output / 'first-dispatch.exe')], sources


def verify(root):
    value = json.loads((root / 'control.json').read_text())
    need(value['kind'] == 'fresh_original_fixture' and value['passed'] is True and
         value['guest_execution'] is False and value['producer_sha256'] == sha256(Path(__file__)),
         'integration_fixture_scope')
    argv, sources = recipe(value['case'], Path(value['compiler']), Path(value['wire']), root)
    need(value['argv'] == argv and value['source_sha256'] == {str(p): sha256(p) for p in sources} and
         value['compiler_sha256'] == sha256(Path(value['compiler']).resolve(strict=True)) and
         value['wire_sha256'] == sha256(Path(value['wire']) / 'wine/pear_fex_memory.h'),
         'integration_fixture_inputs_changed')
    need(value['exit_code'] == 0 and value['pe_sha256'] == sha256(root / 'first-dispatch.exe'),
         'integration_fixture_output_changed')
    raw = (root / 'first-dispatch.exe').read_bytes()
    need(raw[:2] == b'MZ' and len(raw) >= 128, 'integration_fixture_pe')
    offset = struct.unpack_from('<I', raw, 60)[0]
    need(raw[offset:offset+4] == b'PE\0\0' and
         struct.unpack_from('<H', raw, offset+4)[0] ==
         (0xaa64 if value['case'] == 'native-owner' else 0x8664), 'integration_fixture_architecture')
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=CASES, required=True)
    for name in ('compiler', 'wire', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    root = args.output.absolute()
    need(root.parent == REPO / '.build/task5' and not root.exists(), 'integration_fixture_output')
    compiler, wire = args.compiler.absolute(), args.wire.absolute()
    argv, sources = recipe(args.case, compiler, wire, root)
    root.mkdir()
    value = dict(kind='fresh_original_fixture', passed=False, case=args.case, argv=argv,
                 compiler=str(compiler), wire=str(wire), compiler_sha256=sha256(compiler.resolve(strict=True)),
                 wire_sha256=sha256(wire / 'wine/pear_fex_memory.h'),
                 producer_sha256=sha256(Path(__file__)), source_sha256={str(p): sha256(p) for p in sources},
                 expected_exit=68 if args.case == 'native-owner' else 42, guest_execution=False)
    try:
        result = subprocess.run(argv, capture_output=True, timeout=120)
        (root / 'stdout.log').write_bytes(result.stdout)
        (root / 'stderr.log').write_bytes(result.stderr)
        value['exit_code'] = result.returncode
        need(result.returncode == 0, 'integration_fixture_compile')
        value.update(passed=True, pe_sha256=sha256(root / 'first-dispatch.exe'))
    finally:
        save(root / 'control.json', value)
    verify(root)
    print(json.dumps({'passed': True, 'case': args.case, 'guest_execution': False}))


if __name__ == '__main__':
    main()
