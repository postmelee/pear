#!/usr/bin/env python3
"""Task-local build tools and bounded native inspection; no game/runtime execution."""
from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path, PurePosixPath
import shlex
import shutil
import sys
import tarfile
import time
import unicodedata
import urllib.request
if __package__:
    from .common import Error, REPO, bounded_command, load_json, need, operation_output, read_relative, record, relative, sha256, write_json
    from . import byte_readers, prepare as source_preparation
else:
    from common import Error, REPO, bounded_command, load_json, need, operation_output, read_relative, record, relative, sha256, write_json
    import byte_readers
    import prepare as source_preparation

MAX_DOWNLOAD = 128 * 1024 * 1024
MAX_EXPANSION = 400 * 1024 * 1024
MAX_MEMBERS = 25000
CMAKE_SHA = 'd1449f969c54d5c00886d5b643340d493dfb3c81cb39ee29b35453395c11ebf7'
CMAKE_SUM_SHA = '8d08ce0586bf40ff6b80e46fffe2db8855bab5b030db8b3782f11f68b6274ad8'
NINJA_COMMIT = '79feac0f3e3bc9da9effc586cd5fea41e7550051'
CMAKE_BASE = 'https://github.com/Kitware/CMake/releases/download/v3.31.8/'
CMAKE_ROOT = 'cmake-3.31.8-macos-universal'
HELPERS = ('tools/fex/common.py', 'tools/fex/byte_readers.py', 'tools/fex/prepare.py',
           'tools/sources/validate_inventory.py', 'tools/wine/toolchain.py', 'tools/wine/common.py')
GIT = ['/usr/bin/git', '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false',
       '-c', 'protocol.file.allow=never', '-c', 'protocol.ext.allow=never', '-c', 'gc.auto=0']
BASE_ENV = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'LC_ALL': 'C',
            'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null',
            'GIT_CONFIG_SYSTEM': '/dev/null', 'GIT_TERMINAL_PROMPT': '0',
            'GIT_NO_REPLACE_OBJECTS': '1', 'GIT_ATTR_NOSYSTEM': '1'}


def wine_readers():
    """Reuse byte/archive algorithms without importing Wine task4 entrypoints."""
    return byte_readers


def keys(value, expected, code):
    need(isinstance(value, dict) and set(value) == set(expected), code)


def fetch(url, path, expected_sha, max_bytes=MAX_DOWNLOAD, cache=None):
    need(url in (CMAKE_BASE+'cmake-3.31.8-SHA-256.txt', CMAKE_BASE+CMAKE_ROOT+'.tar.gz'), 'unreviewed_tool_origin')
    need(not Path(path).exists(), 'destination_exists')
    if cache is not None and Path(cache).is_file():
        need(Path(cache).stat().st_size <= max_bytes and sha256(cache) == expected_sha, 'cached_tool_digest_mismatch')
        shutil.copyfile(cache, path)
        # The copied bytes, rather than a prior cache observation, are consumed.
        need(Path(path).stat().st_size <= max_bytes and sha256(path) == expected_sha, 'copied_tool_digest_mismatch')
        return {'url': url, 'sha256': expected_sha, 'size_bytes': Path(path).stat().st_size, 'reused_verified_cache': True}
    count = 0
    started = time.monotonic()
    digest = hashlib.sha256()
    request = urllib.request.Request(url, headers={'User-Agent': 'Pear-Stage1-Tools/1'})
    with urllib.request.urlopen(request, timeout=30) as source, Path(path).open('xb') as output:
        need(source.geturl().startswith('https://'), 'non_https_redirect')
        length = source.headers.get('Content-Length')
        need(length is None or int(length) <= max_bytes, 'download_size_limit')
        while block := source.read(1024 * 1024):
            need(time.monotonic() - started <= 180, 'download_timeout')
            count += len(block)
            need(count <= max_bytes, 'download_size_limit')
            digest.update(block)
            output.write(block)
    need(digest.hexdigest() == expected_sha, 'tool_download_digest_mismatch')
    return {'url': url, 'sha256': digest.hexdigest(), 'size_bytes': count}


def resolve_alias(path, links, names, directories):
    """Resolve raw components in filesystem order, including '..' after aliases."""
    pending = path.split('/')
    stack, followed = [], set()
    while pending:
        part = pending.pop(0)
        if part in ('', '.'):
            continue
        if part == '..':
            need(bool(stack), 'archive_link_escape')
            stack.pop()
            continue
        need('\\' not in part and '\0' not in part, 'unsafe_archive_link')
        stack.append(part)
        prefix = '/'.join(stack)
        if prefix in links:
            need(prefix not in followed, 'archive_link_cycle')
            followed.add(prefix)
            need(len(followed) <= 64, 'archive_link_resolution_limit')
            kind, target = links[prefix]
            stack.pop()
            if kind == 'hard':
                stack = []
            pending = target.split('/') + pending
        elif pending:
            # file/.. is not a directory traversal on a real filesystem.
            need(prefix in directories, 'archive_link_not_directory')
    target = '/'.join(stack)
    need(target == '' or target in names or target in directories, 'archive_dangling_link')
    return target


def archive_graph(archive, expected_root, budget):
    """Validate bounded members and framework aliases before extraction writes."""
    need(type(budget) is int and 0 <= budget <= MAX_EXPANSION, 'invalid_archive_budget')
    rows, names, links, directories, aliases = [], set(), {}, set(), {}
    regular, total, root_seen, count = set(), 0, False, 0
    # Avoid allocating an unbounded getmembers() list before checking the count.
    for member in archive:
        count += 1
        need(count <= MAX_MEMBERS, 'archive_member_limit')
        parts = relative(member.name.rstrip('/'))
        need(parts[0] == expected_root, 'archive_root_mismatch')
        if len(parts) == 1:
            need(member.isdir() and not root_seen, 'invalid_archive_root')
            root_seen = True
            continue
        rel = '/'.join(parts[1:])
        need(rel not in names, 'duplicate_archive_member')
        names.add(rel)
        need(member.isfile() or member.isdir() or member.issym() or member.islnk(), 'special_archive_member')
        for i in range(1, len(parts)):
            prefix = '/'.join(parts[1:i+1])
            key = unicodedata.normalize('NFD', prefix).casefold()
            need(key not in aliases or aliases[key] == prefix, 'archive_path_alias')
            aliases[key] = prefix
        directories.update(str(p) for p in PurePosixPath(rel).parents if str(p) != '.')
        if member.isdir():
            directories.add(rel)
        elif member.isfile():
            regular.add(rel)
            need(member.size >= 0 and type(member.mtime) is int and 0 <= member.mtime <= 2**32-1,
                 'invalid_archive_file_metadata')
            total += member.size
            need(total <= budget, 'archive_expansion_limit')
        elif member.issym():
            need(member.linkname and not member.linkname.startswith('/') and '\\' not in member.linkname
                 and '\0' not in member.linkname, 'unsafe_archive_link')
            links[rel] = ('sym', member.linkname)
        else:
            target = relative(member.linkname)
            need(target[0] == expected_root and len(target) > 1, 'unsafe_archive_hardlink')
            links[rel] = ('hard', '/'.join(target[1:]))
        rows.append((member, rel))
    for _, rel in rows:
        parents = {str(p) for p in PurePosixPath(rel).parents if str(p) != '.'}
        need(not parents & set(links), 'archive_link_parent')
        need(not parents & regular, 'archive_file_parent')
    for origin, (kind, _) in links.items():
        target = resolve_alias(origin, links, names, directories)
        need(kind != 'hard' or target in regular, 'unsafe_archive_hardlink')
    return rows, total


def archive_inventory(archive_path, expected_root, budget=MAX_EXPANSION):
    """Reconstruct extracted payload identity from independently pinned bytes."""
    rows = []
    with tarfile.open(archive_path, 'r:*') as archive:
        members, _ = archive_graph(archive, expected_root, budget)
        for member, rel in members:
            if member.issym():
                rows.append({'path': rel, 'symlink': member.linkname})
            elif member.isfile():
                digest = hashlib.sha256()
                count = 0
                with archive.extractfile(member) as source:
                    while block := source.read(1024 * 1024):
                        count += len(block)
                        need(count <= member.size, 'archive_file_size_mismatch')
                        digest.update(block)
                need(count == member.size, 'archive_file_size_mismatch')
                rows.append({'path': rel, 'sha256': digest.hexdigest(), 'size_bytes': count,
                             'mode': 0o755 if member.mode & 0o111 else 0o644})
            elif member.islnk():
                # A hardlink is a regular extracted file; source Git archives do
                # not contain them and CMake hardlinks are refused here until
                # their payload identity is explicitly accounted for.
                raise Error('unaccounted_payload_hardlink')
    return sorted(rows, key=lambda row: row['path'])


def extract(archive_path, destination, expected_root, budget=MAX_EXPANSION):
    need(not destination.exists(), 'destination_exists')
    with tarfile.open(archive_path, 'r:*') as archive:
        members, total = archive_graph(archive, expected_root, budget)
        need(shutil.disk_usage(destination.parent).free >= total + 256 * 1024**2, 'insufficient_extraction_space')
        destination.mkdir()
        for member, rel in members:
            path = destination.joinpath(*relative(rel))
            path.parent.mkdir(parents=True, exist_ok=True)
            if member.isdir():
                path.mkdir(exist_ok=True)
            elif member.isfile():
                with archive.extractfile(member) as source, path.open('xb') as output:
                    shutil.copyfileobj(source, output, 1024 * 1024)
                need(path.stat().st_size == member.size, 'archive_file_size_mismatch')
                path.chmod(0o755 if member.mode & 0o111 else 0o644)
                os.utime(path, (member.mtime, member.mtime), follow_symlinks=False)
        for member, rel in members:
            path = destination.joinpath(*relative(rel))
            if member.issym():
                path.symlink_to(member.linkname)
            elif member.islnk():
                target = destination.joinpath(*relative(member.linkname)[1:])
                need(target.is_file() and not target.is_symlink(), 'unsafe_archive_hardlink')
                os.link(target, path)
    return total


def files(root):
    rows, aliases = [], {}
    for directory, dirs, names in os.walk(root, followlinks=False):
        for name in sorted(names + [n for n in dirs if (Path(directory)/n).is_symlink()]):
            path = Path(directory)/name
            rel = path.relative_to(root).as_posix()
            relative(rel)
            key = unicodedata.normalize('NFD', rel).casefold()
            need(key not in aliases, 'tool_path_alias')
            aliases[key] = rel
            need(len(rows) < MAX_MEMBERS, 'tool_inventory_limit')
            if path.is_symlink():
                target = os.readlink(path)
                need(path.resolve(strict=True).is_relative_to(root.resolve()), 'tool_link_escape')
                rows.append({'path': rel, 'symlink': target})
            else:
                need(path.is_file(), 'nonregular_tool_output')
                rows.append({'path': rel, 'sha256': sha256(path), 'size_bytes': path.stat().st_size,
                             'mode': path.stat().st_mode & 0o777})
    return sorted(rows, key=lambda row: row['path'])


def command(argv, root, ident, commands, env=None, timeout=120, cwd=None):
    logs = root/'logs'/ident
    logs.mkdir(parents=True)
    work = cwd or root
    argv = [str(x) for x in argv]
    result = bounded_command(argv, cwd=work, timeout=timeout, max_output=512*1024, env=env)
    row = {'id': ident, 'argv': argv, 'cwd': str(work), 'environment': dict(env or {}),
           'exit_code': result['returncode'], 'elapsed_ms': result['elapsed_ms'], 'logs': {}}
    for name in ('stdout', 'stderr'):
        path = logs/name
        path.write_bytes(result[name])
        row['logs'][name] = {'path': path.relative_to(root).as_posix(), 'sha256': sha256(path),
                             'size_bytes': path.stat().st_size}
    commands.append(row)
    need(result['returncode'] == 0, 'tool_command_failed:'+ident)
    return result


def lock_pins(lock):
    need(lock.get('scope') == 'fex_component' and lock.get('runtime_qualified') is False, 'wrong_component_scope')
    cmake, ninja = lock['build_tools']['cmake'], lock['build_tools']['ninja']
    need(cmake['version'] == '3.31.8' and cmake['sha256'] == CMAKE_SHA
         and cmake['checksum_sha256'] == CMAKE_SUM_SHA and cmake['origin'] == CMAKE_BASE.rsplit('/download/', 1)[0]+'/tag/v3.31.8'
         and ninja['version'] == '1.13.1' and ninja['commit'] == NINJA_COMMIT
         and ninja['origin'] == 'https://github.com/ninja-build/ninja.git', 'unreviewed_build_tool_pin')


def receipt_shape(data):
    """Reject missing operations and scope inflation before reading any payload."""
    keys(data, ('schema_version', 'record_kind', 'scope', 'toolchain_sha256', 'producer_sha256',
                'helper_sha256', 'downloads', 'inventories', 'tools', 'commands', 'runtime_execution',
                'ninja_source', 'native_build', 'passed'), 'build_tools_record_fields')
    need(data['scope'] == 'fex_component' and data['passed'] is True and data['runtime_execution'] is False,
         'unqualified_build_tools')
    keys(data['helper_sha256'], HELPERS, 'build_tools_helper_closure')
    keys(data['tools'], ('cmake', 'ninja'), 'build_tools_executable_closure')
    need(isinstance(data['inventories'], list) and len(data['inventories']) == 2
         and {r.get('root') for r in data['inventories'] if isinstance(r, dict)} == {'cmake', 'ninja-source'},
         'build_tools_inventory_closure')
    need(isinstance(data['downloads'], list) and len(data['downloads']) == 2
         and {r.get('path') for r in data['downloads'] if isinstance(r, dict)}
         == {'downloads/cmake-SHA-256.txt', 'downloads/cmake.tar.gz'}, 'build_tools_download_closure')
    source = data['ninja_source']
    keys(source, ('commit', 'tree', 'source_root', 'archive', 'files', 'notice', 'reused_cache', 'repository'), 'ninja_source_fields')
    need(source['commit'] == NINJA_COMMIT and source['source_root'] == 'ninja-source'
         and type(source['reused_cache']) is bool, 'ninja_source_identity')
    required = {'cmake.version', 'sdk.path', 'sdk.version', 'ninja.commit', 'ninja.tree-id',
                'ninja.commit-object', 'ninja.tree', 'ninja.archive', 'ninja.bootstrap', 'ninja.version'}
    if not source['reused_cache']:
        required |= {'ninja.init', 'ninja.fetch'}
    commands = data['commands']
    need(isinstance(commands, list) and len(commands) == len(required)
         and {r.get('id') for r in commands if isinstance(r, dict)} == required, 'build_tools_command_closure')
    keys(data['native_build'], ('compiler', 'xcrun', 'python', 'sdk', 'environment'), 'native_build_fields')


def ninja_entries(commit_bytes, listing_bytes, tree, expected_commit=NINJA_COMMIT):
    """Bind the full regular-file tree to the pinned Git commit's exact bytes."""
    need(hashlib.sha1(f'commit {len(commit_bytes)}\0'.encode()+commit_bytes).hexdigest() == expected_commit,
         'ninja_commit_object_mismatch')
    need(commit_bytes.startswith(('tree '+tree+'\n').encode()), 'ninja_commit_tree_mismatch')
    entries = source_preparation.tree_entries(listing_bytes)
    need(all(r['mode'] in ('100644', '100755') for r in entries.values()), 'unsupported_ninja_tree_entry')
    need(source_preparation.tree_identity(entries) == tree, 'ninja_tree_identity_mismatch')
    return entries


def ninja_archive(archive_path, entries, source=None):
    """Compare each archive blob/mode and optional materialized source bytes."""
    rows = []
    with tarfile.open(archive_path, 'r:*') as archive:
        members, _ = archive_graph(archive, 'ninja-source', 32*1024**2)
        ordinary = [(member, path) for member, path in members if not member.isdir()]
        need({path for _, path in ordinary} == set(entries), 'ninja_archive_file_closure')
        for member, path in ordinary:
            need(member.isfile(), 'unsupported_ninja_archive_entry')
            content = archive.extractfile(member).read(member.size+1)
            need(len(content) == member.size, 'archive_file_size_mismatch')
            entry = entries[path]
            blob = hashlib.sha1(f'blob {len(content)}\0'.encode()+content).hexdigest()
            mode = 0o755 if entry['mode'] == '100755' else 0o644
            need(blob == entry['git_object'] and (0o755 if member.mode & 0o111 else 0o644) == mode,
                 'ninja_archive_blob_mismatch')
            row = {'path': path, 'sha256': hashlib.sha256(content).hexdigest(), 'size_bytes': len(content),
                   'mode': mode, 'git_blob': blob}
            if source is not None:
                actual = source.joinpath(*relative(path))
                need(sha256(actual) == row['sha256'] and actual.stat().st_size == len(content)
                     and actual.stat().st_mode & 0o777 == mode, 'ninja_materialized_source_changed')
            rows.append(row)
    return sorted(rows, key=lambda row: row['path'])


def native_tool(row):
    path = Path(row['path'])
    need(path.is_absolute() and sha256(path.resolve(strict=True)) == row['sha256'], 'native_build_tool_changed')
    info = wine_readers().inspect_macho(path)
    need(info['selected_cpu'] == wine_readers().MACH_ARM64 and info['filetype'] == 2, 'native_build_tool_not_arm64')
    return info


def sdk_matches(selected, locked):
    need(isinstance(selected, str) and Path(selected).is_absolute() and Path(selected).is_dir()
         and Path(locked).is_dir() and Path(selected).resolve(strict=True) == Path(locked).resolve(strict=True),
         'selected_sdk_mismatch')


def verify_tools(root, toolchain_path):
    root = operation_output(root, require_empty=False, create=False)
    need(not (root/'prepare-failed.json').exists(), 'failed_tool_preparation')
    data = record(load_json(root/'prepared.json'), 'fex_tools_prepared')
    receipt_shape(data)
    lock = record(load_json(toolchain_path), 'fex_toolchain')
    lock_pins(lock)
    need(data['toolchain_sha256'] == sha256(toolchain_path), 'toolchain_identity_mismatch')
    need(data['producer_sha256'] == sha256(Path(__file__).resolve()), 'tools_producer_mismatch')
    for name, digest in data['helper_sha256'].items():
        need(sha256(REPO.joinpath(*relative(name))) == digest, 'tools_helper_changed')
    for row in data['inventories']:
        keys(row, ('root', 'files'), 'build_tools_inventory_fields')
        need(files(root/row['root']) == row['files'], 'build_tool_inventory_changed')
    artifacts = {row['path']: row for row in data['downloads']}
    for path, digest, url in (('downloads/cmake-SHA-256.txt', CMAKE_SUM_SHA, CMAKE_BASE+'cmake-3.31.8-SHA-256.txt'),
                              ('downloads/cmake.tar.gz', CMAKE_SHA, CMAKE_BASE+CMAKE_ROOT+'.tar.gz')):
        row = artifacts[path]
        need(set(row) in ({'path', 'url', 'sha256', 'size_bytes'}, {'path', 'url', 'sha256', 'size_bytes', 'reused_verified_cache'}),
             'build_tools_download_fields')
        need(row['url'] == url and row['sha256'] == digest and type(row['size_bytes']) is int
             and 0 < row['size_bytes'] <= MAX_DOWNLOAD, 'build_tool_payload_pin')
        need('reused_verified_cache' not in row or row['reused_verified_cache'] is True, 'build_tool_cache_claim')
        actual = read_relative(root, path, MAX_DOWNLOAD)
        need(len(actual) == row['size_bytes'] and hashlib.sha256(actual).hexdigest() == digest, 'build_tool_payload_changed')
    checksum = read_relative(root, 'downloads/cmake-SHA-256.txt', 128*1024).decode()
    need(CMAKE_SHA+'  '+CMAKE_ROOT+'.tar.gz' in checksum.splitlines(), 'publisher_checksum_mismatch')
    need(archive_inventory(root/'downloads/cmake.tar.gz', CMAKE_ROOT) == files(root/'cmake'), 'cmake_payload_inventory_mismatch')
    readers = wine_readers()
    cmake = data['tools']['cmake']
    keys(cmake, ('path', 'sha256', 'native_closure'), 'cmake_record_fields')
    need(cmake['path'] == 'cmake/CMake.app/Contents/bin/cmake', 'cmake_executable_path')
    cmake_path = root/cmake['path']
    need(sha256(cmake_path.resolve()) == cmake['sha256'] and readers.inspect_macho(cmake_path)['filetype'] == 2, 'build_tool_executable_changed')
    closure = readers.inspect_closure(cmake_path, root/'cmake')
    need(closure == cmake['native_closure'] and all(row['selected_cpu'] == readers.MACH_ARM64 for row in closure), 'cmake_native_closure_mismatch')
    native = data['native_build']
    for ident in ('compiler', 'xcrun'):
        expected = lock['native_tools']['clang++' if ident == 'compiler' else 'xcrun']
        need(native[ident] == {'path': expected['path'], 'sha256': expected['sha256']}, 'native_build_input_mismatch')
        native_tool(native[ident])
    keys(native['python'], ('path', 'sha256'), 'bootstrap_interpreter_fields')
    native_tool(native['python'])
    keys(native['sdk'], ('locked_path', 'selected_path', 'version'), 'selected_sdk_fields')
    need(native['sdk']['locked_path'] == lock['sdk']['path'] and native['sdk']['version'] == lock['sdk']['version'], 'selected_sdk_identity')
    sdk_matches(native['sdk']['selected_path'], lock['sdk']['path'])
    environment = native['environment']
    need(isinstance(environment, dict) and set(environment) <= set(BASE_ENV) | {'HOME', 'TMPDIR', 'CXX', 'SDKROOT'}
         and all(environment.get(key) == value for key, value in BASE_ENV.items())
         and environment.get('CXX') == shlex.join(['/usr/bin/arch', '-arm64', native['compiler']['path'], '-isysroot', lock['sdk']['path']])
         and environment.get('SDKROOT') == lock['sdk']['path'], 'native_build_environment_mismatch')
    env = {key: value for key, value in environment.items() if key not in ('CXX', 'SDKROOT')}
    command_rows = {row['id']: row for row in data['commands']}
    stdout = {}
    for ident, row in command_rows.items():
        keys(row, ('id', 'argv', 'cwd', 'environment', 'exit_code', 'elapsed_ms', 'logs'), 'build_tools_command_fields')
        need(row['exit_code'] == 0 and type(row['elapsed_ms']) is int and row['elapsed_ms'] >= 0, 'failed_tool_preparation')
        keys(row['logs'], ('stdout', 'stderr'), 'build_tools_log_closure')
        for name, log in row['logs'].items():
            keys(log, ('path', 'sha256', 'size_bytes'), 'build_tools_log_fields')
            need(log['path'] == 'logs/'+ident+'/'+name and type(log['size_bytes']) is int and 0 <= log['size_bytes'] <= 512*1024,
                 'build_tools_log_path')
            content = read_relative(root, log['path'], 512*1024)
            need(len(content) == log['size_bytes'] and hashlib.sha256(content).hexdigest() == log['sha256'], 'tool_log_changed')
            if name == 'stdout':
                stdout[ident] = content
    source = data['ninja_source']
    repository = source['repository']
    need(isinstance(repository, str) and Path(repository).is_absolute(), 'ninja_repository_path')
    git = GIT+['--git-dir='+repository]
    expected = {
        'cmake.version': ['/usr/bin/arch', '-arm64', str(cmake_path), '--version'],
        'sdk.path': ['/usr/bin/arch', '-arm64', native['xcrun']['path'], '--sdk', 'macosx', '--show-sdk-path'],
        'sdk.version': ['/usr/bin/arch', '-arm64', native['xcrun']['path'], '--sdk', 'macosx', '--show-sdk-version'],
        'ninja.commit': [*git, 'rev-parse', NINJA_COMMIT+'^{commit}'],
        'ninja.tree-id': [*git, 'rev-parse', NINJA_COMMIT+'^{tree}'],
        'ninja.commit-object': [*git, 'cat-file', 'commit', NINJA_COMMIT],
        'ninja.tree': [*git, 'ls-tree', '-r', '-z', NINJA_COMMIT],
        'ninja.archive': [*git, 'archive', '--format=tar', '--prefix=ninja-source/', '--output='+str(root/'ninja.tar'), NINJA_COMMIT],
        'ninja.bootstrap': ['/usr/bin/arch', '-arm64', native['python']['path'], str(root/'ninja-source/configure.py'), '--bootstrap'],
        'ninja.version': ['/usr/bin/arch', '-arm64', str(root/'ninja-source/ninja'), '--version'],
    }
    if not source['reused_cache']:
        need(repository == str(root/'ninja.git'), 'fresh_ninja_repository_scope')
        expected.update({'ninja.init': [*GIT, 'init', '--bare', repository],
                         'ninja.fetch': [*git, 'fetch', '--no-tags', '--depth=1', 'https://github.com/ninja-build/ninja.git', NINJA_COMMIT]})
    for ident, argv in expected.items():
        row = command_rows[ident]
        need(row['argv'] == argv and row['cwd'] == str(root/'ninja-source' if ident == 'ninja.bootstrap' else root)
             and row['environment'] == (environment if ident == 'ninja.bootstrap' else env), 'build_tools_command_recipe')
    need(stdout['cmake.version'].decode().splitlines()[0] == 'cmake version 3.31.8'
         and stdout['ninja.version'].decode().strip() == '1.13.1', 'build_tool_version_mismatch')
    need(stdout['sdk.path'].decode().strip() == native['sdk']['selected_path']
         and stdout['sdk.version'].decode().strip() == lock['sdk']['version'], 'selected_sdk_receipt_mismatch')
    need(stdout['ninja.commit'].decode().strip() == NINJA_COMMIT and stdout['ninja.tree-id'].decode().strip() == source['tree'], 'ninja_source_identity')
    entries = ninja_entries(stdout['ninja.commit-object'], stdout['ninja.tree'], source['tree'])
    artifact = source['archive']
    keys(artifact, ('path', 'sha256', 'size_bytes'), 'ninja_archive_fields')
    need(artifact['path'] == 'ninja.tar' and type(artifact['size_bytes']) is int and 0 < artifact['size_bytes'] <= 32*1024**2,
         'ninja_archive_bounds')
    raw = read_relative(root, 'ninja.tar', 32*1024**2)
    need(len(raw) == artifact['size_bytes'] and hashlib.sha256(raw).hexdigest() == artifact['sha256'], 'ninja_archive_changed')
    need(ninja_archive(root/'ninja.tar', entries, root/'ninja-source') == source['files'], 'ninja_source_manifest_changed')
    notice = source['notice']
    keys(notice, ('path', 'sha256', 'size_bytes'), 'ninja_notice_fields')
    need(notice['path'] == 'COPYING' and any(row['path'] == 'COPYING' and row['sha256'] == notice['sha256']
         and row['size_bytes'] == notice['size_bytes'] for row in source['files']), 'ninja_notice_identity')
    ninja = data['tools']['ninja']
    keys(ninja, ('path', 'sha256', 'architectures', 'selected_cpu', 'subtype', 'filetype', 'dependencies', 'rpaths',
                 'source_commit', 'notice_sha256'), 'ninja_record_fields')
    need(ninja['path'] == 'ninja-source/ninja' and ninja['source_commit'] == NINJA_COMMIT
         and ninja['notice_sha256'] == notice['sha256'], 'ninja_output_identity')
    actual_info = readers.inspect_macho(root/ninja['path'])
    need(actual_info['architectures'] == [readers.MACH_ARM64] and actual_info['filetype'] == 2
         and all(ninja[key] == value for key, value in actual_info.items())
         and sha256(root/ninja['path']) == ninja['sha256'], 'ninja_output_changed')
    return data


def prepare(lock_path, output, artifact_cache=None, source_cache=None):
    lock = record(load_json(lock_path), 'fex_toolchain')
    lock_pins(lock)
    root = operation_output(output)
    data = {'schema_version': 1, 'record_kind': 'fex_tools_prepared', 'scope': 'fex_component',
            'toolchain_sha256': sha256(lock_path), 'producer_sha256': sha256(Path(__file__).resolve()),
            'helper_sha256': {name: sha256(REPO/name) for name in HELPERS}, 'downloads': [],
            'inventories': [], 'tools': {}, 'commands': [], 'runtime_execution': False}
    try:
        env = {key: os.environ[key] for key in ('HOME', 'TMPDIR') if key in os.environ}
        env.update(BASE_ENV)
        readers = wine_readers()
        native = lock['native_tools']
        python = Path(sys.executable).absolute()
        build = {'compiler': {key: native['clang++'][key] for key in ('path', 'sha256')},
                 'xcrun': {key: native['xcrun'][key] for key in ('path', 'sha256')},
                 'python': {'path': str(python), 'sha256': sha256(python.resolve(strict=True))}}
        for ident in ('compiler', 'xcrun', 'python'):
            native_tool(build[ident])
        selected = command(['/usr/bin/arch', '-arm64', build['xcrun']['path'], '--sdk', 'macosx', '--show-sdk-path'],
                           root, 'sdk.path', data['commands'], env)['stdout'].decode().strip()
        sdk_matches(selected, lock['sdk']['path'])
        version = command(['/usr/bin/arch', '-arm64', build['xcrun']['path'], '--sdk', 'macosx', '--show-sdk-version'],
                          root, 'sdk.version', data['commands'], env)['stdout'].decode().strip()
        need(version == lock['sdk']['version'], 'selected_sdk_version_mismatch')
        build['sdk'] = {'locked_path': lock['sdk']['path'], 'selected_path': selected, 'version': version}
        downloads = root/'downloads'
        downloads.mkdir()
        cache = Path(artifact_cache) if artifact_cache else None
        checksum = downloads/'cmake-SHA-256.txt'
        artifact = fetch(CMAKE_BASE+'cmake-3.31.8-SHA-256.txt', checksum, CMAKE_SUM_SHA, 128*1024,
                         cache/'cmake-SHA-256.txt' if cache else None)
        data['downloads'].append({**artifact, 'path': checksum.relative_to(root).as_posix()})
        need(CMAKE_SHA+'  '+CMAKE_ROOT+'.tar.gz' in checksum.read_text().splitlines(), 'publisher_checksum_mismatch')
        payload = downloads/'cmake.tar.gz'
        artifact = fetch(CMAKE_BASE+CMAKE_ROOT+'.tar.gz', payload, CMAKE_SHA,
                         cache=cache/'cmake.tar.gz' if cache else None)
        data['downloads'].append({**artifact, 'path': payload.relative_to(root).as_posix()})
        bundle = root/'cmake'
        extract(payload, bundle, CMAKE_ROOT)
        need(archive_inventory(payload, CMAKE_ROOT) == files(bundle), 'cmake_payload_inventory_mismatch')
        cmake = bundle/'CMake.app/Contents/bin/cmake'
        closure = readers.inspect_closure(cmake, bundle)
        need(readers.inspect_macho(cmake)['filetype'] == 2 and all(row['selected_cpu'] == readers.MACH_ARM64 for row in closure),
             'cmake_native_closure_mismatch')
        data['tools']['cmake'] = {'path': cmake.relative_to(root).as_posix(), 'sha256': sha256(cmake.resolve()), 'native_closure': closure}
        command(['/usr/bin/arch', '-arm64', cmake, '--version'], root, 'cmake.version', data['commands'], env)
        ninja_repo = root/'ninja.git'
        if source_cache is None:
            command([*GIT, 'init', '--bare', ninja_repo], root, 'ninja.init', data['commands'], env)
            command([*GIT, '--git-dir='+str(ninja_repo), 'fetch', '--no-tags', '--depth=1',
                     'https://github.com/ninja-build/ninja.git', NINJA_COMMIT], root, 'ninja.fetch', data['commands'], env, 180)
        else:
            ninja_repo = Path(source_cache).resolve(strict=True)
        # Read-only repository admission rejects helpers, alternates and implicit fetches.
        audit = source_preparation._audit.Audit({}, REPO, ninja_repo.parent)
        try:
            audit.validate_repo(ninja_repo.name)
        except source_preparation._audit.Error as exc:
            raise Error(exc.code) from None
        git = GIT+['--git-dir='+str(ninja_repo)]
        commit = command([*git, 'rev-parse', NINJA_COMMIT+'^{commit}'], root, 'ninja.commit', data['commands'], env)
        need(commit['stdout'].decode().strip() == NINJA_COMMIT, 'ninja_source_commit_mismatch')
        tree = command([*git, 'rev-parse', NINJA_COMMIT+'^{tree}'], root, 'ninja.tree-id', data['commands'], env)['stdout'].decode().strip()
        commit_object = command([*git, 'cat-file', 'commit', NINJA_COMMIT], root, 'ninja.commit-object', data['commands'], env)['stdout']
        listing = command([*git, 'ls-tree', '-r', '-z', NINJA_COMMIT], root, 'ninja.tree', data['commands'], env)['stdout']
        entries = ninja_entries(commit_object, listing, tree)
        archive = root/'ninja.tar'
        command([*git, 'archive', '--format=tar', '--prefix=ninja-source/', '--output='+str(archive), NINJA_COMMIT],
                root, 'ninja.archive', data['commands'], env)
        source = root/'ninja-source'
        source_files = ninja_archive(archive, entries)
        extract(archive, source, 'ninja-source', 32*1024**2)
        need((source/'COPYING').is_file() and (source/'configure.py').is_file(), 'missing_ninja_build_source')
        need(source_files == ninja_archive(archive, entries, source), 'ninja_materialized_source_changed')
        data['ninja_source'] = {'commit': NINJA_COMMIT, 'tree': tree, 'source_root': 'ninja-source',
            'repository': str(ninja_repo), 'reused_cache': source_cache is not None,
            'archive': {'path': 'ninja.tar', 'sha256': sha256(archive), 'size_bytes': archive.stat().st_size},
            'files': source_files, 'notice': {'path': 'COPYING', 'sha256': sha256(source/'COPYING'), 'size_bytes': (source/'COPYING').stat().st_size}}
        build_env = dict(env)
        build_env.update(CXX=shlex.join(['/usr/bin/arch', '-arm64', native['clang++']['path'], '-isysroot', lock['sdk']['path']]),
                         SDKROOT=lock['sdk']['path'])
        build['environment'] = build_env
        data['native_build'] = build
        command(['/usr/bin/arch', '-arm64', python, source/'configure.py', '--bootstrap'], root, 'ninja.bootstrap', data['commands'],
                build_env, 180, source)
        # Bootstrap-generated files are inventoried separately from original source.
        need(source_files == ninja_archive(archive, entries, source), 'ninja_materialized_source_changed')
        ninja = source/'ninja'
        info = readers.inspect_macho(ninja)
        need(info['architectures'] == [readers.MACH_ARM64] and info['filetype'] == 2, 'ninja_not_arm64_only')
        data['tools']['ninja'] = {'path': ninja.relative_to(root).as_posix(), 'sha256': sha256(ninja), **info,
                                'source_commit': NINJA_COMMIT, 'notice_sha256': sha256(source/'COPYING')}
        command(['/usr/bin/arch', '-arm64', ninja, '--version'], root, 'ninja.version', data['commands'], env)
        for name in ('cmake', 'ninja-source'):
            data['inventories'].append({'root': name, 'files': files(root/name)})
        data['passed'] = True
        receipt_shape(data)
        write_json(root/'prepared.json', data)
        verify_tools(root, lock_path)
        return data
    except (Error, OSError, ValueError, KeyError, IndexError, UnicodeError, tarfile.TarError) as exc:
        data.update(passed=False, error=getattr(exc, 'code', type(exc).__name__))
        write_json(root/'prepare-failed.json', data)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare',))
    parser.add_argument('--toolchain', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--artifact-cache')
    parser.add_argument('--source-cache')
    parser.add_argument('--require-empty', action='store_true', required=True)
    args = parser.parse_args()
    try:
        prepare(Path(args.toolchain), Path(args.output), args.artifact_cache, args.source_cache)
        print('PASS: task-local ARM64 CMake and source-built Ninja; no runtime execution')
        return 0
    except (Error, OSError, ValueError, KeyError, IndexError, UnicodeError, tarfile.TarError) as exc:
        print('FAIL: '+getattr(exc, 'code', type(exc).__name__), file=sys.stderr)
        return 1
if __name__ == '__main__':
    raise SystemExit(main())
