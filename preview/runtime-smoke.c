/* SPDX-License-Identifier: GPL-3.0-or-later */
#include <windows.h>
#include <bcrypt.h>
#include <winhttp.h>
#include <stdio.h>
#include <string.h>
static int https(const wchar_t *host, int expect_failure) {
 HINTERNET s=WinHttpOpen(L"Pear-runtime-check/1",WINHTTP_ACCESS_TYPE_NO_PROXY,0,0,0);
 if(!s)return 1;
 WinHttpSetTimeouts(s,10000,10000,10000,15000);
 HINTERNET c=WinHttpConnect(s,host,443,0),q=c?WinHttpOpenRequest(c,L"HEAD",L"/",0,WINHTTP_NO_REFERER,WINHTTP_DEFAULT_ACCEPT_TYPES,WINHTTP_FLAG_SECURE):0;
 BOOL ok=q && WinHttpSendRequest(q,0,0,0,0,0,0) && WinHttpReceiveResponse(q,0); DWORD error=GetLastError(),status=0,size=sizeof(status);
 if(ok)WinHttpQueryHeaders(q,WINHTTP_QUERY_STATUS_CODE|WINHTTP_QUERY_FLAG_NUMBER,0,&status,&size,0);
 printf("HTTPS %ls success=%d status=%lu error=%lu\n",host,ok,status,error);
 if(q)WinHttpCloseHandle(q);if(c)WinHttpCloseHandle(c);WinHttpCloseHandle(s);
 return expect_failure ? (ok || (error!=ERROR_WINHTTP_SECURE_FAILURE && error!=ERROR_WINHTTP_SECURE_CHANNEL_ERROR && error!=ERROR_WINHTTP_SECURE_CERT_CN_INVALID)) : (!ok || status!=200);
}
int main(void) {
 BCRYPT_ALG_HANDLE a=0;BCRYPT_KEY_HANDLE k=0;unsigned char key[16]={0},input[16]={0},out[16];ULONG n=0;
 const unsigned char expected[16]={0x66,0xe9,0x4b,0xd4,0xef,0x8a,0x2c,0x3b,0x88,0x4c,0xfa,0x59,0xca,0x34,0x2b,0x2e};
 if(BCryptOpenAlgorithmProvider(&a,BCRYPT_AES_ALGORITHM,0,0))return 2;
 if(BCryptSetProperty(a,BCRYPT_CHAINING_MODE,(PUCHAR)BCRYPT_CHAIN_MODE_ECB,sizeof(BCRYPT_CHAIN_MODE_ECB),0))return 3;
 if(BCryptGenerateSymmetricKey(a,&k,0,0,key,16,0))return 4;
 if(BCryptEncrypt(k,input,16,0,0,0,out,16,&n,0)||n!=16||memcmp(out,expected,16))return 5;
 BCryptDestroyKey(k);BCryptCloseAlgorithmProvider(a,0);puts("AES known-answer passed");
 HDC dc=CreateCompatibleDC(0);HFONT font=CreateFontW(24,0,0,0,400,0,0,0,DEFAULT_CHARSET,0,0,0,0,L"Arial");SelectObject(dc,font);TEXTMETRICW tm;
 if(!GetTextMetricsW(dc,&tm)||tm.tmHeight<=0)return 6;printf("Font metrics height=%ld\n",tm.tmHeight);DeleteDC(dc);DeleteObject(font);
 if(https(L"store.steampowered.com",0))return 7;
 if(https(L"badssl.com",0))return 9;
 if(https(L"wrong.host.badssl.com",1))return 8;
 puts("PEAR_RUNTIME_OBSERVE_READY");fflush(stdout);Sleep(5000);
 return 0;
}
