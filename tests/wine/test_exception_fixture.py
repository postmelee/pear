"""Exercise the exact original C handler/control flow with fake Windows APIs.
No Windows, restricted ABI, native signal delivery or actual fault is executed.
"""
from pathlib import Path
import json
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parent
PRELUDE=r'''
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <setjmp.h>
#define WINAPI
#define EXCEPTION_CONTINUE_SEARCH 0
#define EXCEPTION_CONTINUE_EXECUTION (-1)
#define MEM_RESERVE 0x2000
#define MEM_COMMIT 0x1000
#define MEM_RELEASE 0x8000
#define PAGE_NOACCESS 1
#define PEAR_STAGE4_SENTINEL UINT64_C(0x3456789a)
typedef int32_t LONG;
typedef struct {uint64_t X0,X18,X19,Pc,Sp;uint32_t ContextFlags;} CONTEXT;
typedef struct {uint32_t ExceptionCode,ExceptionFlags,NumberParameters;void *ExceptionAddress;uint64_t ExceptionInformation[15];} EXCEPTION_RECORD;
typedef struct {EXCEPTION_RECORD *ExceptionRecord;CONTEXT *ContextRecord;} EXCEPTION_POINTERS;
typedef LONG (*handler_fn)(EXCEPTION_POINTERS *);
static handler_fn handlers[2];
static jmp_buf exit_env;
static uint32_t exit_status;
static unsigned mutation,add_fail,adds,removes,rows,emit_fail,allocs,frees;
static unsigned char fake_labels[16];
#define pear_fault_read_pc (fake_labels+0)
#define pear_fault_read_recovery (fake_labels+4)
#define pear_fault_write_pc (fake_labels+8)
#define pear_fault_write_recovery (fake_labels+12)
static void *AddVectoredExceptionHandler(unsigned first,handler_fn fn){if(++adds==add_fail)return NULL;handlers[first?0:1]=fn;return (void *)(uintptr_t)(first?1:2);}
static unsigned RemoveVectoredExceptionHandler(void *p){++removes;handlers[(uintptr_t)p-1]=NULL;return 1;}
static void ExitProcess(uint32_t value){exit_status=value;longjmp(exit_env,1);}
static void *GetCurrentProcess(void){return (void *)-1;}
static void TerminateProcess(void *p,uint32_t value){if(p!=(void *)-1)abort();ExitProcess(value);}
static unsigned GetCurrentProcessId(void){return 42;}
static void *GetModuleHandleW(const void *p){(void)p;return (void *)0x180000000;}
static void *VirtualAlloc(void *p,size_t n,unsigned t,unsigned prot){(void)p;(void)t;(void)prot;++allocs;return malloc(n);}
static unsigned VirtualFree(void *p,size_t n,unsigned t){(void)n;(void)t;++frees;free(p);return 1;}
static void RaiseException(void){}
static unsigned pear_fault_read(volatile unsigned char *);
static unsigned pear_fault_write(volatile unsigned char *);
static unsigned pear_raise_software(void *);
static int pear_emit(const char *kind,const char *const *names,const uint64_t *values,unsigned count){
 ++rows;printf("{\"record_kind\":\"%s\"",kind);for(unsigned i=0;i<count;++i)printf(",\"%s\":%llu",names[i],(unsigned long long)values[i]);puts("}");return !emit_fail;
}
'''
TAIL=r'''
static void deliver(unsigned operation,volatile unsigned char *address,unsigned software)
{
 EXCEPTION_RECORD record={0};CONTEXT context={0};
 record.ExceptionCode=software?0xe0424401u:(uint32_t)expectation.code;
 record.NumberParameters=software?0:2;record.ExceptionInformation[0]=operation;record.ExceptionInformation[1]=(uintptr_t)address;
 context.Pc=software?0x181234500:(uintptr_t)(operation?pear_fault_write_pc:pear_fault_read_pc);
 record.ExceptionAddress=(void *)(uintptr_t)context.Pc;context.X0=(uintptr_t)address;context.X18=0x77770000;
 context.X19=software?0:PEAR_STAGE4_SENTINEL;context.Sp=0x88880000;context.ContextFlags=0x400017;
 switch(mutation){case 1:record.ExceptionCode^=1;break;case 2:record.ExceptionInformation[1]++;break;case 3:context.Pc+=4;break;
 case 4:record.ExceptionInformation[0]^=1;break;case 5:context.X18++;break;case 6:context.X19++;break;case 7:context.Sp++;break;
 case 8:record.NumberParameters=1;break;case 9:context.X0++;break;case 10:record.ExceptionAddress=(void *)1;break;case 11:record.ExceptionFlags=1;break;}
 EXCEPTION_POINTERS pointers={&record,&context};
 if(mutation==12){handlers[1](&pointers);abort();}
 if(handlers[0](&pointers)!=EXCEPTION_CONTINUE_SEARCH)abort();
 if(handlers[1](&pointers)!=EXCEPTION_CONTINUE_EXECUTION)abort();
 if(!software && context.Pc!=(expectation.code==0x80000001u?expectation.fault_pc:expectation.recovery_pc))abort();
}
static unsigned pear_fault_read(volatile unsigned char *address){deliver(0,address,0);return 0x5a;}
static unsigned pear_fault_write(volatile unsigned char *address){deliver(1,address,0);return 0x5a;}
static unsigned pear_raise_software(void *p){(void)p;deliver(0,NULL,1);return 1;}
int main(int argc,char **argv)
{
 unsigned scenario=argc>1?(unsigned)atoi(argv[1]):0;mutation=argc>2?(unsigned)atoi(argv[2]):0;
 if(scenario==2)add_fail=mutation;
 if(scenario==3)emit_fail=1;
 unsigned result=99;
 if(!setjmp(exit_env)){
  if(scenario==4){result=pear_exception_fatal(100);}
  else if(scenario==5){unsigned char byte=0;result=pear_expect_memory_fault(&byte,0,0xc0000005u);}
  else {result=pear_exception_initialize();if(!result){if(scenario==0)result=pear_exception_checks();
   else {unsigned char byte=17;result=pear_expect_memory_fault(&byte,scenario==6?1:0,scenario==7?0x80000001u:0xc0000005u);}
   if(!result)result=pear_exception_finish();}}
 }
 printf("{\"summary\":1,\"result\":%u,\"exit_status\":%u,\"adds\":%u,\"removes\":%u,\"rows\":%u,\"allocs\":%u,\"frees\":%u}\n",result,exit_status,adds,removes,rows,allocs,frees);
 return 0;
}
'''
class ExceptionFixtureTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='pear-stage4-exception-flow-');cls.addClassCleanup(cls.tmp.cleanup)
  src=(ROOT/'fixtures/exceptions_pe.c').read_text();src='\n'.join(line for line in src.splitlines() if not line.startswith('#include'))
  start=src.index('static uint64_t current_teb(void)');end=src.index('\nstatic int exception_event',start)
  src=src[:start]+'static uint64_t current_teb(void){return 0x77770000;}\n'+src[end:]
  folder=Path(cls.tmp.name);(folder/'main.c').write_text(PRELUDE+src+TAIL);cls.exe=folder/'test'
  proc=subprocess.run(['/usr/bin/clang','-std=gnu23','-fsanitize=undefined','-fno-sanitize-recover=all',str(folder/'main.c'),'-o',str(cls.exe)],capture_output=True,text=True)
  if proc.returncode:raise AssertionError(proc.stderr)
 def run_case(self,scenario=0,mutation=0):
  p=subprocess.run([str(self.exe),str(scenario),str(mutation)],capture_output=True,text=True,timeout=10)
  self.assertEqual(p.returncode,0,p.stderr);return [json.loads(line) for line in p.stdout.splitlines()]
 def test_software_and_owned_read_fault(self):
  rows=self.run_case();self.assertEqual(rows[-1]['result'],0);self.assertEqual(rows[-1]['exit_status'],0)
  self.assertEqual(rows[-1]['allocs'],rows[-1]['frees']);self.assertEqual(rows[-1]['removes'],2)
  events=[r for r in rows if r.get('record_kind')=='pear_exception_event'];self.assertEqual([r['kind'] for r in events],[1,2])
  self.assertTrue(all(r['order']==12 and r['continued']==1 for r in events))
 def test_reject_each_wrong_fault_context_and_handler_order(self):
  for mutation in range(1,13):
   with self.subTest(mutation=mutation):self.assertEqual(self.run_case(1,mutation)[-1]['exit_status'],96)
 def test_valid_write_and_guard_recovery(self):
  for scenario in (6,7):
   with self.subTest(scenario=scenario):self.assertEqual(self.run_case(scenario)[-1]['result'],0)
 def test_handler_setup_failures_cleanup(self):
  self.assertEqual(self.run_case(2,1)[-1]['result'],1)
  r=self.run_case(2,2)[-1];self.assertEqual(r['result'],2);self.assertEqual(r['removes'],1)
 def test_emit_failure_is_not_success(self):self.assertNotEqual(self.run_case(3)[-1]['result'],0)
 def test_helper_requires_initialization(self):self.assertEqual(self.run_case(5)[-1]['result'],1)
 def test_controlled_fatal_fault_records_before_termination(self):
  rows=self.run_case(4);self.assertEqual(rows[-1]['exit_status'],0xc0000005)
  self.assertEqual([r.get('record_kind') for r in rows[:-1]],['pear_stage4_child_ready','pear_stage4_child_fault'])
  self.assertEqual(rows[1]['continued'],0);self.assertEqual(rows[1]['order'],12)
if __name__=='__main__':unittest.main()
