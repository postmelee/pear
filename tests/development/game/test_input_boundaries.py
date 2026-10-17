# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Narrow stable-reader controls; no FIFO, process or native code is created."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from pear_runtime.fixtures.inputs import fact
from tools.development.game import inputs


class BoundedLedger(unittest.TestCase):
    def test_open_is_nonblocking_and_no_follow_before_identity_check(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp).resolve()/'input';p.write_bytes(b'a');ref=fact(p);real_open=os.open
            with patch.object(inputs.os,'open',wraps=real_open) as opened:
                inputs.Ledger().check(ref)
            flags=opened.call_args.args[1]
            self.assertTrue(flags&os.O_NONBLOCK);self.assertTrue(flags&os.O_NOFOLLOW)

    def test_open_identity_swap_refuses_and_closes_descriptor(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp).resolve()/'input';p.write_bytes(b'a');ref=fact(p);before=p.stat();real_close=os.close
            swapped=SimpleNamespace(st_dev=before.st_dev,st_ino=before.st_ino+1,st_mode=before.st_mode,
                st_size=before.st_size,st_mtime_ns=before.st_mtime_ns,st_ctime_ns=before.st_ctime_ns)
            with patch.object(inputs.os,'fstat',return_value=swapped),patch.object(inputs.os,'close',wraps=real_close) as closed:
                with self.assertRaisesRegex(Exception,'d24_open_race'):inputs.Ledger().check(ref)
            closed.assert_called_once()

    def test_growing_reader_refuses_on_first_excess_byte_without_second_read(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp).resolve()/'input';p.write_bytes(b'a');ref=fact(p)
            with patch.object(inputs.os,'read',side_effect=[b'aa',AssertionError('unbounded second read')]) as read:
                with self.assertRaisesRegex(Exception,'game_ledger_read_bound'):inputs.Ledger().check(ref)
            self.assertEqual(read.call_count,1);self.assertEqual(read.call_args.args[1],2)

    def test_kept_record_limit_and_changed_size_refuse_before_open(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp).resolve()/'input';p.write_bytes(b'a');ref=fact(p);stat=p.stat()
            oversized=SimpleNamespace(st_size=64*1024**2+1)
            with patch.object(inputs,'regular',return_value=(p,oversized)),patch.object(inputs.os,'open') as opened:
                with self.assertRaisesRegex(Exception,'d24_record_limit'):
                    inputs.Ledger().check({**ref,'size_bytes':oversized.st_size},keep=True)
                opened.assert_not_called()
            with patch.object(inputs.os,'open') as opened:
                with self.assertRaisesRegex(Exception,'d24_input_changed'):
                    inputs.Ledger().check({**ref,'size_bytes':2})
                opened.assert_not_called()

    def test_boolean_negative_and_unbounded_reference_sizes_refuse_before_open(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp).resolve()/'input';p.write_bytes(b'a');ref=fact(p)
            for size in (True,-1,8*1024**3+1):
                with self.subTest(size=size),patch.object(inputs.os,'open') as opened:
                    with self.assertRaisesRegex(Exception,'game_ledger_reference_identity'):
                        inputs.Ledger().check({**ref,'size_bytes':size})
                    opened.assert_not_called()


if __name__=='__main__':unittest.main()
