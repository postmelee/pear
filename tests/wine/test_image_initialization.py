# SPDX-License-Identifier: MIT
"""Reject mapping-only, failed attach, missing next phase and foreign candidates."""
from pathlib import Path
import json,tempfile,unittest
from unittest.mock import patch
from tools.wine.image_initialization_check import attachment,next_phase
from tools.wine.image_initialization_graphics import bind
from tools.wine.image_admission_inputs import fact,REPO

class InitializationEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.raw=(b'0024:trace:module:MODULE_InitDLL (0000000306650000 L"GameAssembly.dll",PROCESS_ATTACH,0000000000000000) - CALL\n'
                  b'0024:trace:module:MODULE_InitDLL (0000000306650000,PROCESS_ATTACH,0000000000000000) - RETURN 1\n'
                  b'0024:trace:module:process_attach (L"GameAssembly.dll",0000000000000000) - END\n')
    def test_attach_requires_same_address_thread_success_and_end(self):
        self.assertGreater(attachment(self.raw,0x306650000),0)
        for bad in (self.raw.replace(b'RETURN 1',b'RETURN 0'),self.raw.replace(b'0024:trace:module:MODULE_InitDLL (0000000306650000,',b'0028:trace:module:MODULE_InitDLL (0000000306650000,'),self.raw.split(b' - RETURN')[0],self.raw.split(b'0024:trace:module:process_attach')[0]):
            with self.assertRaises(Exception):attachment(bad,0x306650000)
        with self.assertRaises(Exception):attachment(self.raw,0x306660000)
    def test_mapping_is_not_initialization(self):
        with self.assertRaises(Exception):attachment(b'Loaded GameAssembly.dll at 0000000306650000',0x306650000)
    def test_next_phase_requires_exact_successful_file_and_gc_start(self):
        path=Path('/owned/game/global-metadata.dat')
        raw=(b'0024:trace:file:CreateFileW L"Z:/owned/game/global-metadata.dat" GENERIC_READ FILE_SHARE_READ creation 3\n'
             b'0024:trace:file:CreateFileW returning 0000000000000104\n'
             b'00b4:trace:thread:SetThreadDescription (000000000000010C, L"GC Finalizer")\n')
        self.assertTrue(next_phase(raw,path)['metadata_open_succeeded'])
        for bad in (raw.replace(b'0000000000000104',b'ffffffffffffffff'),raw.replace(b'Z:/owned',b'Z:/foreign'),raw.replace(b'GC Finalizer',b'worker'),raw.replace(b'0024:trace:file:CreateFileW returning',b'0028:trace:file:CreateFileW returning')):
            with self.assertRaises(Exception):next_phase(bad,path)
    def test_old_run_cannot_be_relabelled_as_current_candidate(self):
        with tempfile.TemporaryDirectory(prefix='pear-initialization-binding-') as temp:
            root=Path(temp);run=root/'run';runtime=root/'current';run.mkdir();runtime.mkdir()
            (runtime/'runtime.json').write_text('{}\n')
            (run/'producer.py').write_bytes((REPO/'tools/wine/image_initialization_regression_run.py').read_bytes())
            v={'fixtures':{'device':{'path':'fixture.exe'}}}
            record=dict(runtime_sha256=fact(runtime/'runtime.json')['sha256'],fixture_id='device',launches=[dict(role='loader',argv=['bootstrap','loader',str(runtime/'fixture.exe')])])
            def put(): (run/'case.json').write_text(json.dumps(record))
            with patch('tools.wine.image_initialization_graphics.admit',return_value=v):
                put();bind(run,runtime)
                record['runtime_sha256']='old';put()
                with self.assertRaises(Exception):bind(run,runtime)
                record['runtime_sha256']=fact(runtime/'runtime.json')['sha256'];record['launches'][0]['argv'][-1]=str(root/'old/fixture.exe');put()
                with self.assertRaises(Exception):bind(run,runtime)
if __name__=='__main__':unittest.main()
