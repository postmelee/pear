"""Build-record rejection tests using owned synthetic files, never Wine execution."""
import copy
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/wine'))
from common import Error, encoded, sha256
import build
import verify


def arm64ec_bytes():
    """Owned PE fixture with bounded CHPE v2 ARM64EC and x64 guest ranges."""
    data = bytearray(4096)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 60, 128)
    data[128:132] = b'PE\0\0'
    struct.pack_into('<HH', data, 132, 0x8664, 1)
    struct.pack_into('<H', data, 148, 240)
    opt = 152
    struct.pack_into('<H', data, opt, 0x20B)
    struct.pack_into('<Q', data, opt + 24, 0x180000000)
    struct.pack_into('<I', data, opt + 56, 0x3000)
    struct.pack_into('<I', data, opt + 108, 16)
    struct.pack_into('<II', data, opt + 112 + 10 * 8, 0x1000, 320)
    section = opt + 240
    data[section:section + 8] = b'.text\0\0\0'
    struct.pack_into('<IIII', data, section + 8, 3584, 0x1000, 3584, 512)
    struct.pack_into('<I', data, section + 36, 0x60000020)
    struct.pack_into('<I', data, 512, 320)
    struct.pack_into('<Q', data, 512 + 0xC8, 0x180001200)
    struct.pack_into('<III', data, 1024, 2, 0x1300, 2)
    struct.pack_into('<IIII', data, 1280, 0x1401, 16, 0x1502, 16)
    return bytes(data)


class PublicationPolicyTests(unittest.TestCase):
    def test_source_argument_policy_preserves_only_absent_legacy_records(self):
        self.assertEqual(build.source_argument_policy({}), 'legacy_absolute_v1')
        self.assertEqual(build.source_argument_policy({'source_argument_policy': 'stable_relative_v1'}),
                         'stable_relative_v1')
        for value in ('legacy_absolute_v1', 'stable_relative_v2', '', None, True, 1, []):
            with self.subTest(value=value), self.assertRaisesRegex(Error, 'build_source_argument_policy'):
                build.source_argument_policy({'source_argument_policy': value})

    def test_legacy_builds_have_no_implicit_executable_publication_grant(self):
        self.assertEqual(build.code_publication_policy({}), 'none')
        self.assertEqual(build.code_publication_policy({'fixture_suite': 'api-abi'}), 'none')

    def test_unknown_or_unscoped_publication_policy_rejects(self):
        for policy in ('rwx', 'thread-jit', '', None, True):
            with self.subTest(policy=policy), self.assertRaisesRegex(Error, 'build_code_publication_policy'):
                build.code_publication_policy({'fixture_suite': 'api-abi', 'code_publication_policy': policy})
        with self.assertRaisesRegex(Error, 'build_code_publication_scope'):
            build.code_publication_policy({'code_publication_policy': 'page-wx'})
        self.assertEqual(build.code_publication_policy({'fixture_suite': 'api-abi',
                                                       'code_publication_policy': 'page-wx'}), 'page-wx')


class NativeArchitecturePolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.makefile = Path(self.temp.name) / 'Makefile'
        self.variants = {
            'arm64': {'id': 'arm64', 'pe_archs': ['aarch64']},
            'arm64ec-build': {'id': 'arm64ec-build', 'pe_archs': ['aarch64', 'arm64ec']},
        }

    def configuration(self, variant='arm64', flags=None, enabled=True):
        variant = self.variants[variant]
        fields = {'HOST_ARCH': 'aarch64', 'PE_ARCHS': ' '.join(variant['pe_archs']),
                  'aarch64_TARGET': 'aarch64-windows', 'arm64ec_TARGET': '',
                  'x86_64_TARGET': 'x86_64-windows' if variant['id'] == 'arm64ec-build' else '',
                  'APPKIT_LIBS': '-framework AppKit', 'CORETEXT_LIBS': '-framework CoreText',
                  'FREETYPE_LIBS': '', 'FONTCONFIG_LIBS': '', 'COREAUDIO_LIBS': ''}
        text = ''.join(key + ' = ' + value + '\n' for key, value in fields.items())
        text += 'dlls/winemac.drv/cocoa_app.o:\n'
        if flags is not None:
            text += ''.join('PEAR_NATIVE_ONLY_ARCH_CFLAGS = ' + value + '\n' for value in flags)
        self.makefile.write_text(text)
        return build.observed_configuration(self.makefile, variant, native_architecture_policy=enabled)

    def test_policy_comes_from_recorded_patch_not_current_series_or_override(self):
        for record in ({}, {'patches': []}, {'native_architecture_policy': True},
                       {'patches': [{'path': '0003k-image-observation-budget.patch'}]}):
            self.assertFalse(build.has_native_architecture_policy(record))
        self.assertTrue(build.has_native_architecture_policy({'patches': [
            {'path': '0003l-native-architecture-policy.patch'}]}))

    def test_historical_configuration_fields_are_unchanged(self):
        for variant in self.variants:
            old = self.configuration(variant, enabled=False)
            self.assertNotIn('PEAR_NATIVE_ONLY_ARCH_CFLAGS', old)
            self.assertEqual(self.configuration(variant, ['unassessed historical field'], False), old)

    def test_native_build_requires_one_exact_macro(self):
        actual = self.configuration(flags=['-DPEAR_NATIVE_ONLY_ARCH=1'])
        self.assertEqual(actual['PEAR_NATIVE_ONLY_ARCH_CFLAGS'], '-DPEAR_NATIVE_ONLY_ARCH=1')
        for flags in (None, [''], ['-DPEAR_NATIVE_ONLY_ARCH=0'],
                      ['-DPEAR_NATIVE_ONLY_ARCH=1', '-DPEAR_NATIVE_ONLY_ARCH=1'],
                      ['-DPEAR_NATIVE_ONLY_ARCH=1 -DOTHER=1']):
            with self.subTest(flags=flags), self.assertRaisesRegex(Error, 'build_native_architecture_macro_mismatch'):
                self.configuration(flags=flags)

    def test_companion_preserves_empty_policy_and_rejects_native_only_macro(self):
        actual = self.configuration('arm64ec-build', [''])
        self.assertEqual(actual['PEAR_NATIVE_ONLY_ARCH_CFLAGS'], '')
        for flags in (None, ['', ''], ['-DPEAR_NATIVE_ONLY_ARCH=1']):
            with self.subTest(flags=flags), self.assertRaisesRegex(Error, 'build_native_architecture_macro_mismatch'):
                self.configuration('arm64ec-build', flags)


class ArenaCapacityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.header = self.root / 'source/dlls/ntdll/unix/pear_pe_arena.h'
        self.header.parent.mkdir(parents=True)
        self.header.write_text('#define PEAR_ARENA_INTERIOR_BYTES ((SIZE_T)196608)\n'
            '#define PEAR_ARENA_ALIGNMENT ((SIZE_T)65536)\n'
            '#define PEAR_ARENA_MAX_IMAGE_BYTES ((SIZE_T)65536)\n'
            '#define PEAR_ARENA_MAX_SLOTS 3u\n#define PEAR_ARENA_PAGE_BYTES ((SIZE_T)4096)\n')
        self.install = self.root / 'install'
        self.install.mkdir()
        self.artifacts = {'files': []}
        self.add_image('one.dll', 4096)
        self.add_image('two.dll', 65536)

    def add_image(self, name, size, machine=0xAA64):
        data = bytearray(256)
        data[:2] = b'MZ'
        struct.pack_into('<I', data, 60, 64)
        data[64:68] = b'PE\0\0'
        struct.pack_into('<H', data, 68, machine)
        struct.pack_into('<H', data, 88, 0x20B)
        struct.pack_into('<I', data, 144, size)
        (self.install / name).write_bytes(data)
        self.artifacts['files'].append({'path': name, 'kind': 'pe', 'machine': machine})

    def evidence(self, variant="arm64"):
        return build.arena_capacity_evidence(self.root / 'source', self.install, self.artifacts, variant=variant)

    def test_inventory_includes_preparation_slot_and_largest_image_margin(self):
        self.add_image('unsupported-x64.exe', 65536, 0x8664)
        value = self.evidence()
        self.assertEqual(value['arm64_image_count'], 2)
        self.assertEqual(value['total_slot_bytes'], 131072)
        self.assertEqual(value['required_interior_bytes'], 196608)
        self.assertEqual(value['required_slots'], 3)
        self.assertFalse(value['wine_execution'])

    def test_extra_images_and_larger_image_cannot_silently_exceed_compiled_limits(self):
        self.add_image('third.dll', 4096)
        with self.assertRaisesRegex(Error, 'arena_capacity_inventory_exceeds_limits'):
            self.evidence()
        self.artifacts['files'].pop()
        data = bytearray((self.install / 'one.dll').read_bytes())
        struct.pack_into('<I', data, 144, 69632)
        (self.install / 'one.dll').write_bytes(data)
        with self.assertRaisesRegex(Error, 'arena_capacity_inventory_exceeds_limits'):
            self.evidence()

    def test_truncated_headers_invalid_sizes_and_duplicate_definitions_reject(self):
        path = self.install / 'one.dll'
        original = path.read_bytes()
        for data in (original[:80], original[:144] + bytes(4) + original[148:]):
            path.write_bytes(data)
            with self.assertRaises(Error):
                self.evidence()
        path.write_bytes(original)
        self.header.write_text(self.header.read_text() + '#define PEAR_ARENA_MAX_SLOTS 3u\n')
        with self.assertRaisesRegex(Error, 'arena_capacity_definition'):
            self.evidence()


    def copy_budget(self, image_size=4096):
        path = 'libexec/pear-stage3/lifetime-arm64.dll'
        (self.install / path).parent.mkdir(parents=True)
        self.add_image(path, image_size)
        self.header.write_text(self.header.read_text().replace('196608', '393216').replace('MAX_SLOTS 3u', 'MAX_SLOTS 6u') +
                               '#define PEAR_ARENA_RELOCATION_COPIES 2u\n')
        return path

    def test_two_actual_fixture_copy_sizes_are_added_to_inventory_margin(self):
        path = self.copy_budget()
        value = self.evidence()
        self.assertEqual(value['required_slots'], 6)
        self.assertEqual(value['required_interior_bytes'], 393216)
        self.assertEqual(value['fixture_copies'], {'path': path, 'count': 2, 'slot_bytes': 65536, 'total_bytes': 131072})
        self.assertEqual(value['arm64_image_count'], 3)

    def test_copy_budget_enforces_both_slot_and_byte_limits(self):
        self.copy_budget()
        original = self.header.read_text()
        for text in (original.replace('MAX_SLOTS 6u', 'MAX_SLOTS 5u'), original.replace('393216', '327680')):
            with self.subTest(text=text):
                self.header.write_text(text)
                with self.assertRaisesRegex(Error, 'arena_capacity_inventory_exceeds_limits'):
                    self.evidence()

    def test_larger_actual_copy_size_is_measured_instead_of_assuming_one_slot(self):
        self.copy_budget(69632)
        self.header.write_text(self.header.read_text().replace('393216', '655360').replace(
            'MAX_IMAGE_BYTES ((SIZE_T)65536)', 'MAX_IMAGE_BYTES ((SIZE_T)131072)'))
        value = self.evidence()
        self.assertEqual(value['fixture_copies']['slot_bytes'], 131072)
        self.assertEqual(value['fixture_copies']['total_bytes'], 262144)
        self.assertEqual(value['required_interior_bytes'], 655360)

    def test_missing_or_wrong_architecture_copy_source_rejects(self):
        self.header.write_text(self.header.read_text() + '#define PEAR_ARENA_RELOCATION_COPIES 2u\n')
        with self.assertRaisesRegex(Error, 'arena_fixture_copy_source_missing'):
            self.evidence()
        path = 'libexec/pear-stage3/lifetime-arm64.dll'
        (self.install / path).parent.mkdir(parents=True)
        self.add_image(path, 4096, 0x8664)
        with self.assertRaisesRegex(Error, 'arena_fixture_copy_source_missing'):
            self.evidence()

    def test_changed_duplicate_or_malformed_copy_count_rejects(self):
        self.copy_budget()
        original = self.header.read_text()
        for text in (original.replace('COPIES 2u', 'COPIES 1u'), original.replace('COPIES 2u', 'COPIES (2)'),
                     original + '#define PEAR_ARENA_RELOCATION_COPIES 2u\n'):
            with self.subTest(text=text):
                self.header.write_text(text)
                with self.assertRaisesRegex(Error, 'arena_fixture_copy_definition'):
                    self.evidence()

    def test_historical_capacity_record_has_no_retroactive_copy_fields(self):
        self.assertNotIn('fixture_copies', self.evidence())


    def test_native_evidence_shape_is_preserved_and_companion_fit_is_not_qualification(self):
        native = self.evidence()
        self.assertNotIn('assessment', native)
        companion = self.evidence('arm64ec-build')
        assessment = companion.pop('assessment')
        self.assertEqual(companion, native)
        self.assertEqual(assessment, {
            'scope': 'compile_only_arm64ec_companion',
            'image_measurement': 'arm64_outer_headers_including_arm64x',
            'fits_native_limits': True, 'native_runtime_qualification': 'unassessed'})

    def test_companion_reports_each_exceeded_native_limit_without_enlarging_it(self):
        original = self.header.read_text()
        for old, new in (('MAX_IMAGE_BYTES ((SIZE_T)65536)', 'MAX_IMAGE_BYTES ((SIZE_T)4096)'),
                         ('MAX_SLOTS 3u', 'MAX_SLOTS 2u'),
                         ('INTERIOR_BYTES ((SIZE_T)196608)', 'INTERIOR_BYTES ((SIZE_T)131072)')):
            with self.subTest(limit=old):
                self.header.write_text(original.replace(old, new))
                with self.assertRaisesRegex(Error, 'arena_capacity_inventory_exceeds_limits'):
                    self.evidence('arm64')
                value = self.evidence('arm64ec-build')
                self.assertFalse(value['assessment']['fits_native_limits'])
                self.assertEqual(value['required_slots'], 3)
                self.assertEqual(value['required_interior_bytes'], 196608)
                self.assertEqual(value['largest_slot_bytes'], 65536)
                self.assertEqual(value['header_sha256'], sha256(self.header))
                self.assertFalse(value['wine_execution'])
                self.assertEqual(self.header.read_text(), original.replace(old, new))

    def test_companion_still_rejects_invalid_header_geometry_and_missing_copy_source(self):
        original = self.header.read_text()
        for changed, error in ((original.replace('PAGE_BYTES ((SIZE_T)4096)',
                                                'PAGE_BYTES ((SIZE_T)16384)'), 'arena_capacity_geometry'),
                               (original + '#define PEAR_ARENA_RELOCATION_COPIES 2u\n',
                                'arena_fixture_copy_source_missing')):
            with self.subTest(error=error):
                self.header.write_text(changed)
                with self.assertRaisesRegex(Error, error):
                    self.evidence('arm64ec-build')
        self.header.write_text(original)
        (self.install / 'one.dll').write_bytes(b'not a PE')
        with self.assertRaisesRegex(Error, 'arena_capacity_pe_header'):
            self.evidence('arm64ec-build')
        with self.assertRaisesRegex(Error, 'build_variant'):
            self.evidence('unknown')

    def test_companion_replay_recomputes_assessment_and_cannot_bypass_native_gate(self):
        self.add_image('larger-arm64x-outer.dll', 131072)
        capacity = self.evidence('arm64ec-build')
        result = {'schema_version': 1, 'record_kind': 'wine_build', 'passed': True,
                  'variant': 'arm64ec-build', 'fixture_suite': 'mac-driver',
                  'code_publication_policy': 'page-wx', 'arena_capacity': capacity,
                  'native_artifact_count': 0, 'pe_artifact_count': 3}
        # Stub unrelated provenance gates; the replay uses real source and PE bytes
        # to recompute capacity, then compares it with the recorded assessment.
        with mock.patch.object(build, 'task_path', side_effect=Path), \
             mock.patch.object(build, 'load_json', return_value=result), \
             mock.patch.object(build, 'verify_build_evidence'), \
             mock.patch.object(build, 'verify_completion_revision'), \
             mock.patch.object(build, 'artifact_inventory', return_value=self.artifacts), \
             mock.patch.object(build, 'required_outputs'), \
             mock.patch.object(build, 'inventory', return_value=self.artifacts):
            self.assertIs(build.verify_build(self.root), result)
            result['arena_capacity'] = copy.deepcopy(capacity)
            result['arena_capacity']['assessment']['fits_native_limits'] = True
            with self.assertRaisesRegex(Error, 'build_arena_capacity_changed'):
                build.verify_build(self.root)
            result['arena_capacity'] = capacity
            result['variant'] = 'arm64'
            with self.assertRaisesRegex(Error, 'arena_capacity_inventory_exceeds_limits'):
                build.verify_build(self.root)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def test_content_mode_and_extra_files_change_identity(self):
        source = self.root / 'file'
        source.write_bytes(b'first')
        first = build.inventory(self.root)
        source.write_bytes(b'second')
        self.assertNotEqual(first, build.inventory(self.root))
        first = build.inventory(self.root)
        source.chmod(0o755)
        self.assertNotEqual(first, build.inventory(self.root))
        first = build.inventory(self.root)
        (self.root / 'extra').write_bytes(b'')
        self.assertNotEqual(first, build.inventory(self.root))

    def test_contained_link_is_recorded_but_escape_and_missing_target_reject(self):
        (self.root / 'target').write_bytes(b'owned')
        link = self.root / 'alias'
        link.symlink_to('target')
        observed = build.inventory(self.root)
        self.assertEqual(observed['symlinks'], [{'path': 'alias', 'target': 'target'}])
        link.unlink()
        link.symlink_to('../outside')
        with self.assertRaisesRegex(Error, 'install_link_escape'):
            build.inventory(self.root)

    def test_absolute_internal_alias_is_not_an_installable_relative_link(self):
        target = self.root / 'target'
        target.write_bytes(b'')
        (self.root / 'alias').symlink_to(target)
        with self.assertRaisesRegex(Error, 'install_link_escape'):
            build.inventory(self.root)

    def test_special_file_rejected_without_reading(self):
        import os
        os.mkfifo(self.root / 'pipe')
        with self.assertRaisesRegex(Error, 'build_special_file'):
            build.inventory(self.root)

    def test_intel_native_image_rejected(self):
        (self.root / 'intel').write_bytes(struct.pack('<IIIIIIII', 0xFEEDFACF, 0x1000007, 0, 2, 0, 0, 0, 0))
        with self.assertRaises(Error):
            build.inventory(self.root, binary=True)

    def test_native_arm64_and_guest_pe_are_distinct(self):
        (self.root / 'native').write_bytes(struct.pack('<IIIIIIII', 0xFEEDFACF, build.MACH_ARM64, 0, 2, 0, 0, 0, 0))
        pe = bytearray(88)
        pe[:2] = b'MZ'
        struct.pack_into('<I', pe, 60, 64)
        pe[64:68] = b'PE\0\0'
        struct.pack_into('<H', pe, 68, 0x8664)
        (self.root / 'guest').write_bytes(pe)
        rows = {x['path']: x for x in build.inventory(self.root, binary=True)['files']}
        self.assertEqual(rows['native']['kind'], 'macho')
        self.assertEqual(rows['guest']['kind'], 'pe')
        self.assertEqual(rows['guest']['machine'], 0x8664)


class PatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / 'runtime/wine/patches').mkdir(parents=True)
        patcher = mock.patch.object(build, 'REPO', self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def row(self, text):
        path = self.root / 'runtime/wine/patches/change.patch'
        path.write_text(text)
        return {'path': 'change.patch', 'sha256': sha256(path)}

    def test_pinned_regular_patch_accepted_without_applying_it(self):
        row = self.row('--- a/loader/main.c\n+++ b/loader/main.c\n@@ -1 +1 @@\n-old\n+new\n')
        self.assertEqual(build.validate_patch(None, row).name, 'change.patch')

    def test_wrong_digest_rejects(self):
        row = self.row('--- a/file\n+++ b/file\n')
        row['sha256'] = '0' * 64
        with self.assertRaisesRegex(Error, 'patch_digest_mismatch'):
            build.validate_patch(None, row)

    def test_escape_and_git_metadata_headers_reject(self):
        for name in ('../outside', '.git/config', '/absolute', 'a//b'):
            with self.subTest(name=name), self.assertRaises(Error):
                build.validate_patch(None, self.row('--- a/' + name + '\n+++ b/' + name + '\n'))

    def test_empty_and_ambiguous_headers_reject(self):
        for text in ('not a patch', '--- a/file\n+++ b/file\n--- a/file\n+++ b/file\n'):
            with self.subTest(text=text), self.assertRaises(Error):
                build.validate_patch(None, self.row(text))


class OutputCoverageTests(unittest.TestCase):
    def complete(self, companion=False):
        paths = {
            'lib/wine/aarch64-unix/wine': 'macho',
            'bin/wineserver': 'macho',
            'lib/wine/aarch64-unix/ntdll.so': 'macho',
            'lib/wine/aarch64-unix/winemac.so': 'macho',
            'lib/wine/aarch64-unix/win32u.so': 'macho',
            'lib/wine/aarch64-windows/ntdll.dll': 'pe',
            'lib/wine/aarch64-windows/wineboot.exe': 'pe',
            'libexec/pear-stage2/bootstrap-native': 'macho',
            'libexec/pear-stage2/sentinel': 'macho',
        }
        files = [{'path': path, 'kind': kind, 'architectures': [build.MACH_ARM64], 'machine': 0xAA64}
                 for path, kind in paths.items()]
        if companion:
            files.extend({'path': path, 'kind': 'pe', 'machine': 0x8664, 'pe_abi': 'arm64ec', 'chpe_version': 2,
                          'code_ranges': [{'code_kind': 'arm64ec'}, {'code_kind': 'x64'}]}
                         for path in sorted(build.ARM64EC_PATHS))
        return {'files': files, 'symlinks': []}

    def test_missing_required_module_or_sentinel_rejects(self):
        original = self.complete(companion=True)
        for row in original['files']:
            value = copy.deepcopy(original)
            value['files'] = [x for x in value['files'] if x['path'] != row['path']]
            with self.subTest(path=row['path']), self.assertRaisesRegex(Error, 'build_required_outputs_missing'):
                build.required_outputs(value, 'arm64ec-build')

    def test_wrong_pe_architecture_cannot_qualify_native_bootstrap(self):
        value = self.complete(companion=True)
        next(row for row in value['files'] if row['path'].endswith('aarch64-windows/ntdll.dll'))['machine'] = 0x8664
        with self.assertRaisesRegex(Error, 'build_pe_architecture'):
            build.required_outputs(value, 'arm64ec-build')

    def test_duplicate_artifact_and_wrong_native_slice_reject(self):
        value = self.complete()
        value['files'].append(value['files'][0].copy())
        with self.assertRaisesRegex(Error, 'build_duplicate_artifact'):
            build.required_outputs(value, 'arm64')
        value = self.complete()
        value['files'][0]['architectures'] = [0x1000007]
        with self.assertRaisesRegex(Error, 'build_native_architecture'):
            build.required_outputs(value, 'arm64')

    def test_companion_uses_native_paths_and_hybrid_proof_is_a_separate_gate(self):
        value = self.complete()
        build.required_outputs(value, 'arm64')
        value = self.complete(companion=True)
        build.required_outputs(value, 'arm64ec-build')
        value['files'].append({'path': 'lib/wine/arm64ec-windows/ntdll.dll', 'kind': 'pe', 'machine': 0x8664})
        with self.assertRaisesRegex(Error, 'build_unexpected_pe_path'):
            build.required_outputs(value, 'arm64ec-build')


    def stage3(self):
        value = self.complete()
        value['files'].append({'path': 'libexec/pear-stage3/api-launch', 'kind': 'macho',
                               'architectures': [build.MACH_ARM64]})
        value['files'].extend({'path': name, 'kind': 'pe', 'machine': machine}
                              for name, machine in build.STAGE3_PE.items())
        return value

    def test_control_pe_files_are_permitted_only_in_the_declared_fixture_suite(self):
        value = self.stage3()
        build.required_outputs(value, 'arm64', 'api-abi')
        with self.assertRaisesRegex(Error, 'build_unexpected_pe_path'):
            build.required_outputs(value, 'arm64', 'bootstrap')
        value['files'].append({'path': 'lib/wine/aarch64-windows/unexpected.dll',
                               'kind': 'pe', 'machine': 0x8664})
        with self.assertRaisesRegex(Error, 'build_pe_architecture'):
            build.required_outputs(value, 'arm64', 'api-abi')

    def test_missing_stage3_fixture_or_wrong_machine_rejects(self):
        for name in build.STAGE3_PE:
            value = self.stage3()
            value['files'] = [row for row in value['files'] if row['path'] != name]
            with self.subTest(name=name), self.assertRaisesRegex(Error, 'build_required_outputs_missing'):
                build.required_outputs(value, 'arm64', 'api-abi')
            value = self.stage3()
            row = next(row for row in value['files'] if row['path'] == name)
            row['machine'] = 0x14c if row['machine'] != 0x14c else 0xAA64
            with self.subTest(name=name), self.assertRaisesRegex(Error, 'build_fixture_pe_architecture'):
                build.required_outputs(value, 'arm64', 'api-abi')

    def test_page_wx_requires_each_original_dll_and_preserves_legacy_coverage(self):
        legacy = self.stage3()
        with self.assertRaisesRegex(Error, 'build_required_outputs_missing'):
            build.required_outputs(legacy, 'arm64', 'api-abi', 'page-wx')
        value = copy.deepcopy(legacy)
        value['files'].extend({'path': name, 'kind': 'pe', 'machine': machine}
                             for name, machine in build.PAGE_WX_PE.items())
        build.required_outputs(value, 'arm64', 'api-abi', 'page-wx')
        with self.assertRaisesRegex(Error, 'build_unexpected_pe_path'):
            build.required_outputs(value, 'arm64', 'api-abi', 'none')
        for name in build.PAGE_WX_PE:
            changed = copy.deepcopy(value)
            next(row for row in changed['files'] if row['path'] == name)['machine'] = 0x8664
            with self.subTest(name=name), self.assertRaisesRegex(Error, 'build_fixture_pe_architecture'):
                build.required_outputs(changed, 'arm64', 'api-abi', 'page-wx')

    def test_legacy_recipe_does_not_retroactively_include_new_dll_commands(self):
        with mock.patch.object(build, 'native_tool', return_value=Path('/owned/clang')):
            legacy = build.fixture_commands(Path('/owned/build'), Path('/owned/tools'),
                                            {'sdk': {'path': '/owned/sdk'}}, 'api-abi')
            current = build.fixture_commands(Path('/owned/build'), Path('/owned/tools'),
                                             {'sdk': {'path': '/owned/sdk'}}, 'api-abi', 'page-wx')
        self.assertTrue(all(current[key] == value for key, value in legacy.items()))
        self.assertEqual(set(current) - set(legacy), {'fixture-lifetime-dll',
            'fixture-missing-name-importlib', 'fixture-missing-name-dll',
            'fixture-missing-ordinal-importlib', 'fixture-missing-ordinal-dll'})
        self.assertEqual(build.fixture_sources({'fixture_suite': 'api-abi'}), build.FIXTURE_SUITES['api-abi'])

    def test_unknown_fixture_suite_cannot_fall_back_to_bootstrap(self):
        with self.assertRaisesRegex(Error, 'build_fixture_suite'):
            build.fixture_suite({'fixture_suite': 'unknown'})
        with self.assertRaisesRegex(Error, 'build_fixture_suite'):
            build.required_outputs(self.complete(), 'arm64', 'unknown')


class SourceDerivationTests(unittest.TestCase):
    def test_declared_changes_are_required_and_extra_changes_rejected(self):
        original = {'files': [{'path': 'a.c', 'mode': '100644', 'sha256': 'a' * 64}]}
        patches = [{'changes': [{'path': 'a.c', 'before_sha256': 'a' * 64, 'after_sha256': 'b' * 64},
                                {'path': 'b.h', 'before_sha256': None, 'after_sha256': 'c' * 64}]}]
        expected = build.expected_source_inventory(original, patches)
        build.verify_source_derivation(expected, original, patches)
        for mutation in ('extra', 'missing', 'modified', 'mode'):
            value = copy.deepcopy(expected)
            if mutation == 'extra':
                value['files'].append({'path': 'extra.c', 'sha256': 'd' * 64, 'mode': 0o644, 'kind': 'data'})
            elif mutation == 'missing':
                value['files'].pop()
            elif mutation == 'modified':
                value['files'][0]['sha256'] = 'e' * 64
            else:
                value['files'][0]['mode'] = 0o755
            with self.subTest(mutation=mutation), self.assertRaisesRegex(Error, 'source_patch_derivation_mismatch'):
                build.verify_source_derivation(value, original, patches)

    def test_reordered_or_missing_preimage_rejected(self):
        original = {'files': [{'path': 'a.c', 'mode': '100644', 'sha256': 'a' * 64}]}
        with self.assertRaisesRegex(Error, 'patch_preimage_changed'):
            build.expected_source_inventory(original, [{'changes': [
                {'path': 'a.c', 'before_sha256': 'b' * 64, 'after_sha256': 'c' * 64}]}])


class ComponentGateTests(unittest.TestCase):
    def test_later_fixture_addition_preserves_old_compiler_evidence_but_changes_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            names = ('toolchain_native.c', 'toolchain_pe.c', 'toolchain_seh.S', 'toolchain_cpp.cpp')
            for name in names:
                (root / name).write_text(name)
            hashes = {name: sha256(root / name) for name in names}
            (root / 'bootstrap_native.c').write_text('later-stage fixture')
            verify.verify_fixture_set(hashes, root)
            (root / names[0]).write_text('changed compiler fixture')
            with self.assertRaisesRegex(Error, 'fixture_identity_mismatch'):
                verify.verify_fixture_set(hashes, root)
            with self.assertRaisesRegex(Error, 'fixture_identity_mismatch'):
                verify.verify_fixture_set({}, root)

    def test_variant_gate_rejects_mixed_patch_or_tool_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            roots = [Path(directory) / name for name in ('native', 'companion')]
            for root in roots:
                root.mkdir()
                (root / 'build.json').write_text('{}')
                (root / 'modules.json').write_text('{}')
            common = {'record_hashes': {}, 'source_prepared_sha256': 'a' * 64,
                      'tool_prepared_sha256': 'b' * 64, 'source_manifest': {'sha256': 'c' * 64},
                      'patches': [], 'fixture_hashes': {}, 'producer_sha256': {}, 'sdk': {},
                      'native_artifact_count': 1, 'pe_artifact_count': 1,
                      'artifacts_manifest': {'sha256': 'd' * 64}}
            first = dict(common, variant='arm64')
            second = dict(common, variant='arm64ec-build')
            artifacts = {'files': [{'kind': 'macho'}, {'kind': 'pe'}]}
            with mock.patch.object(build, 'verify_build', side_effect=[first, second]), \
                 mock.patch.object(build, 'artifact_inventory', return_value=artifacts), \
                 mock.patch('modules.validate_inventory', return_value={}):
                self.assertTrue(verify.validate_builds(*roots)['gate_passed'])
            second = dict(second, tool_prepared_sha256='e' * 64)
            with mock.patch.object(build, 'verify_build', side_effect=[first, second]), \
                 self.assertRaisesRegex(Error, 'build_variant_inputs_differ'):
                verify.validate_builds(*roots)




class FinalizationTests(unittest.TestCase):
    """Resume only finished validation failures; source and evidence remain real files."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name).resolve()
        self.root = self.repo / '.build/task4/result'
        self.root.mkdir(parents=True)
        self.inputs = self.repo / '.build/task4/inputs'
        self.inputs.mkdir()
        self.tools = self.repo / '.build/task4/tools'
        self.tools.mkdir()
        self.patchers = [mock.patch.object(build, 'REPO', self.repo),
                         mock.patch.object(build, 'task_path', side_effect=Path),
                         mock.patch.object(build, 'verify_prepared', return_value={}),
                         mock.patch.object(build, 'verify_prepared_tools', side_effect=self.prepared_tools),
                         mock.patch.object(build, 'inspect_sdk', return_value={'version': 'test'}),
                         mock.patch.object(build, 'native_tool', return_value=Path('/unused/native')),
                         mock.patch.object(build, 'run_build_command', side_effect=AssertionError('must not execute'))]
        for patcher in self.patchers:
            patcher.start()
            self.addCleanup(patcher.stop)
        config = {'schema_version': 1, 'record_kind': 'wine_build_config',
                  'variants': [{'id': 'arm64', 'pe_archs': ['aarch64'], 'configure_args': ['--enable-archs=aarch64']}]}
        for key, name in build.RECORDS.items():
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            value = config if key == 'config' else {'patches': []} if key == 'patch_series' else {
                'schema_version': 1, 'record_kind': 'wine_toolchain', 'sdk': {'path': '/unused/sdk'}} if key == 'toolchain' else {}
            path.write_bytes(encoded(value))
        for name in ('bootstrap_native.c', 'sentinel.c'):
            path = self.repo / 'tests/wine/fixtures' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('owned fixture: ' + name)
        (self.inputs / 'prepared.json').write_text('{}')
        (self.tools / 'prepared.json').write_text('{}')
        source = self.root / 'source'
        source.mkdir()
        (source / 'file.c').write_text('owned source')
        (source / 'file.c').chmod(0o644)
        (self.inputs / 'wine-files.json').write_bytes(encoded({'files': [
            {'path': 'file.c', 'mode': '100644', 'sha256': sha256(source / 'file.c')}]}))
        (self.root / 'source-files.json').write_bytes(encoded(build.inventory(source)))
        objects = self.root / 'objects'
        objects.mkdir()
        fields = {'HOST_ARCH': 'aarch64', 'PE_ARCHS': 'aarch64', 'aarch64_TARGET': 'aarch64-windows',
                  'arm64ec_TARGET': '', 'x86_64_TARGET': '', 'APPKIT_LIBS': '-framework AppKit',
                  'CORETEXT_LIBS': '-framework CoreText', 'FREETYPE_LIBS': '', 'FONTCONFIG_LIBS': '', 'COREAUDIO_LIBS': ''}
        (objects / 'Makefile').write_text(''.join(key + ' = ' + value + '\n' for key, value in fields.items())
                                        + 'dlls/winemac.drv/cocoa_app.o:\n')
        (objects / 'config.log').write_text('owned configuration evidence')
        producer = self.root / 'producer'
        producer.mkdir()
        for name in build.PRODUCERS:
            (producer / name).write_text('original producer: ' + name)
        commands = []
        (objects / '.pear-build-logs').mkdir()
        args = {
            'configure': ['/bin/sh', str(self.root / 'source/configure'), '--prefix=' + str(self.root / 'install'),
                          '--with-mingw=' + str(self.tools / 'llvm-mingw/bin/clang'), '--enable-archs=aarch64'],
            'make': ['/unused/native', '-j4'], 'install': ['/unused/native', 'install']}
        for ident, filename, output in (('fixture-bootstrap', 'bootstrap_native.c', 'bootstrap-native'),
                                        ('fixture-sentinel', 'sentinel.c', 'sentinel')):
            args[ident] = ['/unused/native', '-arch', 'arm64', '-isysroot', '/unused/sdk',
                '-std=c11', '-Wall', '-Wextra', '-Werror', str(self.repo / 'tests/wine/fixtures' / filename),
                '-o', str(self.root / 'install/libexec/pear-stage2' / output)]
        for ident in ('configure', 'make', 'install', 'fixture-bootstrap', 'fixture-sentinel'):
            command = {'id': ident, 'argv': ['/usr/bin/arch', '-arm64', *args[ident]], 'cwd': str(objects),
                       'exit_code': 0, 'timed_out': False, 'output_limit': False, 'interrupted': False}
            for stream in ('stdout', 'stderr'):
                path = objects / '.pear-build-logs' / (ident + '.' + stream)
                path.write_text(ident + ': ' + stream)
                command[stream] = path.read_text()
                command[stream + '_log'] = {'path': str(path), 'sha256': sha256(path), 'size_bytes': path.stat().st_size}
            commands.append(command)
        for row in OutputCoverageTests().complete()['files']:
            if '/arm64ec-windows/' in row['path']:
                continue
            path = self.root / 'install' / row['path']
            path.parent.mkdir(parents=True, exist_ok=True)
            if row['kind'] == 'macho':
                data = struct.pack('<IIIIIIII', 0xFEEDFACF, build.MACH_ARM64, 0, 2, 0, 0, 0, 0)
            else:
                data = bytearray(88)
                data[:2] = b'MZ'
                struct.pack_into('<I', data, 60, 64)
                data[64:68] = b'PE\0\0'
                struct.pack_into('<H', data, 68, 0xAA64)
            path.write_bytes(data)
        patch_path = Path('/usr/bin/patch')
        self.result = {'schema_version': 1, 'record_kind': 'wine_build', 'scope': 'wine_component',
            'variant': 'arm64', 'passed': False, 'error': 'build_required_outputs_missing',
            'private_error': 'original validation failure', 'wine_runtime_execution': False,
            'record_hashes': {key: sha256(self.repo / path) for key, path in build.RECORDS.items()},
            'path_alias': {'invoked': str(self.repo / '.build/task4'), 'resolved': str(self.repo / '.build/task4')},
            'patches': [], 'source_inputs_root': str(self.inputs), 'tools_root': str(self.tools),
            'source_prepared_sha256': sha256(self.inputs / 'prepared.json'),
            'tool_prepared_sha256': sha256(self.tools / 'prepared.json'),
            'source_manifest': {'path': 'source-files.json', 'sha256': sha256(self.root / 'source-files.json')},
            'install_root': str(self.root / 'install'), 'sdk': {'version': 'test'},
            'patch_tool': {'path': str(patch_path), 'sha256': sha256(patch_path), **build.inspect_macho(patch_path)},
            'producer_sha256': {name: sha256(producer / name) for name in build.PRODUCERS},
            'fixture_hashes': {name: sha256(self.repo / 'tests/wine/fixtures' / name)
                               for name in ('bootstrap_native.c', 'sentinel.c')},
            'commands': commands, 'configuration': fields,
            'makefile_sha256': sha256(objects / 'Makefile'), 'config_log_sha256': sha256(objects / 'config.log')}
        self.save()

    def prepared_tools(self, lock, path):
        return {'lock_sha256': sha256(self.repo / build.RECORDS['toolchain'])}

    def save(self):
        (self.root / 'build.json').write_bytes(encoded(self.result))

    def assert_rejected_preserving_record(self, code):
        original = (self.root / 'build.json').read_bytes()
        with self.assertRaisesRegex(Error, code):
            build.finalize_only(self.root)
        self.assertEqual((self.root / 'build.json').read_bytes(), original)
        self.assertFalse((self.root / 'build-before-finalization.json').exists())
        self.assertFalse((self.root / 'finalizer').exists())

    def relative_policy(self):
        self.result['source_argument_policy'] = 'stable_relative_v1'
        self.result['commands'][0]['argv'][3] = '../source/configure'
        makefile = self.root / 'objects/Makefile'
        makefile.write_text(makefile.read_text() + 'srcdir = ../source\n')
        self.result['configuration']['srcdir'] = '../source'
        self.result['makefile_sha256'] = sha256(makefile)

    def test_legacy_absolute_commands_remain_verified_without_policy(self):
        build.verify_build_evidence(self.root, self.result, current=False)
        self.result['commands'][0]['argv'][3] = '../source/configure'
        with self.assertRaisesRegex(Error, 'build_command_invocation'):
            build.verify_build_evidence(self.root, self.result, current=False)

    def test_stable_relative_configuration_and_exact_command_are_bound(self):
        self.relative_policy()
        build.verify_build_evidence(self.root, self.result, current=False)
        for script in (str(self.root / 'source/configure'), './configure', '../../source/configure'):
            self.result['commands'][0]['argv'][3] = script
            with self.subTest(script=script), self.assertRaisesRegex(Error, 'build_command_invocation'):
                build.verify_build_evidence(self.root, self.result, current=False)
        self.result['commands'][0]['argv'][3] = '../source/configure'
        self.result['commands'][0]['cwd'] = str(self.root)
        with self.assertRaisesRegex(Error, 'build_command_invocation'):
            build.verify_build_evidence(self.root, self.result, current=False)

    def test_relative_policy_requires_one_actual_relative_srcdir(self):
        self.relative_policy()
        makefile = self.root / 'objects/Makefile'
        original = makefile.read_text()
        for replacement in ('', 'srcdir = /arbitrary/source\n', 'srcdir = $(SOURCE_ROOT)\n',
                            'srcdir = ../source\nsrcdir = ../source\n'):
            makefile.write_text(original.replace('srcdir = ../source\n', replacement))
            self.result['makefile_sha256'] = sha256(makefile)
            with self.subTest(replacement=replacement), self.assertRaisesRegex(Error, 'build_relative_srcdir_mismatch'):
                build.verify_build_evidence(self.root, self.result, current=False)

    def test_unknown_policy_cannot_bypass_historical_or_current_validation(self):
        self.result['source_argument_policy'] = None
        for current in (False, True):
            with self.subTest(current=current), self.assertRaisesRegex(Error, 'build_source_argument_policy'):
                build.verify_build_evidence(self.root, self.result, current=current)

    def test_page_wx_build_requires_actual_configured_native_pe_macro(self):
        makefile = self.root / 'objects/Makefile'
        variant = {'id': 'arm64', 'pe_archs': ['aarch64']}
        with self.assertRaisesRegex(Error, 'build_publication_macro_mismatch'):
            build.observed_configuration(makefile, variant, 'page-wx')
        makefile.write_text(makefile.read_text() + 'PEAR_NATIVE_PE_PUBLICATION_CFLAGS = -DPEAR_NATIVE_PE_PUBLICATION=1\n')
        value = build.observed_configuration(makefile, variant, 'page-wx')
        self.assertEqual(value['PEAR_NATIVE_PE_PUBLICATION_CFLAGS'], '-DPEAR_NATIVE_PE_PUBLICATION=1')

    def test_historical_verifier_derives_macro_gate_from_its_own_patch_record(self):
        # Source/command derivation has its own tests; exercise the recorded
        # policy selection at the verifier boundary without running a build.
        self.result['patches'] = [{'path': '0003l-native-architecture-policy.patch'}]
        with mock.patch.object(build, 'verify_source_derivation'), \
             mock.patch.object(build, 'verify_build_commands'), \
             self.assertRaisesRegex(Error, 'build_native_architecture_macro_mismatch'):
            build.verify_build_evidence(self.root, self.result, current=False)
        self.result['patches'] = []
        build.verify_build_evidence(self.root, self.result, current=False)

    def test_rehashed_series_cannot_change_recorded_publication_policy(self):
        path = self.repo / build.RECORDS['patch_series']
        path.write_bytes(encoded({'patches': [], 'fixture_suite': 'api-abi',
                                 'code_publication_policy': 'page-wx'}))
        self.result['record_hashes']['patch_series'] = sha256(path)
        self.result['fixture_suite'] = 'api-abi'
        self.result['code_publication_policy'] = 'none'
        self.save()
        self.assert_rejected_preserving_record('build_code_publication_changed')

    def test_completed_failure_finalizes_without_commands_and_retains_both_producers(self):
        raw = (self.root / 'build.json').read_bytes()
        original_hashes = self.result['producer_sha256'].copy()
        self.assertEqual(build.finalize_only(self.root), 0)
        self.assertEqual((self.root / 'build-before-finalization.json').read_bytes(), raw)
        finalized = build.verify_build(self.root)
        self.assertTrue(finalized['passed'])
        self.assertEqual(finalized['producer_sha256'], original_hashes)
        self.assertNotEqual(finalized['completion_revision']['finalizer_sha256'], original_hashes)
        self.assertFalse(finalized['completion_revision']['build_commands_executed'])
        build.run_build_command.assert_not_called()
        with self.assertRaisesRegex(Error, 'build_not_finalizable'):
            build.finalize_only(self.root)

    def test_exact_companion_architecture_validation_failure_finalizes(self):
        config_path = self.repo / build.RECORDS['config']
        config = build.load_json(config_path)
        config['variants'].append({'id': 'arm64ec-build', 'pe_archs': ['aarch64', 'arm64ec'],
                                   'configure_args': ['--enable-archs=aarch64,arm64ec']})
        config_path.write_bytes(encoded(config))
        makefile = self.root / 'objects/Makefile'
        makefile.write_text(makefile.read_text().replace('PE_ARCHS = aarch64\n', 'PE_ARCHS = aarch64 arm64ec\n')
                           .replace('x86_64_TARGET = \n', 'x86_64_TARGET = x86_64-windows\n'))
        self.result['variant'] = 'arm64ec-build'
        self.result['error'] = 'build_pe_architecture'
        self.result['record_hashes']['config'] = sha256(config_path)
        self.result['makefile_sha256'] = sha256(makefile)
        self.result['configuration'] = build.observed_configuration(makefile, config['variants'][1])
        self.result['commands'][0]['argv'][-1] = '--enable-archs=aarch64,arm64ec'
        for name in build.ARM64EC_PATHS:
            path = self.root / 'install' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(arm64ec_bytes())
        self.save()
        raw = (self.root / 'build.json').read_bytes()
        self.assertEqual(build.finalize_only(self.root), 0)
        self.assertEqual((self.root / 'build-before-finalization.json').read_bytes(), raw)
        self.assertTrue(build.verify_build(self.root)['passed'])
        build.run_build_command.assert_not_called()

    def test_native_architecture_failure_is_not_finalizable(self):
        self.result['error'] = 'build_pe_architecture'
        self.save()
        self.assert_rejected_preserving_record('build_not_finalizable')

    def test_partial_commands_cannot_resume(self):
        self.result['commands'].pop()
        self.save()
        self.assert_rejected_preserving_record('build_command_coverage')

    def test_failed_timed_out_interrupted_commands_cannot_resume(self):
        for key, value in (('exit_code', 1), ('timed_out', True), ('output_limit', True), ('interrupted', True)):
            with self.subTest(key=key):
                original = self.result['commands'][0][key]
                self.result['commands'][0][key] = value
                self.save()
                self.assert_rejected_preserving_record('build_command_outcome')
                self.result['commands'][0][key] = original

    def test_other_failure_or_existing_completion_cannot_resume(self):
        for mutation in ('error', 'passed', 'artifacts_manifest', 'completion_revision'):
            with self.subTest(mutation=mutation):
                original = copy.deepcopy(self.result)
                self.result[mutation] = 'build_operation_failed' if mutation == 'error' else True if mutation == 'passed' else {}
                self.save()
                self.assert_rejected_preserving_record('build_not_finalizable')
                self.result = original

    def test_changed_input_tools_source_log_configuration_and_fixture_reject(self):
        paths = [(self.repo / build.RECORDS['inputs'], 'build_input_changed'),
                 (self.tools / 'prepared.json', 'build_prepared_tools_changed'),
                 (self.root / 'source/file.c', 'built_source_changed'),
                 (self.root / 'objects/.pear-build-logs/make.stdout', 'build_command_log_changed'),
                 (self.root / 'objects/config.log', 'build_configuration_changed'),
                 (self.repo / 'tests/wine/fixtures/sentinel.c', 'build_fixture_changed')]
        for path, code in paths:
            with self.subTest(path=path):
                old = path.read_bytes()
                path.write_bytes(old + b' changed')
                self.assert_rejected_preserving_record(code)
                path.write_bytes(old)

    def test_missing_output_or_existing_destination_rejects(self):
        path = self.root / 'install/lib/wine/aarch64-unix/win32u.so'
        path.rename(path.with_name('wrong.so'))
        self.assert_rejected_preserving_record('build_required_outputs_missing')
        path.with_name('wrong.so').rename(path)
        (self.root / 'finalizer').mkdir()
        with self.assertRaisesRegex(Error, 'build_finalization_destination_exists'):
            build.finalize_only(self.root)

    def test_both_producer_snapshots_and_original_record_bound_after_finalization(self):
        build.finalize_only(self.root)
        for path, code in ((self.root / 'producer/build.py', 'build_producer_changed'),
                           (self.root / 'finalizer/build.py', 'build_producer_changed'),
                           (self.root / 'build-before-finalization.json', 'build_original_record_changed')):
            with self.subTest(path=path):
                old = path.read_bytes()
                path.write_bytes(old + b' altered')
                with self.assertRaisesRegex(Error, code):
                    build.verify_build(self.root)
                path.write_bytes(old)
        finalized = build.load_json(self.root / 'build.json')
        finalized['storage'] = {'invented': True}
        (self.root / 'build.json').write_bytes(encoded(finalized))
        with self.assertRaisesRegex(Error, 'build_revision_evidence_changed'):
            build.verify_build(self.root)

    def test_changed_command_identity_and_log_preview_reject(self):
        for mutation in ('argv', 'order', 'cwd', 'preview'):
            with self.subTest(mutation=mutation):
                original = copy.deepcopy(self.result)
                if mutation == 'argv':
                    self.result['commands'][0]['argv'][-1] = '--unapproved'
                elif mutation == 'order':
                    self.result['commands'][0], self.result['commands'][1] = self.result['commands'][1], self.result['commands'][0]
                elif mutation == 'cwd':
                    self.result['commands'][0]['cwd'] = str(self.root / 'source')
                else:
                    self.result['commands'][0]['stdout'] = 'invented preview'
                self.save()
                self.assert_rejected_preserving_record('build_command_')
                self.result = original

    def test_cli_rejects_mixed_modes_without_build_or_finalization(self):
        with mock.patch.object(build, 'finalize_only') as finalize, mock.patch.object(build, 'build') as compile:
            with mock.patch('sys.stdout'):
                self.assertEqual(build.main(['--finalize-only', str(self.root), '--jobs', '2']), 1)
            finalize.assert_not_called()
            compile.assert_not_called()


class WinmdMetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'share/wine/winmd/windows.system.winmd'
        self.path.parent.mkdir(parents=True)
        self.data = bytearray(1024)
        self.data[:2] = b'MZ'
        struct.pack_into('<I', self.data, 60, 128)
        self.data[128:132] = b'PE\0\0'
        struct.pack_into('<HH', self.data, 132, 0x14C, 1)
        struct.pack_into('<H', self.data, 148, 224)
        self.opt = 152
        struct.pack_into('<H', self.data, self.opt, 0x10B)
        struct.pack_into('<I', self.data, self.opt + 92, 16)
        struct.pack_into('<II', self.data, self.opt + 96 + 14 * 8, 0x1000, 72)
        section = self.opt + 224
        self.data[section:section + 8] = b'.text\0\0\0'
        struct.pack_into('<IIII', self.data, section + 8, 512, 0x1000, 512, 512)
        struct.pack_into('<I', self.data, section + 36, 0x40000020)
        struct.pack_into('<IHHIIII', self.data, 512, 72, 2, 5, 0x1048, 40, 1, 0)
        self.data[584:588] = b'BSJB'
        struct.pack_into('<HHII', self.data, 588, 1, 1, 0, 20)
        self.data[600:620] = b'WindowsRuntime 1.4\0\0'
        self.path.write_bytes(self.data)

    def test_exact_pinned_shape_is_metadata_and_not_executable_pe(self):
        row = build.inventory(self.root, binary=True)['files'][0]
        self.assertEqual(row['kind'], 'pe_metadata')
        self.assertEqual(row['machine'], 0x14C)
        self.assertTrue(row['metadata_only'])

    def test_entrypoints_native_code_sections_and_bad_metadata_rejected(self):
        for offset, value in ((self.opt + 4, 1), (self.opt + 16, 1),
                              (self.opt + 224 + 36, 0x60000020),
                              (512 + 16, 0), (512 + 20, 1), (512 + 24, 1),
                              (512 + 8, 0xFFFFF000), (584, 0), (self.opt + 96, 0x1000)):
            with self.subTest(offset=offset):
                data = bytearray(self.data)
                struct.pack_into('<I', data, offset, value)
                self.path.write_bytes(data)
                with self.assertRaises(Error):
                    build.inventory(self.root, binary=True)

    def test_extension_or_path_alone_does_not_exempt_guest_architecture(self):
        other = self.path.with_name('unapproved.winmd')
        self.path.rename(other)
        row = build.inventory(self.root, binary=True)['files'][0]
        self.assertEqual(row['kind'], 'pe')
        artifacts = OutputCoverageTests().complete()
        artifacts['files'].append(row)
        with self.assertRaisesRegex(Error, 'build_unexpected_pe_path'):
            build.required_outputs(artifacts, 'arm64')

    def test_truncated_metadata_cannot_qualify(self):
        for size in (20, 151, 500, 619):
            with self.subTest(size=size):
                self.path.write_bytes(self.data[:size])
                with self.assertRaises(Error):
                    build.inspect_winmd(self.path)


class Arm64ecClassificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'lib/wine/aarch64-windows/xtajit64.dll'
        self.path.parent.mkdir(parents=True)
        self.path.write_bytes(arm64ec_bytes())

    def test_positive_metadata_is_companion_only_and_retains_raw_amd64_header(self):
        row = build.inventory(self.root, binary=True)['files'][0]
        self.assertEqual(row['machine'], 0x8664)
        self.assertEqual(row['pe_abi'], 'arm64ec')
        self.assertEqual([entry['code_kind'] for entry in row['code_ranges']], ['arm64ec', 'x64'])
        artifact = OutputCoverageTests().complete(companion=True)
        artifact['files'] = [item for item in artifact['files'] if item['path'] != row['path']] + [row]
        build.required_outputs(artifact, 'arm64ec-build')
        with self.assertRaisesRegex(Error, 'build_pe_architecture'):
            build.required_outputs(artifact, 'arm64')

    def test_plain_x64_missing_chpe_unmapped_and_wrong_kind_ranges_reject(self):
        for fmt, offset, value in (('Q', 512 + 0xC8, 0), ('I', 1024, 1),
                                  ('I', 1028, 0xFFFF0000), ('I', 1032, 0),
                                  ('I', 1280, 0x1400), ('I', 1280, 0x1402),
                                  ('I', 1284, 0), ('I', 1284, 0xFFFFFFFF),
                                  ('I', 512 + 0xE0, 1), ('I', 392 + 36, 0x40000020)):
            with self.subTest(offset=offset, value=value):
                data = bytearray(arm64ec_bytes())
                struct.pack_into('<' + fmt, data, offset, value)
                self.path.write_bytes(data)
                with self.assertRaises(Error):
                    build.inventory(self.root, binary=True)

    def test_code_range_can_span_contiguous_executable_raw_padding_but_not_a_gap(self):
        data = bytearray(arm64ec_bytes())
        struct.pack_into('<H', data, 134, 2)
        struct.pack_into('<IIII', data, 392 + 8, 0x4F8, 0x1000, 0x500, 512)
        data[432:440] = b'.hexpthk'
        struct.pack_into('<IIII', data, 432 + 8, 0x900, 0x1500, 0x900, 1792)
        struct.pack_into('<I', data, 432 + 36, 0x60000020)
        struct.pack_into('<II', data, 1288, 0x14F2, 32)
        self.path.write_bytes(data)
        self.assertEqual(build.inspect_arm64ec(self.path)['pe_abi'], 'arm64ec')
        struct.pack_into('<I', data, 432 + 12, 0x1600)
        self.path.write_bytes(data)
        with self.assertRaisesRegex(Error, 'arm64ec_unmapped_code_range'):
            build.inspect_arm64ec(self.path)

    def test_positive_metadata_at_unapproved_path_is_not_an_architecture_waiver(self):
        other = self.path.with_name('unapproved.dll')
        self.path.rename(other)
        row = build.inventory(self.root, binary=True)['files'][0]
        self.assertNotIn('pe_abi', row)
        artifact = OutputCoverageTests().complete(companion=True)
        artifact['files'].append(row)
        with self.assertRaisesRegex(Error, 'build_pe_architecture'):
            build.required_outputs(artifact, 'arm64ec-build')

    def test_three_named_companion_modules_must_each_have_positive_arm64ec_facts(self):
        for name in build.ARM64EC_PATHS:
            for mutation in ('missing', 'machine', 'metadata'):
                with self.subTest(name=name, mutation=mutation):
                    artifact = OutputCoverageTests().complete(companion=True)
                    row = next(item for item in artifact['files'] if item['path'] == name)
                    if mutation == 'missing':
                        artifact['files'].remove(row)
                    elif mutation == 'machine':
                        row['machine'] = 0xAA64
                    else:
                        row.pop('pe_abi')
                    with self.assertRaises(Error):
                        build.required_outputs(artifact, 'arm64ec-build')


if __name__ == '__main__':
    unittest.main()
