"""Assess scoped Wine input, build and native bootstrap evidence; no game qualification."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

from common import Error, REPO, encoded, load_json, need, record, sha256
from prepare import validate_inputs, verify_prepared
from toolchain import TARGETS, coff_machine, inspect_closure, inspect_macho, inspect_sdk, native_tool, verify_prepared_tools

TARGET_NAMES = ('aarch64', 'arm64ec', 'x86_64', 'i686')
FRAMEWORKS = {'AppKit', 'Carbon', 'Foundation', 'IOKit', 'Metal', 'OpenGL',
              'QuartzCore', 'Security', 'CoreText', 'CoreFoundation', 'CoreServices',
              'DiskArbitration', 'SystemConfiguration', 'ApplicationServices'}
NATIVE_OUTPUT = '{"fixture":"pear-toolchain-native-v1","value":42}\n'


def required_checks():
    result = {'native', 'frameworks', 'bison', 'configure.arm64', 'configure.arm64ec-build', 'arm64ec.support'}
    for target in TARGET_NAMES:
        result.update(target + '.' + kind for kind in
                      ('compile', 'cxx', 'link', 'imports', 'exports', 'resources',
                       'assembly' if target == 'i686' else 'unwind'))
    return result


def indexed(rows, name):
    need(isinstance(rows, list) and len(rows) <= 1024, name + '_shape')
    result = {}
    for row in rows:
        need(isinstance(row, dict) and isinstance(row.get('id'), str), name + '_shape')
        need(row['id'] not in result, name + '_duplicate')
        result[row['id']] = row
    return result


def assess_report(report, lock_digest, config_digest):
    """Require observed fields and command outcomes; ignore a claimed success flag."""
    record(report, 'wine_toolchain_check')
    need(report.get('lock_sha256') == lock_digest, 'toolchain_lock_mismatch')
    need(report.get('config_sha256') == config_digest, 'configuration_mismatch')
    need(report.get('pe_execution') is False and report.get('wine_runtime_execution') is False,
         'execution_scope_mismatch')
    checks = indexed(report.get('checks'), 'checks')
    need(set(checks) == required_checks(), 'required_checks_incomplete')
    need(all(x.get('status') == 'passed' and isinstance(x.get('details'), dict)
             for x in checks.values()), 'required_check_failed')
    commands = indexed(report.get('commands'), 'commands')
    expected_commands = {'compiler.version', 'native.compile', 'native.run', 'frameworks.link', 'bison.version',
                         'arm64ec.support.inspect'}
    for target in TARGET_NAMES:
        expected_commands.update(target + '.' + suffix for suffix in (
            'main.obj', 'dll.obj', 'cpp.obj', 'assemble', 'unwind.inspect',
            'resource.compile', 'dll.link', 'importlib', 'exe.link',
            'imports.inspect', 'exports.inspect', 'resources.inspect'))
    for variant in ('arm64', 'arm64ec-build'):
        expected_commands.update(('configure.' + variant, 'configure.' + variant + '.make-query'))
    need(expected_commands == set(commands), 'required_commands_incomplete')
    for command in commands.values():
        need(type(command.get('exit_code')) is int and command['exit_code'] == 0
             and command.get('timed_out') is False and command.get('output_limit') is False,
             'command_did_not_pass')
        need(all(isinstance(command.get(stream), str) and
                 len(command[stream].encode('utf-8')) <= 4 * 256 * 1024
                 for stream in ('stdout', 'stderr')), 'command_output_shape')
    need(commands['native.run']['stdout'] == NATIVE_OUTPUT and
         commands['native.run']['stderr'] == '', 'native_result_mismatch')
    need(checks['native']['details'].get('architectures') == [0x0100000c], 'native_architecture')
    need(checks['frameworks']['details'].get('executed') is False, 'framework_execution_scope')
    deps = checks['frameworks']['details'].get('dependencies')
    need(isinstance(deps, list) and all(isinstance(x, str) for x in deps), 'framework_dependencies')
    need(all(any('/' + framework + '.framework/' in d for d in deps)
             for framework in FRAMEWORKS), 'framework_dependency_missing')
    for target in TARGET_NAMES:
        object_machine = TARGETS[target][1]
        expected_pe = 0x8664 if target == 'arm64ec' else object_machine
        need(checks[target + '.compile']['details'].get('machine') == object_machine,
             'coff_machine_mismatch')
        linked = checks[target + '.link']['details']
        need(linked.get('pe_machine') == expected_pe and linked.get('executed') is False,
             'pe_machine_or_scope_mismatch')
        need('pear-toolchain.dll' in commands[target + '.imports.inspect']['stdout'] and
             'pear_toolchain_add' in commands[target + '.imports.inspect']['stdout'], 'missing_import')
        need('pear_toolchain_add' in commands[target + '.exports.inspect']['stdout'], 'missing_export')
        resource = ''.join(commands[target + '.resources.inspect']['stdout'].upper().split())
        need('101' in resource and '504541522A00' in resource, 'missing_resource')
        if target != 'i686':
            need('RuntimeFunction' in commands[target + '.unwind.inspect']['stdout'], 'missing_unwind')
    metadata = commands['arm64ec.support.inspect']['stdout']
    pointers = re.findall(r'CHPEMetadataPointer:\s*0x([0-9a-fA-F]+)', metadata)
    need(len(pointers) == 2 and all(int(value, 16) > 0 for value in pointers)
         and checks['arm64ec.support']['details'].get('output') == metadata, 'arm64ec_metadata_missing')
    need(re.search(r'\bbison \(GNU Bison\) 3\.8\.2(?:\s|$)', commands['bison.version']['stdout']), 'bison_version')
    need(re.search(r'\bclang version 23\.1\.1(?:\s|$)', commands['compiler.version']['stdout']), 'compiler_baseline_mismatch')
    return checks, commands


def owned(path):
    path = Path(path)
    resolved = path.resolve()
    need(resolved.is_relative_to(REPO / '.build/task4') and path.is_file()
         and not path.is_symlink(), 'unowned_evidence_path')
    return resolved


def verify_command_logs(report, work):
    """Bind bounded local logs to their expected roles; this is not authentication."""
    import hashlib
    from common import read_relative

    task_root = (REPO / '.build/task4').resolve()
    work = Path(work)
    need(work.is_absolute() and work == work.resolve() and work.is_relative_to(task_root),
         'command_work_scope')
    for ident, command in indexed(report.get('commands'), 'commands').items():
        need(0 < len(ident) <= 128 and all(c.isascii() and (c.isalnum() or c in '._-')
                                         for c in ident), 'command_identifier')
        need(isinstance(command.get('argv'), list) and
             command['argv'][:2] == ['/usr/bin/arch', '-arm64'], 'command_architecture_scope')
        cwd = work
        if ident.startswith('configure.'):
            parts = ident.split('.')
            need(len(parts) in (2, 3) and parts[1] in ('arm64', 'arm64ec-build')
                 and (len(parts) == 2 or parts[2] == 'make-query'), 'command_directory_role')
            cwd = work / ('configure-' + parts[1])
        raw_cwd = command.get('cwd')
        need(isinstance(raw_cwd, str) and Path(raw_cwd).is_absolute()
             and Path(raw_cwd).resolve() == cwd, 'command_directory_scope')
        for stream in ('stdout', 'stderr'):
            metadata = command.get(stream + '_log')
            need(isinstance(metadata, dict), 'command_log_shape')
            expected = cwd / '.pear-command-logs' / (ident + '.' + stream)
            raw_path = metadata.get('path')
            need(isinstance(raw_path, str) and Path(raw_path).is_absolute()
                 and Path(raw_path).resolve() == expected, 'command_log_path')
            # Read only the canonical expected path, never a caller-selected file.
            # Descriptor-relative opening rejects aliases beneath the owned root.
            try:
                data = read_relative(task_root, expected.relative_to(task_root).as_posix(),
                                     limit=256 * 1024)
            except OSError:
                raise Error('command_log_unavailable') from None
            need(type(metadata.get('size_bytes')) is int
                 and len(data) == metadata['size_bytes']
                 and hashlib.sha256(data).hexdigest() == metadata.get('sha256'),
                 'command_log_identity')
            need(command.get(stream) == data[:16000].decode('utf-8', errors='replace')
                 and command.get(stream + '_preview_truncated') is (len(data) > 16000),
                 'command_log_preview')


def verify_fixture_set(hashes, fixtures):
    """Later-stage additions do not retroactively invalidate compiler fixtures."""
    required = {'toolchain_native.c', 'toolchain_pe.c', 'toolchain_seh.S', 'toolchain_cpp.cpp'}
    need(isinstance(hashes, dict) and required.issubset(hashes), 'fixture_identity_mismatch')
    for name, digest in hashes.items():
        need(isinstance(name, str) and Path(name).name == name and name not in ('.', '..'),
             'fixture_identity_mismatch')
        need(sha256(Path(fixtures) / name) == digest, 'fixture_identity_mismatch')


def validate_stage1(inputs_path, config_path, report_path):
    inputs_path, config_path, report_path = map(Path, (inputs_path, config_path, report_path))
    inputs = record(load_json(inputs_path), 'wine_build_inputs')
    source = validate_inputs(inputs)
    config = record(load_json(config_path), 'wine_build_config')
    need(config.get('scope') == 'wine_component' and config.get('host_architecture') == 'arm64',
         'configuration_scope')
    variants = indexed(config.get('variants'), 'variants')
    need(set(variants) == {'arm64', 'arm64ec-build'} and
         variants['arm64'].get('pe_archs') == ['aarch64'] and
         variants['arm64ec-build'].get('pe_archs') == ['aarch64', 'arm64ec'], 'variant_matrix')
    need(set(config.get('frameworks', [])) == FRAMEWORKS, 'framework_matrix')
    need(config.get('qualification') == {'runtime': 'unassessed', 'game': 'unassessed',
                                       'distribution': 'unassessed'}, 'qualification_promotion')
    lock_path = REPO / 'runtime/wine/toolchain.json'
    lock = record(load_json(lock_path), 'wine_toolchain')
    dependencies = indexed(inputs['dependencies'], 'dependencies')
    need({'wine-source', 'apple-sdk', 'llvm-mingw', 'bison-source', 'native-tools',
          'optional-features'} <= set(dependencies), 'dependency_matrix_incomplete')
    need(dependencies['apple-sdk'].get('version') == config.get('sdk_version') == lock['sdk']['version']
         and set(dependencies['apple-sdk'].get('frameworks', [])) == FRAMEWORKS,
         'sdk_dependency_matrix')
    need(set(dependencies['optional-features'].get('features', [])) == set(config.get('disabled_features', [])),
         'optional_feature_matrix')
    for ident, variant in variants.items():
        expected_args = ['--enable-archs=' + ','.join(variant['pe_archs']), '--disable-tests', '--disable-win16']
        expected_args += ['--without-' + name for name in config['disabled_features']]
        need(variant.get('configure_args') == expected_args, 'configure_argument_matrix')
    report = record(load_json(owned(report_path)), 'wine_toolchain_check')
    checks, commands = assess_report(report, sha256(lock_path), sha256(config_path))
    need(report.get('sdk') == inspect_sdk(lock), 'sdk_identity_mismatch')
    need(report.get('producer_sha256') == {name: sha256(REPO / 'tools/wine' / name)
         for name in ('toolchain.py', 'common.py', 'prepare.py')}, 'producer_identity_mismatch')
    fixtures = REPO / 'tests/wine/fixtures'
    verify_fixture_set(report.get('fixture_hashes'), fixtures)
    source_record_path = owned(report.get('source_prepared_path', ''))
    need(sha256(source_record_path) == report.get('source_prepared_sha256'), 'source_prepared_mismatch')
    prepared = verify_prepared(source_record_path.parent, sha256(inputs_path))
    need(prepared.get('inputs_ref', {}).get('sha256') == sha256(inputs_path)
         and prepared.get('audit_ref') == inputs['audit_ref'], 'prepared_input_binding')
    for component in prepared.get('components', []):
        expected = next((x for x in inputs['components'] if x['id'] == component.get('id')), None)
        need(expected is not None and component.get('commit') == expected['commit']
             and component.get('tree') == expected['tree'], 'prepared_source_binding')
        manifest = owned(source_record_path.parent / component['files_manifest']['path'])
        need(sha256(manifest) == component['files_manifest']['sha256'], 'prepared_manifest_mismatch')
    need(report.get('inputs_sha256') == sha256(inputs_path)
         and report.get('source_manifest_sha256') == prepared['components'][0]['files_manifest']['sha256'],
         'source_report_binding')
    tools = indexed(report.get('tools'), 'tools')
    need(set(tools) == {'clang', 'lld-link', 'llvm-readobj', 'llvm-rc', 'llvm-dlltool'}, 'tool_coverage')
    tool_root = Path(tools['clang']['path']).parents[2].resolve()
    need(tool_root.is_relative_to(REPO / '.build/task4'), 'unowned_tool_root')
    for ident, tool in tools.items():
        path = tool_root / 'llvm-mingw/bin' / ident
        resolved = path.resolve()
        need(Path(tool['path']) == path and resolved.is_relative_to(tool_root / 'llvm-mingw')
             and tool.get('resolved_path') == str(resolved) and sha256(resolved) == tool['sha256'],
             'tool_identity_mismatch')
        need(inspect_closure(path, tool_root / 'llvm-mingw') == tool.get('closure'), 'tool_library_mismatch')
    tool_prepared = owned(tool_root / 'prepared.json')
    need(sha256(tool_prepared) == report.get('prepared_sha256'), 'prepared_tools_mismatch')
    prepared_tools = verify_prepared_tools(lock, tool_root)
    build_commands = indexed(prepared_tools.get('commands'), 'bison_commands')
    need(set(build_commands) == {'bison.configure', 'bison.build', 'bison.install'}, 'bison_build_evidence_missing')
    for command in build_commands.values():
        need(type(command.get('exit_code')) is int and command['exit_code'] == 0
             and command.get('timed_out') is False and command.get('output_limit') is False
             and command.get('argv', [])[:2] == ['/usr/bin/arch', '-arm64'], 'bison_build_evidence_invalid')
    need(prepared_tools.get('lock_sha256') == sha256(lock_path), 'prepared_tool_lock_mismatch')
    bison = owned(tool_root / 'bison/bin/bison')
    need(sha256(bison) == prepared_tools['bison']['sha256'] == checks['bison']['details']['sha256'],
         'derived_bison_mismatch')
    need(inspect_macho(bison)['architectures'] == [0x0100000c], 'bison_architecture')
    support = checks['arm64ec.support']['details'].get('archive', {})
    support_path = 'aarch64-w64-mingw32/lib/libmingwex.a'
    library = owned(tool_root / 'llvm-mingw' / support_path)
    need(support.get('path') == support_path and support.get('sha256') == sha256(library)
         and support.get('size_bytes') == library.stat().st_size, 'arm64ec_support_identity')
    for native in lock['native_tools']:
        native_tool(lock, native['id'])
    work = report_path.resolve().with_suffix('.work')
    verify_command_logs(report, work)
    artifact_results = []
    expected_artifacts = {'native': ['native'], 'frameworks': ['frameworks']}
    for target in TARGET_NAMES:
        expected_artifacts.update({target + '.compile': ['main.obj', 'dll.obj'],
            target + '.cxx': ['cpp.obj'],
            target + ('.assembly' if target == 'i686' else '.unwind'): ['seh.obj'],
            target + '.link': ['fixture.exe', 'pear-toolchain.dll'],
            target + '.imports': ['fixture.lib'], target + '.resources': ['fixture.res']})
    for ident, names in expected_artifacts.items():
        details = checks[ident]['details']
        entries = details.get('artifacts', [details.get('artifact')])
        need(isinstance(entries, list) and len(entries) == len(names), 'output_artifact_count')
        for entry, name in zip(entries, names):
            need(isinstance(entry, dict), 'output_artifact_shape')
            target = ident.split('.')[0]
            path = owned(work / target / name if target in TARGET_NAMES else work / name)
            digest = sha256(path)
            need(entry.get('path') == str(path) and entry.get('sha256') == digest
                 and entry.get('size_bytes') == path.stat().st_size, 'output_identity_mismatch')
            if name.endswith(('.obj', '.exe', '.dll')):
                expected = 0x8664 if ident.endswith('.link') and target == 'arm64ec' else TARGETS[target][1]
                need(coff_machine(path) == expected, 'output_machine_mismatch')
            elif target not in TARGET_NAMES:
                need(inspect_macho(path)['architectures'] == [0x0100000c], 'output_native_architecture')
            artifact_results.append({'id': ident + '/' + name, 'sha256': digest})
    for variant in variants:
        detail = checks['configure.' + variant]['details']
        for filename, key in [('Makefile', 'makefile_sha256'), ('config.log', 'config_log_sha256')]:
            need(sha256(owned(work / ('configure-' + variant) / filename)) == detail.get(key),
                 'configure_output_mismatch')
    return {'schema_version': 1, 'record_kind': 'wine_input_assessment', 'scope': 'wine_component',
            'requested_gate': 'stage1_inputs_and_toolchain', 'gate_passed': True,
            'inputs_sha256': sha256(inputs_path), 'config_sha256': sha256(config_path),
            'toolchain_lock_sha256': sha256(lock_path), 'toolchain_evidence_sha256': sha256(report_path),
            'source_prepared_sha256': sha256(source_record_path),
            'source_manifest_sha256': prepared['components'][0]['files_manifest']['sha256'],
            'tool_prepared_sha256': sha256(tool_prepared),
            'audit_ref': inputs['audit_ref'], 'original_audit_decision': source['audit']['decision'],
            'checks_passed': len(checks), 'commands_passed': len(commands),
            'artifacts': artifact_results, 'source_ports_complete': False,
            'qualification': {'runtime': 'unassessed', 'game': 'unassessed', 'distribution': 'unassessed'}}


def validate_builds(root, companion):
    """Recheck both concrete builds, with matching approved sources and settings."""
    from build import artifact_inventory, verify_build
    from modules import validate_inventory
    roots = [Path(root).resolve(), Path(companion).resolve()]
    need(roots[0] != roots[1], 'build_variants_not_distinct')
    builds = [verify_build(path) for path in roots]
    need([row['variant'] for row in builds] == ['arm64', 'arm64ec-build'], 'build_variant_matrix')
    for key in ('record_hashes', 'source_prepared_sha256', 'tool_prepared_sha256',
                'source_manifest', 'patches', 'fixture_hashes', 'sdk'):
        need(builds[0][key] == builds[1][key], 'build_variant_inputs_differ')
    variants = []
    for path, built in zip(roots, builds):
        validate_inventory(path, verified_build=built)
        artifacts = artifact_inventory(built, path)['files']
        native = [item for item in artifacts if item['kind'] == 'macho']
        guests = [item for item in artifacts if item['kind'] == 'pe']
        need(built['native_artifact_count'] == len(native) and built['pe_artifact_count'] == len(guests),
             'build_artifact_count_mismatch')
        variants.append({'variant': built['variant'], 'build_sha256': sha256(path / 'build.json'),
                         'installed_manifest_sha256': built['artifacts_manifest']['sha256'],
                         'producer_sha256': built['producer_sha256'],
                         'completion_revision': built.get('completion_revision'),
                         'native_artifact_count': len(native), 'pe_artifact_count': len(guests),
                         'pe_metadata_count': sum(item['kind'] == 'pe_metadata' for item in artifacts),
                         'native_architecture': 'arm64', 'wine_runtime_execution': False,
                         'module_inventory_sha256': sha256(path / 'modules.json')})
    return {'schema_version': 1, 'record_kind': 'wine_build_assessment', 'scope': 'wine_component',
            'requested_gate': 'stage2_native_and_companion_builds', 'gate_passed': True,
            'variants': variants, 'record_hashes': builds[0]['record_hashes'],
            'patched_source_manifest_sha256': builds[0]['source_manifest']['sha256'],
            'source_ports_complete': False,
            'qualification': {'runtime': 'unassessed', 'game': 'unassessed', 'distribution': 'unassessed'}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    inputs = sub.add_parser('inputs')
    inputs.add_argument('--inputs', required=True)
    inputs.add_argument('--config', required=True)
    inputs.add_argument('--toolchain', required=True)
    inputs.add_argument('--require-complete', action='store_true', required=True)
    builds = sub.add_parser('build')
    builds.add_argument('--root', required=True)
    builds.add_argument('--companion', required=True)
    builds.add_argument('--require-complete', action='store_true', required=True)
    runs = sub.add_parser('runs')
    runs.add_argument('--root', required=True)
    runs.add_argument('--suite', choices=('bootstrap',), required=True)
    runs.add_argument('--require-complete', action='store_true', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'inputs':
            result = validate_stage1(args.inputs, args.config, args.toolchain)
        elif args.command == 'build':
            result = validate_builds(args.root, args.companion)
        else:
            from run_fixtures import validate_runs
            result = validate_runs(args.root, args.suite)
    except (Error, OSError, ValueError, KeyError, TypeError) as exc:
        print(encoded({'schema_version': 1, 'record_kind': {'inputs': 'wine_input_assessment', 'build': 'wine_build_assessment',
                                       'runs': 'wine_bootstrap_assessment'}[args.command], 'gate_passed': False,
                       'error': getattr(exc, 'code', 'invalid_or_missing_evidence')}).decode(), end='')
        return 3 if isinstance(exc, Error) else 1
    print(encoded(result).decode(), end='')
    return 0


if __name__ == '__main__':
    sys.exit(main())
