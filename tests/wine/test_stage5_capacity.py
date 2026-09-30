"""Portable parser capacity regression using original synthetic fixture events.

The maximal successful window timeline is assessed independently. Added process
image snapshots model bounded Wine initialization volume only: this combined
record is never presented as a successful host run, signature or qualification.
No retained private run, game file, account or host installation is required.
"""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/wine'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import api_runner as api
from common import Error, encoded, read_relative
from test_window_evidence import FACTS, RUNTIME, envelope, fixture
import window_evidence


def source_shaped_case():
    rows, result, signed, dynamic = fixture(99)
    # Fourteen streams are within the 64-process limit. Each receives two
    # 600-image snapshots, within the existing per-snapshot and stream bounds.
    roles = ['loader', *['process-%02d' % n for n in range(1, 13)], 'server']
    for index, role in enumerate(roles):
        events = result['events'].setdefault(role, [])
        for snapshot in range(2):
            for image in range(600):
                events.append(dict(envelope('image'), role=role, pid=123 + index, index=image,
                    path='/synthetic/System/Library/Frameworks/' + 'PublicNativeLibrary' * 4 +
                         '/Versions/A/Image%04d.dylib' % image,
                    cpu_type=0x100000c, uuid='%032x' % (image + 1)))
            events.append(dict(envelope('images_end'), role=role, pid=123 + index, count=600))
    result.update(schema_version=1, record_kind='wine_api_case', case=dict(api.WINDOW_CASE))
    return rows, result, signed, dynamic


def structural_nodes(value):
    if isinstance(value, dict):
        return 1 + sum(1 + structural_nodes(item) for item in value.values())
    if isinstance(value, list):
        return 1 + sum(map(structural_nodes, value))
    return 1


class Stage5CapacityTests(unittest.TestCase):
    def test_maximum_successful_timeline_survives_public_selector(self):
        import stage5_evidence
        rows, result, signed, dynamic = fixture(99)
        with patch.object(window_evidence, 'fixture_facts', return_value=FACTS):
            summary = window_evidence.assess(rows, result, RUNTIME, signed, dynamic)
        self.assertEqual(summary['main_thread_barriers'], 2000)
        self.assertEqual(summary['appkit_event_turns'], 1980)
        self.assertEqual(summary['native_anchor_parts'], 16447)
        self.assertEqual(stage5_evidence.window_summary(summary), summary)

    def test_large_source_shaped_record_requires_only_window_envelope(self):
        _, result, _, _ = source_shaped_case()
        raw = encoded(result)
        nodes = structural_nodes(result)
        self.assertGreater(len(raw), 16 * 1024 * 1024)
        self.assertGreater(nodes, 1_000_000)
        self.assertLess(len(raw), 32 * 1024 * 1024)
        self.assertLess(nodes, 2_000_000)
        total = 0
        for role, events in result['events'].items():
            lines = [json.dumps(row, separators=(',', ':')).encode() + b'\n' for row in events]
            self.assertTrue(all(len(line) <= 512 for line in lines))
            count = sum(map(len, lines)); total += count
            self.assertLess(count, api.event_limit(role, suite=api.STAGE5_SUITE, case_id='window'))
        self.assertLess(total, 32 * 1024 * 1024)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root/'case.json').write_bytes(raw)
            with self.assertRaisesRegex(Error, 'input_size_limit'):
                read_relative(root, 'case.json', api.CASE_JSON_BYTES)
            selected = dict(suite=api.STAGE5_SUITE, case_id='window')
            read_back = read_relative(root, 'case.json', api.case_json_limits(**selected)[0])
            decoded = api.decode_case(read_back, **selected)
            self.assertEqual(len(decoded['events']['loader']), len(result['events']['loader']))
        with self.assertRaisesRegex(Error, 'input_size_limit'):
            api.decode_case(raw)
        with self.assertRaisesRegex(Error, 'input_size_limit'):
            api.decode_case(raw, suite=api.STAGE5_SUITE, case_id='threads')


if __name__ == '__main__':
    unittest.main()
