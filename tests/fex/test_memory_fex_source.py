"""Portable exact-byte source controls, never C++ behavior qualification."""
import hashlib
import json
from pathlib import Path
import unittest
from tools.fex.build import patch_sections, apply_hunks
from tools.fex.common import Error

ROOT = Path(__file__).resolve().parents[2]


class FEXMemorySourceClosureTests(unittest.TestCase):
    def materialized(self):
        root = ROOT / 'runtime/fex/patches'
        manifest = json.loads((root / 'memory-fex-series.json').read_text())
        self.assertEqual(manifest['component'], 'fex-memory-source-supplements')
        self.assertIs(manifest['runtime_execution'], False)
        self.assertEqual(manifest['preserved_abi'], {
            'fex_unixlib_services': 8, 'wire_record_bytes': 128, 'ntdll_unix_index': 10, 'wire_version': 2})
        self.assertTrue(all(v is False for v in manifest['source_gates'].values()))
        self.assertEqual(len(manifest['patches']), 23)
        row = manifest['patches'][0]
        raw = (root / row['file']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), row['sha256'])
        sections = patch_sections(raw)
        self.assertEqual(set(sections), {
            'FEXCore/include/FEXCore/Utils/PearFEXMemory.h',
            'Source/Windows/Common/PearFEXMemory.cpp',
            'Source/Windows/Common/CMakeLists.txt'})
        postimages = {}
        for entry in row['sources']:
            source = ROOT / '.build/task5/stage2-modules3/source' / entry['path']
            # New additive sources have no historical preimage. The source
            # cache is used only for the one existing upstream CMake file.
            if entry['preimage_sha256'] is not None and not source.is_file():
                self.skipTest('Pinned Stage 2 source is unavailable; materialization check is unperformed')
            before = source.read_bytes() if entry['preimage_sha256'] is not None else None
            self.assertEqual(hashlib.sha256(before).hexdigest() if before is not None else None,
                             entry['preimage_sha256'])
            after = apply_hunks(before, sections[entry['path']], entry['path'])
            self.assertEqual(hashlib.sha256(after).hexdigest(), entry['postimage_sha256'])
            self.assertEqual(len(after), entry['postimage_bytes'])
            postimages[entry['path']] = after
        self.assertEqual(set(postimages), set(sections))
        return manifest, postimages, sections

    def test_complete_current_graph_matches_actual_selected_source_if_available(self):
        from tools.fex import memory_fex_check as current
        baseline = ROOT / '.build/task5/stage2-modules3'
        if not (baseline / 'build.json').is_file():
            self.skipTest('Actual selected Stage 2 baseline unavailable; complete graph replay unperformed')
        graph = ROOT / 'runtime/fex/patches/memory/source-graph'
        observed = current.selected_projection(baseline, graph)
        proposal = json.loads((graph / 'final-source-proposal.json').read_bytes())
        self.assertEqual(observed['source_files'], proposal['files'])
        self.assertEqual(observed['layer_count'], 23)

    def test_closed_additive_layer_reproduces_every_postimage(self):
        self.materialized()

    def test_wrong_existing_preimage_cannot_materialize_adapter(self):
        _, _, sections = self.materialized()
        path = 'Source/Windows/Common/CMakeLists.txt'
        with self.assertRaises(Error): apply_hunks(b'wrong upstream\n', sections[path], path)

    def test_cmake_preserves_unrelated_sources_and_curates_exact_wire_header(self):
        manifest, postimages, _ = self.materialized()
        path = 'Source/Windows/Common/CMakeLists.txt'
        base = (ROOT / '.build/task5/stage2-modules3/source' / path).read_bytes()
        # Source-list preservation is byte based, independent of source prose.
        source_list_end = base.index(b'  Threads.cpp)') + len(b'  Threads.cpp)')
        original = base[:source_list_end]
        after = postimages[path]
        self.assertEqual(after[:len(original)+len(b'  PearFEXMemory.cpp\n')].replace(b'  PearFEXMemory.cpp\n', b''), original)
        # The first preserved adapter layer selected ABI1; the complete graph
        # selects ABI2 only after the reviewed layer-13 CMake derivative.
        self.assertIn(b'2957188b00a74a46196341aa1237cf1cf44b375e5253c8bd9457bfc0d6b2aee1', after)
        self.assertEqual(manifest['authoritative_header']['sha256'],
                         'bee4d7f58bb796f7b86f85e5bf3d3dc9100a9df51789f0522762c6846d9ad1cf')


if __name__ == '__main__': unittest.main()
