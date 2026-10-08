# SPDX-License-Identifier: MIT
import unittest
from tools.dxmt.translated_pairing import without_desktop_menu

class PrefixConfigurationTests(unittest.TestCase):
    def sample(self):
        return (b'WINE REGISTRY Version 2\n'
                b'[Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\RunServices] 123\n'
                b'"unrelated"="keep"\n'
                b'"winemenubuilder"="C:\\\\windows\\\\system32\\\\winemenubuilder.exe -a -r"\n')

    def test_removes_only_optional_menu(self):
        raw=self.sample()
        self.assertEqual(without_desktop_menu(raw),b'\n'.join(raw.split(b'\n')[:-2])+b'\n')

    def test_changed_command_is_refused(self):
        with self.assertRaises(Exception):without_desktop_menu(self.sample().replace(b'-a -r',b'-a -other'))

    def test_other_registry_section_is_refused(self):
        with self.assertRaises(Exception):without_desktop_menu(self.sample().replace(b'RunServices',b'OtherServices'))

if __name__=='__main__':unittest.main()
