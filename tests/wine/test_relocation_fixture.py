"""Control-flow and actual ARM64 DLL indirection checks for original fixtures.

The native harness injects Win32 results into two copies of the DLL functions.
The compile-only checks bind a Windows DLL's indirect operands to its bytes.
Neither executes a PE or proves runtime relocation; the signed Wine suite
and independently parsed PE bytes establish that separate gate.
Original harness and checker code: SPDX-License-Identifier: MIT.
"""
import hashlib
import json
import platform
import struct
import sys
import re
from pathlib import Path
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'tools/wine'))
import build
from common import load_json
from modules import PE

FIXTURES = Path(__file__).resolve().parent / 'fixtures'
HEADER = r'''
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#define WINAPI
#define __declspec(x)
#define TRUE 1
#define ERROR_INVALID_DATA 13
#define ERROR_BUFFER_OVERFLOW 111
#define ERROR_WRITE_FAULT 29
#define GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS 4
#define GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT 2
#define MEM_RESERVE 0x2000
#define PAGE_NOACCESS 1
#define STD_OUTPUT_HANDLE 1
typedef uint32_t DWORD;
typedef uint32_t ULONG;
typedef size_t SIZE_T;
typedef uintptr_t ULONG_PTR;
typedef int32_t LONG;
typedef wchar_t WCHAR;
typedef void *HMODULE;
typedef struct { DWORD State, Protect; } MEMORY_BASIC_INFORMATION;
static unsigned scenario, copied, freed[2], refs[2], probe_invocations;
static DWORD last_error;
static int fail_output;
static DWORD GetLastError(void) { return last_error; }
static void SetLastError(DWORD error) { last_error = error; }
'''

STUBS = r'''
static unsigned module_index(HMODULE module)
{
    if (module == (HMODULE)0x20010000) return 0;
    if (module == (HMODULE)0x20020000) return 1;
    abort();
}
static DWORD GetModuleFileNameW(HMODULE module, WCHAR *value, DWORD capacity)
{
    if (module || capacity != 1024) abort();
    if (scenario == 1) { last_error = 126; return 0; }
    if (scenario == 18) return capacity;
    wcscpy(value, L"Z:\\runtime\\abi-arm64.exe");
    return (DWORD)wcslen(value);
}
static DWORD GetCurrentDirectoryW(DWORD capacity, WCHAR *value)
{
    if (capacity != 1024) abort();
    wcscpy(value, L"Z:\\owned");
    return (DWORD)wcslen(value);
}
static unsigned file_index(const WCHAR *path)
{
    if (!wcscmp(path, L"Z:\\owned\\pear-relocation-a.dll")) return 0;
    if (!wcscmp(path, L"Z:\\owned\\pear-relocation-b.dll")) return 1;
    abort();
}
static int CopyFileW(const WCHAR *source, const WCHAR *target, int exclusive)
{
    if (wcscmp(source,L"Z:\\runtime\\lifetime-arm64.dll") || exclusive != 1) abort();
    unsigned index = file_index(target);
    if (index != copied) abort();
    if (scenario == 2 && index == 1) { last_error = 112; return 0; }
    ++copied;
    return 1;
}
static HMODULE LoadLibraryW(const WCHAR *path)
{
    unsigned index = file_index(path);
    if (copied != index + 1) abort();
    if (scenario == 3 && index == 1) { last_error = 193; return NULL; }
    if (scenario == 5 && index == 1) index = 0;
    ++refs[index];
    return (HMODULE)(uintptr_t)(0x20010000 + index * 65536);
}
static LONG probe_a(pear_relocation_observation *out, ULONG desired)
{
    ++probe_invocations;
    if (scenario == 26 && probe_invocations == 3) PearSecurityCookieA ^= 1;
    LONG result = PearRelocationProbeA(out,desired);
    if (scenario == 27) out->security_cookie ^= 1;
    if (scenario == 9) PearRelocationDataB = 0;
    if (scenario == 10) out->call_result = 0;
    if (scenario == 11) return (LONG)0xc000000d;
    return result;
}
static LONG probe_b(pear_relocation_observation *out, ULONG desired)
{
    ++probe_invocations;
    return PearRelocationProbeB(out,desired);
}
static uintptr_t GetProcAddress(HMODULE module, const char *name)
{
    unsigned index = module_index(module);
    if (!refs[index]) abort();
    if (scenario == 4 && index == 1) { last_error = 127; return 0; }
    if (!strcmp(name,"PearSecurityCookie")) return (uintptr_t)((index || scenario == 22) ? &PearSecurityCookieB : &PearSecurityCookieA);
    if (!strcmp(name,"PearRelocationProbe")) return (uintptr_t)(index ? probe_b : probe_a);
    if (!strcmp(name,"PearRelocationCode"))
        return (uintptr_t)((index || scenario == 6 || scenario == 16) ? PearRelocationCodeB : PearRelocationCodeA);
    if (!strcmp(name,"PearRelocationData"))
        return (uintptr_t)(index ? &PearRelocationDataB : &PearRelocationDataA);
    if (!strcmp(name,"PearRelocationCodePointer"))
        return (uintptr_t)(index ? &PearRelocationCodePointerB : &PearRelocationCodePointerA);
    if (!strcmp(name,"PearRelocationDataPointer"))
        return (uintptr_t)((index || scenario == 7) ? &PearRelocationDataPointerB : &PearRelocationDataPointerA);
    abort();
}
static int FreeLibrary(HMODULE module)
{
    unsigned index = module_index(module);
    ++freed[index];
    if ((scenario == 12 || scenario == 16) && index == 0) { last_error = 201; return 0; }
    if (!refs[index]) abort();
    --refs[index];
    return 1;
}
static int GetModuleHandleExW(DWORD flags, const WCHAR *address, HMODULE *out)
{
    unsigned index = module_index((HMODULE)address);
    if (flags != 6) abort();
    if (refs[index] || (scenario == 13 && index == 0)) { *out = (HMODULE)address; return 1; }
    *out = NULL;
    return 0;
}
static size_t VirtualQuery(const void *address, MEMORY_BASIC_INFORMATION *memory, size_t size)
{
    unsigned index = module_index((HMODULE)address);
    if (size != sizeof(*memory)) abort();
    if (scenario == 20 && index == 0) { last_error = 998; return 0; }
    memory->State = (scenario == 14 && index == 0) ? 0x1000 : MEM_RESERVE;
    memory->Protect = PAGE_NOACCESS;
    return size;
}
static void *GetStdHandle(DWORD which) { if (which != STD_OUTPUT_HANDLE) abort(); return (void *)1; }
static int WriteFile(void *handle, const void *data, DWORD size, DWORD *written, void *unused)
{
    if (handle != (void *)1 || unused) abort();
    if (fail_output == 1) { fail_output = 0; last_error = 112; return 0; }
    *written = (DWORD)fwrite(data,1,size,stdout);
    if (scenario == 21 && !fail_output) { --*written; fail_output = 2; }
    return 1;
}
'''

MAIN = r'''
int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    scenario = (unsigned)strtoul(argv[1],NULL,10);
    /* Synthetic initialized values exercise checks; this does not run Wine. */
    PearSecurityCookieA = 0x112233445566ULL; PearSecurityCookieB = 0x778899aabbccULL;
    if (scenario == 23) PearSecurityCookieA = 0;
    if (scenario == 24) PearSecurityCookieA = PEAR_SECURITY_COOKIE_DEFAULT;
    if (scenario == 25) PearSecurityCookieA = (ULONG_PTR)1 << 48;
    if (scenario == 8) PearRelocationDataA = 1;
    if (scenario == 15) fail_output = 1;
    if (scenario == 17) PearRelocationCodePointerA = PearRelocationCodeB;
    int valid = scenario == 19 ? 0 : relocation_check();
    if (!relocation_report()) return 3;
    printf("{\"valid\":%d,\"copied\":%u,\"free_calls\":[%u,%u],\"refs\":[%u,%u],\"probe_invocations\":%u}\n",
           valid,copied,freed[0],freed[1],refs[0],refs[1],probe_invocations);
    return 0;
}
'''


def actual_source():
    abi = (FIXTURES / 'abi_pe.c').read_text()
    dll = (FIXTURES / 'lifetime_pe.c').read_text()
    protocol = (FIXTURES / 'lifetime_pe.h').read_text()
    protocol = protocol[protocol.index('#define PEAR_SECURITY_COOKIE_DEFAULT'):protocol.index('#endif')]
    dll = dll[dll.index('__declspec(dllexport) volatile ULONG_PTR PearSecurityCookie'):
              dll.index('static pear_lifetime_control *control;')]
    copies = []
    for suffix in ('A', 'B'):
        copy = dll
        for name in ('PearSecurityCookie', 'pear_load_config', '_load_config_used', 'PearRelocationAccess', 'PearRelocationCodePointer', 'PearRelocationDataPointer', 'PearRelocationProbe',
                     'PearRelocationCode', 'PearRelocationData'):
            # Token replacement preserves the actual initializer/probe body.
            copy = re.sub(r'\b' + name + r'\b', name + suffix, copy)
        copies.append(copy)
    declarations = abi[abi.index('static unsigned relocation_error,'):
                       abi.index('static void record_error(')]
    functions = abi[abi.index('static void relocation_fail('):abi.index('static int exercise(void)')]
    formatting = abi[abi.index('static char output[1024]'):abi.index('static int lifetime_event(',
                                                                          abi.index('static char output[1024]'))]
    reports = abi[abi.index('static int relocation_event(', abi.index('static char output[1024]')):
                  abi.index('static int lifetime_report(')]
    return HEADER + protocol + ''.join(copies) + STUBS + declarations + functions + formatting + reports + MAIN


class RelocationFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory(prefix='pear-relocation-fixture-')
        root = Path(cls.directory.name)
        source = root / 'fixture.c'
        source.write_text(actual_source())
        cls.binary = root / 'fixture'
        result = subprocess.run(['clang','-std=c11','-Wall','-Wextra','-Werror','-O1',
                                 '-fsanitize=undefined','-fno-sanitize-recover=all',
                                 str(source),'-o',str(cls.binary)],capture_output=True,text=True,timeout=30)
        if result.returncode:
            raise AssertionError(result.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def run_case(self, scenario):
        result = subprocess.run([str(self.binary),str(scenario)],capture_output=True,text=True,
                                timeout=10,check=True)
        self.assertEqual(result.stderr,'')
        return [json.loads(line) for line in result.stdout.splitlines()]

    def test_two_copies_keep_independent_values_and_emit_real_observations(self):
        rows = self.run_case(0)
        probes, retired, report, calls = rows[:4], rows[4:6], rows[6], rows[7]
        self.assertEqual([(row['copy'],row['round']) for row in probes],[(0,0),(1,0),(0,1),(1,1)])
        self.assertEqual([row['peer_value'] for row in probes],[0x13579bdf,0x10203040,0x10203041,0x50607080])
        self.assertEqual([row['before'] for row in probes],[0x13579bdf,0x13579bdf,0x10203040,0x10203041])
        for row in probes:
            self.assertEqual(row['code_pointer'],row['code_address'])
            self.assertEqual(row['data_pointer'],row['data_address'])
            self.assertEqual(row['call_result'],row['after'] ^ 0xa5c31f27)
        self.assertEqual([row['security_cookie'] for row in probes],
                         [0x112233445566, 0x778899aabbcc, 0x112233445566, 0x778899aabbcc])
        self.assertNotEqual(probes[0]['security_cookie_address'], probes[1]['security_cookie_address'])
        self.assertNotEqual(probes[0]['data_address'],probes[1]['data_address'])
        self.assertEqual([(row['event'],row['copy']) for row in retired],[('retired',0),('retired',1)])
        self.assertEqual(report,{'version':1,'record_kind':'pear_relocation_result','passed':True,
            'error_step':0,'win32_error':0,'copies':2,'loads':2,'probe_calls':4,'code_pointer_checks':4,
            'data_pointer_checks':4,'value_checks':4,'retirements':2})
        self.assertEqual(calls,{'valid':1,'copied':2,'free_calls':[1,1],'refs':[0,0],'probe_invocations':4})

    def test_setup_failure_releases_every_acquired_reference(self):
        for scenario,step,code,frees in ((1,1,126,[0,0]),(2,3,112,[1,0]),(3,4,193,[1,0]),
                                         (4,5,127,[1,1]),(5,6,13,[2,0]),(18,1,111,[0,0])):
            with self.subTest(scenario=scenario):
                *_, report, calls = self.run_case(scenario)
                self.assertEqual((report['passed'],report['error_step'],report['win32_error']),(False,step,code))
                self.assertEqual(calls['free_calls'],frees)
                self.assertEqual(calls['refs'],[0,0])

    def test_bad_pointers_data_code_and_peer_values_fail_and_cleanup(self):
        for scenario,step in ((6,9),(7,10),(8,11),(9,11),(10,11),(11,8),(17,8)):
            with self.subTest(scenario=scenario):
                *_, report, calls = self.run_case(scenario)
                self.assertEqual((report['passed'],report['error_step'],report['win32_error']),(False,step,13))
                self.assertEqual(calls['free_calls'],[1,1])
                self.assertEqual(calls['refs'],[0,0])

    def test_invalid_cookie_destination_value_and_instability_fail_and_cleanup(self):
        for scenario in (22, 23, 24, 25, 26, 27):
            with self.subTest(scenario=scenario):
                *_, report, calls = self.run_case(scenario)
                self.assertEqual((report['passed'], report['error_step'], report['win32_error']),
                                 (False, 15, 13))
                self.assertEqual(calls['free_calls'], [1, 1])
                self.assertEqual(calls['refs'], [0, 0])

    def test_retirement_must_be_observed_and_cleanup_failure_does_not_pass(self):
        for scenario,step,code in ((12,12,201),(13,13,13),(14,13,13),(20,13,998)):
            with self.subTest(scenario=scenario):
                rows = self.run_case(scenario)
                report,calls=rows[-2:]
                self.assertEqual((report['passed'],report['error_step'],report['win32_error']),(False,step,code))
                self.assertEqual(calls['free_calls'],[1,1])
                self.assertEqual(report['retirements'],1)
                self.assertEqual([row['copy'] for row in rows if row.get('event')=='retired'],[1])

    def test_first_pointer_error_survives_paired_release_failure(self):
        *_, report,calls=self.run_case(16)
        self.assertEqual((report['error_step'],report['win32_error']),(9,13))
        self.assertEqual(calls['free_calls'],[1,1])
        self.assertEqual(calls['refs'],[1,0])

    def test_unperformed_relocation_check_cannot_report_success(self):
        report, calls = self.run_case(19)
        self.assertFalse(report['passed'])
        self.assertEqual((report['copies'], report['probe_calls'], report['retirements']), (0, 0, 0))
        self.assertEqual(calls['probe_invocations'], 0)

    def test_output_failure_still_releases_both_modules(self):
        for scenario, code in ((15,112),(21,29)):
            with self.subTest(scenario=scenario):
                *_, report,calls=self.run_case(scenario)
                self.assertEqual((report['passed'],report['error_step'],report['win32_error']),(False,7,code))
                self.assertEqual(calls['free_calls'],[1,1])
                self.assertEqual(calls['refs'],[0,0])



def inspect_relocation_indirection(binary, disassembly):
    """Check this fixture's bounded ARM64 indirection contract, without execution.

    Independent PE exports locate both routines and pointer cells. Every reader
    word is bound to the supplied DLL. Only the helper's straight-line operand
    dependencies and the caller's four-instruction argument setup are checked;
    this is not a general ARM64 verifier or proof of runtime relocation.
    """
    def require(condition, reason):
        if not condition:
            raise ValueError('relocation_indirection_' + reason)

    require(isinstance(disassembly, str) and len(disassembly) <= 1024 * 1024, 'reader_limit')
    pe = PE(binary)
    require(pe.machine == 0xaa64, 'machine')
    names = ('PearRelocationAccess', 'PearRelocationProbe',
             'PearRelocationCodePointer', 'PearRelocationDataPointer')
    exports = pe.exports()
    addresses = {}
    for name in names:
        matches = [row for row in exports if row['name'] == name]
        require(len(matches) == 1 and 'forwarder' not in matches[0], 'export')
        addresses[name] = pe.base + matches[0]['rva']
    require(len(set(addresses.values())) == 4, 'export_alias')
    blocks = {name: [] for name in names[:2]}
    active = None
    for line in disassembly.splitlines():
        label = re.fullmatch(r'([0-9a-fA-F]+) <([^>]+)>:', line.strip())
        if label:
            active = label[2] if label[2] in blocks else None
            if active:
                require(int(label[1], 16) == addresses[active], 'reader_export')
            continue
        instruction = re.match(r'^\s*([0-9a-fA-F]+):\s+([0-9a-fA-F]{8})\s', line)
        if instruction and active:
            address, word = int(instruction[1], 16), int(instruction[2], 16)
            rows = blocks[active]
            require(len(rows) < 128 and address == addresses[active] + 4 * len(rows), 'instruction_bounds')
            require(pe.u('I', pe.offset(address - pe.base, 4)) == word, 'reader_bytes')
            rows.append((address, word))
    for name, rows in blocks.items():
        require(rows and rows[-1][1] == 0xd65f03c0, 'routine_end')
        pe.code_range(addresses[name] - pe.base, len(rows) * 4)

    # Fixed helper ABI, independent of compiler-selected temporary registers.
    registers = {0: 'out', 1: 'value', 2: 'code_cell', 3: 'data_cell'}
    records, memory, calls = [], [], 0
    helper = blocks['PearRelocationAccess']
    for index, (_, word) in enumerate(helper):
        rt, rn = word & 31, (word >> 5) & 31
        kind = word & 0xffc00000
        if word in (0xd10043ff, 0x910043ff):  # The bounded 16-byte frame only.
            require(index in (0, len(helper) - 2), 'frame_order')
        elif kind in (0xa9000000, 0xa9400000):
            second = (word >> 10) & 31
            require(rn == 31 and not ((word >> 15) & 127) and
                    19 <= rt <= 30 and 19 <= second <= 30, 'stack_pair')
            if kind == 0xa9400000:
                registers.pop(rt, None)
                registers.pop(second, None)
        elif (word & 0xffe0ffe0) in (0xaa0003e0, 0x2a0003e0):
            require(rt != 31 and (word >> 16) & 31 != 31, 'zero_register')
            value = registers.get((word >> 16) & 31)
            if not word & 0x80000000:
                require(value in ('value', 'before', 'after', 'code_result'), 'narrow_pointer')
            registers[rt] = value
        elif kind in (0xf9400000, 0xb9400000, 0xf9000000, 0xb9000000):
            require(rt != 31 and rn != 31, 'zero_register')
            wide = bool(word & 0x40000000)
            offset = ((word >> 10) & 4095) * (8 if wide else 4)
            base = registers.get(rn)
            if kind == 0xf9400000:
                require(offset == 0 and base in ('code_cell', 'data_cell'), 'pointer_load')
                registers[rt] = 'code_pointer' if base == 'code_cell' else 'data_pointer'
            elif kind == 0xb9400000:
                require(offset == 0 and base == 'data_pointer', 'data_load')
                require(memory in ([], ['read', 'write']), 'data_order')
                registers[rt] = 'before' if not memory else 'after'
                memory.append('read')
            elif base == 'data_pointer':
                require(not wide and offset == 0 and registers.get(rt) == 'value' and
                        memory == ['read'], 'data_store')
                memory.append('write')
            else:
                require(base == 'out', 'observation_base')
                records.append((offset, 8 if wide else 4, registers.get(rt)))
        elif (word & 0xfffffc1f) == 0xd63f0000:
            require(rn != 31, 'zero_register')
            require(registers.get(rn) == 'code_pointer' and registers.get(0) == 'value' and
                    memory == ['read', 'write', 'read'] and calls == 0, 'indirect_call')
            calls += 1
            registers = {reg: value for reg, value in registers.items() if 19 <= reg <= 29}
            registers[0] = 'code_result'
        elif word == 0xd65f03c0:
            require(index == len(helper) - 1, 'early_return')
        else:
            raise ValueError('relocation_indirection_unsupported_helper_instruction')
    require(calls == 1 and memory == ['read', 'write', 'read'], 'operations')
    require(records == [(8, 8, 'code_pointer'), (32, 8, 'data_pointer'),
                        (48, 4, 'before'), (52, 4, 'after'), (56, 4, 'code_result')], 'observations')

    def signed(value, bits):
        return value - (1 << bits) if value & (1 << (bits - 1)) else value

    probe = blocks['PearRelocationProbe']
    direct = [(index, address + (signed(word & 0x3ffffff, 26) << 2))
              for index, (address, word) in enumerate(probe) if word & 0xfc000000 == 0x94000000]
    require(len(direct) == 1 and direct[0][1] == addresses['PearRelocationAccess'], 'probe_call')
    call_index = direct[0][0]
    argument_end = call_index
    # The cookie observation needs out after the call. Permit exactly one
    # harmless copy to a callee-saved register; it cannot overwrite x2 or x3.
    if call_index:
        preceding = probe[call_index - 1][1]
        if (preceding & 0xffe0ffe0) == 0xaa0003e0 and (preceding >> 16) & 31 == 0 and 19 <= preceding & 31 <= 29:
            argument_end -= 1
    require(argument_end >= 4, 'argument_setup')
    for pair, register, name in ((probe[argument_end-4:argument_end-2], 2, names[2]),
                                (probe[argument_end-2:argument_end], 3, names[3])):
        (address, page), (_, add) = pair
        require(page & 0x9f000000 == 0x90000000 and page & 31 == register and
                add & 0xff800000 == 0x91000000 and add & 31 == register and
                (add >> 5) & 31 == register, 'argument_setup')
        immediate = signed((((page >> 5) & 0x7ffff) << 2) | ((page >> 29) & 3), 21)
        value = (address & ~4095) + (immediate << 12)
        value += ((add >> 10) & 4095) << (12 if add & (1 << 22) else 0)
        require(value == addresses[name], 'argument_cell')
    return {'schema_version': 1, 'scope': 'original-fixture-arm64-indirection-only',
            'binary_sha256': hashlib.sha256(binary).hexdigest(),
            'disassembly_sha256': hashlib.sha256(disassembly.encode()).hexdigest(),
            'instruction_counts': {name: len(rows) for name, rows in blocks.items()},
            'reader_words_bound': True, 'exported_cell_arguments_bound': True,
            'observed_operands_bound': True, 'indirect_code_calls': calls,
            'indirect_data_reads': 2, 'indirect_data_writes': 1, 'execution_performed': False}


class RelocationBinaryTests(unittest.TestCase):
    """Compile and inspect actual Windows ARM64 DLLs; never execute a PE."""
    @classmethod
    def setUpClass(cls):
        cls.tools = REPO / '.build/task4/tools'
        cls.reader = cls.tools / 'llvm-mingw/bin/llvm-objdump'
        if platform.system() != 'Darwin' or not cls.reader.is_file() or not (cls.tools / 'llvm-mingw/bin/clang').is_file():
            raise unittest.SkipTest('Prepared macOS LLVM tools unavailable; actual Windows DLL gate unperformed')
        cls.directory = tempfile.TemporaryDirectory(prefix='pear-relocation-binary-')
        cls.addClassCleanup(cls.directory.cleanup)
        cls.root = Path(cls.directory.name)
        cls.destination = cls.root / 'install/libexec/pear-stage3/lifetime-arm64.dll'
        cls.destination.parent.mkdir(parents=True)
        lock = load_json(REPO / build.RECORDS['toolchain'])
        cls.command = ['/usr/bin/arch', '-arm64', *build.fixture_commands(
            cls.root, cls.tools, lock, 'api-abi', 'page-wx')['fixture-lifetime-dll']]
        cls.command = [str(FIXTURES / 'lifetime_pe.c') if arg == str(build.REPO / 'tests/wine/fixtures/lifetime_pe.c')
                       else arg for arg in cls.command]
        cls.compile(cls.command)
        cls.binary = cls.destination.read_bytes()
        cls.disassembly = cls.disassemble(cls.destination)

    @staticmethod
    def compile(command):
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        if result.returncode or result.stderr:
            raise AssertionError(result.stderr or str(result.returncode))

    @classmethod
    def disassemble(cls, path):
        result = subprocess.run(['/usr/bin/arch', '-arm64', str(cls.reader),
            '--disassemble-symbols=PearRelocationAccess,PearRelocationProbe', str(path)],
            capture_output=True, text=True, timeout=30, check=True)
        if result.stderr or len(result.stdout) > 1024 * 1024:
            raise AssertionError('Unexpected binary reader output')
        return result.stdout

    def test_production_windows_dll_uses_actual_cell_operands(self):
        result = inspect_relocation_indirection(self.binary, self.disassembly)
        self.assertEqual(result['indirect_code_calls'], 1)
        self.assertEqual(result['indirect_data_reads'], 2)
        self.assertEqual(result['indirect_data_writes'], 1)
        self.assertFalse(result['execution_performed'])

    def test_windows_dll_has_real_relocated_loader_cookie_input(self):
        pe = PE(self.binary)
        exports = [row for row in pe.exports() if row['name'] == 'PearSecurityCookie']
        self.assertEqual(len(exports), 1)
        self.assertNotIn('forwarder', exports[0])
        cookie = exports[0]['rva']
        self.assertEqual(cookie % 8, 0)
        sections = [row for row in pe.sections if row['rva'] <= cookie and
                    cookie + 8 <= row['rva'] + row['virtual_size']]
        self.assertEqual(len(sections), 1)
        self.assertTrue(sections[0]['characteristics'] & 0x80000000)
        self.assertFalse(sections[0]['characteristics'] & 0x20000000)
        self.assertEqual(pe.u('Q', pe.offset(cookie, 8)), 0x00002b992ddfa232)
        config, size = pe.dirs[10]
        self.assertEqual(size, 96)
        self.assertEqual(pe.u('I', pe.offset(config, 4)), 96)
        self.assertEqual(pe.u('Q', pe.offset(config + 88, 8)), pe.base + cookie)
        start, length = pe.dirs[5]
        cursor, targets = 0, []
        while cursor < length:
            page, block = pe.unpack('II', pe.offset(start + cursor, 8))
            self.assertTrue(8 <= block <= length - cursor and block % 2 == 0)
            for at in range(cursor + 8, cursor + block, 2):
                entry = pe.u('H', pe.offset(start + at, 2))
                if entry >> 12:
                    self.assertEqual(entry >> 12, 10)
                    targets.append(page + (entry & 4095))
            cursor += block
        self.assertEqual(targets.count(config + 88), 1)
        self.assertEqual(len(targets), 3)

    def test_old_optimized_probe_is_rejected_even_with_unused_valid_helper(self):
        source = (FIXTURES / 'lifetime_pe.c').read_text()
        call = 'PearRelocationAccess(out, value, &PearRelocationCodePointer, &PearRelocationDataPointer);'
        self.assertEqual(source.count(call), 1)
        source = source.replace(call, 'out->before = *data; *data = value; out->after = *data; out->call_result = code(value);')
        copied = self.root / 'optimized.c'
        copied.write_text(source)
        (self.root / 'lifetime_pe.h').write_bytes((FIXTURES / 'lifetime_pe.h').read_bytes())
        target = self.root / 'optimized.dll'
        command = [str(copied) if arg == str(FIXTURES / 'lifetime_pe.c') else
                   str(target) if arg == str(self.destination) else arg for arg in self.command]
        self.compile(command)
        disassembly = self.disassemble(target)
        self.assertIn('blr', disassembly)  # An unrelated valid helper cannot satisfy the caller gate.
        with self.assertRaisesRegex(ValueError, 'relocation_indirection_probe_call'):
            inspect_relocation_indirection(target.read_bytes(), disassembly)

    def test_actual_wrong_code_and_data_operands_are_rejected(self):
        pe = PE(self.binary)
        access = next(row['rva'] for row in pe.exports() if row['name'] == 'PearRelocationAccess')
        for name, match, replacement, error in (
            ('code', lambda word: word & 0xfffffc1f == 0xd63f0000,
             lambda word: (word & ~(31 << 5)) | (1 << 5), 'indirect_call'),
            ('data', lambda word: word & 0xffc00000 == 0xf9400000 and (word >> 5) & 31 == 3,
             lambda word: (word & ~(31 << 5)) | (2 << 5), 'data_load')):
            with self.subTest(operand=name):
                data = bytearray(self.binary)
                found = False
                for offset in range(0, 128 * 4, 4):
                    location = pe.offset(access + offset, 4)
                    word = pe.u('I', location)
                    if match(word):
                        struct.pack_into('<I', data, location, replacement(word))
                        found = True
                        break
                    if word == 0xd65f03c0:
                        break
                self.assertTrue(found)
                path = self.root / (name + '-wrong.dll')
                path.write_bytes(data)
                with self.assertRaisesRegex(ValueError, 'relocation_indirection_' + error):
                    inspect_relocation_indirection(bytes(data), self.disassemble(path))
                with self.assertRaisesRegex(ValueError, 'relocation_indirection_reader_bytes'):
                    inspect_relocation_indirection(bytes(data), self.disassembly)

    def test_discarded_pointer_and_call_clobbered_link_register_are_rejected(self):
        # Mutate the actual instruction words and ask LLVM to read those bytes.
        # XZR never carries a loaded value; BLR overwrites LR even if it held out.
        controls = (
            ('discarded', {0xf9400048: 0xf940005f, 0xf9000408: 0xf900041f,
                           0xd63f0100: 0xd63f03e0}, 'zero_register'),
            ('link-register', {0xaa0003f3: 0xaa0003fe, 0xb9003a60: 0xb9003bc0},
             'observation_base'),
        )
        pe = PE(self.binary)
        access = next(row['rva'] for row in pe.exports() if row['name'] == 'PearRelocationAccess')
        for name, replacements, error in controls:
            with self.subTest(control=name):
                data, found = bytearray(self.binary), set()
                for offset in range(0, 128 * 4, 4):
                    location = pe.offset(access + offset, 4)
                    word = pe.u('I', location)
                    if word in replacements:
                        struct.pack_into('<I', data, location, replacements[word])
                        found.add(word)
                    if word == 0xd65f03c0:
                        break
                self.assertEqual(found, set(replacements))
                path = self.root / (name + '-wrong.dll')
                path.write_bytes(data)
                with self.assertRaisesRegex(ValueError, 'relocation_indirection_' + error):
                    inspect_relocation_indirection(bytes(data), self.disassemble(path))

    def test_preserved_out_copy_cannot_clobber_a_cell_argument(self):
        pe = PE(self.binary)
        probe = next(row['rva'] for row in pe.exports() if row['name'] == 'PearRelocationProbe')
        data, found = bytearray(self.binary), False
        for offset in range(0, 128 * 4, 4):
            location = pe.offset(probe + offset, 4)
            word = pe.u('I', location)
            if word & 0xfc000000 == 0x94000000:
                previous = pe.u('I', location - 4)
                self.assertEqual(previous & 0xffe0ffe0, 0xaa0003e0)
                self.assertEqual((previous >> 16) & 31, 0)
                self.assertTrue(19 <= previous & 31 <= 29)
                struct.pack_into('<I', data, location - 4, (previous & ~31) | 2)
                found = True
                break
            if word == 0xd65f03c0:
                break
        self.assertTrue(found)
        target = self.root / 'clobbered-argument.dll'
        target.write_bytes(data)
        with self.assertRaisesRegex(ValueError, 'relocation_indirection_argument_setup'):
            inspect_relocation_indirection(bytes(data), self.disassemble(target))

    def test_reader_bounds_and_export_identity_are_checked(self):
        with self.assertRaisesRegex(ValueError, 'reader_limit'):
            inspect_relocation_indirection(self.binary, ' ' * (1024 * 1024 + 1))
        with self.assertRaisesRegex(ValueError, 'reader_export'):
            inspect_relocation_indirection(self.binary, re.sub(
                r'[0-9a-f]+ <PearRelocationAccess>:', '0 <PearRelocationAccess>:', self.disassembly))
        row = next(line for line in self.disassembly.splitlines() if re.match(r'^[0-9a-f]+:', line))
        with self.assertRaisesRegex(ValueError, 'instruction_bounds'):
            inspect_relocation_indirection(self.binary, self.disassembly.replace(row, row + '\n' + row, 1))


if __name__ == '__main__':
    unittest.main()
