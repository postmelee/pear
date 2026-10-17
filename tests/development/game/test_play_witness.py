# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: MIT
from pathlib import Path
from tempfile import TemporaryDirectory
import json,unittest
from tools.development.game.witness import publish_positive,live_stamp
class WitnessPublication(unittest.TestCase):
    def test_valid_as_of_and_deadline(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/'response.json';times=iter([10,11])
            publish_positive(p,{'valid':True},20,lambda:next(times))
            self.assertEqual(json.loads(p.read_text()),{'valid':True,'deadline_ns':20,'at_ns':10})
    def test_expired_and_malformed_before_publication(self):
        for deadline in (True,0,-1,'20',2**63,9,10):
            with self.subTest(deadline=deadline),TemporaryDirectory() as tmp:
                p=Path(tmp)/'response.json'
                with self.assertRaises(Exception):publish_positive(p,{'valid':True},deadline,lambda:10)
                self.assertFalse(p.exists())
    def test_expiry_during_publication_preserves_prior_historical_receipt(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/'response.json';p.write_text('prior');times=iter([10,20])
            with self.assertRaises(Exception):publish_positive(p,{'valid':True},20,lambda:next(times))
            self.assertEqual(p.read_text(),'prior')
    def test_stop_during_publication(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);calls=[]
            def clock():
                calls.append(1)
                if len(calls)==2:(root/'witness-stop').touch()
                return 10
            with self.assertRaises(Exception):publish_positive(root/'response.json',{'valid':True},20,clock)
            self.assertFalse((root/'response.json').exists())
if __name__=='__main__':unittest.main()
