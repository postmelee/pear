/* Redistributable owned state companion. It validates actual argv, scoped FDs,
 * typed setting bytes and preserved save contents; it never launches a game. */
#include "native_bridge.h"
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/sysctl.h>
#include <time.h>
#include <unistd.h>
#ifndef PEAR_STATE_VARIANT
#define PEAR_STATE_VARIANT 1
#endif
static int selected_fd(const char *key) {
    const char *raw=getenv(key);if(!raw)return -1;
    char *end=NULL;long fd=strtol(raw,&end,10);
    return end && !*end && fd>=3 && fd<=1024 ? (int)fd : -1;
}
static ssize_t read_bytes(int parent,const char *path,char *data,size_t size) {
    int fd=openat(parent,path,O_RDONLY|O_NOFOLLOW|O_CLOEXEC);if(fd<0)return -1;
    ssize_t n=read(fd,data,size-1);close(fd);if(n>=0)data[n]=0;return n;
}
int pear_state_fixture(int argc,char **argv) {
    if(argc!=6 || (strcmp(argv[3],"true")&&strcmp(argv[3],"false")))return 70;
    int translated=-1;size_t size=sizeof(translated);
    int query=sysctlbyname("sysctl.proc_translated",&translated,&size,NULL,0);
    if(!((query==0&&translated==0)||(query<0&&errno==ENOENT)))return 71;
    int prefix=selected_fd("PEAR_FIXTURE_PREFIX_FD"),saves=selected_fd("PEAR_FIXTURE_SAVES_FD");
    const char *wineprefix=getenv("WINEPREFIX"),*marker=getenv("PEAR_FIXTURE_VALUE");
    struct stat held,path;
    if(prefix<0||saves<0||!wineprefix||!marker||strcmp(marker,argv[2])||getenv("PEAR_SECRET_SENTINEL")||fstat(prefix,&held)||stat(wineprefix,&path)||held.st_dev!=path.st_dev||held.st_ino!=path.st_ino)return 72;
    char settings[4096],needle[64];
    if(read_bytes(prefix,"config/options.json",settings,sizeof(settings))<0)return 73;
    snprintf(needle,sizeof(needle),"\"fixture_flag\":%s",argv[3]);if(!strstr(settings,needle))return 74;
    char previous[128];ssize_t n=read_bytes(saves,argv[4],previous,sizeof(previous));
    int existed=n>=0;
    if(existed && strcmp(previous,argv[2]))return 75;
    if(!existed) {
        if(errno!=ENOENT)return 76;
        int save=openat(saves,argv[4],O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
        if(save<0)return 77;
        size_t length=strlen(argv[2]);int ok=write(save,argv[2],length)==(ssize_t)length&&fsync(save)==0;close(save);if(!ok)return 78;
    }
    uint64_t sec=0,usec=0;if(pear_process_identity(getpid(),&sec,&usec))return 79;
    int result=openat(prefix,"last-run.json",O_WRONLY|O_CREAT|O_TRUNC|O_NOFOLLOW|O_CLOEXEC,0600);if(result<0)return 80;
    char record[512];int count=snprintf(record,sizeof(record),"{\"runtime_variant\":%d,\"marker\":\"%s\",\"setting\":%s,\"previous_save\":%s,\"pid\":%d,\"pgid\":%d,\"started_sec\":%llu,\"started_usec\":%llu,\"native\":true}",PEAR_STATE_VARIANT,argv[2],argv[3],existed?"true":"false",getpid(),getpgrp(),(unsigned long long)sec,(unsigned long long)usec);
    if(count<=0||(size_t)count>=sizeof(record)||write(result,record,(size_t)count)!=count||fsync(result)){close(result);return 81;}close(result);
    result=openat(prefix,"identity.json",O_WRONLY|O_CREAT|O_TRUNC|O_NOFOLLOW|O_CLOEXEC,0600);if(result<0)return 83;
    count=snprintf(record,sizeof(record),"{\"pid\":%d,\"pgid\":%d,\"started_sec\":%llu,\"started_usec\":%llu,\"native\":true}",getpid(),getpgrp(),(unsigned long long)sec,(unsigned long long)usec);
    if(count<=0||(size_t)count>=sizeof(record)||write(result,record,(size_t)count)!=count||fsync(result)){close(result);return 84;}close(result);
    char *end=NULL;long delay=strtol(argv[5],&end,10);if(!end||*end||delay<0||delay>1000)return 82;
    struct timespec wait={0,delay*1000000};while(nanosleep(&wait,&wait)<0&&errno==EINTR){}
    return 0;
}
