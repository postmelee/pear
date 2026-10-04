# DXMT build and Wine Metal pairing

Status: historical component build and finite native pairing verified on October 3, 2026, [Issue #7](https://github.com/postmelee/pear/issues/7). As of October 4, two fresh component builds and their complete unsigned comparison have passed. Final native verification failed again after observation 33; task completion remains pending and the earlier access violation is unresolved. This contributor guide describes the implemented build route and its evidence boundaries; it is not an installation guide for playing Windows games.

Pear retains DXMT's C/C++/Objective-C and Meson implementation, Wine's C/Objective-C driver and callback scheduling, and native LLVM shader conversion. CPU instruction translation is a separate [#5/#6](../delivery-plan.md#core-implementation-backlog) prerequisite. Read the [architecture](../architecture.md), [source qualification](../source-qualification.md), [Wine host guide](wine-host.md) and [contribution procedure](../contributing.md) before changing inputs or running native checks.

## Verified scope

| Evidence | Recorded result | Limit |
|---|---|---|
| Input accounting | Nine selected source components and exact gitlinks/terms accounted for | Accounting is separate from shader readiness; the original #1 aggregate decision remains blocked |
| Native shader prerequisites | ARM64 LLVM 15.0.7, native airconv/static dependencies and Metal compiler outputs built and independently inspected | No airconv application execution, shader workload or rendering qualification |
| DXMT artifacts | Four builtin ARM64X Windows DLLs and thin ARM64 native winemetal constructed | ARM64X DLLs inspected, not loaded or executed by the native fixture |
| Typed driver pairing | Rebuilt Wine driver, DXMT bridge and ordinary ARM64 PE fixture; all 39 finite cases passed | No FEX initialization or translated/hybrid guest dispatch |
| Physical lifetime | Three actual views, three layers and one proxy created and deallocated; zero final leases/attachments | Finite schedule, not arbitrary concurrent race freedom |
| Metal diagnostics | Explicit captured-log review observed no Metal API validation error | Validation enabled/configured does not qualify shader semantics or performance |
| Fresh component reconstruction | Two fresh builds and all 2,878 unsigned inventory entries matched exactly; no normalization | Final candidate native evidence and completion review remain pending; not a second-machine result |

The [Stage 2](../../mydocs/working/task_m1_7_stage2.md), [Stage 3](../../mydocs/working/task_m1_7_stage3.md) and [Stage 4](../../mydocs/working/task_m1_7_stage4.md) reports identify their exact receipts and limits. Every observed required host image/process in the Stage 4 finite route was native ARM64 without Rosetta. That result does not qualify Windows x64 Direct3D, Steam, Megabonk, power improvements, older macOS, or ordinary-user distribution. Runtime/game/distribution eligibility remains false.

The [initial access-violation record](../../mydocs/troubleshootings/task_m1_7_initial_access_violation.md)
preserves the original failure and a new incomplete unchanged-candidate run
at the same observation boundary, with different exit signatures. No common
cause, fix or environmental cause has been established. Formal verification
remains failed; diagnostic variants and the historical Stage 4 result cannot
replace it.

## Pinned inputs and build roles

[Component inputs](../../runtime/dxmt/inputs.json), [tool candidates](../../runtime/dxmt/toolchain.json), [baseline configuration](../../runtime/dxmt/build-config.json) and the [ordered graphics supplements](../../runtime/dxmt/patches/series.json) define separate, exact inputs. Historical candidate fields such as `proposed_unacquired`, `unresolved` and `graphics_patch_status: unimplemented` are preserved; later producer-bound preparation/build/pairing receipts record actual outcomes. Do not update a historical field to make an old receipt appear ready.

| Role | Selected revision or version |
|---|---|
| DXMT | `7c8dee1c2d73415301ceb7d1fa810861cef4cd67` |
| DirectX headers | `9df86f2341616ef1888ae59919feaa6d4fad693d` |
| Native LLVM shader libraries | LLVM 15.0.7, `8dfdcc7b7bf66834a761bd8de445840ef68e4d1a` |
| Wine base | `4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf` plus #4's unchanged 23-patch series |
| LLVM-MinGW cross compiler | 20260908 / LLVM 23.1.1; archive SHA-256 `d1dc5d1ecf3a3ced5ed5544c72f1acd0c8e84eb3024d520ecc6b143eec62a149` |
| Native build tools | CMake 3.31.8, Ninja 1.13.1 and Meson 1.10.0, each admitted by actual source/archive/build and byte evidence |
| Selected developer environment | Xcode 26.6 (17F113), SDK 26.5, Apple Clang 21, Python 3.13.5 for the recorded Stage 2 tool configuration, and Metal Toolchain 17F109 |

Wine's historical patch-series SHA-256 is `39371f21f25cf153437fd523951be9f938cc1161bed5c4ef923583c74c89d086`; its final prepared source-manifest SHA-256 is `2c0c861669f9fd8853f8899eaeb08b18207b0cf26b34dae9efe707919e447bc7`. Graphics supplements record each changed file's exact before/after bytes against that baseline. Source caches and earlier patch series stay read-only. The optional `wine-dxmt-interface` source is accounted for but unselected; Pear's downstream typed supplement supplies this component boundary.

Native LLVM 15 supplies shader libraries; cross LLVM 23 compiles Windows ARM64EC/ARM64X code; Apple Clang compiles Darwin code. Their versions and roles are not interchangeable. CMake uses its admitted official archive; Ninja reuses an earlier verified source build rather than claiming a new compiler/tool rebuild in #7; Meson uses pinned source. The tools verifier replays that reuse chain before accepting current bytes.

The selected configuration is release/builtin mode, Windows `arm64ec-w64-mingw32` with `-marm64x`, and ARM64 Darwin host code. D3D12, NVAPI, NVNGX, upstream tests and Windows airconv are disabled. Their source inventory presence does not mean they were built. Native LLVM uses a selected 8,081-file source closure, not a full LLVM checkout/build. Its deployment target 14.0 and different Wine deployment settings do not establish older-OS support.

Twenty-one selected notice files cover DXMT, DirectX headers, native LLVM, Wine, LLVM-MinGW source/LLVM and MinGW-w64. Current DXMT is LGPL-2.1-or-later; preserve exact version-specific notices and contribution policies. Selected build notices do not establish a complete shipped-payload/corresponding-source or release-licensing gate. No upstream submission is part of this workflow.

## Prepare a local development reconstruction

These are the implemented split commands. Run from the Pear checkout under an approved task, use fresh output names, and retain failures. For the historical split tools below, set `pear_dxmt_legacy_python` to the recorded Python 3.13.5 executable. They use historical local imports. For the current `deterministic_*` tools, use the tested `python3 -B -m tools.dxmt.<module>` invocation from the checkout root. Direct script paths put the local `inspect.py` ahead of the standard library and fail in Python 3.14's argparse color initialization; conversely, the historical split tools are not package-module entrypoints. No Python upgrade or historical producer rewrite is implied. All outputs belong under ignored `.build/task7/`; private source/tool/role handles identify local evidence, not distributable files. The tools are currently bound to the reviewed local provenance chain. Another contributor must acquire the exact sources and prepare equivalent Wine/tool records; changing a host/path/receipt lock requires review and fresh qualification, not a guessed path replacement.

Before starting, obtain the source cache described by [source qualification](../source-qualification.md) and the source-built Wine native/companion/tool records described by [Wine host development](wine-host.md). Supply an owned `roles.json` with record kind `dxmt_wine_role_selection`, schema version 1, scope `dxmt_component`, and distinct `native`, `companion` and `cross_tools` absolute local roots. The native role supplies winebuild and native Wine libraries; companion roles supply the actual selected import archives. Both roles use `aarch64-windows` for relevant imports. No nonexistent `arm64ec-windows` directory is required or manufactured.

For the recorded route, define local variables `pear_dxmt_source_cache`, `pear_dxmt_tool_reuse`, `pear_dxmt_meson_repository`, `pear_dxmt_cross_tools` and `pear_dxmt_wine_roles`. They point to the verified cache, earlier tool proof, pinned Meson Git repository, Wine tool root and owned roles file respectively. Values remain private. Do not repurpose HOME, publish profile contents, or replace the locked source cache with an authenticated game prefix.

```sh
"$pear_dxmt_legacy_python" -B tools/dxmt/prepare.py --inputs runtime/dxmt/inputs.json --source-cache "$pear_dxmt_source_cache" --output .build/task7/stage2-inputs2 --require-empty
"$pear_dxmt_legacy_python" -B tools/dxmt/tools.py prepare --toolchain runtime/dxmt/toolchain.json --reuse-root "$pear_dxmt_tool_reuse" --meson-repository "$pear_dxmt_meson_repository" --output .build/task7/stage2-tools2 --require-empty
"$pear_dxmt_legacy_python" -B tools/dxmt/build_native.py prepare --inputs runtime/dxmt/inputs.json --prepared .build/task7/stage2-inputs2 --source-cache "$pear_dxmt_source_cache" --output .build/task7/stage2-native-source5 --require-empty
"$pear_dxmt_legacy_python" -B tools/dxmt/build_native.py llvm --source .build/task7/stage2-native-source5 --tools .build/task7/stage2-tools2 --output .build/task7/stage2-llvm5 --jobs 2 --max-growth-bytes 17179869184 --reserve-free-bytes 4294967296 --require-empty
"$pear_dxmt_legacy_python" -B tools/dxmt/verify.py native --root .build/task7/stage2-llvm5 --require-llvm
"$pear_dxmt_legacy_python" -B tools/dxmt/check.py shader-tools --toolchain runtime/dxmt/toolchain.json --tools .build/task7/stage2-tools2 --output .build/task7/stage2-shader-capabilities1 --require-ready
"$pear_dxmt_legacy_python" -B tools/dxmt/verify.py shader-tools --root .build/task7/stage2-shader-capabilities1 --require-ready
"$pear_dxmt_legacy_python" -B tools/dxmt/build_native.py shaders --llvm .build/task7/stage2-llvm5 --prepared .build/task7/stage2-inputs2 --tools .build/task7/stage2-tools2 --capabilities .build/task7/stage2-shader-capabilities1 --output .build/task7/stage2-native-shaders1 --jobs 2 --max-growth-bytes 8589934592 --reserve-free-bytes 4294967296 --require-empty
"$pear_dxmt_legacy_python" -B tools/dxmt/verify.py native --root .build/task7/stage2-native-shaders1 --require-complete
```

The names above identify accepted historical output roles; on the recorded checkout they already exist. Choose a new reviewed layout and use its matching paths consistently for another preparation. There is no overwrite/resume operation. A Metal lookup or version string cannot replace the required compile/metallib-link capability gate. Missing tools remain unavailable. The recorded Metal component was installed separately after explicit approval; these commands do not install it, change global Xcode selection, accept licenses/accounts or change macOS security protections. Developer prerequisites are not Pear's eventual end-user requirements.

## Construct and inspect the Windows/native artifacts

The [builder](../../tools/dxmt/build.py) combines byte-verified native Wine winebuild/ntdll/winemac/win32u libraries with the companion winecrt0/ntdll/dbghelp import archives. It configures Meson without dependency downloads or a Windows executable wrapper, builds exactly four DLL targets and native winemetal, captures raw compiler outputs, runs four explicit Wine builtin operations, then installs runtime-tagged outputs without rebuilding or stripping.

```sh
"$pear_dxmt_legacy_python" -B tools/dxmt/build.py --inputs runtime/dxmt/inputs.json --config runtime/dxmt/build-config.json --toolchain runtime/dxmt/toolchain.json --native .build/task7/stage2-native-shaders1 --prepared .build/task7/stage2-inputs2 --tools .build/task7/stage2-tools2 --cross-tools "$pear_dxmt_cross_tools" --wine-roles "$pear_dxmt_wine_roles" --output .build/task7/stage3-build --jobs 2 --max-growth-bytes 8589934592 --reserve-free-bytes 4294967296 --require-empty
"$pear_dxmt_legacy_python" -B tools/dxmt/inspect.py --root .build/task7/stage3-build --require-complete
```

Install layout is `aarch64-windows/{d3d11,dxgi,d3d10core,winemetal}.dll` and `aarch64-unix/winemetal.so`. The `.so` is a Mach-O library. Raw outer PE machine `0xaa64`, CHPE ranges, alternate AMD64 view `0x8664` and configured ARM64EC emission are separately inspected; no header is changed to satisfy an architecture reader. Compiler-to-builtin proof permits only the verified 32-byte Wine marker replacement at offset 64. Installed DLLs must equal their postprocessed outputs; native build/install bytes must also match.

Independent inspection replays sources/producers/commands/roles, exports and ordinals, native dependency names/search paths, generated shaders/version header and notices. External Windows API/CRT imports remain unresolved runtime observations. A complete static inventory cannot infer dynamic loader resolution or Direct3D correctness.

## Typed driver and historical finite native verification

[Graphics supplements](../../runtime/dxmt/patches/series.json) replace the copied private Wine window layout with the sole private native getter `pear_macdrv_metal_v1_get_interface`. Version 1 validates a 48-byte table, required feature mask 7 and zeroed error outputs. Opaque leases are bounded to 64 live entries. Acquire/query/release plus `with_layer` define owned references and a checked, bounded borrowed-layer callback. No private Wine offset becomes a stable public ABI.

Wine retains the actual client surface under its existing lock and releases that lock before any potentially reentrant main-thread wait. Surface replacement, detach and destruction invalidate generations. DXMT's retained proxy owns one lease, while all six layer consumers use the checked operation. Final release balances the bridge attachment exactly once; an owned transient reference protects each callback. Finite fixtures observe physical deallocation, not just registry counters.

```sh
"$pear_dxmt_legacy_python" -B tools/dxmt/pairing_build.py --artifact .build/task7/stage3-build --output .build/task7/stage4-build6 --max-growth-bytes 8589934592 --reserve-free-bytes 4294967296 --require-empty
"$pear_dxmt_legacy_python" -B tools/dxmt/pairing_check.py --artifact .build/task7/stage4-build6 --require-native-abi
```

The actual construction rebuilds the Wine Mac driver and full configured DXMT pair from separately projected source. Ten recorded commands include the ordinary ARM64 fixture compilation. The independent [pair reader](../../tools/dxmt/pairing_check.py) replays exact source postimages, copied fixtures/producers, Wine roles/configuration, generated inputs and all eight actual component artifacts. Hybrid DLLs remain compile/inspect-only under the preserved Wine publisher guard.

Restricted native verification requires a current development profile for `io.github.postmelee.pear.wine-loader`, matching device/expiry/claims and an available Apple Development certificate. Refer to the [Wine authorization procedure](wine-host.md) before an approved run. The current profile/CMS and exact signer leaf certificate are checked independently for each relevant signed image; ordinary libraries/server/helpers retain zero entitlements. The actual loader uses authorized cross-architecture/JIT claims, 4 KiB signature pages, Hardened Runtime and library validation. Development signing is a separate identity, not ordinary-user permission.

```sh
"$pear_dxmt_legacy_python" -B tools/dxmt/pairing_runtime.py --artifact .build/task7/stage4-build6 --profile "$pear_wine_profile" --output .build/task7/stage4-runtime1 --require-empty
"$pear_dxmt_legacy_python" -B tools/dxmt/run_pairing.py --runtime .build/task7/stage4-runtime1 --output .build/task7/stage4-pairing1 --require-empty
# An explicit separate immutable private diagnostics review is required.
"$pear_dxmt_legacy_python" -B tools/dxmt/pairing_evidence.py --run .build/task7/stage4-pairing1 --require-complete
```

The runtime preserves the full retained Wine payload, replaces only the paired driver images, and adds native winemetal and the original ordinary ARM64 fixture. Fresh live Apple admission is separate from pure structural replay. Run serially in the tested active/awake graphical-session conditions with fresh synthetic prefixes, owned descendants, deadlines, bounded logs and an unrelated sentinel. These tools execute actual ordinary ARM64 PE/native code; they do not execute FEX or ARM64X renderer DLLs.

The selected [Apple Metal-validation guide](apple-tooling.md) and installed manual are reconciled with Wine's actual environment before device creation. API error mode remains `assert`, warnings use `nslog`, shader validation uses `zerofill` with stderr reporting. The closed runner sets these variables directly before the verified Wine process creates its device; Apple's generic `open --env` app example is not a substitute for this Wine recipe. Validation controls are correctness settings, not performance measurements.

The native evidence gate requires an owned read-only `diagnostics-review.json` bound to the exact run/case/assessment/runtime/producers and every raw stream. It requires explicit review even if stderr is empty, covers every nonfixture stderr line by offset/length/hash, and refuses validation errors or unknown validation warnings. The original run's review remains `unperformed`; the separate review establishes only `finite_native_scope_complete`. The recorded 39 cases cover ABI errors, view/lease ownership, six layer operations, resize/replacement/detach/destruction, owned exception/reentry, native dlclose, physical lifetime and cleanup. General shader/rendering/performance qualification remains unperformed.

## Fresh deterministic reconstruction and current native verification

The [deterministic constructor](../../tools/dxmt/deterministic_pair.py),
[native adapter](../../tools/dxmt/deterministic_native.py) and
[coordinator](../../tools/dxmt/deterministic_reproduce.py) preserve historical
producers through an exact captured-source namespace. The current constructor
has a distinct record kind and source-pin closure. It cannot reuse an older
recipe's success flag or native execution record. Final completion remains
pending until the two current constructions, raw comparison and fresh final
candidate execution all pass.

The selected deterministic recipe fixes Windows compilation directories and
`SOURCE_DATE_EPOCH`, sends the original shader bytes through bounded stdin,
and binds the actual Metal resource directory and four original recipe options.
The current candidate also adds `-Wl,-objc_stubs_small` to native C/C++ link
settings. On October 4, repeated links of identical inputs exposed two raw
winemetal outputs with the default linker settings; the small-stub option
produced identical whole bytes in eleven trials. Two fresh full builds and
native execution of this changed recipe remain unperformed.
[Apple describes this option](https://developer.apple.com/videos/play/wwdc2022/110363/)
as a size-oriented alternative with an additional call indirection. Its runtime
performance impact here is unmeasured; this is a scoped reproducibility
workaround, not a speed improvement. Windows cross settings and shader inputs
are unchanged. See the [partial observations](../../mydocs/working/task_m1_7_stage5_reconstruction_observations.json)
for trial counts and explicit incomplete gates.
It does not rewrite generated binaries or normalize comparison differences.
Here, unsigned comparison means the payload before Pear development signing.
Any linker-generated ad hoc CodeDirectory remains part of the exact raw bytes;
it is not stripped or excluded from the comparison.
The observer admits only the source-bound Wine locale link and narrowly checked
transient Metal module-cache lock links. The original process supervisor still
owns deadlines, logs, process-group cleanup, output growth and free-space limits.

Prepare an independently reviewed `dxmt_deterministic_input_qualification`
schema-3 record as `pear_dxmt_qualification`. This currently binds retained
original build/control records, complete Metal resource bytes, prior real
shader controls and the fixed-compilation-directory proof. It is a private
local research prerequisite, not an automatically generated portable installer
manifest. Retain its actual inputs. The committed code alone does not recreate
these private historical receipts; moving to another host or replacing input
identities requires new qualification. No Steam/game/account data is needed
for this finite component workflow.

Define `pear_repo` as the absolute checkout path and `pear_wine_profile` as the
private currently authorized loader development profile. The names below are
examples of fresh owned outputs. Existing destinations are rejected. Serialize
compilation, signing, native execution and cleanup; the recorded runs use a
shared host lock and two build jobs.

```sh
python3 -B -m tools.dxmt.deterministic_pair --repo "$pear_repo" --construct --artifact .build/task7/stage3-build --qualification "$pear_dxmt_qualification" --output .build/task7/deterministic-reference --max-growth-bytes 2147483648 --reserve-free-bytes 4294967296 --require-empty
python3 -B -m tools.dxmt.deterministic_pair --repo "$pear_repo" --construct --artifact .build/task7/stage3-build --qualification "$pear_dxmt_qualification" --output .build/task7/deterministic-candidate --max-growth-bytes 2147483648 --reserve-free-bytes 4294967296 --require-empty
python3 -B -m tools.dxmt.deterministic_reproduce --repo "$pear_repo" --constructor-root tools/dxmt --compare --reference .build/task7/deterministic-reference --candidate .build/task7/deterministic-candidate --output .build/task7/deterministic-comparison --require-empty
```

Each construction reprojects sources and recompiles the affected Wine driver,
ordinary ARM64 fixture and configured DXMT pair. Compiler, Wine base runtime,
LLVM and selected tool prerequisites are reused only after byte/source checks.
This is same-host component reconstruction, not an independent compiler build,
second-machine result or reconstruction of the entire runtime.

The comparison inventories the complete conceptual unsigned Wine payload with
its exact graphics overlays, the complete DXMT install and selected compiler,
generated, shader and notice products. It checks path sets, bytes, sizes, modes
and contained aliases. Normalization is `none`; any difference fails with both
inventories and detailed comparison retained. Linker-generated ad-hoc Mach-O
signatures remain part of the unsigned bytes. An explanation of a difference
does not make it pass. `construction.json` records native pairing as unperformed
and overall reconstruction as incomplete even after a passing raw comparison.

Use the exact second candidate for current development signing and execution:

```sh
python3 -B -m tools.dxmt.deterministic_native --repo "$pear_repo" --constructor-root tools/dxmt --prepare --build .build/task7/deterministic-candidate --profile "$pear_wine_profile" --output .build/task7/deterministic-runtime
python3 -B -m tools.dxmt.deterministic_native --repo "$pear_repo" --constructor-root tools/dxmt --run --runtime .build/task7/deterministic-runtime --output .build/task7/deterministic-pairing
python3 -B -m tools.dxmt.deterministic_native --repo "$pear_repo" --constructor-root tools/dxmt --review-context --run-root .build/task7/deterministic-pairing
# Explicitly review all raw streams and write the bound immutable private review.
python3 -B -m tools.dxmt.deterministic_native --repo "$pear_repo" --constructor-root tools/dxmt --evidence --run-root .build/task7/deterministic-pairing
python3 -B -m tools.dxmt.deterministic_reproduce --repo "$pear_repo" --constructor-root tools/dxmt --complete --output .build/task7/deterministic-comparison --native-evidence .build/task7/deterministic-pairing --require-complete
python3 -B -m tools.dxmt.deterministic_reproduce --repo "$pear_repo" --constructor-root tools/dxmt --verify --output .build/task7/deterministic-comparison --require-complete
```

The native adapter preserves the original 39-case protocol, per-image live
permission checks, exact runtime bytes and required private diagnostics review.
The raw review-context API preserves process-ID sets for validation-notice
attribution; the CLI exports those validated identities as sorted JSON lists
for private inspection. This serialization does not grant diagnostics approval.
The historical Stage 4 result cannot satisfy the current finalizer: fresh
execution must bind to this exact candidate and current constructor source.
No ARM64X renderer DLL, FEX initialization or translated x64 guest is executed
by this ordinary ARM64 fixture.

Only the finalizer and independent replay can establish
`reconstruction_complete=true`. They preserve `runtime_eligible=false`,
`game_qualified=false` and `distribution_qualified=false`. They do not sign or
launch native processes. Requested operation failures return 1; argument usage
errors return 2. Preserve failures and use a new reviewed output for a retry;
never overwrite the original build, run or review to obtain a passing record.

## Storage, verification and handoff

Native operations are serialized. Actual admission uses two jobs, a 16 GiB LLVM or 8 GiB shader/component output-growth ceiling, and at least a 4 GiB free reserve. A stricter reviewed growth ceiling may be used while retaining the reserve. Admission includes the selected ceiling plus reserve; they are operational bounds, not measured disk/memory peaks. Stage 2 observed 459,530,240-byte LLVM and 69,992,448-byte shader output growth, which does not guarantee future requirements. Materializing/signing the full Wine payload and fresh prefixes needs additional explicitly admitted storage.

Retain required source caches, original native/companion Wine receipts/install origins, tool sources/archive proof, accepted LLVM/shader objects/installs, accepted component outputs, raw command/diagnostic records and private current authorization until their consumers no longer need them. Do not delete a referenced payload merely because its receipt or source code is on GitHub. Safe pruning must identify exact reproducible unreferenced duplicates, preserve failure evidence and reconstruction identity, and account for any loss of historical replay availability. Git is not a store for proprietary binaries, private profiles or raw diagnostics.

```sh
python3 -B -m unittest discover -s tests/dxmt -p 'test_*.py'
python3 -B -m unittest discover -s tests/wine -p 'test_*.py'
python3 tools/check_governance.py
git diff --check
```

Portable tests validate only their selected reader/refusal/lifecycle contracts; conditional skips remain unperformed. The recorded Stage 4 counts are 284 DXMT tests and 842 Wine tests with ten conditional skips. Preserve native warnings, actual OS errors, failed attempts, unknown observations and deadlines separately from test counts. A missing required record or failed requested gate cannot be promoted by a producer-supplied `passed` flag.

[#8](https://github.com/postmelee/pear/issues/8) must qualify actual x64 Direct3D 11 through the matching #5/#6 translation path: device/resource/shader/compute/depth/blend/readback, swapchain/resize/present, callbacks, actual module selection and rendering results. #10 owns complete process/module observation; #11/#12 own Steam and Megabonk; #13 and ordinary-user work own assembled release authorization, notices, packaging and clean-user installation. This build and finite native guide does not close those gates or promise a performance advantage.
