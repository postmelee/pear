# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: MIT
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import os, unittest
from tools.development.game import inputs as d
from pear_runtime.fixtures.inputs import fact

class LedgerTests(unittest.TestCase):
    def test_mutate_and_restore_bytes_still_refused(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp).resolve()/'input';p.write_bytes(b'old');ledger=d.Ledger();ledger.check(fact(p))
            p.write_bytes(b'new');p.write_bytes(b'old')
            with self.assertRaisesRegex(Exception,'d24_input_changed_during_check'):ledger.finish()

    def test_file_changed_during_read_refused(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp).resolve()/'input';p.write_bytes(b'old');ref=fact(p);original=os.read
            def changed(fd,size):
                data=original(fd,size)
                if data:p.write_bytes(b'new')
                return data
            with patch.object(d.os,'read',side_effect=changed):
                with self.assertRaisesRegex(Exception,'d24_read_race'):d.Ledger().check(ref)

    def test_inode_replacement_and_closed_ledger_refused(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp).resolve()/'input';p.write_bytes(b'old');ledger=d.Ledger();ledger.check(fact(p))
            q=p.with_name('replacement');q.write_bytes(b'old');q.replace(p)
            with self.assertRaisesRegex(Exception,'d24_input_changed_during_check'):ledger.finish()
            new=d.Ledger();new.check(fact(p));new.finish()
            with self.assertRaisesRegex(Exception,'d24_ledger_closed'):new.check(fact(p))
