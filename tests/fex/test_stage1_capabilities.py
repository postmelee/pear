"""Meaningful format, runtime-policy and evidence refusal controls; no guest run."""
import importlib.util
import io
from pathlib import Path
import struct
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.fex import check as capability, tools as build_tools, verify as replay
from tools.fex.common import Error, encoded


def coff_archive(machine=0xaa64):
    body=struct.pack('<H',machine)+bytes(18)
    header=b'object.o/       '+b'0           '+b'0     '+b'0     '+b'644     '+str(len(body)).encode().ljust(10)+b'`\n'
    return b'!<arch>\n'+header+body


def pe(machine=0xaa64):
    value=bytearray(1024);value[:2]=b'MZ';struct.pack_into('<I',value,60,128)
    value[128:132]=b'PE\0\0';struct.pack_into('<HH',value,132,machine,1);struct.pack_into('<H',value,148,240)
    opt=152;struct.pack_into('<H',value,opt,0x20b);struct.pack_into('<Q',value,opt+24,0x180000000)
    table=opt+240;struct.pack_into('<IIII',value,table+8,512,0x1000,512,512)
    return bytes(value)


class FormatContracts(unittest.TestCase):
    def file(self,value):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);p=Path(t.name)/'data';p.write_bytes(value);return p
    def test_static_archive_derives_member_machine(self):
        actual=capability.archive_machines(self.file(coff_archive()))
        self.assertEqual(actual['machines'],{'43620':1});self.assertEqual(actual['coff_members'],1)
    def test_static_archive_refuses_empty_and_unrecognized_objects(self):
        for value in (b'!<arch>\n',coff_archive(99),coff_archive()[:-2]):
            with self.subTest(value=len(value)),self.assertRaises(Error):capability.archive_machines(self.file(value))
    def test_pe_header_is_fact_not_filename_architecture(self):
        self.assertEqual(capability.pe_facts(self.file(pe(0x8664)))['outer_machine'],0x8664)
    def test_pe_refuses_truncated_and_out_of_bounds_sections(self):
        data=bytearray(pe());struct.pack_into('<I',data,152+240+20,9999)
        for value in (b'MZ',bytes(data)):
            with self.subTest(value=len(value)),self.assertRaises(Error):capability.pe_facts(self.file(value))
    def test_arm64ec_requires_positive_metadata_not_amd64_header(self):
        with self.assertRaises(Error):capability.inspect_fixture_arm64ec(self.file(pe(0x8664)))


class ArchiveContracts(unittest.TestCase):
    def archive(self,rows):
        memory=io.BytesIO()
        with tarfile.open(fileobj=memory,mode='w') as a:
            for name,target in rows:
                info=tarfile.TarInfo(name)
                if target is None:
                    info.size=1;a.addfile(info,io.BytesIO(b'x'))
                else:
                    info.type=tarfile.SYMTYPE;info.linkname=target;a.addfile(info)
        memory.seek(0);return tarfile.open(fileobj=memory,mode='r')
    def test_framework_intermediate_directory_alias_is_resolved(self):
        with self.archive([('root/Qt/Versions/A/Qt',None),('root/Qt/Versions/Current','A'),('root/Qt/Qt','Versions/Current/Qt')]) as a:
            members,total=build_tools.archive_graph(a,'root',100)
            self.assertEqual((len(members),total),(3,1))
    def test_parent_write_link_escape_and_cycle_refused(self):
        cases=[ [('root/a','../../escape')], [('root/a','b'),('root/b','a')], [('root/a','b'),('root/b/file',None),('root/a/file',None)] ]
        for rows in cases:
            with self.subTest(rows=rows),self.archive(rows) as a,self.assertRaises(Error):build_tools.archive_graph(a,'root',100)
    def test_duplicate_and_expansion_limit_refused(self):
        for rows,budget in (([('root/a',None),('root/a',None)],100),([('root/a',None)],0)):
            with self.subTest(rows=rows),self.archive(rows) as a,self.assertRaises(Error):build_tools.archive_graph(a,'root',budget)


class EvidenceContracts(unittest.TestCase):
    def refusal(self,**changes):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            data={'schema_version':1,'record_kind':'fex_stage1_capabilities','scope':'fex_component','passed':True,**dict.fromkeys(capability.FALSE_FLAGS,False),**changes}
            (root/'capabilities.json').write_bytes(encoded(data))
            with mock.patch.object(replay,'operation_output',return_value=root),self.assertRaises(Error):replay.verify_stage1(root)
    def test_failed_gate_cannot_be_promoted(self):self.refusal(passed=False)
    def test_compilation_cannot_be_promoted_to_runtime(self):
        for name in capability.FALSE_FLAGS:
            with self.subTest(name=name):self.refusal(**{name:True})
    def test_wrong_component_scope_refused(self):self.refusal(scope='wine_component')

if __name__=='__main__':unittest.main()
