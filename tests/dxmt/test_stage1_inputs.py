"""Source pins, configured gitlinks and real derivation/replay failures."""
import copy
from pathlib import Path
import unittest
from support import Fixture
from common import Error, digest, encoded
import prepare

class Inputs(unittest.TestCase):
    def setUp(self):
        self.f = Fixture()
        self.addCleanup(self.f.close)

    def test_exact_inputs_are_accounted_without_shader_or_runtime(self):
        value = prepare.validate_inputs(self.f.inputs, self.f.root)
        self.assertEqual(len(value['components']), 9)

    def test_wrong_source_commit_is_rejected_against_audit(self):
        self.f.inputs['components'][0]['commit'] = digest(b'other')[:40]
        with self.assertRaisesRegex(Error, 'component_pin'):
            prepare.validate_inputs(self.f.inputs, self.f.root)

    def test_wrong_listing_is_rejected_against_audit(self):
        self.f.inputs['components'][1]['listing']['value'] = digest(b'changed')
        with self.assertRaisesRegex(Error, 'component_listing'):
            prepare.validate_inputs(self.f.inputs, self.f.root)

    def test_duplicate_source_identity_is_rejected(self):
        self.f.inputs['components'].append(copy.deepcopy(self.f.inputs['components'][0]))
        with self.assertRaisesRegex(Error, 'component_identity'):
            prepare.validate_inputs(self.f.inputs, self.f.root)

    def test_disabled_gitlink_cannot_be_materialized(self):
        self.f.inputs['gitlinks'][1]['enabled'] = True
        with self.assertRaisesRegex(Error, 'gitlink_selection'):
            prepare.validate_inputs(self.f.inputs, self.f.root)

    def test_wrong_gitlink_revision_is_rejected(self):
        self.f.inputs['gitlinks'][0]['commit'] = digest(b'wrong')[:40]
        with self.assertRaisesRegex(Error, 'gitlink_selection'):
            prepare.validate_inputs(self.f.inputs, self.f.root)

    def test_changed_notice_bytes_are_rejected(self):
        self.f.inputs['components'][0]['terms'][0]['sha256'] = digest(b'replacement')
        self.f.refresh()
        with self.assertRaisesRegex(Error, 'source_file_digest'):
            self.f.derive()

    def test_missing_git_object_fails_inspection(self):
        c = self.f.inputs['components'][0]
        repo = self.f.cache / c['cache_path']
        blob = c['terms'][0]['git_blob']
        (repo / 'objects' / blob[:2] / blob[2:]).unlink()
        with self.assertRaisesRegex(Error, 'git_read_failed'):
            self.f.derive()

    def test_unexpected_git_config_includes_are_rejected(self):
        c = self.f.inputs['components'][0]
        config = self.f.cache / c['cache_path'] / 'config'
        config.write_text(config.read_text() + '[include]\n path = /unapproved/config\n')
        with self.assertRaisesRegex(Error, 'unsafe_git_config'):
            self.f.derive()

    def test_source_derivation_preserves_required_header_and_skips_optional_gitlink(self):
        result = self.f.derive()
        source = self.f.root / '.build/task7/prepared/source'
        self.assertTrue((source / 'dxmt/include/native/directx/d3d11.h').is_file())
        self.assertFalse((source / 'dxmt/external/nvapi').exists())
        self.assertFalse(result['runtime_eligible'])
        self.assertEqual(prepare.verify_prepared(self.f.root / '.build/task7/prepared', self.f.root), result)

    def test_changed_materialized_file_fails_independent_replay(self):
        self.f.derive()
        root = self.f.root / '.build/task7/prepared'
        (root / 'source/dxmt/LICENSE').write_text('changed\n')
        with self.assertRaisesRegex(Error, 'prepared_materialized_changed'):
            prepare.verify_prepared(root, self.f.root)

    def test_extra_materialized_file_fails_replay(self):
        self.f.derive()
        root = self.f.root / '.build/task7/prepared'
        (root / 'source/dxmt/extra').write_text('extra\n')
        with self.assertRaisesRegex(Error, 'prepared_materialized_changed'):
            prepare.verify_prepared(root, self.f.root)

    def test_changed_source_mode_fails_replay(self):
        self.f.derive()
        root = self.f.root / '.build/task7/prepared'
        (root / 'source/dxmt/LICENSE').chmod(0o755)
        with self.assertRaisesRegex(Error, 'prepared_materialized_changed'):
            prepare.verify_prepared(root, self.f.root)

    def test_changed_preparation_manifest_digest_fails_replay(self):
        self.f.derive()
        root = self.f.root / '.build/task7/prepared'
        (root / 'source-files.json').write_bytes(encoded({'modified': True}))
        with self.assertRaisesRegex(Error, 'prepared_manifest_digest'):
            prepare.verify_prepared(root, self.f.root)

    def test_nonmaterialized_llvm_symlink_is_metadata_only(self):
        result = self.f.derive()
        llvm = next(r for r in result['components'] if r['id'] == 'llvm-dxmt')
        self.assertEqual(llvm['unmaterialized_symlink_entries'], 1)
        self.assertFalse((self.f.root / '.build/task7/prepared/source/llvm').exists())

    def test_materialized_component_cannot_extract_upstream_symlink(self):
        llvm = next(c for c in self.f.inputs['components'] if c['id'] == 'llvm-dxmt')
        llvm.update(materialize=True, source_path='llvm')
        with self.assertRaisesRegex(Error, 'unsupported_tree_entry'):
            self.f.derive()

    def test_changed_producer_is_refused_by_replay(self):
        self.f.derive()
        path = self.f.root / 'tools/dxmt/check.py'
        path.write_bytes(path.read_bytes() + b'\n# changed original fixture producer\n')
        with self.assertRaisesRegex(Error, 'producer_changed'):
            prepare.verify_prepared(self.f.root / '.build/task7/prepared', self.f.root)

    def test_missing_selected_notice_is_refused(self):
        self.f.inputs['components'][0]['terms'].pop()
        with self.assertRaisesRegex(Error, 'selected_source_policy'):
            prepare.validate_inputs(self.f.inputs, self.f.root)

    def test_omitted_driver_source_check_is_refused(self):
        wine = next(c for c in self.f.inputs['components'] if c['id'] == 'wine-upstream')
        wine['source_checks'] = []
        with self.assertRaisesRegex(Error, 'selected_source_policy'):
            prepare.validate_inputs(self.f.inputs, self.f.root)

    def test_missing_selected_source_component_is_refused(self):
        self.f.inputs['components'] = [c for c in self.f.inputs['components'] if c['id'] != 'llvm-mingw-source']
        with self.assertRaisesRegex(Error, 'required_component'):
            prepare.validate_inputs(self.f.inputs, self.f.root)

    def test_unknown_input_semantics_are_rejected(self):
        self.f.inputs['guess_supported'] = True
        with self.assertRaisesRegex(Error, 'record_fields'):
            prepare.validate_inputs(self.f.inputs, self.f.root)

if __name__ == '__main__':
    unittest.main()
