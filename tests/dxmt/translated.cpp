// SPDX-License-Identifier: MIT
// Original Pear bounded device probe. API setup reviewed against DXMT's
// tests/dx11/dx11_triangle.cpp at 7c8dee1c2d73415301ceb7d1fa810861cef4cd67.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <d3d11.h>
#include <dxgi.h>
#include <cstdio>

static bool module(const wchar_t *name) {
    HMODULE handle = GetModuleHandleW(name);
    wchar_t path[32768];
    if (!handle || !GetModuleFileNameW(handle, path, 32768)) return false;
    std::printf("PEAR_GRAPHICS_MODULE name=%ls base=%p path=%ls\n", name, handle, path);
    return true;
}
int main() {
    setvbuf(stdout, nullptr, _IONBF, 0);
    std::puts("PEAR_GRAPHICS_BEGIN suite=device version=1");
    HMODULE dll = LoadLibraryW(L"d3d11.dll");
    if (!dll) { std::printf("PEAR_GRAPHICS_ERROR load=%lu\n", GetLastError()); return 101; }
    auto create = reinterpret_cast<decltype(&D3D11CreateDevice)>(GetProcAddress(dll, "D3D11CreateDevice"));
    if (!create) return 102;
    ID3D11Device *device = nullptr; ID3D11DeviceContext *context = nullptr;
    D3D_FEATURE_LEVEL requested = D3D_FEATURE_LEVEL_11_0, obtained = D3D_FEATURE_LEVEL_9_1;
    HRESULT hr = create(nullptr, D3D_DRIVER_TYPE_HARDWARE, nullptr, 0, &requested, 1,
                        D3D11_SDK_VERSION, &device, &obtained, &context);
    std::printf("PEAR_GRAPHICS_DEVICE hr=%08lx level=%04x device=%p context=%p\n",
                static_cast<unsigned long>(hr), obtained, device, context);
    if (FAILED(hr) || !device || !context || obtained != requested) return 103;
    IDXGIDevice *dxgi = nullptr; IDXGIAdapter *adapter = nullptr;
    hr = device->QueryInterface(__uuidof(IDXGIDevice), reinterpret_cast<void **>(&dxgi));
    if (FAILED(hr) || !dxgi || FAILED(dxgi->GetAdapter(&adapter)) || !adapter) return 104;
    DXGI_ADAPTER_DESC description = {};
    if (FAILED(adapter->GetDesc(&description))) return 105;
    std::printf("PEAR_GRAPHICS_ADAPTER vendor=%08x device=%08x description=%ls\n",
                description.VendorId, description.DeviceId, description.Description);
    if (!module(L"d3d11.dll") || !module(L"dxgi.dll") || !module(L"winemetal.dll")) return 106;
    adapter->Release(); dxgi->Release(); context->ClearState(); context->Flush();
    context->Release(); device->Release(); FreeLibrary(dll);
    // COM releases alone do not establish physical Metal teardown.
    std::puts("PEAR_GRAPHICS_END suite=device cases=1 passed=1");
    return 42;
}
