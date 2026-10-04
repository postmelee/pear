"""Portable diagnostics review/refusal controls; no native admission or execution.

The successful case uses scalar protocol fixtures and an explicit prerequisite
replay double. It does not qualify an actual Wine, GPU, profile or game runtime.
"""
import copy
import importlib.util
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

REPO=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO/'tools/dxmt'))
spec=importlib.util.spec_from_file_location('_pear_dxmt_pair_evidence_tests',REPO/'tools/dxmt/pairing_evidence.py')
evidence=importlib.util.module_from_spec(spec);spec.loader.exec_module(evidence)
from common import Error,digest,encoded
protocol_spec=importlib.util.spec_from_file_location('_pear_dxmt_metadata_wire_reuse',REPO/'tests/dxmt/test_run_pairing.py')
protocol=importlib.util.module_from_spec(protocol_spec);protocol_spec.loader.exec_module(protocol)


class EvidenceControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='pear-pair-review-pure-')
        self.addCleanup(self.temp.cleanup)
        self.repo=Path(self.temp.name).resolve()/'repo';self.repo.mkdir()
        self.root=self.repo/'.build/task7/run';self.root.mkdir(parents=True)
        self.runtime_root=self.repo/'.build/task7/runtime';self.runtime_root.mkdir()
        self.runner,self.runtime,self.raw_run,_=evidence.adapters(REPO)
        names=set(self.runner.producers(REPO))|set(self.runtime.producers(REPO))|{'tools/dxmt/pairing_evidence.py'}
        for path in names:self.put(path,(REPO/path).read_bytes(),self.repo)
        self.put('runtime.json',encoded({'synthetic':'non-executable metadata'}),self.runtime_root)
        self.diagnostics=b'Metal API Validation Enabled\nShader Validation Enabled\nordinary native diagnostic\n'
        self.raw_logs={(role,channel):b''for role in ['loader','server','sentinel']for channel in ['stdout','stderr']}
        self.raw_logs[('loader','stderr')]=protocol.wire(protocol.protocol_rows())+self.diagnostics
        self.raw_logs[('loader','events')]=b'';self.raw_logs[('server','events')]=b''
        self.case={'events':{'loader':[],'server':[]},'logs':[],
            'processes':{role:{'identity':{'pid':pid}}for role,pid in [('loader',102),('server',101),('sentinel',100)]},
            'registrations':[{'identity':{'pid':102}},{'identity':{'pid':103}}]}
        self.refresh_logs()
        self.observed={'native_pairing_observed':True,'diagnostics':{'sha256':digest(self.diagnostics),
            'size_bytes':len(self.diagnostics),'review':'unperformed','scope':'captured_nonfixture_loader_stderr'}}
        self.run={'schema_version':1,'record_kind':'dxmt_pairing_run','scope':'finite_native_metal_pairing',
            'runtime_ref':{'path':str(self.runtime_root),'sha256':digest((self.runtime_root/'runtime.json').read_bytes())},
            'producers':self.runner.producers(self.repo),'bounds':self.runner.BOUNDS,'timeout_ms':self.runner.TIMEOUT_MS,
            'metal_environment':self.runner.METAL_ENV,'case_ref':{},'assessment_ref':{},
            'native_pairing_observed':True,'ordinary_arm64_pe_execution_performed':True,
            'diagnostics_review':'unperformed','passed':True,
            **{key:False for key in ['hybrid_execution_performed','translated_guest_execution_performed',
                'game_qualified','runtime_eligible','distribution_qualified']}}
        self.refresh_receipts()
        self.replay=mock.patch.object(evidence,'pure_replay',side_effect=lambda *args:(copy.deepcopy(self.observed),{}))
        self.replay.start();self.addCleanup(self.replay.stop)
        self.review=self.make_review()

    def put(self,path,raw,root=None,mode=0o644):
        target=(root or self.root)/path;target.parent.mkdir(parents=True,exist_ok=True)
        # Only disposable synthetic controls are replaced between test cases.
        if target.exists()and not target.is_symlink():target.chmod(0o644)
        target.write_bytes(raw);target.chmod(mode);return target

    def refresh_logs(self):
        self.case['logs']=[]
        for (role,channel),raw in sorted(self.raw_logs.items()):
            path=role+'.'+channel+'.log';self.put(path,raw)
            self.case['logs'].append({'role':role,'channel':channel,'path':path,'sha256':digest(raw),
                'bytes':len(raw),'observed_bytes':len(raw),'eof':True,'write_error':None})
        self.put('case.json',encoded(self.case))

    def refresh_receipts(self):
        self.put('assessment.json',encoded({'passed':True,'error':None,'observations':self.observed}))
        self.run['case_ref']={'path':'case.json','sha256':digest((self.root/'case.json').read_bytes())}
        self.run['assessment_ref']={'path':'assessment.json','sha256':digest((self.root/'assessment.json').read_bytes())}
        self.put('run.json',encoded(self.run))

    def make_review(self):
        context,_=evidence.review_context(self.root,repo=self.repo)
        bindings={key:context[key]for key in ['run_ref','case_ref','assessment_ref','runtime_ref','producers',
            'logs','diagnostics','metal_environment']}
        findings=[]
        for item in context['finding_inputs']:
            raw=self.raw_logs[(item['role'],item['channel'])][item['byte_offset']:item['byte_offset']+item['byte_count']]
            kind='validation_enabled_notice'if b'Validation Enabled'in raw else'nonvalidation_native_diagnostic'
            findings.append({**item,'classification':kind})
        return {'schema_version':1,'record_kind':'dxmt_pairing_diagnostics_review','scope':evidence.SCOPE,
            'review':'performed','review_actor':'root_orchestrator','reviewed_at_utc':'2026-10-03T01:00:00Z',
            **bindings,'assessment':{'method':'explicit_raw_log_review','coverage':'all_captured_stderr_nonfixture_lines',
                'validation_errors_observed':False,'findings':findings,
                **{key:'unperformed'for key in evidence.UNPERFORMED}}}

    def write_review(self,value=None,mode=0o444):return self.put(evidence.REVIEW,encoded(value or self.review),mode=mode)

    def test_explicit_exact_review_closes_only_finite_native_scope_without_changing_run(self):
        before=(self.root/'run.json').read_bytes();self.write_review()
        observed=evidence.verify_native_evidence(self.root,repo=self.repo)
        self.assertIs(observed['finite_native_scope_complete'],True)
        self.assertEqual(observed['diagnostics_review'],'performed')
        self.assertEqual(observed['shader_workload'],'unperformed')
        self.assertIs(observed['runtime_eligible'],False)
        self.assertIs(observed['game_qualified'],False)
        self.assertEqual((self.root/'run.json').read_bytes(),before)
        self.assertEqual(len(self.review['logs']),8)
        self.assertEqual(len(self.review['assessment']['findings']),3)

    def test_missing_review_never_infers_success_even_from_empty_diagnostics(self):
        self.raw_logs[('loader','stderr')]=protocol.wire(protocol.protocol_rows());self.diagnostics=b''
        self.observed['diagnostics'].update(sha256=digest(b''),size_bytes=0)
        self.refresh_logs();self.refresh_receipts()
        with self.assertRaises((Error,OSError)):evidence.verify_native_evidence(self.root,repo=self.repo)
        self.assertFalse((self.root/evidence.REVIEW).exists())

    def test_review_requires_immutable_owned_leaf_and_no_alias(self):
        for changed in ['mode','leaf','parent']:
            with self.subTest(changed=changed):
                path=self.write_review(mode=0o644 if changed=='mode'else 0o444)
                if changed=='leaf':
                    path.rename(self.root/'other-review');path.symlink_to('other-review')
                if changed=='parent':
                    # The owned root rule rejects aliased roots before parsing.
                    alias=self.repo/'.build/task7/aliased-run';alias.symlink_to('run',target_is_directory=True)
                with self.assertRaises((Error,OSError)):
                    evidence.verify_native_evidence(alias if changed=='parent'else self.root,repo=self.repo)
                if path.is_symlink():path.unlink()

    def test_every_stream_byte_and_reference_is_bound_including_events(self):
        self.write_review()
        for path in ['loader.stderr.log','server.events.log','sentinel.stdout.log','run.json','case.json','assessment.json']:
            target=self.root/path;raw=target.read_bytes();target.write_bytes(raw+b'changed')
            with self.subTest(path=path):
                with self.assertRaises((Error,ValueError)):evidence.verify_native_evidence(self.root,repo=self.repo)
            target.write_bytes(raw)
        target=self.runtime_root/'runtime.json';raw=target.read_bytes();target.write_bytes(raw+b'changed')
        with self.assertRaises(Error):evidence.verify_native_evidence(self.root,repo=self.repo)
        target.write_bytes(raw)

    def test_rehashed_wrong_assessment_cannot_replace_independent_observations(self):
        assessment={'passed':True,'error':None,'observations':{**self.observed,'native_pairing_observed':False}}
        self.put('assessment.json',encoded(assessment))
        self.run['assessment_ref']['sha256']=digest((self.root/'assessment.json').read_bytes());self.put('run.json',encoded(self.run))
        value=copy.deepcopy(self.review);value['run_ref']['sha256']=digest((self.root/'run.json').read_bytes())
        value['assessment_ref']=copy.deepcopy(self.run['assessment_ref']);self.write_review(value)
        with self.assertRaisesRegex(Error,'pair_evidence_assessment_changed'):
            evidence.verify_native_evidence(self.root,repo=self.repo)

    def test_producer_environment_or_scope_changes_cannot_be_reviewed_as_complete(self):
        for key,value in [('producers',{}),('metal_environment',{}),('scope','general_renderer'),
                          ('review','unperformed'),('review_actor','automatic_empty_log'),('schema_version',True)]:
            changed=copy.deepcopy(self.review);changed[key]=value;self.write_review(changed)
            with self.subTest(key=key):
                with self.assertRaises(Error):evidence.verify_native_evidence(self.root,repo=self.repo)
        source=self.repo/'tools/dxmt/pairing_runtime.py';before=source.read_bytes();source.write_bytes(before+b'\n')
        self.write_review()
        with self.assertRaises(Error):evidence.verify_native_evidence(self.root,repo=self.repo)

    def test_findings_need_exact_complete_ordered_byte_coverage_and_closed_classification(self):
        changes=[lambda rows:rows.pop(),lambda rows:rows.append(rows[0]),lambda rows:rows.reverse(),
            lambda rows:rows[0].update(byte_offset=True),lambda rows:rows[0].update(byte_count=1),
            lambda rows:rows[0].update(sha256='0'*64),lambda rows:rows[0].update(classification='accepted_unknown'),
            lambda rows:rows[0].update(classification='nonvalidation_native_diagnostic')]
        for change in changes:
            value=copy.deepcopy(self.review);change(value['assessment']['findings']);self.write_review(value)
            with self.assertRaises(Error):evidence.verify_native_evidence(self.root,repo=self.repo)

    def test_no_validation_error_unknown_validation_or_shader_warning_can_be_relabelled_benign(self):
        for line in [b'Metal API Validation error: invalid texture\n',b'failed assertion in validateLayer\n',
                     b'MTLDebugDevice: unknown validation result\n',b'Shader Validation warning: invalid access\n',
                     b'unknown native diagnostic \xff\n']:
            self.diagnostics=line;self.raw_logs[('loader','stderr')]=protocol.wire(protocol.protocol_rows())+line
            self.observed['diagnostics'].update(sha256=digest(line),size_bytes=len(line))
            self.refresh_logs();self.refresh_receipts();self.review=self.make_review();self.write_review()
            with self.subTest(line=line):
                with self.assertRaises(Error):evidence.verify_native_evidence(self.root,repo=self.repo)

    def replace_diagnostics(self,line):
        self.diagnostics=line;self.raw_logs[('loader','stderr')]=protocol.wire(protocol.protocol_rows())+line
        self.observed['diagnostics'].update(sha256=digest(line),size_bytes=len(line))
        self.refresh_logs();self.refresh_receipts();self.review=self.make_review();self.write_review()

    def test_exact_nslog_enabled_notices_bind_owned_loader_or_descendant_pid(self):
        for pid in [102,103]:
            for body in evidence.ENABLED_NOTICES:
                line=('2026-10-03 04:12:50.836 wine['+str(pid)+':3878251] '+body+'\n').encode()
                with self.subTest(pid=pid,body=body):
                    self.replace_diagnostics(line)
                    self.assertIs(evidence.verify_native_evidence(self.root,repo=self.repo)['finite_native_scope_complete'],True)
                    self.assertEqual(evidence.verify_native_evidence(self.root,repo=self.repo)['shader_workload'],'unperformed')
        self.replace_diagnostics(b'Metal GPU Validation Enabled\n')
        self.assertIs(evidence.verify_native_evidence(self.root,repo=self.repo)['finite_native_scope_complete'],True)

    def test_nslog_notice_rejects_unknown_pid_bad_calendar_prefix_and_validation_suffix(self):
        lines=[
            b'2026-10-03 04:12:50.836 wine[999:3878251] Metal API Validation Enabled\n',
            b'2026-10-03 04:12:50.836 wine[101:3878251] Metal API Validation Enabled\n',
            b'2026-99-03 04:12:50.836 wine[102:3878251] Metal API Validation Enabled\n',
            b'2026-10-03 04:12:50.836 other[102:3878251] Metal API Validation Enabled\n',
            b'2026-10-03 04:12:50.836 wine[0102:3878251] Metal API Validation Enabled\n',
            b'2026-10-03 04:12:50.836 wine[102:0] Metal API Validation Enabled\n',
            b'2026-10-03 04:12:50.836 wine[102:18446744073709551616] Metal GPU Validation Enabled\n',
            b'2026-10-03 04:12:50.836 wine[102:3878251] Metal GPU Validation Enabled assertion failed\n',
            b'2026-10-03 04:12:50.836 wine[102:3878251] Metal GPU Validation Enabled extra\n',
            b'2026-10-03 04:12:50.836 wine[102:3878251] Metal GPU Validation unknown\n',
        ]
        for line in lines:
            with self.subTest(line=line):
                self.replace_diagnostics(line)
                for row in self.review['assessment']['findings']:row['classification']='validation_enabled_notice'
                self.write_review()
                with self.assertRaises(Error):evidence.verify_native_evidence(self.root,repo=self.repo)
        self.replace_diagnostics(b'Metal GPU Validation Enabled\n')
        self.review['assessment']['findings'][0]['classification']='nonvalidation_native_diagnostic';self.write_review()
        with self.assertRaisesRegex(Error,'pair_review_unclassified_validation'):
            evidence.verify_native_evidence(self.root,repo=self.repo)

    def test_explicit_nonblocking_api_warning_requires_warning_classification(self):
        self.diagnostics=b'Metal API Validation warning: selected finite notice\n'
        self.raw_logs[('loader','stderr')]=protocol.wire(protocol.protocol_rows())+self.diagnostics
        self.observed['diagnostics'].update(sha256=digest(self.diagnostics),size_bytes=len(self.diagnostics))
        self.refresh_logs();self.refresh_receipts();value=self.make_review();self.write_review(value)
        with self.assertRaises(Error):evidence.verify_native_evidence(self.root,repo=self.repo)
        value['assessment']['findings'][0]['classification']='metal_api_warning';self.write_review(value)
        self.assertIs(evidence.verify_native_evidence(self.root,repo=self.repo)['finite_native_scope_complete'],True)

    def test_review_cannot_expand_shader_renderer_performance_or_game_scope(self):
        for key in evidence.UNPERFORMED:
            value=copy.deepcopy(self.review);value['assessment'][key]='performed';self.write_review(value)
            with self.subTest(key=key):
                with self.assertRaises(Error):evidence.verify_native_evidence(self.root,repo=self.repo)
        value=copy.deepcopy(self.review);value['assessment']['validation_errors_observed']=True;self.write_review(value)
        with self.assertRaises(Error):evidence.verify_native_evidence(self.root,repo=self.repo)
        value=copy.deepcopy(self.review);value['assessment']['validation_errors_observed']=0;self.write_review(value)
        with self.assertRaises(Error):evidence.verify_native_evidence(self.root,repo=self.repo)

    def test_ast_replay_uses_only_structural_runtime_adapter_and_preserves_scope_checks(self):
        self.replay.stop()
        def forbidden(*args,**kwargs):raise AssertionError('live admission called from pure gate')
        runner=SimpleNamespace(runtime_values=forbidden)
        value={'code_publication_policy':'page-wx','runtime_eligible':False,'game_qualified':False}
        runtime=SimpleNamespace(verify_runtime=forbidden,verify_structural=mock.Mock(return_value=(value,{},b'')))
        raw=b'def verify_run(root, repo=None):\n    return runtime_values(root, repo=repo)\n'
        observed,captured=evidence.pure_replay(self.root,self.repo,runner,runtime,raw)
        self.assertEqual(observed,value);self.assertEqual(captured,value)
        runtime.verify_structural.assert_called_once_with(self.root,repo=self.repo)
        value['runtime_eligible']=True
        with self.assertRaisesRegex(Error,'pair_runtime_scope'):
            evidence.pure_replay(self.root,self.repo,runner,runtime,raw)
        for raw in [b'def another(root): pass\n',b'@decorator\ndef verify_run(root):pass\n']:
            with self.assertRaises(Error):evidence.pure_replay(self.root,self.repo,runner,runtime,raw)

    def test_malformed_review_extra_fields_or_wrong_timestamp_refuse(self):
        for key,value in [('extra','unexpected'),('reviewed_at_utc','2026-99-03T01:00:00Z'),
                          ('reviewed_at_utc','2026-10-03'),('diagnostics',{})]:
            changed=copy.deepcopy(self.review);changed[key]=value;self.write_review(changed)
            with self.subTest(key=key):
                with self.assertRaises(Error):evidence.verify_native_evidence(self.root,repo=self.repo)
        self.put(evidence.REVIEW,b'{"schema_version":1,',mode=0o444)
        with self.assertRaises(Error):evidence.verify_native_evidence(self.root,repo=self.repo)


if __name__=='__main__':unittest.main()
