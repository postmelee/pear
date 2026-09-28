"""Portable rejection tests for the real tool preparation and format readers."""
import io
import json
from pathlib import Path
import struct
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import os

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools/wine"))
from common import Error
import toolchain


class ArchiveTests(unittest.TestCase):
    def archive(self, rows):
        content = io.BytesIO()
        with tarfile.open(fileobj=content, mode="w") as archive:
            for name, kind, value in rows:
                item = tarfile.TarInfo(name)
                item.type = kind
                if kind == tarfile.REGTYPE:
                    item.size = len(value)
                    archive.addfile(item, io.BytesIO(value))
                else:
                    item.linkname = value
                    archive.addfile(item)
        content.seek(0)
        return tarfile.open(fileobj=content)

    def test_valid_internal_symlink(self):
        with self.archive([("root/bin/clang", tarfile.REGTYPE, b"x"),
                           ("root/bin/clang++", tarfile.SYMTYPE, "clang")]) as archive:
            rows, size = toolchain.archive_members(archive, "root", 100)
        self.assertEqual((len(rows), size), (2, 1))

    def test_escape_name(self):
        for name in ("/root/file", "root/../file", "root//file", "different/file"):
            with self.subTest(name=name), self.archive([(name, tarfile.REGTYPE, b"x")]) as archive:
                with self.assertRaises(Error):
                    toolchain.archive_members(archive, "root", 100)

    def test_escape_symlink(self):
        for target in ("../../outside", "/absolute"):
            with self.subTest(target=target), self.archive([("root/a", tarfile.SYMTYPE, target)]) as archive:
                with self.assertRaises(Error):
                    toolchain.archive_members(archive, "root", 100)

    def test_symlink_parent_rejected(self):
        with self.archive([("root/a", tarfile.SYMTYPE, "b"),
                           ("root/b", tarfile.DIRTYPE, ""),
                           ("root/a/file", tarfile.REGTYPE, b"x")]) as archive:
            with self.assertRaisesRegex(Error, "archive_link_parent"):
                toolchain.archive_members(archive, "root", 100)

    def test_cycle_and_dangling(self):
        for rows in ([('root/a', tarfile.SYMTYPE, 'b')],
                     [('root/a', tarfile.SYMTYPE, 'b'), ('root/b', tarfile.SYMTYPE, 'a')]):
            with self.subTest(rows=rows), self.archive(rows) as archive:
                with self.assertRaises(Error):
                    toolchain.archive_members(archive, "root", 100)

    def test_expansion_bound(self):
        with self.archive([("root/file", tarfile.REGTYPE, b"abc")]) as archive:
            with self.assertRaisesRegex(Error, "archive_expansion_limit"):
                toolchain.archive_members(archive, "root", 2)

    def test_duplicate_and_device(self):
        for rows in ([('root/a', tarfile.REGTYPE, b'1'), ('root/a', tarfile.REGTYPE, b'2')],
                     [('root/a', tarfile.CHRTYPE, '')]):
            with self.subTest(rows=rows), self.archive(rows) as archive:
                with self.assertRaises(Error):
                    toolchain.archive_members(archive, "root", 100)


class FormatTests(unittest.TestCase):
    def write(self, directory, data):
        path = Path(directory) / "binary"
        path.write_bytes(data)
        return path

    def test_arm64_macho(self):
        with tempfile.TemporaryDirectory() as directory:
            data = struct.pack('<IIIIIIII', 0xFEEDFACF, toolchain.MACH_ARM64, 0, 2, 0, 0, 0, 0)
            info = toolchain.inspect_macho(self.write(directory, data))
            self.assertEqual(info['selected_cpu'], toolchain.MACH_ARM64)

    def test_intel_macho_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            data = struct.pack('<IIIIIIII', 0xFEEDFACF, 0x1000007, 0, 2, 0, 0, 0, 0)
            with self.assertRaises(Error):
                toolchain.inspect_macho(self.write(directory, data))

    def test_truncated_command_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            data = struct.pack('<IIIIIIII', 0xFEEDFACF, toolchain.MACH_ARM64, 0, 2, 1, 8, 0, 0)
            data += struct.pack('<II', 12, 100)
            with self.assertRaises(Error):
                toolchain.inspect_macho(self.write(directory, data))

    def test_coff_and_pe_are_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            coff = struct.pack('<H', 0xA641) + bytes(18)
            self.assertEqual(toolchain.coff_machine(self.write(directory, coff)), 0xA641)
            pe = bytearray(88)
            pe[:2] = b'MZ'
            struct.pack_into('<I', pe, 60, 64)
            pe[64:68] = b'PE\0\0'
            struct.pack_into('<H', pe, 68, 0x8664)
            self.assertEqual(toolchain.coff_machine(self.write(directory, pe)), 0x8664)

    def test_bad_pe_offset(self):
        with tempfile.TemporaryDirectory() as directory:
            pe = bytearray(64)
            pe[:2] = b'MZ'
            struct.pack_into('<I', pe, 60, 1000)
            with self.assertRaises(Error):
                toolchain.coff_machine(self.write(directory, pe))


class IdentityTests(unittest.TestCase):
    def test_sdk_version_checked_from_actual_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            sdk = Path(directory)
            (sdk / "SDKSettings.json").write_text(json.dumps({"Version": "26.4", "CanonicalName": "macosx26.4"}))
            with self.assertRaisesRegex(Error, "sdk_version_mismatch"):
                toolchain.inspect_sdk({"sdk": {"path": directory, "version": "26.5"}})

    def test_extraction_change_and_extra_file_rejected_against_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            tools = repo / "tools"
            installed = tools / "bundle"
            installed.mkdir(parents=True)
            archive_path = repo / "input.tar.xz"
            with tarfile.open(archive_path, "w:xz") as archive:
                member = tarfile.TarInfo("root/file")
                member.size = 4
                archive.addfile(member, io.BytesIO(b"real"))
            spec = {"download_path": "input.tar.xz", "size_bytes": archive_path.stat().st_size,
                    "sha256": toolchain.sha256(archive_path), "archive_root": "root", "max_unpacked_bytes": 100,
                    "install_subdir": "bundle"}
            artifact = {"path": str(installed)}
            (installed / "file").write_bytes(b"real")
            with patch.object(toolchain, "REPO", repo):
                toolchain.verify_extracted(spec, artifact, tools)
                (installed / "file").write_bytes(b"fake")
                with self.assertRaisesRegex(Error, "prepared_tool_archive_mismatch"):
                    toolchain.verify_extracted(spec, artifact, tools)
                (installed / "file").write_bytes(b"real")
                (installed / "extra").write_bytes(b"injected")
                with self.assertRaisesRegex(Error, "prepared_tool_inventory_mismatch"):
                    toolchain.verify_extracted(spec, artifact, tools)


class CommandTests(unittest.TestCase):
    def test_environment_does_not_inherit_build_injection(self):
        polluted = {"PATH": "/bad-tools", "CFLAGS": "-bad-flag", "CC": "/bad-compiler", "DYLD_INSERT_LIBRARIES": "/bad-library", "CPATH": "/bad-headers", "SDKROOT": "/bad-sdk", "MACOSX_DEPLOYMENT_TARGET": "1.0", "HOME": "/home/test"}
        with patch.dict(os.environ, polluted, clear=True):
            env = toolchain.base_env("/approved-sdk", ["/approved-tools"])
        for key in ("CFLAGS", "CC", "DYLD_INSERT_LIBRARIES", "CPATH", "MACOSX_DEPLOYMENT_TARGET"):
            self.assertNotIn(key, env)
        self.assertEqual(env["SDKROOT"], "/approved-sdk")
        self.assertEqual(env["PATH"], "/approved-tools:/usr/bin:/bin:/usr/sbin:/sbin")

    def test_duplicate_native_tool_rejected_before_execution(self):
        row = {"id": "clang", "path": "/not-executed", "sha256": "0" * 64}
        with self.assertRaisesRegex(Error, "missing_or_duplicate_native_tool"):
            toolchain.native_tool({"native_tools": [row, row.copy()]}, "clang")

    def test_nonzero_exit_preserves_diagnostic(self):
        with tempfile.TemporaryDirectory() as directory:
            commands = []
            with self.assertRaisesRegex(Error, 'command_failed'):
                toolchain.run_command(commands, 'failure', [sys.executable, '-c', 'import sys; print("owned-error", file=sys.stderr); sys.exit(7)'], directory, os.environ.copy())
            self.assertEqual(commands[0]['exit_code'], 7)
            self.assertIn('owned-error', commands[0]['stderr'])
            self.assertTrue(Path(commands[0]['stderr_log']['path']).is_file())

    def test_fast_output_overflow_cannot_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            commands = []
            with self.assertRaisesRegex(Error, 'command_failed'):
                toolchain.run_command(commands, 'overflow', [sys.executable, '-c', 'import os; os.write(1, b"x" * 300000)'], directory, os.environ.copy())
            self.assertTrue(commands[0]['output_limit'])

    def test_timeout_kills_owned_process(self):
        with tempfile.TemporaryDirectory() as directory:
            commands = []
            with self.assertRaisesRegex(Error, 'command_failed'):
                toolchain.run_command(commands, 'timeout', [sys.executable, '-c', 'import time; time.sleep(10)'], directory, os.environ.copy(), timeout=0.05)
            self.assertTrue(commands[0]['timed_out'])


if __name__ == '__main__':
    unittest.main()
