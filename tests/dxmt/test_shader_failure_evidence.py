"""Original portable shader-bound evidence controls; all launches are mocked."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/dxmt'))
import common
import check
import tools
from common import Error, digest, sha256


class BoundedFailureFactsTests(unittest.TestCase):
    def exercise(self,cause):
        process=mock.Mock(pid=34567)
        process.wait.return_value=-9;process.poll.return_value=-9
        process.stdout.fileno.return_value=101;process.stderr.fileno.return_value=102
        selector=mock.Mock();selector.get_map.return_value=True
        key=SimpleNamespace(fileobj=process.stdout,data='stdout')
        selector.select.return_value=[(key,1)]
        times=[0,2_000_000_000,3_000_000_000] if cause=='timeout' else [0,0,2_000_000_000]
        with tempfile.TemporaryDirectory(prefix='pear-dxmt-bound-facts-') as directory:
            root=Path(directory)
            with mock.patch.object(common.subprocess,'Popen',return_value=process) as launch, \
                 mock.patch.object(common.selectors,'DefaultSelector',return_value=selector), \
                 mock.patch.object(common.os,'set_blocking'),mock.patch.object(common.os,'read',return_value=b'original bound output'), \
                 mock.patch.object(common.os,'killpg') as kill,mock.patch.object(common.time,'monotonic_ns',side_effect=times):
                with self.assertRaises(Error) as caught:
                    common.run_bounded(['fixture-command'],timeout=1,limit=16,log_directory=root)
            self.assertEqual(caught.exception.code,'command_bound')
            fact=caught.exception.bound_outcome
            self.assertEqual(fact['timed_out'],cause=='timeout')
            self.assertEqual(fact['output_limit'],cause=='output_limit')
            self.assertEqual(set(fact),{'timed_out','output_limit','elapsed_ms'})
            self.assertIsInstance(fact['elapsed_ms'],int)
            self.assertNotIn('exit_code',fact)
            self.assertEqual((root/'stderr').read_bytes(),b'')
            self.assertEqual((root/'stdout').read_bytes(),b'' if cause=='timeout' else b'original bound output')
            launch.assert_called_once();self.assertTrue(launch.call_args.kwargs['start_new_session'])
            kill.assert_called_once_with(34567,common.signal.SIGKILL)

    def test_observed_timeout_exposed_without_invented_exit(self):self.exercise('timeout')
    def test_observed_output_bound_exposed_without_invented_exit(self):self.exercise('output_limit')


def bounded_failure(cause):
    def execute(argv,**kwargs):
        directory=kwargs['log_directory']
        (directory/'stdout').write_bytes(b'original partial compiler stream')
        (directory/'stderr').write_bytes(b'original bounded diagnostic')
        error=Error('command_bound')
        error.bound_outcome={'timed_out':cause=='timeout','output_limit':cause=='output_limit','elapsed_ms':1235}
        raise error
    return execute


class ShaderFailureRowTests(unittest.TestCase):
    def test_successful_command_schema_remains_unchanged(self):
        with tempfile.TemporaryDirectory(prefix='pear-dxmt-shader-success-') as directory:
            root=Path(directory);rows=[];argv=['/fixture/metal','--version'];env={'SDKROOT':'/fixture/sdk'}
            def completed(argv,**kwargs):
                for name,data in [('stdout',b'fixture version'),('stderr',b'')]:
                    (kwargs['log_directory']/name).write_bytes(data)
                return {'argv':argv,'exit_code':0,'timed_out':False,'output_limit':False,'elapsed_ms':7,
                        'stdout':b'fixture version','stderr':b''}
            with mock.patch.object(check,'run_bounded',side_effect=completed):
                check.shader_command(root,'metal.version',argv,env,rows)
            self.assertEqual(set(rows[0]),{'id','argv','cwd','environment','exit_code','timed_out','output_limit','elapsed_ms','logs'})
            self.assertEqual(rows[0]['exit_code'],0)

    def test_bound_rows_preserve_attempt_cause_raw_bytes_and_unknown_exit(self):
        for cause in ['timeout','output_limit']:
            with self.subTest(cause=cause),tempfile.TemporaryDirectory(prefix='pear-dxmt-shader-bound-') as directory:
                root=Path(directory);rows=[];argv=['/usr/bin/arch','-arm64','/fixture/metal','--version'];env={'SDKROOT':'/fixture/sdk'}
                with mock.patch.object(check,'run_bounded',side_effect=bounded_failure(cause)):
                    with self.assertRaisesRegex(Error,'command_bound'):check.shader_command(root,'metal.version',argv,env,rows)
                self.assertEqual(len(rows),1);row=rows[0]
                self.assertEqual(row['argv'],argv);self.assertEqual(row['environment'],env);self.assertEqual(row['cwd'],str(root))
                self.assertIsNone(row['exit_code']);self.assertEqual(row['status'],'failed');self.assertEqual(row['error'],'command_bound')
                self.assertEqual(row['timed_out'],cause=='timeout');self.assertEqual(row['output_limit'],cause=='output_limit')
                self.assertEqual(row['elapsed_ms'],1235)
                self.assertEqual(set(row['logs']),{'stdout','stderr'})
                for ref in row['logs'].values():
                    self.assertEqual(sha256(root/ref['path']),ref['sha256'])
                    self.assertEqual((root/ref['path']).stat().st_size,ref['size_bytes'])

    def test_unobserved_operational_outcome_stays_unknown(self):
        with tempfile.TemporaryDirectory(prefix='pear-dxmt-shader-launch-') as directory:
            root=Path(directory);rows=[]
            with mock.patch.object(check,'run_bounded',side_effect=OSError('original fixture launch failure')):
                with self.assertRaisesRegex(OSError,'original fixture launch failure'):
                    check.shader_command(root,'metal.version',['/fixture/metal','--version'],{},rows)
            self.assertIsNone(rows[0]['exit_code']);self.assertIsNone(rows[0]['timed_out']);self.assertIsNone(rows[0]['output_limit'])
            self.assertEqual(rows[0]['logs'],{});self.assertEqual(rows[0]['error'],'OSError')


class ShaderProducerFailureTests(unittest.TestCase):
    def failure_receipt(self,cause):
        with tempfile.TemporaryDirectory(prefix='pear-dxmt-shader-producer-') as directory:
            repo=Path(directory).resolve();tool_root=repo/'.build/task7/tools';tool_root.mkdir(parents=True)
            (tool_root/'prepared.json').write_bytes(b'original fixture tools')
            toolchain='runtime/dxmt/toolchain.json';lock=repo/toolchain;lock.parent.mkdir(parents=True);lock.write_bytes(b'{}')
            for name in ['tools/dxmt/check.py','tools/dxmt/common.py','tools/dxmt/tools.py','tools/wine/common.py','tools/wine/toolchain.py']:
                path=repo/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'original producer fixture')
            record={'toolchain_ref':{'path':toolchain,'sha256':sha256(lock)},'sdk':{'path':'/fixture/sdk'}}
            selected=lambda path:{'path':str(path),'sha256':digest(str(path).encode())}
            with mock.patch.object(check,'validate_toolchain',return_value={}), \
                 mock.patch.object(tools,'verify_tools',return_value=record),mock.patch.object(tools,'native_file',side_effect=selected), \
                 mock.patch.object(check,'run_bounded',side_effect=bounded_failure(cause)):
                with self.assertRaisesRegex(Error,'command_bound'):
                    check.shader_capabilities(toolchain,tool_root,'.build/task7/shader',metal='/fixture/metal',metallib='/fixture/metallib',repo=repo)
            output=repo/'.build/task7/shader';failure=json.loads((output/'failure.json').read_text())
            self.assertFalse((output/'capabilities.json').exists())
            self.assertEqual(failure['record_kind'],'dxmt_shader_capability_failure')
            self.assertEqual(failure['error'],'command_bound');self.assertFalse(failure['shader_build_ready'])
            self.assertFalse(failure['gpu_or_guest_execution_performed']);self.assertFalse(failure['runtime_eligible'])
            self.assertEqual(failure['output_qualification'],'incomplete')
            self.assertEqual(len(failure['commands']),1);row=failure['commands'][0]
            self.assertEqual(row['id'],'metal.version')
            self.assertEqual(row['argv'],['/usr/bin/arch','-arm64','/fixture/metal','--version'])
            self.assertEqual(row['environment'],failure['environment']);self.assertIsNone(row['exit_code'])
            self.assertEqual(row['timed_out'],cause=='timeout');self.assertEqual(row['output_limit'],cause=='output_limit')
            self.assertEqual(set(row['logs']),{'stdout','stderr'})
            for ref in row['logs'].values():
                self.assertEqual(sha256(output/ref['path']),ref['sha256'])

    def test_timeout_writes_closed_failed_receipt(self):self.failure_receipt('timeout')
    def test_output_bound_writes_closed_failed_receipt(self):self.failure_receipt('output_limit')
    def test_failure_marker_blocks_capability_replay_before_native_tool_checks(self):
        with tempfile.TemporaryDirectory(prefix='pear-dxmt-shader-failed-replay-') as directory:
            repo=Path(directory).resolve();root=repo/'.build/task7/shader';root.mkdir(parents=True)
            (root/'failure.json').write_bytes(b'original failure marker')
            with mock.patch.object(tools,'verify_tools',side_effect=AssertionError('must not reach native tool qualification')):
                with self.assertRaisesRegex(Error,'failed_shader_capability_probe'):check.verify_shader_capabilities(root,repo)


if __name__=='__main__':unittest.main()
