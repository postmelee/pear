// SPDX-License-Identifier: MIT
// Ordinary host control: provider and fatal sink are substitutes, not Wine/FEX execution.
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <list>
#include <memory>
#include <memory_resource>
#include <unordered_map>
#include <fmt/format.h>

static void require(bool value) { if (!value) std::exit(90); }
using DWORD = uint32_t;
constexpr DWORD MEM_RELEASE = 0x8000;
static std::unordered_map<void*, size_t> live;
static unsigned calls, error_reads;
static DWORD error_code;
static void* refused;
static size_t refused_size;
static bool baseline;
static int VirtualFree(void* p, size_t size, DWORD flags) {
  require(size == 0 && flags == MEM_RELEASE && live.contains(p));
  ++calls;
  if (error_code && calls == 2) {
    refused = p; refused_size = live.at(p); return 0;
  }
  live.erase(p); std::free(p); return 1;
}
static DWORD GetLastError() { ++error_reads; return error_code; }
namespace LogMan::Throw {
[[noreturn]] void MFmt(const char* pattern, const fmt::format_args& args) {
  require(!baseline && calls == 2 && error_reads == 1 && live.size() == 2);
  require(live.at(refused) == refused_size && *static_cast<unsigned char*>(refused) == 0x51);
  require(fmt::vformat(pattern, args) == fmt::format(
    "Pear VirtualFree failed: Win32 error {}, address {}, requested bytes {}", error_code, refused, refused_size));
  std::printf("{\"failure_intercepted\":true,\"error\":%u,\"provider_calls\":%u,\"retained_buffers\":%zu,\"error_reads\":%u}\n",
              error_code, calls, live.size(), error_reads);
  std::fflush(stdout);
  // Keep noexcept/destructor semantics. Intercept before the actual fatal trap.
  std::_Exit(0);
}
}
namespace FEXCore {
template<class T> T AlignUp(T value, T alignment) { return value + (alignment - value % alignment) % alignment; }
namespace Utils { constexpr size_t FEX_PAGE_SIZE = 4096; }
namespace Allocator {
void* VirtualAlloc(size_t size) {
  void* p = nullptr; require(posix_memalign(&p, Utils::FEX_PAGE_SIZE, size) == 0);
  require(live.emplace(p, size).second); return p;
}
void VirtualName(const char*, void*, size_t) {}
#include "wrapper_under_test.inc"
}
}
namespace fextl { template<class T> using list = std::list<T>; }
#define LOGMAN_THROW_A_FMT(condition, ...) require(condition)
#include "resource_under_test.inc"
int main(int argc, char** argv) {
  require(argc == 3);
  baseline = std::strcmp(argv[1], "baseline") == 0;
  require(baseline || std::strcmp(argv[1], "checked") == 0);
  error_code = static_cast<DWORD>(std::strtoul(argv[2], nullptr, 10));
  {
    fextl::pmr::named_monotonic_page_buffer_resource resource("release-error");
    for (size_t size : {size_t(4096), size_t(8192), size_t(16384)}) {
      auto* p = static_cast<unsigned char*>(resource.allocate(size, 16)); *p = 0x51;
    }
    require(live.size() == 3);
    resource.release();
    require(calls == 3 && error_reads == 0 && live.size() == (error_code ? 1U : 0U));
    require(baseline || error_code == 0);
    resource.release(); require(calls == 3);
  }
  require(calls == 3);
  const auto retained = live.size();
  for (const auto& entry : live) std::free(entry.first);
  live.clear();
  std::printf("{\"failure_intercepted\":false,\"error\":%u,\"provider_calls\":%u,\"retained_buffers\":%zu,\"error_reads\":%u}\n",
              error_code, calls, retained, error_reads);
}
