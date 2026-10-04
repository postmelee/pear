/* Original Pear finite ordinary ARM64 Win32 fixture. SPDX-License-Identifier: MIT.
 * No game, CPU translator, hybrid PE dispatch, external C runtime or input injection. */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include "protocol.h"
static LONG (WINAPI *control)(struct pear_pairing_request *);
static uint64_t teb,tid;
static DWORD primary_step,primary_error,cleanup_error,cleanup_flags,completed_phases;
static uint32_t control_status,bridge_status;
void *memset(void *out,int value,size_t bytes) { unsigned char *p=out;while(bytes--)*p++=(unsigned char)value;return out; }
void *memcpy(void *out,const void *in,size_t bytes) { unsigned char *p=out;const unsigned char *q=in;while(bytes--)*p++=*q++;return out; }
static uint64_t current_teb(void) { uint64_t value;__asm__ volatile("mov %0,x18":"=r"(value));return value; }
static LRESULT CALLBACK wndproc(HWND hwnd,UINT message,WPARAM wp,LPARAM lp)
{
    if(current_teb()!=teb || GetCurrentThreadId()!=tid) ExitProcess(30);
    return DefWindowProcW(hwnd,message,wp,lp);
}
static int invoke(unsigned op,HWND hwnd)
{
    struct pear_pairing_request r={0};
    r.magic=PEAR_PAIRING_MAGIC;r.version=1;r.bytes=sizeof(r);r.operation=op;
    r.hwnd=(uintptr_t)hwnd;r.cycle=1;r.guest_teb=current_teb();r.guest_tid=GetCurrentThreadId();
    r.x18_entry=r.x18_exit=UINT64_MAX;
    LONG status=control(&r);control_status=(uint32_t)status;bridge_status=(uint32_t)r.status;
    if(status || r.status || !r.flags || r.native_tid!=tid || r.x18_entry || r.x18_exit || current_teb()!=teb) return 0;
    if(op==PEAR_PAIRING_FINAL && (r.lease_count || r.attachment_count)) return 0;
    completed_phases=op;return 1;
}
static char terminal[512];static unsigned length;
static void text(const char *s) { while(*s && length<sizeof(terminal)) terminal[length++]=*s++; }
static void number(uint32_t n) { char digits[10];unsigned count=0;do { digits[count++]=(char)('0'+n%10);n/=10; } while(n);while(count && length<sizeof(terminal)) terminal[length++]=digits[--count]; }
static int emit_terminal(void)
{
    const char *keys[]={"primary_step","primary_error","control_status","bridge_status","cleanup_error","cleanup_flags","completed_phases"};
    uint32_t values[]={primary_step,primary_error,control_status,bridge_status,cleanup_error,cleanup_flags,completed_phases};
    text("{\"record_kind\":\"pear_metal_pairing_pe\",\"version\":1");
    for(unsigned i=0;i<7;i++) { text(",\"");text(keys[i]);text("\":");number(values[i]); }
    text("}\n");DWORD written=0;
    return length<sizeof(terminal) && WriteFile(GetStdHandle(STD_OUTPUT_HANDLE),terminal,length,&written,NULL) && written==length;
}
void mainCRTStartup(void)
{
    WNDCLASSW cls={0};HWND hwnd=NULL;HMODULE driver=NULL;unsigned step=1,registered=0;
    teb=current_teb();tid=GetCurrentThreadId();
    cls.lpfnWndProc=wndproc;cls.hInstance=GetModuleHandleW(NULL);cls.lpszClassName=L"PearMetalPairing";
    if(!RegisterClassW(&cls)) goto win32_failed;registered=1;
    step=2;hwnd=CreateWindowExW(WS_EX_NOACTIVATE,cls.lpszClassName,L"Pear Metal Pairing",WS_OVERLAPPEDWINDOW|WS_VISIBLE,80,80,320,240,NULL,NULL,cls.hInstance,NULL);
    if(!hwnd) goto win32_failed;
    step=3;driver=LoadLibraryW(L"winemac.drv");if(!driver) goto win32_failed;
    step=4;control=(void*)GetProcAddress(driver,"PearMetalPairingControl");if(!control) goto win32_failed;
    step=5;if(!invoke(PEAR_PAIRING_INIT,hwnd)) goto control_failed;
    step=6;if(!invoke(PEAR_PAIRING_RUN,hwnd)) goto control_failed;
    step=7;if(!SetWindowPos(hwnd,NULL,80,80,480,320,SWP_NOACTIVATE|SWP_NOZORDER)) goto win32_failed;
    step=8;if(!invoke(PEAR_PAIRING_RESIZE,hwnd)) goto control_failed;
    step=9;if(!invoke(PEAR_PAIRING_DETACH,hwnd)) goto control_failed;
    { HWND destroyed=hwnd;step=10;if(!DestroyWindow(hwnd)) goto win32_failed;hwnd=NULL;cleanup_flags|=1;
      step=11;if(!invoke(PEAR_PAIRING_DESTROYED,destroyed)) goto control_failed; }
    step=12;if(!invoke(PEAR_PAIRING_FINAL,NULL)) goto control_failed;
    goto done;
 win32_failed: primary_step=step;primary_error=GetLastError();goto done;
 control_failed: primary_step=step;primary_error=0;
 done:
    if(hwnd) { if(!DestroyWindow(hwnd)) cleanup_error|=1;else cleanup_flags|=1; }
    if(driver) { if(!FreeLibrary(driver)) cleanup_error|=2;else cleanup_flags|=2; }
    if(registered) { if(!UnregisterClassW(cls.lpszClassName,cls.hInstance)) cleanup_error|=4;else cleanup_flags|=4; }
    if(!emit_terminal()) cleanup_error|=8;
    ExitProcess(primary_step?1:cleanup_error?2:0);
}
