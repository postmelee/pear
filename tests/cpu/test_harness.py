# SPDX-License-Identifier: MIT
"""Synthetic refusal checks; these do not execute or qualify guest instructions."""
import copy
import unittest
import tempfile
import struct
from pathlib import Path

from tools.cpu.results import assess_records, canonical, digest, decode, admit_build
from tools.cpu.generate import reservations, assembly

REPO=Path(__file__).resolve().parents[2]


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.manifest=decode((REPO/'tests/cpu/corpus.json').read_bytes())
        self.hash=digest(canonical(self.manifest))
        ids=[c['id'] for c in self.manifest['cases']]+[c['id'] for c in self.manifest['boundaries'] if c['stage']==2]
        self.build=dict(scope='cpu_pe_build',passed=True,manifest_sha256=self.hash,
                        cases=[dict(id=i,sha256='a'*64) for i in ids])
        rows=[]
        for c in self.manifest['cases']:
            rows.append(dict(id=c['id'],binary_sha256='a'*64,exit_code=42,outcome='exited',events=[
                dict(event='begin',id=c['id'],manifest=self.hash,cpuid_ecx='0x0000000018000000',
                     cpuid_edx='0x0000000004000000',xcr0='0x0000000000000006',avx=True),
                dict(event='result',id=c['id'],values=[e['value'] for e in c['contract']['expectations']],rflags='0x0000000000000202',matched=True)]))
        expected=[0x1020304050607080+i for i in range(8)]
        for i in range(10):expected += [0x1122334455667700+i,0x8877665544332200+i]
        for c in self.manifest['boundaries']:
            if c['stage']==2:
                events=[dict(event='abi_state',values=[f'0x{v:016x}' for v in expected*4])] if c['id']=='abi-state' else []
                rows.append(dict(id=c['id'],binary_sha256='a'*64,exit_code=42,outcome='exited',events=events))
        self.run=dict(scope='cpu_native_results',complete=True,completed_count=len(rows),
                      build_sha256=digest(canonical(self.build)),host=dict(native_machine=0x8664,process_machine=0,pointer_bits=64),cases=rows)

    def assess(self):
        return assess_records(self.manifest,canonical(self.build),self.run,'native')

    def rejected(self,reason):
        with self.assertRaisesRegex(ValueError,reason):self.assess()

    def test_windows_line_endings_do_not_change_contract_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            pe=bytearray(96);pe[:2]=b'MZ';struct.pack_into('<I',pe,60,64);pe[64:70]=b'PE\0\0\x64\x86'
            for row in self.build['cases']:
                row.update(path=row['id']+'.exe',sha256=digest(pe));(root/row['path']).write_bytes(pe)
            raw=canonical(self.manifest).replace(b'\n',b'\r\n')
            self.assertEqual(len(admit_build(self.manifest,raw,self.build,root)),19)
            changed=copy.deepcopy(self.manifest);changed['version']=999
            with self.assertRaisesRegex(ValueError,'build_manifest'):admit_build(changed,canonical(changed),self.build,root)

    def test_complete_declared_results(self):
        self.assertEqual(len(self.assess()),19)
        self.assertTrue(all(r['status']=='passed' for r in self.assess().values()))

    def test_wrong_value_rejected_even_when_driver_claims_pass(self):
        self.run['cases'][0]['events'][1]['values'][0]='0x0000000000000000'
        self.rejected('golden_mismatch')

    def test_missing_final_and_missing_case_rejected(self):
        self.run['complete']=False;self.rejected('incomplete_run')
        self.run['complete']=True;self.run['cases'].pop();self.rejected('missing_case')

    def test_truncated_build_cannot_shorten_comparison(self):
        self.build['cases'].pop()
        self.run['build_sha256']=digest(canonical(self.build))
        self.rejected('build_case_set')

    def test_binary_or_manifest_mix_rejected(self):
        self.run['cases'][0]['binary_sha256']='b'*64;self.rejected('case_binary_or_outcome')
        self.run['cases'][0]['binary_sha256']='a'*64
        self.manifest['cases'][0]['contract']['expectations'][0]['value']='0x0000000000000000'
        self.rejected('build_contract')

    def test_avx_upper_lane_corruption_rejected(self):
        self.run['cases'][11]['events'][1]['values'][2]='0x0000000000000000'
        self.rejected('golden_mismatch')

    def test_feature_absence_is_unavailable_not_pass(self):
        r=self.run['cases'][11];r['exit_code']=77
        r['events'][0].update(cpuid_ecx='0x0000000000000000',xcr0='0x0000000000000000',avx=False)
        r['events'][1]=dict(event='unavailable',reason='AVX_OSXSAVE_XCR0')
        self.assertEqual(self.assess()[r['id']]['status'],'unavailable')
        r['events'][0]['avx']=True;self.rejected('feature_record')

    def test_undefined_flag_bit_is_masked_but_defined_bit_is_not(self):
        r=self.run['cases'][2]['events'][1]
        r['values'][0]='0x0000000000005600';self.assess()
        r['values'][0]='0x0000000000004601';self.rejected('golden_mismatch')

    def test_abi_state_is_independently_checked(self):
        self.run['cases'][-2]['events'][0]['values'][40]='0x0000000000000000'
        self.rejected('abi_state_mismatch')

    def test_crash_and_non_native_reference_rejected(self):
        self.run['cases'][-1]['exit_code']=0xc0000005;self.rejected('boundary_failed')
        self.run['cases'][-1]['exit_code']=42
        self.run['host']['native_machine']=0xaa64;self.rejected('reference_not_native_x64')

    def test_mapping_keeps_absolute_page_with_granular_reservation(self):
        c=next(c for c in self.manifest['cases'] if c['id']=='absolute-displacement')
        reserved,committed=reservations(c)
        self.assertIn([0x7fff0000,0x80000000],reserved)
        self.assertIn(dict(address=0x7ffff000,size=4096),committed)

    def test_bad_capture_input_and_duplicate_results_rejected(self):
        c=self.manifest['cases'][0]
        for body in ('nop','%include "other.asm"\nhlt'):
            with self.assertRaises(Exception):assembly(c,('%ifdef CONFIG\n{}\n%endif\n'+body).encode())
        with self.assertRaisesRegex(ValueError,'duplicate_key'):decode(b'{"complete":false,"complete":true}')


if __name__=='__main__':unittest.main()
