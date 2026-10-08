"""Portable protocol/refusal controls; no native process or Metal execution."""
import copy
import errno
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'tools/dxmt'))
spec = importlib.util.spec_from_file_location('_pear_dxmt_pairing_run_tests', REPO / 'tools/dxmt/run_pairing.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
from common import Error, digest, encoded


def protocol_rows():
    """Scalar source-protocol observations only, never executable fixtures."""
    leases = [0]*10 + [1,2,2,2,2,2,1,1,2,2,2,2,2,2,2,1,1,1,0,1,1,0,1,1,1,0,0,0,0]
    rows = []
    for index, (name, status) in enumerate(runner.CASES, 1):
        views = 0 if index < 14 else (1 if index < 30 else (2 if index < 33 else 3))
        proxies = int(index >= 20)
        rows.append({'record_kind':'pear_metal_pairing','version':1,'case_id':index,'case':name,
            'status':status,'expected_status':status,'facts':1,'lease_count':leases[index-1],
            'attachment_count':int(leases[index-1]>0),'main_thread':int(index>=14),'x18_mode':0,
            'delegate_state':int(index>=14),'created_views':views,'deallocated_views':views if index==39 else 0,
            'created_layers':views,'deallocated_layers':views if index==39 else 0,
            'created_proxies':proxies,'deallocated_proxies':proxies if index==39 else 0})
    return rows


def wire(rows):
    # Match the actual source-owned prefix rather than JSON's sorted key order.
    import json
    return b''.join(json.dumps(row,separators=(',',':')).encode()+b'\n' for row in rows)


class ProtocolControls(unittest.TestCase):
    def test_complete_protocol_keeps_diagnostic_review_separate(self):
        facts,diagnostics=runner.native_rows(wire(protocol_rows())+b'captured native warning\n')
        self.assertEqual(facts['case_count'],39)
        self.assertEqual(facts['physical_lifetime'],'observed_balanced')
        self.assertEqual(diagnostics,b'captured native warning\n')
        self.assertNotIn('rendering_qualified',facts)

    def test_unknown_unbalanced_or_early_physical_lifetime_refuses(self):
        for index,key,value in [(38,'deallocated_layers',2),(38,'deallocated_proxies',0),
                                (13,'deallocated_views',2),(30,'deallocated_layers',1),
                                (13,'delegate_state',2)]:
            with self.subTest(index=index,key=key):
                rows=protocol_rows();rows[index][key]=value
                with self.assertRaises(Error):runner.native_rows(wire(rows))

    def test_wrong_case_status_lease_main_thread_or_x18_refuses(self):
        for index,key,value in [(15,'facts',0),(21,'status',13),(27,'lease_count',0),
                                (13,'main_thread',0),(13,'x18_mode',1),(23,'case','unknown'),
                                (5,'status',2**32),(1,'expected_status',True)]:
            with self.subTest(index=index,key=key):
                rows=protocol_rows();rows[index][key]=value
                with self.assertRaises(Error):runner.native_rows(wire(rows))

    def test_duplicate_missing_reordered_and_unterminated_rows_refuse(self):
        rows=protocol_rows()
        for raw in [wire(rows[:-1]),wire(rows+[rows[-1]]),wire(rows[1:]+rows[:1]),wire(rows)[:-1]]:
            with self.assertRaises(Error):runner.native_rows(raw)

    def test_own_unknown_json_namespace_cannot_be_hidden_as_diagnostics(self):
        for extra in [b'{"record_kind":"pear_metal_pairing_extra"}\n',
                      b'{"version":1,"record_kind":"pear_metal_pairing"}\n',
                      b' {"record_kind": "pear_metal_pairing"}\n']:
            with self.assertRaises(Error):runner.native_rows(wire(protocol_rows())+extra)

    def test_pe_terminal_requires_primary_and_all_cleanup_success(self):
        helper=SimpleNamespace(base=SimpleNamespace(validate_helper=lambda *args:None))
        terminal={'record_kind':'pear_metal_pairing_pe','version':1,
                  **{key:0 for key in runner.PE_FIELDS},'cleanup_flags':7,'completed_phases':6}
        raw=lambda row:wire([{'record_kind':'pear_bootstrap_helper'},row])
        self.assertEqual(runner.pe_rows(raw(terminal),helper,None)['completed_phases'],6)
        for key,value in [('primary_error',5),('cleanup_error',1),('cleanup_flags',3),
                          ('completed_phases',5),('control_status',False),('primary_step',4)]:
            row=dict(terminal);row[key]=value
            with self.subTest(key=key):
                with self.assertRaises(Error):runner.pe_rows(raw(row),helper,None)
        with self.assertRaises(Error):runner.pe_rows(raw(terminal)+b'additional output\n',helper,None)

    def test_closed_environment_preserves_home_without_inheriting_wine_or_dyld(self):
        source={'HOME':'/ordinary home','DYLD_INSERT_LIBRARIES':'bad','WINEPREFIX':'other',
                'PEAR_STAGE3_CONTROL':'other','STEAM_TOKEN':'private','PATH':'unreviewed'}
        with mock.patch.dict(os.environ,source,clear=True):
            result=runner.environment(Path('/owned/work'),Path('/owned/prefix'),'a'*32)
        self.assertEqual(result['HOME'],'/ordinary home')
        self.assertEqual(result['PATH'],'/usr/bin:/bin')
        self.assertEqual(result['WINEPREFIX'],'/owned/prefix')
        self.assertNotIn('DYLD_INSERT_LIBRARIES',result)
        self.assertNotIn('STEAM_TOKEN',result)
        self.assertNotIn('PEAR_STAGE3_CONTROL',result)
        self.assertEqual(result['MTL_DEBUG_LAYER_ERROR_MODE'],'assert')
        self.assertEqual(result['MTL_DEBUG_LAYER_WARNING_MODE'],'nslog')
        self.assertEqual(result['MTL_SHADER_VALIDATION_FAIL_MODE'],'zerofill')
        for nonce in ['A'*32,'a'*31,'a'*33,True]:
            with self.assertRaises(Error):runner.environment(Path('/work'),Path('/prefix'),nonce)

    def test_exact_launch_argv_environment_and_pid_are_replayed(self):
        runtime=Path('/owned/runtime');value={'entrypoints':{key:'bin/'+key for key in
            ['sentinel','server','bootstrap_helper','loader','fixture_pe']}}
        result={'base_environment':{'closed':'base'},'loader_environment':{'closed':'loader'},
                'processes':{key:{'identity':{'pid':index+100}}for index,key in enumerate(['sentinel','server','loader'])}}
        recipes=runner.launch_recipes(runtime,value,result['base_environment'],result['loader_environment'],14)
        result['launches']=[{'role':role,'argv':argv,'environment':env,'started':True,
            'pid':result['processes'][role]['identity']['pid']}for role,(argv,env)in recipes.items()]
        runner.validate_launches(result,runtime,value)
        for role,key,alter in [('loader','argv',lambda row:row['argv']+['unexpected']),
                               ('server','environment',lambda row:{**row['environment'],'DYLD_LIBRARY_PATH':'bad'}),
                               ('sentinel','pid',lambda row:True),('loader','started',lambda row:None)]:
            mutated=copy.deepcopy(result);row=next(item for item in mutated['launches']if item['role']==role)
            row[key]=alter(row)
            with self.subTest(role=role,key=key):
                with self.assertRaises(Error):runner.validate_launches(mutated,runtime,value)

    def test_runtime_ntdll_role_is_unique_and_capacity_is_preserved(self):
        value={'native_images':[{'path':'native/ntdll.so','origin':{'role':'baseline-native','path':'lib/wine/ntdll.so'}}],
               'entrypoints':{'loader':'loader','server':'server','bootstrap_helper':'helper'},'arena_capacity':65536}
        self.assertEqual(runner.assessment_packet(value)['arena_capacity'],65536)
        value['native_images']*=2
        with self.assertRaises(Error):runner.assessment_packet(value)

    def test_passive_reader_refuses_unselected_signal_window_and_dynamic_paths(self):
        with runner.wine_helpers(REPO)as helper:
            empty={'events':{'loader':[],'server':[]}}
            packet={'arena_capacity':{}}
            self.assertIs(runner.passive_dynamic_observations(empty,packet,helper)['dynamic_supported'],False)
            for event in ['stage4_signal','stage5_window','dynamic_failure','dynamic_protect']:
                value={'events':{'loader':[{'event':event}],'server':[]}}
                with self.subTest(event=event):
                    with self.assertRaises((Error,helper.Error)):
                        runner.passive_dynamic_observations(value,packet,helper)



class FailureControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='pear-pair-run-pure-')
        self.root=Path(self.temp.name).resolve()

    def tearDown(self):self.temp.cleanup()

    def test_log_byte_and_eof_proof_refuses_truncation_or_boolean_count(self):
        result={'events':{'loader':[],'server':[]},'logs':[]}
        for role in ['loader','server','sentinel']:
            for channel in ['stdout','stderr']+(['events']if role!='sentinel'else[]):
                path=role+'.'+channel+'.log';(self.root/path).write_bytes(b'')
                result['logs'].append({'role':role,'channel':channel,'path':path,'sha256':digest(b''),
                    'bytes':0,'observed_bytes':0,'eof':True,'write_error':None})
        runner.verify_logs(self.root,result)
        for key,value in [('observed_bytes',False),('observed_bytes',1),('eof',False),('write_error','failed')]:
            altered=copy.deepcopy(result);altered['logs'][0][key]=value
            with self.subTest(key=key,value=value):
                with self.assertRaises(Error):runner.verify_logs(self.root,altered)
        (self.root/'loader.stderr.log').write_bytes(b'changed')
        with self.assertRaises(Error):runner.verify_logs(self.root,result)

    def test_cleanup_exception_still_attempts_server_sentinel_and_log_capture(self):
        calls=[]
        incomplete={'signals':[],'errors':[],'observation_gap':False,'reaped':{},'complete':True}
        def cleanup(roles,bounds):
            calls.append(roles)
            if roles==('loader','server'):raise OSError(errno.EIO,'synthetic observation error')
            return copy.deepcopy(incomplete)
        session=SimpleNamespace(children={},observer=SimpleNamespace(refresh=lambda:None,registrations={}),
                                cleanup=cleanup,finish_logs=lambda budget:[])
        result=runner.cleanup_session(session,None,None,self.root)
        self.assertEqual(calls,[('loader','server'),('server',),('sentinel',)])
        self.assertFalse(result[1]['complete'])
        self.assertEqual(result[-1][0]['errno'],errno.EIO)
        self.assertEqual(result[-1][0]['operation'],'owned_group_cleanup')

    def test_failed_finalizer_preserves_raw_streams_and_unknown_eof(self):
        session=SimpleNamespace(streams={('loader','stderr'):{'data':b'primary diagnostic\n',
            'total_bytes':19,'eof':False}},finish_logs=mock.Mock(side_effect=OSError(errno.EIO,'finalizer failed')))
        errors=[];rows=runner.finish_capture(session,self.root,errors)
        self.assertEqual((self.root/'loader.stderr.log').read_bytes(),b'primary diagnostic\n')
        self.assertFalse(rows[0]['eof'])
        self.assertEqual(errors[0]['operation'],'finish_logs')
        self.assertEqual(errors[0]['errno'],errno.EIO)

    def test_owned_setup_failure_gets_structured_failure_without_launch(self):
        repo=self.root/'repo';repo.mkdir();(repo/'.build/task7').mkdir(parents=True)
        runtime=repo/'.build/task7/runtime';runtime.mkdir();(runtime/'runtime.json').write_bytes(b'{}\n')
        with mock.patch.object(runner,'runtime_values',return_value={}),\
             mock.patch.object(runner,'producers',side_effect=Error('producer_capture_failed')),\
             mock.patch.object(runner,'wine_helpers')as native:
            with self.assertRaisesRegex(Error,'producer_capture_failed'):
                runner.run(runtime,repo/'.build/task7/run',repo=repo)
        native.assert_not_called()
        value=runner.decode_json((repo/'.build/task7/run/failed.json').read_bytes())
        self.assertEqual(value['phase'],'preparation')
        self.assertEqual(value['code'],'producer_capture_failed')
        self.assertIs(value['runtime_eligible'],False)

    def test_primary_launch_error_survives_cleanup_and_assessment_refusal(self):
        failure=Error('actual_launch_refusal')
        session=SimpleNamespace(children={},events={},failure=None,endpoint='/private/tmp/pear-stage3-pure/control',
            observer=SimpleNamespace(refresh=lambda:None,registrations={},signal_observations=[]),
            launch=mock.Mock(side_effect=failure),cleanup=mock.Mock(side_effect=OSError(errno.EIO,'cleanup failed')),
            finish_logs=lambda budget:[])
        value={'native_images':[{'path':'ntdll.so','origin':{'role':'baseline-native','path':'lib/wine/ntdll.so'}}],
               'arena_capacity':{},'entrypoints':{name:'bin/'+name for name in
               ['sentinel','server','loader','bootstrap_helper','fixture_pe','winemetal_native']}}
        helper=SimpleNamespace(Error=Error,api=SimpleNamespace(APISession=lambda *args,**kwargs:session,
            graphical_session=lambda:{'status':0,'available':True}),
            base=SimpleNamespace(prefix_identity=lambda path:{'device':1,'inode':2,'namespace':'owned'}))
        with mock.patch.object(runner.os,'pipe',return_value=(42,43)),mock.patch.object(runner.os,'close'):
            with self.assertRaisesRegex(Error,'actual_launch_refusal'):
                runner.run_case(Path('/owned/runtime'),value,self.root,helper)
        record=runner.decode_json((self.root/'case.json').read_bytes())
        self.assertEqual(record['error'],'actual_launch_refusal')
        self.assertEqual(record['launches'][0]['started'],None)
        self.assertEqual(record['launches'][0]['pid'],None)
        self.assertEqual(record['cleanup_errors'][0]['errno'],errno.EIO)
        self.assertIs(record['ordinary_arm64_pe_execution_performed'],False)
        self.assertIs(record['passed'],False)
        self.assertIs(runner.decode_json((self.root/'assessment.json').read_bytes())['passed'],False)

    def test_post_execution_input_change_preserves_structured_failure(self):
        from contextlib import contextmanager
        repo=self.root/'repo';repo.mkdir();(repo/'.build/task7').mkdir(parents=True)
        runtime=repo/'.build/task7/runtime';runtime.mkdir();(runtime/'runtime.json').write_bytes(b'{}\n')
        @contextmanager
        def helpers(*args):yield SimpleNamespace(Error=Error)
        with mock.patch.object(runner,'runtime_values',side_effect=[{'pin':1},{'pin':2}]),\
             mock.patch.object(runner,'producers',return_value={}),\
             mock.patch.object(runner,'wine_helpers',helpers),\
             mock.patch.object(runner,'run_case',return_value=({},{})):
            with self.assertRaisesRegex(Error,'pair_run_inputs_changed'):
                runner.run(runtime,repo/'.build/task7/run',repo=repo)
        record=runner.decode_json((repo/'.build/task7/run/failed.json').read_bytes())
        self.assertEqual(record['phase'],'post_execution_replay')
        self.assertEqual(record['code'],'pair_run_inputs_changed')
        self.assertFalse((repo/'.build/task7/run/run.json').exists())

    def test_pure_wine_namespace_is_restored_and_marker_extension_is_isolated(self):
        original=sys.modules.get('common')
        with runner.wine_helpers(REPO)as helper:
            self.assertIsNot(sys.modules['common'],original)
            self.assertNotIn('metal_pairing_images',helper.api.EVENTS)
            self.assertIn('metal_pairing_images',helper.assess_native.__globals__['EVENTS'])
            self.assertIs(helper.api.assess_native_events.__globals__['EVENTS'],helper.api.EVENTS)
        self.assertIs(sys.modules.get('common'),original)

    def test_changed_helper_bytes_refuse_before_module_execution(self):
        expected={'tools/wine/'+name+'.py':'0'*64 for name in runner.WINE_HELPERS}
        with mock.patch.object(runner,'local')as loader:
            with self.assertRaisesRegex(Error,'pair_run_helper_changed'):
                with runner.wine_helpers(REPO,expected):pass
        loader.assert_not_called()


if __name__=='__main__':unittest.main()
