"""Original disposable Stage 1 fixtures; no upstream/game runtime execution."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import zlib

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / 'tools/dxmt'
sys.path.insert(0, str(TOOLS))
from common import digest, encoded, producer_hashes
import prepare
import check


def obj(repository, kind, content):
    raw = kind.encode() + b' ' + str(len(content)).encode() + b'\0' + content
    value = hashlib.sha1(raw).hexdigest()
    path = repository / 'objects' / value[:2] / value[2:]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(zlib.compress(raw))
    return value


def bare(cache, name, files, links=None, modes=None):
    repository = cache / name / 'repo.git'
    repository.mkdir(parents=True)
    (repository / 'config').write_text('[core]\n\tbare = true\n\trepositoryformatversion = 0\n')
    (repository / 'refs').mkdir()
    (repository / 'HEAD').write_text('ref: refs/heads/main\n')
    entries, listing = [], []
    for path, data in files.items():
        blob = obj(repository, 'blob', data)
        entries.append((path, (modes or {}).get(path, '100644'), blob, 'blob'))
    for path, commit in (links or {}).items():
        entries.append((path, '160000', commit, 'commit'))
    def make_tree(rows):
        names = {}
        for path, mode, blob, kind in rows:
            first, _, rest = path.partition('/')
            if rest:
                names.setdefault(first, []).append((rest, mode, blob, kind))
            else:
                names[first] = (mode, blob, kind)
        result = []
        for name, row in names.items():
            if isinstance(row, list):
                result.append((name, '40000', make_tree(row)))
            else:
                result.append((name, row[0], row[1]))
        raw = b''
        for name, mode, blob in sorted(result, key=lambda r: (r[0] + ('/' if r[1] == '40000' else '')).encode()):
            raw += mode.encode() + b' ' + name.encode() + b'\0' + bytes.fromhex(blob)
        return obj(repository, 'tree', raw)
    tree = make_tree(entries)
    for path, mode, blob, kind in sorted(entries):
        listing.append(f'{mode} {kind} {blob}\t{path}'.encode() + b'\0')
    commit = obj(repository, 'commit', f'tree {tree}\nauthor Fixture <fixture@example.invalid> 0 +0000\ncommitter Fixture <fixture@example.invalid> 0 +0000\n\nOriginal synthetic source fixture\n'.encode())
    (repository / 'refs/heads').mkdir()
    (repository / 'refs/heads/main').write_text(commit + '\n')
    listing = b''.join(listing)
    (cache / name / 'tree.z').write_bytes(listing)
    return {'id': name, 'url': 'https://example.invalid/' + name + '.git', 'commit': commit, 'tree': tree,
            'cache_path': name + '/repo.git', 'listing': {'cache_path': name + '/tree.z', 'value': digest(listing), 'size_bytes': len(listing)},
            'materialize': False, 'source_path': None,
            'terms': [{'path': p, 'git_blob': b, 'sha256': digest(files[p]), 'size_bytes': len(files[p])}
                      for p, mode, b, k in entries if k == 'blob' and mode in ['100644', '100755'] and '%' not in p], 'source_checks': []}


class Fixture:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pear-dxmt-unit-')
        self.root = Path(self.temp.name).resolve()
        self.cache = self.root / 'cache'
        self.cache.mkdir()
        for path in ['tools/dxmt/common.py', 'tools/dxmt/prepare.py', 'tools/dxmt/check.py', 'tools/dxmt/verify.py',
                     'tools/wine/common.py', 'tools/sources/validate_inventory.py']:
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, target)
        # Names follow the approved policy; all bytes below are original fixtures.
        selected = json.loads((ROOT / 'runtime/dxmt/inputs.json').read_text())
        candidates = {c['id']: c for c in selected['components']}
        components = []
        def component(name, links=None):
            original = candidates[name]
            files = {r['path']: ('Original selected source fixture: ' + name + '/' + r['path'] + '\n').encode()
                     for r in original['terms'] + original['source_checks']}
            modes = None
            if name == 'llvm-dxmt':
                files.update({'unused-link': b'../not-extracted', 'zir_%for.cond': b'Original literal IR-name fixture.\n'})
                modes = {'unused-link': '120000'}
            c = bare(self.cache, name, files, links, modes)
            pins = {row['path']: row for row in c['terms']}
            c['terms'] = [pins[row['path']] for row in original['terms']]
            c['source_checks'] = [pins[row['path']] for row in original['source_checks']]
            c.update(materialize=original['materialize'], source_path=original['source_path'])
            return c
        directx = component('dxmt-directx')
        nvapi = component('dxmt-nvapi')
        dxmt = component('dxmt-upstream', {'include/native/directx': directx['commit'], 'external/nvapi': nvapi['commit']})
        components = [dxmt, directx, nvapi] + [component(name) for name in candidates if name not in ['dxmt-upstream', 'dxmt-directx', 'dxmt-nvapi']]
        audit = {'schema_version': 1, 'record_kind': 'source_audit', 'components': [
            {'component_id': c['id'], 'source': {'url': c['url'], 'commit_object_id': c['commit'], 'tree_object_id': c['tree']},
             'acquisition': {'cache_path': c['cache_path']}, 'content_digests': [{'scope': 'git_tree_listing_bytes', **c['listing']}]}
            for c in components]}
        ap = self.root / 'runtime/sources/manifest.json'
        ap.parent.mkdir(parents=True)
        ap.write_bytes(encoded(audit))
        series = self.root / 'runtime/wine/patches/series.json'
        series.parent.mkdir(parents=True)
        series.write_bytes(encoded({'original_fixture': True}))
        self.inputs = {'schema_version': 1, 'record_kind': 'dxmt_build_inputs', 'scope': 'dxmt_component',
            'audit_ref': {'path': 'runtime/sources/manifest.json', 'sha256': digest(encoded(audit))},
            'components': components,
            'gitlinks': [{'parent': 'dxmt-upstream', 'path': 'include/native/directx', 'component': 'dxmt-directx', 'commit': directx['commit'], 'enabled': True, 'reason': 'required synthetic header'},
                         {'parent': 'dxmt-upstream', 'path': 'external/nvapi', 'component': 'dxmt-nvapi', 'commit': nvapi['commit'], 'enabled': False, 'reason': 'explicit disabled fixture input'}],
            'wine_baseline': {'patch_series': {'path': 'runtime/wine/patches/series.json', 'sha256': digest(series.read_bytes())},
                'source_manifest_sha256': digest(b'fixture source manifest'),
                'build_refs': {r: {'sha256': digest(r.encode()), 'installed_manifest_sha256': digest((r + '-files').encode())} for r in ['native', 'companion']}},
            'limits': {'max_listing_bytes': 33554432, 'max_blob_bytes': 33554432, 'max_materialized_bytes': 268435456}}
        ip = self.root / 'runtime/dxmt/inputs.json'
        ip.parent.mkdir(parents=True)
        ip.write_bytes(encoded(self.inputs))
        self.input_path = 'runtime/dxmt/inputs.json'

    def refresh(self):
        (self.root / self.input_path).write_bytes(encoded(self.inputs))

    def derive(self, name='prepared'):
        self.refresh()
        return prepare.prepare(self.input_path, self.cache, '.build/task7/' + name, self.root)

    def close(self):
        self.temp.cleanup()
