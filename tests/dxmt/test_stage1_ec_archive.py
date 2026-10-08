"""Bounded ARM64EC archive-index controls; no compiler/guest execution."""
import struct
import unittest
from support import Fixture
from common import Error, archive_machines

def member(name,body):
    header=name.encode().ljust(16)+b'0           '+b'0     '+b'0     '+b'644     '+str(len(body)).encode().ljust(10)+b'`\n'
    return header+body+(b'\n' if len(body)&1 else b'')


def ec_archive(index=1, member_offset_delta=0, ec_count=1, ec_name=b'name\0'):
    first=member('/',bytes(4))
    ec=member('/<ECSYMBOLS>/',struct.pack('<IH',ec_count,index)+ec_name)
    dummy=member('/',struct.pack('<IIIH',1,0,1,1)+b'name\0')
    offset=8+len(first)+len(dummy)+len(ec)
    second=member('/',struct.pack('<IIIH',1,offset+member_offset_delta,1,1)+b'name\0')
    obj=member('member.o/',struct.pack('<H',0xa641)+bytes(18))
    return b'!<arch>\n'+first+second+ec+obj

class ECArchiveControls(unittest.TestCase):
    def test_ec_index_is_metadata_not_an_object_machine(self):
        result=self.read_archive(ec_archive())
        self.assertEqual(self.machines(result),{0xa641})
    def test_truncated_counts_and_unterminated_strings_are_refused(self):
        for value in [ec_archive(ec_count=2),ec_archive(ec_name=b'name'),ec_archive()[:-1]]:
            with self.subTest(size=len(value)),self.assertRaises(Error):self.read_archive(value)
    def test_zero_or_out_of_range_member_indices_are_refused(self):
        for index in [0,2,65535]:
            with self.subTest(index=index),self.assertRaises(Error):self.read_archive(ec_archive(index=index))
    def test_offset_must_reference_an_actual_regular_member(self):
        with self.assertRaises(Error):self.read_archive(ec_archive(member_offset_delta=1))

    def read_archive(self,value):return archive_machines(value)
    def machines(self,value):return set(value)

if __name__=='__main__':unittest.main()
