/* Synthetic observer inputs only: no signal delivery or ABI mode change. */
#include "signal_native.c"
#include <stdio.h>
pthread_key_t thread_data_key;
static unsigned char test_mode(void){return 0;}
unsigned char (*pear_x18_getter)(void)=test_mode;
static unsigned checks;
#define CHECK(c) do {++checks;if(!(c)){fprintf(stderr,"check failed at %u\n",__LINE__);return 1;}}while(0)
static struct __darwin_mcontext64 machine;
static ucontext_t context;
static void reset(unsigned phase)
{
 memset(slots,0,sizeof(slots));memset(&machine,0,sizeof(machine));memset(&context,0,sizeof(context));
 context.uc_mcontext=&machine;enabled=1;
 slots[0].registered=slots[0].armed=1;slots[0].teb=0x700000;
 slots[0].guest_low=0x100000;slots[0].guest_high=0x110000;slots[0].kernel_low=0x200000;slots[0].kernel_high=0x210000;
 slots[0].guest_begin=0x300000;slots[0].guest_end=0x300020;slots[0].observation.phase=phase;
 machine.__ss.__sp=phase==PEAR_S4_HOST?0x208000:0x108000;
 machine.__ss.__pc=phase==PEAR_S4_HOST?(uintptr_t)pear_stage4_host_begin+4:0x300004;
 machine.__ss.__x[18]=slots[0].teb;machine.__ss.__x[19]=PEAR_STAGE4_SENTINEL;
}
int main(void)
{
 for(unsigned phase=1;phase<=3;++phase){
  reset(phase);unsigned mode=phase==PEAR_S4_HOST?0:1;
  pear_stage4_signal_before(SIGUSR1,mode,0,&context);
  CHECK(slots[0].observation.before_count==1 && !slots[0].observation.bad && !slots[0].observation.after_count);
  pear_s4_request request={0};snapshot(&slots[0],&request);
  CHECK(request.observation.before_count==1 && !request.observation.after_count && request.observation.before_pc==machine.__ss.__pc);
  pear_stage4_signal_after(SIGUSR1,mode,&context);
  CHECK(slots[0].observation.after_count==1 && !slots[0].observation.bad && slots[0].release==1);
  memset(&request,0,sizeof(request));snapshot(&slots[0],&request);
  CHECK(request.observation.after_count==1 && request.observation.before_pc==request.observation.after_pc);
 }
 for(unsigned bad=0;bad<5;++bad){
  reset(1);unsigned mode=1,handler=0;
  if(bad==0)machine.__ss.__pc=0x400000;
  if(bad==1)machine.__ss.__x[18]++;
  if(bad==2)machine.__ss.__x[19]++;
  if(bad==3)mode=0;
  if(bad==4)handler=1;
  pear_stage4_signal_before(SIGUSR1,mode,handler,&context);
  CHECK(slots[0].observation.before_count==1 && slots[0].observation.bad);
 }
 for(unsigned bad=0;bad<4;++bad){
  reset(1);pear_stage4_signal_before(SIGUSR1,1,0,&context);
  if(bad==0)machine.__ss.__pc+=4;
  if(bad==1)machine.__ss.__x[18]++;
  if(bad==2)machine.__ss.__x[19]++;
  pear_stage4_signal_after(SIGUSR1,bad==3?0:1,&context);
  CHECK(slots[0].observation.after_count==1 && (slots[0].observation.bad&16));
 }
 reset(1);enabled=0;pear_stage4_signal_before(SIGUSR1,1,0,&context);CHECK(!slots[0].observation.before_count);
 reset(1);slots[0].armed=0;pear_stage4_signal_before(SIGUSR1,1,0,&context);CHECK(!slots[0].observation.before_count);
 reset(1);machine.__ss.__sp=0x500000;pear_stage4_signal_before(SIGUSR1,1,0,&context);CHECK(!slots[0].observation.before_count);
 reset(1);pear_stage4_signal_before(SIGUSR2,1,0,&context);CHECK(!slots[0].observation.before_count);
 reset(1);pear_stage4_signal_before(SIGUSR1,1,0,&context);pear_stage4_signal_before(SIGUSR1,1,0,&context);CHECK(slots[0].observation.bad&1);
 pear_stage4_signal_after(SIGUSR1,1,&context);pear_stage4_signal_after(SIGUSR1,1,&context);CHECK(slots[0].observation.bad&8);
 int channel[2];char descriptor[32],bytes[8192];size_t used=0;
 CHECK(!pipe(channel));snprintf(descriptor,sizeof(descriptor),"%d",channel[1]);
 CHECK(!setenv("PEAR_BOOTSTRAP_FD",descriptor,1));CHECK(!setenv("PEAR_BOOTSTRAP_NONCE","0123456789abcdef0123456789abcdef",1));
 CHECK(!setenv("PEAR_BOOTSTRAP_GENERATION","0",1));
 slots[0].teb=slots[0].tid=slots[0].ntdll_base=slots[0].guest_begin=slots[0].guest_end=UINT64_MAX;
 slots[0].init_seen=slots[0].init_mode=slots[0].init_tls_match=UINT64_MAX;
 for(unsigned i=0;i<sizeof(slots[0].observation)/8;++i)((uint64_t *)&slots[0].observation)[i]=UINT64_MAX;
 slots[0].observation.phase=3;
 emit_registration(0,&slots[0]);emit_signal(0,&slots[0],&slots[0].observation);close(channel[1]);
 for(;;){ssize_t got=read(channel[0],bytes+used,sizeof(bytes)-used);if(got<0)return 2;if(!got)break;used+=got;if(used==sizeof(bytes))return 3;}
 close(channel[0]);unsigned lines=0,length=0,maximum=0;
 for(size_t i=0;i<used;++i){++length;if(bytes[i]=='\n'){if(length>maximum)maximum=length;++lines;CHECK(length<=472);length=0;}}
 CHECK(lines==12 && !length);fwrite(bytes,1,used,stdout);
 printf("{\"native_part_rows\":%u,\"maximum_line_bytes\":%u}\n",lines,maximum);
 printf("{\"synthetic_observer_checks\":%u,\"passed\":true,\"signal_delivery_performed\":false,\"restricted_mode_performed\":false}\n",checks);
 return 0;
}
