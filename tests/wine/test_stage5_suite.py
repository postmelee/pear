"""Stage 5 suite isolation and prerequisite tests; these do not run Wine."""
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


class Stage5SuiteTests(unittest.TestCase):
    def test_all_regressions_and_window_case_are_required(self):
        value = load_json(api.cases_path(api.STAGE5_SUITE))
        self.assertEqual(api.validate_cases(value, api.STAGE5_SUITE), value)
        self.assertEqual([item['id'] for item in value['cases']], ['api', 'abi', 'threads', 'window'])
        for index in range(4):
            changed = copy.deepcopy(value)
            del changed['cases'][index]
            with self.subTest(index=index), self.assertRaises(Error):
                api.validate_cases(changed, api.STAGE5_SUITE)

    def test_previous_suite_cannot_be_relabelled(self):
        for suite in api.PE_SUITES[:-1]:
            old = load_json(api.cases_path(suite))
            with self.subTest(suite=suite), self.assertRaises(Error):
                api.validate_cases(old, api.STAGE5_SUITE)
            with self.subTest(suite=suite), self.assertRaises(Error):
                api.validate_cases(load_json(api.cases_path(api.STAGE5_SUITE)), suite)

    def test_window_entrypoint_and_bounds_are_not_caller_options(self):
        value = load_json(api.cases_path(api.STAGE5_SUITE))
        for key, replacement in [('entrypoint', 'x64_control'), ('args', ['--skip-teardown']),
                                 ('timeout_ms', 0), ('expected_exit', 1), ('expected_exit', False)]:
            changed = copy.deepcopy(value)
            changed['cases'][3][key] = replacement
            with self.subTest(key=key), self.assertRaises(Error):
                api.validate_cases(changed, api.STAGE5_SUITE)

    def test_only_stage5_authorization_admits_driver_case(self):
        signed = {'authorization_scope': 'development_windows_mac_driver_fixtures',
                  'code_publication_policy': 'page-wx', 'entrypoints': {'stage4_pe': 'a.exe', 'window_pe': 'b.exe', 'window_driver_pe': 'winemac.drv'}}
        for suite in api.PE_SUITES:
            api.validate_suite_authorization(suite, signed)
        for scope in ('development_windows_api_abi_fixtures', 'development_windows_thread_memory_exception_fixtures'):
            with self.subTest(scope=scope), self.assertRaises(Error):
                api.validate_suite_authorization(api.STAGE5_SUITE, {**signed, 'authorization_scope': scope})
        for name in ('stage4_pe', 'window_pe', 'window_driver_pe'):
            value = copy.deepcopy(signed)
            del value['entrypoints'][name]
            with self.subTest(name=name), self.assertRaises(Error):
                api.validate_suite_authorization(api.STAGE5_SUITE, value)

    def test_window_environment_does_not_enable_stage4_signal_fixture(self):
        env = api.fixture_loader_environment(Path('/home'), Path('/prefix'), 'a'*32, '/control', 123, stage5=True)
        self.assertEqual(env['PEAR_WINE_STAGE5_FIXTURE'], '1')
        self.assertNotIn('PEAR_WINE_STAGE4_FIXTURE', env)
        old = api.fixture_loader_environment(Path('/home'), Path('/prefix'), 'a'*32, '/control', 123)
        self.assertNotIn('PEAR_WINE_STAGE5_FIXTURE', old)

    def test_missing_graphical_api_is_unavailable(self):
        with patch.object(api.ctypes, 'CDLL', side_effect=OSError('not a graphical Mac')):
            self.assertEqual(api.graphical_session(), {'status': None, 'available': False})

    def test_graphical_api_failure_or_missing_bit_is_not_available(self):
        class Query:
            def __init__(self, status, bits): self.status, self.bits = status, bits
            def __call__(self, caller, session, attributes):
                self.caller, self.session = caller.value, session
                attributes._obj.value = self.bits
                return self.status
        for status, bits, available in ((0, 0x10, True), (0, 0, False), (-1, 0x10, False)):
            q = Query(status, bits)
            with patch.object(api.ctypes, 'CDLL', return_value=type('Security', (), {'SessionGetInfo': q})()):
                self.assertEqual(api.graphical_session(), {'status': status, 'available': available})
                self.assertEqual(q.caller, 0xffffffff)
                self.assertIsNone(q.session)


if __name__ == '__main__':
    unittest.main()
