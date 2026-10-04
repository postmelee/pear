/* Original Pear source integration. SPDX-License-Identifier: LGPL-2.1-or-later. */
#include "pear_macdrv_metal_v1.h"
#include <pthread.h>
#include <string.h>
static const struct pear_macdrv_metal_v1 *pear_driver;
static pthread_once_t pear_driver_once=PTHREAD_ONCE_INIT;
static void pear_resolve_driver(void)
{
    pear_metal_get_interface get=(pear_metal_get_interface)dlsym(RTLD_DEFAULT,"pear_macdrv_metal_v1_get_interface");
    const struct pear_macdrv_metal_v1 *table=NULL;
    if(!get || get(PEAR_METAL_VERSION,sizeof(*table),PEAR_METAL_FEATURES,&table) || !table) return;
    if(table->version!=PEAR_METAL_VERSION || table->bytes!=sizeof(*table) ||
       (table->features & PEAR_METAL_FEATURES)!=PEAR_METAL_FEATURES ||
       !table->acquire || !table->query || !table->release || !table->with_layer) return;
    pear_driver=table;
}
@interface PearDXMTMetalLease : NSObject { @public uint64_t token; }
@end
@implementation PearDXMTMetalLease
- (void)dealloc { if(token && pear_driver) pear_driver->release(token); token=0; [super dealloc]; }
@end
struct pear_layer_call { void *params; NTSTATUS result; };
static NTSTATUS pear_call_layer(obj_handle_t value,pear_metal_layer_operation operation,struct pear_layer_call *call)
{
    PearDXMTMetalLease *lease=(PearDXMTMetalLease *)(uintptr_t)value;
    pthread_once(&pear_driver_once,pear_resolve_driver);
    if(!pear_driver || !lease || ![lease isKindOfClass:[PearDXMTMetalLease class]] || !lease->token) return STATUS_UNSUCCESSFUL;
    call->result=STATUS_UNSUCCESSFUL;
    if(pear_driver->with_layer(lease->token,operation,call)) return STATUS_UNSUCCESSFUL;
    return call->result;
}
static NTSTATUS _CreateMetalViewFromHWND(void *obj)
{
    struct unixcall_create_metal_view_from_hwnd *params=obj;
    PearDXMTMetalLease *lease;
    uint64_t token=0;
    params->ret_view=params->ret_layer=0;
    pthread_once(&pear_driver_once,pear_resolve_driver);
    if(!pear_driver || pear_driver->acquire(params->hwnd,params->device,&token) || !token) return STATUS_UNSUCCESSFUL;
    lease=[[PearDXMTMetalLease alloc] init];
    if(!lease) { pear_driver->release(token); return STATUS_UNSUCCESSFUL; }
    lease->token=token;
    params->ret_view=params->ret_layer=(obj_handle_t)(uintptr_t)lease;
    return STATUS_SUCCESS;
}
static NTSTATUS _ReleaseMetalView(void *obj)
{
    struct unixcall_generic_obj_noret *params=obj;
    PearDXMTMetalLease *lease=(PearDXMTMetalLease *)(uintptr_t)params->handle;
    if(!lease || ![lease isKindOfClass:[PearDXMTMetalLease class]]) return STATUS_UNSUCCESSFUL;
    [lease release]; return STATUS_SUCCESS;
}
