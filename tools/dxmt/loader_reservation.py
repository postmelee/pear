"""Source-bound, loader-only ARM64 heap reservation on the retained Wine port.

Reuse Wine's zero-fill reservation, the exact-context patch reader and bounded
command supervisor. This adds no allocator, translated execution or new grant.
"""
from pathlib import Path
import argparse
import fcntl
import hashlib
import json
import re
import shlex
import shutil
import stat
import struct

PATCH = 'runtime/wine/patches/0004-arm64-native-heap-reservation.patch'
SOURCE = 'tools/dxmt/loader_reservation.py'
KIND = 'wine_arm64_loader_reservation_build'
ORIGIN = 'source-built-arm64-loader-reservation'
BASE_SOURCE = '8b8ac735e36de1a7d16b0bf2570e2fe657b741b113047331ecb54d475ba58bec'
INPUTS = ('source/loader/main.c', 'source/loader/main.h',
          'source/include/wine/pear_bootstrap.h', 'source/include/wine/pear_stage3.h',
          'objects/Makefile', 'objects/include/config.h', 'objects/loader/main.o',
          'objects/loader/wine_info.plist', 'objects/loader/wine',
          'install/lib/wine/aarch64-unix/wine')
OUTPUTS = ('main.c', 'control/main.o', 'control/wine', 'first/main.o',
           'first/wine', 'second/main.o', 'second/wine')
FIELDS = {'schema_version', 'record_kind', 'baseline_ref', 'producers', 'inputs',
          'commands', 'outputs', 'layout', 'unsigned_equal', 'runtime_eligible',
          'execution_performed', 'game_qualified'}


def need(value, code):
    if not value:
        raise ValueError(code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def sources(adapter):
    return {name: digest(adapter.source_read(adapter.repo, name)) for name in (SOURCE, PATCH)}


def facts(root, names, adapter):
    result = {}
    for name in names:
        raw = adapter.common.read_relative(root, name, 64 * 1024**2)
        mode = stat.S_IMODE((root / name).stat().st_mode)
        result[name] = {'sha256': digest(raw), 'size_bytes': len(raw), 'mode': mode}
    return result


def layout(raw):
    need(len(raw) >= 32, 'loader_macho_header')
    magic, cpu, subtype, kind, count, size, flags, reserved = struct.unpack_from('<8I', raw)
    need(magic == 0xfeedfacf and cpu == 0x100000c and kind == 2 and flags & 0x200000,
         'loader_arm64_pie_required')
    need(count <= 256 and size <= len(raw) - 32, 'loader_commands_bound')
    segments, pos = [], 32
    for _ in range(count):
        need(pos + 8 <= 32 + size, 'loader_command_bound')
        cmd, length = struct.unpack_from('<II', raw, pos)
        need(length >= 8 and length % 8 == 0 and pos + length <= 32 + size,
             'loader_command_size')
        if cmd == 0x19:
            need(length >= 72, 'loader_segment_size')
            name = raw[pos + 8:pos + 24].split(b'\0')[0].decode('ascii')
            address, vmsize, offset, filesize, maximum, initial, sections, sf = struct.unpack_from('<4Q4I', raw, pos + 24)
            need(offset + filesize <= len(raw) and address + vmsize < 2**64,
                 'loader_segment_bound')
            segments.append({'name': name, 'address': address, 'size': vmsize,
                             'offset': offset, 'file_bytes': filesize,
                             'maximum': maximum, 'initial': initial})
        pos += length
    need(pos == 32 + size, 'loader_commands_end')
    need([s['name'] for s in segments] ==
         ['__PAGEZERO', '__TEXT', '__DATA_CONST', '__DATA', 'WINE_RESERVE', '__LINKEDIT'],
         'loader_segment_set')
    zero, text, const, data, reserve, linkedit = segments
    need(zero['address'] == 0 and zero['size'] == 0x10000 and
         zero['file_bytes'] == zero['initial'] == zero['maximum'] == 0,
         'loader_null_guard')
    need(text['address'] == 0x10000 and text['offset'] == 0 and text['initial'] == 5,
         'loader_text_layout')
    need(all(a['address'] + a['size'] == b['address'] for a, b in zip(segments, segments[1:])),
         'loader_low_address_hole')
    need(reserve['file_bytes'] == 0 and reserve['size'] == 0xffff0000 and
         reserve['address'] < 0x100000 and linkedit['address'] >= 0x100000000 and
         linkedit['address'] + linkedit['size'] < 0x180000000,
         'loader_reservation_layout')
    return {'arm64': True, 'pie': True, 'segments': segments}


def baseline_inputs(baseline, adapter):
    builder = adapter.capture.load('tools/dxmt/pairing_build.py')
    reader = adapter.capture.load('tools/dxmt/pairing_check.py')
    value = builder.source_baseline(baseline)
    lock, config = reader.wine_inputs(value, adapter.repo)
    reader.external_native_tools(lock)
    observed = facts(baseline, INPUTS, adapter)
    need(observed['source/loader/main.c']['sha256'] == BASE_SOURCE and
         observed['objects/Makefile']['sha256'] == value['makefile_sha256'] and
         observed['objects/loader/wine']['sha256'] ==
         observed['install/lib/wine/aarch64-unix/wine']['sha256'], 'loader_baseline_changed')
    return value, lock, observed


def patched_source(baseline, adapter):
    reader = adapter.capture.load('tools/dxmt/pairing_source.py')
    patch = adapter.source_read(adapter.repo, PATCH)
    sections = reader.patch_sections(patch)
    need(set(sections) == {'loader/main.c'}, 'loader_patch_scope')
    original = adapter.common.read_relative(baseline, 'source/loader/main.c')
    need(digest(original) == BASE_SOURCE, 'loader_source_baseline')
    return reader.apply_hunks(original, sections['loader/main.c'], 'loader/main.c')


def recipes(root, baseline, adapter, lock):
    make = adapter.common.read_relative(baseline, 'objects/Makefile', 64 * 1024**2).decode()
    variables = {}
    for key in ('CC', 'CFLAGS', 'LDFLAGS'):
        rows = re.findall(r'^' + key + r' = (.*)$', make, re.M)
        need(len(rows) == 1, 'loader_make_variable')
        variables[key] = rows[0]
    def recipe(target, output):
        lines = make.splitlines()
        positions = [i for i, line in enumerate(lines[:-1])
                     if line.startswith(target + ':') and lines[i + 1].startswith('\t')]
        need(len(positions) == 1, 'loader_make_target')
        i = positions[0] + 1
        while i < len(lines) and not lines[i].startswith('\t'):
            i += 1
        need(i < len(lines), 'loader_make_recipe')
        text = lines[i].strip()
        while text.endswith('\\'):
            i += 1
            text = text[:-1] + ' ' + lines[i].strip()
        text = text.replace('$@', shlex.quote(str(output)))
        for key, value in variables.items():
            text = text.replace('$(' + key + ')', value)
        need('$' not in text, 'loader_unknown_make_variable')
        return shlex.split(text)
    cc = next(row['path'] for row in lock['native_tools'] if row['id'] == 'clang')
    env = {'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C', 'TMPDIR': str(root / 'tmp'),
           'SDKROOT': lock['sdk']['path'], 'MACOSX_DEPLOYMENT_TARGET': lock['sdk']['version']}
    result = []
    for name in ('control', 'first', 'second'):
        compile_args = recipe('loader/main.o', root / name / 'main.o')
        link_args = recipe('loader/wine', root / name / 'wine')
        need(compile_args[0] == link_args[0] == cc and '-fPIE' in compile_args and
             compile_args.count('../source/loader/main.c') == 1 and link_args.count('loader/main.o') == 1,
             'loader_recipe_scope')
        if name != 'control':
            compile_args[compile_args.index('../source/loader/main.c')] = str(root / 'main.c')
            compile_args += ['-iquote', str(baseline / 'source/loader')]
            link_args[link_args.index('loader/main.o')] = str(root / name / 'main.o')
            link_args += ['-Wl,-no_huge,-no_fixup_chains']
        for suffix, args in [('compile', compile_args), ('link', link_args)]:
            result.append({'id': name + '.' + suffix, 'argv': args,
                           'cwd': str(baseline / 'objects'), 'environment': env})
    return result


def verify(root, adapter, expected_baseline=None):
    root = adapter.common.owned_directory(root, adapter.repo)
    need(not (root / 'failed.json').exists(), 'loader_failed_build')
    value = adapter.common.decode_json(adapter.common.read_relative(root, 'loader.json'))
    need(set(value) == FIELDS and value['schema_version'] == 1 and value['record_kind'] == KIND,
         'loader_record_fields')
    ref = value['baseline_ref']
    need(type(ref) is dict and set(ref) == {'path', 'sha256'}, 'loader_baseline_ref')
    baseline = Path(ref['path']).resolve(strict=True)
    if expected_baseline is not None:
        need(baseline == expected_baseline, 'loader_wrong_baseline')
    need(digest(adapter.common.read_relative(baseline, 'build.json')) == ref['sha256'],
         'loader_baseline_receipt')
    _, lock, observed = baseline_inputs(baseline, adapter)
    need(value['inputs'] == observed and value['producers'] == sources(adapter), 'loader_inputs_changed')
    for name, pin in value['producers'].items():
        need(digest(adapter.common.read_relative(root, 'producers/' + name)) == pin, 'loader_producer_copy')
    need(adapter.common.read_relative(root, 'main.c') == patched_source(baseline, adapter), 'loader_patch_result')
    expected = recipes(root, baseline, adapter, lock)
    need(type(value['commands']) is list and len(value['commands']) == len(expected), 'loader_command_count')
    for row, wanted in zip(value['commands'], expected):
        need(set(row) == set(wanted) | {'exit_code', 'logs'} and all(row[k] == v for k, v in wanted.items())
             and type(row['exit_code']) is int and row['exit_code'] == 0, 'loader_command_recipe')
        need(set(row['logs']) == {'stdout', 'stderr'}, 'loader_log_set')
        for channel, info in row['logs'].items():
            name = 'logs/' + row['id'] + '/' + channel
            need(info == facts(root, [name], adapter)[name], 'loader_log_changed')
            need(info['size_bytes'] <= 2**20, 'loader_log_bound')
    outputs = facts(root, OUTPUTS, adapter)
    need(value['outputs'] == outputs and outputs['control/main.o'] == observed['objects/loader/main.o']
         and outputs['control/wine'] == observed['objects/loader/wine'], 'loader_control_reproduction')
    need(outputs['first/main.o'] == outputs['second/main.o'] and outputs['first/wine'] == outputs['second/wine']
         and value['unsigned_equal'] is True, 'loader_unsigned_difference')
    actual_layout = layout(adapter.common.read_relative(root, 'second/wine'))
    need(value['layout'] == actual_layout and all(value[key] is False for key in
         ('runtime_eligible', 'game_qualified', 'execution_performed')), 'loader_scope')
    return value


def build(baseline, output, adapter):
    baseline = Path(baseline).resolve(strict=True)
    _, lock, before = baseline_inputs(baseline, adapter)
    need(shutil.disk_usage(adapter.repo).free >= 4 * 1024**3, 'loader_storage')
    root = adapter.common.output_directory(output, adapter.repo)
    commands = []
    try:
        for name in ('tmp', 'control', 'first', 'second'):
            (root / name).mkdir(mode=0o700)
        current = sources(adapter)
        for name in current:
            target = root / 'producers' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(adapter.source_read(adapter.repo, name)); target.chmod(0o644)
        (root / 'main.c').write_bytes(patched_source(baseline, adapter)); (root / 'main.c').chmod(0o644)
        for row in recipes(root, baseline, adapter, lock):
            directory = root / 'logs' / row['id']; directory.mkdir(parents=True)
            result = adapter.common.run_bounded(row['argv'], cwd=row['cwd'], env=row['environment'],
                                               timeout=60, limit=2**20, log_directory=directory)
            observed = dict(row, exit_code=result['exit_code'], logs={})
            for channel in ('stdout', 'stderr'):
                name = 'logs/' + row['id'] + '/' + channel
                observed['logs'][channel] = facts(root, [name], adapter)[name]
            commands.append(observed)
            need(result['exit_code'] == 0, 'loader_command_failed')
        need(before == facts(baseline, INPUTS, adapter) and current == sources(adapter), 'loader_inputs_mutated')
        value = {'schema_version': 1, 'record_kind': KIND,
                 'baseline_ref': {'path': str(baseline), 'sha256': digest(adapter.common.read_relative(baseline, 'build.json'))},
                 'producers': current, 'inputs': before, 'commands': commands,
                 'outputs': facts(root, OUTPUTS, adapter), 'layout': layout((root / 'second/wine').read_bytes()),
                 'unsigned_equal': (root / 'first/wine').read_bytes() == (root / 'second/wine').read_bytes(),
                 'execution_performed': False, 'runtime_eligible': False, 'game_qualified': False}
        adapter.common.write_new(root / 'loader.json', value)
        return verify(root, adapter, baseline)
    except BaseException as error:
        adapter.common.write_new(root / 'failed.json', {'error': str(error), 'commands': commands,
                                                       'runtime_eligible': False})
        raise


def main():
    from tools.dxmt import deterministic_native as native
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True); parser.add_argument('--constructor-root', required=True)
    parser.add_argument('--baseline'); parser.add_argument('--output', required=True)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    with native.adapter(args.repo, args.constructor_root) as adapter:
        if args.verify:
            result = verify(args.output, adapter)
        else:
            need(args.baseline, 'loader_baseline_required')
            with open('/private/tmp/pear-native-compilation.lock', 'a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                result = build(args.baseline, args.output, adapter)
        print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
