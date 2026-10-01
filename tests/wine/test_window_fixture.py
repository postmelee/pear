"""Exercise the original window fixture with deterministic fake Win32 APIs.
This tests guest control flow, first-error retention and cleanup only. It does
not create native windows or qualify the Cocoa, Wine or ARM64 ABI boundaries.
"""
from pathlib import Path
import json
import subprocess
import tempfile
import unittest
from stage4_source import REPO

PRELUDE = r"""
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#include <setjmp.h>
#undef memset
#undef memcpy
#include "stage5_protocol.h"
#define WINAPI
#define CALLBACK
#define __declspec(x)
#define TRUE 1
#define FALSE 0
#define ERROR_INVALID_DATA 13
#define ERROR_INSUFFICIENT_BUFFER 122
#define ERROR_WRITE_FAULT 29
#define ERROR_INVALID_WINDOW_HANDLE 1400
#define STD_OUTPUT_HANDLE ((uint32_t)-11)
#define WM_CREATE 1
#define WM_DESTROY 2
#define WM_CLOSE 16
#define WM_QUIT 18
#define WM_MOUSEACTIVATE 33
#define MA_NOACTIVATE 3
#define WM_NCCREATE 129
#define WM_NCDESTROY 130
#define WM_SYSCOMMAND 274
#define SC_CLOSE 0xf060
#define PM_REMOVE 1
#define WS_EX_TOOLWINDOW 128
#define WS_EX_NOACTIVATE 0x8000000
#define WS_OVERLAPPEDWINDOW 0xcf0000
#define SW_SHOWNOACTIVATE 4
#define QS_ALLINPUT 0x4ff
#define MWMO_INPUTAVAILABLE 4
#define WAIT_FAILED ((uint32_t)-1)
#define WAIT_OBJECT_0 0
#define WAIT_TIMEOUT 258
#define MUTATE(value) (scenario==(value) && attempt_cycle==7)
typedef uint32_t DWORD,UINT;
typedef int32_t LONG;
typedef uint64_t ULONGLONG;
typedef wchar_t WCHAR;
typedef uintptr_t WPARAM;
typedef intptr_t LPARAM,LRESULT;
typedef void *HWND,*HMODULE;
typedef struct {void *lpCreateParams;} CREATESTRUCTW;
typedef LRESULT (*WNDPROC)(HWND,UINT,WPARAM,LPARAM);
typedef struct {WNDPROC lpfnWndProc;HMODULE hInstance;const WCHAR *lpszClassName;} WNDCLASSW;
typedef struct {HWND hwnd;UINT message;WPARAM wParam;LPARAM lParam;} MSG;
static unsigned scenario,attempt_cycle,registered,unregistered,live,queued,drain_calls,write_calls;
static unsigned title_updated,driver_references,exit_value,cleanup_failure;
static DWORD fake_error;
static uint64_t fake_teb=0x120000,fake_time;
static DWORD fake_tid=0x88;
static WCHAR fake_title[64];
static jmp_buf exit_target;
static DWORD GetLastError(void) {return fake_error;}
static DWORD GetCurrentThreadId(void) {return fake_tid;}
static DWORD GetCurrentProcessId(void) {return 0x99;}
static ULONGLONG GetTickCount64(void) {return fake_time;}
static HMODULE GetModuleHandleW(const WCHAR *name) {if(name)abort();return (void*)0x100000;}
static void *GetStdHandle(DWORD value) {if(value!=STD_OUTPUT_HANDLE)abort();return (void*)1;}
static int WriteFile(void *,const void *,DWORD,DWORD *,void *);
static HMODULE LoadLibraryW(const WCHAR *);
static void *GetProcAddress(HMODULE,const char *);
static unsigned RegisterClassW(const WNDCLASSW *);
static int UnregisterClassW(const WCHAR *,HMODULE);
static HWND CreateWindowExW(DWORD,const WCHAR *,const WCHAR *,DWORD,int,int,int,int,HWND,void *,HMODULE,void *);
static int ShowWindow(HWND,int);
static int IsWindow(HWND);
static DWORD GetWindowThreadProcessId(HWND,DWORD *);
static int SetWindowTextW(HWND,const WCHAR *);
static int GetWindowTextW(HWND,WCHAR *,int);
static int DestroyWindow(HWND);
static LRESULT DefWindowProcW(HWND,UINT,WPARAM,LPARAM);
static int PeekMessageW(MSG *,HWND,UINT,UINT,UINT);
static LRESULT DispatchMessageW(const MSG *);
static DWORD MsgWaitForMultipleObjectsEx(DWORD,const void *,DWORD,DWORD,DWORD);
static void ExitProcess(unsigned);
"""
TAIL = r"""
static LONG fake_control(pear_s5_request *r)
{
    if(r->magic!=PEAR_STAGE5_MAGIC || r->version!=1 || r->guest_teb!=fake_teb || r->guest_tid!=fake_tid)abort();
    if(r->operation==PEAR_S5_INIT || r->operation==PEAR_S5_FINAL){if(r->cycle||r->hwnd||r->token)abort();}
    else if(r->cycle!=attempt_cycle || r->hwnd!=(uintptr_t)active.hwnd || r->token!=PEAR_STAGE5_TOKEN(attempt_cycle))abort();
    r->host_entry=r->host_exit=0;r->native_pid=0x77;r->native_tid=0x88;r->teb=0x120000;
    r->created=r->armed=r->triggered=r->cocoa_close=r->dispatched=r->reentered=r->title_changed=1;
    r->callback_returned=r->destroyed=r->cocoa_destroyed=r->discarded=r->deallocated=r->completed=1;
    r->barriers=r->drains=1;r->callback_result=PEAR_STAGE5_REPLY(r->token);
    switch(r->operation){
    case PEAR_S5_INIT:if(live||registered||attempt_cycle)abort();return 0;
    case PEAR_S5_ARM:if(!live||queued)abort();return 0;
    case PEAR_S5_FIRE:if(!live||queued)abort();queued=MUTATE(10)?0:1;return 0;
    case PEAR_S5_REENTRY:
        if(!live||!title_updated)abort();
        if(MUTATE(6)){r->host_entry=UINT64_MAX;return (LONG)0xc0000022u;}
        if(MUTATE(7))r->host_exit=1;
        if(MUTATE(20))fake_teb++;
        return 0;
    case PEAR_S5_DRAIN:
        if(live)abort();++drain_calls;
        if(MUTATE(8))r->deallocated=0;
        if(MUTATE(9))r->callback_result++;
        if(MUTATE(11)&&drain_calls==2)PearWindowProc(active.hwnd,WM_CREATE,0,0);
        if(MUTATE(21) || drain_calls==1)return PEAR_STAGE5_PENDING;
        return 0;
    case PEAR_S5_FINAL:
        if(live||registered||unregistered!=1)abort();
        r->created=r->destroyed=r->deallocated=r->completed=20;
        if(scenario==15)return (LONG)0xc0000022u;
        return 0;
    default:abort();
    }
}
static int WriteFile(void *handle,const void *buffer,DWORD length,DWORD *written,void *overlapped)
{
    if(handle!=(void*)1||overlapped)abort();++write_calls;
    if(scenario==14&&write_calls==8){fake_error=998;return 0;}
    *written=(DWORD)fwrite(buffer,1,length,stdout);return *written==length;
}
static HMODULE LoadLibraryW(const WCHAR *name)
{
    if(wcscmp(name,L"winemac.drv"))abort();
    if(scenario==18){fake_error=998;return NULL;}
    ++driver_references;return (void*)0x200000;
}
static void *GetProcAddress(HMODULE value,const char *name)
{
    if(value!=(void*)0x200000||strcmp(name,"PearStage5Control"))abort();return (void*)(uintptr_t)fake_control;
}
static unsigned RegisterClassW(const WNDCLASSW *definition)
{
    if(wcscmp(definition->lpszClassName,L"PearStage5Window")||definition->lpfnWndProc!=PearWindowProc||registered)abort();
    registered=1;return 1;
}
static int UnregisterClassW(const WCHAR *name,HMODULE value)
{
    if(wcscmp(name,L"PearStage5Window")||value!=(void*)0x100000||!registered)abort();
    if(scenario==12||scenario==13||scenario==19){fake_error=997;cleanup_failure++;return 0;}
    if(live){fake_error=996;return 0;}
    registered=0;unregistered++;return 1;
}
static HWND CreateWindowExW(DWORD extended,const WCHAR *name,const WCHAR *title,DWORD style,int x,int y,int width,int height,
    HWND parent,void *menu,HMODULE value,void *param)
{
    (void)title;
    if(extended!=(WS_EX_TOOLWINDOW|WS_EX_NOACTIVATE)||style!=WS_OVERLAPPEDWINDOW||wcscmp(name,L"PearStage5Window")||
       parent||menu||value!=(void*)0x100000||width!=320||height!=180||x!=64||y!=64||live||!registered)abort();
    ++attempt_cycle;drain_calls=title_updated=0;
    if(MUTATE(16)){fake_error=998;return NULL;}
    HWND hwnd=(void*)(uintptr_t)(0x300000+attempt_cycle*16);live=1;
    CREATESTRUCTW created={param};
    if(!PearWindowProc(hwnd,WM_NCCREATE,0,(LPARAM)&created)||PearWindowProc(hwnd,WM_CREATE,0,0)){live=0;return NULL;}
    return hwnd;
}
static int ShowWindow(HWND hwnd,int command) {if(hwnd!=active.hwnd||command!=SW_SHOWNOACTIVATE||!live)abort();return 0;}
static int IsWindow(HWND hwnd) {return hwnd==active.hwnd&&live;}
static DWORD GetWindowThreadProcessId(HWND hwnd,DWORD *pid) {if(hwnd!=active.hwnd||!live)abort();*pid=0x99;return MUTATE(17)?0x89:0x88;}
static int SetWindowTextW(HWND hwnd,const WCHAR *title)
{
    if(hwnd!=active.hwnd||!live)abort();
    if(MUTATE(12)||MUTATE(13)){fake_error=998;return 0;}
    wcscpy(fake_title,title);title_updated=1;if(MUTATE(5))fake_teb++;return 1;
}
static int GetWindowTextW(HWND hwnd,WCHAR *title,int length)
{
    if(hwnd!=active.hwnd||!live||length!=64)abort();wcscpy(title,fake_title);return wcslen(title);
}
static int DestroyWindow(HWND hwnd)
{
    if(hwnd!=active.hwnd||!live)abort();
    PearWindowProc(hwnd,WM_DESTROY,0,0);PearWindowProc(hwnd,WM_NCDESTROY,0,0);live=0;return 1;
}
static LRESULT DefWindowProcW(HWND hwnd,UINT message,WPARAM wp,LPARAM lp)
{
    (void)lp;
    if(message==WM_SYSCOMMAND && PearWindowProc(hwnd,WM_MOUSEACTIVATE,0,0)!=MA_NOACTIVATE)abort();
    if(message==WM_SYSCOMMAND&&(wp&0xfff0)==SC_CLOSE)return PearWindowProc(hwnd,WM_CLOSE,0,0);
    return 0;
}
static int PeekMessageW(MSG *message,HWND hwnd,UINT low,UINT high,UINT remove)
{
    if(hwnd||low||high||remove!=PM_REMOVE)abort();
    if(!queued)return 0;
    message->hwnd=active.hwnd;message->message=queued==1||queued==3?PEAR_STAGE5_MESSAGE:WM_SYSCOMMAND;
    message->wParam=message->message==PEAR_STAGE5_MESSAGE?attempt_cycle:SC_CLOSE;
    message->lParam=message->message==PEAR_STAGE5_MESSAGE?PEAR_STAGE5_TOKEN(attempt_cycle):0;
    if(queued==1){
        if(MUTATE(1))message->lParam++;if(MUTATE(2))message->wParam++;
        if(MUTATE(4))fake_teb++;
        queued=MUTATE(3)?3:2;
    }else if(queued==3)queued=2;else queued=0;
    return 1;
}
static LRESULT DispatchMessageW(const MSG *message) {return PearWindowProc(message->hwnd,message->message,message->wParam,message->lParam);}
static DWORD MsgWaitForMultipleObjectsEx(DWORD count,const void *handles,DWORD milliseconds,DWORD mask,DWORD flags)
{
    if(count||handles||mask!=QS_ALLINPUT||flags!=MWMO_INPUTAVAILABLE||milliseconds!=20)abort();
    fake_time+=milliseconds;return WAIT_TIMEOUT;
}
static void ExitProcess(unsigned code) {exit_value=code;longjmp(exit_target,1);}
int main(int argc,char **argv)
{
    if(argc>1)scenario=(unsigned)atoi(argv[1]);
    if(!setjmp(exit_target))mainCRTStartup();
    printf("{\"harness\":1,\"exit\":%u,\"live\":%u,\"registered\":%u,\"unregistered\":%u,\"driver_references\":%u,"
        "\"error_step\":%u,\"error_code\":%u,\"cleanup_failure\":%u,\"drain_calls\":%u}\n",
        exit_value,live,registered,unregistered,driver_references,error_step,error_code,cleanup_failure,drain_calls);
    return 0;
}
"""

class WindowFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='pear-window-flow-')
        cls.addClassCleanup(cls.tmp.cleanup)
        folder=Path(cls.tmp.name)
        fixtures=REPO/'tests/wine/fixtures'
        (folder/'stage5_protocol.h').write_bytes((fixtures/'stage5_protocol.h').read_bytes())
        source=(fixtures/'window_pe.c').read_text()
        source='\n'.join(line for line in source.splitlines() if not line.startswith('#include'))
        begin=source.index('static uint64_t current_teb(void)')
        end=source.index('\n',begin)
        source=source[:begin]+'static uint64_t current_teb(void) {return fake_teb;}'+source[end:]
        (folder/'fixture.c').write_text(PRELUDE+source+TAIL)
        cls.exe=folder/'fixture'
        result=subprocess.run(['/usr/bin/clang','-std=gnu23','-fno-builtin','-fsanitize=undefined',
            '-fno-sanitize-recover=all',str(folder/'fixture.c'),'-o',str(cls.exe)],text=True,capture_output=True)
        if result.returncode:raise AssertionError(result.stderr)

    def run_case(self,scenario=0):
        result=subprocess.run([str(self.exe),str(scenario)],text=True,capture_output=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        return [json.loads(line) for line in result.stdout.splitlines()]

    def test_complete_twenty_cycles_and_output_contract(self):
        rows=self.run_case()
        self.assertEqual([r.get('record_kind') for r in rows[:-1]],
            ['pear_window_identity']+['pear_window_cycle']*20+['pear_window_result'])
        self.assertEqual(rows[0]['cycles'],20)
        self.assertNotEqual(rows[0]['driver_control'],0)
        for cycle,row in enumerate(rows[1:21],1):
            self.assertEqual(row['cycle'],cycle)
            self.assertEqual(row['token'],0x53350000+cycle)
            self.assertEqual(row['callback_result'],row['token']^0x13579bdf)
            self.assertEqual(row['late_callbacks'],0)
            for key in ['nccreate','create','app_messages','reentries','sysclose','close','destroy','ncdestroy',
                        'title_checks','hwnd_gone','drain_complete']:
                self.assertEqual(row[key],1,key)
        final=rows[-2]
        self.assertEqual(final['passed'],1)
        for key in ['cycles','app_messages','reentries','closes','destroys','ncdestroys']:self.assertEqual(final[key],20)
        for key in ['class_registered','class_unregistered','native_final','cleanup_complete']:self.assertEqual(final[key],1)
        self.assertEqual(final['error_step']+final['error_code']+final['late_callbacks'],0)
        self.assertEqual(rows[-1]['exit']+rows[-1]['live']+rows[-1]['registered'],0)
        self.assertEqual(rows[-1]['driver_references'],1)

    def test_rejects_wrong_payload_order_identity_and_native_evidence(self):
        for scenario in [1,2,3,4,5,7,8,9,10,11,15,16,17,18,19,20,21]:
            with self.subTest(scenario=scenario):
                rows=self.run_case(scenario)
                self.assertEqual(rows[-1]['exit'],1)
                self.assertNotEqual(rows[-1]['error_step'],0)
                self.assertEqual(rows[-2]['passed'],0)
                self.assertEqual(rows[-1]['live'],0)

    def test_native_operation_failure_keeps_original_status(self):
        rows=self.run_case(6)
        self.assertEqual(rows[-1]['exit'],1)
        self.assertEqual(rows[-1]['error_step'],27)
        self.assertEqual(rows[-1]['error_code'],0xc0000022)

    def test_cleanup_failure_preserves_first_operation_failure(self):
        rows=self.run_case(13)
        self.assertEqual(rows[-1]['error_step'],25)
        self.assertEqual(rows[-1]['error_code'],998)
        self.assertEqual(rows[-1]['cleanup_failure'],1)
        self.assertEqual(rows[-2]['cleanup_complete'],0)
        self.assertEqual(rows[-1]['live'],0)

    def test_output_failure_stops_cycles_and_cleans_up(self):
        rows=self.run_case(14)
        self.assertEqual(rows[-1]['error_step'],90)
        self.assertEqual(rows[-1]['error_code'],998)
        self.assertEqual(rows[-1]['exit'],1)
        self.assertEqual(rows[-1]['live']+rows[-1]['registered'],0)

if __name__=='__main__':unittest.main()
