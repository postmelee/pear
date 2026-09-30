/* Original synthetic ledger tests; no Wine, AppKit or restricted mode. */
#define PEAR_S5_CENSUS_IMPLEMENTATION
#include "stage5_census.h"
#include <stdio.h>
#include <stdlib.h>
static struct pear_s5_census_state state={.lock=PTHREAD_MUTEX_INITIALIZER};
static unsigned checks,failed;
static void check(int value){checks++;if(!value)failed++;}
static void reset(void){pthread_mutex_destroy(&state.lock);memset(&state,0,sizeof(state));pthread_mutex_init(&state.lock,NULL);pear_s5_census_register_window(&state,1,0x7000);}
static void *worker(void *value){uintptr_t offset=(uintptr_t)value;for(unsigned i=0;i<250;i++){uintptr_t id=offset+i+1;pear_s5_census_object(&state,1,1,id,0x7000,7);pear_s5_census_object(&state,1,3,id,0x7000,7);}return NULL;}
int main(void)
{
    struct pear_s5_census_snapshot out;
    reset();pear_s5_census_object(&state,1,1,0x100,0x7000,7);pear_s5_census_read(&state,1,0x7000,17,&out);
    check(out.complete && out.events_live==1 && out.events_target==1 && out.detail_count==1);
    pear_s5_census_object(&state,2,1,0x200,0,0);pear_s5_census_read(&state,1,0x7000,17,&out);
    check(!out.complete && out.queries_live==1 && out.queries_unbound==1 && !out.queries_target);
    pear_s5_census_object(&state,2,2,0x200,0x7000,3);pear_s5_census_read(&state,1,0x7000,17,&out);
    check(out.complete && out.queries_target==1 && !out.queries_unbound);
    pear_s5_census_object(&state,1,2,0x100,0x7000,8);pear_s5_census_read(&state,1,0x7000,17,&out);
    check(out.complete && out.details[0].type==8); /* Upstream mouse coalescing changes type. */
    pear_s5_census_object(&state,1,3,0x100,0x7000,8);pear_s5_census_object(&state,2,3,0x200,0x7000,3);
    pear_s5_census_object(&state,1,1,0x100,0x7000,9);pear_s5_census_read(&state,1,0x7000,17,&out);
    check(out.complete && out.allocations==3 && out.events_target==1 && !out.queries_live && out.details[0].ordinal==3);
    pear_s5_census_draw(&state,0x7000,1,0);pear_s5_census_draw(&state,0x7000,2,1);pear_s5_census_draw(&state,0x7000,3,1);
    pear_s5_census_marker(&state,0);pear_s5_census_marker(&state,1);pear_s5_census_read(&state,1,0x7000,17,&out);
    check(out.draw_scheduled==1 && out.draw_entered==1 && out.draw_completed==1 && out.draw_after_close==1 && out.marker_submitted==1 && out.marker_completed==1);
    pear_s5_census_object(&state,1,1,0x100,0x7000,9);pear_s5_census_read(&state,1,0x7000,17,&out);check(!out.complete && out.errors==1);
    reset();pear_s5_census_object(&state,2,1,0x200,0,0);pear_s5_census_object(&state,2,2,0x200,0x7000,3);pear_s5_census_object(&state,2,2,0x200,0x9999,3);pear_s5_census_read(&state,1,0x7000,17,&out);check(!out.complete && out.errors==1 && out.queries_target==1);
    reset();pear_s5_census_object(&state,1,3,0x999,0x7000,9);pear_s5_census_read(&state,1,0x7000,17,&out);check(!out.complete && out.errors==1);
    reset();for(unsigned i=0;i<PEAR_S5_CENSUS_CAPACITY+1;i++)pear_s5_census_object(&state,1,1,i+1,0x7000,7);
    pear_s5_census_read(&state,1,0x7000,17,&out);check(!out.complete && out.allocations==2048 && out.overflow==1 && out.events_target==2048 && out.detail_count==32 && out.details_truncated==2016);
    reset();pear_s5_census_object(&state,1,1,0x987,0x9999,17);pear_s5_census_read(&state,1,0x7000,17,&out);
    check(!out.complete && out.indirect_unobserved==1 && !out.events_target);
    reset();pthread_t threads[4];for(uintptr_t i=0;i<4;i++)check(!pthread_create(threads+i,NULL,worker,(void *)(i*1000)));
    for(unsigned i=0;i<500;i++){pear_s5_census_read(&state,1,0x7000,17,&out);check(out.complete && out.events_target<=4 && out.events_target==out.events_live);}
    for(unsigned i=0;i<4;i++)check(!pthread_join(threads[i],NULL));
    pear_s5_census_read(&state,1,0x7000,17,&out);check(out.complete && out.allocations==1000 && !out.events_live && !out.queries_live);
    printf("{\"checks\":%u,\"failed\":%u,\"wine_executed\":false,\"restricted_mode_executed\":false}\n",checks,failed);
    pthread_mutex_destroy(&state.lock);return failed?1:0;
}
