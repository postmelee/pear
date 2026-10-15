/* SPDX-FileCopyrightText: 2026 Pear contributors
 * SPDX-License-Identifier: GPL-3.0-or-later
 * Synthetic processes only. Parent retains handles to every child it cleans up.
 */
#define _WIN32_WINNT 0x0A00
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct { HANDLE child, grandchild; DWORD error; } Result;
static char self[MAX_PATH];
static HANDLE number(const char *s) { return (HANDLE)(ULONG_PTR)strtoull(s, NULL, 10); }
static void cleanup(HANDLE h) {
    if (!h) return;
    if (WaitForSingleObject(h, 0) == WAIT_TIMEOUT) TerminateProcess(h, 91);
    WaitForSingleObject(h, 5000); CloseHandle(h);
}
static BOOL spawn(const char *exe, char *cmd, HANDLE job, PROCESS_INFORMATION *pi) {
    STARTUPINFOEXA si = {0}; SIZE_T bytes=0; BOOL ok;
    si.StartupInfo.cb=sizeof(si);
    InitializeProcThreadAttributeList(NULL,1,0,&bytes);
    si.lpAttributeList=HeapAlloc(GetProcessHeap(),0,bytes);
    if (!si.lpAttributeList || !InitializeProcThreadAttributeList(si.lpAttributeList,1,0,&bytes)) return FALSE;
    if (job && !UpdateProcThreadAttribute(si.lpAttributeList,0,PROC_THREAD_ATTRIBUTE_JOB_LIST,&job,sizeof(job),NULL,NULL)) return FALSE;
    ok=CreateProcessA(exe,cmd,NULL,NULL,TRUE,EXTENDED_STARTUPINFO_PRESENT,NULL,NULL,&si.StartupInfo,pi);
    DeleteProcThreadAttributeList(si.lpAttributeList); HeapFree(GetProcessHeap(),0,si.lpAttributeList);
    return ok;
}
int main(int argc, char **argv) {
    GetModuleFileNameA(NULL,self,MAX_PATH);
    if (argc>1 && !strcmp(argv[1],"leaf")) { Sleep(60000); return 0; }
    if (argc>1 && !strcmp(argv[1],"child")) {
        HANDLE map=number(argv[2]), observer=number(argv[3]), ready=number(argv[4]);
        Result *r=MapViewOfFile(map,FILE_MAP_ALL_ACCESS,0,0,sizeof(*r));
        HANDLE inner=CreateJobObjectW(NULL,NULL); PROCESS_INFORMATION p={0}; char cmd[2048];
        snprintf(cmd,sizeof(cmd),"\"%s\" leaf --type=utility",self);
        if (!inner || !spawn(self,cmd,inner,&p) || !DuplicateHandle(GetCurrentProcess(),p.hProcess,observer,&r->grandchild,0,FALSE,DUPLICATE_SAME_ACCESS)) r->error=GetLastError();
        SetEvent(ready); Sleep(60000); cleanup(p.hProcess); if(p.hThread)CloseHandle(p.hThread); if(inner)CloseHandle(inner); return 0;
    }
    if (argc>1 && !strcmp(argv[1],"browser")) {
        HANDLE map=number(argv[2]), observer=number(argv[3]), ready=number(argv[4]), release=number(argv[5]), caller=number(argv[6]);
        Result *r=MapViewOfFile(map,FILE_MAP_ALL_ACCESS,0,0,sizeof(*r));
        char cmd[2048]; PROCESS_INFORMATION p={0};
        snprintf(cmd,sizeof(cmd),"\"%s\" child %s %s %s --type=%s",argv[7],argv[2],argv[3],argv[4],argv[8]);
        if (!spawn(argv[7],cmd,caller,&p) || !DuplicateHandle(GetCurrentProcess(),p.hProcess,observer,&r->child,0,FALSE,DUPLICATE_SAME_ACCESS)) {r->error=GetLastError();SetEvent(ready);}
        WaitForSingleObject(release,20000);
        if(p.hThread)CloseHandle(p.hThread); if(p.hProcess)CloseHandle(p.hProcess); return 0;
    }
    const struct {const char *name; int enabled,wrong,other,parent_role; const char *role; int dies;} cases[]={
        {"renderer-owned",1,0,0,0,"renderer",1},{"utility-owned",1,0,0,0,"utility",1},
        {"optin-off",0,0,0,0,"renderer",0},{"wrong-parent-path",1,1,0,0,"renderer",0},
        {"other-child-image",1,0,1,0,"renderer",0},{"renderer-parent-excluded",1,0,0,1,"renderer",0},
        {"unknown-role",1,0,0,0,"renderer-extra",0}
    };
    int failed=0;
    for (unsigned i=0;i<sizeof(cases)/sizeof(cases[0]);++i) {
        SECURITY_ATTRIBUTES sa={sizeof(sa),NULL,TRUE}; PROCESS_INFORMATION browser={0}, outsider={0};
        HANDLE map=CreateFileMappingA(INVALID_HANDLE_VALUE,&sa,PAGE_READWRITE,0,sizeof(Result),NULL), observer=NULL;
        HANDLE ready=CreateEventA(&sa,TRUE,FALSE,NULL), release=CreateEventA(&sa,TRUE,FALSE,NULL), caller=CreateJobObjectA(&sa,NULL);
        Result *r=MapViewOfFile(map,FILE_MAP_ALL_ACCESS,0,0,sizeof(*r)); BOOL member=FALSE; char cmd[4096],other[MAX_PATH];
        snprintf(other,sizeof(other),"%s",self); char *slash=strrchr(other,'\\'); if(!slash)return 40; strcpy(slash+1,"other.exe");
        SetEnvironmentVariableA("PEAR_STEAM_WEBHELPER_PATH",cases[i].enabled ? (cases[i].wrong?other:self) : NULL);
        if(!map||!r||!ready||!release||!caller||!DuplicateHandle(GetCurrentProcess(),GetCurrentProcess(),GetCurrentProcess(),&observer,PROCESS_DUP_HANDLE,TRUE,0))return 41;
        ZeroMemory(r,sizeof(*r));
        snprintf(cmd,sizeof(cmd),"\"%s\" leaf",self);
        if(!spawn(self,cmd,NULL,&outsider))return 42;
        snprintf(cmd,sizeof(cmd),"\"%s\" browser %llu %llu %llu %llu %llu \"%s\" %s%s",self,
          (unsigned long long)(ULONG_PTR)map,(unsigned long long)(ULONG_PTR)observer,(unsigned long long)(ULONG_PTR)ready,
          (unsigned long long)(ULONG_PTR)release,(unsigned long long)(ULONG_PTR)caller,cases[i].other?other:self,cases[i].role,
          cases[i].parent_role?" --type=utility":"");
        int ok=spawn(self,cmd,NULL,&browser) && WaitForSingleObject(ready,10000)==WAIT_OBJECT_0 && !r->error && r->child && r->grandchild;
        if(ok)ok=IsProcessInJob(r->child,caller,&member)&&member;
        if(ok)ok=WaitForSingleObject(browser.hProcess,0)==WAIT_TIMEOUT && WaitForSingleObject(r->child,0)==WAIT_TIMEOUT;
        SetEvent(release);
        if(ok)ok=WaitForSingleObject(browser.hProcess,5000)==WAIT_OBJECT_0;
        if(ok){DWORD expect=cases[i].dies?WAIT_OBJECT_0:WAIT_TIMEOUT; ok=WaitForSingleObject(r->child,cases[i].dies?5000:200)==expect && WaitForSingleObject(r->grandchild,cases[i].dies?5000:200)==expect && WaitForSingleObject(outsider.hProcess,0)==WAIT_TIMEOUT;}
        printf("%s: %s (error=%lu)\n",cases[i].name,ok?"PASS":"FAIL",r->error);fflush(stdout);failed+=!ok;
        cleanup(r->child);cleanup(r->grandchild);cleanup(browser.hProcess);cleanup(outsider.hProcess);
        if(browser.hThread)CloseHandle(browser.hThread);if(outsider.hThread)CloseHandle(outsider.hThread);
        UnmapViewOfFile(r);CloseHandle(map);CloseHandle(ready);CloseHandle(release);CloseHandle(caller);CloseHandle(observer);
    }
    return failed?1:0;
}
