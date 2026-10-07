"""Portable constructor controls; no compiler, Wine or native fixture is run."""
from copy import deepcopy
from contextlib import contextmanager
import errno
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock
from tools.fex import memory_wine_build as build
from tools.fex.common import Error


class WineMemorySourceTests(unittest.TestCase):
    def test_closed_ordered_patch_identity(self):
        value = build.load_json(build.REPO / build.RECORDS[4])
        self.assertIs(build.checked_series(value), value)
        for mutate in (
            lambda v: v['patches'].reverse(),
            lambda v: v.update(runtime_execution=True),
            lambda v: v['prototype'].update(unix_index=9),
            lambda v: v['patches'][0]['sources'].append(v['patches'][0]['sources'][0]),
            lambda v: v['patches'][1].update(sha256='0' * 64),
            lambda v: v.update(schema_version=True),
            lambda v: v.update(extra='unreviewed'),
        ):
            candidate = deepcopy(value); mutate(candidate)
            with self.assertRaises(Error): build.checked_series(candidate)

    def test_copy_refuses_changed_source_and_link_escape(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); origin = root / 'origin'; origin.mkdir()
            (origin / 'source.c').write_bytes(b'original\n')
            inventory = {'schema_version':1, 'record_kind':'wine_build_inventory', 'symlinks':[],
                         'files':[{'path':'source.c','sha256':build.digest_bytes(b'original\n'),
                                   'size_bytes':9,'mode':0o644,'kind':'data'}]}
            build.copy_inventory(origin, root / 'copy', inventory)
            self.assertEqual((root / 'copy/source.c').read_bytes(), b'original\n')
            (origin / 'source.c').write_bytes(b'changed!\n')
            with self.assertRaisesRegex(Error, 'copy_identity'):
                build.copy_inventory(origin, root / 'changed', inventory)
            inventory['symlinks'] = [{'path':'escaping', 'target':'/outside'}]
            with self.assertRaisesRegex(Error, 'copy_link'):
                build.copy_inventory(root / 'copy', root / 'unsafe', inventory)

    def test_legacy_error_code_crosses_namespace_without_class_leak(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); owned = root / 'owned'; owned.mkdir()
            (root / 'outside').write_bytes(b'outside')
            (owned / 'alias').symlink_to(root / 'outside')
            with self.assertRaisesRegex(Error,'install_link_escape'):
                with build.wine_readers() as (_,owner): owner.inventory(owned)

    def test_inventory_rejects_duplicate_paths_and_boolean_sizes(self):
        row = {'path':'file','sha256':'0'*64,'size_bytes':1,'mode':0o644}
        for candidate in ([row, row], [dict(row, size_bytes=True)], [dict(row, path='../escape')]):
            with self.assertRaises(Error): build.pin_rows(candidate)


class WineMemoryHistoricalLogTests(unittest.TestCase):
    @contextmanager
    def evidence(self):
        with tempfile.TemporaryDirectory(prefix='pear-task4-', dir='/private/tmp') as folder:
            holder = Path(folder); tools = holder / 'tools'; tools.mkdir()
            alias = holder / 'workspace'; alias.symlink_to(tools, target_is_directory=True)
            logs = tools / 'bison-build/.pear-command-logs'; logs.mkdir(parents=True)
            prepared = {'alias': {'invoked': str(alias), 'resolved': str(tools)}, 'commands': []}
            for ident in ('bison.configure', 'bison.build', 'bison.install'):
                row = {'id': ident, 'cwd': str(alias / 'bison-build'), 'exit_code': 0,
                       'timed_out': False, 'output_limit': False}
                for stream in ('stdout', 'stderr'):
                    data = (ident + ':' + stream).encode() if stream == 'stdout' else b''
                    path = logs / (ident + '.' + stream); path.write_bytes(data)
                    row[stream + '_log'] = {'path': str(alias / path.relative_to(tools)),
                                           'sha256': build.digest_bytes(data), 'size_bytes': len(data)}
                prepared['commands'].append(row)
            yield tools, alias, prepared

    def test_exact_original_log_alias_admitted_by_rooted_bytes(self):
        with self.evidence() as (tools, alias, prepared):
            build.verify_bison_logs(tools, prepared)
            self.assertFalse(Path(prepared['commands'][0]['stdout_log']['path']).is_relative_to(tools))
            self.assertEqual(alias.resolve(), tools)

    def test_redirected_or_changed_log_refused(self):
        with self.evidence() as (tools, alias, prepared):
            for mutate in (
                lambda p: p['commands'][0]['stdout_log'].update(path=str(tools / 'outside')),
                lambda p: p['commands'][0]['stdout_log'].update(size_bytes=True),
                lambda p: p['commands'][0]['stdout_log'].update(sha256='0'*64),
                lambda p: p['commands'].reverse(),
                lambda p: p['commands'][0].update(cwd=str(tools / 'bison-build')),
                lambda p: p['commands'][0].update(exit_code=False),
            ):
                value = deepcopy(prepared); mutate(value)
                with self.assertRaises(Error): build.verify_bison_logs(tools, value)
            log = tools / 'bison-build/.pear-command-logs/bison.configure.stdout'
            log.write_bytes(b'changed')
            with self.assertRaisesRegex(Error, 'bison_log'):
                build.verify_bison_logs(tools, prepared)

    def test_retargeted_owned_workspace_alias_refused(self):
        with self.evidence() as (tools, alias, prepared):
            outside = alias.parent / 'outside'; outside.mkdir()
            alias.unlink(); alias.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(Error, 'bison_alias'):
                build.verify_bison_logs(tools, prepared)

    def test_log_leaf_alias_refused_even_with_matching_bytes(self):
        with self.evidence() as (tools, alias, prepared):
            log = tools / 'bison-build/.pear-command-logs/bison.configure.stdout'
            target = tools / 'matching'; target.write_bytes(log.read_bytes())
            log.unlink(); log.symlink_to(target)
            with self.assertRaises(OSError): build.verify_bison_logs(tools, prepared)



class WineMemoryRecipeTests(unittest.TestCase):
    def inputs(self):
        config = build.load_json(build.REPO / build.RECORDS[1])
        tools = {'sdk': {'path':'/SDK with spaces'},
                 'native':{name:{'path':'/native/' + name} for name in ('clang','clang++','make','flex')}}
        alias = {'workspace':'/private/tmp/pear-task5-memory-finite/workspace',
                 'tools':'/private/tmp/pear-task5-memory-finite/tools'}
        return config, tools, alias

    def test_target_only_source_snapshot_and_space_safe_argv(self):
        config, tools, alias = self.inputs()
        commands, env = build.recipe(Path('/project with spaces/.build/task5/wine'), alias, tools, config, 2)
        self.assertEqual([c[0] for c in commands], ['configure','ntdll','owner-launch','wine-owner'])
        self.assertEqual(commands[1][1][-1], 'dlls/ntdll/all')
        self.assertNotIn('install', commands[1][1])
        self.assertEqual(commands[0][1][3], '../source/configure')
        self.assertTrue(all(c[1][:2] == ['/usr/bin/arch','-arm64'] for c in commands))
        for name in ('CPPFLAGS','CFLAGS','aarch64_CFLAGS'):
            self.assertIn(build.MACRO, env[name])
        self.assertIn('-isysroot', commands[2][1]); self.assertIn('/SDK with spaces', commands[2][1])
        self.assertIn('-static', commands[3][1])
        self.assertNotIn('-nostdlib', commands[3][1])
        self.assertFalse(any(key.startswith(('DYLD_','FEX_','LD_')) for key in env))
        self.assertNotIn('HOME',env)
        self.assertTrue(all('inputs/tests/fex/memory/' in arg for arg in commands[3][1] if arg.endswith('.c')))

    def test_parallelism_and_wrong_sdk_rejected(self):
        config, tools, alias = self.inputs()
        for jobs in (True,0,3):
            with self.assertRaisesRegex(Error,'parallelism'):
                build.recipe(Path('/output'), alias, tools, config, jobs)
        config['deployment_target'] = '14.0'
        with self.assertRaisesRegex(Error,'configuration'):
            build.recipe(Path('/output'), alias, tools, config, 2)

    def test_exact_selected_make_recipe(self):
        text = 'target: first \\\n  second\n\tclang -c source.c \\\n  $(CFLAGS)\nother: none\n'
        self.assertIn('clang -c', build.rule(text, 'target'))
        with self.assertRaisesRegex(Error,'make_rule'): build.rule(text, 'missing')
        with self.assertRaisesRegex(Error,'make_rule'): build.rule(text + text, 'target')


class WineMemoryConfigurationOwnerTests(unittest.TestCase):
    def test_reuses_real_owner_path_variant_and_keyword_contract(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root / 'objects/include').mkdir(parents=True)
            (root / 'inputs/runtime/wine').mkdir(parents=True)
            config = build.load_json(build.REPO / build.RECORDS[1])
            build.write_json(root / 'inputs/runtime/wine/build-config.json', config)
            variables = {
                'srcdir':'../source', 'HOST_ARCH':'aarch64', 'PE_ARCHS':'aarch64',
                'aarch64_TARGET':'aarch64-windows', 'arm64ec_TARGET':'', 'x86_64_TARGET':'',
                'APPKIT_LIBS':'-framework AppKit', 'CORETEXT_LIBS':'-framework CoreText',
                'FREETYPE_LIBS':'', 'FONTCONFIG_LIBS':'', 'COREAUDIO_LIBS':'',
                'PEAR_NATIVE_PE_PUBLICATION_CFLAGS':'-DPEAR_NATIVE_PE_PUBLICATION=1',
                'PEAR_NATIVE_ONLY_ARCH_CFLAGS':'-DPEAR_NATIVE_ONLY_ARCH=1',
                'CPPFLAGS':build.MACRO, 'CFLAGS':build.MACRO, 'aarch64_CFLAGS':build.MACRO,
            }
            text = ''.join(key + ' = ' + value + '\n' for key,value in variables.items())
            text += 'dlls/winemac.drv/cocoa_app.o:\n\t$(CC) -c cocoa_app.m\n'
            for target in ('dlls/ntdll/unix/pear_fex_memory.o', 'dlls/ntdll/unix/virtual.o'):
                text += target + ':\n\t$(CC) $(CFLAGS) -c source.c\n'
            text += 'dlls/ntdll/aarch64-windows/pear_fex_memory.o:\n\t$(CC) $(aarch64_CFLAGS) -c source.c\n'
            for target,member in zip(build.TARGETS, ('dlls/ntdll/unix/pear_fex_memory.o',
                                                     'dlls/ntdll/aarch64-windows/pear_fex_memory.o')):
                text += target + ':\n\t$(CC) ' + member + '\n'
            (root / 'objects/Makefile').write_text(text)
            (root / 'objects/include/config.h').write_bytes(b'/* Original parser fixture. */\n')
            facts = build.observed_config(root)
            self.assertEqual(facts['baseline_configuration']['HOST_ARCH'], 'aarch64')
            self.assertEqual(facts['baseline_configuration']['srcdir'], '../source')
            self.assertEqual(facts['finite_fixture_macro'], build.MACRO)
            (root / 'objects/Makefile').write_text(text.replace('srcdir = ../source', 'srcdir = /unselected/source'))
            with self.assertRaisesRegex(Error,'relative_srcdir'):
                build.observed_config(root)


class WineMemoryFailureTests(unittest.TestCase):
    def test_spawn_errno_and_empty_actual_logs_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); rows = []
            with mock.patch.object(build.subprocess, 'Popen', side_effect=OSError(errno.ENOEXEC,'bad executable')):
                with self.assertRaises(OSError) as caught:
                    build.execute(root,'compiler',['/unperformed/compiler'],str(root),{},5,rows,1024**2,1)
            self.assertEqual(caught.exception.errno, errno.ENOEXEC)
            row = rows[0]
            self.assertIsNone(row['exit_code']); self.assertEqual(row['status'],'failed')
            self.assertEqual(row['environment']['PWD'],str(root))
            self.assertEqual((row['error_domain'],row['error_code']),('errno',errno.ENOEXEC))
            self.assertEqual(set(row['logs']),{'stdout','stderr'})
            self.assertTrue(all(log['size_bytes'] == 0 for log in row['logs'].values()))
            self.assertEqual(build.load_json(root / 'logs/compiler/command.json'),row)

    def test_log_failure_does_not_replace_spawn_errno(self):
        with tempfile.TemporaryDirectory() as folder:
            rows = []
            with mock.patch.object(build.subprocess,'Popen',side_effect=OSError(errno.EACCES,'refused')), \
                 mock.patch.object(build,'sha256',side_effect=Error('changed_log')):
                with self.assertRaises(OSError) as caught:
                    build.execute(Path(folder),'compiler',['/unperformed/compiler'],folder,{},5,rows,1024**2,1)
            self.assertEqual(caught.exception.errno,errno.EACCES)
            self.assertEqual(rows[0]['log_collection_error']['code'],'changed_log')
            self.assertIsNone(rows[0]['exit_code'])

    def test_budget_refuses_growth_boolean_and_free_floor(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root / 'data').write_bytes(b'1234')
            with self.assertRaisesRegex(Error,'growth_limit'): build.budget(root,3,1)
            with self.assertRaisesRegex(Error,'storage_bounds'): build.budget(root,True,1)
            with mock.patch.object(build.shutil,'disk_usage',return_value=type('Usage',(),{'free':0})()):
                with self.assertRaisesRegex(Error,'free_floor'): build.budget(root,10,1)


class WineMemoryOwnedOutputTests(unittest.TestCase):
    def test_macho_parser_uses_owned_fd_and_refuses_directory_alias(self):
        # Original synthetic Mach-O header; this is only a byte-reader control.
        data = struct.pack('<8I',0xfeedfacf,0x100000c,0,2,0,0,0,0)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root / 'fixtures').mkdir(); (root / 'fixtures/native').write_bytes(data)
            parsed, facts = build.inspect_rooted_macho(root,'fixtures/native')
            self.assertEqual(parsed,data); self.assertEqual(facts['architectures'],[0x100000c])
            (root / 'alias').symlink_to(root / 'fixtures',target_is_directory=True)
            with self.assertRaises(OSError): build.inspect_rooted_macho(root,'alias/native')

    def test_native_leaf_alias_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root / 'actual').write_bytes(b'not a macho')
            (root / 'alias').symlink_to(root / 'actual')
            with self.assertRaises(OSError): build.inspect_rooted_macho(root,'alias')

    def synthetic_dll(self):
        # Original generated byte-format fixture, never executable test evidence.
        data = bytearray(1536); data[:2] = b'MZ'
        struct.pack_into('<I',data,60,128); data[128:132] = b'PE\0\0'
        struct.pack_into('<HH',data,132,0xaa64,2); struct.pack_into('<H',data,148,240)
        struct.pack_into('<H',data,150,0x2000); opt = 152
        struct.pack_into('<H',data,opt,0x20b); struct.pack_into('<I',data,opt+108,16)
        struct.pack_into('<II',data,opt+112,8192,256)
        for offset,rva,raw,flags in ((392,4096,512,0x60000020),(432,8192,1024,0x40000040)):
            struct.pack_into('<4I',data,offset+8,512,rva,512,raw)
            struct.pack_into('<I',data,offset+36,flags)
        struct.pack_into('<6I',data,1024+16,1,1,1,8192+40,8192+44,8192+48)
        struct.pack_into('<I',data,1064,4096); struct.pack_into('<I',data,1068,8192+64)
        struct.pack_into('<H',data,1072,0)
        name = b'__wine_pear_fex_memory\0'; data[1088:1088+len(name)] = name
        return data

    def test_private_export_requires_actual_named_executable_target(self):
        data = self.synthetic_dll()
        facts = build.pe_facts(bytes(data),True)
        self.assertTrue(facts['private_memory_thunk_export'])
        self.assertFalse(facts['execution'])
        for offset,fmt,value in ((1064,'I',0),(1064,'I',8192+100),(1072,'H',2),(428,'I',0x40000020)):
            changed = bytearray(data); struct.pack_into('<'+fmt,changed,offset,value)
            with self.assertRaises(Error): build.pe_facts(bytes(changed),True)

    def test_delay_import_or_wrong_outer_machine_refused(self):
        data = self.synthetic_dll()
        for offset,fmt,value in ((132,'H',0x8664),(152+112+13*8,'I',8192)):
            changed = bytearray(data); struct.pack_into('<'+fmt,changed,offset,value)
            with self.assertRaises(Error): build.pe_facts(bytes(changed),True)

    def test_invalid_or_non_arm64_pe_refused(self):
        for value in (b'',b'MZ' + bytes(62),bytearray(b'invalid'), b'MZ' + bytes(100)):
            with self.assertRaises(Error): build.pe_facts(value,False)

    def test_failed_replay_refuses_before_positive_receipt_read(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root / 'failure.json').write_text('{}')
            with mock.patch.object(build,'operation_output',return_value=root), \
                 mock.patch.object(build,'load_json',side_effect=AssertionError('must not read positive record')):
                with self.assertRaisesRegex(Error,'failed_replay'): build.verify_build(root)


if __name__ == '__main__': unittest.main()
