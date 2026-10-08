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


class RenderingTests(unittest.TestCase):
    def test_known_integer_endpoints_and_changed_element(self):
        import struct
        from tools.dxmt.translated_render_check import compare
        values=[i*66051+5 for i in range(64)]
        self.assertEqual(values[-1],4161218)
        self.assertEqual(compare('buffer',64,1,256,'uint32',struct.pack('<64I',*values)),64)
        values[31]^=1
        with self.assertRaises(Exception):compare('buffer',64,1,256,'uint32',struct.pack('<64I',*values))

    def test_zero_filled_outputs_cannot_pass(self):
        from tools.dxmt.translated_render_check import compare,NAMES
        for name in NAMES:
            with self.subTest(name=name),self.assertRaises(Exception):
                if name in ('buffer','compute'):compare(name,64,1,256,'uint32',bytes(256))
                else:
                    size=8 if name.startswith('texture') else 64
                    compare(name,size,size,size*4,'rgba8',bytes(size*size*4))

    def test_depth_occlusion_and_blend_tolerance(self):
        from tools.dxmt.translated_render_check import compare
        self.assertEqual(compare('depth',64,64,256,'rgba8',bytes([255,0,0,255])*4096),4096)
        for pixel in ([127,0,128,127],[128,0,127,128]):
            self.assertEqual(compare('blend',64,64,256,'rgba8',bytes(pixel)*4096),4096)
        for name,pixel in [('depth',[0,255,0,255]),('blend',[126,0,128,128])]:
            with self.assertRaises(Exception):compare(name,64,64,256,'rgba8',bytes(pixel)*4096)

    def test_clear_only_raster_and_short_pitch_are_rejected(self):
        from tools.dxmt.translated_render_check import compare
        with self.assertRaises(Exception):compare('raster',64,64,256,'rgba8',bytes([17,34,51,255])*4096)
        with self.assertRaises(Exception):compare('depth',64,64,255,'rgba8',bytes([255,0,0,255])*4096)

    def test_incomplete_render_terminal(self):
        from tools.dxmt.translated_render_check import terminal
        with self.assertRaises(Exception):terminal(b'{"record_kind":"pear_bootstrap_helper"}\nPEAR_RENDER_BEGIN version=1 cases=5\n')
        with self.assertRaises(Exception):terminal(b'{"record_kind":"pear_bootstrap_helper"}\nPEAR_RENDER_BEGIN version=1 cases=5\nPEAR_RENDER_END cases=5 readbacks=7 completed=1\n')

    def test_logged_error_fails_despite_validation_banner(self):
        from tools.dxmt.translated_render_check import validation
        banner=b'Metal API Validation Enabled\nMetal GPU Validation Enabled\n'
        validation(banner)
        for error in (b'Shader validation error: out-of-bounds read (zerofill)',b'failed assertion',b'GPU AddressSanitizer: invalid read'):
            with self.subTest(error=error),self.assertRaises(Exception):validation(banner+error)

    def test_pipeline_state_requires_actual_fixture_shaders(self):
        from tools.dxmt.translated_render_check import pipeline_validation
        shaders={'vertex':{'sha1':'12345678'+'0'*32},'transform':{'sha1':'abcdef01'+'0'*32}}
        raw=(b'PEAR_METAL_PIPELINE kind=render validation=1 function=vs_12345678_variant\n'*4+
             b'PEAR_METAL_PIPELINE kind=compute validation=1 function=cs_abcdef01_variant\n')
        self.assertTrue(pipeline_validation(raw,shaders)['all_observed_enabled'])
        for broken in (raw.replace(b'validation=1',b'validation=2'),raw.replace(b'vs_12345678_',b'vs_00000000_'),b'Metal GPU Validation Enabled\n'):
            with self.assertRaises(Exception):pipeline_validation(broken,shaders)

if __name__=='__main__':unittest.main()
