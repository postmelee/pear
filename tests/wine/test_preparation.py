"""Real temporary bare Git inputs and adversarial, self-owned tar archives."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[2] / 'tools/wine'
sys.path.insert(0, str(TOOLS))
import common
import prepare
from test_inputs import input_fixture


def git_blob(data):
    return hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()


def make_archive(path, entries):
    with tarfile.open(path, 'w', format=tarfile.USTAR_FORMAT) as archive:
        for name, kind, content, mode in entries:
            member = tarfile.TarInfo(name)
            member.mode = mode
            member.type = kind
            if kind == tarfile.REGTYPE:
                member.size = len(content)
                archive.addfile(member, io.BytesIO(content))
            else:
                member.linkname = content.decode()
                archive.addfile(member)


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.archive = self.root / 'owned.tar'
        self.expected = {'source.c': {'mode': '100644', 'git_blob': git_blob(b'owned')}}

    def test_traversal_and_escaping_links_never_write_outside(self):
        for index, (name, kind, content) in enumerate([
            ('../escape', tarfile.REGTYPE, b'owned'),
            ('/escape', tarfile.REGTYPE, b'owned'),
            ('source.c', tarfile.SYMTYPE, b'../escape'),
            ('source.c', tarfile.LNKTYPE, b'../escape'),
            ('source.c', tarfile.FIFOTYPE, b'')]):
            make_archive(self.archive, [(name, kind, content, 0o644)])
            with self.subTest(name=name, kind=kind), self.assertRaises(common.Error):
                prepare.extract_verified(self.archive, self.root / f'out-{index}', self.expected)
        self.assertFalse((self.root / 'escape').exists())

    def test_changed_missing_and_duplicate_content_cannot_pass(self):
        cases = [([('source.c', tarfile.REGTYPE, b'changed', 0o644)], 'archive_blob_mismatch'),
                 ([], 'archive_missing_files'),
                 ([('source.c', tarfile.REGTYPE, b'owned', 0o644)] * 2, 'duplicate_archive_entry'),
                 ([('source.c', tarfile.REGTYPE, b'owned', 0o4755)], 'unsafe_archive_mode'),
                 ([('source.c', tarfile.REGTYPE, b'owned', 0o755)], 'archive_mode_mismatch')]
        for index, (entries, code) in enumerate(cases):
            make_archive(self.archive, entries)
            with self.subTest(code=code), self.assertRaisesRegex(common.Error, code):
                prepare.extract_verified(self.archive, self.root / f'out-{index}', self.expected)

    def test_member_and_expansion_limits_are_enforced(self):
        make_archive(self.archive, [('source.c', tarfile.REGTYPE, b'owned', 0o644)])
        for index, key in enumerate(['MAX_MEMBER', 'MAX_CONTENT']):
            with patch.object(prepare, key, 4), self.assertRaises(common.Error):
                prepare.extract_verified(self.archive, self.root / f'out-{index}', self.expected)

    def test_tree_links_case_aliases_and_file_directory_conflicts_rejected(self):
        blob = git_blob(b'owned').encode()
        for value in [b'120000 blob ' + blob + b'\tsource\0',
                      b'160000 commit ' + blob + b'\tsource\0',
                      b'100644 blob ' + blob + b'\tA/file\0' + b'100644 blob ' + blob + b'\ta/other\0',
                      b'100644 blob ' + blob + b'\ta\0' + b'100644 blob ' + blob + b'\ta/file\0']:
            with self.subTest(value=value), self.assertRaises(common.Error):
                prepare.tree_entries(value)


@unittest.skipUnless(shutil.which('git'), 'installed Git is required for real owned bare-repository tests')
class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.inputs, self.audit = input_fixture(self.root)
        self.repository = self.root / '.build/task1-sources/inputs/wine-upstream/repo.git'
        self.repository.mkdir(parents=True)
        self.env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
        self.env.update(GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_SYSTEM='/dev/null', GIT_CONFIG_NOSYSTEM='1',
                        GIT_AUTHOR_NAME='Owned fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
                        GIT_COMMITTER_NAME='Owned fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid',
                        GIT_AUTHOR_DATE='2026-01-01T00:00:00Z', GIT_COMMITTER_DATE='2026-01-01T00:00:00Z')
        self.git('init', '--bare', '--quiet', str(self.repository), in_repo=False)
        self.content = b'#!/bin/sh\necho never-executed\n'
        blob = self.git('hash-object', '-w', '--stdin', input=self.content).strip().decode()
        tree = self.git('mktree', input=f'100755 blob {blob}\tconfigure\n'.encode()).strip().decode()
        commit = self.git('commit-tree', tree, input=b'Owned synthetic fixture\n').strip().decode()
        self.git('update-ref', 'refs/heads/main', commit)
        component = self.audit['components'][0]
        component['source'].update(commit_object_id=commit, tree_object_id=tree)
        self.inputs['components'][0].update(commit=commit, tree=tree)
        listing = self.git('ls-tree', '-r', '-z', '--full-tree', commit)
        component['content_digests'][0]['value'] = hashlib.sha256(listing).hexdigest()
        (self.repository.parent / 'tree-listing.z').write_bytes(listing)
        self.write_inputs()

    def git(self, *argv, input=None, in_repo=True):
        command = [shutil.which('git'), '-c', 'core.hooksPath=/dev/null']
        if in_repo:
            command += ['-C', str(self.repository)]
        run = subprocess.run(command + list(argv), input=input, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, env=self.env, timeout=10)
        self.assertEqual(run.returncode, 0, run.stderr.decode())
        return run.stdout

    def write_inputs(self):
        audit_path = self.root / 'runtime/sources/manifest.json'
        audit_path.write_bytes(common.encoded(self.audit))
        self.inputs['audit_ref']['sha256'] = common.sha256(audit_path)
        path = self.root / 'runtime/wine/inputs.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(common.encoded(self.inputs))

    def prepare(self):
        return prepare.prepare('runtime/wine/inputs.json', '.build/task1-sources/inputs',
                               '.build/task4/inputs', self.root)

    def snapshot(self):
        return {str(p.relative_to(self.root)): common.sha256(p) for p in self.root.rglob('*')
                if p.is_file() and not p.is_relative_to(self.root / '.build/task4')}

    def test_materialization_preserves_cache_audit_and_executable_bytes(self):
        before = self.snapshot()
        result = self.prepare()
        self.assertEqual(self.snapshot(), before)
        source = self.root / '.build/task4/inputs/wine/configure'
        self.assertEqual(source.read_bytes(), self.content)
        self.assertEqual(source.stat().st_mode & 0o777, 0o755)
        component = result['components'][0]
        self.assertEqual(component['file_count'], 1)
        manifest = self.root / '.build/task4/inputs/wine-files.json'
        self.assertEqual(common.sha256(manifest), component['files_manifest']['sha256'])
        self.assertEqual(json.loads(manifest.read_text())['files'][0]['sha256'], common.sha256(source))
        self.assertTrue(result['preparation_only'])
        self.assertFalse(result['runtime_qualified'])
        self.assertEqual(prepare.verify_prepared(source.parent.parent, result['inputs_ref']['sha256']), result)

    def test_prepared_record_identity_and_manifest_are_required(self):
        result = self.prepare()
        output = self.root / '.build/task4/inputs'
        with self.assertRaisesRegex(common.Error, 'prepared_inputs_mismatch'):
            prepare.verify_prepared(output, '0' * 64)
        prepared_path = output / 'prepared.json'
        original = prepared_path.read_bytes()
        for field, bad in [('schema_version', True), ('components', result['components'] * 2),
                           ('runtime_qualified', True)]:
            record = copy.deepcopy(result)
            record[field] = bad
            prepared_path.write_bytes(common.encoded(record))
            with self.subTest(field=field), self.assertRaises(common.Error):
                prepare.verify_prepared(output)
            prepared_path.write_bytes(original)
        manifest_path = output / 'wine-files.json'
        original_manifest = manifest_path.read_bytes()
        manifest_path.write_bytes(original_manifest + b' ')
        with self.assertRaisesRegex(common.Error, 'prepared_manifest_digest'):
            prepare.verify_prepared(output)
        manifest = json.loads(original_manifest)
        manifest['schema_version'] = 2
        manifest_path.write_bytes(common.encoded(manifest))
        result['components'][0]['files_manifest']['sha256'] = common.sha256(manifest_path)
        prepared_path.write_bytes(common.encoded(result))
        with self.assertRaisesRegex(common.Error, 'unsupported_record_version'):
            prepare.verify_prepared(output)

    def test_materialized_bytes_modes_links_extra_and_missing_files_rejected(self):
        self.prepare()
        output = self.root / '.build/task4/inputs'
        source = output / 'wine/configure'
        for mutation in ['bytes', 'mode', 'symlink', 'extra', 'extra_directory', 'missing']:
            source.write_bytes(self.content)
            source.chmod(0o755)
            extra = output / 'wine/unexpected'
            if mutation == 'bytes':
                source.write_bytes(b'!' + self.content[1:])
            elif mutation == 'mode':
                source.chmod(0o644)
            elif mutation == 'symlink':
                source.unlink()
                source.symlink_to(self.root / 'runtime/wine/inputs.json')
            elif mutation == 'extra':
                extra.write_bytes(b'owned extra')
            elif mutation == 'extra_directory':
                extra.mkdir()
            else:
                source.unlink()
            with self.subTest(mutation=mutation), self.assertRaises(common.Error):
                prepare.verify_prepared(output)
            if source.is_symlink():
                source.unlink()
            if extra.is_dir():
                extra.rmdir()
            elif extra.exists():
                extra.unlink()
        source.write_bytes(self.content)
        source.chmod(0o755)
        self.assertTrue(prepare.verify_prepared(output)['preparation_only'])

    def test_listing_digest_must_describe_the_manifest(self):
        result = self.prepare()
        output = self.root / '.build/task4/inputs'
        result['components'][0]['tree_listing_sha256'] = '0' * 64
        (output / 'prepared.json').write_bytes(common.encoded(result))
        with self.assertRaisesRegex(common.Error, 'prepared_selected_source'):
            prepare.verify_prepared(output)

    def test_changed_manifest_cannot_retarget_original_tree(self):
        result = self.prepare()
        output = self.root / '.build/task4/inputs'
        manifest_path = output / 'wine-files.json'
        manifest = json.loads(manifest_path.read_bytes())
        replacement = b'changed' + self.content[7:]
        manifest['files'][0]['git_blob'] = git_blob(replacement)
        manifest['files'][0]['sha256'] = hashlib.sha256(replacement).hexdigest()
        (output / 'wine/configure').write_bytes(replacement)
        manifest_path.write_bytes(common.encoded(manifest))
        result['components'][0]['files_manifest']['sha256'] = common.sha256(manifest_path)
        (output / 'prepared.json').write_bytes(common.encoded(result))
        with self.assertRaisesRegex(common.Error, 'prepared_tree_identity'):
            prepare.verify_prepared(output)

    def test_recomputed_prepared_tree_cannot_replace_selected_input(self):
        result = self.prepare()
        output = self.root / '.build/task4/inputs'
        manifest_path = output / 'wine-files.json'
        manifest = json.loads(manifest_path.read_bytes())
        replacement = b'changed' + self.content[7:]
        row = manifest['files'][0]
        row['git_blob'] = git_blob(replacement)
        row['sha256'] = hashlib.sha256(replacement).hexdigest()
        (output / 'wine/configure').write_bytes(replacement)
        manifest_path.write_bytes(common.encoded(manifest))
        component = result['components'][0]
        component['files_manifest']['sha256'] = common.sha256(manifest_path)
        component['tree'] = prepare._manifest_tree(manifest['files'])
        listing = (row['mode'] + ' blob ' + row['git_blob'] + '\t' + row['path']).encode() + b'\0'
        component['tree_listing_sha256'] = hashlib.sha256(listing).hexdigest()
        (output / 'prepared.json').write_bytes(common.encoded(result))
        with self.assertRaisesRegex(common.Error, 'prepared_selected_source'):
            prepare.verify_prepared(output, result['inputs_ref']['sha256'])
        self.assertEqual(result['inputs_ref']['sha256'], common.sha256(self.root / 'runtime/wine/inputs.json'))

    def test_manifest_nested_tree_identity_matches_git_ordering(self):
        blob = git_blob(self.content)
        subtree = self.git('mktree', input=f'100644 blob {blob}\tfile.c\n'.encode()).strip().decode()
        root_tree = self.git('mktree', input=(f'100644 blob {blob}\ta.c\n040000 tree {subtree}\ta\n'
                                             f'100755 blob {blob}\ta0\n').encode()).strip().decode()
        rows = [{'path': path, 'mode': mode, 'git_blob': blob} for path, mode in
                [('a.c', '100644'), ('a/file.c', '100644'), ('a0', '100755')]]
        self.assertEqual(prepare._manifest_tree(rows), root_tree)

    def test_existing_destination_is_not_replaced(self):
        output = self.root / '.build/task4/inputs'
        output.mkdir(parents=True)
        sentinel = output / 'keep'
        sentinel.write_bytes(b'preserve')
        before = self.snapshot()
        with self.assertRaisesRegex(common.Error, 'output_not_empty'):
            self.prepare()
        self.assertEqual(sentinel.read_bytes(), b'preserve')
        self.assertEqual(self.snapshot(), before)

    def test_symlink_output_and_broad_paths_are_rejected(self):
        outside = self.root / 'outside'
        outside.mkdir()
        (self.root / '.build/task4').symlink_to(outside)
        with self.assertRaisesRegex(common.Error, 'symlink_output'):
            self.prepare()
        self.assertEqual(list(outside.iterdir()), [])
        for path in ['.build/task4', '.build/task4/../inputs', '/tmp/inputs', '.build/task4/a/b']:
            with self.subTest(path=path), self.assertRaises(common.Error):
                prepare.output_path(self.root, path)

    def test_wrong_tree_and_missing_commit_fail_before_output(self):
        for field, wrong in [('tree', 'f' * 40), ('commit', 'e' * 40)]:
            original = copy.deepcopy((self.inputs, self.audit))
            self.inputs['components'][0][field] = wrong
            self.audit['components'][0]['source'][field + '_object_id'] = wrong
            self.write_inputs()
            with self.subTest(field=field), self.assertRaises(common.Error):
                self.prepare()
            self.assertFalse((self.root / '.build/task4/inputs').exists())
            self.inputs, self.audit = original
            self.write_inputs()

    def test_changed_cached_listing_and_unsafe_git_configuration_fail(self):
        path = self.repository.parent / 'tree-listing.z'
        listing = path.read_bytes()
        path.write_bytes(listing + b'changed')
        with self.assertRaisesRegex(common.Error, 'cached_listing_mismatch'):
            self.prepare()
        path.write_bytes(listing)
        config = self.repository / 'config'
        config.write_text(config.read_text() + '\n[include]\n path = /outside/config\n')
        with self.assertRaisesRegex(common.Error, 'unsafe_git_config'):
            self.prepare()
        self.assertFalse((self.root / '.build/task4/inputs').exists())

    def test_git_export_transformation_cannot_silently_remove_source(self):
        blob = self.git('hash-object', '-w', '--stdin', input=b'configure export-ignore\n').strip().decode()
        source_blob = git_blob(self.content)
        tree = self.git('mktree', input=f'100644 blob {blob}\t.gitattributes\n100755 blob {source_blob}\tconfigure\n'.encode()).strip().decode()
        commit = self.git('commit-tree', tree, input=b'Owned export-ignore fixture\n').strip().decode()
        self.inputs['components'][0].update(commit=commit, tree=tree)
        self.audit['components'][0]['source'].update(commit_object_id=commit, tree_object_id=tree)
        listing = self.git('ls-tree', '-r', '-z', '--full-tree', commit)
        self.audit['components'][0]['content_digests'][0]['value'] = hashlib.sha256(listing).hexdigest()
        (self.repository.parent / 'tree-listing.z').write_bytes(listing)
        self.write_inputs()
        with self.assertRaisesRegex(common.Error, 'archive_missing_files'):
            self.prepare()
        self.assertFalse((self.root / '.build/task4/inputs/prepared.json').exists())


if __name__ == '__main__':
    unittest.main()
