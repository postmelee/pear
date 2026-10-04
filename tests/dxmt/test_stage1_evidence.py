"""Accounted inventory cannot be upgraded to build/runtime readiness."""
import copy
import struct
import unittest
from unittest.mock import patch
from support import Fixture
from common import Error, MACH_ARM64, digest, encoded
import check
import verify


def observations():
    return [{'id': name, 'status': 'unavailable', 'path': None, 'capability': 'unperformed', 'candidate_acquired': False}
            for name in ['cmake', 'meson', 'ninja', 'metal', 'metallib']]


class Evidence(unittest.TestCase):
    def setUp(self):
        self.f = Fixture()
        self.addCleanup(self.f.close)

    def test_accounted_inventory_passes_with_explicit_missing_metallib(self):
        rows = observations()
        value = {'inventory_complete': True, 'runtime_eligible': False, 'tools': rows, 'readiness': check.readiness(rows)}
        self.assertEqual(verify.gate_result(value), 0)
        self.assertEqual(verify.gate_result(value, shader=True), 3)

    def test_all_resolved_paths_still_do_not_prove_shader_capability(self):
        rows = observations()
        for row in rows:
            row.update(status='resolved_unverified', path='/fixture/tool')
        value = {'inventory_complete': True, 'runtime_eligible': False, 'tools': rows, 'readiness': check.readiness(rows)}
        self.assertEqual(value['readiness']['unavailable_tools'], [])
        self.assertEqual(verify.gate_result(value, shader=True), 3)

    def test_tampered_ready_claim_is_refused(self):
        rows = observations()
        value = {'inventory_complete': True, 'runtime_eligible': False, 'tools': rows, 'readiness': check.readiness(rows)}
        value['readiness']['shader_build_ready'] = True
        with self.assertRaisesRegex(Error, 'gate_readiness'):
            verify.gate_result(value, shader=True)

    def test_runtime_eligibility_upgrade_is_refused(self):
        rows = observations()
        value = {'inventory_complete': True, 'runtime_eligible': True, 'tools': rows, 'readiness': check.readiness(rows)}
        with self.assertRaisesRegex(Error, 'gate_scope'):
            verify.gate_result(value)

    def test_missing_tool_observation_is_not_accounted(self):
        with self.assertRaisesRegex(Error, 'tool_observation_set'):
            check.readiness(observations()[:-1])

    def test_fake_capability_or_acquisition_is_refused(self):
        for key, value in [('capability', 'passed'), ('candidate_acquired', True)]:
            rows = observations()
            rows[0][key] = value
            with self.assertRaisesRegex(Error, 'tool_observation_state'):
                check.readiness(rows)

    def test_unavailable_tool_cannot_have_an_available_path(self):
        rows = observations()
        rows[0]['path'] = '/invented/tool'
        with self.assertRaisesRegex(Error, 'tool_observation_path'):
            check.readiness(rows)

    def test_config_rejects_d3d12_and_wrong_host(self):
        from pathlib import Path
        from common import load_json
        config = load_json(Path(__file__).resolve().parents[2] / 'runtime/dxmt/build-config.json')
        for key in ['feature', 'host']:
            value = copy.deepcopy(config)
            if key == 'feature':
                value['features']['enable_d3d12'] = True
            else:
                value['native_target'] = 'x86_64-apple-darwin'
            with self.assertRaises(Error):
                check.validate_config(value)

    def test_terms_limit_cannot_claim_distribution_closure(self):
        from pathlib import Path
        from common import load_json
        original = load_json(Path(__file__).resolve().parents[2] / 'runtime/dxmt/build-config.json')
        for unsupported in ['All distribution rights are verified.', True, {}, None]:
            value = copy.deepcopy(original)
            value['source_terms_limit'] = unsupported
            with self.assertRaisesRegex(Error, 'config_gate'):
                check.validate_config(value)

    def test_wrong_wine_role_is_rejected_before_artifact_use(self):
        root = self.f.root / 'native-role'
        root.mkdir()
        record = {'record_kind': 'wine_build', 'scope': 'wine_component', 'passed': True, 'variant': 'arm64ec-build'}
        raw = encoded(record)
        (root / 'build.json').write_bytes(raw)
        self.f.inputs['wine_baseline']['build_refs']['native']['sha256'] = digest(raw)
        with self.assertRaisesRegex(Error, 'wine_role_variant'):
            check.inspect_wine_role(root, 'native', self.f.inputs)

    def test_wine_build_digest_mutation_is_rejected(self):
        root = self.f.root / 'native-role'
        root.mkdir()
        (root / 'build.json').write_bytes(encoded({'record_kind': 'changed'}))
        with self.assertRaisesRegex(Error, 'wine_build_digest'):
            check.inspect_wine_role(root, 'native', self.f.inputs)

    def test_public_export_withholds_private_roots_and_streams(self):
        rows = observations()
        value = {'sources': [], 'wine_roles': [], 'tools': rows, 'readiness': check.readiness(rows),
                 'local_roots': {'credential_prefix': '/private/fixture'}, 'commands': [{'stdout': 'sensitive'}]}
        result = verify.public_observations(value)
        self.assertNotIn('local_roots', result)
        self.assertNotIn('commands', result)
        self.assertFalse(result['gpu_or_guest_execution_performed'])
        self.assertFalse(result['compilation_performed'])

if __name__ == '__main__':
    unittest.main()
