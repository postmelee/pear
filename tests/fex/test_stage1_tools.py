"""Portable tool provenance and archive refusal controls; no executable runs."""
import copy
import hashlib
import io
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.fex import tools
from tools.fex.common import Error


def tar_bytes(rows):
    """Rows are (relative name, kind, content/target); fixtures are redistributable."""
    value = io.BytesIO()
    with tarfile.open(fileobj=value, mode='w') as archive:
        for name, kind, content in rows:
            info = tarfile.TarInfo('root/'+name)
            info.mode = 0o644
            if kind == 'file':
                info.size = len(content)
                archive.addfile(info, io.BytesIO(content))
            else:
                info.type = {'sym': tarfile.SYMTYPE, 'hard': tarfile.LNKTYPE, 'dir': tarfile.DIRTYPE}[kind]
                if kind != 'dir':
                    info.linkname = content
                archive.addfile(info)
    return value.getvalue()


def minimal_receipt():
    """Shape-only synthetic receipt; never accepted as actual tool evidence."""
    source = {'commit': tools.NINJA_COMMIT, 'tree': '0'*40, 'source_root': 'ninja-source',
              'archive': {}, 'files': [], 'notice': {}, 'reused_cache': True, 'repository': '/unused'}
    ids = ('cmake.version', 'sdk.path', 'sdk.version', 'ninja.commit', 'ninja.tree-id',
           'ninja.commit-object', 'ninja.tree', 'ninja.archive', 'ninja.bootstrap', 'ninja.version')
    return {'schema_version': 1, 'record_kind': 'fex_tools_prepared', 'scope': 'fex_component',
            'toolchain_sha256': '0'*64, 'producer_sha256': '0'*64,
            'helper_sha256': dict.fromkeys(tools.HELPERS, '0'*64),
            'downloads': [{'path': 'downloads/cmake-SHA-256.txt'}, {'path': 'downloads/cmake.tar.gz'}],
            'inventories': [{'root': 'cmake'}, {'root': 'ninja-source'}],
            'tools': {'cmake': {}, 'ninja': {}}, 'commands': [{'id': ident} for ident in ids],
            'runtime_execution': False, 'ninja_source': source,
            'native_build': dict.fromkeys(('compiler', 'xcrun', 'python', 'sdk', 'environment'), {}), 'passed': True}


class AliasContracts(unittest.TestCase):
    def graph(self, rows, budget=100):
        with tarfile.open(fileobj=io.BytesIO(tar_bytes(rows)), mode='r') as archive:
            return tools.archive_graph(archive, 'root', budget)

    def test_framework_alias_followed_before_parent_components(self):
        # Current/.. refers to Versions after resolving Current -> A.
        rows = [('Qt/Versions/A/Qt', 'file', b'x'), ('Qt/Versions/Current', 'sym', 'A'),
                ('Qt/Qt', 'sym', 'Versions/Current/../A/Qt')]
        members, total = self.graph(rows)
        self.assertEqual((len(members), total), (3, 1))

    def test_normpath_cannot_hide_alias_then_parent_escape(self):
        rows = [('z', 'dir', ''), ('f', 'file', b'x'), ('d/b', 'sym', '../z'),
                ('d/l', 'sym', 'b/../../f')]
        with self.assertRaisesRegex(Error, 'archive_link_escape'):
            self.graph(rows)
        # Graph rejection must precede every extraction write.
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            archive = parent/'input.tar'
            archive.write_bytes(tar_bytes(rows))
            destination = parent/'output'
            with self.assertRaises(Error):
                tools.extract(archive, destination, 'root')
            self.assertFalse(destination.exists())
            self.assertFalse((parent/'f').exists())

    def test_file_is_not_a_directory_even_when_parent_normalizes(self):
        with self.assertRaisesRegex(Error, 'archive_link_not_directory'):
            self.graph([('f', 'file', b'x'), ('good', 'file', b'y'), ('link', 'sym', 'f/../good')])

    def test_implicit_directory_alias_cycle_dangling_and_write_refused(self):
        cases = [ [('a', 'sym', 'b'), ('b', 'sym', 'a')],
                  [('a', 'sym', 'missing')],
                  [('a', 'sym', 'b'), ('b/file', 'file', b'x'), ('a/file', 'file', b'y')],
                  [('a', 'file', b'x'), ('a/child', 'file', b'y')] ]
        for rows in cases:
            with self.subTest(rows=rows), self.assertRaises(Error):
                self.graph(rows)

    def test_case_and_unicode_aliases_refused_before_extraction(self):
        for left, right in (('A/file', 'a/other'), ('caf\u00e9/x', 'cafe\u0301/y')):
            with self.subTest(left=left), self.assertRaisesRegex(Error, 'archive_path_alias'):
                self.graph([(left, 'file', b'x'), (right, 'file', b'y')])

    def test_member_limit_checked_during_iteration(self):
        with mock.patch.object(tools, 'MAX_MEMBERS', 2), self.assertRaisesRegex(Error, 'archive_member_limit'):
            self.graph([(str(i), 'file', b'x') for i in range(3)])

    def test_payload_replay_matches_actual_framework_files(self):
        rows = [('Qt/Versions/A/Qt', 'file', b'reusable fixture'), ('Qt/Versions/Current', 'sym', 'A'),
                ('Qt/Qt', 'sym', 'Versions/Current/Qt')]
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            archive = parent/'input.tar'
            archive.write_bytes(tar_bytes(rows))
            destination = parent/'output'
            tools.extract(archive, destination, 'root')
            expected = tools.archive_inventory(archive, 'root')
            self.assertEqual(tools.files(destination), expected)
            (destination/'Qt/Versions/A/Qt').write_bytes(b'mutated')
            self.assertNotEqual(tools.files(destination), expected)


class EvidenceContracts(unittest.TestCase):
    def test_incomplete_passed_record_cannot_qualify_empty_tools(self):
        for name, value in (('tools', {}), ('downloads', []), ('inventories', []), ('commands', []), ('helper_sha256', {})):
            data = minimal_receipt()
            data[name] = value
            with self.subTest(name=name), self.assertRaises(Error):
                tools.receipt_shape(data)

    def test_runtime_claim_wrong_pin_duplicate_or_omitted_operation_refused(self):
        variants = []
        data = minimal_receipt(); data['runtime_execution'] = True; variants.append(data)
        data = minimal_receipt(); data['ninja_source']['commit'] = '0'*40; variants.append(data)
        data = minimal_receipt(); data['commands'][-1] = copy.deepcopy(data['commands'][0]); variants.append(data)
        data = minimal_receipt(); data['ninja_source']['reused_cache'] = False; variants.append(data)
        data = minimal_receipt(); data['extra_support'] = True; variants.append(data)
        for data in variants:
            with self.subTest(data=data), self.assertRaises(Error):
                tools.receipt_shape(data)

    def test_copied_cache_bytes_rehashed_before_consumption(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache = root/'cache'
            cache.write_bytes(b'original')
            expected = hashlib.sha256(b'original').hexdigest()
            def corrupt_copy(_source, destination):
                Path(destination).write_bytes(b'different')
            with mock.patch.object(tools.shutil, 'copyfile', side_effect=corrupt_copy), self.assertRaisesRegex(Error, 'copied_tool_digest_mismatch'):
                tools.fetch(tools.CMAKE_BASE+tools.CMAKE_ROOT+'.tar.gz', root/'copy', expected, cache=cache)
            self.assertEqual(cache.read_bytes(), b'original')

    def test_selected_sdk_symlink_identity_not_path_spelling(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            selected = root/'MacOSX26.5.sdk'; selected.mkdir()
            locked = root/'MacOSX.sdk'; locked.symlink_to(selected.name)
            tools.sdk_matches(str(selected), str(locked))
            different = root/'Other.sdk'; different.mkdir()
            with self.assertRaisesRegex(Error, 'selected_sdk_mismatch'):
                tools.sdk_matches(str(different), str(locked))


class SourceProofContracts(unittest.TestCase):
    def fixture(self):
        content = b'redistributable source fixture\n'
        blob = hashlib.sha1(f'blob {len(content)}\0'.encode()+content).hexdigest()
        listing = b'100644 blob '+blob.encode()+b'\tCOPYING\0'
        entries = {'COPYING': {'mode': '100644', 'git_object': blob}}
        tree = tools.source_preparation.tree_identity(entries)
        commit = ('tree '+tree+'\nauthor Fixture <fixture@example.invalid> 0 +0000\ncommitter Fixture <fixture@example.invalid> 0 +0000\n\nFixture\n').encode()
        ident = hashlib.sha1(f'commit {len(commit)}\0'.encode()+commit).hexdigest()
        return content, listing, entries, tree, commit, ident

    def test_commit_bytes_tree_and_blob_all_bound_independently(self):
        content, listing, entries, tree, commit, ident = self.fixture()
        self.assertEqual(tools.ninja_entries(commit, listing, tree, ident), entries)
        for raw, ls_tree, expected_tree in ((commit+b'changed', listing, tree),
                                           (commit, listing.replace(b'COPYING', b'OTHER'), tree),
                                           (commit, listing, '0'*40)):
            with self.subTest(tree=expected_tree), self.assertRaises(Error):
                tools.ninja_entries(raw, ls_tree, expected_tree, ident)

    def test_mutated_source_archive_or_installed_notice_refused(self):
        content, _, entries, _, _, _ = self.fixture()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root/'ninja.tar'
            def write(value):
                with tarfile.open(archive, 'w') as output:
                    member = tarfile.TarInfo('ninja-source/COPYING'); member.size = len(value); member.mode = 0o644
                    output.addfile(member, io.BytesIO(value))
            write(content)
            source = root/'source'; source.mkdir(); (source/'COPYING').write_bytes(content)
            tools.ninja_archive(archive, entries, source)
            (source/'COPYING').write_bytes(b'notice changed')
            with self.assertRaisesRegex(Error, 'ninja_materialized_source_changed'):
                tools.ninja_archive(archive, entries, source)
            write(b'archive changed')
            with self.assertRaisesRegex(Error, 'ninja_archive_blob_mismatch'):
                tools.ninja_archive(archive, entries)

if __name__ == '__main__':
    unittest.main()
