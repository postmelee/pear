"""Portable rejection checks for early native heap layout and recipe ownership."""
import importlib.util
from pathlib import Path
import struct
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('loader_reservation', ROOT / 'tools/dxmt/loader_reservation.py')
loader = importlib.util.module_from_spec(spec); spec.loader.exec_module(loader)


def image():
    segments = [('__PAGEZERO', 0, 0x10000, 0, 0, 0),
                ('__TEXT', 0x10000, 0x3000, 0, 0x3000, 5),
                ('__DATA_CONST', 0x13000, 0x1000, 0x3000, 0x1000, 3),
                ('__DATA', 0x14000, 0x1000, 0x4000, 0x1000, 3),
                ('WINE_RESERVE', 0x15000, 0xffff0000, 0, 0, 3),
                ('__LINKEDIT', 0x100005000, 0x1000, 0x5000, 0x1000, 1)]
    raw = bytearray(0x6000)
    struct.pack_into('<8I', raw, 0, 0xfeedfacf, 0x100000c, 0, 2, 6, 6 * 72, 0x200000, 0)
    for i, (name, addr, size, offset, count, prot) in enumerate(segments):
        struct.pack_into('<II16s4Q4I', raw, 32 + i * 72, 25, 72, name.encode(),
                         addr, size, offset, count, prot, prot, 0, 0)
    return raw


class Layout(unittest.TestCase):
    def test_contiguous_pie_reservation_preserves_low_guest_guard(self):
        result = loader.layout(bytes(image()))
        self.assertTrue(result['pie'])
        self.assertEqual(result['segments'][0]['size'], 65536)
    def test_disabled_aslr_refused(self):
        raw = image(); struct.pack_into('<I', raw, 24, 0)
        with self.assertRaisesRegex(ValueError, 'arm64_pie'): loader.layout(raw)
    def test_wrong_native_architecture_refused(self):
        raw = image(); struct.pack_into('<I', raw, 4, 0x1000007)
        with self.assertRaisesRegex(ValueError, 'arm64_pie'): loader.layout(raw)
    def test_heap_allocation_gap_refused(self):
        raw = image(); struct.pack_into('<Q', raw, 32 + 4 * 72 + 24, 0x16000)
        with self.assertRaisesRegex(ValueError, 'low_address_hole'): loader.layout(raw)
    def test_shared_cache_overlap_refused(self):
        raw = image(); struct.pack_into('<Q', raw, 32 + 4 * 72 + 32, 0x1ffff0000)
        struct.pack_into('<Q', raw, 32 + 5 * 72 + 24, 0x200005000)
        with self.assertRaisesRegex(ValueError, 'reservation_layout'): loader.layout(raw)
    def test_fixed_four_gib_guard_refused(self):
        raw = image(); struct.pack_into('<Q', raw, 32 + 32, 0x100000000)
        with self.assertRaisesRegex(ValueError, 'null_guard'): loader.layout(raw)
    def test_truncated_load_command_refused(self):
        raw = image(); struct.pack_into('<I', raw, 32 + 4, 0xfffffff8)
        with self.assertRaisesRegex(ValueError, 'command_size'): loader.layout(raw)


class Recipes(unittest.TestCase):
    def test_dependency_only_target_does_not_select_other_recipe(self):
        make = "CC = /clang\nCFLAGS = -arch arm64\nLDFLAGS = \nloader/main.o: ../source/loader/main.c\n\t$(CC) -c -o $@ ../source/loader/main.c -fPIE $(CFLAGS)\nloader/main.o: include/config.h\nother: source.c\n\t/evil\nloader/wine: loader/main.o\n\t$(CC) -o $@ loader/main.o $(LDFLAGS)\n"
        adapter = SimpleNamespace(common=SimpleNamespace(read_relative=lambda *args: make.encode()))
        lock = {'native_tools': [{'id': 'clang', 'path': '/clang'}], 'sdk': {'path': '/sdk', 'version': '26.5'}}
        result = loader.recipes(Path('/out'), Path('/baseline'), adapter, lock)
        self.assertEqual(len(result), 6)
        self.assertTrue(all(row['argv'][0] == '/clang' for row in result))
        self.assertIn('/out/main.c', result[2]['argv'])
        self.assertIn('/out/second/main.o', result[5]['argv'])



class LoaderComparison(unittest.TestCase):
    def test_complete_payload_uses_both_new_loader_outputs(self):
        spec = importlib.util.spec_from_file_location('_loader_complete_inventory', ROOT / 'tools/dxmt/deterministic_reproduce.py')
        reproduction = importlib.util.module_from_spec(spec); spec.loader.exec_module(reproduction)
        path = 'wine/lib/wine/aarch64-unix/wine'
        old = {'path': path, 'kind': 'file', 'sha256': 'a' * 64, 'size_bytes': 1, 'mode': 0o755}
        facts = {'sha256': 'b' * 64, 'size_bytes': 2, 'mode': 0o755}
        proof = {'inputs': {'install/lib/wine/aarch64-unix/wine': {'sha256': 'a' * 64}},
                 'outputs': {'first/wine': facts, 'second/wine': facts}}
        calls = []
        def verify(root, adapter, baseline):
            calls.append(baseline); return proof
        adapter = SimpleNamespace(loader_root=Path('/loader'), loader_module=SimpleNamespace(verify=verify),
                                  loader_reference=lambda: {'path': '/loader', 'sha256': 'c' * 64})
        left, right, origins = reproduction.loader_inventory_views(adapter, [old], [old], {'baseline_root': '/baseline'})
        self.assertEqual(left[0]['sha256'], facts['sha256'])
        self.assertEqual(right[0]['sha256'], facts['sha256'])
        self.assertEqual(old['sha256'], 'a' * 64)
        self.assertEqual(origins['loader_reservation']['candidate_output'], 'second/wine')
        self.assertEqual(calls, [Path('/baseline')])
        with self.assertRaisesRegex(reproduction.Error, 'loader_baseline'):
            reproduction.loader_inventory_views(adapter, left, right, {'baseline_root': '/baseline'})


if __name__ == '__main__': unittest.main()
