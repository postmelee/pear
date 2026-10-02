"""Pure-EC metadata controls; structural fixtures never prove linked code."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_stage1_ec_archive import member
from tools.fex.check import archive_machines
from tools.fex.common import Error


def pure_ec(index=1,ec_count=1,ordinary_tail=b'',first=bytes(4),with_object=True):
    first_member=member('/',first)
    ec=member('/<ECSYMBOLS>/',struct.pack('<I',ec_count)+(struct.pack('<H',index)+b'owned-symbol\0' if ec_count else b''))
    dummy=member('/',struct.pack('<III',1,0,0)+ordinary_tail)
    offset=8+len(first_member)+len(dummy)+len(ec)
    second=member('/',struct.pack('<III',1,offset,0)+ordinary_tail)
    object_member=member('owned.obj/',struct.pack('<H',0xa641)+bytes(18)) if with_object else b''
    return b'!<arch>\n'+first_member+second+ec+object_member


class PureECArchive(unittest.TestCase):
    def read(self,value):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'original.a';p.write_bytes(value);return archive_machines(p)

    def test_empty_ordinary_table_with_positive_real_ec_metadata(self):
        result=self.read(pure_ec())
        self.assertEqual(result['coff_members'],1)
        self.assertEqual(result['ec_symbol_index'],{'symbol_count':1,'indexed_members':1})

    def test_no_empty_ec_or_metadata_only_archive(self):
        for value in [pure_ec(ec_count=0),pure_ec(with_object=False)]:
            with self.subTest(value=value),self.assertRaises(Error):self.read(value)

    def test_empty_ordinary_table_cannot_hide_bytes_or_symbols(self):
        for value in [pure_ec(ordinary_tail=b'hidden'),pure_ec(first=struct.pack('>I',1)),pure_ec(index=0),pure_ec(index=2)]:
            with self.subTest(value=value),self.assertRaises(Error):self.read(value)


if __name__=='__main__':unittest.main()
