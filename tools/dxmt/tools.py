#!/usr/bin/env python3
"""Prepare task-local DXMT build tools; never install globally or run a guest.

The bounded archive graph/extraction algorithms below reuse the reviewed Pear
FEX tool preparer. Qualification and receipts are independently DXMT-scoped.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib
import importlib.util
import os
from pathlib import Path, PurePosixPath
import posixpath
import shutil
import stat
import sys
import tarfile
import unicodedata
import types
from common import (REPO, MACH_ARM64, Error, clean_env, decode_json, digest, encoded,
                    fields, git, load_json, need, output_directory, owned_directory,
                    read_relative, real_directory, relative, run_bounded, sha256,
                    tree_entries, validate_bare_repo, write_new)
from check import validate_toolchain

CMAKE_SHA = 'd1449f969c54d5c00886d5b643340d493dfb3c81cb39ee29b35453395c11ebf7'
CMAKE_SUM_SHA = '8d08ce0586bf40ff6b80e46fffe2db8855bab5b030db8b3782f11f68b6274ad8'
CMAKE_ROOT = 'cmake-3.31.8-macos-universal'
NINJA_COMMIT = '79feac0f3e3bc9da9effc586cd5fea41e7550051'
MESON_COMMIT = '415917b7c0d4759f73d0fe6564cbdda7fbf1eb9a'
MAX_DOWNLOAD, MAX_EXPANSION, MAX_MEMBERS = 128*1024**2, 400*1024**2, 25000
MAX_ARCHIVE_MTIME = (2**63-1)//1000000000
HELPERS = ['tools/dxmt/common.py', 'tools/dxmt/check.py', 'tools/wine/common.py',
           'tools/wine/toolchain.py', 'tools/sources/validate_inventory.py']


def readers():
    # Only Mach-O byte/dependency readers, not task4 entrypoints or archives.
    spec = importlib.util.spec_from_file_location('_pear_dxmt_native_readers', REPO/'tools/wine/toolchain.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def producers(repo=REPO):
    return {name: digest(read_relative(repo, name)) for name in ['tools/dxmt/tools.py']+HELPERS}


def lock_pins(lock):
    selected = {row['id']: row for row in lock['candidates']}
    need(selected['cmake']['version'] == '3.31.8' and selected['cmake']['archive_sha256'] == CMAKE_SHA
         and selected['cmake']['checksum_sha256'] == CMAKE_SUM_SHA
         and selected['cmake']['origin'] == 'https://github.com/Kitware/CMake/releases/download/v3.31.8/'+CMAKE_ROOT+'.tar.gz'
         and selected['cmake']['checksum_origin'] == 'https://github.com/Kitware/CMake/releases/download/v3.31.8/cmake-3.31.8-SHA-256.txt'
         and selected['ninja']['commit'] == NINJA_COMMIT and selected['ninja']['version'] == '1.13.1'
         and selected['ninja']['origin'] == 'https://github.com/ninja-build/ninja.git'
         and selected['meson']['commit'] == MESON_COMMIT and selected['meson']['version'] == '1.10.0'
         and selected['meson']['origin'] == 'https://github.com/mesonbuild/meson.git', 'unreviewed_build_tool_pin')


def command(root, ident, argv, env, commands, timeout=120):
    result = run_bounded([str(v) for v in argv], cwd=root, env=env, timeout=timeout, limit=512*1024)
    row = {k: result[k] for k in ['argv','exit_code','timed_out','output_limit','elapsed_ms']}
    row.update(id=ident, cwd=str(root), environment=env, logs={})
    for stream in ['stdout','stderr']:
        path = root/'logs'/ident/stream
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(result[stream])
        row['logs'][stream] = {'path': path.relative_to(root).as_posix(), 'sha256': digest(result[stream]), 'size_bytes': len(result[stream])}
    commands.append(row)
    need(result['exit_code'] == 0, 'tool_command_failed:'+ident)
    return result['stdout']


def native_file(path):
    path = Path(path).absolute()
    need('..' not in path.parts and path.is_file(), 'native_tool_path')
    actual = path.resolve(strict=True)
    info = readers().inspect_macho(actual)
    need(info['selected_cpu'] == MACH_ARM64 and info['filetype'] == 2, 'native_tool_not_arm64')
    need(actual.stat().st_mode & 0o111, 'native_tool_not_executable')
    return {'path': str(path), 'resolved_path': str(actual), 'sha256': sha256(actual),
            'size_bytes': actual.stat().st_size, 'mode': stat.S_IMODE(actual.stat().st_mode), **info}


def source_identity(repository, commit):
    repository = real_directory(repository)
    validate_bare_repo(repository.parent, repository.name)
    need(git(repository,'rev-parse',commit+'^{commit}').decode().strip() == commit, 'tool_source_commit')
    raw_commit = git(repository,'cat-file','commit',commit)
    need(hashlib.sha1(f'commit {len(raw_commit)}\0'.encode()+raw_commit).hexdigest() == commit, 'tool_source_commit_bytes')
    tree = git(repository,'rev-parse',commit+'^{tree}').decode().strip()
    need(raw_commit.startswith(('tree '+tree+'\n').encode()), 'tool_source_tree')
    listing = git(repository,'ls-tree','-r','-z',commit)
    entries = tree_entries(listing, metadata_only=True)
    return {'repository': str(repository), 'commit': commit, 'tree': tree, 'listing_sha256': digest(listing)}, entries


def meson_selection(entries):
    rows = [r for r in entries if r['path'] in ['meson.py','COPYING'] or r['path'].startswith('mesonbuild/')]
    need(rows and any(r['path'] == 'meson.py' for r in rows) and any(r['path'] == 'COPYING' for r in rows), 'meson_source_closure')
    need(all(r['mode'] in ['100644','100755'] for r in rows), 'meson_source_entry')
    for row in rows:
        relative(row['path'])
    return rows


def materialize_meson(repository, entries, output):
    output.mkdir()
    rows = []
    total = 0
    for row in meson_selection(entries):
        raw = git(repository,'cat-file','blob',row['git_object'])
        total += len(raw)
        need(total <= 32*1024**2 and hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest() == row['git_object'], 'meson_blob_identity')
        target = output.joinpath(*relative(row['path']))
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(raw)
        target.chmod(0o755 if row['mode'] == '100755' else 0o644)
        rows.append({'path': row['path'], 'sha256': digest(raw), 'size_bytes': len(raw), 'mode': target.stat().st_mode & 0o777,
                     'git_blob': row['git_object']})
    return sorted(rows,key=lambda r:r['path'])


def notices(rows):
    result = [r for r in rows if any(w in r['path'].lower() for w in ['license','copyright','copying']) and 'sha256' in r]
    need(result, 'build_tool_notices_missing')
    return result


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



REUSE_RECEIPT_SHA='245802ba8aa450b18c1b7862c3f1d02604bf3fbdde7c1f05d72cb39ce184605a'
REUSE_PRODUCER_SHA='cdb6067315561cc5c27134d028b02471129618b1397639de8be6cb7eda6f6863'
REUSE_TOOLCHAIN_SHA='d69b53d06a0cb99e49c3014f6e2c1abbbde6f65e78182ca721b9b42e4f153ed6'
REUSE_HELPERS={
 'tools/fex/byte_readers.py':'bbfc08e473bfc91d51cb34a234be706cabe56c36e87acf00b90a587f48604316',
 'tools/fex/common.py':'d33dea8a1ed7680d5377c57133848ec8f9cbfd0602853eeb6e2747595d850fec',
 'tools/fex/prepare.py':'f9d3e15249fdeefa190f512e4fba4cbb617c95ef91e9529adc0b9356ed046b3b',
 'tools/sources/validate_inventory.py':'a851ee6978002a4e45934b91e4abdfe0151d73178e862e45b2b0824a4e0b3710',
 'tools/wine/common.py':'5c2789ca3392f70f93c5ae0656e803c0f8a01d4cc1c1d2622e8af0014690e171',
 'tools/wine/toolchain.py':'760e701e79337635c6c8ae77fc607d4ee550932cd04c419540e44f5a9e2cb597'}


def verify_reuse(reuse):
    """Replay the exact reviewed FEX source-build proof in an isolated package.

    This imports only hash-admitted Pear verifier code. It never bootstraps a
    tool or runs a compiler. Its source/command/native checks keep FEX scope;
    the separately prepared DXMT record supplies fresh byte/tool qualification.
    """
    reuse=real_directory(reuse)
    raw=read_relative(reuse,'prepared.json');old=decode_json(raw)
    need(digest(raw)==REUSE_RECEIPT_SHA and old.get('producer_sha256')==REUSE_PRODUCER_SHA
         and old.get('helper_sha256')==REUSE_HELPERS and old.get('toolchain_sha256')==REUSE_TOOLCHAIN_SHA,'reuse_reviewed_proof_changed')
    repo=real_directory(reuse.parents[2])
    need(sha256(repo/'tools/fex/tools.py')==REUSE_PRODUCER_SHA
         and all(sha256(repo/path)==value for path,value in REUSE_HELPERS.items())
         and sha256(repo/'runtime/fex/toolchain.json')==REUSE_TOOLCHAIN_SHA,'reuse_verifier_identity')
    name='_pear_dxmt_reviewed_fex_'+digest(str(repo).encode())[:16]
    need(name not in sys.modules,'reuse_package_collision')
    package=types.ModuleType(name);package.__path__=[str(repo/'tools/fex')];package.__package__=name
    sys.modules[name]=package
    try:
        module=importlib.import_module(name+'.tools')
        result=module.verify_tools(reuse,repo/'runtime/fex/toolchain.json')
        need(result==old,'reuse_verifier_result')
    except Exception as error:
        if hasattr(error,'code'):raise Error(error.code) from None
        raise
    finally:
        for key in list(sys.modules):
            if key==name or key.startswith(name+'.'):sys.modules.pop(key,None)
    return old,raw


def ninja_archive(path, entries):
    regular = {r['path']:r for r in entries}
    need(all(r['mode'] in ['100644','100755'] for r in entries), 'ninja_source_entry')
    rows = []
    with tarfile.open(path,'r:*') as archive:
        members,_ = archive_graph(archive,'ninja-source',32*1024**2)
        ordinary = [(m,p) for m,p in members if not m.isdir()]
        need({p for _,p in ordinary} == set(regular), 'ninja_archive_closure')
        for member,name in ordinary:
            need(member.isfile(), 'ninja_archive_entry')
            data = archive.extractfile(member).read(member.size+1)
            entry = regular[name]
            mode = 0o755 if entry['mode'] == '100755' else 0o644
            need(len(data) == member.size and hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest() == entry['git_object']
                 and (0o755 if member.mode & 0o111 else 0o644) == mode,'ninja_archive_blob')
            rows.append({'path':name,'sha256':digest(data),'size_bytes':len(data),'mode':mode})
    return sorted(rows,key=lambda r:r['path'])


def expected_commands(root,value):
    native = value['native_tools']
    return {'cmake.version':['/usr/bin/arch','-arm64',str(root/'cmake/CMake.app/Contents/bin/cmake'),'--version'],
            'ninja.version':['/usr/bin/arch','-arm64',str(root/'ninja-source/ninja'),'--version'],
            'meson.version':['/usr/bin/arch','-arm64',native['python']['path'],'-B',str(root/'meson-source/meson.py'),'--version'],
            'sdk.path':['/usr/bin/arch','-arm64',native['xcrun']['path'],'--sdk','macosx','--show-sdk-path'],
            'sdk.version':['/usr/bin/arch','-arm64',native['xcrun']['path'],'--sdk','macosx','--show-sdk-version']}


def verify_commands(root,value):
    expected = expected_commands(root,value)
    need(len(value['commands']) == 5 and {r.get('id') for r in value['commands']} == set(expected), 'tools_command_set')
    results = {}
    for row in value['commands']:
        fields(row,['id','argv','cwd','environment','exit_code','timed_out','output_limit','elapsed_ms','logs'])
        need(row['argv'] == expected[row['id']] and row['cwd'] == str(root) and row['environment'] == value['environment']
             and row['exit_code'] == 0 and row['timed_out'] is False and row['output_limit'] is False
             and type(row['elapsed_ms']) is int and row['elapsed_ms'] >= 0,'tools_command_recipe')
        fields(row['logs'],['stdout','stderr'])
        for stream,ref in row['logs'].items():
            fields(ref,['path','sha256','size_bytes'])
            need(ref['path'] == 'logs/'+row['id']+'/'+stream, 'tools_log_path')
            raw = read_relative(root,ref['path'],512*1024)
            need(len(raw) == ref['size_bytes'] and digest(raw) == ref['sha256'],'tools_log_changed')
            if stream == 'stdout': results[row['id']] = raw.decode().strip()
    need(results['cmake.version'].splitlines()[0] == 'cmake version 3.31.8' and results['ninja.version'] == '1.13.1'
         and results['meson.version'] == '1.10.0','build_tool_version')
    need(results['sdk.version'] == value['sdk']['version'] and Path(results['sdk.path']).resolve(strict=True)
         == Path(value['sdk']['path']).resolve(strict=True),'tools_sdk_changed')


def verify_tools(root,repo=REPO):
    root = owned_directory(root,repo)
    need(not (root/'failed.json').exists(), 'failed_tool_preparation')
    value = load_json(root/'prepared.json')
    fields(value,['schema_version','record_kind','scope','toolchain_ref','producers','reuse_ref','downloads','sources',
                  'inventories','tools','native_tools','sdk','environment','commands','notices','passed','runtime_eligible'], 'dxmt_tools_prepared')
    need(value['scope'] == 'dxmt_component' and value['passed'] is True and value['runtime_eligible'] is False,'tools_scope')
    need(value['producers'] == producers(repo),'tools_producer_changed')
    ref=value['toolchain_ref'];fields(ref,['path','sha256'])
    raw=read_relative(repo,ref['path']);need(digest(raw)==ref['sha256'],'tools_lock_changed')
    lock=validate_toolchain(decode_json(raw),repo);lock_pins(lock)
    need(value['sdk'] == lock['sdk'] and value['environment'] == clean_env(),'tools_environment')
    need(set(value['native_tools']) == {'python','xcrun','xxd','clang','clang++'},'tools_native_set')
    for name,fact in value['native_tools'].items():
        expected=lock['native_tool_paths'].get(name, '/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/'+name)
        need(fact['path']==expected and native_file(expected)==fact,'tools_native_changed')
    need({r['path'] for r in value['downloads']} == {'downloads/cmake.tar.gz','downloads/cmake-SHA-256.txt','downloads/ninja.tar'},'tools_download_set')
    for row in value['downloads']:
        fields(row,['path','sha256','size_bytes'])
        raw=read_relative(root,row['path'],MAX_DOWNLOAD)
        need(digest(raw)==row['sha256'] and len(raw)==row['size_bytes'],'tool_archive_changed')
    need(sha256(root/'downloads/cmake.tar.gz')==CMAKE_SHA and sha256(root/'downloads/cmake-SHA-256.txt')==CMAKE_SUM_SHA,'cmake_archive_pin')
    need(CMAKE_SHA+'  '+CMAKE_ROOT+'.tar.gz' in read_relative(root,'downloads/cmake-SHA-256.txt',128*1024).decode().splitlines(),'publisher_checksum')
    need(set(value['inventories'])=={'cmake','ninja-source','meson-source'} and all(files(root/k)==v for k,v in value['inventories'].items()),'tool_payload_changed')
    need(archive_inventory(root/'downloads/cmake.tar.gz',CMAKE_ROOT)==value['inventories']['cmake'],'cmake_payload_identity')
    need(set(value['sources'])=={'meson','ninja'},'tools_source_set')
    for name,commit in [('meson',MESON_COMMIT),('ninja',NINJA_COMMIT)]:
        fields(value['sources'][name],['repository','commit','tree','listing_sha256'])
        actual,entries=source_identity(value['sources'][name]['repository'],commit)
        need(actual==value['sources'][name],'tool_source_changed')
        if name=='ninja':
            expected=ninja_archive(root/'downloads/ninja.tar',entries)
            observed=[r for r in value['inventories']['ninja-source'] if r['path']!='ninja']
            need(expected==observed,'ninja_source_changed')
        else:
            selected=meson_selection(entries)
            rows=value['inventories']['meson-source']
            need({r['path'] for r in rows}=={r['path'] for r in selected},'meson_payload_closure')
            for row in rows:
                e=next(e for e in selected if e['path']==row['path'])
                content=read_relative(root/'meson-source',row['path'])
                need(hashlib.sha1(f'blob {len(content)}\0'.encode()+content).hexdigest()==e['git_object']
                     and row['mode']==(0o755 if e['mode']=='100755' else 0o644),'meson_payload_blob')
    need(set(value['tools']) == {'cmake','meson','ninja'},'tools_executable_set')
    for name in ['cmake','ninja']:
        fact=value['tools'][name]
        fields(fact,['path','sha256','native_closure'])
        expected='cmake/CMake.app/Contents/bin/cmake' if name=='cmake' else 'ninja-source/ninja'
        need(fact['path']==expected and sha256(root/expected)==fact['sha256']
             and readers().inspect_closure(root/expected,root/name.replace('ninja','ninja-source'))==fact['native_closure'],'tool_native_closure')
        need(all(r['selected_cpu']==MACH_ARM64 for r in fact['native_closure']),'tool_requires_rosetta')
    need(value['tools']['meson']=={'path':'meson-source/meson.py','sha256':sha256(root/'meson-source/meson.py'),'execution':'selected_native_python'},'meson_entrypoint')
    need(value['notices']=={name:notices(rows) for name,rows in value['inventories'].items()},'tools_notice_closure')
    reuse=value['reuse_ref'];fields(reuse,['root','receipt_sha256','ninja_binary_sha256','source_build_status'])
    need(reuse['source_build_status']=='reused_source_build_not_reproduced_in_task7' and reuse['ninja_binary_sha256']==value['tools']['ninja']['sha256'],'ninja_build_scope')
    _prior,prior=verify_reuse(reuse['root'])
    need(digest(prior)==reuse['receipt_sha256'],'reuse_provenance_changed')
    verify_commands(root,value)
    return value


def prepare_tools(toolchain,reuse_root,meson_repository,output,repo=REPO):
    lockpath=Path(repo)/toolchain
    lock=validate_toolchain(load_json(lockpath),repo);lock_pins(lock)
    reuse=real_directory(reuse_root)
    old,oldraw=verify_reuse(reuse)
    need(old['record_kind']=='fex_tools_prepared' and old['scope']=='fex_component' and old['passed'] is True
         and old['runtime_execution'] is False and old['ninja_source']['commit']==NINJA_COMMIT,'reuse_scope')
    root=output_directory(output,repo)
    value={'schema_version':1,'record_kind':'dxmt_tools_prepared','scope':'dxmt_component',
           'toolchain_ref':{'path':toolchain,'sha256':sha256(lockpath)},'producers':producers(repo),
           'reuse_ref':{'root':str(reuse),'receipt_sha256':digest(oldraw), 'ninja_binary_sha256':old['tools']['ninja']['sha256'],
                       'source_build_status':'reused_source_build_not_reproduced_in_task7'},
           'downloads':[],'sources':{},'inventories':{},'tools':{},'native_tools':{},'sdk':lock['sdk'],
           'environment':clean_env(),'commands':[],'notices':{},'passed':True,'runtime_eligible':False}
    try:
        (root/'downloads').mkdir()
        for name,prior,expected in [('cmake.tar.gz','downloads/cmake.tar.gz',CMAKE_SHA),('cmake-SHA-256.txt','downloads/cmake-SHA-256.txt',CMAKE_SUM_SHA),
                                    ('ninja.tar','ninja.tar',old['ninja_source']['archive']['sha256'])]:
            content=read_relative(reuse,prior,MAX_DOWNLOAD)
            need(digest(content)==expected,'reuse_archive_changed')
            path=root/'downloads'/name;path.write_bytes(content)
            value['downloads'].append({'path':'downloads/'+name,'sha256':expected,'size_bytes':len(content)})
        need(CMAKE_SHA+'  '+CMAKE_ROOT+'.tar.gz' in (root/'downloads/cmake-SHA-256.txt').read_text().splitlines(),'publisher_checksum')
        extract(root/'downloads/cmake.tar.gz',root/'cmake',CMAKE_ROOT)
        ninjasrc,ninjaentries=source_identity(old['ninja_source']['repository'],NINJA_COMMIT)
        ninja_archive(root/'downloads/ninja.tar',ninjaentries)
        extract(root/'downloads/ninja.tar',root/'ninja-source','ninja-source',32*1024**2)
        binary=read_relative(reuse,old['tools']['ninja']['path'],MAX_DOWNLOAD)
        need(digest(binary)==old['tools']['ninja']['sha256'],'reuse_ninja_binary')
        (root/'ninja-source/ninja').write_bytes(binary);(root/'ninja-source/ninja').chmod(0o755)
        mesonsrc,mesonentries=source_identity(meson_repository,MESON_COMMIT)
        materialize_meson(meson_repository,mesonentries,root/'meson-source')
        value['sources']={'ninja':ninjasrc,'meson':mesonsrc}
        value['inventories']={name:files(root/name) for name in ['cmake','ninja-source','meson-source']}
        for name,path in [('cmake','cmake/CMake.app/Contents/bin/cmake'),('ninja','ninja-source/ninja')]:
            info=readers().inspect_macho(root/path)
            need(info['filetype']==2 and info['selected_cpu']==MACH_ARM64 and (name!='ninja' or info['architectures']==[MACH_ARM64]),'tool_requires_rosetta')
            value['tools'][name]={'path':path,'sha256':sha256(root/path),'native_closure':readers().inspect_closure(root/path,root/name.replace('ninja','ninja-source'))}
        value['tools']['meson']={'path':'meson-source/meson.py','sha256':sha256(root/'meson-source/meson.py'),'execution':'selected_native_python'}
        native=dict(lock['native_tool_paths'])
        native={k:v for k,v in native.items() if k in ['python','xcrun','xxd']}
        for name in ['clang','clang++']:
            native[name]='/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/'+name
        value['native_tools']={k:native_file(v) for k,v in native.items()}
        for ident,argv in expected_commands(root,value).items():
            command(root,ident,argv,value['environment'],value['commands'])
        value['notices']={name:notices(rows) for name,rows in value['inventories'].items()}
        verify_commands(root,value)
        write_new(root/'prepared.json',value)
        verify_tools(root,repo)
        return value
    except (Error,OSError,ValueError,KeyError) as error:
        write_new(root/'failed.json',{'error':error.code if isinstance(error,Error) else 'tool_preparation_failed','passed':False,'runtime_eligible':False})
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='operation',required=True)
    prepare=sub.add_parser('prepare')
    prepare.add_argument('--toolchain',required=True);prepare.add_argument('--reuse-root',required=True)
    prepare.add_argument('--meson-repository',required=True);prepare.add_argument('--output',required=True)
    prepare.add_argument('--require-empty',action='store_true',required=True)
    verify=sub.add_parser('verify');verify.add_argument('--root',required=True)
    args=parser.parse_args()
    try:
        value=prepare_tools(args.toolchain,args.reuse_root,args.meson_repository,args.output) if args.operation=='prepare' else verify_tools(args.root)
        print(encoded({'tools_ready':value['passed'],'source_build_status':value['reuse_ref']['source_build_status'],'runtime_eligible':False}).decode(),end='')
        return 0
    except (Error,OSError,ValueError,KeyError,UnicodeError) as error:
        print(encoded({'tools_ready':False,'error':error.code if isinstance(error,Error) else 'tool_preparation_failed','runtime_eligible':False}).decode(),end='')
        return 1

if __name__=='__main__':
    sys.exit(main())
