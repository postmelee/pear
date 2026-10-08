# SPDX-License-Identifier: MIT
"""Reject incomplete/foreign host evidence before accepting guest output."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from tools.cpu.compare import observe_pear
from tools.cpu.results import digest

REPO=Path(__file__).resolve().parents[2]


class ExecutionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.runtime=self.root/'runtime';self.runtime.mkdir()
        self.run=self.root/'run';self.run.mkdir()
        (self.runtime/'runtime.json').write_text('{}\n')
        self.hash=digest((self.runtime/'runtime.json').read_bytes())
        (self.runtime/'case.exe').write_bytes(b'fixture')
        self.fixture=dict(id='case',sha256=digest(b'fixture'))
        self.value=dict(fixtures={'case':dict(path='case.exe',sha256=self.fixture['sha256'])})
        self.record=dict(kind='cpu_corpus_observation',runtime_sha256=self.hash,fixture_id='case',fixture_sha256=self.fixture['sha256'],
            outcome='exited',error=None,stream_error=None,cleanup_errors=[],cleanup=dict(complete=True),
            sentinel_survived=True,authorization_before_after_passed=True,
            events=dict(loader=[dict(translation_value=0,translation_error=0,cpu_type=16777228),dict(event='image',cpu_type=16777228)]),
            processes=dict(loader=dict(exit_code=42,identity=dict(pid=100,ppid=90,start_sec=123,start_usec=4))),launches=[dict(role='loader',argv=['owner','--exec-4k','wine',str(self.runtime/'case.exe')])])
        (self.run/'producer.py').write_bytes((REPO/'tools/cpu/pear_run.py').read_bytes())
        for side in ['before','after']:
            (self.run/side).mkdir();(self.run/side/'control.json').write_text(json.dumps(dict(passed=True,runtime_sha256=self.hash)))
        (self.run/'run').mkdir()
        helper=dict(version=1,record_kind='pear_bootstrap_helper',cpu_type=16777228,translation_value=0,query_errno=0,pid=100,ppid=90,start_sec=123,start_usec=4)
        raw=(json.dumps(helper)+'\n').encode();(self.run/'run/loader.stdout.log').write_bytes(raw)
        self.record['logs']=[dict(role='loader',channel='stdout',sha256=digest(raw),bytes=len(raw),eof=True,write_error=None)]

    def observe(self):
        (self.run/'case.json').write_text(json.dumps(self.record))
        return observe_pear(self.run,self.runtime,self.value,self.fixture)

    def test_admits_only_complete_observation_shape(self):
        row,evidence=self.observe()
        self.assertEqual(row['exit_code'],42)
        self.assertFalse(evidence['late_load_coverage_complete'])

    def test_cleanup_and_sentinel_failures_cannot_pass(self):
        self.record['cleanup']['complete']=False
        with self.assertRaisesRegex(ValueError,'execution_boundary'):self.observe()
        self.record['cleanup']['complete']=True;self.record['sentinel_survived']=False
        with self.assertRaisesRegex(ValueError,'execution_boundary'):self.observe()

    def test_rosetta_or_foreign_image_cannot_pass(self):
        self.record['events']['loader'][0]['translation_value']=1
        with self.assertRaisesRegex(ValueError,'translated_host_process'):self.observe()
        self.record['events']['loader'][0]['translation_value']=0
        self.record['events']['loader'][1]['cpu_type']=16777223
        with self.assertRaisesRegex(ValueError,'non_arm64_image'):self.observe()

    def test_other_binary_cannot_stand_in_for_requested_case(self):
        self.record['launches'][0]['argv'][-1]='other.exe'
        with self.assertRaisesRegex(ValueError,'different_fixture_launched'):self.observe()


if __name__=='__main__':unittest.main()
