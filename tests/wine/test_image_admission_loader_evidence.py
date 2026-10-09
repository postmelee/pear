# SPDX-License-Identifier: MIT
"""Reject incomplete terminal and supervision evidence without native execution."""
import copy,json,unittest
from tools.wine.image_admission_correction_check import terminal,ownership
class LoaderEvidenceTests(unittest.TestCase):
    def setUp(self):
        rows=[json.dumps({'record_kind':'pear_bootstrap_helper'}),'PEAR_LOADER_BEGIN role=arm64']
        for case in (10,20):
            for round in (0,1):
                if case==20:rows.append('PEAR_LOADER_ATTACH_REJECT')
                rows.append(f'PEAR_LOADER_REJECT case={case:016x} round={round:016x} error={193:016x}')
        for case,size,base in ((30,57647104,0x300000000),(40,67108864,0x310000000)):
            for round in (0,1):rows.append(f'PEAR_LOADER_PASS case={case:016x} round={round:016x} base={base:016x} bytes={size:016x}')
        rows.append('PEAR_LOADER_END passed=8');self.raw=('\n'.join(rows)+'\n').encode()
    def test_complete_terminal(self):self.assertEqual(len(terminal(self.raw,'aarch64')['successes']),4)
    def test_missing_work_and_wrong_role(self):
        for line in self.raw.splitlines()[1:]:
            with self.assertRaises(Exception):terminal(self.raw.replace(line+b'\n',b'',1),'aarch64')
        with self.assertRaises(Exception):terminal(self.raw,'x86_64')
    def test_unrelocated_and_unreused_module(self):
        for bad in (self.raw.replace(b'0000000300000000',b'0000000180000000'),self.raw.replace(b'0000000300000000',b'0000000320000000',1)):
            with self.assertRaises(Exception):terminal(bad,'aarch64')
    def test_incomplete_cleanup_or_integrity(self):
        clean=dict(complete=True,errors=[],observation_gap=False,reaped={'loader':True})
        row=dict(outcome='exited',processes={'loader':{'exit_code':42},'sentinel':{'exit_code':0}},error=None,stream_error=None,cleanup_errors=[],cleanup=clean,sentinel_cleanup=copy.deepcopy(clean),sentinel_survived=True,authorization_before_after_passed=True,fixtures_unchanged=True,runtime_unchanged=True)
        ownership(row)
        for key in ('sentinel_survived','authorization_before_after_passed','fixtures_unchanged','runtime_unchanged'):
            bad=copy.deepcopy(row);bad[key]=False
            with self.assertRaises(Exception):ownership(bad)
        bad=copy.deepcopy(row);bad['cleanup']['reaped']['loader']=False
        with self.assertRaises(Exception):ownership(bad)
if __name__=='__main__':unittest.main()
