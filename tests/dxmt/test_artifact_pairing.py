"""Original portable metadata-only DXMT artifact and failure fixtures.

PE entrypoints are zero and no executable instructions are supplied. Mach-O
fixtures contain headers/symbol metadata only. No native/guest tool is invoked.
"""
import copy
import importlib.util
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO/'tools/dxmt'))
spec = importlib.util.spec_from_file_location('_pear_dxmt_artifact_inspector', REPO/'tools/dxmt/inspect.py')
inspector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inspector)
from common import Error, digest, encoded


def pe_image(exports, machine=0xaa64, imports=('ntdll.dll',)):
    """Original bounded PE metadata; zero entrypoint, no runnable payload."""
    data = bytearray(8192)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 60, 128)
    data[128:132] = b'PE\0\0'
    struct.pack_into('<HH', data, 132, machine, 1)
    struct.pack_into('<HH', data, 148, 240, 0x2000)
    struct.pack_into('<H', data, 152, 0x20b)
    struct.pack_into('<Q', data, 176, 0x180000000)
    struct.pack_into('<II', data, 208, 0x4000, 512)
    struct.pack_into('<I', data, 260, 16)
    data[392:400] = b'.rdata\0\0'
    struct.pack_into('<IIII', data, 400, 7680, 0x1000, 7680, 512)
    # Executable-section metadata is necessary to encode CHPE range kinds;
    # all addresses still refer to zero metadata bytes, never instructions.
    struct.pack_into('<I', data, 428, 0x60000020)
    at = lambda rva: 512+rva-0x1000
    struct.pack_into('<II', data, 264, 0x1000, 0x180)
    base = min(exports.values())
    count = max(exports.values())-base+1
    struct.pack_into('<6I', data, at(0x1000)+16, base, count, len(exports), 0x1040, 0x1100, 0x1180)
    string_at = 0x1200
    for index, (name, ordinal) in enumerate(sorted(exports.items())):
        struct.pack_into('<I', data, at(0x1040)+4*(ordinal-base), 0x2800)
        struct.pack_into('<I', data, at(0x1100)+4*index, string_at)
        struct.pack_into('<H', data, at(0x1180)+2*index, ordinal-base)
        value = name.encode()+b'\0'
        data[at(string_at):at(string_at)+len(value)] = value
        string_at += len(value)
    struct.pack_into('<II', data, 264+8, 0x1800, (len(imports)+1)*20)
    for index, name in enumerate(imports):
        rva = 0x1a00+index*128
        struct.pack_into('<5I', data, at(0x1800)+20*index, 0, 0, 0, rva, 0)
        value = name.encode()+b'\0'
        data[at(rva):at(rva)+len(value)] = value
    struct.pack_into('<II', data, 264+10*8, 0x1c00, 0x140)
    struct.pack_into('<I', data, at(0x1c00), 0x140)
    struct.pack_into('<Q', data, at(0x1c00)+0xc8, 0x180002000)
    struct.pack_into('<IH', data, at(0x1c00)+0xe0, 0x1200, 1)
    struct.pack_into('<3I', data, at(0x2000), 2, 0x2040, 2)
    struct.pack_into('<4I', data, at(0x2040), 0x2800, 4, 0x2811, 4)
    struct.pack_into('<II', data, at(0x2200), 1, 24)
    struct.pack_into('<QI', data, at(0x2208), 6, 12)
    struct.pack_into('<IIHH', data, at(0x2214), 0, 12, 0x5084, 0x8664)
    return bytes(data)


def macho_image(name, dependencies=('/usr/lib/libSystem.B.dylib',), rpaths=('@loader_path/',), symbols=(), filetype=6, cpu=0x100000c):
    """Original load-command/symbol metadata; no sections or machine code."""
    def string_command(kind, value, fixed):
        raw = value.encode()+b'\0'
        length = (fixed+len(raw)+7)//8*8
        return struct.pack('<III', kind, length, fixed)+bytes(fixed-12)+raw+bytes(length-fixed-len(raw))
    commands = [string_command(0xd, '@rpath/'+name, 24)]
    commands += [string_command(0xc, dependency, 24) for dependency in dependencies]
    commands += [string_command(0x8000001c, rpath, 12) for rpath in rpaths]
    strings = b'\0'+b''.join(symbol.encode()+b'\0' for symbol in symbols)
    command_bytes = sum(map(len, commands))+24
    symoff = 32+command_bytes
    stroff = symoff+16*len(symbols)
    commands.append(struct.pack('<6I', 2, 24, symoff, len(symbols), stroff, len(strings)))
    data = bytearray(struct.pack('<8I', 0xfeedfacf, cpu, 0, filetype, len(commands), command_bytes, 0, 0)+b''.join(commands))
    offset = 1
    for symbol in symbols:
        data += struct.pack('<IBBHQ', offset, 3, 0, 0, 0)  # external absolute metadata symbol
        offset += len(symbol)+1
    return bytes(data)+strings


def dual_archive():
    data = b'!<arch>\n'
    for name, machine in [('native.obj/', 0xaa64), ('ec.obj/', 0xa641)]:
        body = struct.pack('<H', machine)+bytes(18)
        header = (name.ljust(16)+'0'.ljust(12)+'0'.ljust(6)+'0'.ljust(6)+'644'.ljust(8)+str(len(body)).ljust(10)+'`\n').encode()
        data += header+body
    return data


def header(payload, name):
    body = ', '.join('0x%02x'%value for value in payload)
    return ('unsigned char '+name+'[] = {'+body+'};\nunsigned int '+name+'_len = '+str(len(payload))+';\n').encode()


class ArtifactPairingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name).resolve()/'repo'
        self.root = self.repo/'.build/task7/static-fixture'
        self.root.mkdir(parents=True)
        self.put('tools/wine/modules.py', (REPO/'tools/wine/modules.py').read_bytes(), base=self.repo)
        self.value = {'schema_version': 1, 'record_kind': 'dxmt_artifact_build', 'scope': 'dxmt_component',
                      'pairing_verified': False, 'gpu_or_guest_execution_performed': False, 'runtime_eligible': False,
                      'generated_inputs': [], 'wine_layout': [], 'refs': {}}
        exports = {'d3d11.dll': {'D3D11CoreCreateDevice': 18, 'D3D11CreateDevice': 22,
                                'D3D11CreateDeviceAndSwapChain': 23, 'D3D11On12CreateDevice': 24},
                   'dxgi.dll': {'CreateDXGIFactory': 9, 'CreateDXGIFactory1': 10, 'CreateDXGIFactory2': 11,
                                'DXGIDeclareAdapterRemovalSupport': 16, 'DXGIGetDebugInterface1': 17},
                   'd3d10core.dll': {'D3D10CoreCreateDevice': 1, 'D3D10CoreRegisterLayers': 2},
                   'winemetal.dll': {name: index+1 for index, name in enumerate(sorted(inspector.WINEMETAL_EXPORTS))}}
        for name, mapping in exports.items():
            raw = pe_image(mapping, imports=('ntdll.dll', 'winemetal.dll') if name != 'winemetal.dll' else ('ntdll.dll',))
            self.put('compiler/'+name, raw)
            processed = raw[:64]+inspector.BUILTIN_MARKER+raw[96:]
            self.put('objects/'+inspector.PE_PATHS[name], processed)
            self.put('install/aarch64-windows/'+name, processed)
            if name in inspector.DEFS:
                definition = 'LIBRARY '+name+'\nEXPORTS\n'+'\n'.join(key+' @'+str(value) for key, value in mapping.items())+'\n'
                self.put('source/'+inspector.DEFS[name], definition.encode())
        for path, role in inspector.WINE_LAYOUT.items():
            name = Path(path).name
            if name.endswith('.a'):
                data, mode = dual_archive(), 0o644
            elif name == 'winebuild':
                data, mode = macho_image(name, rpaths=(), filetype=2), 0o755
            else:
                deps = ('@rpath/ntdll.so', '@rpath/win32u.so') if name == 'winemac.so' else (('@rpath/ntdll.so',) if name == 'win32u.so' else ('/usr/lib/libSystem.B.dylib',))
                data, mode = macho_image(name, dependencies=deps), 0o755
            self.put(path, data, mode)
            _, fact = inspector.file_bytes(self.root, path)
            self.value['wine_layout'].append({**fact, 'origin_role': role, 'origin_path': 'lib/wine/'+name})
        native = macho_image('winemetal.so', dependencies=('@rpath/ntdll.so', '@rpath/winemac.so', '/System/Library/Frameworks/Metal.framework/Versions/A/Metal'),
                             rpaths=tuple(inspector.NATIVE_RPATHS), symbols=('___wine_unix_call_funcs', '___wine_unix_call_wow64_funcs'))
        self.put('objects/'+inspector.NATIVE_PATH, native, 0o755)
        self.put('install/aarch64-unix/winemetal.so', native, 0o755)
        for name in ['air_msad', 'air_samplepos', 'air_tessellation']:
            path = 'objects/src/airconv/darwin/libairconv.a.p/'+name
            payload = b'BC\xc0\xde'+bytes(40)
            self.put(path+'.air', payload)
            self.put(path+'.h', header(payload, name))
        path = 'objects/src/dxmt/libdxmt.a.p/dxmt_command'
        self.put(path+'.air', b'BC\xc0\xde'+bytes(40))
        payload = b'MTLB'+bytes(40)
        self.put(path+'.metallib', payload)
        self.put(path+'.h', header(payload, 'dxmt_command'))
        self.put('source/version.h.in', b'#define DXMT_VERSION "@VCS_TAG@"\n')
        self.put('objects/version.h', b'#define DXMT_VERSION "'+inspector.DXMT_COMMIT.encode()+b'"\n')
        components = []
        for name in sorted(inspector.NOTICE_IDS):
            payload = ('Original notice fixture '+name).encode()
            path = 'notices/'+name+'/LICENSE'
            self.put(path, payload)
            self.value['generated_inputs'].append(inspector.file_bytes(self.root, path)[1])
            components.append({'id': name, 'commit': inspector.DXMT_COMMIT,
                               'terms': [{'path': 'LICENSE', 'sha256': digest(payload), 'size_bytes': len(payload)}]})
        data = encoded({'components': components})
        self.put('runtime/dxmt/inputs.json', data, base=self.repo)
        self.value['refs']['inputs'] = {'path': 'runtime/dxmt/inputs.json', 'sha256': digest(data)}
        self.put('native.ini', b'[binaries]\n')
        self.value['generated_inputs'].append(inspector.file_bytes(self.root, 'native.ini')[1])

    def tearDown(self):
        self.temp.cleanup()

    def put(self, path, data, mode=0o644, base=None):
        full = (base or self.root)/path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_bytes(data)
        full.chmod(mode)
        return full

    def inspect(self):
        return inspector.inspect_outputs(self.root, self.value, repo=self.repo)

    def refuse(self, code=None):
        with self.assertRaises(Error) as caught:
            self.inspect()
        if code:
            self.assertEqual(caught.exception.code, code)

    def test_complete_metadata_inventory_has_truthful_finite_scope(self):
        value = self.inspect()
        self.assertEqual(len(value['pe_modules']), 4)
        self.assertEqual(len(value['shader_outputs']), 9)
        self.assertEqual(len(value['notices']), 7)
        self.assertEqual(value, self.inspect())
        self.assertFalse(value['pairing_verified'])
        self.assertFalse(value['runtime_eligible'])
        self.assertEqual(value['runtime_loader_resolution'], 'unperformed')
        kinds = {item['kind'] for item in value['pe_modules'][0]['facts']['import_dependencies']}
        self.assertEqual(kinds, {'dxmt_component_dependency', 'external_windows_api_or_crt_dependency'})

    def test_raw_machine_never_normalized(self):
        raw = (self.root/'compiler/dxgi.dll').read_bytes()
        data = bytearray(raw);struct.pack_into('<H', data, 132, 0xa641)
        self.put('compiler/dxgi.dll', data)
        processed = bytes(data[:64])+inspector.BUILTIN_MARKER+bytes(data[96:])
        self.put('objects/'+inspector.PE_PATHS['dxgi.dll'], processed)
        self.put('install/aarch64-windows/dxgi.dll', processed)
        self.refuse('artifact_outer_machine')

    def test_plain_arm64_without_hybrid_metadata_refused(self):
        data = bytearray((self.root/'compiler/dxgi.dll').read_bytes())
        struct.pack_into('<II', data, 264+10*8, 0, 0)
        with self.assertRaises(Error) as caught:
            inspector.inspect_pe_bytes(bytes(data))
        self.assertEqual(caught.exception.code, 'module_arm64x_metadata_missing')

    def test_wrong_alternate_machine_refused(self):
        data = bytearray((self.root/'compiler/dxgi.dll').read_bytes())
        struct.pack_into('<H', data, 512+0x221e-0x1000, 0xaa64)
        with self.assertRaises(Error):
            inspector.inspect_pe_bytes(bytes(data))

    def test_missing_dll_characteristic_refused(self):
        data = bytearray((self.root/'compiler/dxgi.dll').read_bytes())
        struct.pack_into('<H', data, 150, 0)
        with self.assertRaises(Error) as caught:
            inspector.inspect_pe_bytes(bytes(data))
        self.assertEqual(caught.exception.code, 'artifact_not_dll')

    def test_compiler_already_builtin_refused(self):
        self.put('compiler/dxgi.dll', (self.root/'install/aarch64-windows/dxgi.dll').read_bytes())
        self.refuse('artifact_compiler_already_builtin')

    def test_builtin_additional_mutation_refused(self):
        path = 'objects/'+inspector.PE_PATHS['dxgi.dll']
        data = bytearray((self.root/path).read_bytes());data[-1] = 1
        self.put(path, data)
        self.refuse('artifact_builtin_mutation')

    def test_installed_bytes_changed_refused(self):
        path = 'install/aarch64-windows/dxgi.dll'
        data = bytearray((self.root/path).read_bytes());data[-1] = 1
        self.put(path, data)
        self.refuse('artifact_installed_pe_changed')

    def test_missing_or_extra_installed_file_refused(self):
        (self.root/'install/aarch64-windows/dxgi.dll').unlink()
        self.refuse('artifact_install_set')
        self.put('install/aarch64-windows/extra.dll', b'original extra metadata')
        self.refuse('artifact_install_set')

    def test_intermediate_installed_alias_refused(self):
        directory = self.root/'install/aarch64-windows'
        target = self.root/'renamed'
        directory.rename(target);directory.symlink_to(target, target_is_directory=True)
        self.refuse('artifact_install_directory_alias')

    def test_nonstandard_mode_refused(self):
        (self.root/'compiler/dxgi.dll').chmod(0o666)
        self.refuse('artifact_mode')

    def test_definition_ordinal_mismatch_refused(self):
        self.put('source/'+inspector.DEFS['dxgi.dll'], b'LIBRARY DXGI.DLL\nEXPORTS\nCreateDXGIFactory @10\n')
        self.refuse('artifact_definition_exports')
        self.assertEqual(inspector.definition_exports(b'LIBRARY X\nEXPORTS\nHello @42\n'), {'Hello': 42})

    def test_definition_exact_ordinal_is_bound(self):
        self.put('source/'+inspector.DEFS['dxgi.dll'], b'LIBRARY DXGI.DLL\nEXPORTS\nCreateDXGIFactory @10\n')
        facts = {'exports': [{'name': 'CreateDXGIFactory', 'ordinal': 9, 'rva': 0x2800}]}
        with self.assertRaises(Error) as caught:
            inspector.check_exports('dxgi.dll', facts, self.root)
        self.assertEqual(caught.exception.code, 'artifact_definition_ordinals')

    def test_native_intermediate_alias_refused(self):
        directory = self.root/'objects/src/winemetal/unix'
        target = self.root/'native-target'
        directory.rename(target)
        directory.symlink_to(target, target_is_directory=True)
        with self.assertRaises(OSError):
            inspector.inspect_native(self.root, 'objects/'+inspector.NATIVE_PATH)

    def test_notice_generated_membership_is_required(self):
        self.value['generated_inputs'] = self.value['generated_inputs'][1:]
        self.refuse('artifact_notice_generated_omission')

    def test_unaccounted_native_dependency_refused(self):
        data = macho_image('winemetal.so', dependencies=('/opt/homebrew/lib/libexample.dylib',), rpaths=tuple(inspector.NATIVE_RPATHS),
                           symbols=('___wine_unix_call_funcs', '___wine_unix_call_wow64_funcs'))
        self.put('objects/'+inspector.NATIVE_PATH, data, 0o755)
        self.put('install/aarch64-unix/winemetal.so', data, 0o755)
        self.refuse('artifact_native_unaccounted_dependency')

    def test_bad_native_rpath_refused(self):
        data = macho_image('winemetal.so', rpaths=('/opt/homebrew/lib',), symbols=('___wine_unix_call_funcs', '___wine_unix_call_wow64_funcs'))
        self.put('objects/'+inspector.NATIVE_PATH, data, 0o755)
        self.put('install/aarch64-unix/winemetal.so', data, 0o755)
        self.refuse('artifact_native_search_paths')

    def test_wrong_native_slice_refused(self):
        data = macho_image('winemetal.so', cpu=0x1000007)
        self.put('objects/'+inspector.NATIVE_PATH, data, 0o755)
        with self.assertRaises(Error):
            self.inspect()

    def test_native_install_name_and_export_tables_required(self):
        data = macho_image('wrong.so', rpaths=tuple(inspector.NATIVE_RPATHS))
        self.put('objects/'+inspector.NATIVE_PATH, data, 0o755)
        self.put('install/aarch64-unix/winemetal.so', data, 0o755)
        self.refuse('artifact_native_search_paths')
        data = macho_image('winemetal.so', rpaths=tuple(inspector.NATIVE_RPATHS))
        self.put('objects/'+inspector.NATIVE_PATH, data, 0o755)
        self.put('install/aarch64-unix/winemetal.so', data, 0o755)
        self.refuse('artifact_native_unix_exports')

    def test_wine_import_role_and_current_bytes_bound(self):
        self.value['wine_layout'][1]['origin_role'] = 'native'
        self.refuse('artifact_wine_origin_role')
        self.value['wine_layout'][1]['origin_role'] = 'companion'
        self.put(self.value['wine_layout'][1]['path'], b'not an import archive')
        self.refuse('artifact_wine_layout_changed')

    def test_native_counterpart_dependency_closed(self):
        info = {'dependencies': ['@rpath/missing.so']}
        with self.assertRaises(Error) as caught:
            inspector.native_dependencies(info, {})
        self.assertEqual(caught.exception.code, 'artifact_native_unaccounted_dependency')
        with self.assertRaises(Error):
            inspector.native_dependencies({'dependencies': ['/usr/lib/../private/lib.dylib']}, {})

    def test_shader_header_payload_mismatch_refused(self):
        self.put('objects/src/airconv/darwin/libairconv.a.p/air_msad.h', header(b'wrong', 'air_msad'))
        self.refuse('embedded_header_payload')

    def test_metallib_format_and_version_pin_required(self):
        self.put('objects/src/dxmt/libdxmt.a.p/dxmt_command.metallib', b'notMTLB'+bytes(40))
        self.refuse('artifact_metallib_format')
        self.put('objects/src/dxmt/libdxmt.a.p/dxmt_command.metallib', b'MTLB'+bytes(40))
        self.put('objects/version.h', b'#define DXMT_VERSION "parent Pear commit"\n')
        self.refuse('artifact_version_identity')

    def test_notice_bytes_and_generated_membership_required(self):
        path = self.value['generated_inputs'][0]['path']
        self.put(path, b'wrong')
        self.refuse('artifact_generated_changed')

    def test_generated_mode_boolean_is_not_integer(self):
        self.value['generated_inputs'][0]['mode'] = True
        self.refuse('artifact_generated_changed')

    def test_overclaimed_runtime_scope_refused(self):
        self.value['runtime_eligible'] = True
        self.refuse('artifact_runtime_overclaim')
        self.value['runtime_eligible'] = False
        self.value['pairing_verified'] = 0
        self.refuse('artifact_runtime_overclaim')

    def test_pe_import_paths_and_duplicate_names_refused(self):
        for names in [['../ntdll.dll'], ['ntdll.dll', 'NTDLL.DLL'], ['ntdll.dll\n']]:
            with self.assertRaises(Error):
                inspector.imports_policy(names)

    def test_entire_reused_reader_bytes_are_bound(self):
        self.put('tools/wine/modules.py', b'class PE: pass\n', base=self.repo)
        with self.assertRaises(Error) as caught:
            inspector.pe_readers(self.repo)
        self.assertEqual(caught.exception.code, 'artifact_pe_reader_identity')

    def test_malformed_native_symbol_bounds_refused(self):
        data = bytearray(macho_image('test.so', symbols=('A',)))
        # Last LC_SYMTAB points outside the file; no external tools are used.
        command_count, command_bytes = struct.unpack_from('<II', data, 16)
        struct.pack_into('<I', data, 32+command_bytes-24+8, len(data)+1)
        with self.assertRaises(Error) as caught:
            inspector.macho_details(bytes(data))
        self.assertEqual(caught.exception.code, 'artifact_native_symbol_bounds')

    def test_replay_binds_current_manifest_bytes_and_independent_builder(self):
        facts = self.inspect()
        data = encoded(facts)
        self.put('artifacts.json', data)
        value = copy.deepcopy(self.value)
        value['artifacts_manifest'] = {'path': 'artifacts.json', 'sha256': digest(data)}
        builder = mock.Mock()
        builder.verify_build.return_value = value
        original = inspector.load_local
        def selected(path, alias):
            return builder if Path(path).name == 'build.py' else original(path, alias)
        with mock.patch.object(inspector, 'load_local', side_effect=selected):
            self.assertEqual(inspector.verify_artifacts(self.root, repo=self.repo), facts)
            builder.verify_build.assert_called_once_with(self.root, repo=self.repo)
            self.put('artifacts.json', data+b' ')
            with self.assertRaises(Error) as caught:
                inspector.verify_artifacts(self.root, repo=self.repo)
            self.assertEqual(caught.exception.code, 'artifact_manifest_digest')


if __name__ == '__main__':
    unittest.main()
