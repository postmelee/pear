# SPDX-License-Identifier: MIT
"""Refuse missing, misattributed and incompletely supervised diagnostic evidence."""
import copy, unittest
from tools.wine.image_admission_check import refusal,ownership

class ImageAdmissionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.target=dict(dev=3,ino=44,bytes=55)
        self.raw=b'\n'.join(b'PEAR_IMAGE_ADMISSION pid=20 fd=7 dev=3 ino=44 bytes=55 phase='+p+b' status='+s for p,s in
            [(b'caller.begin',b'00000000'),(b'parser.begin',b'00000000'),(b'parser.return08',b'c00000bb'),(b'caller.parsed',b'c00000bb')])
    def test_attributed_refusal(self):
        self.assertEqual(refusal(self.raw,self.target,20)['first_refusal'],'parser.return08')
    def test_wrong_file_and_process(self):
        for field in ('dev','ino','bytes'):
            t=dict(self.target);t[field]+=1
            with self.assertRaises(Exception):refusal(self.raw,t,20)
        with self.assertRaises(Exception):refusal(self.raw,self.target,21)
    def test_missing_boundaries(self):
        for marker in (b'caller.begin',b'parser.begin',b'caller.parsed'):
            with self.assertRaises(Exception):refusal(b'\n'.join(r for r in self.raw.splitlines() if marker not in r),self.target,20)
    def test_success_is_not_refusal(self):
        with self.assertRaises(Exception):refusal(self.raw.replace(b'c00000bb',b'00000000'),self.target,20)
    def test_split_attempt_not_combined(self):
        raw=self.raw.replace(b'phase=parser.return08',b'phase=caller.begin')
        with self.assertRaises(Exception):refusal(raw,self.target,20)
    def test_cleanup_and_integrity(self):
        clean=dict(complete=True,errors=[],observation_gap=False,reaped={'loader':True})
        r=dict(outcome='image_refused',error=None,stream_error=None,cleanup_errors=[],cleanup=clean,sentinel_cleanup=copy.deepcopy(clean),sentinel_survived=True,processes={'sentinel':{'exit_code':0}},authorization_before_after_passed=True,original_files_unchanged=True,runtime_unchanged=True)
        ownership(r)
        for key in ('sentinel_survived','authorization_before_after_passed','original_files_unchanged','runtime_unchanged'):
            bad=copy.deepcopy(r);bad[key]=False
            with self.assertRaises(Exception):ownership(bad)
        bad=copy.deepcopy(r);bad['cleanup']['reaped']['loader']=False
        with self.assertRaises(Exception):ownership(bad)

if __name__=='__main__':unittest.main()
