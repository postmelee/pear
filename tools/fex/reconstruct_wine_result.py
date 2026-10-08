"""Collect the final Wine build without applying the historical arena formula.

The loader arena and FEX JIT arena are distinct source-defined regions. Measure
installed image requirements without claiming every image is loaded together.
"""
from pathlib import Path
import json
import re
import struct
from tools.fex.common import need, sha256
from tools.fex import integration, memory_wine_build as monitor
from tools.fex.reconstruct import H, save


def capacity(source, install, artifacts):
    header = source / 'dlls/ntdll/unix/pear_pe_arena.h'
    text = header.read_text()
    limits = {}
    for key in ('INTERIOR_BYTES', 'ALIGNMENT', 'MAX_IMAGE_BYTES', 'MAX_SLOTS', 'PAGE_BYTES'):
        rows = re.findall(r'^#define PEAR_ARENA_' + key + r' (?:\(\(SIZE_T\)([0-9]+)\)|([0-9]+)u)$', text, re.M)
        need(len(rows) == 1, 'reconstruction_arena_definition')
        limits[key.lower()] = int(rows[0][0] or rows[0][1])
    need(limits['alignment'] == 65536 and limits['page_bytes'] == 4096,
         'reconstruction_arena_geometry')
    formula = '#define PEAR_ARENA_MAPPING_BYTES (PEAR_ARENA_FEX_DISPATCHER_OFFSET + PEAR_FEX_MEMORY_DISPATCHER_BYTES + PEAR_ARENA_ALIGNMENT)'
    need(formula in text.splitlines(), 'reconstruction_integrated_arena_mapping')
    sizes = {}
    for row in artifacts['files']:
        if row.get('kind') != 'pe' or row.get('machine') != 0xaa64:
            continue
        raw = (install / row['path']).read_bytes()
        offset = struct.unpack_from('<I', raw, 60)[0]
        need(raw[offset:offset+4] == b'PE\0\0', 'reconstruction_arena_pe')
        size = struct.unpack_from('<I', raw, offset + 80)[0]
        need(size > 0 and size % 4096 == 0, 'reconstruction_arena_image_size')
        sizes[row['path']] = (size + 65535) & ~65535
    need(bool(sizes), 'reconstruction_arena_empty')
    copies = 2 * sizes['libexec/pear-stage3/lifetime-arm64.dll']
    largest, total = max(sizes.values()), sum(sizes.values())
    required, slots = total + largest + copies, len(sizes) + 3
    return dict(policy='page-wx', header_sha256=sha256(header), limits=limits,
                arm64_image_count=len(sizes), total_slot_bytes=total,
                largest_slot_bytes=largest, preparation_margin_bytes=largest,
                required_interior_bytes=required, required_slots=slots,
                dynamic_limits=dict(bytes=524288, slots=8, slot_bytes=65536),
                integrated_jit_mapping_bytes=1588985856, wine_execution=False,
                assessment=dict(scope='build_image_inventory_not_simultaneous_load',
                    fits_native_limits=largest <= limits['max_image_bytes'] and
                    slots <= limits['max_slots'] and required <= limits['interior_bytes'],
                    image_measurement='arm64_outer_headers_including_arm64x',
                    native_runtime_qualification='unassessed'))


def collect(root, value):
    with monitor.wine_readers() as (_, wb):
        manifest = json.loads((root / 'source-files.json').read_text())
        need(sha256(root / 'source-files.json') == value['source_manifest_sha256'] and
             wb.inventory(root / 'source') == manifest, 'reconstruct_mutated_source')
        artifacts = wb.inventory(root / 'install', binary=True)
        series = json.loads((integration.REPO / 'runtime/wine/patches/series.json').read_text())
        wb.required_outputs(artifacts, 'arm64ec-build', wb.fixture_suite(series), wb.code_publication_policy(series))
    value['arena_capacity'] = capacity(root / 'source', root / 'install', artifacts)
    save(root / 'installed-files.json', artifacts)
    value['artifacts_manifest'] = dict(path='installed-files.json', sha256=sha256(root / 'installed-files.json'))
    value['outputs'] = [dict(path='install/' + r['path'], sha256=r['sha256'], size_bytes=r['size_bytes'])
                       for r in artifacts['files'] if r['path'] in
                       ('lib/wine/aarch64-unix/ntdll.so', 'lib/wine/aarch64-windows/ntdll.dll')]
    need(len(value['outputs']) == 2, 'reconstruct_ntdll_pair')
    return value
