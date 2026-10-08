# SPDX-License-Identifier: MIT
"""Reject stale or incomplete final coverage indexes before expensive replay."""
import copy
from pathlib import Path
import tempfile
import unittest
from tools.dxmt.translated_inputs import fact
from tools.dxmt.translated_qualification import references, REQUIRED, FILENAMES

class QualificationReferences(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        refs = {}
        for key in REQUIRED:
            directory = self.root / key
            directory.mkdir()
            path = directory / FILENAMES.get(key, 'dependencies.json')
            path.write_text('{"passed":true}')
            refs[key] = fact(path)
        self.index = dict(scope='translated_graphics_stage4', stage=4, references=refs)

    def test_complete_reference_set_is_resolved(self):
        self.assertEqual(set(references(self.index)), set(REQUIRED))

    def test_saved_pass_does_not_admit_changed_bytes(self):
        (self.root / 'rendering/case.json').write_text('{"passed":true,"changed":true}')
        with self.assertRaises(Exception):
            references(self.index)

    def test_missing_required_scope_is_rejected(self):
        for key in REQUIRED:
            value = copy.deepcopy(self.index)
            del value['references'][key]
            with self.subTest(key=key), self.assertRaises(Exception):
                references(value)

    def test_prior_stage_cannot_be_promoted(self):
        self.index['stage'] = 3
        with self.assertRaises(Exception):
            references(self.index)
