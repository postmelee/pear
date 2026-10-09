/* SPDX-License-Identifier: MIT
 * Original redistributable large-image loader fixture. No game content.
 * Build either a real DLL (including attach failure) or its Wine API driver.
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>

static void text(const char *s) {
    DWORD n = 0, written; while (s[n]) ++n;
    WriteFile(GetStdHandle(STD_OUTPUT_HANDLE), s, n, &written, NULL);
}
static void hex(uint64_t v) {
    char s[17]; const char *digits = "0123456789abcdef";
    for (unsigned i=0;i<16;++i) s[15-i]=digits[(v>>(4*i))&15];
    s[16]=0; text(s);
}
#ifdef PEAR_DLL
static volatile unsigned char large_zero[57600000];
static volatile ULONG data = 0x13579bdf;
static volatile ULONG * volatile data_pointer = &data;
static ULONG WINAPI code(ULONG n) { return n ^ 0xa5c31f27; }
static ULONG (WINAPI * volatile code_pointer)(ULONG) = code;
static ULONG initialized;
__declspec(dllexport) ULONG WINAPI PearProbe(void) {
    if (initialized != 1 || data_pointer != &data || code_pointer != code ||
        code_pointer(0x1234) != (0x1234 ^ 0xa5c31f27) || *data_pointer != 0x13579bdf ||
        large_zero[0] || large_zero[sizeof(large_zero)-1]) return 0;
    large_zero[0]=1; large_zero[sizeof(large_zero)-1]=2; *data_pointer=9;
    return 42;
}
BOOL WINAPI DllMain(HINSTANCE instance, DWORD reason, LPVOID reserved) {
    (void)instance; (void)reserved;
    if (reason == DLL_PROCESS_ATTACH) {
#ifdef PEAR_FAIL_ATTACH
        text("PEAR_LOADER_ATTACH_REJECT\n"); return FALSE;
#else
        if (large_zero[0] || large_zero[sizeof(large_zero)-1] || initialized) return FALSE;
        initialized=1;
#endif
    }
    return TRUE;
}
#else
static WCHAR path[2048];
static void fail(unsigned step) { text("PEAR_LOADER_FAIL step=");hex(step);text(" error=");hex(GetLastError());text("\n");ExitProcess(90); }
static void name(const WCHAR *base) {
    DWORD n=GetModuleFileNameW(NULL,path,1800); if (!n || n>=1800) fail(1);
    while(n && path[n-1]!='\\') --n;
    while(*base) path[n++]=*base++; path[n]=0;
}
static void rejected(const WCHAR *base, unsigned id) {
    for (unsigned round=0;round<2;++round) {
        name(base); SetLastError(0); HMODULE m=LoadLibraryW(path);
        DWORD error=GetLastError(); if (m || !error || GetModuleHandleW(path)) fail(id);
        text("PEAR_LOADER_REJECT case=");hex(id);text(" round=");hex(round);text(" error=");hex(error);text("\n");
    }
}
static void accepted(const WCHAR *base, unsigned id, ULONG expected) {
    HMODULE prior=NULL;
    for (unsigned round=0;round<2;++round) {
        name(base); HMODULE m=LoadLibraryW(path); if(!m) fail(id);
        ULONG (WINAPI *probe)(void)=(void *)GetProcAddress(m,"PearProbe");
        const IMAGE_DOS_HEADER *dos=(void *)m;
        const IMAGE_NT_HEADERS64 *nt=(void *)((char *)m+dos->e_lfanew);
        if(!probe || probe()!=42 || nt->OptionalHeader.SizeOfImage!=expected ||
           (uintptr_t)m==0x180000000ULL || (round && m!=prior)) fail(id+1);
        text("PEAR_LOADER_PASS case=");hex(id);text(" round=");hex(round);text(" base=");hex((uintptr_t)m);text(" bytes=");hex(expected);text("\n");
        prior=m; if(!FreeLibrary(m) || GetModuleHandleW(path)) fail(id+2);
    }
}
void mainCRTStartup(void) {
#ifdef _M_ARM64
    text("PEAR_LOADER_BEGIN role=arm64\n");
#else
    text("PEAR_LOADER_BEGIN role=x64\n");
#endif
    rejected(L"beyond.dll",10);
    rejected(L"attach-fail.dll",20);
    accepted(L"required.dll",30,57647104);
    accepted(L"ceiling.dll",40,67108864);
    text("PEAR_LOADER_END passed=8\n"); ExitProcess(42);
}
#endif
