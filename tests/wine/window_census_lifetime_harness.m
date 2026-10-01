/* Source-bound ordinary Foundation lifetime checks. No Wine runtime or UI. */
#import "config.h"
#import "macdrv.h"
#import "cocoa_event.h"
#import "cocoa_window.h"
#define PEAR_S5_CENSUS_IMPLEMENTATION
#include "stage5_census.h"
#include <stdio.h>
static struct pear_s5_census_state state={.lock=PTHREAD_MUTEX_INITIALIZER};
static unsigned checks,failed,deallocated,terminal_observations;
static void check(int value){checks++;if(!value)failed++;}
void pear_stage5_census_object(unsigned kind,unsigned action,uintptr_t identity,uintptr_t target,unsigned type)
{
    if(action==PEAR_S5_CENSUS_FREE)terminal_observations++;
    pear_s5_census_object(&state,kind,action,identity,target,type);
}
@interface PearCensusObject : NSObject @end
@implementation PearCensusObject
- (void)dealloc {deallocated++;[super dealloc];}
@end
#include "event_lifetime_source.inc"
static void bind_query(macdrv_query *query)
{
#include "query_bind_source.inc"
}
int main(void)
{
    @autoreleasepool {
        struct pear_s5_census_snapshot out;
        PearCensusObject *object=[[PearCensusObject alloc]init];uintptr_t target=(uintptr_t)object;
        pear_s5_census_register_window(&state,1,target);
        macdrv_event *event=macdrv_create_event(WINDOW_CLOSE_REQUESTED,(WineWindow *)object);
        [object release];macdrv_retain_event(event);macdrv_release_event(event);
        pear_s5_census_read(&state,1,target,WINDOW_GOT_FOCUS,&out);
        check(!deallocated && !terminal_observations && out.complete && out.events_target==1);
        macdrv_release_event(event);pear_s5_census_read(&state,1,target,WINDOW_GOT_FOCUS,&out);
        check(deallocated==1 && terminal_observations==1 && out.complete && !out.events_live);

        object=[[PearCensusObject alloc]init];target=(uintptr_t)object;
        pear_s5_census_register_window(&state,2,target);
        macdrv_query *query=macdrv_create_query();query->window=[(WineWindow *)object retain];query->type=QUERY_MIN_MAX_INFO;
        [object release];pear_s5_census_read(&state,2,target,WINDOW_GOT_FOCUS,&out);
        check(!out.complete && out.queries_unbound==1 && deallocated==1);
        bind_query(query);macdrv_retain_query(query);macdrv_release_query(query);
        pear_s5_census_read(&state,2,target,WINDOW_GOT_FOCUS,&out);
        check(out.complete && out.queries_target==1 && deallocated==1);
        macdrv_release_query(query);pear_s5_census_read(&state,2,target,WINDOW_GOT_FOCUS,&out);
        check(out.complete && !out.queries_live && deallocated==2 && terminal_observations==2);

        object=[[PearCensusObject alloc]init];target=(uintptr_t)object;
        pear_s5_census_register_window(&state,3,target);
        query=macdrv_create_query();query->window=[(WineWindow *)object retain];query->type=QUERY_MIN_MAX_INFO;bind_query(query);
        event=macdrv_create_event(QUERY_EVENT,(WineWindow *)object);event->query_event.query=macdrv_retain_query(query);
        [object release];macdrv_release_query(query);pear_s5_census_read(&state,3,target,WINDOW_GOT_FOCUS,&out);
        check(out.complete && out.events_target==1 && out.queries_target==1 && deallocated==2);
        macdrv_release_event(event);pear_s5_census_read(&state,3,target,WINDOW_GOT_FOCUS,&out);
        check(out.complete && !out.events_live && !out.queries_live && out.allocations==4 && deallocated==3 && terminal_observations==4);
        object=[[PearCensusObject alloc]init];target=(uintptr_t)object;
        pear_s5_census_register_window(&state,4,target);
        event=macdrv_create_event(WINDOW_GOT_FOCUS,nil);
        event->window_got_focus.tried_windows=[[NSMutableSet alloc]initWithObjects:object,nil];
        [object release];pear_s5_census_read(&state,4,target,WINDOW_GOT_FOCUS,&out);
        check(!out.complete && out.indirect_unobserved==1 && !out.events_target && deallocated==3);
        macdrv_release_event(event);pear_s5_census_read(&state,4,target,WINDOW_GOT_FOCUS,&out);
        check(out.complete && !out.events_live && deallocated==4 && terminal_observations==5);
        printf("{\"checks\":%u,\"failed\":%u,\"objects_deallocated\":%u,\"terminal_observations\":%u,\"wine_executed\":false,\"cocoa_windows_created\":false,\"restricted_mode_executed\":false}\n",checks,failed,deallocated,terminal_observations);
    }
    return failed?1:0;
}
