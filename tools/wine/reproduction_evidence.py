"""Bind a fresh, same-host Wine reconstruction to independently checked evidence.

This module neither builds, signs nor runs Wine. Local receipts establish a
controlled reproduction history, not authentication against a hostile owner.
Existing source, tool, build, module, signing and native-fixture validators remain
responsible for their own gates. Partial attempts cannot produce public success.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import sys
import uuid

from common import Error, REPO, decode_json, encoded, need, read_relative, relative, sha256
import stage5_evidence

GIB = 1024 ** 3
MINIMUM_FREE_BYTES = 26 * GIB
OPERATIONS = ('prepare_inputs', 'toolchain_check', 'native_arena',
              'native_reference_build', 'native_reference_modules', 'native_build', 'native_modules', 'native_abi',
              'companion_build', 'companion_modules', 'unsigned_compare', 'signing', 'bootstrap', 'mac_driver')
SOURCES = {**stage5_evidence.SOURCES,
           'reproduction_coordinator': 'tools/wine/reproduce.py',
           'reproduction_validator': 'tools/wine/reproduction_evidence.py',
           'unsigned_comparator': 'tools/wine/unsigned_compare.py',
           'input_and_variant_validator': 'tools/wine/verify.py',
           'module_validator': 'tools/wine/modules.py',
           'native_arena_reconstruction': 'tools/wine/arena_reproduction.py',
           'native_arena_receipt_reader': 'tools/wine/arena_evidence.py',
           'native_arena_probe': 'tools/wine/pe_arena_probe.py',
           'native_arena_fixture': 'tests/wine/fixtures/pe_arena_native.c',
           'profile_validator': 'host/probe/provisioned_probe.py',
           'hardened_signature_validator': 'host/probe/hardened_baseline.py',
           'source_inventory_validator': 'tools/sources/validate_inventory.py',
           'prerequisite_toolchain_lock': 'runtime/wine/toolchain.json'}
PRODUCERS = tuple(sorted(set(SOURCES.values())))
CONFIGURATION = {'inputs': 'runtime/wine/inputs.json', 'config': 'runtime/wine/build-config.json',
                 'toolchain': 'runtime/wine/toolchain.json', 'patch_series': 'runtime/wine/patches/series.json'}
REFERENCE_BUILD = REPO / '.build/task4/build-stage5-attempt6'
REFERENCE_PUBLIC = REPO / 'mydocs/working/task_m1_4_stage5_observations.json'
REFERENCE_BUILD_SHA256 = 'a9d43c3f7fe1f922fba8319dc286b6d456e4dc1a704b2bf7253a125f33de115e'
REFERENCE_PUBLIC_SHA256 = '91540517e5150d26217ba765c65e4b3aa9c15bd9d4cf47f82072a517bfc66c55'
SCOPE = 'same_host_fresh_wine_component_reproduction'
SOURCE_ARGUMENT_POLICY = 'stable_relative_v1'
BUILD_ROLES = (('native_reference_build', 'arm64'), ('native_build', 'arm64'),
               ('companion_build', 'arm64ec-build'))
STORAGE_ESTIMATE = {'unit': 'MiB', 'values_are_approximate': True,
    'measurement_resolution': 'rounded_du_human_readable', 'retained_allocated_native': 3175,
    'native_reference': 3175,
    'retained_allocated_companion': 5632, 'source': 807, 'signed_runtime': 1229,
    'mac_driver_runs': 4404, 'bootstrap_runs': 1,
    'limitation': 'Retained APFS allocation can understate fresh copies; the minimum includes additional headroom.'}


def exact(actual, expected, code):
    need(encoded(actual) == encoded(expected), code)


def _digest(value):
    need(type(value) is str and re.fullmatch('[a-f0-9]{64}', value), 'reproduction_digest')
    return value


def _integer(value, minimum=0, maximum=2**53-1):
    need(type(value) is int and minimum <= value <= maximum, 'reproduction_integer')
    return value


def _path(path):
    path = Path(path).absolute()
    root = REPO.resolve()
    need('..' not in path.parts and path.is_relative_to(root), 'reproduction_path_scope')
    current = root
    for part in relative(path.relative_to(root).as_posix()):
        current /= part
        need(not current.is_symlink(), 'reproduction_symlink')
    return path


def _name(path):
    return _path(path).relative_to(REPO.resolve()).as_posix()


def _identity(path):
    path = _path(path)
    need(path.is_dir(), 'reproduction_directory_missing')
    info = path.stat()
    return {'device': info.st_dev, 'inode': info.st_ino}


def layout(root):
    root = _path(root)
    need(root.parent == REPO.resolve() / '.build/task4' and
         re.fullmatch('[a-z0-9][a-z0-9_-]{0,79}', root.name), 'reproduction_root_scope')
    return {'root': root, 'inputs': root.with_name(root.name + '-inputs'),
            'native_reference_build': root.with_name(root.name + '-anchor6'),
            'native_build': root.with_name(root.name + '-native6'),
            'companion_build': root.with_name(root.name + '-companion6'),
            'toolchain_check': root / 'toolchain.json', 'toolchain_work': root / 'toolchain.work',
            'native_arena': root / 'native-arena',
            'signed': root / 'signed', 'bootstrap': root / 'runs-bootstrap',
            'mac_driver': root / 'runs-mac-driver', 'unsigned_compare': root / 'unsigned-comparison.json'}


def operation_paths(paths):
    """Return fixed record and directory roles; callers cannot supply file paths."""
    return {
        'prepare_inputs': (paths['inputs'] / 'prepared.json', paths['inputs']),
        'toolchain_check': (paths['toolchain_check'], paths['toolchain_work']),
        'native_arena': (paths['native_arena'] / 'reproduction.json', paths['native_arena']),
        'native_reference_build': (paths['native_reference_build'] / 'build.json', paths['native_reference_build']),
        'native_reference_modules': (paths['native_reference_build'] / 'modules.json', paths['native_reference_build']),
        'native_build': (paths['native_build'] / 'build.json', paths['native_build']),
        'native_modules': (paths['native_build'] / 'modules.json', paths['native_build']),
        'native_abi': (paths['native_build'] / 'abi-review.json', paths['native_build']),
        'companion_build': (paths['companion_build'] / 'build.json', paths['companion_build']),
        'companion_modules': (paths['companion_build'] / 'modules.json', paths['companion_build']),
        'unsigned_compare': (paths['unsigned_compare'], paths['root']),
        'signing': (paths['signed'] / 'signed.json', paths['signed']),
        'bootstrap': (paths['bootstrap'] / 'run.json', paths['bootstrap']),
        'mac_driver': (paths['mac_driver'] / 'run.json', paths['mac_driver'])}


def _write_new(path, value):
    with _path(path).open('xb') as stream:
        stream.write(encoded(value))


def _read(path):
    return decode_json(read_relative(REPO, _name(path)))


def source_hashes():
    return {name: sha256(_path(REPO / name)) for name in PRODUCERS}


def _reference():
    need(sha256(_path(REFERENCE_BUILD / 'build.json')) == REFERENCE_BUILD_SHA256 and
         sha256(_path(REFERENCE_PUBLIC)) == REFERENCE_PUBLIC_SHA256, 'reproduction_reference_changed')
    observed = _read(REFERENCE_PUBLIC)
    need(observed.get('record_kind') == 'wine_stage5_observations' and
         observed.get('build', {}).get('build_sha256') == REFERENCE_BUILD_SHA256,
         'reproduction_reference_scope')
    return {'build': {'path': _name(REFERENCE_BUILD / 'build.json'), 'sha256': REFERENCE_BUILD_SHA256},
            'public': {'path': _name(REFERENCE_PUBLIC), 'sha256': REFERENCE_PUBLIC_SHA256}}


def _input_paths(paths, source_cache, tools, local_signing):
    source_cache, tools, local_signing = map(_path, (source_cache, tools, local_signing))
    need(source_cache.is_dir() and tools.is_dir() and local_signing.is_file(), 'reproduction_input_missing')
    need(tools.is_relative_to(REPO.resolve() / '.build/task4') and
         local_signing.is_relative_to(REPO.resolve() / '.build/task4'), 'reproduction_input_scope')
    for source in (source_cache, tools, local_signing, REFERENCE_BUILD):
        need(all(not source.is_relative_to(target) and not target.is_relative_to(source)
                 for target in (paths['root'], paths['inputs'], paths['native_reference_build'], paths['native_build'], paths['companion_build'])),
             'reproduction_input_output_alias')
    return source_cache, tools, local_signing


def create_start(root, *, source_cache, tools, local_signing, jobs=4, required_free_bytes=MINIMUM_FREE_BYTES):
    paths = layout(root)
    root = paths['root']
    need(type(jobs) is int and 1 <= jobs <= 4, 'reproduction_parallelism')
    _integer(required_free_bytes, MINIMUM_FREE_BYTES)
    for value in paths.values():
        _path(value)
    need(not root.exists() or (root.is_dir() and not any(root.iterdir())), 'reproduction_output_not_empty')
    for role, path in paths.items():
        if role != 'root':
            need(not path.exists(), 'reproduction_output_exists')
    source_cache, tools, local_signing = _input_paths(paths, source_cache, tools, local_signing)
    free = shutil.disk_usage(root.parent).free
    need(free >= required_free_bytes, 'reproduction_storage_budget')
    sources = source_hashes()
    configurations = {key: sha256(REPO / name) for key, name in CONFIGURATION.items()}
    reference = _reference()
    tool_hash = sha256(tools / 'prepared.json')
    signing_hash = sha256(local_signing)
    initial_state = 'empty' if root.exists() else 'absent'
    root.mkdir(mode=0o700, exist_ok=True)
    value = {'schema_version': 1, 'record_kind': 'wine_reproduction_start', 'scope': SCOPE,
        'attempt_id': uuid.uuid4().hex, 'root': _name(root), 'root_identity': _identity(root),
        'root_initial_state': initial_state, 'layout': {key: _name(path) for key, path in paths.items()},
        'outputs_initially_absent': [key for key in paths if key != 'root'],
        'configuration_sha256': configurations, 'producer_sha256': sources, 'jobs': jobs,
        'source_cache': _name(source_cache),
        'tool_cache': {'path': _name(tools), 'prepared_sha256': tool_hash, 'reused': True},
        'local_signing': {'path': _name(local_signing), 'sha256': signing_hash},
        'reference': reference,
        'storage': {'free_bytes_before': free, 'required_free_bytes': required_free_bytes,
                    'estimate': dict(STORAGE_ESTIMATE)},
        'qualification': {'runtime': False, 'game': False, 'distribution': False}}
    for name, digest in sources.items():
        destination = root / 'producer' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        raw = read_relative(REPO, name)
        need(hashlib.sha256(raw).hexdigest() == digest, 'reproduction_producer_changed')
        with destination.open('xb') as stream:
            stream.write(raw)
    need(source_hashes() == sources and _reference() == reference and
         sha256(tools / 'prepared.json') == tool_hash and sha256(local_signing) == signing_hash,
         'reproduction_start_changed')
    _write_new(root / 'start.json', value)
    return value


def load_start(root):
    paths = layout(root)
    value = _read(paths['root'] / 'start.json')
    fields = {'schema_version','record_kind','scope','attempt_id','root','root_identity','root_initial_state',
        'layout','outputs_initially_absent','configuration_sha256','producer_sha256','jobs','source_cache',
        'tool_cache','local_signing','reference','storage','qualification'}
    need(set(value) == fields and type(value.get('schema_version')) is int and value['schema_version'] == 1 and
         value.get('record_kind') == 'wine_reproduction_start' and value.get('scope') == SCOPE,
         'reproduction_start_shape')
    need(type(value['attempt_id']) is str and re.fullmatch('[a-f0-9]{32}', value['attempt_id']) and
         value['root_initial_state'] in ('empty','absent'), 'reproduction_start_identity')
    exact(value['root'], _name(paths['root']), 'reproduction_root_changed')
    exact(value['root_identity'], _identity(paths['root']), 'reproduction_root_changed')
    exact(value['layout'], {key: _name(path) for key,path in paths.items()}, 'reproduction_layout_changed')
    exact(value['outputs_initially_absent'], [key for key in paths if key != 'root'], 'reproduction_freshness_scope')
    exact(value['qualification'], {'runtime':False,'game':False,'distribution':False}, 'reproduction_scope')
    _integer(value['jobs'],1,4)
    exact(value['configuration_sha256'], {key:sha256(REPO/name) for key,name in CONFIGURATION.items()},
          'reproduction_configuration_changed')
    exact(value['producer_sha256'], source_hashes(), 'reproduction_producer_changed')
    for name,digest in value['producer_sha256'].items():
        need(hashlib.sha256(read_relative(paths['root'], 'producer/'+name)).hexdigest() == digest,
             'reproduction_producer_snapshot_changed')
    exact(value['reference'], _reference(), 'reproduction_reference_changed')
    cache = value['tool_cache']; signing = value['local_signing']; storage = value['storage']
    need(set(cache) == {'path','prepared_sha256','reused'} and cache['reused'] is True and
         set(signing) == {'path','sha256'} and set(storage) == {'free_bytes_before','required_free_bytes','estimate'},
         'reproduction_inputs_shape')
    _input_paths(paths, *[REPO.joinpath(*relative(name)) for name in
                          (value['source_cache'],cache['path'],signing['path'])])
    need(sha256(REPO/cache['path']/'prepared.json') == _digest(cache['prepared_sha256']) and
         sha256(REPO/signing['path']) == _digest(signing['sha256']), 'reproduction_inputs_changed')
    _integer(storage['required_free_bytes'],MINIMUM_FREE_BYTES)
    _integer(storage['free_bytes_before'],storage['required_free_bytes'])
    exact(storage['estimate'],STORAGE_ESTIMATE,'reproduction_storage_estimate')
    return value


def operation_result(start, ident, status, *, error=None, started_ns=None, finished_ns=None):
    need(ident in OPERATIONS and status in ('passed','failed','unperformed'), 'reproduction_operation')
    root = REPO.joinpath(*relative(start['root']))
    path,directory = operation_paths(layout(root))[ident]
    if status == 'unperformed':
        need(started_ns is None and finished_ns is None, 'reproduction_unperformed_time')
        reference = identity = None
    else:
        _integer(started_ns,1); _integer(finished_ns,started_ns)
        try:
            reference = {'path':_name(path),'sha256':sha256(_path(path))} if path.is_file() else None
            identity = _identity(directory) if directory.exists() else None
        except (Error,OSError,ValueError,KeyError,TypeError):
            if status == 'passed':
                raise
            # Preserve the primary operation failure when its partial output is
            # missing, unreadable or unsafe. No absent capture can pass a gate.
            reference = identity = None
        need(status != 'passed' or (reference is not None and identity is not None), 'reproduction_missing_artifact')
    need((error is None) if status in ('passed','unperformed') else
         (type(error) is str and re.fullmatch('[a-z0-9_.:-]{1,160}',error)), 'reproduction_operation_error')
    return {'id':ident,'status':status,'error':error,'started_ns':started_ns,'finished_ns':finished_ns,
            'record':reference,'directory_identity':identity}


def _check_operations(start, operations, *, complete, recheck=True):
    need(isinstance(operations,list) and len(operations) == len(OPERATIONS), 'reproduction_operation_coverage')
    paths = layout(REPO/start['root']); previous = 0; halted = False
    for ident,row in zip(OPERATIONS,operations):
        need(isinstance(row,dict) and set(row) == {'id','status','error','started_ns','finished_ns','record','directory_identity'}
             and row['id'] == ident, 'reproduction_operation_order')
        need(row['status'] in ('passed','failed','unperformed'), 'reproduction_operation_status')
        need(not halted or row['status']=='unperformed', 'reproduction_operation_after_failure')
        if row['status']=='unperformed':
            need(halted and row['record'] is None and row['directory_identity'] is None and
                 row['started_ns'] is None and row['finished_ns'] is None, 'reproduction_unperformed_shape')
        else:
            _integer(row['started_ns'],max(1,previous+1)); _integer(row['finished_ns'],row['started_ns'])
            previous = row['finished_ns']
            path,directory = operation_paths(paths)[ident]
            if row['record'] is not None:
                need(set(row['record']) == {'path','sha256'} and row['record']['path'] == _name(path),
                     'reproduction_record_changed')
                _digest(row['record']['sha256'])
                if recheck:
                    need(row['record']['sha256']==sha256(_path(path)), 'reproduction_record_changed')
            if row['directory_identity'] is not None:
                need(set(row['directory_identity'])=={'device','inode'}, 'reproduction_directory_changed')
                for number in row['directory_identity'].values(): _integer(number,1)
                if recheck:
                    exact(row['directory_identity'],_identity(directory),'reproduction_directory_changed')
            need(row['status']!='passed' or (row['record'] is not None and row['directory_identity'] is not None),
                 'reproduction_missing_artifact')
        need((row['error'] is None) if row['status'] in ('passed','unperformed') else
             (type(row['error']) is str and re.fullmatch('[a-z0-9_.:-]{1,160}',row['error'])),
             'reproduction_operation_error')
        halted |= row['status']=='failed'
    need(not complete or all(row['status']=='passed' for row in operations), 'reproduction_incomplete')
    return operations


def write_terminal(root, start, operations, error=None):
    root = layout(root)['root']
    complete = all(row['status']=='passed' for row in operations)
    if complete:
        exact(_read(root/'start.json'),start,'reproduction_start_changed')
    _check_operations(start,operations,complete=False,recheck=complete)
    need((error is None) if complete else
         (type(error) is str and re.fullmatch('[a-z0-9_.:-]{1,160}',error)), 'reproduction_terminal_error')
    value = {'schema_version':1,'record_kind':'wine_reproduction','scope':SCOPE,
        'start_sha256':hashlib.sha256(encoded(start)).hexdigest(),'attempt_id':start['attempt_id'],
        'operations':operations,'complete':complete,'error':error,
        'runtime_qualified':False,'game_qualified':False,'distribution_qualified':False}
    _write_new(root/'reproduction.json',value)
    return value


def _terminal(root,start):
    value = _read(root/'reproduction.json')
    need(set(value) == {'schema_version','record_kind','scope','start_sha256','attempt_id','operations','complete',
                       'error','runtime_qualified','game_qualified','distribution_qualified'} and
         type(value.get('schema_version')) is int and value['schema_version']==1 and
         value['record_kind']=='wine_reproduction' and value['scope']==SCOPE,
         'reproduction_terminal_shape')
    need(value['start_sha256']==sha256(root/'start.json') and value['attempt_id']==start['attempt_id'],
         'reproduction_terminal_binding')
    need(value['complete'] is True and value['error'] is None and all(value[key] is False for key in
         ('runtime_qualified','game_qualified','distribution_qualified')), 'reproduction_incomplete')
    _check_operations(start,value['operations'],complete=True)
    return value


def validate(root):
    from build import artifact_inventory, verify_build, PRODUCERS as BUILD_PRODUCERS
    from prepare import verify_prepared
    from toolchain import verify_prepared_tools
    from verify import validate_stage1, validate_builds
    from unsigned_compare import validate_unsigned_comparison, public_summary
    from arena_reproduction import validate as validate_native_arena
    from modules import validate_inventory
    paths=layout(root); root=paths['root']; start=load_start(root); terminal=_terminal(root,start)
    terminal_digest=sha256(root/'reproduction.json')
    prepared=verify_prepared(paths['inputs'],start['configuration_sha256']['inputs'])
    tools=REPO/start['tool_cache']['path']
    lock=_read(REPO/CONFIGURATION['toolchain'])
    tool_cache=verify_prepared_tools(lock,tools)
    need(tool_cache['lock_sha256']==start['configuration_sha256']['toolchain'], 'reproduction_tool_lock')
    input_gate=validate_stage1(REPO/CONFIGURATION['inputs'],REPO/CONFIGURATION['config'],paths['toolchain_check'])
    need(input_gate.get('gate_passed') is True and input_gate['source_prepared_sha256']==sha256(paths['inputs']/'prepared.json')
         and input_gate['tool_prepared_sha256']==start['tool_cache']['prepared_sha256'], 'reproduction_input_gate')
    tool_report=_read(paths['toolchain_check'])
    need(tool_report['source_prepared_path']==str(paths['inputs']/'prepared.json'), 'reproduction_source_root')
    component=prepared['components'][0]
    need(sha256(paths['inputs']/'wine-source.tar')==component['archive_sha256'], 'reproduction_source_archive')
    matrix=validate_builds(paths['native_build'],paths['companion_build'])
    need(matrix.get('gate_passed') is True, 'reproduction_variant_gate')
    builds={}; public_builds={}
    for key,variant in BUILD_ROLES:
        if key=='native_reference_build':
            built=verify_build(paths[key])
            validate_inventory(paths[key],verified_build=built)
        else:
            built=_read(paths[key]/'build.json')
        builds[key]=built
        need(built.get('variant')==variant and built.get('fixture_suite')=='mac-driver' and
             built.get('code_publication_policy')=='page-wx' and built.get('completion_revision') is None and
             built.get('source_argument_policy')==SOURCE_ARGUMENT_POLICY and
             built.get('source_inputs_root')==str(paths['inputs']) and built.get('tools_root')==str(tools) and
             built.get('source_prepared_sha256')==sha256(paths['inputs']/'prepared.json') and
             built.get('tool_prepared_sha256')==start['tool_cache']['prepared_sha256'], 'reproduction_build_binding')
        exact(built.get('producer_sha256'),{name:sha256(REPO/'tools/wine'/name) for name in BUILD_PRODUCERS},
              'reproduction_build_producer_changed')
        exact(built.get('record_hashes'),start['configuration_sha256'],'reproduction_build_inputs')
        files=artifact_inventory(built,paths[key])['files']; machines={}
        for item in files:
            if item.get('kind')=='pe':
                code=_integer(item.get('machine')); machines[str(code)]=machines.get(str(code),0)+1
        modules=_read(paths[key]/'modules.json')
        selected=[]
        for row in modules['modules']:
            selected.append({'module':Path(row['path']).name,'sha256':_digest(row['sha256']),
                'machine':_integer(row['facts']['machine']), 'hybrid_metadata_required':row['hybrid_required'] is True,
                'export_count':len(row['facts']['exports'])})
        public_builds[key]={'variant':variant,'build_sha256':sha256(paths[key]/'build.json'),
            'source_manifest_sha256':_digest(built['source_manifest']['sha256']),
            'installed_manifest_sha256':_digest(built['artifacts_manifest']['sha256']),
            'module_inventory_sha256':sha256(paths[key]/'modules.json'),'selected_modules':selected,
            'native_artifact_count':_integer(built['native_artifact_count'],1),
            'pe_artifact_count':_integer(built['pe_artifact_count'],1),'pe_machine_counts':machines,
            'commands_passed':len(built['commands']),'host_architecture':'arm64',
            'source_argument_policy':SOURCE_ARGUMENT_POLICY,
            'wine_runtime_executed':key=='native_build'}
    anchor=builds['native_reference_build']
    for key,_ in BUILD_ROLES[1:]:
        for field in ('source_manifest','patches','fixture_hashes','sdk','record_hashes'):
            exact(builds[key][field],anchor[field],'reproduction_shared_build_inputs')
    exact(builds['native_build']['configuration'],anchor['configuration'],'reproduction_native_configuration')
    companion=builds['companion_build']['arena_capacity'].get('assessment')
    need(isinstance(companion,dict) and companion.get('scope')=='compile_only_arm64ec_companion' and
         companion.get('image_measurement')=='arm64_outer_headers_including_arm64x' and
         type(companion.get('fits_native_limits')) is bool and
         companion.get('native_runtime_qualification')=='unassessed', 'reproduction_companion_arena_scope')
    native_evidence=stage5_evidence.export(paths['native_build'],paths['mac_driver'],paths['bootstrap'])
    need(native_evidence['build']['build_sha256']==sha256(paths['native_build']/'build.json'),
         'reproduction_native_gate')
    # The existing exporter independently binds both suites to this exact root.
    signed=_read(paths['signed']/'signed.json')
    need(native_evidence['signed_sha256']==sha256(paths['signed']/'signed.json') and
         signed['build_ref']['path']==str(paths['native_build']/'build.json'), 'reproduction_signed_root')
    comparison=validate_unsigned_comparison(paths['unsigned_compare'],paths['native_reference_build'],paths['native_build'])
    need(comparison.get('gate_passed') is True, 'reproduction_unsigned_difference_unexplained')
    need(comparison.get('reference_build_sha256')==sha256(paths['native_reference_build']/'build.json') and
         comparison.get('candidate_build_sha256')==sha256(paths['native_build']/'build.json') and
         comparison.get('reference_inventory_sha256')==anchor['artifacts_manifest']['sha256'] and
         comparison.get('candidate_inventory_sha256')==builds['native_build']['artifacts_manifest']['sha256'],
         'reproduction_comparison_reference')
    compared=public_summary(comparison)
    # The comparator is responsible for complete inventory coverage and accepted
    # changed-byte regions. A saved success flag alone is never a comparison.
    public={'schema_version':1,'record_kind':'wine_stage6_observations','scope':SCOPE,
        'reproduction_sha256':terminal_digest,'start_sha256':terminal['start_sha256'],
        'reproduction_passed':True,'source_rematerialized':True,'wine_variants_rebuilt':['arm64','arm64ec-build'],
        'native_rebuild_count':2,'source_argument_policy':SOURCE_ARGUMENT_POLICY,
        'source':{'commit':component['commit'],'tree':component['tree'],
                  'archive_sha256':_digest(component['archive_sha256']),
                  'manifest_sha256':_digest(component['files_manifest']['sha256'])},
        'input_record_sha256':dict(start['configuration_sha256']),
        'tool_cache':{'reused':True,'independently_rebuilt':False,
            'prepared_sha256':start['tool_cache']['prepared_sha256'],
            'fresh_feature_check_sha256':sha256(paths['toolchain_check']),
            'checks_passed':_integer(input_gate['checks_passed'],1),
            'commands_passed':_integer(input_gate['commands_passed'],1)},
        'operations':[{'id':row['id'],'status':'passed','record_sha256':row['record']['sha256']} for row in terminal['operations']],
        'variants':[public_builds[key] for key in ('native_build','companion_build')],
        'fresh_reference':{'scope':'compile_and_inspect_only', 'development_signed':False, 'runtime_executed':False,
            **public_builds['native_reference_build']},'unsigned_comparison':compared,
        'historical_reference':{'stage':5,'build_sha256':REFERENCE_BUILD_SHA256,'observations_sha256':REFERENCE_PUBLIC_SHA256,
            'runtime_reexecuted':False,'companion_same_final_patch_reference_available':False,
            'source_argument_policy':'legacy_absolute_v1', 'byte_equivalence_reference':False,
            'byte_equivalence_to_fresh_builds_claimed':False},
        'companion':{'scope':'compile_only_arm64ec_companion','native_runtime_qualification':'unassessed',
            'guest_execution':False,'translator_execution':False,'native_arena_fit_observed':companion['fits_native_limits']},
        'native_fixture_evidence':native_evidence,
        'producer_sha256':{label:start['producer_sha256'][name] for label,name in SOURCES.items()},
        'same_host':True,'independent_machine_tested':False,'clean_machine_tested':False,
        'compiler_rebuilt':False,'translator_execution':False,'game_execution':False,
        'runtime_qualified':False,'distribution_qualified':False,
        'limits':['Fresh directories on the same declared development Mac; reused compiler cache was reverified.',
            'Native bootstrap and combined API/ABI/thread/window fixtures share one newly signed runtime.',
            'The current standalone page-wx arena prerequisite is rebuilt, signed and rerun separately from Wine.',
            'The two earlier failed thread-jit designs remain historical evidence and are not rerun.',
            'The ARM64EC companion is compiled and inspected only; no translator or companion runtime execution is qualified.',
            'Unsigned comparison covers two fresh native builds using the same stable relative source invocation.',
            'Historical absolute-source builds contain observed ICU code and data layout differences; these are not relabeled metadata.',
            'No byte or semantic equivalence to the historical Stage5 payload is claimed.',
            'Unsigned-byte explanations are limited to independently parsed fields and exact reviewed path regions.',
            'Signatures are separate identities; deterministic signed bytes are neither required nor claimed.',
            'Prior failures and original evidence are retained; this is not a clean-machine or independent-tester result.',
            'Steam, Megabonk, graphics pairing and ordinary-user distribution remain unqualified.']}
    arena=validate_native_arena(paths['native_arena'],REPO/start['local_signing']['path'])
    need(arena.get('gate_passed') is True and arena.get('policy')=='page-wx' and
         arena.get('scope')=='fresh_native_arena_prerequisite' and
         all(arena.get(key) is False for key in ('wine_execution','runtime_qualified','game_qualified')),
         'reproduction_native_arena_gate')
    public['native_arena_prerequisite']=arena
    exact(load_start(root),start,'reproduction_changed_during_validation')
    exact(_terminal(root,start),terminal,'reproduction_changed_during_validation')
    need(sha256(root/'reproduction.json')==terminal_digest,'reproduction_changed_during_validation')
    # Close the interval after runtime replay and unsigned comparison without
    # executing those suites again. Rehash actual source/install/signed trees.
    from build import inventory as build_inventory
    from signing import inventory as signed_inventory, BUNDLE
    verify_prepared(paths['inputs'],start['configuration_sha256']['inputs'])
    for key,_ in BUILD_ROLES:
        built=builds[key]
        exact(build_inventory(paths[key]/'source'),_read(paths[key]/built['source_manifest']['path']),
              'reproduction_final_source_changed')
        exact(build_inventory(paths[key]/'install',binary=True),artifact_inventory(built,paths[key]),
              'reproduction_final_install_changed')
        validate_inventory(paths[key],verified_build=built)
    signed_files=_read(paths['signed']/'signed-files.json')
    need(sha256(paths['signed']/'signed-files.json')==signed['files_manifest_sha256'],
         'reproduction_final_signed_manifest_changed')
    exact(signed_inventory(paths['signed']/BUNDLE),signed_files['files'],'reproduction_final_signed_changed')
    verify_prepared_tools(lock,tools)
    exact(load_start(root),start,'reproduction_changed_during_validation')
    exact(_terminal(root,start),terminal,'reproduction_changed_during_validation')
    return public


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True)
    parser.add_argument('--output')
    args=parser.parse_args(argv)
    try:
        value=validate(args.root)
        if args.output:
            destination=_path(args.output)
            need(destination.parent==REPO.resolve()/'mydocs/working' and destination.suffix=='.json',
                 'reproduction_export_destination')
            _write_new(destination,value)
        else:
            print(encoded(value).decode(),end='')
    except (Error,OSError,ValueError,KeyError,TypeError,AttributeError) as error:
        print(encoded({'schema_version':1,'record_kind':'wine_reproduction_assessment',
            'gate_passed':False,'error':getattr(error,'code','invalid_or_missing_evidence')}).decode(),end='')
        return 3 if isinstance(error,Error) else 1
    return 0


if __name__=='__main__':
    sys.exit(main())
