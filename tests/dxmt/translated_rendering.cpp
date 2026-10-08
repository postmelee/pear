// SPDX-License-Identifier: MIT
// Original Pear fixture. D3DCompile/device setup reviewed against DXMT's
// tests/dx11/dx11_triangle.cpp at 7c8dee1c2d73415301ceb7d1fa810861cef4cd67.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <d3d11.h>
#include <d3dcompiler.h>
#include <dxgi.h>
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <initializer_list>
#include <array>
#include "translated_shader.h"

template<class T> struct Com {
    T *p = nullptr;
    ~Com() { if (p) p->Release(); }
    T **put() { return &p; }
    T *operator->() const { return p; }
};
static void check(HRESULT hr, const char *operation) {
    std::printf("PEAR_RENDER_HR operation=%s hr=%08lx\n", operation, (unsigned long)hr);
    if (FAILED(hr)) std::exit(101);
}
static void module(const wchar_t *name) {
    HMODULE h = GetModuleHandleW(name); wchar_t path[32768];
    if (!h || !GetModuleFileNameW(h,path,32768)) std::exit(102);
    std::printf("PEAR_GRAPHICS_MODULE name=%ls base=%p path=%ls\n",name,h,path);
}
static void bytes(const unsigned char *p, size_t n) {
    for (size_t i=0;i<n;i++) std::printf("%02x",p[i]);
}
static void read_buffer(ID3D11Device *d, ID3D11DeviceContext *c, ID3D11Buffer *src, const char *name) {
    D3D11_BUFFER_DESC desc={}; src->GetDesc(&desc);
    UINT size=desc.ByteWidth; desc.Usage=D3D11_USAGE_STAGING; desc.BindFlags=0;
    desc.CPUAccessFlags=D3D11_CPU_ACCESS_READ; desc.MiscFlags=0; desc.StructureByteStride=0;
    Com<ID3D11Buffer> stage; check(d->CreateBuffer(&desc,nullptr,stage.put()),"buffer_staging");
    c->CopyResource(stage.p,src); D3D11_MAPPED_SUBRESOURCE mapped={};
    check(c->Map(stage.p,0,D3D11_MAP_READ,0,&mapped),"buffer_map");
    std::printf("PEAR_RENDER_DATA name=%s width=%u height=1 pitch=%u format=uint32 data=",name,size/4,mapped.RowPitch);
    bytes((unsigned char*)mapped.pData,size); std::puts(""); c->Unmap(stage.p,0);
}
static void read_texture(ID3D11Device *d, ID3D11DeviceContext *c, ID3D11Texture2D *src, const char *name) {
    D3D11_TEXTURE2D_DESC desc={}; src->GetDesc(&desc);
    desc.Usage=D3D11_USAGE_STAGING; desc.BindFlags=0; desc.CPUAccessFlags=D3D11_CPU_ACCESS_READ; desc.MiscFlags=0;
    Com<ID3D11Texture2D> stage; check(d->CreateTexture2D(&desc,nullptr,stage.put()),"texture_staging");
    c->CopyResource(stage.p,src); D3D11_MAPPED_SUBRESOURCE mapped={};
    check(c->Map(stage.p,0,D3D11_MAP_READ,0,&mapped),"texture_map");
    if (mapped.RowPitch<desc.Width*4) std::exit(103);
    std::printf("PEAR_RENDER_DATA name=%s width=%u height=%u pitch=%u format=rgba8 data=",name,desc.Width,desc.Height,mapped.RowPitch);
    for (UINT y=0;y<desc.Height;y++) bytes((unsigned char*)mapped.pData+y*mapped.RowPitch,desc.Width*4);
    std::puts(""); c->Unmap(stage.p,0);
}
int main() {
    setvbuf(stdout,nullptr,_IONBF,0);
    std::puts("PEAR_RENDER_BEGIN version=1 cases=5");
    HMODULE dll=LoadLibraryW(L"d3d11.dll"), compiler=LoadLibraryW(L"d3dcompiler_47.dll");
    if (!dll || !compiler) return 104;
    auto create=(decltype(&D3D11CreateDevice))GetProcAddress(dll,"D3D11CreateDevice");
    auto compile=(decltype(&D3DCompile))GetProcAddress(compiler,"D3DCompile");
    if (!create || !compile) return 105;
    Com<ID3D11Device> d; Com<ID3D11DeviceContext> c;
    D3D_FEATURE_LEVEL requested=D3D_FEATURE_LEVEL_11_0, obtained=D3D_FEATURE_LEVEL_9_1;
    check(create(nullptr,D3D_DRIVER_TYPE_HARDWARE,nullptr,0,&requested,1,D3D11_SDK_VERSION,d.put(),&obtained,c.put()),"device");
    if (obtained!=requested) return 106;
    std::printf("PEAR_RENDER_DEVICE level=%04x\n",obtained);
    for (auto n : {L"d3d11.dll",L"dxgi.dll",L"winemetal.dll",L"d3dcompiler_47.dll"}) module(n);
    Com<ID3DBlob> vs,ps,sample,cs;
    auto shader=[&](const char *entry,const char *profile,Com<ID3DBlob>& blob) {
        Com<ID3DBlob> errors;
        HRESULT hr=compile(shader_source,sizeof(shader_source)-1,"translated.hlsl",nullptr,nullptr,entry,profile,
                           D3DCOMPILE_ENABLE_STRICTNESS,0,blob.put(),errors.put());
        if (FAILED(hr) && errors.p) std::fwrite(errors->GetBufferPointer(),1,errors->GetBufferSize(),stderr);
        check(hr,entry);
        std::printf("PEAR_RENDER_SHADER entry=%s profile=%s data=",entry,profile);
        bytes((unsigned char*)blob->GetBufferPointer(),blob->GetBufferSize());std::puts("");
    };
    shader("vertex","vs_5_0",vs);shader("solid","ps_5_0",ps);
    shader("sample_image","ps_5_0",sample);shader("transform","cs_5_0",cs);
    Com<ID3D11VertexShader> vertex;Com<ID3D11PixelShader> solid, sampled;Com<ID3D11ComputeShader> compute;
    check(d->CreateVertexShader(vs->GetBufferPointer(),vs->GetBufferSize(),nullptr,vertex.put()),"vertex_shader");
    check(d->CreatePixelShader(ps->GetBufferPointer(),ps->GetBufferSize(),nullptr,solid.put()),"solid_shader");
    check(d->CreatePixelShader(sample->GetBufferPointer(),sample->GetBufferSize(),nullptr,sampled.put()),"sample_shader");
    check(d->CreateComputeShader(cs->GetBufferPointer(),cs->GetBufferSize(),nullptr,compute.put()),"compute_shader");
    uint32_t input[64]; for (UINT i=0;i<64;i++) input[i]=i*0x010203u+5;
    D3D11_BUFFER_DESC bd={};bd.ByteWidth=sizeof(input);bd.Usage=D3D11_USAGE_DEFAULT;bd.BindFlags=D3D11_BIND_VERTEX_BUFFER;
    Com<ID3D11Buffer> buffer;check(d->CreateBuffer(&bd,nullptr,buffer.put()),"buffer");
    c->UpdateSubresource(buffer.p,0,nullptr,input,0,0);read_buffer(d.p,c.p,buffer.p,"buffer");
    // Immutable upload data isolates the GPU case from guest pattern generation.
    // rendering1 exposed a separate unhandled cross-boundary x64 word store;
    // retaining that failure is required, and this fixture does not qualify it.
    static constexpr auto texels=[] {
        std::array<unsigned char,256> data={};
        for(unsigned y=0;y<8;y++)for(unsigned x=0;x<8;x++) {
            unsigned i=(y*8+x)*4;data[i]=x*17+3;data[i+1]=y*19+5;data[i+2]=(x+y)*11+7;data[i+3]=255;
        }
        return data;
    }();
    D3D11_TEXTURE2D_DESC td={};td.Width=td.Height=8;td.MipLevels=td.ArraySize=1;
    td.Format=DXGI_FORMAT_R8G8B8A8_UNORM;td.SampleDesc.Count=1;td.Usage=D3D11_USAGE_DEFAULT;td.BindFlags=D3D11_BIND_SHADER_RESOURCE;
    D3D11_SUBRESOURCE_DATA initial={texels.data(),32,0};Com<ID3D11Texture2D> texture;
    check(d->CreateTexture2D(&td,&initial,texture.put()),"texture_upload");read_texture(d.p,c.p,texture.p,"texture_copy");
    Com<ID3D11ShaderResourceView> srv;check(d->CreateShaderResourceView(texture.p,nullptr,srv.put()),"texture_srv");
    D3D11_SAMPLER_DESC sd={};sd.Filter=D3D11_FILTER_MIN_MAG_MIP_POINT;
    sd.AddressU=sd.AddressV=sd.AddressW=D3D11_TEXTURE_ADDRESS_CLAMP;sd.MaxLOD=D3D11_FLOAT32_MAX;
    Com<ID3D11SamplerState> sampler;check(d->CreateSamplerState(&sd,sampler.put()),"point_sampler");
    D3D11_RASTERIZER_DESC rd={};rd.FillMode=D3D11_FILL_SOLID;rd.CullMode=D3D11_CULL_NONE;rd.DepthClipEnable=TRUE;
    Com<ID3D11RasterizerState> raster;check(d->CreateRasterizerState(&rd,raster.put()),"raster_state");c->RSSetState(raster.p);
    struct Parameters { float color[4], geometry[4]; } parameters={};
    bd.ByteWidth=sizeof(parameters);bd.BindFlags=D3D11_BIND_CONSTANT_BUFFER;
    Com<ID3D11Buffer> constants;check(d->CreateBuffer(&bd,nullptr,constants.put()),"constants");
    c->VSSetConstantBuffers(0,1,&constants.p);c->PSSetConstantBuffers(0,1,&constants.p);
    c->VSSetShader(vertex.p,nullptr,0);c->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
    td.BindFlags=D3D11_BIND_RENDER_TARGET;Com<ID3D11Texture2D> sample_target;
    check(d->CreateTexture2D(&td,nullptr,sample_target.put()),"sample_target");
    Com<ID3D11RenderTargetView> sample_rtv;check(d->CreateRenderTargetView(sample_target.p,nullptr,sample_rtv.put()),"sample_rtv");
    D3D11_VIEWPORT viewport={0,0,8,8,0,1};c->RSSetViewports(1,&viewport);
    c->UpdateSubresource(constants.p,0,nullptr,&parameters,0,0);
    c->OMSetRenderTargets(1,&sample_rtv.p,nullptr);c->PSSetShader(sampled.p,nullptr,0);
    c->PSSetShaderResources(0,1,&srv.p);c->PSSetSamplers(0,1,&sampler.p);c->Draw(3,0);
    read_texture(d.p,c.p,sample_target.p,"texture_sample");
    td.Width=td.Height=64;Com<ID3D11Texture2D> target;
    check(d->CreateTexture2D(&td,nullptr,target.put()),"raster_target");
    Com<ID3D11RenderTargetView> rtv;check(d->CreateRenderTargetView(target.p,nullptr,rtv.put()),"raster_rtv");
    c->OMSetRenderTargets(1,&rtv.p,nullptr);c->PSSetShader(solid.p,nullptr,0);
    const float clear[4]={17/255.f,34/255.f,51/255.f,1};c->ClearRenderTargetView(rtv.p,clear);
    viewport={16,16,32,32,0,1};c->RSSetViewports(1,&viewport);
    parameters={{0,1,0,1},{0,0,0,0}};c->UpdateSubresource(constants.p,0,nullptr,&parameters,0,0);c->Draw(3,0);
    read_texture(d.p,c.p,target.p,"raster");
    td.Format=DXGI_FORMAT_D32_FLOAT;td.BindFlags=D3D11_BIND_DEPTH_STENCIL;
    Com<ID3D11Texture2D> depth;Com<ID3D11DepthStencilView> dsv;
    check(d->CreateTexture2D(&td,nullptr,depth.put()),"depth_target");
    check(d->CreateDepthStencilView(depth.p,nullptr,dsv.put()),"depth_view");
    D3D11_DEPTH_STENCIL_DESC dd={};dd.DepthEnable=TRUE;dd.DepthWriteMask=D3D11_DEPTH_WRITE_MASK_ALL;dd.DepthFunc=D3D11_COMPARISON_LESS;
    Com<ID3D11DepthStencilState> depth_state;check(d->CreateDepthStencilState(&dd,depth_state.put()),"depth_state");
    c->OMSetDepthStencilState(depth_state.p,0);c->OMSetRenderTargets(1,&rtv.p,dsv.p);
    viewport={0,0,64,64,0,1};c->RSSetViewports(1,&viewport);c->ClearDepthStencilView(dsv.p,D3D11_CLEAR_DEPTH,1,0);
    auto draw=[&](float r,float g,float b,float a,float z) {
        parameters={{r,g,b,a},{0,0,z,0}};c->UpdateSubresource(constants.p,0,nullptr,&parameters,0,0);c->Draw(3,0);
    };
    draw(1,0,0,1,.25f);draw(0,1,0,1,.75f);read_texture(d.p,c.p,target.p,"depth");
    D3D11_BLEND_DESC blend_desc={};auto &blend=blend_desc.RenderTarget[0];blend.BlendEnable=TRUE;
    blend.SrcBlend=D3D11_BLEND_SRC_ALPHA;blend.DestBlend=D3D11_BLEND_INV_SRC_ALPHA;blend.BlendOp=D3D11_BLEND_OP_ADD;
    blend.SrcBlendAlpha=D3D11_BLEND_ONE;blend.DestBlendAlpha=D3D11_BLEND_ZERO;blend.BlendOpAlpha=D3D11_BLEND_OP_ADD;
    blend.RenderTargetWriteMask=D3D11_COLOR_WRITE_ENABLE_ALL;
    Com<ID3D11BlendState> blend_state;check(d->CreateBlendState(&blend_desc,blend_state.put()),"blend_state");
    c->OMSetBlendState(blend_state.p,nullptr,0xffffffffu);draw(0,0,1,.5f,.1f);read_texture(d.p,c.p,target.p,"blend");
    for(UINT i=0;i<64;i++)input[i]=i^0xa5u;
    bd.ByteWidth=sizeof(input);bd.BindFlags=D3D11_BIND_SHADER_RESOURCE;bd.MiscFlags=D3D11_RESOURCE_MISC_BUFFER_STRUCTURED;bd.StructureByteStride=4;
    initial={input,0,0};Com<ID3D11Buffer> compute_input,compute_output;
    check(d->CreateBuffer(&bd,&initial,compute_input.put()),"compute_input");
    bd.BindFlags=D3D11_BIND_UNORDERED_ACCESS;check(d->CreateBuffer(&bd,nullptr,compute_output.put()),"compute_output");
    Com<ID3D11ShaderResourceView> compute_srv;Com<ID3D11UnorderedAccessView> uav;
    check(d->CreateShaderResourceView(compute_input.p,nullptr,compute_srv.put()),"compute_srv");
    check(d->CreateUnorderedAccessView(compute_output.p,nullptr,uav.put()),"compute_uav");
    c->CSSetShader(compute.p,nullptr,0);c->CSSetShaderResources(1,1,&compute_srv.p);c->CSSetUnorderedAccessViews(0,1,&uav.p,nullptr);
    c->Dispatch(4,1,1);read_buffer(d.p,c.p,compute_output.p,"compute");
    c->ClearState();c->Flush();
    // Map completed all submitted readbacks. Physical native destruction is Stage 3.
    std::puts("PEAR_RENDER_END cases=5 readbacks=7 completed=1");return 42;
}
