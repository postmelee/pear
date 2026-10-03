"""Portable refusal and failure-fidelity controls; no tool/compiler execution."""
import argparse
from contextlib import contextmanager
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import unittest
from unittest import mock

HERE=Path(__file__).parent
REPO=Path(os.environ.get('PEAR_TEST_REPO',str(Path(__file__).resolve().parents[2])))
IMPLEMENTATION=Path(os.environ.get('PEAR_TEST_IMPLEMENTATION_ROOT',str(REPO/'tools/dxmt')))
spec=importlib.util.spec_from_file_location('_private_deterministic_pair_controls',IMPLEMENTATION/'deterministic_pair.py')
pair=importlib.util.module_from_spec(spec);spec.loader.exec_module(pair)
metal,reuse=pair.metal,pair.reuse
# Supplying an input means it must parse/pass; absent private artifacts alone
# opt out of actual-byte review controls, without suppressing portable tests.
QUAL_PATH=Path(os.environ['PEAR_TEST_QUALIFICATION'])if os.environ.get('PEAR_TEST_QUALIFICATION')else None
QUAL=json.loads(QUAL_PATH.read_bytes())if QUAL_PATH is not None else None
METAL_ROOT=Path(QUAL['metal_control_ref']['path']).parent if QUAL is not None else None


class Temporary(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='pear-det-controls-',dir='/private/tmp')
        self.root=Path(self.temporary.name)
    def tearDown(self):self.temporary.cleanup()
    def write(self,name,raw,mode=0o644):
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);p.chmod(mode);return p


class Recipe(Temporary):
    def test_cross_flags_preserve_original_and_both_path_spellings(self):
        physical=Path('/private/tmp/a path');invocation=Path('/private/tmp/alias')
        wine,dxmt=pair.environments({'CFLAGS':'native-original'},{'PATH':'native'},physical,invocation)
        self.assertEqual(pair.shlex.split(wine['CROSSCFLAGS']),['-g','-O2',
            '-fdebug-prefix-map=/private/tmp/a path/wine/objects=/pear/reconstruction/wine/objects',
            '-fdebug-prefix-map=/private/tmp/alias/wine/objects=/pear/reconstruction/wine/objects'])
        self.assertEqual(wine['CFLAGS'],'native-original');self.assertEqual(dxmt['SOURCE_DATE_EPOCH'],'0')
    def test_same_spelling_deduplicated(self):self.assertEqual(len(pair.maps(self.root,self.root)),1)
    def test_existing_cross_policy_refused(self):
        for key in ('CROSSCFLAGS','SOURCE_DATE_EPOCH'):
            with self.subTest(key=key),self.assertRaises(reuse.Error):pair.environments({key:'0'},{},self.root,self.root)
    def test_existing_dxmt_epoch_refused(self):
        with self.assertRaises(reuse.Error):pair.environments({}, {'SOURCE_DATE_EPOCH':'0'},self.root,self.root)
    def test_configure_missing_cross_table_refused(self):
        self.write('Makefile',b'CFLAGS = -arch arm64\n')
        with self.assertRaisesRegex(reuse.Error,'det_config_cross_flags_missing'):
            pair.input_configuration(self.root,self.root,'Makefile')
    def test_configure_wrong_map_or_lost_optimization_refused(self):
        for flags in ('-g -O0','-g -O2 -ffile-prefix-map=a=b','-g -O2'):
            self.write('Makefile',('aarch64_CFLAGS = '+flags+'\naarch64_CXXFLAGS = '+flags+'\n').encode())
            with self.assertRaises(reuse.Error):pair.input_configuration(self.root,self.root,'Makefile')
    def test_configure_exact_actual_flags(self):
        flags=pair.shlex.join(['-g','-O2',*pair.maps(self.root,self.root)])
        self.write('Makefile',('aarch64_CFLAGS = '+flags+'\naarch64_CXXFLAGS = '+flags+'\n').encode())
        self.assertEqual(pair.input_configuration(self.root,self.root,'Makefile')['aarch64_CFLAGS'],pair.shlex.split(flags))
    def test_duplicate_configure_field_refused(self):
        self.write('Makefile',b'aarch64_CFLAGS = -g -O2\naarch64_CFLAGS = -g -O2\naarch64_CXXFLAGS = -g -O2\n')
        with self.assertRaises(reuse.Error):pair.input_configuration(self.root,self.root,'Makefile')
    def test_debug_policy_has_no_product_allowance(self):
        value=pair.policy(self.root,self.root);self.assertEqual(value['normalization'],'none')
        self.assertTrue(value['raw_product_comparison_required']);self.assertTrue(value['fresh_native_evidence_required'])
    def test_default_command_target_is_retained(self):
        source='src/dxmt/dxmt_command.metal'
        spec={'root':str(self.root),'metal':{'path':'/exact/metal'}}
        plan=metal.plan(spec,['-o',metal.OUTPUTS[source],'-c','../source/'+source])
        self.assertNotIn('-std=metal3.1',plan['argv']);self.assertNotIn('--target=air64-apple-macos14.0',plan['argv'])
    def test_each_airconv_original_target_is_retained(self):
        for source in metal.SOURCES:
            if source.startswith('src/airconv/'):
                plan=metal.plan({'root':str(self.root),'metal':{'path':'/exact/metal'}},
                    ['-o',metal.OUTPUTS[source],'-c','../source/'+source,*metal.EXTRAS[source]])
                self.assertIn('-std=metal3.1',plan['argv']);self.assertIn('--target=air64-apple-macos14.0',plan['argv'])
    def test_uniform_command_target_refused(self):
        source='src/dxmt/dxmt_command.metal'
        with self.assertRaises(metal.Error):metal.plan({'root':str(self.root),'metal':{'path':'/metal'}},
            ['-o',metal.OUTPUTS[source],'-c','../source/'+source,'-std=metal3.1','--target=air64-apple-macos14.0'])
    def test_arbitrary_output_and_source_refused(self):
        source=next(iter(metal.SOURCES))
        for output,name in [('../escape.air',source),(metal.OUTPUTS[source],'../../other.metal')]:
            with self.assertRaises(metal.Error):metal.plan({'root':str(self.root),'metal':{'path':'/metal'}},
                ['-o',output,'-c','../source/'+name,*metal.EXTRAS[source]])
    def test_main_remainder_delimiter_is_not_compiler_flag(self):
        with mock.patch.object(metal,'load_spec',return_value={}),mock.patch.object(metal,'command')as run:
            self.assertEqual(metal.main(['--spec','x','--spec-sha','a'*64,'--','-o','exact']),0)
        run.assert_called_once_with({},['-o','exact'])
    def test_wrapper_keeps_metallib_and_bounds_only_metal(self):
        raw=pair.wrapper(self.root,'/admitted/python',{'metallib':{'path':'/actual/metallib'}},'a'*64).decode()
        self.assertIn('metallib) shift; exec /usr/bin/arch -arm64 /actual/metallib "$@"',raw)
        self.assertIn(' -- "$@"',raw);self.assertIn('*) exit 64',raw)


@unittest.skipUnless(QUAL is not None,'optional actual Metal controls require PEAR_TEST_QUALIFICATION')
class MetalControlEnvironment(Temporary):
    def context(self):
        with reuse.legacy(REPO)as cap:
            common=cap.load('tools/dxmt/common.py')
            raw=common.read_relative(METAL_ROOT,'control.json')
        return json.loads(raw)
    @contextmanager
    def common(self):
        with reuse.legacy(REPO)as cap:yield cap.load('tools/dxmt/common.py')
    def test_genuine_predecessor_environment_and_tool_replay(self):
        value=self.context()
        with self.common()as common:
            prior=pair.metal_predecessor(value,METAL_ROOT,QUAL['metal_predecessor_refs'],common)
        self.assertEqual(value['tool_sha256'],prior['tool_sha256'])
    def test_zero_or_rehashed_predecessor_refused(self):
        for pin in ('0'*64,'a'*64,False):
            value=self.context();value['prior_probe_sha256']=pin
            with self.subTest(pin=pin),self.common()as common,self.assertRaises(reuse.Error):
                pair.metal_predecessor(value,METAL_ROOT,QUAL['metal_predecessor_refs'],common)
    def test_extra_dynamic_loader_and_altered_recipe_env_refused(self):
        for key,new in [('DYLD_INSERT_LIBRARIES','/unapproved.dylib'),('SDKROOT','/otherSDK'),
                        ('PATH','/unapproved/bin'),('TMPDIR','/other/tmp'),('HOME','/other/home')]:
            value=self.context();value['environment'][key]=new
            with self.subTest(key=key),self.common()as common,self.assertRaises(reuse.Error):
                pair.metal_predecessor(value,METAL_ROOT,QUAL['metal_predecessor_refs'],common)
    def test_predecessor_refs_are_closed_and_exactly_pinned(self):
        for action in ('extra','missing','changed_digest'):
            refs=copy.deepcopy(QUAL['metal_predecessor_refs'])
            if action=='extra':refs['unexpected']=refs['control']
            elif action=='missing':refs.pop('recipe')
            else:refs['producer']['sha256']='0'*64
            with self.subTest(action=action),self.common()as common,self.assertRaises(reuse.Error):
                pair.metal_predecessor(self.context(),METAL_ROOT,refs,common)
    def test_copied_ref_path_refused_by_original_producer_declaration(self):
        refs=copy.deepcopy(QUAL['metal_predecessor_refs']);original=Path(refs['control']['path'])
        copied=self.write('control.json',original.read_bytes());refs['control']['path']=str(copied)
        with self.common()as common,self.assertRaisesRegex(reuse.Error,'det_metal_predecessor_source_paths'):
            pair.metal_predecessor(self.context(),METAL_ROOT,refs,common)
    def test_altered_tool_digest_refused(self):
        value=self.context();value['tool_sha256']='0'*64
        with self.common()as common,self.assertRaises(reuse.Error):
            pair.metal_predecessor(value,METAL_ROOT,QUAL['metal_predecessor_refs'],common)


class Dependencies(Temporary):
    def test_literal_path_reader_rejects_arbitrary_or_dynamic_code(self):
        for raw in (b'prior = load_secret()',b'prior = Path(other)',b'prior = Path("../out")',
                    b'prior = Path("/valid")\nprior = Path("/other")'):
            with self.subTest(raw=raw),self.assertRaises(reuse.Error):pair.declared_path(raw,'prior')
    def test_make_escaped_spaces_and_continuation(self):
        self.assertEqual(pair.make_dependencies(b'/output\\ space.air: /resource\\ name/header \\\n /header.h\n'),
                         ('/output space.air',['/resource name/header','/header.h']))
    def test_malformed_make_controls(self):
        for raw in [b'a b: x',b'a: x x',b'a:',b'a: x\\',b'a: x\0',b'no target',b'a: x\nb: y']:
            with self.subTest(raw=raw),self.assertRaises((reuse.Error,UnicodeError)):pair.make_dependencies(raw)
    def test_dependency_size_bound(self):
        with self.assertRaises(reuse.Error):pair.make_dependencies(b'x'*(65536+1))
    def test_dependency_type_bound(self):
        with self.assertRaises(reuse.Error):pair.make_dependencies('a: b')


class Reuse(Temporary):
    def historical_root(self):
        # Only the reader's source-owner geometry is needed; no build payload,
        # signing/profile/authenticated prefix or executable is created.
        path=self.root/'owner/.build/task4/role'
        path.mkdir(parents=True,exist_ok=True)
        return path
    def test_actual_captured_imports_are_isolated_and_pure(self):
        previous=dict(sys.modules)
        with mock.patch('subprocess.Popen',side_effect=AssertionError('no tools permitted')):
            with reuse.legacy(REPO)as cap:
                reader=cap.load('tools/dxmt/pairing_check.py')
                self.assertEqual(reader.stage3.inspector().pe_readers()[0].__name__,'PE')
                self.assertEqual(reader.tools.readers().MACH_ARM64,0x100000c)
                self.assertEqual(len(cap.closure()),17)
        self.assertIs(sys.modules.get('common'),previous.get('common'))
        self.assertFalse(any(name.startswith(cap.name+'.')for name in sys.modules))
    def test_global_common_name_cannot_replace_captured_reader(self):
        foreign=object()
        with mock.patch.dict(sys.modules,{'common':foreign}):
            with reuse.legacy(REPO)as cap:self.assertIsNot(cap.load('tools/dxmt/pairing_check.py').need,foreign)
            self.assertIs(sys.modules['common'],foreign)
    def test_original_historical_reader_cannot_mutate_global_aliases_during_context(self):
        foreign = {key: object() for key in ('common', 'prepare', 'toolchain')}
        with mock.patch.dict(sys.modules, foreign), mock.patch('subprocess.Popen', side_effect=AssertionError('no tools')):
            with reuse.legacy(REPO) as cap:
                helper = cap.load('tools/dxmt/pairing_reuse.py')
                with helper.historical_toolchain(self.historical_root()) as reader:
                    for key, sentinel in foreign.items():
                        self.assertIs(sys.modules[key], sentinel)
                        self.assertIsNot(cap.module_view[key], sentinel)
                    self.assertTrue(reader.__name__.startswith(cap.name + '.'))
                    self.assertIs(reader, cap.module_view['toolchain'])
                for key, sentinel in foreign.items():
                    self.assertIs(sys.modules[key], sentinel)
                self.assertFalse(any(key in cap.module_view.aliases for key in foreign))
    def test_sys_proxy_rejects_unrelated_assignment_and_removal(self):
        with reuse.legacy(REPO) as cap:
            helper = cap.load('tools/dxmt/pairing_reuse.py')
            self.assertIsNot(helper.sys, sys)
            for key in ('unrelated', 'json', 'common'):
                with self.subTest(key=key), self.assertRaises(reuse.Error):
                    helper.sys.modules[key] = __import__('types').ModuleType(key)
            with self.assertRaises(reuse.Error):
                del helper.sys.modules['json']
    def test_sys_proxy_rejects_unselected_fex_package(self):
        with reuse.legacy(REPO) as cap:
            package = __import__('types').ModuleType('_pear_dxmt_reviewed_fex_bad')
            package.__path__ = [str(self.root / 'tools/fex')];package.__package__ = package.__name__
            with self.assertRaises(reuse.Error):cap.module_view[package.__name__] = package
    def test_local_alias_restoration_does_not_change_real_alias(self):
        with reuse.legacy(REPO) as cap:
            helper = cap.load('tools/dxmt/pairing_reuse.py')
            spec = cap.dynamic_spec('common', REPO / 'tools/wine/common.py')
            own = importlib.util.module_from_spec(spec);spec.loader.exec_module(own)
            cap.module_view['common'] = own
            with helper.historical_toolchain(self.historical_root()):
                self.assertIsNot(cap.module_view['common'], own)
            self.assertIs(cap.module_view['common'], own)
    @unittest.skipUnless(os.environ.get('PEAR_TEST_FEX_REPO'),'optional retained FEX input requires PEAR_TEST_FEX_REPO')
    def test_reviewed_fex_package_import_is_captured_without_global_package_alias(self):
        owner = Path(os.environ['PEAR_TEST_FEX_REPO'])
        name = '_pear_dxmt_reviewed_fex_' + reuse.digest(str(owner).encode())[:16]
        with mock.patch('subprocess.Popen', side_effect=AssertionError('no tools')):
            with reuse.legacy(REPO) as cap:
                package = __import__('types').ModuleType(name)
                package.__path__ = [str(owner / 'tools/fex')];package.__package__ = name
                cap.module_view[name] = package
                module = cap.import_module(name + '.tools')
                self.assertNotIn(name, sys.modules);self.assertNotIn(name + '.tools', sys.modules)
                self.assertTrue(module.__name__.startswith(cap.name + '.'))
                self.assertIs(module, cap.module_view[name + '.tools'])
                self.assertTrue(callable(module.verify_tools));cap.closure()
                with self.assertRaises(reuse.Error):cap.import_module(name + '.unreviewed')
    def test_unique_module_assignment_rejects_forged_source_and_unissued_name(self):
        with reuse.legacy(REPO) as cap:
            module = __import__('types').ModuleType(cap.name + '.forged')
            module.__file__ = str(REPO / 'tools/wine/common.py')
            with self.assertRaises(reuse.Error):cap.module_view[module.__name__] = module
    def test_relative_fromlist_cannot_admit_unselected_source(self):
        with reuse.legacy(REPO) as cap:
            origin={'__file__':str(REPO / 'tools/dxmt/pairing_check.py')}
            for names in [('*',),('pairing_runtime',),('../outside',)]:
                with self.subTest(names=names),self.assertRaises(reuse.Error):
                    cap.import_source('',origin,fromlist=names,level=1)
    def test_changed_predecessor_refused_before_module_execution(self):
        manifest=json.loads((IMPLEMENTATION/'reuse-pins.json').read_bytes())
        for path in manifest['files']:
            source=REPO/path;target=self.root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
        target=self.root/'tools/dxmt/check.py';target.write_bytes(target.read_bytes()+b'\n# altered\n')
        with self.assertRaisesRegex(reuse.Error,'reuse_predecessor_changed'):reuse.Captured(self.root,IMPLEMENTATION)
    def test_unselected_dynamic_module_refused(self):
        with reuse.legacy(REPO)as cap:
            with self.assertRaises(reuse.Error):cap.dynamic_spec('arbitrary',REPO/'tools/dxmt/pairing_runtime.py')
    def test_capture_symlink_leaf_refused(self):
        self.write('data',b'actual');(self.root/'alias').symlink_to('data')
        with self.assertRaises(OSError):reuse.read_file(self.root,'alias')
    def test_capture_symlink_parent_refused(self):
        self.write('real/data',b'actual');(self.root/'alias').symlink_to('real',target_is_directory=True)
        with self.assertRaises(OSError):reuse.read_file(self.root,'alias/data')
    def test_capture_unsafe_relative_names_refused(self):
        for name in ['../data','/data','data/../other','./data']:
            with self.subTest(name=name),self.assertRaises(reuse.Error):reuse.read_file(self.root,name)


class Resource(Temporary):
    @contextmanager
    def common(self):
        with reuse.legacy(REPO)as cap:yield cap.load('tools/dxmt/common.py')
    def test_contained_directory_alias_is_accounted_without_following(self):
        self.write('usr/metal/32023/header',b'exact');(self.root/'usr/metal/current').symlink_to('32023',target_is_directory=True)
        with self.common()as c:value=pair.resource_inventory(self.root,c)
        self.assertEqual(len(value['files']),2)
        self.assertEqual([x['type']for x in value['files']],['regular','symlink'])
    def test_contained_leaf_alias_is_accounted(self):
        self.write('actual',b'bytes');(self.root/'alias').symlink_to('actual')
        with self.common()as c:self.assertEqual(len(pair.resource_inventory(self.root,c)['files']),2)
    def test_absolute_alias_refused(self):
        self.write('data',b'x');(self.root/'alias').symlink_to(self.root/'data')
        with self.common()as c,self.assertRaises(reuse.Error):pair.resource_inventory(self.root,c)
    def test_escape_alias_refused(self):
        (self.root/'alias').symlink_to('../outside')
        with self.common()as c,self.assertRaises((reuse.Error,OSError)):pair.resource_inventory(self.root,c)
    def test_special_resource_refused(self):
        os.mkfifo(self.root/'fifo')
        with self.common()as c,self.assertRaises(reuse.Error):pair.resource_inventory(self.root,c)
    def test_empty_resource_refused(self):
        with self.common()as c,self.assertRaises(reuse.Error):pair.resource_inventory(self.root,c)


class FailedCompiler(Temporary):
    def fixture(self):
        source='src/dxmt/dxmt_command.metal'
        # Synthetic text is a failure-observation control only; no executable
        # fixture/compiler admission or qualified shader claim is constructed.
        raw=b'// finite source failure-control input\n'
        header=b'// finite header failure-control input\n'
        source_patch=mock.patch.dict(metal.SOURCES,{source:(metal.digest(raw),len(raw))})
        header_patch=mock.patch.object(metal,'HEADER_PIN',(metal.digest(header),len(header)))
        source_patch.start();header_patch.start();self.addCleanup(source_patch.stop);self.addCleanup(header_patch.stop)
        self.write('source/'+source,raw)
        self.write('source/'+metal.HEADER,header)
        for name in ['objects','shader-cache','shader-evidence']:(self.root/name).mkdir()
        spec={'root':str(self.root),'metal':{'path':'/selected/metal'},'environment':{'SOURCE_DATE_EPOCH':'0'},'resources_ref':{}}
        args=['-o',metal.OUTPUTS[source],'-c','../source/'+source]
        return source,spec,args
    @contextmanager
    def cwd(self):
        before=Path.cwd();os.chdir(self.root/'objects')
        try:yield
        finally:os.chdir(before)
    def test_start_errno_has_unknown_exit_and_preserved_raw_logs(self):
        _,spec,args=self.fixture()
        with self.cwd(),mock.patch.object(metal.subprocess,'Popen',side_effect=OSError(13,'denied')):
            with self.assertRaises(OSError):metal.command(spec,args)
        v=json.loads((self.root/'shader-evidence/dxmt_command.failed.json').read_bytes())
        self.assertEqual(v['native_error'],{'domain':'posix_errno','code':13});self.assertIsNone(v['exit_code'])
        self.assertFalse(v['process_started']);self.assertTrue(v['compilation_attempted']);self.assertFalse(v['passed'])
        self.assertEqual(set(v['logs']),{'stdout','stderr'})
    def test_original_source_error_does_not_claim_compiler_start(self):
        _,spec,args=self.fixture();self.write('source/'+metal.HEADER,b'wrong')
        with self.cwd(),mock.patch.object(metal.subprocess,'Popen')as run:
            with self.assertRaises(metal.Error):metal.command(spec,args)
        run.assert_not_called();v=json.loads((self.root/'shader-evidence/dxmt_command.failed.json').read_bytes())
        self.assertFalse(v['compilation_attempted']);self.assertFalse(v['process_started'])
    def test_nonzero_real_mock_exit_not_relabelled_zero(self):
        _,spec,args=self.fixture();process=mock.Mock(returncode=7);process.poll.return_value=7;process.wait.return_value=7
        with self.cwd(),mock.patch.object(metal.subprocess,'Popen',return_value=process):
            with self.assertRaises(metal.Error):metal.command(spec,args)
        v=json.loads((self.root/'shader-evidence/dxmt_command.failed.json').read_bytes())
        self.assertEqual(v['exit_code'],7);self.assertTrue(v['process_started']);self.assertFalse(v['passed'])
    def test_primary_communication_errno_survives_kill_and_wait_failure(self):
        _,spec,args=self.fixture();primary=OSError(13,'original communicate failure')
        process=mock.Mock();process.communicate.side_effect=primary;process.poll.return_value=None
        process.kill.side_effect=OSError(22,'secondary kill failure')
        process.wait.side_effect=OSError(10,'secondary wait failure')
        with self.cwd(),mock.patch.object(metal.subprocess,'Popen',return_value=process):
            with self.assertRaises(OSError)as caught:metal.command(spec,args)
        self.assertIs(caught.exception,primary)
        v=json.loads((self.root/'shader-evidence/dxmt_command.failed.json').read_bytes())
        self.assertEqual(v['native_error'],{'domain':'posix_errno','code':13})
        self.assertEqual([row['operation']for row in v['cleanup_errors']],['kill','wait'])
        self.assertEqual([row['native_error']['code']for row in v['cleanup_errors']],[22,10])
        self.assertIsNone(v['exit_code']);self.assertFalse(v['passed'])
        process.wait.assert_called_once_with(timeout=5)
    def test_cleanup_poll_failure_still_attempts_bounded_kill_and_wait(self):
        process=mock.Mock();process.poll.side_effect=OSError(5,'poll failure');process.wait.return_value=-9
        exit_code,rows=metal.stop(process)
        self.assertEqual(exit_code,-9);self.assertEqual(rows[0]['operation'],'poll')
        self.assertEqual(rows[0]['native_error']['code'],5)
        process.kill.assert_called_once();process.wait.assert_called_once_with(timeout=5)
    def test_cleanup_timeout_does_not_invent_exit(self):
        process=mock.Mock();process.poll.return_value=None
        process.wait.side_effect=metal.subprocess.TimeoutExpired('compiler',5)
        exit_code,rows=metal.stop(process)
        self.assertIsNone(exit_code);self.assertEqual(rows,[{'operation':'wait','error':'TimeoutExpired'}])
    def test_timeout_retains_attempt_argv_and_unknown_post_kill_exit(self):
        _,spec,args=self.fixture();process=mock.Mock();process.poll.return_value=None
        process.communicate.side_effect=metal.subprocess.TimeoutExpired('metal',.1)
        process.wait.side_effect=metal.subprocess.TimeoutExpired('metal',5)
        ticks=iter([0,0,601,602])
        with self.cwd(),mock.patch.object(metal.subprocess,'Popen',return_value=process),mock.patch.object(metal.time,'monotonic',side_effect=lambda:next(ticks)):
            with self.assertRaises(metal.Error):metal.command(spec,args)
        v=json.loads((self.root/'shader-evidence/dxmt_command.failed.json').read_bytes())
        self.assertEqual(v['bound_outcome'],'timeout');self.assertIsNone(v['exit_code']);self.assertTrue(v['argv'])
    def test_fast_oversized_output_refused_after_exit(self):
        _,spec,args=self.fixture();process=mock.Mock(returncode=0);process.poll.return_value=0;process.wait.return_value=0
        def communicate(**_):(self.root/'shader-evidence/dxmt_command.stderr').write_bytes(b'x'*(metal.MAX_LOG+1))
        process.communicate.side_effect=communicate
        with self.cwd(),mock.patch.object(metal.subprocess,'Popen',return_value=process):
            with self.assertRaises(metal.Error):metal.command(spec,args)
        v=json.loads((self.root/'shader-evidence/dxmt_command.failed.json').read_bytes())
        self.assertEqual(v['bound_outcome'],'output_limit');self.assertEqual(v['exit_code'],0);self.assertFalse(v['passed'])
        self.assertEqual(v['logs']['stderr']['size_bytes'],metal.MAX_LOG+1)
    def test_secondary_log_error_cannot_erase_primary_errno(self):
        _,spec,args=self.fixture();original=metal.fact
        def altered(root,path,limit=2**20):
            if path.endswith('.stdout'):raise OSError(5,'secondary')
            return original(root,path,limit)
        with self.cwd(),mock.patch.object(metal.subprocess,'Popen',side_effect=OSError(13,'primary')),mock.patch.object(metal,'fact',side_effect=altered):
            with self.assertRaises(OSError)as caught:metal.command(spec,args)
        self.assertEqual(caught.exception.errno,13);v=json.loads((self.root/'shader-evidence/dxmt_command.failed.json').read_bytes())
        self.assertEqual(v['native_error']['code'],13);self.assertEqual(v['evidence_errors'][0]['native_error']['code'],5)


class BuildScope(unittest.TestCase):
    def value(self):
        with reuse.legacy(REPO)as cap:
            reader=cap.load('tools/dxmt/pairing_check.py')
            value=dict.fromkeys([*reader.BUILD_FIELDS,*pair.ADDITIONS]);value.update(schema_version=1,record_kind=pair.KIND,scope=pair.SCOPE,passed=True)
            for name in reader.RUNTIME_FLAGS:value[name]=False
            return value,reader
    def test_constructed_build_has_no_runtime_authority(self):
        value,reader=self.value();self.assertIs(pair.constructor_record(value,reader),value)
    def test_each_false_runtime_flag_required(self):
        value,reader=self.value()
        for flag in reader.RUNTIME_FLAGS:
            bad=copy.deepcopy(value);bad[flag]=True
            with self.subTest(flag=flag),self.assertRaises(reuse.Error):pair.constructor_record(bad,reader)
    def test_old_kind_and_extra_fields_are_refused(self):
        value,reader=self.value()
        for change in [{'record_kind':'dxmt_pairing_build'},{'unexpected':'normalization'}]:
            bad={**value,**change}
            with self.assertRaises(reuse.Error):pair.constructor_record(bad,reader)
    def test_integer_booleans_refused(self):
        value,reader=self.value()
        for field in ['passed','native_execution']:
            bad=copy.deepcopy(value);bad[field]=1 if field=='passed'else 0
            with self.assertRaises(reuse.Error):pair.constructor_record(bad,reader)


class Epoch(unittest.TestCase):
    def pe(self,coff=0,debug=(0,0),timestamps=()):
        values={72:coff}
        for index,value in enumerate(timestamps):values[100+index*28+4]=value
        return type('ScalarPE',(),{'pe':64,'dirs':[(0,0)]*6+[debug],
            'u':lambda self,fmt,offset:values[offset],
            'offset':lambda self,rva,size:100})()
    def test_absent_debug_with_actual_epoch_zero(self):pair.pe_epoch(self.pe())
    def test_epoch_header_nonzero_refused(self):
        with self.assertRaises(reuse.Error):pair.pe_epoch(self.pe(coff=123))
    def test_debug_all_zero_accepted(self):pair.pe_epoch(self.pe(debug=(1000,56),timestamps=(0,0)))
    def test_one_debug_timestamp_nonzero_refused(self):
        with self.assertRaises(reuse.Error):pair.pe_epoch(self.pe(debug=(1000,56),timestamps=(0,7)))
    def test_malformed_debug_extent_refused(self):
        for debug in [(0,28),(1000,0),(1000,27),(1000,28*1025)]:
            with self.subTest(debug=debug),self.assertRaises(reuse.Error):pair.pe_epoch(self.pe(debug=debug))


class QualificationRefusals(Temporary):
    def test_old_two_control_summary_shape_refused(self):
        value=dict.fromkeys(pair.QUAL_FIELDS);value.update(schema_version=1,
            record_kind='dxmt_deterministic_input_qualification',scope='compiler_source_and_resource_bytes_only',
            source_date_epoch='0',native_engine_execution_performed=False,gpu_execution_performed=False)
        value['metal_control_refs']={};value.pop('metal_control_ref')
        self.write('qualification.json',pair.encoded(value));ref={'path':str(self.root/'qualification.json'),'sha256':pair.digest(pair.encoded(value))}
        with reuse.legacy(REPO)as cap,self.assertRaises(reuse.Error):pair.qualification(ref,self.root,cap.load('tools/dxmt/common.py'))
    def test_boolean_schema_version_not_integer_version(self):
        value=dict.fromkeys(pair.QUAL_FIELDS);value.update(schema_version=True,
            record_kind='dxmt_deterministic_input_qualification',scope='compiler_source_and_resource_bytes_only',
            source_date_epoch='0',native_engine_execution_performed=False,gpu_execution_performed=False)
        self.write('qualification.json',pair.encoded(value));ref={'path':str(self.root/'qualification.json'),'sha256':pair.digest(pair.encoded(value))}
        with reuse.legacy(REPO)as cap,self.assertRaises(reuse.Error):pair.qualification(ref,self.root,cap.load('tools/dxmt/common.py'))
    def test_changed_reference_bytes_refused(self):
        self.write('record.json',b'{}');ref={'path':str(self.root/'record.json'),'sha256':'0'*64}
        with reuse.legacy(REPO)as cap,self.assertRaises(reuse.Error):pair.ref_file(ref,cap.load('tools/dxmt/common.py'))
    def test_producer_membership_requires_exact_reviewed_source(self):
        raw=b'// arbitrary producer';self.write('producer',raw)
        value={'path':str(self.root/'producer'),'sha256':pair.digest(raw),'size_bytes':len(raw),'unchanged_observed':True}
        with reuse.legacy(REPO)as cap,self.assertRaises(reuse.Error):pair.probe_producer(value,pair.METAL_PROBE_PRODUCER,cap.load('tools/dxmt/common.py'))
    def test_old_metal_control_kind_refused(self):
        self.write('control.json',pair.encoded({'record_kind':'root_actual_four_shader_stdin_compile_probe'}))
        ref={'path':str(self.root/'control.json'),'sha256':pair.digest((self.root/'control.json').read_bytes())}
        with reuse.legacy(REPO)as cap,self.assertRaises(reuse.Error):pair.metal_control(ref,list(metal.SOURCES),self.root,{},{},cap.load('tools/dxmt/common.py'))
    def test_incomplete_wine_control_refused(self):
        self.write('control.json',pair.encoded({'record_kind':'root_actual_Wine_PE_object_debug_map_and_LLD_epoch_probe'}))
        ref={'path':str(self.root/'control.json'),'sha256':pair.digest((self.root/'control.json').read_bytes())}
        with reuse.legacy(REPO)as cap,self.assertRaises(reuse.Error):pair.wine_control(ref,self.root,cap.load('tools/dxmt/common.py'))


class TemplateInputs(Temporary):
    def template(self):
        return {'root':metal.ROOT_TOKEN,'environment':{'PATH':metal.ROOT_TOKEN+'/bin:/native/tools:/usr/bin',
            'TMPDIR':metal.ROOT_TOKEN+'/tmp','SDKROOT':'/selected/sdk','SOURCE_DATE_EPOCH':'0'}}
    def test_runtime_env_only_closed_root_slots_expand(self):
        value=metal.materialize(self.template(),self.root)
        self.assertEqual(value['root'],str(self.root));self.assertEqual(value['environment']['TMPDIR'],str(self.root/'tmp'))
        self.assertEqual(value['environment']['PATH'],str(self.root/'bin')+':/native/tools:/usr/bin')
        self.assertEqual(value['environment']['SDKROOT'],'/selected/sdk')
    def test_absolute_root_in_stored_template_refused(self):
        v=self.template();v['root']=str(self.root)
        with self.assertRaises(metal.Error):metal.materialize(v,self.root)
    def test_unknown_slot_or_repeated_path_slot_refused(self):
        for field,value in [('SDKROOT',metal.ROOT_TOKEN+'/sdk'),('PATH',metal.ROOT_TOKEN+'/bin:'+metal.ROOT_TOKEN+'/other'),
                            ('TMPDIR',metal.ROOT_TOKEN+'/elsewhere')]:
            v=self.template();v['environment'][field]=value
            with self.subTest(field=field),self.assertRaises(metal.Error):metal.materialize(v,self.root)
    def test_template_input_is_not_modified(self):
        v=self.template();before=copy.deepcopy(v);metal.materialize(v,self.root);self.assertEqual(v,before)
    def test_relative_root_template_preserves_whole_generated_bytes(self):
        a=self.root/'short';b=self.root/'sixteen-more-characters';a.mkdir();b.mkdir()
        generated=mock.Mock(return_value={'native.ini':(b'original native configuration',0o644)})
        h={'common':object(),'stage3':type('Stage3',(),{'generated_bytes':generated})()}
        cap={'selected':{'metal':{'path':'/actual/metal'},'metallib':{'path':'/actual/metallib'}}}
        record={'native_tools':{'python':{'path':'/actual/python'}}}
        fixed={'path':'/actual/metal','resolved_path':'/actual/metal','sha256':'a'*64,'size_bytes':1,'mode':0o755}
        with mock.patch.object(pair,'external_fact',return_value=fixed):
            first=pair.generated_inputs(h,a,{}, {},self.root,record,cap,{},
                {'PATH':str(a/'bin')+':/native','TMPDIR':str(a/'tmp'),'SOURCE_DATE_EPOCH':'0'}, {'resource_ref':{'path':'/sealed/catalog','sha256':'b'*64}})
            second=pair.generated_inputs(h,b,{}, {},self.root,record,cap,{},
                {'PATH':str(b/'bin')+':/native','TMPDIR':str(b/'tmp'),'SOURCE_DATE_EPOCH':'0'}, {'resource_ref':{'path':'/sealed/catalog','sha256':'b'*64}})
        self.assertEqual(first[0],second[0]);self.assertNotEqual(first[1]['root'],second[1]['root'])
        self.assertNotIn(str(a).encode(),first[0]['shader-inputs.json'][0])
        self.assertNotIn(str(b).encode(),second[0]['bin/xcrun'][0])
    def test_wrapper_does_not_embed_owned_root_or_parent_traversal(self):
        raw=pair.wrapper(self.root,'/python',{'metallib':{'path':'/metallib'}},'a'*64)
        self.assertNotIn(str(self.root).encode(),raw);self.assertNotIn(b'/../',raw)


class SpecBinding(Temporary):
    def test_changed_raw_spec_refused_before_any_tool_read(self):
        p=self.write('shader-inputs.json',b'{"root":"changed"}')
        with self.assertRaisesRegex(metal.Error,'shader_spec_digest'):metal.load_spec(p,'0'*64)
    def test_boolean_or_malformed_spec_digest_refused(self):
        p=self.write('shader-inputs.json',b'{}')
        for sha in [False,'a'*63,'z'*64,'A'*64]:
            with self.subTest(sha=sha),self.assertRaises(metal.Error):metal.load_spec(p,sha)
    def test_matching_digest_does_not_admit_invalid_spec_shape(self):
        raw=b'{}';p=self.write('shader-inputs.json',raw)
        with self.assertRaisesRegex(metal.Error,'shader_spec'):metal.load_spec(p,metal.digest(raw))
    def test_current_generated_spec_pin_is_in_wrapper(self):
        expected='e'*64;raw=pair.wrapper(self.root,'/python',{'metallib':{'path':'/metallib'}},expected)
        self.assertIn(('--spec-sha '+expected).encode(),raw)


if __name__=='__main__':unittest.main()
