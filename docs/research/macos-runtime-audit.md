# Rosetta-free macOS runtime audit

Checked: 2026-09-27. Status: architecture research, not an implemented or certified Pear runtime.

This audit distinguishes inspected public source, locally inspected SDK declarations, vendor demonstrations, and work that Pear must still validate. It does not claim that Megabonk has run without Rosetta. The existing local Wine/DXMT game experiment remains a Rosetta-dependent reference.

Implementation follow-up, September 27, 2026: the [native host diagnostic](../host-capabilities.md) now records process-local observations and their limits. It does not execute the ABI, memory/JIT or signing-authorization tests proposed in this audit.

## Recommendation

Develop a direct macOS runtime around ARM64 Wine, its ARM64EC/WoW64 emulator interfaces, FEX, and an ARM64-capable graphics layer. Start with public-source and host-capability gates, then fund the missing macOS integration as actual runtime engineering. Avoid building the product around an opaque commercial preview binary.

The preferred FEX entry point is its Windows emulator modules, not a wholesale port of its Linux application loader and Linux syscall emulation. Keep Windows API implementation in Wine and macOS host work in a narrow, documented platform boundary. That boundary must handle memory, ABI transitions, exceptions, executable code, thread state, and signing; changing implementation language or code-generation backend does not eliminate those requirements.

A Linux ARM64 virtual machine is a useful independent reference and a possible fallback architecture. Its graphics and integration costs must be measured before selecting it for the product.

## Evidence and limits

| Evidence | What it establishes | What it does not establish |
| --- | --- | --- |
| [CodeWeavers ARM64 Mac Preview announcement, 2026-07-31](https://www.codeweavers.com/blog/mjohnson/2026/7/31/crossover-preview-the-right-to-bear-arm64-on-mac) | The vendor reports ARM64 Wine, a macOS adaptation of FEX, and ARM64 DXMT. Its native path requires macOS 26.5+. | A reproducible Pear build, availability of all preview patches, current Megabonk compatibility, or a license to redistribute the complete commercial product. |
| [CrossOver public source page](https://www.codeweavers.com/crossover/source) | The page currently links source for 26.3.0. | That this archive contains the later ARM64 Preview changes. The archive was not downloaded or audited here. |
| [Wine maintainer announcement, 2026-08-07](https://list.winehq.org/hyperkitty/list/wine-devel@list.winehq.org/message/CKG5CEN2BE5VRXZ7O7NX4YUSBH3247WH/) | Documents new macOS facilities and planned upstream integration. | That the complete implementation is merged and buildable today. |
| [Wine September discussion](https://list.winehq.org/hyperkitty/list/wine-devel@list.winehq.org/2026/9/?view=messages) | On September 8, upstream MRs/documentation were still planned; a participant reported inability to enable the capability with a free developer account. | A definitive policy for all Apple accounts, or proof that no later patch exists. |
| Public source and SDK inspection below | Identifies concrete reuse points and port responsibilities. | Successful compilation, entitled execution, or a complete repository-wide absence proof. |

The Preview announcement describes its initial build as testing-oriented and notes launcher limitations. Universal packaging may choose Intel Wine on an older OS. Therefore “the app opened” is insufficient evidence of Rosetta independence.

## Exact public source inspected

The following commit IDs were resolved through GitHub's public API during this audit. They are evidence snapshots, not approved release dependencies.

### Wine

Commit: [`4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf`](https://github.com/wine-mirror/wine/tree/4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf).

Inspected files:

- [`loader/main.c`](https://github.com/wine-mirror/wine/blob/4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf/loader/main.c)
- [`loader/preloader_mac.c`](https://github.com/wine-mirror/wine/blob/4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf/loader/preloader_mac.c)
- [`dlls/ntdll/unix/loader.c`](https://github.com/wine-mirror/wine/blob/4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf/dlls/ntdll/unix/loader.c)
- [`dlls/ntdll/unix/signal_arm64.c`](https://github.com/wine-mirror/wine/blob/4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf/dlls/ntdll/unix/signal_arm64.c)
- [`configure.ac`](https://github.com/wine-mirror/wine/blob/4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf/configure.ac)

`signal_arm64.c` already contains Apple-specific signal-context handling. It is inaccurate to describe upstream as having no ARM64 macOS code. Conversely, these sampled loader, signal, and configuration files did not contain the API spellings `os_set_custom_x18_abi_enabled`, `posix_spawnattr_set_4k_page_size_np`, or `thread_set_x86_64_compat`. The sampled Mac preloader still has CPU-specific implementation branches and an unsupported-CPU error. This does not mean that every build configuration uses that preloader, or prove the APIs are absent from all other branches/files.

**Required follow-up:** inspect the complete chosen Wine tree and relevant merge requests; produce an explicit patch inventory, configure invocation, toolchain lock, and clean build log. Do not turn this bounded search into an assertion that a full port must begin from zero.

### FEX

Commit: [`59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa`](https://github.com/FEX-Emu/FEX/tree/59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa).

Inspected files:

- [`CMakeLists.txt`](https://github.com/FEX-Emu/FEX/blob/59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa/CMakeLists.txt)
- [`Source/Windows/CMakeLists.txt`](https://github.com/FEX-Emu/FEX/blob/59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa/Source/Windows/CMakeLists.txt)
- [`Source/Windows/ARM64EC/Module.cpp`](https://github.com/FEX-Emu/FEX/blob/59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa/Source/Windows/ARM64EC/Module.cpp)
- [`Source/Windows/UnixLib/CMakeLists.txt`](https://github.com/FEX-Emu/FEX/blob/59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa/Source/Windows/UnixLib/CMakeLists.txt)
- [`Source/Windows/UnixLib/FEXUnixLib.cpp`](https://github.com/FEX-Emu/FEX/blob/59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa/Source/Windows/UnixLib/FEXUnixLib.cpp)
- [`Source/Windows/Common/FEXUnixLib.h`](https://github.com/FEX-Emu/FEX/blob/59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa/Source/Windows/Common/FEXUnixLib.h)
- [`Source/Windows/Common/FEXUnixLib.cpp`](https://github.com/FEX-Emu/FEX/blob/59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa/Source/Windows/Common/FEXUnixLib.cpp)

Findings:

1. The root build rules accept Linux and Windows, and reject a native Darwin target. Removing that check alone is not a macOS port. Cross-building a Windows PE module is a different target and is not ruled out by this Darwin check.
2. Windows modules and Wine Unix libraries already form an integration boundary. The Unix library build explicitly emits `.so` files and links `rt`; its implementation includes Linux `prctl` handling. Port those host services deliberately, including hardware memory-order controls, rather than assuming Linux binaries can be copied to macOS.
3. The ARM64EC module has guest-context reconstruction, suspend handling, guard-page handling, and self-modifying-code invalidation logic. Reuse these semantics and their tests. Replacing only the ARM instruction emitter would not replace this runtime.

The [FEX ARM64EC guide](https://wiki.fex-emu.com/index.php/Development:ARM64EC) explains the architectural advantage: FEX's Windows modules handle CPU emulation while Wine/ARM64EC handles the surrounding API boundary. Native host libraries can then be used without translating a whole x86 Linux userspace. Its published build recipe and fork recommendations are Linux-oriented; they are not a macOS installation guide.

### Graphics boundary

DXMT has a public [`build-arm64ec.txt`](https://github.com/3Shain/dxmt/blob/main/build-arm64ec.txt) using ARM64EC tools and ARM64X options. This is useful build evidence, not proof that every native Metal bridge or dependency is ready for Pear. The graphics workstream must inventory the PE DLLs, native library slices, shader compiler dependencies, ABI callbacks, and required Wine changes as a single tested version set.

## Host facilities and port responsibilities

The local Xcode SDK reported version **26.5**. Only headers were inspected; no entitlement-requiring probe was executed during this audit. SDK paths below are relative to `$(xcrun --show-sdk-path)` and contain no developer-specific paths.

| Boundary | Evidence | Required Pear work |
| --- | --- | --- |
| Windows versus Apple `x18` usage | `usr/include/os/arch/arm64.h` declares `os_set_custom_x18_abi_enabled` and `os_custom_x18_abi_enabled`. | Centralize entry/exit thunks and model nested callbacks, signals, and error exits. Preserve the Windows thread pointer on the foreign-ABI side. |
| Windows 4 KiB page semantics | `usr/include/spawn.h` declares `posix_spawnattr_set_4k_page_size_np`. | Set up the process before PE mappings; verify page size and independent sub-page protection/decommit behavior. Do not infer semantics from alignment alone. |
| Guest low address space | The Wine maintainer documents the `-Wl,-x86_64_layout_emulation` linker facility and adjustable/remappable `PAGEZERO`. | Reserve the required address ranges before system allocations and validate Windows shared-data placement and 32-bit helper mappings. |
| x86 memory ordering | `usr/include/mach/mach_traps.h` declares `thread_set_x86_64_compat`. The maintainer states the mode is per-thread and is not inherited. | Apply and verify the selected policy for every relevant thread; retain a correct fallback when hardware acceleration is unavailable. |
| Windows exceptions on Mach/POSIX | Wine already has Apple ARM64 context handling; FEX reconstructs guest state. | Test fault address/program counter, SEH dispatch, stack unwinding, guard pages, asynchronous suspend, and resumption across guest/native boundaries. |
| JIT and changed executable pages | Apple's JIT documentation and FEX's invalidation machinery cover different sides of this boundary. | Specify allocation, write/execute transitions, instruction-cache invalidation, patch visibility, and lifetime synchronization for the chosen Wine/FEX port. |

The SDK's availability annotations differ from the vendor's supported product floor: the inspected x18 declarations are annotated macOS 26.4 and the 4 KiB spawn declaration macOS 26.0. These are compile-time declarations, not proof of all kernel, entitlement, and runtime prerequisites on those releases. **Keep macOS 26.5 as the initial candidate minimum until the full capability suite proves another minimum.**

### The x18 contract is more than a register save

The inspected Apple SDK header requires custom mode only while executing the foreign ABI. Calling ordinary macOS libraries/frameworks, including POSIX interfaces, in that mode is disallowed. Calling the mode setter with the already-active value aborts. Leaving custom mode destroys its x18 value, so the foreign side must preserve and restore its own thread pointer; Apple maintains the system-side value. Asynchronous callbacks must make the same distinction.

Consequently the port needs an explicit state transition contract. A logging call, allocation, signal-handler helper, Objective-C callback, or graphics callback can violate it. Audit all such transitions and test nested guest → host → guest calls. The contract applies whether the surrounding code is C, C++, Rust, Swift, or generated by Cranelift.

### Executable memory and signing are separate gates

[Apple's JIT guidance](https://developer.apple.com/documentation/apple-silicon/porting-just-in-time-compilers-to-apple-silicon) documents `MAP_JIT`, write/execute protection, callback allowlisting, and instruction-cache invalidation. Those are implementation constraints to reconcile with the selected Wine memory manager, not a reason to blindly replace every guest allocation with `MAP_JIT`. Test JIT code-cache allocation separately from PE image loading and guest self-modifying memory.

The Wine maintainer identifies restricted `com.apple.developer.cross-architecture-support` and `com.apple.developer.cross-architecture-support-unmanaged` entitlements, provisioning profiles, and an app-bundled loader. The September reports leave free-account access unresolved. Neither an ad-hoc signature nor adding an entitlement string proves that Apple authorizes it.

Pear must establish two independently recorded outcomes:

1. **Developer execution:** an approved development identity/profile can run a signed probe with SIP and normal code-signing protections enabled.
2. **User distribution:** the intended Developer ID/notarization/provisioning route works on a second Mac without enrolling every user as a developer, if that is the promised installation model.

Do not equate success on a registered development device with general distribution. [Apple's Hardened Runtime documentation](https://developer.apple.com/documentation/xcode/configuring-the-hardened-runtime) also ties notarization to the hardened runtime; document necessary exceptions narrowly. A SIP/AMFI-disabled experiment does not pass either Pear product gate.

Record the scope of the first-milestone result explicitly. Development-profile execution under normal protections can establish that technical result; it must not be described as a generally distributable consumer release until the separate distribution test passes.

## Direct macOS versus Linux ARM64 VM

| Dimension | Direct Wine/FEX/DXMT on macOS | Linux ARM64 VM with Wine/FEX |
| --- | --- | --- |
| Reuse | Windows API and CPU core are reusable; Darwin boundaries need completion. | FEX's established host and Linux Wine integration are closer to existing workflows. |
| Host CPU execution | ARM64 macOS processes execute generated ARM64 code. | ARM64 guest can use hardware virtualization; FEX still translates the game's x64 code. |
| Graphics | D3D11 → DXMT → Metal. | Candidate D3D11 → DXVK → guest Vulkan/Venus → host graphics backend; each layer needs verification. |
| Platform risk | Cross-architecture entitlement, ABI, memory layout, JIT, signing. | VM graphics features, guest maintenance, display/input/audio, memory/disk footprint, host graphics translation. |
| Value for Pear | Preferred coherent Mac runtime when gates pass. | Independent compatibility reference and contingency, not assumed to be faster or simpler overall. |

[UTM 5.0.6 Beta, released September 24](https://github.com/utmapp/UTM/releases/tag/v5.0.6), documents Vulkan 1.3 for Linux through VirtIO Venus and updates graphics backends. It also documents remaining rendering limitations. Thus “macOS VMs cannot accelerate graphics” is outdated, while “Vulkan 1.3 makes Megabonk work” remains unproven. Select a particular VM backend/driver stack and test the actual required features; do not conflate Apple's Virtualization framework path with QEMU's Venus path.

Use a 4 KiB-page ARM64 Linux guest as an initial controlled reference. Ensure guest x86 execution uses FEX, with any Rosetta-for-Linux integration disabled. This avoids accidentally passing the CPU independence claim through a different Rosetta entry point.

Booting Asahi Linux directly is another useful engineering reference, but it changes the host operating system and does not itself meet the goal of playing inside macOS.

## Bounded host-runtime acceptance tests

These are proposed tests, not completed results. H0–H6 are local audit test groups, not additional project milestones; the G0–G4 gates in [the architecture specification](../architecture.md#8-quality-gates-and-dependency-order) are normative. Keep each issue attached to saved commands, versions, expected outcomes, and sanitized logs.

| Gate | Bounded acceptance test | Failure decision |
| --- | --- | --- |
| H0 — Source completeness | One manifest lists exact commits, patches, dependencies, licenses, build tools, and native/PE outputs. A clean machine reproduces the build without commercial preview binaries. | Inventory the missing component and either implement its port or wait for usable upstream source; do not mark a binary-only setup as an open build. |
| H1 — Host capability and distribution | Build a small ARM64 probe; record OS/SDK, entitlement validation, actual page size, low mapping, x18 transitions, TSO return values, and JIT execution. Run under normal protections. Before claiming general-user distribution, separately test the intended distribution package on a second Mac. | Resolve platform access or choose a different architecture. Do not make a language rewrite the response to a signing failure. |
| H2 — CPU/API correctness | Run small x64 PE tests for arithmetic/SIMD, Windows API calls, TLS, nested callbacks, faults/SEH, guard pages, code modification and multithreading. Run a 32-bit smoke test for launcher helpers. Compare deterministic outputs with native Windows reference results. | Minimize failures to the Wine, FEX, or Darwin boundary before attempting full-game debugging. |
| H3 — Graphics and callbacks | Run an x64 D3D11 test covering resource upload/readback, shaders, presentation, resize and repeated device creation. Record the native graphics dependencies and callback path. | Fix the ARM64EC/graphics bridge or unsupported feature; CPU smoke-test success cannot close this gate. |
| H4 — Full required process tree | Launch the legitimately acquired game through the selected Steam integration, inventory all helpers and native loaded images, and capture architecture/translation evidence throughout launch and gameplay. | Any required Rosetta process keeps the first milestone open, even if the game itself uses FEX. |
| H5 — Game and persistence | On a declared Mac/OS/runtime/game build, demonstrate menu, input, audio, save/load, clean exit/relaunch, and at least 20 minutes of active gameplay. Retain frame-time/crash evidence and known issues. | Fix reproducible problems; do not substitute a paused menu or FPS screenshot for active gameplay. |
| H6 — Reproduction and manual recovery | A second person or clean environment follows the documented recipe and reproduces the result. Validate isolated prefixes, manual backup of test saves, and restoration of the previous runtime/prefix without damaging the retained working setup. | Fix isolation and recovery instructions before expanding supported-game claims. Automated product upgrade/rollback is subsequent work, not an additional first-milestone requirement. |

For H4, `file`/Mach-O slice inventory is static evidence only. Instrument Pear-owned loaders to report their own `sysctl.proc_translated` state and actual selected architecture, and collect per-process evidence for helpers. Querying this sysctl in an unrelated shell proves only that shell's state. Apple's [Rosetta documentation](https://developer.apple.com/documentation/apple-silicon/about-the-rosetta-translation-environment) describes the process-local check. There is no requirement to uninstall Rosetta from the user's existing Mac.

Performance comparison follows correctness. Use the same scene, settings, frame cap, display mode, power source and thermal starting conditions, with repeated runs. The prior uncontrolled power samples do not establish an advantage for either architecture.

## Work that can be substantial without becoming a rewrite

- Maintain a small, rebased macOS Wine patch series for host capabilities and ABI transitions, with regression tests.
- Port FEX's Wine host services and integrate its emulator modules into that native runtime.
- Make guest exception/JIT/thread state observable enough to diagnose crashes across translated code.
- Build ARM64 graphics bridges and validate all transitions into macOS frameworks.
- Own an auditable release pipeline, runtime manifest, test harness, and compatibility record.

These form a legitimate Pear runtime engineering effort. They are not merely launcher configuration. A new CPU translator can remain a later research option, but it must eventually pass the same host/API correctness gates and cannot bypass macOS distribution policy.
