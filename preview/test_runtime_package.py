# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
import hashlib
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import runtime_package as p
from runtime_build import inventory


class PackageTests(unittest.TestCase):
    def test_regenerated_pin_keeps_notices_and_exact_artifact_identity(self):
        result = {'runtime_id': 'fixture-id', 'name': 'fixture.tar.gz',
                  'sha256': 'a' * 64, 'size': 123}
        source = p.render_pin(result)
        self.assertTrue(source.startswith('// SPDX-FileCopyrightText: 2026 Pear contributors\n'
                                          '// SPDX-License-Identifier: GPL-3.0-or-later\n'))
        body = '\n'.join(line for line in source.splitlines() if not line.startswith('//')) + '\n'
        self.assertEqual(body, 'pub const RUNTIME_ID: &str = "fixture-id";\n'
                         'pub const RUNTIME: super::Artifact = super::Artifact {\n'
                         '    name: "fixture.tar.gz", url: "", sha: "' + 'a' * 64
                         + '", size: 123,\n};\n')

    def test_override_changes_only_reviewed_marker(self):
        data = b'x' * 64 + b'Wine builtin DLL' + b'y' * 64
        out = p.native_dxmt(data)
        self.assertEqual(out[:64], data[:64])
        self.assertEqual(out[80:], data[80:])
        with self.assertRaises(ValueError):
            p.native_dxmt(out)
        with self.assertRaises(ValueError):
            p.native_dxmt(b'bad')

    def test_exact_inventory_and_no_private_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = root / 'Runtime'
            (runtime / 'bin').mkdir(parents=True)
            (runtime / 'bin/wine').write_bytes(b'fixture')
            (runtime / 'bin/wine').chmod(0o755)
            (runtime / 'bin/wine64').symlink_to('wine')
            for arch in ['i386-windows', 'x86_64-windows']:
                directory = runtime / 'share/pear/dxmt' / arch
                directory.mkdir(parents=True)
                for name in ['d3d11.dll', 'dxgi.dll', 'd3d10core.dll', 'winemetal.dll']:
                    (directory / name).write_bytes(b'x' * 64 + b'Wine builtin DLL' + b'y')
            (root / 'private').mkdir()
            (root / 'private/secret').write_text('not for distribution')
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps(inventory(runtime)))
            with patch.object(p, 'BASELINE', hashlib.sha256(manifest.read_bytes()).hexdigest()):
                out = root / 'candidate.tar.gz'
                result = p.package(runtime, manifest, out)
                self.assertTrue(result['baseline_unchanged'])
                with tarfile.open(out) as archive:
                    self.assertFalse(any('private' in n for n in archive.getnames()))
                    self.assertEqual(archive.getmember('Libraries/Wine/bin/wine').mode, 0o755)
                    self.assertEqual(archive.getmember('Libraries/Wine/bin/wine64').linkname, 'wine')
                with self.assertRaises(ValueError):
                    p.package(runtime, manifest, out)
                (runtime / 'credentials').write_text('unexpected')
                with self.assertRaises(ValueError):
                    p.package(runtime, manifest, root / 'other.tar.gz')

    def test_signed_archive_preserves_bytes_modes_and_rejects_extra_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); libraries = root/'Libraries'; libraries.mkdir()
            binary = libraries/'wine'; binary.write_bytes(b'signed Mach-O fixture'); binary.chmod(0o755)
            (libraries/'wine64').symlink_to('wine')
            manifest = root/'signing.json'; manifest.write_text(json.dumps({'files': inventory(libraries)}))
            digest = p.sha256(manifest)
            result = p.package_signed(libraries, manifest, digest, root/'signed.tar.gz')
            with tarfile.open(root/'signed.tar.gz') as archive:
                self.assertEqual(archive.extractfile('Libraries/wine').read(), binary.read_bytes())
                self.assertEqual(archive.getmember('Libraries/wine').mode, 0o755)
                self.assertEqual(archive.getmember('Libraries/wine64').linkname, 'wine')
            with self.assertRaisesRegex(ValueError, 'fresh'):
                p.package_signed(libraries, manifest, digest, root/'signed.tar.gz')
            with self.assertRaisesRegex(ValueError, 'manifest changed'):
                p.package_signed(libraries, manifest, 'bad', root/'other.tar.gz')
            (libraries/'login').write_text('private')
            with self.assertRaisesRegex(ValueError, 'inventory changed'):
                p.package_signed(libraries, manifest, digest, root/'other.tar.gz')
            self.assertFalse((root/'other.tar.gz').exists())

    def test_unknown_manifest_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / 'manifest.json'
            manifest.write_text('[]')
            with self.assertRaises(ValueError):
                p.package(root, manifest, root / 'candidate.tar.gz')


if __name__ == '__main__':
    unittest.main()
