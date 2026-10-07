#!/usr/bin/env python3
"""Assess finite development execution without claiming game qualification."""
from pathlib import Path
import argparse, hashlib, json, re, struct
H = lambda raw: hashlib.sha256(raw).hexdigest()

def assess(run, runtime, output, layout=None):
    case = json.loads((run / 'case.json').read_text())
    manifest = json.loads((runtime / 'runtime.json').read_text())
    assert case['runtime_sha256'] == H((runtime / 'runtime.json').read_bytes())
    assert case['outcome'] == 'exited' and case['processes']['loader']['exit_code'] == 42
    assert not case['error'] and not case['stream_error'] and not case['cleanup_errors']
    assert case['cleanup']['complete'] and case['sentinel_survived'] and case['authorization_before_after_passed']
    events = [row for rows in case['events'].values() for row in rows]
    translated = [row for row in events if 'translation_value' in row]
    assert translated and all(row['translation_value'] == 0 and row['translation_error'] == 0 and row['cpu_type'] == 16777228 for row in translated)
    images = [row for row in events if row.get('event') == 'image']
    assert images and all(row['cpu_type'] == 16777228 for row in images)
    # The existing observer's image event name is source-version specific.
    image_kinds = sorted({row['event'] for row in events if 'image' in row.get('event', '')})
    result = dict(scope='finite_x64_execution', passed=True,
        case_sha256=H((run/'case.json').read_bytes()), runtime_sha256=case['runtime_sha256'],
        source_receipts=manifest['input_receipts'], instrumented=bool(manifest.get('test_instrumentation')),
        translation_observations=len(translated), arm64_image_events=len(images), image_event_kinds=image_kinds,
        host_architecture='ARM64', authorization_before_after=True, cleanup_complete=True,
        sentinel_survived=True, exit_code=42, elapsed_ms=case['elapsed_ms'],
        late_load_coverage_complete=False, game_execution=False, distribution_qualified=False)
    if layout:
        log = (run / 'run/loader.stderr.log').read_text()
        for required in ('ECMemory.complete: status=00000000 domain=0 code=62',
                         'ECConcurrent.active-retire: status=00000005 domain=0 code=0',
                         'ECConcurrent.pinned-retire: status=00000003 domain=0 code=0',
                         'ECConcurrent.complete: status=00000000 domain=0 code=2'):
            assert required in log, required
        metadata = dict((k, int(v)) for k, v in re.findall(r'(\w+)=(\d+)', next(line for line in log.splitlines() if 'Pear EC metadata:' in line)))
        assert metadata['fixed_native'] <= 131072 and metadata['added_leaves'] <= 4 and metadata['bitmap_writable'] <= 262144 and metadata['view_slots'] >= 1024
        dll = runtime / 'PearWineLoader.app/Contents/Resources/runtime/lib/wine/aarch64-windows/xtajit64.dll'
        pe = dll.read_bytes(); header = struct.unpack_from('<I', pe, 60)[0]
        count = struct.unpack_from('<H', pe, header+6)[0]; optional = struct.unpack_from('<H', pe, header+20)[0]
        mutable = 0
        for index in range(count):
            offset = header+24+optional+40*index
            size = struct.unpack_from('<I', pe, offset+8)[0]; flags = struct.unpack_from('<I', pe, offset+36)[0]
            if flags & 0x80000000: mutable += (size+4095)//4096*4096
        assert mutable <= 131072
        sizes = json.loads((layout/'control.json').read_text())['sizes']
        page = lambda n: (n+4095)//4096*4096
        # Charge full objects, including unchanged upstream fields, and 256
        # possible buffer holders (twice the owner's total extent capacity).
        objects = page(sizes['context']) + page(sizes['dispatcher']) + 3*sum(page(sizes[k]) for k in ('thread','jit','lookup')) + 256*page(sizes['buffer'])
        assert objects <= 2*1048576
        profile = dict(native_owner_and_adapter=131072, complete_PE_mutable_image=131072,
            source_objects_with_page_allowance=2097152, three_guest_stacks=3145728,
            three_emulator_stacks=786432, protection_leaf_headroom=4194304,
            view_block_headroom=2097152, retained_bitmap_headroom=262144,
            alignment_and_transition_headroom=262144)
        total = sum(profile.values()); assert total < 16*1048576
        result.update(scope='finite_actual_EC_memory_and_x64_execution', lifecycle_checks=62,
            concurrent_workers=2, real_source_identity=True,
            active_retirement='quiescence_timeout', parked_pinned_retirement='unavailable',
            released_retirement='passed', stale_entry='refused',
            worker_teardown='parked native workers reaped at process exit; ordinary ThreadTerm is Stage 5',
            resource_profile=dict(scope='one Context, at most three participating EC threads',
                kind='reviewed conservative bookkeeping estimate, not resident high-water measurement',
                declared_bytes=16*1048576, accounted_bytes=total, headroom_bytes=16*1048576-total,
                entries=profile, observed_metadata=metadata, complete_mutable_PE_pages_bytes=mutable, compiler_object_payload_with_page_allowance=objects,
                compiler_layout_sha256=H((layout/'control.json').read_bytes()),
                ordinary_engine_allocations_included=False, physical_resident_peak_measured=False,
                limit='Not a whole-process allocator cap or a 64-thread/game memory qualification'))
    assert not output.exists(); output.mkdir()
    (output/'control.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('run', 'runtime', 'output'): parser.add_argument('--'+key, type=Path, required=True)
    parser.add_argument('--layout', type=Path)
    args = parser.parse_args(); assess(args.run, args.runtime, args.output, args.layout)
