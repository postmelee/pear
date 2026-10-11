/* SPDX-License-Identifier: GPL-3.0-or-later */
#include <dlfcn.h>
#include <stdio.h>
#include <stdint.h>
int main(int argc,char **argv) {
 if(argc!=4)return 1;void *g=dlopen(argv[1],RTLD_NOW),*f=dlopen(argv[2],RTLD_NOW),*v=dlopen(argv[3],RTLD_NOW);
 if(!g||!f||!v){puts(dlerror());return 2;}
 const char *(*version)(const char*)=dlsym(g,"gnutls_check_version");int (*init)(void)=dlsym(g,"gnutls_global_init");void (*done)(void)=dlsym(g,"gnutls_global_deinit");int (*rnd)(int,void*,size_t)=dlsym(g,"gnutls_rnd");int (*fi)(void**)=dlsym(f,"FT_Init_FreeType");int (*fd)(void*)=dlsym(f,"FT_Done_FreeType");int (*vi)(uint32_t*)=dlsym(v,"vkEnumerateInstanceVersion");
 if(!version||!init||!done||!rnd||!fi||!fd||!vi)return 3;
 char bytes[32];void *ft=0;uint32_t vk=0;if(init()||rnd(1,bytes,sizeof(bytes))||fi(&ft)||vi(&vk))return 4;
 printf("GnuTLS %s; FreeType initialized; Vulkan loader version %u.%u.%u\n",version(0),vk>>22,(vk>>12)&1023,vk&4095);fd(ft);done();return 0;
}
