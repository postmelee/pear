# Task #7 Implementation Plan — ARM64EC DXMT and Native Metal Build Pairing

Task plan: [`task_m1_7.md`](task_m1_7.md)
GitHub Issue: [#7](https://github.com/postmelee/pear/issues/7)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta
Prepared October 2, 2026. The requester approved the task plan. The requester approved this implementation plan and Stage 1 on October 2, 2026. Stages 1–3 are implemented; actual results are in their stage reports. The requester explicitly approved Stage 4 on October 3, 2026; its typed-driver implementation and finite native verification are complete and recorded in the Stage 4 report. The requester explicitly approved Stage 5 continuation on October 3, 2026; reconstruction and its required verification remain in progress.

## Applicable Context and Reuse

Follow the approved task plan's architecture, delivery plan, runtime contracts, source qualification, graphics research, root/runtime/tests/host/docs rules and Hyper-Waterfall procedures. Preserve #1's original aggregate `blocked` snapshot and #4's dated final report, 23-patch series and private evidence. Keep upstream C/C++/Objective-C and Meson; bounded Python source/build/evidence helpers may reuse existing Pear readers after their actual contracts are reviewed. No Rust rewrite or upstream submission is planned.

Initial DXMT commit `7c8dee1c2d73415301ceb7d1fa810861cef4cd67`, DirectX headers `9df86f2341616ef1888ae59919feaa6d4fad693d`, native LLVM 15.0.7 `8dfdcc7b7bf66834a761bd8de445840ef68e4d1a`, conditional NVAPI `d08488fcc82eef313b0464db37d2955709691e94`, and Wine base `4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf` plus #4's immutable series are inherited candidates. Bind the #4 23-patch series SHA-256 `39371f21f25cf153437fd523951be9f938cc1161bed5c4ef923583c74c89d086` and final prepared source-manifest SHA-256 `2c0c861669f9fd8853f8899eaeb08b18207b0cf26b34dae9efe707919e447bc7` separately to their actual scopes and verified local receipts. The LLVM-MinGW 20260908 artifact is identified by existing SHA-256 `d1dc5d1ecf3a3ced5ed5544c72f1acd0c8e84eb3024d520ecc6b143eec62a149`; its current unpacked ARM64 tools and companion import libraries still need revalidation. Distinguish native LLVM 15 shader libraries from LLVM-MinGW's LLVM 23.1.1 compiler.

For actual approved Metal/lifetime verification later, use Pear's Apple-tooling router at pinned Apple source `4f42344c90be22112f46becc3fb9687f423f2f88`, plugin reference `1.0.0-beta.1`. Stage 1 does not require a GPU expert. Select `using-metal-validation` only when Stage 4's concrete native Metal checks need it. `managing-metal-cpp-lifetimes` is conditional on actual metal-cpp use; DXMT's Objective-C bridge alone does not trigger that expert. Read the selected source and actual SDK/header contract before commands. Do not install a plugin or start Apple's porting lifecycle.

## Stage Overview

| Stage | Title | Main Output | Verification |
|---|---|---|---|
| 1 | Input, tool and layout closure | `runtime/dxmt/{inputs,toolchain,build-config}.json`, isolated source/layout record | Exact selected identities, all configured gitlinks/terms, bounded tool availability and candidate Wine role inspection; shader readiness may remain unavailable |
| 2 | Native shader prerequisites | Native ARM64 LLVM 15/airconv and generated shader inputs | Actual local tool capabilities, native library/header identity, slices/dependencies/notices and real metal/metallib compilation |
| 3 | ARM64EC/native artifact construction | DXMT required DLLs, paired native winemetal and complete artifact inventory | PE/hybrid headers, Mach-O slices, Wine import/tool/native dependency pairing, modes/search paths/hashes |
| 4 | Typed driver pairing | Graphics-only Wine/DXMT adapter patches and finite native boundary records | Version/error/type/ownership contracts and actual native artifact/lifecycle checks; hybrid execution remains gated on #5/#6 |
| 5 | Fresh reconstruction and handoff | Independently checked fresh final component and contributor guide | Empty-output rebuild, strictly explained unsigned comparison, source/notice/output closure and bounded #8 handoff |

Stage 1 closure means the inventory and layout have been fully accounted for, not that all build tools exist or that Stage 2 is runnable. Missing `metallib` is a required **unavailable shader-build prerequisite**: it does not turn a correctly verified source inventory into failure or an invented ready toolchain.

## Document Location Check

| File | Planned Location in Task Plan | Stage Artifact Path | Match | Notes |
|---|---|---|---|---|
| Exact contributor guide | `docs/development/dxmt-build.md` | Same, Stage 5 | OK | Source/tool/pairing instructions and observed limitations |
| Guide index | `docs/README.md` | Same, Stage 5 | OK | Narrow guide link only |
| Dated graphics follow-up | `docs/research/graphics-and-game-integration.md` | Same, Stage 5 | OK | Append verified component observations; preserve historical research |
| Driver handoff cross-reference | `docs/development/wine-host.md` | Same, Stage 5 | OK | Link actual typed bridge; preserve dated private-layout finding |
| Plans/reports/boards | Approved `mydocs/` paths | `mydocs/plans/task_m1_7_impl.md`, `mydocs/working/task_m1_7_stage{N}.md`, observation sidecars and active-date board | OK | Workflow history rather than product instructions |

No official documentation is edited in Stage 1. Component records, scoped implementation rules and tool interfaces are implementation artifacts in the task plan's approved runtime/tool/test areas. New product/API document locations or changed ownership require review before changes.

## Shared Evidence and Execution Contract

All component records use integer schema versions and a local `scope: dxmt_component`; they do not add a product-record kind to `runtime/contracts/`. Use canonical bounded JSON and exact stored-byte digests; commit/tree IDs, tree listings, archives, ordered patches, output files and signed observations retain distinct scopes. Preserve unknown/unavailable/unsupported/failed/unperformed observations. A producer boolean or exit zero alone is not a pass.

Each private operation receipt records the producer/config/input digests, actual structured argument list, selected environment keys, command status, monotonic timing, bounded stdout/stderr references, output inventory and omissions. Public sidecars are allowlisted derivatives with distinct digests. No private paths, profiles/signing identity, credentials, whole environments, prefixes, saves or proprietary payloads are published. Source and runtime eligibility are separate gates.

Planned CLI status contract: 0 means the specifically requested gate passed; 1 means bounded operational/input failure; 2 means CLI usage error; 3 means valid evidence cannot meet the requested readiness/compatibility gate. A complete inventory containing a required unavailable shader tool passes `--require-accounted` but returns 3 for `--require-shader-build-ready`. Never collapse these outcomes.

Reuse read-only original source caches. Materialize only into new owned `.build/task7/` directories and refuse existing destinations, symlink escapes, traversal, duplicate paths, unsupported entries, unexpected gitlinks or changed digests. Acquire a missing selected public source only after Stage 1 approval, with exact commit/HTTPS origin and no recursive checkout, source execution or moving-ref substitution. Keep any new acquisition separate from the original audit cache. Failed outputs remain; retry into a newly reviewed layout.

Candidate Wine roles explicitly identify #4 source/patch/configuration, native host `winebuild`, ARM64EC companion PE import libraries and native `ntdll.so`/`winemac.so`. Directory names and `aarch64-windows` labels are insufficient: inspect headers/import identities and record why each role matches. Retained outputs may be inspected as build input candidates; current signatures/authorization do not carry over automatically to a changed library/executable.

Reuse helpers only at their actual supported scope. `tools/wine/prepare.py` validates a single Wine component, rejects Gitlinks in its materialization path, and binds outputs/replay to `.build/task4/`; `tools/wine/toolchain.py` also pins download/output/alias ownership to task4 and Wine-specific records. They are not generic #7 entrypoints. Reuse reviewed bounded low-level algorithms or implement a DXMT-scoped wrapper with real ownership/schema tests; do not relabel records, create task4 outputs from #7, or relax historical validation to make reuse work. `tools/wine/modules.py:inspect_pe` requires raw COFF machine `0xaa64`; its observed ARM64X fixups describe a distinct effective alternate view. Extend inspection deliberately for actual ARM64EC/ARM64X variants while retaining raw bytes, outer COFF machine and hybrid metadata separately. Never edit headers or substitute a native-view value merely to pass an inspector.

Root serializes shared Wine helper/contract/index/board edits, signing, large builds, native runs and storage maintenance. #5 owns FEX and translator-specific Wine loader/CHPE/memory/x18/exception changes. #7 owns graphics bridge/Mac-driver patches and its own input/tool/fixture records. Keep a separate graphics supplemental patch layer with immutable base/series and explicitly consumed #5 layer identities; do not edit the historical #4 patch bytes or #1 manifest. Parallel read-only source review and independent portable fixture work are allowed; live native runs and large builders on this Mac do not compete.

## Stage 1 - Input, Tool and Layout Closure

### Artifacts

New:

- `runtime/dxmt/AGENTS.md`: implemented component rules, source/build/runtime distinctions and graphics-versus-CPU ownership.
- `runtime/dxmt/inputs.json`: initial exact source/tree/listing/gitlink pins, source provenance, original audit reference, Wine layer identities and terms paths.
- `runtime/dxmt/toolchain.json`: locked reusable #4 cross-tool candidate plus explicit local tool/SDK/Metal candidates, unresolved digest reasons and roles.
- `runtime/dxmt/build-config.json`: candidate release/debug mode, builtin DLL selection, ARM64EC/ARM64X guest/native ARM64 targets, explicit disabled NVAPI/NVNGX/D3D12/Windows-airconv/tests, bounded jobs and owned layout.
- `tools/dxmt/{common,prepare,check,verify}.py`: bounded input/materialization/availability/layout readers; no full-build or GPU entrypoint in Stage 1.
- `tests/dxmt/test_stage1_inputs.py`, `test_stage1_layout.py`, `test_stage1_evidence.py`, `test_stage1_probes.py`, `test_stage1_ec_archive.py` and `support.py`: original meaningful rejection and source-role tests.
- `mydocs/working/task_m1_7_stage1.md` and `task_m1_7_stage1_observations.json`.

Modified: this implementation plan only for concrete selected pin/command clarifications within the approved scope, and active-date board through root. No docs, #4 patch series or original source manifest edits.

### Changes

1. Recheck exact Git commits/trees/listing digests and selected source files/submodule gitlinks. Record required DirectX header materialization; NVAPI remains disabled with its explicit condition. Reconcile selected source licenses and notices, including embedded DXBCParser terms and the difference from MIT-through-v0.80 DXMT.
2. Materialize DXMT and required headers into a fresh owned source root. Inventory LLVM source identity/size without unbounded whole-tree expansion; full LLVM derivation for building may occur Stage 2. Explicit gitlink mapping replaces uncontrolled `git submodule update --recursive`.
3. Inspect the retained #4 tool and Wine artifacts read-only; bind exact actual ARM64 host tool slices, selected companion import library variants and native dependency paths to source/build receipts. Inspect the source export/layout mismatch and future adapter requirement; do not author that adapter in this stage.
4. Record bounded `--version`/tool-resolution probes for existing native build tools, SDK/toolchain and cross compilers. These are developer-tool metadata probes, not execution of a Windows/Metal fixture. No DXMT, LLVM or shader compilation, no guest execution and no signing/native GPU fixture in Stage 1.
5. Candidate local tools are **proposed targets**, not available/downloaded/usable artifacts: [CMake 3.31.8 universal macOS tar](https://github.com/Kitware/CMake/releases/download/v3.31.8/cmake-3.31.8-macos-universal.tar.gz), proposed artifact SHA-256 `d1449f969c54d5c00886d5b643340d493dfb3c81cb39ee29b35453395c11ebf7`; its [publisher checksum text](https://github.com/Kitware/CMake/releases/download/v3.31.8/cmake-3.31.8-SHA-256.txt), proposed text SHA-256 `8d08ce0586bf40ff6b80e46fffe2db8855bab5b030db8b3782f11f68b6274ad8`; [Ninja 1.13.1 source](https://github.com/ninja-build/ninja/tree/79feac0f3e3bc9da9effc586cd5fea41e7550051), commit `79feac0f3e3bc9da9effc586cd5fea41e7550051`; and [Meson 1.10.0 source](https://github.com/mesonbuild/meson/tree/415917b7c0d4759f73d0fe6564cbdda7fbf1eb9a), commit `415917b7c0d4759f73d0fe6564cbdda7fbf1eb9a`. These supplied primary-origin metadata values await actual acquired-byte/checksum text/object cross-check; this draft does not claim those bytes were read, downloaded or authenticated. Stage 1 may read primary metadata, acquire missing exact selected public source commits after approval, and record platform/tree/listing/archive candidate identities. Build-tool installation/bootstrap remains Stage 2. A source commit does not establish a built tool's archive SHA, native slice or usability. Metal Toolchain version/platform/origin is unresolved; do not infer its usable compiler from the Xcode version.
6. Check current free disk/memory and measured source/cache expansion sizes. Record a prospective Stage 2 budget with its evidence, retention and concurrent disk-growth limits. No guessed DXMT/LLVM budget and no automatic deletion. Do not inherit #4's 26 GiB requirement.
7. Export only a bounded source/tool/layout summary. `inventory_complete` is independent of `shader_build_ready`, `dxmt_built`, `pairing_verified` and `runtime_eligible`; all latter states remain false/unknown until their actual gates pass.

### Verification

Inputs: approved component candidates and actual retained original source cache/#4 receipt locations. Tools: installed Python 3, Git, bounded file/header readers, existing Xcode inspection tools; exact Python/Git identities recorded. Planning observed CMake/Meson/Ninja absent from PATH, `metal` resolvable and `metallib` lookup exit 72. Present cache files were not reverified during planning.

Implemented Stage 1 CLI; the final accepted outputs below follow preserved earlier attempts:

```sh
python3 tools/dxmt/prepare.py --inputs runtime/dxmt/inputs.json --source-cache <original-read-only-cache> --output .build/task7/stage1-inputs5 --require-empty
python3 tools/dxmt/check.py inventory --inputs runtime/dxmt/inputs.json --toolchain runtime/dxmt/toolchain.json --config runtime/dxmt/build-config.json --prepared .build/task7/stage1-inputs5 --wine-native <retained-native-role> --wine-companion <retained-companion-role> --tools <retained-locked-tools> --output .build/task7/stage1-check3 --require-accounted
python3 tools/dxmt/verify.py inventory --root .build/task7/stage1-check3 --require-accounted
python3 tools/dxmt/verify.py inventory --root .build/task7/stage1-check3 --require-shader-build-ready
python3 -B -m unittest discover -s tests/dxmt -p 'test_stage1_*.py'
python3 tools/check_governance.py
git diff --check
```

Placeholders denote validated local private handles recorded by the actual command; never include them in public sidecars. Independent inventory replay rechecks current blobs/gitlinks, tool bytes and derived source/layout against receipts. Tests reject changed/missing Git objects, wrong gitlink mappings, mismatched or mixed Wine roles, unsupported target/format, hash/receipt changes, duplicate/unbounded JSON and unsafe/existing output paths. Meaningful portable tests do not fake a working compiler or renderer.

Expected success: all required source/terms/layout facts are accounted for, actual invalid evidence is rejected, and all affected portable tests/governance/whitespace pass. Missing shader tools are recorded unavailable; the `--require-shader-build-ready` refusal is **expected exit 3** while missing prerequisites persist. It must never be presented as a passed readiness check. Stage 1 may complete with that explicit refusal; Stage 2's shader-build-dependent operations cannot proceed until the missing prerequisites are verified.

Retain private raw receipts, failed/rejected controls, original byte hashes, source/target/dependency/notice matrix and current storage observations. Public report says whether the inventory passed and separately names unavailable tools/unperformed compilation. No #7 Issue criterion is closed by inventory alone.


Implemented closure clarification: nine exact source components and their required selected notice/source-check sets are accounted for. Literal `%` filenames are accepted only by nonmaterialized Git-tree accounting without URL decoding; output/materialized path restrictions remain strict. ARM64EC `/<ECSYMBOLS>/` indices are bounded metadata, with real member references checked before reporting COFF machines. Native and companion import archives are inspected separately; mixed ARM64/ARM64EC companion members are observations, not a link-compatibility assertion.

The inventory performs nine bounded metadata probes, including both SDK path and version. Existing shell wrappers are invoked through explicit ARM64 `/bin/sh`, after binding their real Clang alias/driver chain. The legacy #4 cross-tool manifest has no mode pin: actual regular/executable modes are observed and replay-bound, with the historical baseline explicitly unavailable rather than invented. No missing tool is installed or bootstrapped in this stage; FEX's task-local tools may become separately verified reuse candidates in Stage 2.

### Commit

```text
Task #7 Stage 1: qualify DXMT inputs and native build prerequisites
```

## Stage 2 - Native Shader Prerequisites

### Artifacts

- Finalized exact tool artifact/source SHA identities in `runtime/dxmt/toolchain.json` and explicit native recipes in `build-config.json`.
- `tools/dxmt/tools.py`, `build_native.py`, native prerequisites inspection and independent verifier extensions.
- `tests/dxmt/test_native_build_evidence.py` and original compile-only tool capability fixtures.
- Private `.build/task7/stage2-tools`, LLVM source/objects/install and native shader receipts; Stage 2 report and sanitized observations.

### Changes

Prepare approved build-only CMake/Meson/Ninja inputs into task-local directories with exact archive/wheel/source identities, safe unpacking, native slices and applicable notices. Reuse the already locked cross-tool cache only after current verification. No global pip/Homebrew installation, `--break-system-packages`, persistent PATH or Xcode selection change. An optional Metal Toolchain installation/Apple account/license interaction is outside implicit source-build authorization: first record the exact required action and authorization, or use an already installed verified scoped `DEVELOPER_DIR`/toolchain selector. Keep unavailable observations if no permitted path exists.

Build LLVM 15.0.7 native ARM64 from the source pin using the upstream CI's reviewed CMake baseline: ARM64 host/architecture, Release, assertions on, ZSTD off, empty target list, tools off, Ninja generator. Record Apple compiler/SDK/deployment target and each additional feature choice, system header/library dependency, generated configuration and actual library major. Review rather than copy disabled option assumptions; installed native static LLVM libraries and headers must match. No independent source-build claim for reused LLVM-MinGW binaries.

Materialize and compile the required airconv/DXMT built-in Metal shader prerequisites using exact selected `metal`/`metallib` bytes and actual settings, including upstream airconv Metal 3.1/AIR target where applicable. Inventory the native airconv objects/libraries/tool and generated AIR/metallib headers. Native `airconv` compile success does not prove shader semantic equivalence or GPU correctness. Compiler invocation is allowed after verified tool readiness; it is not a GPU runtime test.

### Verification

Required tools: finalized candidates with actual available ARM64 execution, CMake >=3.27, selected Ninja/Meson 1.10.0, LLVM-MinGW 20260908, Xcode/SDK consistent with the recorded target, and functioning `metal`/`metallib`. Settings: task-owned output, measured sufficient disk/memory, bounded serial jobs, no persistent configuration changes. Source/tools must pass exact identity verification before build commands.

```sh
python3 -B tools/dxmt/prepare.py --inputs runtime/dxmt/inputs.json --source-cache "$pear_dxmt_source_cache" --output "$pear_dxmt_stage2_inputs" --require-empty
python3 -B tools/dxmt/tools.py prepare --toolchain runtime/dxmt/toolchain.json --reuse-root "$pear_dxmt_tool_reuse" --meson-repository "$pear_dxmt_meson_repository" --output "$pear_dxmt_stage2_tools" --require-empty
python3 -B tools/dxmt/build_native.py prepare --inputs runtime/dxmt/inputs.json --prepared "$pear_dxmt_stage2_inputs" --source-cache "$pear_dxmt_source_cache" --output "$pear_dxmt_native_source" --require-empty
python3 -B tools/dxmt/build_native.py llvm --source "$pear_dxmt_native_source" --tools "$pear_dxmt_stage2_tools" --output "$pear_dxmt_llvm" --jobs 2 --max-growth-bytes 17179869184 --reserve-free-bytes 4294967296 --require-empty
python3 -B tools/dxmt/verify.py native --root "$pear_dxmt_llvm" --require-llvm
python3 -B tools/dxmt/check.py shader-tools --toolchain runtime/dxmt/toolchain.json --tools "$pear_dxmt_stage2_tools" --output "$pear_dxmt_shader_capabilities" --require-ready
python3 -B tools/dxmt/verify.py shader-tools --root "$pear_dxmt_shader_capabilities" --require-ready
python3 -B tools/dxmt/build_native.py shaders --llvm "$pear_dxmt_llvm" --prepared "$pear_dxmt_stage2_inputs" --tools "$pear_dxmt_stage2_tools" --capabilities "$pear_dxmt_shader_capabilities" --output "$pear_dxmt_stage2_native" --jobs 2 --max-growth-bytes 8589934592 --reserve-free-bytes 4294967296 --require-empty
python3 -B tools/dxmt/verify.py native --root "$pear_dxmt_stage2_native" --require-complete
python3 -B -m unittest discover -s tests/dxmt -p 'test_*.py'
python3 tools/check_governance.py
git diff --check
```

Implementation clarification: task-specific variables select verified private caches and fresh `.build/task7/` outputs; their private values are not repository artifacts. Split source preparation, LLVM-only and Metal-dependent gates preserve unavailable shader tooling explicitly. The 16 GiB LLVM and 8 GiB shader ceilings with 4 GiB free reserve are operational stop limits, not measured build peaks; admission must be rechecked immediately before each operation. Existing exact candidate/configuration selectors retain their source-inspected state; actual acquisition, tool execution and finalized native options are recorded separately in producer-bound `prepared.json`/`build.json` receipts and explicit `build_native.py` recipes. This prevents a selection lock from being mistaken for an availability or support claim. No approved artifact root, GPU/guest scope or separate Metal-install approval requirement changes.

Expected: actual compile/link capability fixtures, required native LLVM major/library/header closure, ARM64-only host output/dependencies and all required shader-generation steps pass. A Metal shim path or version alone cannot pass. Record compiler warnings, rejected outputs and private command/output hashes. No guest/GPU/renderer execution occurs here.

### Commit

```text
Task #7 Stage 2: build native ARM64 shader prerequisites
```

## Stage 3 - ARM64EC and Native Artifact Construction

### Artifacts

- `tools/dxmt/build.py`, `inspect.py` and build/artifact replay extensions.
- Actual component `build.json`, `artifacts.json`, selected PE/import/export/native dependency records under private `.build/task7/stage3-build`.
- `tests/dxmt/test_artifact_pairing.py`, PE/hybrid/mode/dependency rejection fixtures, Stage 3 report and public observations.

### Changes

Derive a fresh DXMT source tree and required submodules from verified inputs. Build through reviewed Meson ARM64EC cross configuration with `-marm64x`, required builtin/native DLL mode and explicit native ARM64 host flags. Select the exact source-built Wine `winebuild`, ARM64EC import role and native `ntdll`/Mac-driver pair instead of upstream opaque Wine release binaries. The pinned Meson definitions use one Wine install/build root for import libraries, `winebuild` and native dependencies. Realize distinct native/companion roles through an explicitly verified task-owned combined layout or reviewed build adapter, preserving each original source/build/byte identity and refusing mixed incompatible roles; independent CLI labels alone do not solve that layout constraint. Required outputs include `d3d11.dll`, `dxgi.dll`, `d3d10core.dll`, `winemetal.dll`, native `winemetal.so` and configured shader/dependencies; inspect actual built names/variants, not only a static expected list. Keep NVAPI/NVNGX/D3D12/Windows-airconv disabled initially.

Record Wine builtin postprocessing separately from compiler output and installation. Track all host tools versus shipped native/guest components. Inventory raw outer PE COFF machine, ARM64EC/ARM64X alternate-view and CHPE/dynamic relocation metadata, imports/exports, native Mach-O slice/install-name/rpath/system framework and library dependencies, permissions/symlinks, notices, source/patch provenance and full output hashes. Existing Wine inspection's `0xaa64` requirement is a scoped native-view assumption, not permission to fake or normalize DXMT's raw header. A build may expose the known missing driver interface; record it as **built but pairing not verified**, not runtime compatibility.

### Verification

Inputs: completed native prerequisite records, exact Wine role records and the declared DXMT configuration. Tools/settings: Stage 2 verified toolchain, new owned build/install, bounded serial jobs and current storage admission. No PE/hybrid execution or loader-guard expansion in this stage.

```sh
python3 -B tools/dxmt/build.py --inputs runtime/dxmt/inputs.json --config runtime/dxmt/build-config.json --toolchain runtime/dxmt/toolchain.json --native .build/task7/stage2-native-shaders1 --prepared .build/task7/stage2-inputs2 --tools .build/task7/stage2-tools2 --cross-tools "$pear_dxmt_cross_tools" --wine-roles "$pear_dxmt_wine_roles" --output .build/task7/stage3-build --jobs 2 --max-growth-bytes 8589934592 --reserve-free-bytes 4294967296 --require-empty
python3 -B tools/dxmt/inspect.py --root .build/task7/stage3-build --require-complete
python3 -B -m unittest discover -s tests/dxmt -p 'test_*.py'
python3 tools/check_governance.py
git diff --check
```

Implementation clarification: keep every Stage 2 source/tool/native producer byte unchanged. Stage 3 uses new `build.py` and `inspect.py` for construction and independent exact-byte replay; the new inspector command replaces the equivalent planned `verify.py artifacts` dispatch so an additive CLI edit cannot invalidate native prerequisites. Reuse the existing Wine PE class and hybrid reader by fixed AST selection of those two definitions only, binding the full reader source digest; the native-view wrapper is not used to normalize raw headers. The owned Wine layout combines verified native `winebuild`, `ntdll.so`, `winemac.so` and transitive `win32u.so` with companion ARM64/ARM64EC imports. Native/compiler outputs, four explicit in-place builtin-marker operations and installation have separate byte identities. A bounded owned Git adapter returns the full selected DXMT commit for the sole `describe --always` request, preventing discovery of the parent Pear repository. The original DXMT source remains unchanged. Exact generated adapters/configuration, source notices, role origins and commands are replay-bound. The 8 GiB ceiling / 4 GiB reserve are operational limits with fresh admission, not measured peaks. This stays within the approved artifact-construction and internal-plan locations; the typed driver interface, signing and GPU/guest execution remain later gates.

Expected: complete versioned artifacts and dependency/notice inventories, exact native ARM64 slices and valid configured hybrid metadata; unknown/missing/changed outputs fail the relevant gate. Test wrong target/slice/major/role, unaccounted dependency, builtin mode mismatch, bad rpath, changed bytes and omitted outputs. Missing typed interface remains a Stage 4 prerequisite, not something compilation can resolve by assertion. Retain failed builds with exact errors.

### Commit

```text
Task #7 Stage 3: reproduce the paired ARM64EC DXMT artifacts
```

## Stage 4 - Typed Wine Driver Pairing

### Artifacts

- Attributed graphics supplemental patches and input identities under `runtime/dxmt/patches/`; no historical #4 patch mutation.
- A shared source-defined native adapter header within the materialized patch layer, consumed by Wine Mac-driver and DXMT unixlib; original source-bound/native bridge fixtures under `tests/dxmt/`.
- `tools/dxmt/check_pairing.py`, `run_pairing.py`, independent artifact/fixture verification and private owned rebuilt Wine/DXMT pair.
- Stage 4 report, sanitized interface/ownership results and explicit pending hybrid runtime evidence.

### Changes

Define a source-matched native Darwin C ABI boundary, provisionally `pear_macdrv_metal_v1_get_interface`, with explicit requested version, table byte size and feature capabilities. The adapter is Pear-owned downstream integration, not a stable upstream Wine API. The table must expose opaque lease-based acquire/query/release operations and explicit status codes; no copied `macdrv_win_data` or numerical private offset becomes public ABI. Native BOOL/Windows WINBOOL and PE callback conventions remain distinct.

Proposed method contracts for detailed source review before coding:

- Get-interface validates version/size and sets output null before failure; unavailable/wrong-version/missing required method is refused.
- Acquire takes a typed native HWND/device input and produces a zero-initialized opaque lease only on success. Distinguish invalid/destroyed window, absent client surface, unavailable device/view/layer and incompatible interface. No success with an uninitialized output.
- The lease owns exactly documented native references and a generation/validity association. A borrowed Metal layer is usable only while its lease remains valid; consumer retention and invalidation rules are explicit. Returning a pointer after unlocking is not lifetime protection.
- Resize/detach/destroy update validity on Wine's appropriate main-thread/driver path. Source review must define protected retention, lock ordering and reentrant main-thread handoff without holding the driver mutex across a potentially reentrant wait. Merely renaming a private field is rejected.
- Release balances the adapter's owned acquisition; repeated cached-view acquisition cannot blindly add/remove Wine view ownership. Multiple leases on one underlying view and final disposal need an explicit count/epoch policy tied to actual Wine source behavior. Reject stale/double release in owned tests without dereferencing freed tokens.

#### Stage 4 internal design record (approved scope refinement, October 3)

Location/reuse decision: retain this private source integration contract in the existing implementation plan. No product/API document or stable upstream API is created. Scoped attributes in the approved patch/fixture roots preserve unified-diff context and exact upstream notice whitespace; ordinary source and documentation checks remain active. Graphics-only supplemental patches, a canonical shared header and original finite fixtures are new inputs under the already approved `runtime/dxmt/patches/` and `tests/dxmt/pairing/` locations. Preserve all earlier producer bytes and the historical 23-patch Wine series (SHA-256 `39371f21f25cf153437fd523951be9f938cc1161bed5c4ef923583c74c89d086`) and final Wine source manifest (`2c0c861669f9fd8853f8899eaeb08b18207b0cf26b34dae9efe707919e447bc7`). Supplement selected Wine `4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf` and DXMT `7c8dee1c2d73415301ceb7d1fa810861cef4cd67` with exact ordered before/after file identities; no cache mutation.

Concrete native ABI: one default-visible getter, `pear_macdrv_metal_v1_get_interface(uint32_t version, uint32_t table_bytes, uint64_t required_features, const struct pear_macdrv_metal_v1 **out)`. Output is null before validation. Version is 1; table size is 48 bytes on the selected 64-bit Darwin ABI. Header offsets are version 0 (u32), bytes 4 (u32), features 8 (u64); four native C function pointers occupy offsets 16/24/32/40. Required feature bits are lease ownership=1, checked main-thread layer operation=2, source surface generations=4 (supported mask 7; unknown bits refuse). Methods are `acquire(uint64_t hwnd, uint64_t native_device, uint64_t *lease)`, `query(uint64_t lease, struct pear_metal_query_v1 *out)`, `release(uint64_t lease)` and `with_layer(uint64_t lease, void (*operation)(void *context, uint64_t borrowed_layer), void *context)`, all returning signed 32-bit bridge status. Native device/layer values describe actual owned native Objective-C objects; this is a trusted component boundary, not arbitrary guest-pointer validation. No Wine private data layout, Windows BOOL, Objective-C BOOL, PE callback convention or C++ type crosses it.

`pear_metal_query_v1` is 32 bytes: bytes/state u32 at offsets 0/4, source generation u64 at 8, drawable width/height binary64 at 16/24. Query writes a zeroed record before failure, and on success returns bytes=32/state=LIVE(1). Lease tokens are nonzero monotonically allocated identifiers, never native object addresses; no freed token is dereferenced. At most 64 live lease slots are admitted; exhausting the bounded registry returns CAPACITY. Integer wrap refuses allocation. Lifecycle is RESERVED -> LIVE -> INVALID -> RELEASED; partial acquire rolls back without publishing a token. INVALID leases refuse query/layer operations but can be released exactly once; a released/unknown token refuses again. These bounds and layouts are private implementation choices, not general runtime support claims.

Closed bridge statuses: OK=0, ARGUMENT=1, VERSION=2, SIZE=3, FEATURES=4, WINDOW=5, NO_CLIENT=6, DEVICE=7, VIEW=8, LAYER=9, STALE=10, OWNER_CONFLICT=11, CAPACITY=12, NATIVE_EXCEPTION=13. Invalid/null outputs, missing window/client/device and unavailable/mismatched interface remain distinct. The DXMT native resolver selects only the getter, validates the complete required table, and fails with zeroed outputs; no private accessor fallback remains. Existing PE thunk indices and public DXMT exports remain unchanged. Native bridge statuses are mapped to actual Unix-call failure separately; they are not relabeled NTSTATUS values.

Source state and lifetime: `window.c` owns an internal nonreused generation assigned to each window data instance and each changed/presented client surface. Source snapshot helpers obtain/retain the actual client view under `get_win_data` and release the driver mutex before any AppKit operation or wait. Resize preserves the binding and updates actual layer dimensions; replacement, detach and destroy invalidate the old generation before disposing the client view. All attachment/lease registry and Objective-C mutation runs on the Wine main thread. Execute directly if already on main; otherwise use Wine `OnMainThread` with no driver/registry lock held. Its wait pumps QUERY_EVENT callbacks (`cocoa_event.m:529-581`), and its unconditional queuing makes a main-thread self-wait unsafe. Validate the source identity/generation again before publishing acquire and before each layer callback. Driver lifecycle invalidation performs no synchronous main-thread wait under `win_data_mutex`.

One bridge-owned attachment uses the actual WineMetalView/CAMetalLayer implementation, with a source-owned interlock on WineContentView. Refuse a preexisting legacy Wine Metal cache; legacy creation refuses while the bridge owns that cache. Do not silently share/remap an existing legacy view or create a shadow view. The attachment owns its original view creation and client/device references. Each published lease owns additional view/layer references; multiple leases share the attachment. Final adapter release removes the bridge-owned view and balances its attachment reference exactly once. Other releases balance only their own references. Invalidation keeps referenced native memory alive until leases release while refusing new operations. A transient layer reference protects a callback. The callback may use only the supplied native layer and owned request data; it must not reenter Wine, dispatch a main-thread wait, retain a borrowed layer for later use or release attachment ownership. It executes only after validity checking; source AppKit detach is serialized after the operation. Objective-C exceptions become NATIVE_EXCEPTION. This closes physical lifetime and the finite selected operation schedule; arbitrary native misuse is not a sandbox guarantee.

DXMT integration: return a retainable original native Objective-C lease proxy as both the view handle (owned) and its layer handle (borrowed). The proxy owns one driver lease; deallocation releases it once. Existing generic NSObject retain/release therefore remains meaningful. Route every actual layer consumer through `with_layer`: `nextDrawable`, `setProps`, `getProps`, `setColorSpace`, `getEDRValue` and `_WMTQueryDisplaySettingForLayer` (`winemetal_unix.c:1603,1624,1641,2266,2406,2484`). Initialize output handles/structures on all errors; nullable drawable and unsupported color space remain actual observations. Do not cast a lease token/proxy directly to CAMetalLayer. Retain upstream C/C++/Objective-C and exact native WMT property conversions. General renderer recovery from the existing swapchain constructor abort is outside this finite native bridge qualification.

Finite actual fixture: an original ordinary ARM64 PE entry creates/owns a Win32 window and calls `PearMetalPairingControl` through an appended actual Mac-driver Unix-call entry. An original Objective-C native fixture consumes the typed getter, creates/presents/detaches an actual `macdrv_CreateClientSurface` and uses its real Wine lifecycle. Plain HWND/no-client must first refuse. Cases cover getter version/size/features/null output, valid acquire/query/layer callback, null device, unknown/stale token, multiple acquisitions and distinct release, foreign legacy cache exclusion, resize, surface replacement/detach, destroyed HWND, final no-live-lease/attachment cleanup and native/main-thread/x18 evidence. Exercise an owned Objective-C exception and a refused nested query without changing lease counts. The native fixture loads only the verified rebuilt winemetal.so and calls its existing source-matched `__wine_unix_call_funcs` entries 67/70/71/72/73/93/97/101 through copied unchanged pinned DXMT thunk headers; no new DXMT export or private Wine field copy is needed. Keep finite control prerequisites/nonce/thread ownership, process deadlines/bounded logs, owned prefix/process group and cleanup; no keyboard/mouse injection. JSON rows have record_kind `pear_metal_pairing`, version=1, sequential case/cycle, actual and expected bridge statuses, scalar state/count/main-thread/x18 observations. Raw addresses/diagnostics remain private. Source-fixture-only associated lifetime witnesses attach to actual WineMetalView, CAMetalLayer and DXMT proxy objects with private fixed keys. Observe the public CAMetalLayer.delegate only; require its runtime class to be the actual source WineMetalView, record missing/wrong delegate explicitly and never mutate it. Witnesses own scalar kind only, hold no owner reference/cycle and update atomic creation/destruction counters. Mark all three bridge-created attachments and the selected proxy; after caller autorelease-pool drain, a finite main/event/CA transaction drain (32 iterations, two-second observed bound plus process deadline) must observe exact created/deallocated equality. Unknown physical lifetime blocks acceptance even when registry counts are zero. Explicit native dlclose and post-pool lifetime rows and a terminal PE row preserve primary step/error/control status separately from cleanup failures. Ordinary ARM64 PE execution is reported as performed when actually run; translated/hybrid guest dispatch remains unperformed and is never hidden behind a generic PE-execution=false claim.

Metal route: source-bound Wine device creation and the actual fixture process receive API validation variables before MTLDevice creation. Read the pinned Apple `using-metal-validation` guide; record `MTL_DEBUG_LAYER`, shader-validation settings and actual SDK/tool/host identities. The selected SDK CAMetalLayer header documents nullable nextDrawable and a default one-second timeout; keep `allowsNextDrawableTimeout=YES`, never force an infinite wait, and record an unavailable drawable rather than fabricate success. These are finite correctness diagnostics, not performance evidence. Root alone builds/signs/runs. Check current per-executable provisioning/signature admission before restricted Wine/x18 work; no inherited #4 permission assertion, new privilege bypass, Metal capture or installation follows from this design. Any native-only fixture limitation or missing actual paired symbol/lifecycle acceptance blocks Stage 4 completion.

Review exact Wine/Metal method semantics and finalize this state machine in the Stage 4 design record before implementation. If it needs a different exported ABI, new product/API document, shared CPU gateway changes or scope conflict, obtain a concrete amendment first. Keep Wine callback/x18 machinery and existing loader refusal rules.

Build and inspect the graphics-patched actual pair, verify exported symbol/table layout and DXMT's selected resolver. Execute approved native/ordinary ARM64 fixtures for valid/missing/no-view/null/error, multiple acquisitions and balanced release, resize/detach/destroy interleavings, native callbacks and owned cleanup. Source mocks alone cannot qualify actual interface pairing. Native Metal validation is a correctness operation only, using the relevant pinned guide after tool/platform/SDK verification. No capture required, no performance claim.

Hybrid ARM64X/ARM64EC Windows renderer execution is **dependent on #5/#6**. #4 still refuses non-ARM64/CHPE publication. Do not bypass or enlarge that gate in #7; if the actual ownership/pairing requirement cannot be completed with the approved native/ordinary ARM64 fixture route, preserve the blocked acceptance and wait for the properly reviewed translated path. No full D3D sample suite in #7.

### Verification

Required inputs: actual graphics-patched source/build pair and native fixture revisions, exact development signature/grant for each executable needing restricted operation, active tested graphical session and recorded Metal capabilities. Existing #4 permission/snapshot evidence is not inherited. Settings: isolated prefix/owned processes, deadlines/bounded logs/sentinels, serial native run, no game or keyboard/mouse injection; validation on for targeted correctness and explicitly recorded.

```sh
python3 -B tools/dxmt/pairing_check.py --artifact <new-verified-pair-record> --require-native-abi
python3 -B tools/dxmt/pairing_runtime.py --artifact <new-verified-pair-record> --profile <private-current-development-profile> --output <fresh-owned-runtime-output> --require-empty
python3 -B tools/dxmt/run_pairing.py --runtime <verified-signed-runtime-output> --output <fresh-owned-pairing-output> --require-empty
# Root explicitly reviews every captured diagnostic line into a separate immutable private assessment.
python3 -B tools/dxmt/pairing_evidence.py --run <verified-owned-pairing-output> --require-complete
python3 -B -m unittest discover -s tests/dxmt -p 'test_*.py'
python3 -B -m unittest discover -s tests/wine -p 'test_*.py'
python3 tools/check_governance.py
git diff --check
```

Expected: actual version/signature/exports and paired source-to-binary identities match; native fixture outcomes, observed layer/view lifetime transitions and cleanup agree with independently read records. Explicit finite race schedule coverage and observation gaps stay visible. Changed shared Wine behavior requires meaningful affected regressions; retain native and portable results separately. Any missing required actual adapter behavior prevents Stage 4 completion. General rendering, arbitrary thread/callback timing, hybrid execution and game support remain unqualified.

### Commit

```text
Task #7 Stage 4: verify the typed Wine Metal bridge pairing
```

## Stage 5 - Fresh Reconstruction and Integration Handoff

### Artifacts

- `tools/dxmt/reproduce.py`, strict comparator and independent complete-reconstruction verifier.
- Final component inputs/tool/config/patch/notices and private empty-output rebuild/comparison records; Stage 5 report/public observations.
- `docs/development/dxmt-build.md`; narrow approved index/research/Wine-handoff changes.
- Final task report only through the separate authorized final-report procedure after all stages complete.

### Changes

Rebuild the final required graphics component from exact pinned source/ordered layers in a new owned output; reuse compiler/native LLVM caches only under explicit current-byte verification and report that reuse. A fresh DXMT build is not an independently rebuilt compiler/LLVM or second-machine result. Rebuild the affected Wine component if changed pairing patches require it; root coordinates its exact shared layer with #5 and serial admission.

Compare complete unsigned installs with exact files/modes/symlinks and all raw hashes. Explain only source/format-bound metadata/path differences proven by independent checks; arbitrary code/shader/data changes remain failures. Signed bytes form separate identities; do not promise deterministic development signatures. Reexecute affected same-artifact native pairing where inputs changed and bind all reports to the final candidate. No blind reexecution solely for export.

Document the exact contributor procedure, SDK/tools/permissions, built host/guest identities, enabled/disabled dependencies, correct DLL mode/layout, known failures and finite native adapter coverage. Link #8's required actual D3D qualification and #5/#6's hybrid execution. Append dated evidence without rewriting #1/#4 history or implying end-user distribution.

### Verification

```sh
python3 tools/dxmt/reproduce.py --inputs runtime/dxmt/inputs.json --toolchain runtime/dxmt/toolchain.json --config runtime/dxmt/build-config.json --source-cache <read-only-selected-cache> --tools <verified-local-tools> --native <verified-native-prerequisite-record> --wine-roles <verified-final-Wine-layer-record> --output .build/task7/final-reproduction --require-empty
python3 tools/dxmt/verify.py reproduction --root .build/task7/final-reproduction --require-complete
python3 -B -m unittest discover -s tests/dxmt -p 'test_*.py'
python3 tools/check_governance.py
git diff --check
```

Inputs/tools/settings: actual final records and layers, exact current tool/native dependency bytes, measured storage/job budget, independently readable private receipts. Expected: complete artifact/notice/source closure, no unexplained comparison differences and all required native-scope pairing evidence on final bytes. Documentation links and approved locations pass. Missing #5/#6-dependent required behavior stays blocked; do not mark #7 complete if its actual paired-interface criterion remains unverified. Full translated D3D/Steam/game/distribution are expressly not this gate.

### Commit

```text
Task #7 Stage 5: reconstruct DXMT and document the verified pairing
```

## Verification

Run the applicable stage commands before its report. Portable tests, source inspection, compiler output, native execution, GPU diagnostics and game qualification are distinct evidence. Actual unexpected verification failure leaves that stage incomplete. A deliberate negative gate or an accounted unavailable prerequisite is successful only for the expressly declared inventory/refusal contract, never a positive build/runtime claim.

Finalize actual CLI spelling/local layouts with current implemented readers before execution and record commands; substantial scope/ABI/document-location changes need requester approval first. Keep the worktree clean after each stage commit, preserve failed artifacts, and use the shared stage-report skill before continuation. No Issue closure/PR/merge/ordinary-user release follows from plan approval alone.

## Commits

Each stage commit includes its artifacts, tests/evidence and `mydocs/working/task_m1_7_stage{N}.md`, plus narrow root-owned board updates. Messages follow `Task #7 Stage {N}: summary`. Retain all stage commits and historical patch identities; the final report/publication procedure is a separate checkpoint.

## Stage Dependencies

- Stage 1 starts only after explicit approval of this implementation plan and Stage 1 scope.
- Stage 2 requires Stage 1 completion/report/commit and explicit continuation. Actual native shader build additionally requires usable verified Metal/compiler/build tools; an unavailable inventory row does not authorize a failed build or global installation.
- Stage 3 requires Stage 2 build prerequisites and explicit continuation; no actual hybrid runtime dependency is claimed by compile-only work.
- Stage 4 requires Stage 3 pair construction and explicit continuation. Runtime work beyond approved native/ordinary ARM64 scope requires properly completed #5/#6 evidence and any necessary amendment.
- Stage 5 requires the final source-matched native pairing and explicit continuation. All essential #7 criteria must pass before its final report/publication checkpoint.

## Risks and Responses

- **Missing Metal/build tools:** complete source accounting independently; refuse shader readiness until a permitted exact usable toolchain exists. Local setup only; no silent global/system changes.
- **Private ABI and lifetime:** use an opaque versioned source-defined adapter, actual mutex/main-thread/reentrancy review and final artifact tests; numerical private offsets are historical evidence only.
- **Wine role mixing/hybrid guard:** bind import/native/build tools separately, inspect actual formats and keep loader/translation changes with #5; compilation cannot bypass CHPE refusal.
- **Concurrent shared changes/resources:** root serializes common files, builders/signing/native operations; immutable layers and isolated outputs prevent source/cache/prefix collisions.
- **Unknown storage or nondeterminism:** measure actual source/build requirements before large work; preserve failures and raw differences; no arbitrary code normalization or unrelated deletion.
- **Terms/policy:** preserve selected LGPL/LLVM/MinGW/DirectX/DXBCParser/conditional notices and corresponding modified source/build material. No AI-authored upstream contribution or legal/release clearance is claimed.

## Approval Request

Approve the five-stage implementation split, artifact/CLI/evidence contracts, separate inventory-versus-toolchain gates, document-location matches, typed adapter direction and commit messages. Authorize Stage 1 input/tool/layout closure only. Later stages require explicit continuation after their predecessor's report/commit, and actual shader/native runtime prerequisites must pass before their dependent operations.

## Approval Record

On October 2, 2026, the requester explicitly continued in the same thread with “Proceed.” (translated from Korean) after the joint detailed-plan review request. This approves the implementation plan and Stage 1 only. Stage 2 and later transitions retain their separate report, commit and explicit-continuation checkpoints.

On October 2, 2026, the requester explicitly continued in the same thread with “Proceed.” (translated from Korean) after both completed Stage 1 reports and bundled commits. This authorizes Stage 2 within its approved scope. Later stages, the concrete FEX executable-memory design and any additional Metal installation/account interaction retain their separate approval checkpoints.

On October 2, 2026, the requester explicitly approved the reviewed official Metal Toolchain 17F109 download and installation action. The exact Apple command and bounded private installation receipt are retained under the task-owned output. This authorizes that component setup and the already approved Stage 2 compiler qualification; no account/license acceptance, Xcode selection or security-setting change is included.

After reviewing both completed Stage 2 reports and bundled commits, the requester explicitly continued in the same thread. This authorizes Stage 3 artifact construction for #7 and the concrete executable-memory design review for #5. The #5 owner prototype still requires explicit approval of that completed design; later stages retain their own checkpoints.

On October 3, 2026, the requester explicitly approved the completed Task #5 concrete single-address memory-owner design and continuation to Task #7 Stage 4 in the same thread. This authorizes Task #5 Stage 3 implementation/prototype within its reviewed capacity, ABI, synchronization, permission and finite verification scope, and Task #7 typed-driver implementation/native verification within its approved plan. Later stages, guest/game execution, new security or shared-scope changes and PR publication retain their separate gates.


On October 3, 2026, the requester explicitly continued in the same thread,
approving Stage 5 within the completed Stage 4 handoff and approved reconstruction
and documentation scope. The requester also authorized incremental GitHub
preservation of important results and pruning unnecessary repeated local outputs.
Completed Stages 1–4 are preserved on `codex/publish-task7`. Keep unique source,
producer, command, failure and inventory records before removing redundant
generated payloads, and retain current dependency donors. A pruned historical
payload is unavailable for complete replay; retained receipts do not substitute
for its bytes. Upload only reviewed source and sanitized observations, never
private diagnostic/signing/profile/prefix/game/account data. This supersedes
blanket retention of redundant generated payloads. Root serializes shared Wine,
heavy builds, native execution, cleanup and publication with fresh disk admission.
Stage 5 completion/final publication still require actual verification; no merge,
Issue closure or ordinary-user release is authorized by this continuation.


### Stage 5 Finalized CLI and Verification Boundaries

Finalize the approved routine CLI against the existing paired builder and
independent checker. New `tools/dxmt/reproduce.py` and `compare.py` reconstruct
the complete conceptual unsigned Wine payload, DXMT install and selected
compiler/built/generated/shader outputs. Reuse the unchanged
`pairing_build.construct`, `pairing_check.verify_build` and native-evidence
reader. Keep `tools/dxmt/verify.py` and every historical producer unchanged,
since those bytes are part of accepted prerequisite identities.

```sh
python3 -B tools/dxmt/reproduce.py --artifact .build/task7/stage3-build --reference .build/task7/stage4-build6 --output .build/task7/stage5-reconstruction1 --max-growth-bytes 4294967296 --reserve-free-bytes 4294967296 --require-empty
python3 -B tools/dxmt/reproduce.py --complete --native-evidence <matching-reference-or-final-candidate-run> --output .build/task7/stage5-reconstruction1 --require-complete
python3 -B tools/dxmt/reproduce.py --verify --output .build/task7/stage5-reconstruction1 --require-complete
```

The owned candidate is the sibling `stage5-reconstruction1-candidate`, respecting
the existing immediate-child output policy. Construction creates immutable
`construction.json` only after actual fresh source/compiler reconstruction and
strict raw comparison; this is not completion. Explicit finalization then binds
matching actual finite native evidence and creates `reproduction.json` once.
The existing Stage4 evidence may be reused only when complete unsigned payloads
and all selected source/settings match exactly; this does not transfer signing
permission. Changed or unexplained bytes refuse and retain both inventories.
No metadata allowance is preselected. A new same-candidate native run, when
needed, requires its own current admission and reviewed diagnostics.

The source-only private coordinator/comparator checkpoint passed59 portable
controls; native gates were explicit doubles and fixtures were ordinary plain
bytes. Root changed only proposal comments and portable test discovery/temp-root
selection before repository integration. Actual fresh construction/comparison
and final native binding remain unperformed at this checkpoint. Existing Stage4
source/receipt identities and all runtime/game/distribution exclusions remain.


The repository-integrated Stage5 tools passed59 targeted portable controls and
all343 graphics portable regression controls. The actual standalone `--help`
entrypoint passed. Governance checked22 documents/172 local targets and the diff
check passed. These are Python/source/refusal checks, with explicit native-gate
doubles; fresh component construction and native binding remain unperformed.
The retained final Stage4 build independently replayed under the unchanged
original checker before selective duplicate-source pruning.


### October 3 Reviewed Duplicate Source Pruning

After independent replay of retained Stage4 build6, a private file-by-file ledger
was independently rechecked for both original and retained donor hashes, sizes,
types and modes. The cleanup removed98,254 regular files (2,595,732,533 logical
bytes) identical to protected donors across17 obsolete source roots: old input
snapshots, native source reconstructions and Stage4 build1–5 Wine/DXMT sources.
All unmatched unique files, symlinks, receipts, commands, raw failures and
producer records remain; current Stage3/4/5 and shared dependency donors were
excluded. Observed volume free space increased2,876,813,312 bytes (about2.68GiB);
APFS physical allocation/sharing and unrelated activity make this a volume
observation, not an exact payload physical-reclaim measurement. Cleanup receipt
SHA-256:
`41d21ab7e2ecca705ea2dd85070a11780430b44fe35463d8033d3127ef28d4c1`.
The complete pruned historical source trees are unavailable for replay until
exact donor-based rehydration. Inventory receipts do not substitute for bytes.
The current fresh Stage5 reconstruction remains independent; no raw-difference
normalization, game execution or distribution qualification is inferred.


### October 3 Actual Fresh Reconstruction Refusal

The fresh Stage5 candidate completed all10 actual source/configuration/compiler/
postprocessing/install commands with exit0 and passed its unchanged independent
component build replay. Current source/settings signatures match the retained
Stage4 reference. The complete unsigned comparator refused26 file hash
differences with `reconstruction_unsigned_difference`; its normalization policy
remains `none`. These include raw/postprocessed/installed PE files, unsigned
winemetal.so and AIR/generated shader headers. Identical sizes and modes do not
explain changed bytes. Do not treat these as timestamps, UUIDs, paths or harmless
shader differences before independent exact-offset/source/format evidence.

The candidate, both complete inventories, all raw differences and original
failed operation are retained. Comparison SHA-256:
`b4e06b72ebec749ebdea2780fb6f2cb71d2cec8691cf318562d7eeb413db42fd`;
failed operation
`0aeadcf283eebc415496f2582ab880866d7df034f53a9aa509c415c3eaec0b8c`.
No construction-complete record, final native binding or Stage5 completion was
created. Native execution on this candidate is unperformed. Apply the already
approved independent metadata/path explanation boundary; unexplained code,
shader or other data changes remain failures. Preserve these bytes instead of
blindly repeating the same construction. All hybrid/game/distribution gates
remain false.


### October 3 Exact Difference Audit and Actual Shader Input Probe

An independent source/format audit mapped all26 refused inventory entries to
18 actual byte pairs. Simple PE pairs differ only at their COFF and debug
directory timestamps. Wine PE code/data/pdata/relocations remain identical,
but debug compilation paths,1328 DW_FORM_strp operands and a synthetic CodeView
GUID also change. All4 AIR pairs retain decoded function bodies, while their
air.source_file_name strings and dependent bitstream offsets change. Embedded
AIR growth changes actual winemetal instructions, array sizes, native layout and
link metadata. These findings do not justify blanket binary normalization,
semantic native-code equivalence, GPU validation or Stage5 completion.
Private audit manifest:
`e2cdef1fb4c7386241d6de923693df38b04423b4f56d4efc59fb7320a25761f6`;
18 explicitly portable audit controls passed without native/compiler execution.

The root then ran actual Metal compile probes with the currently selected
compiler, owned module cache and unchanged original sources. An earlier default
cache attempt failed permission checks and remains preserved. Six minimal
shader compiles with owned caches passed, but accepted file/debug prefix-map
flags did not make source-path-dependent AIR identical. Two further minimal
stdin compiles produced equal complete AIR bytes; that alone did not qualify
the actual selected shader dependency closure.

The complete four-source control then compiled each actual shader twice from
different owned paths using source bytes on stdin, the original constants
header, owned quote includes and emitted dependency records. All8 actual
compiler commands exited0, and all4 pairs matched complete AIR bytes exactly.
Original sources and compiler bytes remained unchanged. Control SHA-256:
`74252bb78d2b8bb6de3592ce867dc05c51a648ef240173df02a96ac94e488e1a`.
This is compiler input/reproducibility evidence, not a full native rebuild,
shader/GPU execution, driver qualification or pipeline change. The failed
original candidate and all Stage3/4 producer contracts remain untouched.

Selected LLD source supports a fixed SOURCE_DATE_EPOCH, and Wine's actual
PE configure path supports CROSSCFLAGS/debug prefix maps. Any deterministic
recipe must independently bind these changed environment/adapter identities
and its complete outputs; the original producer/checker cannot be relabelled.
Actual PE prefix-map qualification, an additive reviewed constructor and any
required final-candidate native verification remain open. No unexplained code
or shader bytes are accepted, and Stage5 remains in progress.
