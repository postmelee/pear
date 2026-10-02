"""Portable negative controls for exact FEX downstream source and host receipts."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from tools.fex import build
from tools.fex.common import Error


class Stage2SourceTests(unittest.TestCase):
    def test_pinned_patches_apply_to_exact_source_bytes(self):
        prepared=build.REPO/'.build/task5/stage1-inputs3'
        if not prepared.is_dir(): self.skipTest('private pinned source cache unavailable')
        series=build.patch_set()
        rows,changed=build.derive_source(prepared,series)
        self.assertEqual(len(rows),6951)
        self.assertEqual(set(changed),{change['path'] for patch in series['patches'] for change in patch['changes']})
        for patch in series['patches']:
            for change in patch['changes']:
                self.assertEqual(hashlib.sha256(changed[change['path']]).hexdigest(),change['after_sha256'])
        self.assertIn('Source/Windows/UnixLib/FEXUnixLibDarwin.cpp',changed)

    def test_exact_context_and_hunk_counts_reject_corruption(self):
        lines=['--- a/file\n','+++ b/file\n','@@ -1 +1 @@\n','-old\n','+new\n']
        self.assertEqual(build.apply_hunks(b'old\n',lines,'file'),b'new\n')
        with self.assertRaisesRegex(Error,'patch_context_mismatch'):
            build.apply_hunks(b'wrong\n',lines,'file')
        with self.assertRaisesRegex(Error,'patch_hunk_counts'):
            build.apply_hunks(b'old\n',[*lines[:2],'@@ -1,2 +1 @@\n',*lines[3:]],'file')

    def test_path_escape_duplicate_and_missing_headers_rejected(self):
        for raw in (b'diff --git a/../file b/../file\n',b'content before header\n',
                    b'diff --git a/file b/file\ndiff --git a/file b/file\n'):
            with self.assertRaises(Error):build.patch_sections(raw)


class Stage2BuildFailureTests(unittest.TestCase):
    def test_bounded_failure_keeps_original_streams(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            def failure(argv,**kwargs):
                self.assertEqual(kwargs['output_dir'],root/'logs/native.configure')
                (kwargs['output_dir']/'stdout.bin').write_bytes(b'original configure failure')
                (kwargs['output_dir']/'stderr.bin').write_bytes(b'bounded command diagnostic')
                raise Error('command_timeout')
            with mock.patch.object(build,'bounded_command',side_effect=failure):
                with self.assertRaisesRegex(Error,'command_timeout'):
                    build.run_command(root,'native.configure',['qualified-native-tool'],{},[])
            self.assertEqual((root/'logs/native.configure/stdout.bin').read_bytes(),b'original configure failure')
            self.assertEqual((root/'logs/native.configure/stderr.bin').read_bytes(),b'bounded command diagnostic')


class Stage2HostMetadataTests(unittest.TestCase):
    def write_metadata(self,root,cache='128\n'):
        specs={'cache-line':['/usr/bin/arch','-arm64','/usr/sbin/sysctl','-n','hw.cachelinesize'],
               'memory':['/usr/bin/arch','-arm64','/usr/sbin/sysctl','-n','hw.memsize'],
               'os-build':['/usr/bin/arch','-arm64','/usr/bin/sw_vers','-buildVersion']}
        values={'cache-line':cache,'memory':'25769803776\n','os-build':'25F84\n'}
        data={'schema_version':1,'record_kind':'fex_stage2_host_metadata','scope':'fex_component','fex_initialization':False,'guest_execution':False,'commands':[]}
        for ident,argv in specs.items():
            (root/ident).mkdir()
            row={'id':ident,'argv':argv,'returncode':0,'elapsed_ms':1,'status':'completed','logs':{}}
            for stream in ('stdout','stderr'):
                raw=(values[ident] if stream=='stdout' else '').encode();path=root/ident/(stream+'.bin');path.write_bytes(raw)
                row['logs'][stream]={'path':path.relative_to(root).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'size_bytes':len(raw)}
            data['commands'].append(row)
        path=root/'observations.json';path.write_text(json.dumps(data));return path,data

    def test_observed_geometry_binds_logs_without_optional_isa_claims(self):
        with tempfile.TemporaryDirectory() as temp:
            path,_=self.write_metadata(Path(temp));facts=build.host_metadata(path)
            self.assertEqual(facts['cache_line_bytes'],128)
            self.assertEqual(facts['dcache_line_log2'],5)
            self.assertEqual(facts['processor_count_provider'],'PE_GetSystemInfo_unperformed')
            self.assertTrue(facts['software_tso_required'])
            self.assertEqual(facts['hardware_tso'],'unsupported')

    def test_unusable_geometry_or_changed_stream_refused(self):
        for cache in ('0\n','96\n','2048\n'):
            with tempfile.TemporaryDirectory() as temp:
                path,_=self.write_metadata(Path(temp),cache)
                with self.assertRaisesRegex(Error,'host_cache_geometry'):build.host_metadata(path)
        with tempfile.TemporaryDirectory() as temp:
            path,_=self.write_metadata(Path(temp));(Path(temp)/'cache-line/stdout.bin').write_bytes(b'64\n')
            with self.assertRaisesRegex(Error,'host_metadata_log_changed'):build.host_metadata(path)

    def test_wrong_command_and_runtime_promotion_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            path,data=self.write_metadata(Path(temp));data['commands'][0]['argv'][-1]='hw.fake';path.write_text(json.dumps(data))
            with self.assertRaisesRegex(Error,'host_metadata_failed'):build.host_metadata(path)
            data['commands'][0]['argv'][-1]='hw.cachelinesize';data['guest_execution']=True;path.write_text(json.dumps(data))
            with self.assertRaisesRegex(Error,'host_metadata_scope'):build.host_metadata(path)

if __name__=='__main__':unittest.main()
