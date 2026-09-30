/* Source-bound synthetic Stage 5 observer tests. No Wine or UI is executed. */
#import "config.h"
#import "macdrv.h"
#import "cocoa_event.h"
#import "cocoa_window.h"
#include "stage5_protocol.h"
#include "wine/pear_bootstrap.h"
#include <dlfcn.h>
static unsigned fake_main,pending_wake,hold_wake,post_fail,post_deallocate,consume_in_process;
static void fake_deallocate_during_post(void);
static unsigned diagnostic_calls,diagnostic_queue_calls,fake_pending_queue;
static struct macdrv_thread_data diagnostic_thread;
static macdrv_event diagnostic_event;
static struct macdrv_thread_data *fake_thread_data(void){return &diagnostic_thread;}
void pear_stage5_diag_app(uintptr_t target,struct pear_s5_diag_snapshot *out){(void)target;diagnostic_calls++;out->main_thread=fake_main;out->app_windows=out->app_target=1;}
void pear_stage5_queue_snapshot(void *queue,uintptr_t target,struct pear_s5_diag_snapshot *out){(void)queue;(void)target;diagnostic_queue_calls++;out->queue_total=out->queue_target=fake_pending_queue;out->queue_target_event_refs=2*fake_pending_queue;}
int pear_stage5_post_wake(uint64_t payload){if(post_fail)return 0;if(post_deallocate)fake_deallocate_during_post();pending_wake=payload;return 1;}
static unsigned parts,snapshots,images,skip_title,bad_reply,checks,failed,fake_empty=1,capture_events;
static unsigned char fake_mode(void){return 0;}
static TEB *fake_teb(void){return (TEB *)(uintptr_t)0x10000;}
static DWORD fake_thread(void){return 0x80;}
static int fake_pthread_main(void){return fake_main;}
static int fake_thread_id(pthread_t thread,uint64_t *value){(void)thread;*value=fake_main?11:22;return 0;}
static void *fake_symbol(void *handle,const char *name){(void)handle;return !strcmp(name,"os_custom_x18_abi_enabled")?(void *)fake_mode:NULL;}
static int fake_address(const void *address,Dl_info *info){(void)address;memset(info,0,sizeof(*info));info->dli_fbase=(void *)(uintptr_t)0x20000;return 1;}
static void fake_event(const char *role,const char *name,const char *detail){if(strcmp(role,"loader")||strcmp(name,"stage5_window")||strlen(detail)>220)failed=1;parts++;if(capture_events)printf("{\"event\":\"stage5_window\"%s}\n",detail);}
static void fake_snapshot(const char *role,const char *name){if(strcmp(role,"loader")||strcmp(name,"stage5_window_images"))failed=1;snapshots++;}
static void fake_main_block(dispatch_block_t block){unsigned previous=fake_main;fake_main=1;if(pending_wake && !hold_wake){unsigned payload=pending_wake;pending_wake=0;pear_stage5_window_wake_consumed(PEAR_STAGE5_WAKE_SUBTYPE,PEAR_STAGE5_WAKE_TAG,payload,0);}@autoreleasepool{block();}fake_main=previous;}
static WINBOOL fake_process(DWORD mask){if(mask!=QS_ALLINPUT)failed=1;if(consume_in_process)fake_main_block(^{});return fake_empty;}
static void fake_images(const char *role){if(strcmp(role,"loader"))failed=1;images++;}
static INT WINAPI fake_classname(HWND hwnd,WINBOOL real,UNICODE_STRING *text){(void)hwnd;(void)real;static const WCHAR name[]={'P','e','a','r','S','t','a','g','e','5','W','i','n','d','o','w',0};memcpy(text->Buffer,name,sizeof(name));text->Length=32;return 16;}
static LRESULT WINAPI fake_message(HWND,UINT,WPARAM,LPARAM,void *,UINT,WINBOOL);
static void fake_census_dispatch(dispatch_queue_t queue,dispatch_block_t block){(void)queue;unsigned prior=fake_main;fake_main=1;block();fake_main=prior;}
#define dispatch_async fake_census_dispatch
#undef GetCurrentThreadId
#define GetCurrentThreadId fake_thread
#define NtCurrentTeb fake_teb
#define pthread_main_np fake_pthread_main
#define pthread_threadid_np fake_thread_id
#define dlsym fake_symbol
#define dladdr fake_address
#define pear_bootstrap_event fake_event
#define pear_bootstrap_snapshot fake_snapshot
#define pear_bootstrap_images fake_images
#define OnMainThread fake_main_block
#define macdrv_thread_data() fake_thread_data()
#define macdrv_ProcessEvents fake_process
#define NtUserGetClassName fake_classname
#define NtUserMessageCall fake_message
#include "window_native.m"
static void check(int value){checks++;if(!value)failed=1;}
static void fake_deallocate_during_post(void){pear_stage5_window_deallocated((void *)(uintptr_t)records[0].window);}
static void reset(void){memset(census.objects,0,sizeof(census.objects));memset(census.windows,0,sizeof(census.windows));census.used=census.overflow=census.errors=0;census.marker_submitted=census.marker_completed=0;pending_wake=hold_wake=post_fail=post_deallocate=consume_in_process=0;memset(wake_posted,0,sizeof(wake_posted));memset(wake_consumed,0,sizeof(wake_consumed));memset(consumed_barrier,0,sizeof(consumed_barrier));memset(diagnostic_close_hits,0,sizeof(diagnostic_close_hits));memset(diagnostic_first_ns,0,sizeof(diagnostic_first_ns));memset(&diagnostic_thread,0,sizeof(diagnostic_thread));diagnostic_thread.queue=(void *)(uintptr_t)0x30000;fake_pending_queue=0;memset(records,0,sizeof(records));memset(lookup_live,0,sizeof(lookup_live));memset(queue_empty,0,sizeof(queue_empty));initialized=created_count=completed_count=finalized=global_errors=0;owner_teb=owner_tid=driver_base=driver_entry=event_sequence=0;fake_main=parts=snapshots=images=skip_title=bad_reply=0;fake_empty=1;}
static void init_request(pear_s5_request *r,unsigned op,unsigned cycle){memset(r,0,sizeof(*r));r->magic=PEAR_STAGE5_MAGIC;r->version=1;r->operation=op;r->guest_teb=0x10000;r->guest_tid=0x80;if(cycle){r->cycle=cycle;r->hwnd=0x100+cycle;r->token=PEAR_STAGE5_TOKEN(cycle);}}
static NTSTATUS invoke(unsigned op,unsigned cycle,pear_s5_request *r){init_request(r,op,cycle);return pear_stage5_window_control(r);}
static LRESULT WINAPI fake_message(HWND hwnd,UINT msg,WPARAM wp,LPARAM lp,void *result,UINT type,WINBOOL ansi)
{
    check((uintptr_t)hwnd==0x100+wp && msg==PEAR_STAGE5_MESSAGE && (uint64_t)lp==PEAR_STAGE5_TOKEN(wp) && !result && type==NtUserSendMessage && !ansi);
    pear_s5_request r;
    if(!skip_title){fake_main=1;pear_stage5_window_title_changed((void *)(uintptr_t)records[wp-1].window,@"Pear Stage 5 callback");fake_main=0;}
    NTSTATUS status=invoke(PEAR_S5_REENTRY,wp,&r);
    if(skip_title)check(status!=0);else check(!status && r.reentered==1 && r.title_changed==1);
    return bad_reply?0:PEAR_STAGE5_REPLY(lp);
}
@interface PearFakeWindow : NSObject
- (void)performClose:(id)sender;
@end
@implementation PearFakeWindow
- (void)performClose:(id)sender{(void)sender;pear_stage5_window_close_requested(self);}
- (void)dealloc{uintptr_t identity=(uintptr_t)self;pear_stage5_window_diagnostic_deallocating((void *)identity);[super dealloc];pear_stage5_window_deallocated((void *)identity);}
@end
static PearFakeWindow *create(unsigned cycle)
{
    PearFakeWindow *window=[[PearFakeWindow alloc]init];void *hwnd=(void *)(uintptr_t)(0x100+cycle);
    pear_stage5_window_create_begin(hwnd);fake_main=1;pear_stage5_window_created(hwnd,window,(void *)(uintptr_t)0x30000);fake_main=0;return window;
}
static void close_window(PearFakeWindow *window)
{
    pear_stage5_window_destroy_begin(window);fake_main=1;pear_stage5_window_diagnostic_closed(window);pear_stage5_window_cocoa_destroyed(window);fake_main=0;pear_stage5_window_discarded(window);
}
/* Scalar turn tests exercise actual observer entrypoints without target messages. */
static void seed_turn(pear_s5_request *r)
{
    reset();check(!invoke(PEAR_S5_INIT,0,r));created_count=1;
    records[0].cycle=1;records[0].hwnd=0x101;records[0].token=PEAR_STAGE5_TOKEN(1);
    records[0].window=0x70000;records[0].queue=0x30000;lookup_live[0]=1;
    records[0].discarded=records[0].destroyed=records[0].cocoa_destroyed=1;
    records[0].barriers=records[0].drains=1;
}
int main(void)
{
    @autoreleasepool{
        setenv("PEAR_WINE_STAGE5_FIXTURE","1",1);setenv("PEAR_BOOTSTRAP_NONCE","0123456789abcdef0123456789abcdef",1);
        pear_s5_request r;reset();capture_events=1;check(!invoke(PEAR_S5_INIT,0,&r));check(snapshots==1 && images==1 && parts==3 && r.teb==0x10000 && r.native_tid==0x80);
        for(unsigned cycle=1;cycle<=20;cycle++){
            PearFakeWindow *window=create(cycle);check(!invoke(PEAR_S5_ARM,cycle,&r));check(!invoke(PEAR_S5_FIRE,cycle,&r));
            pear_stage5_window_dispatch(window,(void *)(uintptr_t)(0x100+cycle));close_window(window);
            if(cycle==1){fake_empty=0;check(invoke(PEAR_S5_DRAIN,cycle,&r)==STATUS_PENDING && !r.deallocated && !r.completed);}
            uintptr_t identity=(uintptr_t)window;[window release];
            if(cycle==1){check(invoke(PEAR_S5_DRAIN,cycle,&r)==STATUS_PENDING && r.deallocated==1 && !r.completed);fake_empty=1;}
            if(cycle>1)check(invoke(PEAR_S5_DRAIN,cycle,&r)==STATUS_PENDING && !r.completed);
            check(!invoke(PEAR_S5_DRAIN,cycle,&r));
            unsigned prior_errors=global_errors;fake_main=1;pear_stage5_window_created((void *)(uintptr_t)0x9000,(void *)identity,(void *)(uintptr_t)0x40000);fake_main=0;
            pear_stage5_window_any_event((void *)identity);check(global_errors==prior_errors && records[cycle-1].window==identity);check(r.completed==1 && !r.active && !r.errors && !r.late && r.deallocated==1);
        }
        fake_empty=0;check(invoke(PEAR_S5_FINAL,0,&r)==STATUS_UNSUCCESSFUL && !finalized);fake_empty=1;
        check(!invoke(PEAR_S5_FINAL,0,&r));check(r.completed==20 && r.created==20 && r.deallocated==20 && r.barriers==41 && r.drains==41 && !r.active && !r.errors);check(parts==773);capture_events=0;
        reset();check(!invoke(PEAR_S5_INIT,0,&r));PearFakeWindow *window=create(1);init_request(&r,PEAR_S5_ARM,1);r.guest_teb++;check(pear_stage5_window_control(&r)==STATUS_INVALID_PARAMETER);
        check(!invoke(PEAR_S5_ARM,1,&r));check(invoke(PEAR_S5_ARM,1,&r)==STATUS_INVALID_PARAMETER && r.errors);check(!invoke(PEAR_S5_FIRE,1,&r));
        pear_stage5_window_dispatch(window,(void *)(uintptr_t)0x101);close_window(window);pear_stage5_window_any_event(window);[window release];check(invoke(PEAR_S5_DRAIN,1,&r)==STATUS_UNSUCCESSFUL && r.late==1 && r.errors && !r.completed);
        reset();check(!invoke(PEAR_S5_INIT,0,&r));window=create(1);check(!invoke(PEAR_S5_ARM,1,&r));check(!invoke(PEAR_S5_FIRE,1,&r));skip_title=1;bad_reply=1;pear_stage5_window_dispatch(window,(void *)(uintptr_t)0x101);close_window(window);[window release];check(invoke(PEAR_S5_DRAIN,1,&r)==STATUS_UNSUCCESSFUL && !r.title_changed && !r.callback_result && r.errors && !r.completed);
        reset();check(!invoke(PEAR_S5_INIT,0,&r));window=create(1);check(!invoke(PEAR_S5_ARM,1,&r));check(!invoke(PEAR_S5_FIRE,1,&r));
        pear_stage5_window_dispatch(window,(void *)(uintptr_t)0x101);close_window(window);
        diagnostic_event.type=WINDOW_CLOSE_REQUESTED;diagnostic_event.window=(void *)window;diagnostic_event.refs=1;
        diagnostic_thread.current_event=&diagnostic_event;fake_pending_queue=1;
        for(unsigned attempt=0;attempt<100;attempt++)check(invoke(PEAR_S5_DRAIN,1,&r)==STATUS_PENDING && !r.deallocated && !r.completed);
        check(diagnostic_calls==3 && diagnostic_queue_calls>3);
        check(wake_posted[0]==100 && wake_consumed[0]==100 && r.drains==100);
        diagnostic_thread.current_event=NULL;[window release];
        check(invoke(PEAR_S5_DRAIN,1,&r)==STATUS_INVALID_PARAMETER && !r.completed);
        /* Each strict queue-state input independently prevents completion. */
        reset();check(!invoke(PEAR_S5_INIT,0,&r));window=create(1);check(!invoke(PEAR_S5_ARM,1,&r));check(!invoke(PEAR_S5_FIRE,1,&r));
        pear_stage5_window_dispatch(window,(void *)(uintptr_t)0x101);close_window(window);[window release];
        check(invoke(PEAR_S5_DRAIN,1,&r)==STATUS_PENDING && !r.completed); /* wake has not crossed a later barrier */
        fake_empty=0;check(invoke(PEAR_S5_DRAIN,1,&r)==STATUS_PENDING && !r.completed);check(queue_state(records,0)==14);
        fake_empty=1;fake_pending_queue=1;check(invoke(PEAR_S5_DRAIN,1,&r)==STATUS_PENDING && !r.completed);check(queue_state(records,1)==13);
        fake_pending_queue=0;diagnostic_thread.current_event=&diagnostic_event;
        check(invoke(PEAR_S5_DRAIN,1,&r)==STATUS_PENDING && !r.completed);check(queue_state(records,1)==11);
        diagnostic_thread.current_event=NULL;diagnostic_thread.queue=(void *)(uintptr_t)0x40000;
        check(queue_state(records,1)==7);check(invoke(PEAR_S5_DRAIN,1,&r)==STATUS_UNSUCCESSFUL && !r.completed);
        diagnostic_thread.queue=NULL;check(queue_state(records,1)==0);
        /* Even early deallocation and same-barrier consumption need a later barrier. */
        reset();check(!invoke(PEAR_S5_INIT,0,&r));window=create(1);check(!invoke(PEAR_S5_ARM,1,&r));check(!invoke(PEAR_S5_FIRE,1,&r));
        pear_stage5_window_dispatch(window,(void *)(uintptr_t)0x101);close_window(window);[window release];consume_in_process=1;
        check(invoke(PEAR_S5_DRAIN,1,&r)==STATUS_PENDING && r.deallocated==1 && !r.completed);
        check(wake_posted[0]==1 && wake_consumed[0]==1 && r.barriers==consumed_barrier[0]);
        consume_in_process=0;check(!invoke(PEAR_S5_DRAIN,1,&r) && r.completed==1 && r.barriers>consumed_barrier[0]);
        /* An unconsumed turn cannot overlap another, even across drain requests. */
        seed_turn(&r);hold_wake=1;
        for(unsigned i=0;i<3;i++)check(invoke(PEAR_S5_DRAIN,1,&r)==STATUS_PENDING && wake_posted[0]==1 && !wake_consumed[0]);
        hold_wake=0;records[0].deallocated=1;
        check(invoke(PEAR_S5_DRAIN,1,&r)==STATUS_PENDING && wake_posted[0]==1 && wake_consumed[0]==1);
        /* Failed posts preserve an explicit failure and cannot invent progress. */
        seed_turn(&r);post_fail=1;
        check(invoke(PEAR_S5_DRAIN,1,&r)==STATUS_UNSUCCESSFUL && !wake_posted[0] && r.errors);
        /* A later post racing real deallocation is conservatively rejected. */
        seed_turn(&r);wake_posted[0]=wake_consumed[0]=1;post_deallocate=1;
        check(invoke(PEAR_S5_DRAIN,1,&r)==STATUS_UNSUCCESSFUL && r.deallocated==1 && r.errors && !r.completed);
        /* Missing/duplicate/malformed/wrong-window ordinals never satisfy a turn. */
        const intptr_t payloads[]={0,-1,PEAR_STAGE5_WAKE_PAYLOAD(21,1),PEAR_STAGE5_WAKE_PAYLOAD(1,0),PEAR_STAGE5_WAKE_PAYLOAD(1,101),PEAR_STAGE5_WAKE_PAYLOAD(1,2)};
        for(unsigned i=0;i<sizeof(payloads)/sizeof(payloads[0]);i++){
            seed_turn(&r);wake_posted[0]=1;fake_main=1;
            pear_stage5_window_wake_consumed(PEAR_STAGE5_WAKE_SUBTYPE,PEAR_STAGE5_WAKE_TAG,payloads[i],0);fake_main=0;
            check(global_errors && !wake_consumed[0]);
        }
        for(unsigned i=0;i<4;i++){
            seed_turn(&r);wake_posted[0]=1;fake_main=i!=3;
            pear_stage5_window_wake_consumed(PEAR_STAGE5_WAKE_SUBTYPE+(i==0),PEAR_STAGE5_WAKE_TAG+(i==1),PEAR_STAGE5_WAKE_PAYLOAD(1,1),i==2);fake_main=0;
            check(global_errors && !wake_consumed[0]);
        }
        seed_turn(&r);wake_posted[0]=1;fake_main=1;
        pear_stage5_window_wake_consumed(PEAR_STAGE5_WAKE_SUBTYPE,PEAR_STAGE5_WAKE_TAG,PEAR_STAGE5_WAKE_PAYLOAD(1,1),0);
        check(!global_errors && wake_consumed[0]==1 && consumed_barrier[0]==1);
        pear_stage5_window_wake_consumed(PEAR_STAGE5_WAKE_SUBTYPE,PEAR_STAGE5_WAKE_TAG,PEAR_STAGE5_WAKE_PAYLOAD(1,1),0);fake_main=0;
        check(global_errors && wake_consumed[0]==1);
        seed_turn(&r);wake_posted[0]=1;records[0].completed=1;fake_main=1;
        pear_stage5_window_wake_consumed(PEAR_STAGE5_WAKE_SUBTYPE,PEAR_STAGE5_WAKE_TAG,PEAR_STAGE5_WAKE_PAYLOAD(1,1),0);fake_main=0;
        check(global_errors && !wake_consumed[0]);
        printf("{\"record_kind\":\"synthetic_window_observer\",\"checks\":%u,\"failed\":%u,\"wine_executed\":false,\"cocoa_windows_created\":false,\"restricted_mode_executed\":false}\n",checks,failed);
    }
    return failed?1:0;
}
