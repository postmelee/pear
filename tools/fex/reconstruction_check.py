"""Admission of fresh final component receipts for the existing runtime packager.

Inspect current bytes and completed command logs; a passed flag or filename alone
is never sufficient. Runtime authorization remains in integration_runtime.py.
"""
from pathlib import Path
import json
from tools.fex.common import REPO, need, relative, sha256
from tools.fex.reconstruct import WINE_BASE, FEX_BASE, H
from tools.fex import memory_wine_build as monitor, memory_fex_check


def command_gate(root, rows, names):
    need(isinstance(rows, list) and [r['id'] for r in rows] == names,
         'reconstruction_command_set')
    for row in rows:
        need(row['status'] == 'completed' and type(row['exit_code']) is int and
             row['exit_code'] == 0 and row['error_domain'] is None and
             row['error_code'] is None and 'cleanup_error' not in row,
             'reconstruction_command_failed')
        need(row['argv'][:2] == ['/usr/bin/arch', '-arm64'], 'reconstruction_native_command')
        for stream in ('stdout', 'stderr'):
            ref = row['logs'][stream]
            relative(ref['path'])
            data = (root / ref['path']).read_bytes()
            need(H(data) == ref['sha256'] and len(data) == ref['size_bytes'],
                 'reconstruction_log_changed')
        saved = json.loads((root / 'logs' / row['id'] / 'command.json').read_text())
        need(saved == row, 'reconstruction_command_record_changed')


def load(root, kind, source, producer, series):
    need(root.parent == REPO / '.build/task5', 'reconstruction_foreign')
    value = json.loads((root / 'build.json').read_text())
    if (root / 'failure.json').exists():
        final = value.get('finalization', {})
        prior = json.loads((root / 'build.failed.json').read_text())
        need(kind == 'fresh_final_wine' and final.get('scope') == 'collection_only_no_recompile' and
             prior.get('error') == 'arena_dynamic_mapping_capacity' and prior['passed'] is False and
             final['original_failed_receipt_sha256'] == sha256(root / 'build.failed.json') and
             final['original_failure_sha256'] == sha256(root / 'failure.json') and
             final['collector_sha256'] == sha256(root / 'collector.py') ==
             sha256(REPO / 'tools/fex/reconstruct_wine_result.py') and
             value['construction_producer_sha256'] == prior['producer_sha256'] ==
             sha256(root / 'producer.build.py') and value['commands'] == prior['commands'] and
             value['source_manifest_sha256'] == prior['source_manifest_sha256'],
             'reconstruction_failed_without_valid_finalization')
    need(value['passed'] is True and value['kind'] == kind and
         value['source_base_sha256'] == source and value['source_only_reuse'] is True and
         value['previous_objects_reused'] is False and value['guest_execution'] is False,
         'reconstruction_build_scope')
    need(value['producer_sha256'] == sha256(REPO / producer) == sha256(root / 'producer.py') and
         value['series_sha256'] == sha256(REPO / series), 'reconstruction_producer_changed')
    return value


def components(base, paired, fex, linked):
    need(base == paired and fex == linked, 'reconstruction_mixed_pair')
    wine = load(base, 'fresh_final_wine', WINE_BASE, 'tools/fex/reconstruct.py',
                'runtime/fex/patches/integration/series.json')
    cpu = load(fex, 'fresh_final_fex', FEX_BASE, 'tools/fex/reconstruct_fex.py',
               'runtime/fex/patches/integration/fex-series.json')
    command_gate(base, wine['commands'], ['configure', 'make', 'install'] +
                 [r['id'] for r in wine['commands'][3:]])
    need(wine['commands'][1]['argv'][-1] == '-j2' and
         wine['commands'][2]['argv'][-1] == 'install', 'reconstruction_full_wine_build')
    expected = ['native.configure', 'native.build', 'native.fixture',
                'arm64ec.configure', 'arm64ec.build', 'arm64ec.inspect',
                'wow64.configure', 'wow64.build', 'wow64.inspect', 'deployment.strip']
    command_gate(fex, cpu['commands'], expected)
    for index in (4, 7):
        argv = cpu['commands'][index]['argv']
        need('--build' in argv and '--target' in argv and '--parallel' in argv and
             argv[-3:] == ['--', '-d', 'keepdepfile'], 'reconstruction_full_fex_build')
    with monitor.wine_readers() as (_, wb):
        source = json.loads((base / 'source-files.json').read_text())
        need(sha256(base / 'source-files.json') == wine['source_manifest_sha256'] and
             wb.inventory(base / 'source') == source, 'reconstruction_wine_source_changed')
        installed = json.loads((base / 'installed-files.json').read_text())
        need(sha256(base / 'installed-files.json') == wine['artifacts_manifest']['sha256'] and
             wb.inventory(base / 'install', binary=True) == installed, 'reconstruction_wine_install_changed')
    source = json.loads((fex / 'materialized-source.json').read_text())
    need(sha256(fex / 'materialized-source.json') == cpu['source_manifest_sha256'] and
         memory_fex_check.source_inventory(fex / 'source') == source['files'],
         'reconstruction_fex_source_changed')
    need(sha256(fex / 'wire/wine/pear_fex_memory.h') == cpu['wire_sha256'] ==
         sha256(base / 'source/include/wine/pear_fex_memory.h'), 'reconstruction_wire_mismatch')
    need(sha256(fex / 'module-proofs.json') == cpu['module_proofs_sha256'],
         'reconstruction_module_proofs_changed')
    for root, rows in ((base, wine['outputs']), (fex, cpu['outputs'] + cpu['artifacts'])):
        for row in rows:
            relative(row['path'])
            raw = (root / row['path']).read_bytes()
            need(H(raw) == row['sha256'] and len(raw) == row['size_bytes'],
                 'reconstruction_artifact_changed')
    expected_receipts = dict(paired=sha256(base / 'build.json'), fex=sha256(fex / 'build.json'),
                             linked=sha256(fex / 'build.json'))
    return expected_receipts, dict(paired=wine, fex=cpu, linked=cpu)
