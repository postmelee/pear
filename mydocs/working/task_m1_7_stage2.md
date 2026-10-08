# Task #7 Stage 2 — Native ARM64 Shader Prerequisites

GitHub Issue: [#7](https://github.com/postmelee/pear/issues/7)
Implementation plan: [`task_m1_7_impl.md`](../plans/task_m1_7_impl.md)
Stage: 2 — completed October 2, 2026; Stage 3 is not started.

## Stage Purpose

Build and independently verify the selected native LLVM 15, ARM64 airconv and Metal shader prerequisites before constructing DXMT's Windows/native pair. This stage establishes source-derived compilation and artifact closure; it does not establish a running renderer or Rosetta-free Megabonk.

Context used: approved task/implementation plans, root/runtime/DXMT/tests rules, architecture/runtime/source contracts, graphics research and the retained #4 Wine handoff. Reuse preserves upstream C/C++/Objective-C, CMake/Meson definitions and selected notices. Reporting follows the [stage procedure](../skills/task-stage-report/SKILL.md), [daily board procedure](../skills/todo/SKILL.md) and central Hyper-Waterfall v0.3.0 template. The requester explicitly continued to Stage 2 and separately approved Apple's Metal Toolchain 17F109 installation. Compile-only work required no GPU capture or rendering/lifetime expert procedure.

## Artifacts

| File | Change Summary |
|---|---|
| `tools/dxmt/tools.py` | Task-local CMake/Meson/Ninja derivation, exact reused-source/tool identity and native capability replay |
| `tools/dxmt/build_native.py` | Pinned LLVM construction, native airconv/Metal recipes, bounded operations, rooted archive/executable inspection and independent replay |
| `tools/dxmt/check.py`, `common.py`, `verify.py` | Functional Metal compilation/linking, finite failed-attempt evidence and separate LLVM-only/full-prerequisite gates |
| `tests/dxmt/test_native_build_evidence.py`, `test_shader_failure_evidence.py` | Native-format, alias, source/tool/output change, incomplete evidence and setup/cleanup/command failure controls |
| [Observations](task_m1_7_stage2_observations.json) | Reviewed source/tool/command/artifact outcomes without private paths, profiles or raw streams |
| `mydocs/plans/task_m1_7_impl.md`, `mydocs/orders/20261002.md` | Actual split CLI/options, explicit installation authorization and stage progress |

## Body Change Scope / Lossless Preservation

Changes stay in the approved `tools/dxmt/`, `tests/dxmt/` and internal `mydocs/` locations. No official product/API documentation, original source cache, Stage 1 receipt or #4 Wine patch/build layer changed. Repository text is English; private build trees, command streams and installation receipts remain ignored. No artifacts were deleted for storage. Successful receipt schemas and the selected Stage 1 source/tool locks are preserved; current availability and finalized recipes live in separate producer-bound records rather than rewriting historical unavailable observations.

All nine selected source components remain accounted for. The actual shader build uses DXMT `7c8dee1c2d73415301ceb7d1fa810861cef4cd67`, DirectX headers `9df86f2341616ef1888ae59919feaa6d4fad693d` and native LLVM 15.0.7 `8dfdcc7b7bf66834a761bd8de445840ef68e4d1a`. Native LLVM materialization contains 8,081 selected files / 131,624,187 bytes. Existing licenses/notices and original source bytes are retained. NVAPI/NVNGX/D3D12/tests and Windows airconv are disabled; their inventory presence does not imply construction or execution. No Rust rewrite, source-semantic patch or upstream submission was made.

CMake 3.31.8 uses the exact official archive; Ninja 1.13.1 reuses the verified earlier source build, without claiming reproduction in #7. Meson 1.10.0 uses its pinned source and selected Python. LLVM-MinGW 20260908 / LLVM 23.1.1 remains a separate reused cross-tool role, not this native LLVM 15 source-build result. The Metal installation used the approved official component command; no account/license acceptance, persistent PATH, Xcode selection or security-setting change was performed.

## Verification Results

Execution context: Apple M4 Pro, 24 GiB, macOS 26.5.2 (25F84), Xcode 26.6 (17F113), SDK 26.5, Apple Clang 21, selected Python 3.13.5, CMake 3.31.8, Ninja 1.13.1, Meson 1.10.0 and Metal Toolchain 17F109. Native builds select ARM64 and deployment target 14.0; this is a build setting, not qualification on older macOS. Native developer tools and compiler-sanity checks executed; the airconv application, GPU and PE/guest execution were unperformed.

Commands executed (private variables select verified original caches/tool sources; exact arguments and streams remain in owned ignored outputs):

```sh
python3 -B tools/dxmt/prepare.py --inputs runtime/dxmt/inputs.json --source-cache "$pear_dxmt_source_cache" --output .build/task7/stage2-inputs2 --require-empty
python3 -B tools/dxmt/tools.py prepare --toolchain runtime/dxmt/toolchain.json --reuse-root "$pear_dxmt_tool_reuse" --meson-repository "$pear_dxmt_meson_repository" --output .build/task7/stage2-tools2 --require-empty
python3 -B tools/dxmt/build_native.py prepare --inputs runtime/dxmt/inputs.json --prepared .build/task7/stage2-inputs2 --source-cache "$pear_dxmt_source_cache" --output .build/task7/stage2-native-source5 --require-empty
python3 -B tools/dxmt/build_native.py llvm --source .build/task7/stage2-native-source5 --tools .build/task7/stage2-tools2 --output .build/task7/stage2-llvm5 --jobs 2 --max-growth-bytes 17179869184 --reserve-free-bytes 4294967296 --require-empty
python3 -B tools/dxmt/verify.py native --root .build/task7/stage2-llvm5 --require-llvm
python3 -B tools/dxmt/check.py shader-tools --toolchain runtime/dxmt/toolchain.json --tools .build/task7/stage2-tools2 --output .build/task7/stage2-shader-capabilities1 --require-ready
python3 -B tools/dxmt/verify.py shader-tools --root .build/task7/stage2-shader-capabilities1 --require-ready
python3 -B tools/dxmt/build_native.py shaders --llvm .build/task7/stage2-llvm5 --prepared .build/task7/stage2-inputs2 --tools .build/task7/stage2-tools2 --capabilities .build/task7/stage2-shader-capabilities1 --output .build/task7/stage2-native-shaders1 --jobs 2 --max-growth-bytes 8589934592 --reserve-free-bytes 4294967296 --require-empty
python3 -B tools/dxmt/verify.py native --root .build/task7/stage2-native-shaders1 --require-complete
python3 -B -m unittest discover -s tests/dxmt -p 'test_*.py'
python3 -B tools/check_governance.py
git diff --check
```

- Fresh source/tool preparation and independent reference replay passed. Five actual version/SDK commands exited 0. Native LLVM configure, all 1,674 build tasks and installation passed, followed by independent LLVM-only replay. **1,904 installed files / 73 static libraries** have exact version/header, real-member, ARM64-object and byte closure, with bounded symbol-metadata byte inventory. Link compatibility is limited to the actual dependent airconv link below. The upstream TableGen utility is explicitly accounted for as native ARM64 with system-only dependencies; tools-off does not falsely imply no utility was installed.
- The approved official Metal download/install command exited 0; the installed component was observed as 17F109. **Six actual capability commands exited 0**, including shader compilation and metallib linking, followed by independent replay. The probe produced 3,552-byte AIR and 3,527-byte metallib. A lookup/version result alone cannot pass this gate.
- All **five native shader construction commands exited 0**: Meson configuration, airconv compilation, built-in Metal compilation, metallib linking and embedded-header generation. Final independent full-prerequisite replay passed. The native airconv executable is ARM64; `libairconv.a` has 18 real ARM64 objects / 3,587,416 bytes, and required `libDXBCParserNative.a` has three / 53,776 bytes. Rooted descriptor-based inspections reject intermediate aliases and bind exact executable/archive bytes.
- **15 generated shader outputs** are closed: six upstream Metal 3.1 AIR files and six payload-matched headers for the executable/static targets, plus DXMT built-in AIR, metallib and header. The built-in AIR is 36,400 bytes; its metallib is 161,854 bytes. Exact target/settings, selected compiler bytes, generated wrapper/native configuration, logs and output/header payload identities are replay-bound. The wrapper permits only the selected ARM64 Metal/metallib tools; Meson's source/dependency downloads are disabled.
- Builds used two jobs, 16 GiB LLVM / 8 GiB shader growth ceilings and a 4 GiB free reserve. Admission was checked before each operation. Final observed owned-output growth was 459,530,240 bytes for LLVM and 69,992,448 bytes for shaders. These observations and operational limits do not establish a measured peak. LLVM-only verifier output deliberately kept `stage2_complete` false; only the complete shader gate sets it true. Runtime/game/distribution fields remain false.
- **156 portable tests passed in 20.596 seconds.** Original captured execution exited 0 with `OK`; it was not rerun merely for reporting. Controls cover strict exit typing, source/tool/mode/SDK/configuration/output changes, archives and intermediate aliases, shader/header payloads, unavailable prerequisites, log bounds, failed setup/cleanup/metadata operations and failed-positive refusal. Failed shader evidence distinguishes unperformed, attempted but unverified and observed compilation; unknown exit status is never invented as success. Governance and final report/staged whitespace checks pass before the bundled commit.

Accepted LLVM receipt: `d9b4e44415764454dcdace445c88de6b7282a3cbe6bc5ff509dd8b44c623b887`. Accepted native shader receipt: `783d7e5d689c32b24a657acd44c14057d92782119682508adbaa1a46e50f78de`. Exact native bytes and selected source/tool/capability receipt digests are in the observations export.

Earlier attempts remain preserved. LLVM1 stopped on a transient compiler-output disappearance; the monitor now distinguishes that race from an actual special-file refusal. LLVM2 completed compiler commands but its final inspector refused the legitimate upstream TableGen utility. LLVM3/4 passed their then-current LLVM-only gates; later evidence/inspection changes made those producer-bound records historical. The final LLVM5 and shader build use the unchanged final producers and fresh roots. No historical failure or earlier success was rewritten or promoted to substitute for the final gate.

Compiler logs retain LLVM warnings about deprecated declarations, function-pointer casts, nontrivial memory calls, final-class virtual declarations and unused command-line arguments. Native airconv emitted return-path and potentially uninitialized-value warnings in unchanged upstream code. Build success does not resolve those possible execution defects; no warning-driven source patch or runtime claim is included in Stage 2.

## Residual Risks

- The airconv application has not been executed. Shader semantic equivalence, warning-related execution behavior, GPU correctness and native renderer behavior remain unverified.
- Full DXMT Windows DLL/native bridge construction, ARM64EC/builtin/import compatibility and the typed Wine driver interface remain later gates. Static native archive inspection and this airconv link do not qualify the future Wine/DXMT pair.
- FEX/CHPE/loader/JIT integration remains with #5/#6. No translated D3D, Steam, Megabonk, performance, thermal or ordinary-user distribution result follows from these compilation checks. Broader macOS/hardware support and final reconstruction remain unperformed.
- Selected component terms and contributor-policy observations do not establish Pear release/license clearance or permission for an upstream contribution. Existing macOS protections remain required.

## Impact on Next Stage

Stage 3 inherits these verified native prerequisites and constructs the planned ARM64EC/native artifact set with an explicitly verified combined Wine-role layout. It must separately inspect compiler output and Wine builtin postprocessing, raw PE/CHPE/dynamic relocation facts, native slices/dependencies, permissions, notices and exact bytes. Missing typed driver pairing remains Stage 4 work; do not normalize headers or infer it from a successful link. Root continues to serialize shared/native operations and preserve original inputs and failed attempts.

## Approval Request

Review Stage 2 and approve continuation to Stage 3 artifact construction only. GPU, PE/guest/game execution, final task/PR publication and ordinary-user distribution are not requested here. #5 separately awaits continuation to its concrete executable-memory design review; that owner prototype still requires approval of the completed design.
