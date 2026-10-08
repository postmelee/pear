// SPDX-License-Identifier: MIT
// Per-frame visible evidence variant of the original bounded presentation fixture.
// Alternate colors and a bounded hold distinguish each frame from its predecessor.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <d3d11.h>
#include <dxgi.h>
#include <cstdio>
#include <cstdlib>

static unsigned cycle, sizes, destroys;
static DWORD owner;
static void require(bool ok) { if (!ok) { std::printf("PEAR_PRESENT_ERROR win32=%lu\n",GetLastError()); std::exit(101); } }
static void hr(HRESULT value,const char *op) {
    std::printf("PEAR_PRESENT_HR cycle=%u operation=%s hr=%08lx\n",cycle,op,(unsigned long)value);
    require(value==S_OK);
}
static LRESULT CALLBACK wndproc(HWND window,UINT msg,WPARAM wp,LPARAM lp) {
    require(GetCurrentThreadId()==owner);
    if(msg==WM_SIZE) { ++sizes; std::printf("PEAR_PRESENT_SIZE cycle=%u width=%u height=%u count=%u\n",cycle,LOWORD(lp),HIWORD(lp),sizes); }
    if(msg==WM_DESTROY) ++destroys;
    return DefWindowProcW(window,msg,wp,lp);
}
static void pump(DWORD duration) {
    ULONGLONG end=GetTickCount64()+duration; unsigned count=0;
    do { MSG m; while(PeekMessageW(&m,nullptr,0,0,PM_REMOVE)) { require(++count<20000); TranslateMessage(&m); DispatchMessageW(&m); } Sleep(5); } while(GetTickCount64()<end);
}
static void module(const wchar_t *name) {
    HMODULE h=GetModuleHandleW(name); wchar_t path[32768];
    require(h && GetModuleFileNameW(h,path,32768));
    std::printf("PEAR_GRAPHICS_MODULE name=%ls base=%p path=%ls\n",name,h,path);
}
static void wait_gpu(ID3D11DeviceContext *ctx,ID3D11Query *query) {
    ctx->End(query);ctx->Flush(); ULONGLONG end=GetTickCount64()+5000; BOOL done=FALSE; HRESULT value;
    do { value=ctx->GetData(query,&done,sizeof(done),0);require(value==S_OK || value==S_FALSE); if(value==S_OK && done) break; pump(5); } while(GetTickCount64()<end);
    require(value==S_OK && done);
}
int main() {
    setvbuf(stdout,nullptr,_IONBF,0);owner=GetCurrentThreadId();
    std::puts("PEAR_PRESENT_BEGIN version=1 cycles=3 frames=18");
    HMODULE lib=LoadLibraryW(L"d3d11.dll");require(lib!=nullptr);
    auto create=(decltype(&D3D11CreateDeviceAndSwapChain))GetProcAddress(lib,"D3D11CreateDeviceAndSwapChain");require(create!=nullptr);
    WNDCLASSW cls={};cls.lpfnWndProc=wndproc;cls.hInstance=GetModuleHandleW(nullptr);cls.lpszClassName=L"PearPresentation";require(RegisterClassW(&cls)!=0);
    // A borderless owned window keeps the declared client sizes exact.
    for(cycle=1;cycle<=3;cycle++) {
        sizes=0;unsigned before_destroy=destroys;
        HWND window=CreateWindowExW(WS_EX_TOPMOST,cls.lpszClassName,L"Pear Presentation",WS_POPUP|WS_VISIBLE,100,100,64,64,nullptr,nullptr,cls.hInstance,nullptr);require(window!=nullptr);pump(100);
        // Immutable setup and explicit alignment isolate graphics qualification
        // from the separately retained delivered-unaligned-store CPU limitation.
        static const DXGI_SWAP_CHAIN_DESC initial={
            {64,64,{0,1},DXGI_FORMAT_R8G8B8A8_UNORM,DXGI_MODE_SCANLINE_ORDER_UNSPECIFIED,DXGI_MODE_SCALING_UNSPECIFIED},
            {1,0},DXGI_USAGE_RENDER_TARGET_OUTPUT,2,nullptr,TRUE,DXGI_SWAP_EFFECT_DISCARD,0};
        alignas(16) DXGI_SWAP_CHAIN_DESC desc=initial;desc.OutputWindow=window;
        ID3D11Device *device=nullptr; ID3D11DeviceContext *ctx=nullptr;IDXGISwapChain *swap=nullptr;
        D3D_FEATURE_LEVEL level=D3D_FEATURE_LEVEL_11_0,obtained;
        hr(create(nullptr,D3D_DRIVER_TYPE_HARDWARE,nullptr,0,&level,1,D3D11_SDK_VERSION,&desc,&swap,&device,&obtained,&ctx),"device_swapchain");require(obtained==level && swap && device && ctx);
        if(cycle==1) { module(L"d3d11.dll");module(L"dxgi.dll");module(L"winemetal.dll"); }
        ID3D11Query *query=nullptr;D3D11_QUERY_DESC q={D3D11_QUERY_EVENT,0};hr(device->CreateQuery(&q,&query),"query");
        for(unsigned phase=0;phase<3;phase++) {
            unsigned width=phase==1?96:64,height=phase==1?80:64;
            if(phase) { unsigned previous=sizes;require(SetWindowPos(window,HWND_TOPMOST,100,100,width,height,SWP_NOACTIVATE));pump(100);require(sizes>previous);hr(swap->ResizeBuffers(2,width,height,DXGI_FORMAT_UNKNOWN,0),"resize"); }
            RECT rect;require(GetClientRect(window,&rect));require(rect.right==long(width) && rect.bottom==long(height));
            ID3D11Texture2D *back=nullptr; ID3D11RenderTargetView *rtv=nullptr;
            hr(swap->GetBuffer(0,__uuidof(ID3D11Texture2D),(void**)&back),"backbuffer");hr(device->CreateRenderTargetView(back,nullptr,&rtv),"rtv");
            static const FLOAT colors[3][4]={{1,0,0,1},{0,1,0,1},{0,0,1,1}};
            for(unsigned frame=0;frame<2;frame++) {
                FLOAT color[4]={colors[phase][0],colors[phase][1],colors[phase][2],1};
                if(frame) for(unsigned i=0;i<3;i++) color[i]=1-color[i];
                ctx->ClearRenderTargetView(rtv,color);hr(swap->Present(1,0),"present");wait_gpu(ctx,query);
                std::printf("PEAR_PRESENT_FRAME cycle=%u phase=%u frame=%u width=%u height=%u gpu=1\n",cycle,phase,frame,width,height);pump(1500);
            }
            std::printf("PEAR_PRESENT_READY cycle=%u phase=%u width=%u height=%u\n",cycle,phase,width,height);pump(3000);
            ctx->ClearState();wait_gpu(ctx,query);rtv->Release();back->Release();
        }
        query->Release();ctx->ClearState();ctx->Flush();swap->Release();ctx->Release();device->Release();
        require(DestroyWindow(window));pump(1000);require(destroys==before_destroy+1 && sizes>=3);
        std::printf("PEAR_PRESENT_CYCLE cycle=%u resize_callbacks=%u destroy_callbacks=1\n",cycle,sizes);
    }
    require(UnregisterClassW(cls.lpszClassName,cls.hInstance));FreeLibrary(lib);
    std::puts("PEAR_PRESENT_END cycles=3 frames=18 passed=1");return 42;
}
