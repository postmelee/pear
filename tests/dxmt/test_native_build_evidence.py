"""Original portable Stage 2 source/tool/command rejection fixtures.

These tests execute no upstream tool, native compiler, Metal compiler or guest.
"""
import hashlib
import io
from pathlib import Path
import struct
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools/dxmt'))
import tools
from common import Error, digest


class ToolArchiveTests(unittest.TestCase):
    def graph(self, members):
        buffer=io.BytesIO()
        with tarfile.open(fileobj=buffer,mode='w') as archive:
            for name,kind,target in members:
                member=tarfile.TarInfo('payload/'+name)
                if kind=='file':
                    member.size=1;archive.addfile(member,io.BytesIO(b'x'))
                else:
                    member.type=tarfile.SYMTYPE;member.linkname=target;archive.addfile(member)
        buffer.seek(0)
        with tarfile.open(fileobj=buffer,mode='r') as archive:
            return tools.archive_graph(archive,'payload',32)

    def test_escaping_link_refused_before_extraction(self):
        with self.assertRaises(Error):self.graph([('good','file',None),('bad','link','../../outside')])

    def test_link_parent_refused_before_extraction(self):
        with self.assertRaises(Error):self.graph([('actual','file',None),('alias','link','actual'),('alias/child','file',None)])

    def test_case_alias_refused(self):
        with self.assertRaises(Error):self.graph([('Tool','file',None),('tool','file',None)])

    def test_contained_alias_accounted(self):
        rows,total=self.graph([('actual','file',None),('alias','link','actual')])
        self.assertEqual(total,1)
        self.assertEqual(len(rows),2)

    def test_meson_unsupported_selected_source_refused(self):
        with self.assertRaises(Error):
            tools.meson_selection([{'path':'meson.py','mode':'100644'}, {'path':'COPYING','mode':'100644'},
                                   {'path':'mesonbuild/unsafe','mode':'120000'}])

    def test_meson_selects_only_runtime_source_and_notice(self):
        rows=tools.meson_selection([{'path':'meson.py','mode':'100644'}, {'path':'COPYING','mode':'100644'},
                                   {'path':'mesonbuild/core.py','mode':'100644'}, {'path':'test cases/untrusted','mode':'120000'}])
        self.assertEqual({r['path'] for r in rows},{'meson.py','COPYING','mesonbuild/core.py'})


class ToolCommandTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='pear-dxmt-native-evidence-')
        self.root=Path(self.temp.name).resolve()
        sdk=self.root/'sdk';sdk.mkdir()
        self.value={'native_tools':{'python':{'path':'/fixture/native-python'},'xcrun':{'path':'/fixture/native-xcrun'}},
                    'sdk':{'path':str(sdk),'version':'26.5'},'environment':tools.clean_env(),'commands':[]}
        outputs={'cmake.version':b'cmake version 3.31.8\n', 'ninja.version':b'1.13.1\n','meson.version':b'1.10.0\n',
                 'sdk.path':str(sdk).encode()+b'\n','sdk.version':b'26.5\n'}
        for ident,argv in tools.expected_commands(self.root,self.value).items():
            logs={}
            for stream,data in [('stdout',outputs[ident]),('stderr',b'')]:
                path=self.root/'logs'/ident/stream;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
                logs[stream]={'path':path.relative_to(self.root).as_posix(),'sha256':digest(data),'size_bytes':len(data)}
            self.value['commands'].append({'id':ident,'argv':argv,'cwd':str(self.root),'environment':tools.clean_env(),
                                          'exit_code':0,'timed_out':False,'output_limit':False,'elapsed_ms':1,'logs':logs})

    def tearDown(self):self.temp.cleanup()
    def test_complete_metadata_recipe_accepted(self):tools.verify_commands(self.root,self.value)
    def test_native_arch_request_cannot_be_omitted(self):
        self.value['commands'][0]['argv']=self.value['commands'][0]['argv'][2:]
        with self.assertRaises(Error):tools.verify_commands(self.root,self.value)
    def test_missing_tool_probe_cannot_claim_readiness(self):
        self.value['commands'].pop()
        with self.assertRaises(Error):tools.verify_commands(self.root,self.value)
    def test_ambient_path_cannot_change_recipe(self):
        self.value['commands'][0]['environment']={**tools.clean_env(),'PATH':'/unreviewed/toolchain'}
        with self.assertRaises(Error):tools.verify_commands(self.root,self.value)
    def test_changed_logged_version_rejected(self):
        (self.root/'logs/meson.version/stdout').write_bytes(b'2.0.0\n')
        with self.assertRaises(Error):tools.verify_commands(self.root,self.value)
    def test_tool_failures_cannot_be_success(self):
        self.value['commands'][2]['exit_code']=1
        with self.assertRaises(Error):tools.verify_commands(self.root,self.value)




import build_native


class NativeSourceAndPolicyTests(unittest.TestCase):
    def entries(self):
        return [{'path':name,'mode':'100644','git_object':'1'*40} for name in
                ['llvm/CMakeLists.txt','llvm/LICENSE.TXT','cmake/Modules/ExtendPath.cmake','llvm/lib/Core/Module.cpp',
                 'llvm/test/literal%test.ll','llvm/unittests/unused.cpp','clang/lib/unused.cpp']]

    def test_build_closure_excludes_ir_test_names_and_other_projects(self):
        self.assertEqual({r['path'] for r in build_native.select_llvm(self.entries())},
                         {'llvm/CMakeLists.txt','llvm/LICENSE.TXT','cmake/Modules/ExtendPath.cmake','llvm/lib/Core/Module.cpp'})

    def test_selected_symlink_refused(self):
        entries=self.entries()+[{'path':'llvm/lib/unsafe','mode':'120000','git_object':'2'*40}]
        with self.assertRaises(Error):build_native.select_llvm(entries)

    def test_materialized_percent_name_refused(self):
        entries=self.entries()+[{'path':'llvm/lib/unsafe%name','mode':'100644','git_object':'2'*40}]
        with self.assertRaises(Error):build_native.select_llvm(entries)

    def test_unbounded_jobs_refused(self):
        with self.assertRaises(Error):build_native.storage_policy(5,8*1024**3,4*1024**3)

    def test_ceiling_explicitly_not_measured_peak(self):
        policy=build_native.storage_policy(2,8*1024**3,4*1024**3)
        self.assertIsNone(policy['measured_build_peak_bytes'])
        self.assertFalse(policy['ceiling_is_peak_measurement'])

    def test_llvm_recipe_uses_upstream_arm64_baseline_and_scoped_system_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            record={'sdk':{'path':'/fixture/sdk'},'native_tools':{'clang':{'path':'/fixture/clang'},
                      'clang++':{'path':'/fixture/clang++'},'python':{'path':'/fixture/python'}}}
            recipe,options=build_native.llvm_recipe(root,root/'source-input',root/'tools',record,2)
            self.assertEqual(recipe['llvm.configure'][:2],['/usr/bin/arch','-arm64'])
            self.assertEqual(options['LLVM_TARGETS_TO_BUILD'],'')
            self.assertEqual(options['LLVM_ENABLE_ZSTD'],'OFF')
            self.assertEqual(options['CMAKE_OSX_ARCHITECTURES'],'arm64')
            self.assertEqual(options['LIBXML2_LIBRARY'],'/fixture/sdk/usr/lib/libxml2.tbd')
            self.assertEqual(options['CMAKE_FIND_USE_SYSTEM_ENVIRONMENT_PATH'],'FALSE')

    def library(self,cpu=build_native.MACH_ARM64):
        body=b'\xcf\xfa\xed\xfe'+struct.pack('<IIIIIII',cpu,0,1,0,0,0,0)
        header=b'object.o/       '+b'0           '+b'0     '+b'0     '+b'100644  '+str(len(body)).encode().ljust(10)+b'`\n'
        return b'!<arch>\n'+header+body

    def test_native_static_object_archive_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'libFixture.a';path.write_bytes(self.library())
            self.assertEqual(build_native.inspect_native_archive(path)['architectures'],[build_native.MACH_ARM64])

    def test_x64_static_member_cannot_be_native_prerequisite(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'libFixture.a';path.write_bytes(self.library(0x1000007))
            with self.assertRaises(Error):build_native.inspect_native_archive(path)


class NativeReplayTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='pear-dxmt-native-replay-')
        self.root=Path(self.temp.name).resolve()
        self.policy=build_native.storage_policy(2,8*1024**3,4*1024**3)
        self.env={'PATH':'/fixture/native-tools'}
        self.recipe={'fixture.compile':['/usr/bin/arch','-arm64','/fixture/compiler','-c','/fixture/source.cpp']}
        logs={}
        for stream in ['stdout','stderr']:
            path=self.root/'logs/fixture.compile'/stream;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'')
            logs[stream]={'path':path.relative_to(self.root).as_posix(),'sha256':digest(b''),'size_bytes':0}
        self.commands=[{'id':'fixture.compile','argv':self.recipe['fixture.compile'],'cwd':str(self.root),'environment':self.env,
                        'exit_code':0,'elapsed_ms':1,'stop_reason':None,'growth_bytes_observed':1,'logs':logs}]

    def tearDown(self):self.temp.cleanup()
    def test_accounted_compile_record_accepted(self):
        build_native.verify_native_commands(self.root,self.commands,self.recipe,self.env,self.policy)
    def test_false_boolean_cannot_replace_observed_zero_exit_code(self):
        self.commands[0]['exit_code']=False
        with self.assertRaises(Error):
            build_native.verify_native_commands(self.root,self.commands,self.recipe,self.env,self.policy)
    def test_storage_stop_cannot_be_a_build_pass(self):
        self.commands[0]['stop_reason']='growth_ceiling'
        with self.assertRaises(Error):build_native.verify_native_commands(self.root,self.commands,self.recipe,self.env,self.policy)
    def test_missing_native_operation_refused(self):
        with self.assertRaises(Error):build_native.verify_native_commands(self.root,[],self.recipe,self.env,self.policy)
    def test_changed_compiler_scope_refused(self):
        self.commands[0]['argv']=['/usr/bin/arch','-x86_64','/fixture/compiler']
        with self.assertRaises(Error):build_native.verify_native_commands(self.root,self.commands,self.recipe,self.env,self.policy)
    def test_scoped_environment_derivation_is_read_only(self):
        record={'sdk':{'path':'/fixture/sdk'}}
        before=set(self.root.iterdir())
        first=build_native.native_environment(self.root,self.root/'tools',record)
        second=build_native.native_environment(self.root,self.root/'tools',record)
        self.assertEqual(first,second)
        self.assertEqual(set(self.root.iterdir()),before)
    def test_xcrun_forwarder_binds_real_paths_and_native_cpu(self):
        selected={'metal':{'path':'/fixture/Metal Toolchain/metal'},'metallib':{'path':'/fixture/Metal Toolchain/metallib'}}
        wrapper=build_native.xcrun_wrapper(selected)
        self.assertIn(b'exec /usr/bin/arch -arm64',wrapper)
        self.assertIn(b"'/fixture/Metal Toolchain/metal'",wrapper)
        self.assertIn(b'*) exit 64',wrapper)


class LiveBuildInventoryTests(unittest.TestCase):
    def test_vanished_compiler_temporary_file_is_not_special_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);temporary=root/'compiler.tmp';temporary.write_bytes(b'temporary object')
            original=Path.lstat
            def raced(path,*args,**kwargs):
                if path==temporary and temporary.exists():temporary.unlink()
                return original(path,*args,**kwargs)
            with mock.patch.object(Path,'lstat',raced):
                self.assertEqual(build_native.directory_usage(root),0)

    def test_vanished_directory_does_not_disable_remaining_accounting(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);vanished=root/'temporary';vanished.mkdir();retained=root/'object.o';retained.write_bytes(b'object')
            expected=retained.lstat().st_blocks*512;original=Path.lstat
            def raced(path,*args,**kwargs):
                if path==vanished and vanished.exists():vanished.rmdir()
                return original(path,*args,**kwargs)
            with mock.patch.object(Path,'lstat',raced):
                self.assertEqual(build_native.directory_usage(root),expected)

    def test_existing_file_and_directory_links_remain_refused(self):
        for target_kind in ['file','directory']:
            with self.subTest(target_kind=target_kind),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);target=root/'target'
                target.mkdir() if target_kind=='directory' else target.write_bytes(b'object')
                (root/'alias').symlink_to(target,target_is_directory=target_kind=='directory')
                with self.assertRaises(Error):build_native.directory_usage(root)

    def test_existing_special_file_remains_refused(self):
        import os
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);os.mkfifo(root/'special')
            with self.assertRaises(Error):build_native.directory_usage(root)

    def test_nonabsence_inventory_error_is_not_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with mock.patch.object(Path,'lstat',side_effect=PermissionError('fixture denied')):
                with self.assertRaises(PermissionError):build_native.directory_usage(root)

    def test_walk_error_only_tolerates_missing_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            def denied(*args,**kwargs):
                kwargs['onerror'](PermissionError('fixture denied'))
                return iter(())
            with mock.patch.object(build_native.os,'walk',side_effect=denied):
                with self.assertRaises(PermissionError):build_native.directory_usage(root)


class NativeMonitorFailureTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='pear-dxmt-monitor-');self.root=Path(self.temp.name)
        self.policy=build_native.storage_policy(2,8*1024**3,4*1024**3);self.commands=[]
        self.process=mock.Mock(pid=54321)
        self.process.poll.return_value=None;self.process.wait.return_value=-9
        def launch(*args,**kwargs):
            kwargs['stdout'].write(b'partial compiler output');kwargs['stdout'].flush()
            kwargs['stderr'].write(b'partial compiler diagnostic');kwargs['stderr'].flush()
            return self.process
        self.launch=mock.patch.object(build_native.subprocess,'Popen',side_effect=launch)

    def tearDown(self):self.temp.cleanup()

    def run_failure(self,observations):
        with self.launch as launch,mock.patch.object(build_native,'directory_usage',side_effect=observations),mock.patch.object(build_native.os,'killpg') as kill:
            with self.assertRaises(Error) as caught:
                build_native.monitored_command(self.root,'fixture.compile',['/fixture/compiler'],{'PATH':'/fixture'},self.policy,self.commands)
        self.assertEqual(caught.exception.code,'native_build_special_output')
        self.assertEqual(len(self.commands),1)
        row=self.commands[0]
        self.assertEqual(row['stop_reason'],'inventory_error:native_build_special_output')
        self.assertIsInstance(row['elapsed_ms'],int)
        self.assertEqual(set(row['logs']),{'stdout','stderr'})
        for ref in row['logs'].values():
            self.assertEqual(sha256(self.root/ref['path']),ref['sha256'])
            self.assertEqual((self.root/ref['path']).stat().st_size,ref['size_bytes'])
        with self.assertRaises(Error):
            build_native.verify_native_commands(self.root,self.commands,{'fixture.compile':['/fixture/compiler']},{'PATH':'/fixture'},self.policy)
        return row,launch,kill

    def test_running_inventory_failure_stops_owned_group_and_preserves_row(self):
        row,launch,kill=self.run_failure([0,Error('native_build_special_output'),0])
        self.assertEqual(row['exit_code'],-9);launch.assert_called_once()
        kill.assert_called_once_with(54321,build_native.signal.SIGKILL)
        self.assertEqual((self.root/row['logs']['stdout']['path']).read_bytes(),b'partial compiler output')
        self.assertEqual((self.root/row['logs']['stderr']['path']).read_bytes(),b'partial compiler diagnostic')

    def test_final_inventory_failure_preserves_already_completed_command(self):
        self.process.poll.return_value=0;self.process.wait.return_value=0
        row,launch,kill=self.run_failure([0,Error('native_build_special_output')])
        self.assertEqual(row['exit_code'],0);launch.assert_called_once();kill.assert_not_called()

    def test_initial_inventory_failure_records_no_launched_process(self):
        row,launch,kill=self.run_failure([Error('native_build_special_output'),0])
        self.assertIsNone(row['exit_code']);launch.assert_not_called();kill.assert_not_called()
        self.assertEqual(row['logs']['stdout']['size_bytes'],0)
        self.assertEqual(row['logs']['stderr']['size_bytes'],0)


class EmbeddedShaderTests(unittest.TestCase):
    def test_air_bytes_and_length_bound(self):
        header=b'unsigned char fixture[] = {0x42, 0x43};\nunsigned int fixture_len = 2;\n'
        build_native.verify_embedded_header(header,b'BC','fixture')
    def test_matching_name_cannot_hide_changed_air(self):
        header=b'unsigned char fixture[] = {0x42, 0x43};\nunsigned int fixture_len = 2;\n'
        with self.assertRaises(Error):build_native.verify_embedded_header(header,b'XX','fixture')
    def test_false_embedded_length_rejected(self):
        header=b'unsigned char fixture[] = {0x42, 0x43};\nunsigned int fixture_len = 3;\n'
        with self.assertRaises(Error):build_native.verify_embedded_header(header,b'BC','fixture')




class InstalledLLVMClosureTests(unittest.TestCase):
    def test_archive_members_have_exact_byte_identity(self):
        fixture=NativeSourceAndPolicyTests()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'libFixture.a';path.write_bytes(fixture.library())
            result=build_native.inspect_native_archive(path)
            self.assertEqual(len(result['members']),1)
            self.assertEqual(result['members'][0]['size_bytes'],32)
            self.assertEqual(result['members'][0]['cpu'],build_native.MACH_ARM64)
            self.assertEqual(len(result['members'][0]['sha256']),64)
    def test_symbol_like_name_cannot_hide_x64_object(self):
        fixture=NativeSourceAndPolicyTests()
        data=fixture.library(0x1000007).replace(b'object.o/       ',b'__.SYMDEFbad/   ')
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'libFixture.a';path.write_bytes(data)
            with self.assertRaises(Error):build_native.inspect_native_archive(path)
    def test_second_member_byte_changes_are_observable(self):
        fixture=NativeSourceAndPolicyTests()
        first=fixture.library()[8:]
        second=first.replace(b'object.o/       ',b'second.o/       ')
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'libFixture.a';path.write_bytes(b'!<arch>\n'+first+second)
            result=build_native.inspect_native_archive(path)
            self.assertEqual(len(result['members']),2)
            self.assertEqual(result['members'][1]['name'],'second.o/')


class InstalledTableGenTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='pear-dxmt-installed-tablegen-')
        self.root=Path(self.temp.name);self.install=self.root/'install'
        header=self.install/'include/llvm/Config/llvm-config.h';header.parent.mkdir(parents=True)
        header.write_bytes(b'#define LLVM_VERSION_MAJOR 15\n#define LLVM_VERSION_MINOR 0\n#define LLVM_VERSION_PATCH 7\n')
        (header.parent/'abi-breaking.h').write_bytes(b'Original fixture ABI header')
        (self.install/'lib').mkdir()
        archive=NativeSourceAndPolicyTests().library()
        for name in build_native.LLVM_LIBRARIES:(self.install/'lib'/('lib'+name+'.a')).write_bytes(archive)
        self.built=self.root/'objects/bin/llvm-tblgen';self.built.parent.mkdir(parents=True)
        self.installed=self.install/'bin/llvm-tblgen';self.installed.parent.mkdir()
        self.replace_both(self.macho())

    def tearDown(self):self.temp.cleanup()

    def macho(self,cpu=build_native.MACH_ARM64,filetype=2,dependency='/usr/lib/libSystem.B.dylib'):
        payload=dependency.encode()+b'\0';length=(24+len(payload)+7)&~7
        command=struct.pack('<IIIIII',0xc,length,24,0,0,0)+payload
        command+=b'\0'*(length-len(command))
        return b'\xcf\xfa\xed\xfe'+struct.pack('<7I',cpu,0,filetype,1,length,0,0)+command+b'Original TableGen fixture code'

    def replace_both(self,content):
        for path in [self.built,self.installed]:path.write_bytes(content);path.chmod(0o755)

    def test_only_source_built_installed_arm64_tablegen_is_admitted(self):
        result=build_native.inspect_llvm(self.root)
        tool=result['installed_tablegen']
        self.assertEqual(tool['path'],'bin/llvm-tblgen')
        self.assertEqual(tool['built_origin'],'objects/bin/llvm-tblgen')
        self.assertEqual(tool['sha256'],result['tablegen']['sha256'])
        self.assertEqual(tool['architectures'],[build_native.MACH_ARM64])
        self.assertEqual(tool['dependencies'],['/usr/lib/libSystem.B.dylib'])
        self.assertEqual(tool['mode'],0o755)

    def test_changed_installed_bytes_cannot_be_relabelled_as_built_origin(self):
        self.installed.write_bytes(self.installed.read_bytes()+b'changed')
        with self.assertRaisesRegex(Error,'installed_tablegen_origin_changed'):build_native.inspect_llvm(self.root)

    def test_missing_or_nonexecutable_installed_role_is_refused(self):
        self.installed.chmod(0o644)
        with self.assertRaisesRegex(Error,'installed_tablegen_missing'):build_native.inspect_llvm(self.root)
        self.installed.unlink()
        with self.assertRaisesRegex(Error,'installed_tablegen_missing'):build_native.inspect_llvm(self.root)

    def test_exact_byte_copy_cannot_admit_x64_or_shared_library_tablegen(self):
        for content in [self.macho(cpu=0x1000007),self.macho(filetype=6)]:
            with self.subTest(kind=content[4:16]):
                self.replace_both(content)
                with self.assertRaises(Error):build_native.inspect_llvm(self.root)

    def test_exact_byte_copy_cannot_admit_non_system_dependencies(self):
        self.replace_both(self.macho(dependency='/opt/homebrew/lib/libunreviewed.dylib'))
        with self.assertRaisesRegex(Error,'tablegen_native_closure'):build_native.inspect_llvm(self.root)

    def test_other_installed_native_binary_is_refused(self):
        for magic in [b'\xcf\xfa\xed\xfe',b'\xce\xfa\xed\xfe',b'\xfe\xed\xfa\xcf',b'\xfe\xed\xfa\xce',
                      b'\xca\xfe\xba\xbe',b'\xca\xfe\xba\xbf',b'\xbe\xba\xfe\xca',b'\xbf\xba\xfe\xca']:
            with self.subTest(magic=magic):
                (self.install/'bin/unrelated-tool').write_bytes(magic+b'Unreviewed binary fixture')
                with self.assertRaisesRegex(Error,'unexpected_installed_native_binary'):build_native.inspect_llvm(self.root)

    def test_installed_shared_library_remains_refused(self):
        (self.install/'lib/unexpected.dylib').write_bytes(self.macho(filetype=6))
        with self.assertRaisesRegex(Error,'unexpected_dynamic_llvm'):build_native.inspect_llvm(self.root)

    def test_installed_alias_does_not_replace_required_regular_tool(self):
        self.installed.unlink();self.installed.symlink_to(self.built)
        with self.assertRaises(Error):build_native.inspect_llvm(self.root)




from unittest import mock
import check
from common import encoded, sha256, run_bounded


class ShaderCapabilityReplayTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='pear-dxmt-shader-replay-')
        self.repo=Path(self.temp.name).resolve();self.root=self.repo/'.build/task7/capability';self.root.mkdir(parents=True)
        self.tool_root=self.repo/'.build/task7/tools';self.tool_root.mkdir();(self.tool_root/'prepared.json').write_bytes(b'Original fixture tool evidence')
        self.record={'sdk':{'path':'/fixture/sdk'},'native_tools':{'xcrun':{'path':'/fixture/xcrun'}}}
        self.selected={name:{'path':'/fixture/'+name,'sha256':digest(name.encode())} for name in ['metal','metallib']}
        for name in ['tools/dxmt/check.py','tools/dxmt/common.py','tools/dxmt/tools.py','tools/wine/common.py','tools/wine/toolchain.py']:
            path=self.repo/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'Original producer fixture')
        (self.root/'probe.metal').write_bytes(check.SHADER_PROBE)
        (self.root/'probe.air').write_bytes(b'BC\xc0\xde'+b'A'*40)
        (self.root/'probe.metallib').write_bytes(b'MTLB'+b'L'*40)
        env=check.shader_environment(self.root,self.record)
        self.value={'schema_version':1,'record_kind':'dxmt_shader_capabilities','scope':'dxmt_component',
             'tools_ref':{'path':str(self.tool_root),'sha256':sha256(self.tool_root/'prepared.json')},'producers':check.shader_producers(self.repo),
             'selection_mode':'explicit_paths','selected':self.selected,'environment':env,'commands':[],
             'outputs':[check.shader_output(self.root/'probe.air','air'),check.shader_output(self.root/'probe.metallib','metallib')],
             'shader_build_ready':True,'gpu_or_guest_execution_performed':False,'runtime_eligible':False}
        for ident,argv in check.shader_recipe(self.root,self.selected).items():
            logs={}
            for stream,data in [('stdout',b'Original fixture version/compile log'),('stderr',b'')]:
                path=self.root/'logs'/ident/stream;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
                logs[stream]={'path':path.relative_to(self.root).as_posix(),'sha256':digest(data),'size_bytes':len(data)}
            self.value['commands'].append({'id':ident,'argv':argv,'cwd':str(self.root),'environment':env,'exit_code':0,
                  'timed_out':False,'output_limit':False,'elapsed_ms':1,'logs':logs})

    def tearDown(self):self.temp.cleanup()
    def replay(self):
        (self.root/'capabilities.json').write_bytes(encoded(self.value))
        with mock.patch.object(tools,'verify_tools',return_value=self.record),mock.patch.object(tools,'native_file',side_effect=lambda p:self.selected[Path(p).name]):
            return check.verify_shader_capabilities(self.root,self.repo)
    def test_complete_synthetic_record_replays_without_execution(self):
        self.assertTrue(self.replay()['shader_build_ready'])
    def test_missing_metallib_operation_refused(self):
        self.value['commands'].pop()
        with self.assertRaises(Error):self.replay()
    def test_failed_metadata_cannot_claim_ready(self):
        self.value['commands'][1]['exit_code']=1
        with self.assertRaises(Error):self.replay()
    def test_failed_compile_can_be_accounted_without_shader_readiness(self):
        self.value['commands'][-2]['exit_code']=1;self.value['commands'].pop()
        self.value['shader_build_ready']=False
        (self.root/'probe.metallib').unlink();self.value['outputs'].pop()
        self.assertFalse(self.replay()['shader_build_ready'])
    def test_changed_air_bytes_refused(self):
        (self.root/'probe.air').write_bytes(b'BC\xc0\xde'+b'X'*40)
        with self.assertRaises(Error):self.replay()
    def test_gpu_execution_claim_refused(self):
        self.value['gpu_or_guest_execution_performed']=True
        with self.assertRaises(Error):self.replay()
    def test_changed_shader_target_refused(self):
        self.value['commands'][2]['argv'][-1]='--target=air64-apple-macos26.0'
        with self.assertRaises(Error):self.replay()


class BoundedFailureStreamTests(unittest.TestCase):
    def test_bound_failure_preserves_raw_streams(self):
        with tempfile.TemporaryDirectory(prefix='pear-dxmt-command-bound-') as directory:
            root=Path(directory)
            with self.assertRaises(Error):
                run_bounded([sys.executable,'-B','-c','import sys;sys.stdout.write("original fixture output"*1000);sys.stdout.flush()'],
                            timeout=5,limit=64,log_directory=root)
            self.assertGreater((root/'stdout').stat().st_size,64)
            self.assertEqual((root/'stderr').read_bytes(),b'')



class ShaderNativeDependencyTests(unittest.TestCase):
    """Original byte fixtures model Meson's native parser archive dependency."""
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='pear-dxmt-native-parser-')
        self.root=Path(self.temp.name)
        for target in ['airconv.p','libairconv.a.p']:
            base=self.root/'objects/src/airconv/darwin'/target;base.mkdir(parents=True)
            for name in ['air_msad','air_samplepos','air_tessellation']:
                payload=b'BC\xc0\xde'+b'Original AIR fixture bytes'*2
                (base/(name+'.air')).write_bytes(payload)
                (base/(name+'.h')).write_bytes(self.header(payload,name))
        shaders=self.root/'shaders';shaders.mkdir()
        (shaders/'dxmt_command.air').write_bytes(b'BC\xc0\xde'+b'Original builtin AIR fixture'*2)
        metallib=b'MTLB'+b'Original builtin library fixture'*2
        (shaders/'dxmt_command.metallib').write_bytes(metallib)
        (shaders/'dxmt_command.h').write_bytes(self.header(metallib,'dxmt_command'))
        self.archive=NativeSourceAndPolicyTests().library()
        base=self.root/'objects/src/airconv/darwin'
        (base/'airconv').write_bytes(InstalledTableGenTests().macho())
        (base/'libairconv.a').write_bytes(self.archive)
        self.parser=self.root/'objects/libs/DXBCParser/libDXBCParserNative.a'
        self.parser.parent.mkdir(parents=True);self.parser.write_bytes(self.archive)

    def tearDown(self):self.temp.cleanup()

    @staticmethod
    def header(payload,name):
        tokens=', '.join('0x%02x'%value for value in payload)
        return ('unsigned char '+name+'[] = {'+tokens+'};\nunsigned int '+name+'_len = '+str(len(payload))+';\n').encode()

    def test_native_parser_role_binds_actual_archive_and_each_object(self):
        result=build_native.inspect_shader_build(self.root)
        parser=result['dxbc_parser_native_library']
        self.assertEqual(parser['path'],'objects/libs/DXBCParser/libDXBCParserNative.a')
        self.assertEqual(parser['sha256'],digest(self.archive))
        self.assertEqual(parser['architectures'],[build_native.MACH_ARM64])
        self.assertEqual(parser['members'][0]['sha256'],digest(self.archive[68:]))
        self.assertEqual(parser['members'][0]['filetype'],1)
        self.assertEqual(result['airconv_execution'],'unperformed')
        self.assertEqual(result['gpu_execution'],'unperformed')

    def test_missing_separate_parser_archive_is_not_covered_by_executable(self):
        self.parser.unlink()
        with self.assertRaisesRegex(Error,'airconv_native_parser_missing'):
            build_native.inspect_shader_build(self.root)

    def test_parser_archive_with_x64_object_cannot_claim_native_closure(self):
        self.parser.write_bytes(NativeSourceAndPolicyTests().library(0x1000007))
        with self.assertRaisesRegex(Error,'native_archive_requires_rosetta'):
            build_native.inspect_shader_build(self.root)

    def test_parser_member_byte_change_changes_replayed_output(self):
        before=build_native.inspect_shader_build(self.root)['dxbc_parser_native_library']
        changed=bytearray(self.archive);changed[-1]^=1;self.parser.write_bytes(changed)
        after=build_native.inspect_shader_build(self.root)['dxbc_parser_native_library']
        self.assertNotEqual(before['sha256'],after['sha256'])
        self.assertNotEqual(before['members'][0]['sha256'],after['members'][0]['sha256'])

    def test_parser_leaf_alias_cannot_replace_owned_output(self):
        self.parser.unlink();self.parser.symlink_to(self.root/'objects/src/airconv/darwin/libairconv.a')
        with self.assertRaisesRegex(Error,'airconv_native_parser_missing'):
            build_native.inspect_shader_build(self.root)

    def test_parser_parent_alias_cannot_escape_dependency_output(self):
        base=self.parser.parent;other=base.with_name('actual-parser');base.rename(other);base.symlink_to(other,target_is_directory=True)
        with self.assertRaises((Error,OSError)):
            build_native.inspect_shader_build(self.root)


class ShaderOwnedPathTests(unittest.TestCase):
    setUp=ShaderNativeDependencyTests.setUp
    tearDown=ShaderNativeDependencyTests.tearDown
    header=staticmethod(ShaderNativeDependencyTests.header)

    def test_airconv_executable_parent_alias_is_refused(self):
        base=self.root/'objects/src/airconv/darwin';other=base.with_name('actual-darwin')
        base.rename(other);base.symlink_to(other,target_is_directory=True)
        with self.assertRaises((Error,OSError)):build_native.inspect_shader_build(self.root)

    def test_airconv_archive_parent_alias_is_refused_by_rooted_reader(self):
        base=self.root/'objects/src/airconv/darwin';other=base.with_name('actual-darwin')
        base.rename(other);base.symlink_to(other,target_is_directory=True)
        with self.assertRaises((Error,OSError)):
            build_native.inspect_native_archive(base/'libairconv.a',root=self.root)

    def test_airconv_executable_leaf_alias_is_refused(self):
        exe=self.root/'objects/src/airconv/darwin/airconv';actual=exe.with_name('actual-airconv')
        exe.rename(actual);exe.symlink_to(actual)
        with self.assertRaises((Error,OSError)):build_native.inspect_shader_build(self.root)

    def test_rooted_executable_hash_matches_the_exact_inspected_bytes(self):
        exe=self.root/'objects/src/airconv/darwin/airconv'
        self.assertEqual(build_native.inspect_rooted_macho(self.root,exe)['sha256'],digest(exe.read_bytes()))


class ShaderBuildAttemptTests(unittest.TestCase):
    def run_fixture(self,failed_id=None,subprocess_failure=False):
        import json
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory(prefix='pear-dxmt-build-attempt-') as directory:
            repo=Path(directory).resolve();task=repo/'.build/task7';task.mkdir(parents=True)
            for name,receipt in [('tools','prepared.json'),('llvm','build.json'),('prepared','prepared.json'),('caps','capabilities.json')]:
                root=task/name;root.mkdir();(root/receipt).write_bytes(b'Original private record fixture')
            tools_root=task/'tools';prepared=task/'prepared';llvm=task/'llvm';caps=task/'caps'
            tool_ref={'path':str(tools_root),'sha256':sha256(tools_root/'prepared.json')}
            source_ref={'path':str(prepared),'sha256':sha256(prepared/'prepared.json')}
            tool_record={'sdk':{'path':'/fixture/sdk'},'native_tools':{name:{'path':'/fixture/'+name} for name in ['clang','clang++','python','xxd']}}
            capability={'shader_build_ready':True,'tools_ref':tool_ref,'selected':{name:{'path':'/fixture/'+name} for name in ['metal','metallib']}}
            def copy(prepared_root,output):
                (output/'source').mkdir()
                if failed_id=='source.copy':raise OSError('original_fixture_failure')
            def command(root,ident,argv,env,policy,rows):
                rows.append({'id':ident,'exit_code':None if ident==failed_id else 0,'stop_reason':'fixture_failure' if ident==failed_id else None})
                if ident==failed_id:
                    if subprocess_failure:raise build_native.subprocess.TimeoutExpired('original_fixture_failure',1)
                    raise Error('original_fixture_failure')
                if ident=='builtin.metal':(root/'shaders/dxmt_command.air').write_bytes(b'BC\xc0\xde'+b'Original compiled AIR fixture'*2)
            with mock.patch.object(build_native,'verify_llvm',return_value={'tools_ref':tool_ref,'source_ref':{'path':'/fixture/source'}}), \
                 mock.patch.object(tools,'verify_tools',return_value=tool_record),mock.patch.object(check,'verify_shader_capabilities',return_value=capability), \
                 mock.patch.object(build_native,'verify_prepared',return_value={}),mock.patch.object(build_native,'verify_source',return_value={'prepared_ref':source_ref}), \
                 mock.patch.object(build_native,'copy_dxmt',side_effect=copy),mock.patch.object(build_native,'producers',return_value={}), \
                 mock.patch.object(build_native.shutil,'disk_usage',return_value=SimpleNamespace(free=64*1024**3)), \
                 mock.patch.object(build_native,'monitored_command',side_effect=command),mock.patch.object(build_native,'inspect_shader_build',return_value={'original_fixture':'complete'}):
                if failed_id:
                    expected=OSError if failed_id=='source.copy' else build_native.subprocess.TimeoutExpired if subprocess_failure else Error
                    with self.assertRaisesRegex(expected,'original_fixture_failure'):
                        build_native.build_shaders(llvm,prepared,tools_root,caps,'.build/task7/output',2,8*1024**3,4*1024**3,repo)
                    result=json.loads((task/'output/failed.json').read_text())
                    self.assertFalse((task/'output/build.json').exists())
                else:
                    result=build_native.build_shaders(llvm,prepared,tools_root,caps,'.build/task7/output',2,8*1024**3,4*1024**3,repo)
            return result

    def test_owned_source_setup_failure_preserves_unperformed_failed_receipt(self):
        result=self.run_fixture('source.copy')
        self.assertEqual(result['generated_inputs'],[]);self.assertEqual(result['commands'],[])
        self.assertFalse(result['shader_compilation_performed'])
        self.assertEqual(result['shader_compilation_observation']['status'],'unperformed')
        self.assertFalse(result['passed']);self.assertFalse(result['stage2_complete'])

    def test_configuration_failure_records_compilation_unperformed(self):
        result=self.run_fixture('airconv.configure')
        self.assertFalse(result['shader_compilation_performed'])
        self.assertEqual(result['shader_compilation_observation']['status'],'unperformed')
        self.assertFalse(result['passed']);self.assertFalse(result['stage2_complete'])
        self.assertFalse(result['gpu_or_guest_execution_performed']);self.assertFalse(result['runtime_eligible'])

    def test_unverified_build_attempt_does_not_claim_metal_child_execution(self):
        result=self.run_fixture('airconv.compile')
        self.assertIsNone(result['shader_compilation_performed'])
        observation=result['shader_compilation_observation']
        self.assertEqual(observation['status'],'attempted_unverified')
        self.assertEqual(observation['observed_air_outputs'],[])
        self.assertEqual(observation['parent_commands_attempted'][0]['id'],'airconv.compile')
        self.assertIsNone(observation['parent_commands_attempted'][0]['exit_code'])

    def test_later_header_failure_preserves_observed_direct_metal_compilation(self):
        result=self.run_fixture('builtin.header')
        self.assertTrue(result['shader_compilation_performed'])
        self.assertEqual(result['shader_compilation_observation']['status'],'observed')
        self.assertEqual(result['shader_compilation_observation']['observed_air_outputs'][0]['path'],'shaders/dxmt_command.air')
        self.assertFalse(result['passed']);self.assertFalse(result['stage2_complete'])

    def test_subprocess_cleanup_failure_preserves_original_error_and_failed_receipt(self):
        result=self.run_fixture('airconv.compile',subprocess_failure=True)
        self.assertEqual(result['error'],'shader_build_failed')
        self.assertIsNone(result['shader_compilation_performed'])
        self.assertEqual(result['commands'][-1]['id'],'airconv.compile')
        self.assertFalse(result['passed']);self.assertFalse(result['stage2_complete'])

    def test_complete_success_retains_original_true_schema(self):
        result=self.run_fixture()
        self.assertTrue(result['shader_compilation_performed']);self.assertTrue(result['passed']);self.assertTrue(result['stage2_complete'])
        self.assertNotIn('shader_compilation_observation',result)


class NativeConstructorFailureTests(unittest.TestCase):
    def test_llvm_subprocess_cleanup_exception_writes_failed_receipt(self):
        import json
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory(prefix='pear-dxmt-llvm-constructor-') as directory:
            repo=Path(directory).resolve();task=repo/'.build/task7';task.mkdir(parents=True)
            source=task/'source';source.mkdir();(source/'prepared.json').write_bytes(b'Original source receipt fixture')
            tools_root=task/'tools';tools_root.mkdir();(tools_root/'prepared.json').write_bytes(b'Original tool receipt fixture')
            error=build_native.subprocess.TimeoutExpired('original_fixture_failure',1)
            def command(root,ident,argv,env,policy,rows):
                rows.append({'id':ident,'exit_code':None,'stop_reason':'cleanup_error:TimeoutExpired'})
                raise error
            with mock.patch.object(build_native,'verify_source',return_value={}),mock.patch.object(tools,'verify_tools',return_value={}), \
                 mock.patch.object(build_native.shutil,'disk_usage',return_value=SimpleNamespace(free=64*1024**3)), \
                 mock.patch.object(build_native,'native_environment',return_value={}),mock.patch.object(build_native,'producers',return_value={}), \
                 mock.patch.object(build_native,'llvm_recipe',return_value=({'llvm.configure':['/fixture/compiler']},{})), \
                 mock.patch.object(build_native,'monitored_command',side_effect=command):
                with self.assertRaises(build_native.subprocess.TimeoutExpired) as caught:
                    build_native.build_llvm(source,tools_root,'.build/task7/output',2,8*1024**3,4*1024**3,repo)
            self.assertIs(caught.exception,error)
            result=json.loads((task/'output/failed.json').read_text())
            self.assertEqual(result['error'],'native_build_failed');self.assertFalse(result['passed'])
            self.assertFalse(result['shader_compilation_performed']);self.assertFalse(result['gpu_or_guest_execution_performed'])
            self.assertFalse((task/'output/build.json').exists())


class RootedMachOChangeTests(unittest.TestCase):
    def test_change_during_inspection_does_not_produce_hash_info_of_different_bytes(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory(prefix='pear-dxmt-macho-change-') as directory:
            root=Path(directory);exe=root/'airconv';exe.write_bytes(InstalledTableGenTests().macho())
            reader=tools.readers()
            def inspect(path):
                result=reader.inspect_macho(path);exe.write_bytes(exe.read_bytes()+b'changed during pure byte inspection');return result
            with mock.patch.object(tools,'readers',return_value=SimpleNamespace(inspect_macho=inspect)):
                with self.assertRaisesRegex(Error,'native_artifact_changed'):build_native.inspect_rooted_macho(root,exe)


class NativeLogFinalizationTests(unittest.TestCase):
    setUp=NativeMonitorFailureTests.setUp
    tearDown=NativeMonitorFailureTests.tearDown

    def test_completed_process_row_survives_log_hash_failure(self):
        self.process.poll.return_value=0;self.process.wait.return_value=0
        error=PermissionError('original fixture log metadata denied')
        with self.launch,mock.patch.object(build_native,'directory_usage',return_value=0), \
             mock.patch.object(build_native,'sha256',side_effect=error):
            with self.assertRaises(PermissionError) as caught:
                build_native.monitored_command(self.root,'fixture.compile',['/fixture/compiler'],{},self.policy,self.commands)
        self.assertIs(caught.exception,error);self.assertEqual(len(self.commands),1)
        row=self.commands[0]
        self.assertEqual(row['exit_code'],0);self.assertEqual(row['log_collection_error'],'PermissionError')
        self.assertEqual(row['stop_reason'],'log_collection_error:PermissionError')
        self.assertEqual((self.root/'logs/fixture.compile/stdout').read_bytes(),b'partial compiler output')

    def test_log_failure_does_not_replace_original_inventory_failure(self):
        error=Error('native_build_special_output')
        with self.launch,mock.patch.object(build_native,'directory_usage',side_effect=[0,error,0]), \
             mock.patch.object(build_native.os,'killpg'),mock.patch.object(build_native,'sha256',side_effect=PermissionError('secondary fixture log error')):
            with self.assertRaises(Error) as caught:
                build_native.monitored_command(self.root,'fixture.compile',['/fixture/compiler'],{},self.policy,self.commands)
        self.assertIs(caught.exception,error);self.assertEqual(len(self.commands),1)
        self.assertEqual(self.commands[0]['stop_reason'],'inventory_error:native_build_special_output')
        self.assertEqual(self.commands[0]['log_collection_error'],'PermissionError')
        self.assertEqual(self.commands[0]['exit_code'],-9)


if __name__=='__main__':unittest.main()
