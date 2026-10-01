"""Synthetic Stage 5 packaging checks, without Wine execution or signing.

Reuses the earlier export scaffolding for private receipts. The new window
summary and altered suite scopes are supplied independently of its producer.
"""
import copy
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/wine'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import api_runner
import build
import evidence
import stage5_evidence as exporter
import test_stage4_evidence as stage4_fixture
from common import Error, encoded, sha256
from test_evidence_stage3 import digest


class Stage5ExportTests(unittest.TestCase):
    def setUp(self):
        # Enumerate producer names without requiring a build or generated copies.
        with mock.patch.object(api_runner, 'sha256', return_value='0'*64):
            self.producer_names = tuple(api_runner.producers(exporter.SUITE))
        self.previous = stage4_fixture.Stage4ExportTests(methodName='runTest')
        self.addCleanup(self.previous.doCleanups)
        self.previous.setUp()
        self.base = b = self.previous.base
        patcher = mock.patch.object(exporter, 'REPO', b.root)
        patcher.start(); self.addCleanup(patcher.stop)
        for name in exporter.SOURCES.values():
            path = b.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists(): path.write_text('Synthetic private Stage 5 source: ' + name)
        b.built.update(fixture_suite=exporter.SUITE, commands=[{'id': name, 'exit_code': 0,
            'timed_out': False, 'output_limit': False, 'argv': ['/Users/PRIVATE_SECRET']}
            for name in ['patch-1', *sorted(exporter.COMMANDS)]])
        b.signed['authorization_scope'] = exporter.SCOPE
        b.api_record.update(suite=exporter.SUITE, producer_sha256={name:sha256(b.root/name) for name in self.producer_names})
        b.api.update(record_kind='wine_mac_driver_assessment', suite=exporter.SUITE, case_count=4,
            evidence_scope='instrumented-arm64-mac-driver-with-constrained-owned-descendants',
            producer_sha256=copy.deepcopy(b.api_record['producer_sha256']))
        window = copy.deepcopy(b.api['cases'][0])
        window.update(id='window',fixture_results=[{'version':1,'record_kind':'pear_window_result',
            'passed':1,'error_step':0,'error_code':0,'cycles':20,'app_messages':20,'reentries':20,
            'closes':20,'destroys':20,'ncdestroys':20,'late_callbacks':0,'class_registered':1,
            'class_unregistered':1,'native_final':1,'cleanup_complete':1}], window_observations={
            'fixture_sha256':'4'*64,'driver_pe_sha256':'5'*64,'native_driver_sha256':'6'*64,
            'cycles':20,'native_anchor_parts':767,'native_image_snapshot_count':280,
            'native_main_thread_verified':True,'wine_callback_thread_verified':True,
            'cocoa_close_events':20,'application_messages':20,'callback_reentries':20,
            'destroyed_windows':20,'deallocated_windows':20,'appkit_event_turns':20,'final_queue_idle_verified':True,'main_thread_barriers':40,'event_drains':40,
            'observed_late_callbacks':0,'active_windows_at_completion':0,'pending_owned_events_at_completion':0,
            'loaded_driver_verified':True,'loaded_appkit_verified':True,'loaded_corefoundation_verified':True,
            'observation_scope':'twenty_owned_lifetimes_through_final_barrier',
            'unqualified':['metal_rendering','dxmt_driver_pairing','general_callbacks','native_created_guest_callback_thread',
                'x64_guest_translation','game_execution','ordinary_user_distribution'],
            'native_hwnd':998877,'native_profile':'PRIVATE_SECRET','private_path':'/Users/PRIVATE_SECRET'})
        b.api['cases'].append(window)
        patcher=mock.patch.object(api_runner,'producers',return_value=b.api_record['producer_sha256'])
        patcher.start();self.addCleanup(patcher.stop)
        self.refresh()

    def refresh(self):
        self.previous.refresh()

    def export(self):
        b=self.base
        return exporter.export(b.build,b.api_root,b.bootstrap_root)

    def rejected(self, code=None):
        with self.assertRaises(Error) as raised:self.export()
        if code:self.assertEqual(raised.exception.code,code)

    def test_export_binds_four_cases_and_same_signed_bootstrap(self):
        result=self.export()
        self.assertEqual(result['record_kind'],'wine_stage5_observations')
        self.assertEqual(result['signed_sha256'],digest(self.base.signed))
        self.assertEqual(result['build']['build_sha256'],digest(self.base.built))
        self.assertEqual(result['run_assessments']['mac_driver']['case_count'],4)
        self.assertEqual([r['id'] for r in result['run_assessments']['mac_driver']['cases']],['api','abi','threads','window'])
        self.base.mocks['api_runner.validate_runs'].assert_called_once_with(self.base.api_root,'mac-driver')
        self.base.mocks['run_fixtures.validate_runs'].assert_called_once_with(self.base.bootstrap_root,'bootstrap')
        self.assertIn('window_validator',result['producer_hashes']['stage5_run'])
        self.assertIn('window_native_fixture',result['reviewed_source_hashes'])
        for key in ('translator_execution','game_execution','runtime_qualified','distribution_qualified'):
            self.assertIs(result[key],False)
        self.assertIn('dxmt_driver_pairing',result['unqualified'])

    def test_current_suite_producers_are_explicitly_allowlisted(self):
        # Captured from the real producer-name function before gate mocks.
        self.assertLessEqual(set(self.producer_names), set(exporter.SOURCE_LABELS))
        census = 'tests/wine/fixtures/stage5_census.h'
        self.assertIn(census, self.producer_names)
        self.assertEqual(exporter.SOURCE_LABELS[census], 'window_census_header')
        result = self.export()
        expected = sha256(self.base.root / census)
        self.assertEqual(result['reviewed_source_hashes']['window_census_header'], expected)
        self.assertEqual(result['producer_hashes']['stage5_run']['window_census_header'], expected)
        # A source changed after the run receipt must not be publicly rebound.
        (self.base.root / census).write_text('Changed after the recorded run')
        self.rejected('export_producer_changed')

    def test_private_identity_and_unknown_raw_fields_are_never_copied(self):
        text=encoded(self.export()).decode()
        for secret in ('PRIVATE_SECRET','998877','/Users/','native_hwnd','native_profile','private_path','driver_base',
                       'claim_keys','profile_checks','same_team','current_provisioning_device_match','runtime_path','argv'):
            self.assertNotIn(secret,text)

    def test_window_booleans_must_not_be_numeric_and_counters_bind(self):
        value=self.base.api['cases'][-1]['window_observations']
        for key, replacement in [('cycles',True),('native_main_thread_verified',1),('native_anchor_parts',604),
                                 ('event_drains',21),('main_thread_barriers',19),('native_image_snapshot_count',2),
                                 ('native_image_snapshot_count',2049),('observed_late_callbacks',1),('pending_owned_events_at_completion',1)]:
            old=value[key];value[key]=replacement
            with self.subTest(key=key):self.rejected()
            value[key]=old

    def test_bounded_extra_drain_attempts_preserve_exact_parts(self):
        value=self.base.api['cases'][-1]['window_observations']
        value.update(main_thread_barriers=41,event_drains=41,native_anchor_parts=771)
        self.assertEqual(self.export()['run_assessments']['mac_driver']['cases'][-1]['window_observations']['event_drains'],41)

    def test_variable_turns_and_maximum_success_shape_are_publicly_bound(self):
        value=self.base.api['cases'][-1]['window_observations']
        value.update(main_thread_barriers=2000,event_drains=2000,
                     appkit_event_turns=1980,native_anchor_parts=16447)
        summary=self.export()['run_assessments']['mac_driver']['cases'][-1]['window_observations']
        self.assertEqual(summary['appkit_event_turns'],1980)
        self.assertEqual(summary['native_anchor_parts'],16447)
        for key,bad in [('appkit_event_turns',True),('appkit_event_turns',19),
                        ('appkit_event_turns',2001),('native_anchor_parts',16451)]:
            old=value[key];value[key]=bad
            with self.subTest(key=key,bad=bad):self.rejected()
            value[key]=old
        value.update(main_thread_barriers=40,event_drains=40,
                     appkit_event_turns=41,native_anchor_parts=851)
        self.rejected('export_window_count_binding')

    def test_earlier_signed_scope_cannot_be_relabelled(self):
        self.base.signed['authorization_scope']='development_windows_thread_memory_exception_fixtures'
        self.refresh();self.rejected('export_stage5_signed_scope')

    def test_old_assessment_or_build_scope_is_not_mac_driver(self):
        self.base.api['record_kind']='wine_thread_memory_exception_assessment'
        self.rejected('export_stage5_assessment_scope')
        self.base.api['record_kind']='wine_mac_driver_assessment'
        self.base.built['fixture_suite']='threads-memory-exceptions'
        self.refresh();self.rejected('export_build_scope')

    def test_required_regression_and_window_observation_cannot_be_omitted(self):
        window=self.base.api['cases'].pop()
        self.rejected()
        self.base.api['cases'].append(window)
        del window['window_observations'];self.rejected('export_window_summary')

    def test_window_observations_cannot_be_attached_to_api_regression(self):
        self.base.api['cases'][0]['window_observations']=copy.deepcopy(self.base.api['cases'][-1]['window_observations'])
        self.rejected('export_window_scope')

    def test_window_scope_cannot_claim_dxmt_or_omit_limitations(self):
        self.base.api['cases'][-1]['window_observations']['unqualified'].remove('dxmt_driver_pairing')
        self.rejected('export_window_facts')

    def test_bootstrap_requires_same_signed_bytes_and_actual_record_kind(self):
        self.base.bootstrap['signed_sha256']='f'*64
        self.rejected('export_mixed_signed_runtime')
        self.base.bootstrap['signed_sha256']=self.base.api['signed_sha256']
        self.base.bootstrap_record['record_kind']='wine_api_run'
        self.refresh();self.rejected()

    def test_unexecuted_architecture_controls_remain_unexecuted(self):
        controls=self.export()['run_assessments']['mac_driver']['controls']
        self.assertEqual([r['machine'] for r in controls],['x86_64','i386'])
        self.assertTrue(all(r['executed'] is False and r['accepted'] is False for r in controls))
        self.base.api['controls'][0]['executed']=True;self.rejected('export_control_scope')

    def test_bootstrap_regression_failure_cannot_be_exported(self):
        self.base.bootstrap['cases'][1]['cleanup_complete']=False
        self.rejected('export_bootstrap_case')

    def test_extra_or_failed_build_command_cannot_enter_export(self):
        self.base.built['commands'][0]['exit_code']=1
        self.refresh();self.rejected('export_command_failure')

    def test_native_artifact_x64_is_rejected(self):
        next(row for row in self.base.artifacts['files'] if row['kind']=='macho')['architectures']=[0x1000007]
        self.rejected('export_host_architecture')


if __name__=='__main__':unittest.main()
