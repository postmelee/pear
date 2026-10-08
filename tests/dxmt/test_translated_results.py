# SPDX-License-Identifier: MIT
import unittest
from tools.dxmt.translated_check import terminal

class TerminalTests(unittest.TestCase):
    def sample(self):
        return (b'{"record_kind":"pear_bootstrap_helper"}\n'
                b'PEAR_GRAPHICS_BEGIN suite=device version=1\n'
                b'PEAR_GRAPHICS_DEVICE hr=00000000 level=b000 device=1234 context=5678\n'
                b'PEAR_GRAPHICS_ADAPTER vendor=0000106b device=00000000 description=Apple GPU\n'
                b'PEAR_GRAPHICS_MODULE name=d3d11.dll base=1000 path=C:\\windows\\system32\\d3d11.dll\n'
                b'PEAR_GRAPHICS_MODULE name=dxgi.dll base=2000 path=C:\\windows\\system32\\dxgi.dll\n'
                b'PEAR_GRAPHICS_MODULE name=winemetal.dll base=3000 path=C:\\windows\\system32\\winemetal.dll\n'
                b'PEAR_GRAPHICS_END suite=device cases=1 passed=1\n')
    def test_complete_terminal(self):self.assertEqual(len(terminal(self.sample())),3)
    def test_incomplete_device_is_rejected(self):
        with self.assertRaises(Exception):terminal(self.sample().rsplit(b'PEAR_GRAPHICS_END',1)[0])
    def test_failed_device_is_rejected(self):
        with self.assertRaises(Exception):terminal(self.sample().replace(b'hr=00000000',b'hr=80004005'))
    def test_substitute_module_is_rejected(self):
        with self.assertRaises(Exception):terminal(self.sample().replace(b'name=winemetal.dll',b'name=wined3d.dll'))
    def test_extra_result_is_rejected(self):
        with self.assertRaises(Exception):terminal(self.sample()+b'PEAR_GRAPHICS_END suite=device cases=1 passed=1\n')

if __name__=='__main__':unittest.main()
