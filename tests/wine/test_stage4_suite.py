"""Finite suite rejection checks; these do not execute Wine or restricted APIs."""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/wine'))
import api_runner as api
import build
import signing
from common import Error, load_json


class Stage4SuiteTests(unittest.TestCase):
    def test_required_regressions_and_thread_case_cannot_be_skipped(self):
        value = load_json(api.cases_path(api.STAGE4_SUITE))
        self.assertEqual(api.validate_cases(value, api.STAGE4_SUITE), value)
        for index in range(3):
            changed = copy.deepcopy(value)
            del changed['cases'][index]
            with self.subTest(index=index), self.assertRaises(Error):
                api.validate_cases(changed, api.STAGE4_SUITE)

    def test_old_authorization_cannot_be_relabelled_as_stage4_cases(self):
        value = load_json(api.CASES)
        with self.assertRaises(Error):
            api.validate_cases(value, api.STAGE4_SUITE)
        value = load_json(api.cases_path(api.STAGE4_SUITE))
        with self.assertRaises(Error):
            api.validate_cases(value)

    def test_unbounded_or_alternate_entrypoint_rejected(self):
        value = load_json(api.cases_path(api.STAGE4_SUITE))
        for key, replacement in [('entrypoint', 'x64_control'), ('args', ['--skip-memory']),
                                 ('timeout_ms', 0), ('expected_exit', 5)]:
            changed = copy.deepcopy(value)
            changed['cases'][2][key] = replacement
            with self.subTest(key=key), self.assertRaises(Error):
                api.validate_cases(changed, api.STAGE4_SUITE)

    def test_stage3_signed_scope_cannot_authorize_stage4(self):
        old = {'authorization_scope': 'development_windows_api_abi_fixtures',
               'code_publication_policy': 'page-wx', 'entrypoints': {'stage4_pe': 'claimed.exe'}}
        api.validate_suite_authorization('api-abi', old)
        with self.assertRaisesRegex(Error, 'api_authorization_required'):
            api.validate_suite_authorization(api.STAGE4_SUITE, old)
        new = {**old, 'authorization_scope': 'development_windows_thread_memory_exception_fixtures'}
        api.validate_suite_authorization(api.STAGE4_SUITE, new)
        api.validate_suite_authorization('api-abi', new)
        new['entrypoints'] = {}
        with self.assertRaisesRegex(Error, 'stage4_signed_entrypoint_missing'):
            api.validate_suite_authorization(api.STAGE4_SUITE, new)

    def test_stage4_fixture_is_arm64_and_not_implicitly_in_old_suite(self):
        self.assertNotIn('libexec/pear-stage4/stage4-arm64.exe', build.fixture_pe_outputs('api-abi', 'page-wx'))
        self.assertEqual(build.fixture_pe_outputs(build.STAGE4_SUITE, 'page-wx')['libexec/pear-stage4/stage4-arm64.exe'], 0xaa64)
        built = {'fixture_suite': build.STAGE4_SUITE, 'code_publication_policy': 'page-wx'}
        self.assertEqual(signing.guest_fixtures_for(built)['stage4_pe'][1:], (0xaa64, True))
        built['fixture_suite'] = 'api-abi'
        self.assertNotIn('stage4_pe', signing.guest_fixtures_for(built))

    def test_stage4_commands_build_real_pe_and_preserve_old_regressions(self):
        with patch.object(build, 'native_tool', return_value=Path('/usr/bin/clang')):
            old = build.fixture_commands(Path('/build'), Path('/tools'), {'sdk': {'path': '/sdk'}}, 'api-abi', 'page-wx')
            new = build.fixture_commands(Path('/build'), Path('/tools'), {'sdk': {'path': '/sdk'}}, build.STAGE4_SUITE, 'page-wx')
        self.assertTrue(all(new[key] == argv for key, argv in old.items()))
        argv = new['fixture-stage4-arm64']
        self.assertIn('--target=aarch64-w64-windows-gnu', argv)
        self.assertTrue(all(any(arg.endswith('/' + name) for arg in argv) for name in
                            ('threads_pe.c', 'memory_pe.c', 'exceptions_pe.c', 'threads_gateway.S')))
        self.assertNotIn('-Wl,--allow-multiple-definition', argv)


if __name__ == '__main__':
    unittest.main()
