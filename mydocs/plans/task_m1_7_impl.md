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
That first probe reused airconv target flags for dxmt_command rather than its
original default target; it does not establish original command-recipe equivalence.
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


### October 3 Original Shader Recipes, Independent Caches and Bound Resources

The original source recipes differ: the three airconv shaders use Metal3.1 and
AIR/macOS14 flags; dxmt_command uses the selected compiler defaults. A separate
actual default-command probe passed two compilations with equal complete AIR
bytes. A fresh all-four probe then retained each original shader's own options
and used independent owned caches for the two source locations. All8 actual
compiler commands passed, and all4 complete AIR byte pairs are equal.

The stronger final probe binds its exact producer, source/header copies, emitted
dependency files, stdout/stderr, AIR bytes, SDKSettings and the complete canonical
selected Metal toolchain resource tree before/after. It passed with control
`0a1261b70e8143d879a33895990a7568f529e4ab08e63a44e60c115246afb9e1`.
It is compiler-source/resource reproducibility evidence, not GPU execution,
complete Wine/DXMT construction or native engine qualification. A contained
toolchain directory alias remains explicitly enumerated without traversal.
The selected compiler/std/header semantics are preserved; source-name metadata
and the generated dxmt_command initializer symbol change under stdin input.
An independently bound new constructor and fresh finite native verification
are required for the resulting candidate. All14 predecessor producer bodies
and the original26-difference failed candidate remain immutable.

Actual direct Wine object compilation preserved the original source-relative
invocation and debug level while adding only an object-directory debug prefix
map. The selected LLD fixture link with SOURCE_DATE_EPOCH=0 produced equal
complete PE bytes with timestamp0. Intermediate compiler-produced object
timestamps are not fixed by that LLD setting; a coincident equal timestamp is
not deterministic object proof. Initial fixture compilation failed because a
required protocol header was not copied; that failure is preserved. These early
probes lack the stronger complete producer/dependency bindings and cannot
admit the new full constructor.

The next strengthened dependency probe refused its first compiled object:
-M discovery includes system headers while -MMD excludes them. This is a
dependency-observation mismatch, not evidence of game or runtime failure.
Its original output and producer are preserved. The corrected probe uses full
-MD dependencies and records actual discovery streams, the pre-overwrite
depfile, source/protocol inputs and every dependency hash before/after. Its
current result is pending. Actual configure CROSSCFLAGS insertion/quoting,
two full fresh deterministic builds and final native binding are unperformed.
No unsigned comparison policy was relaxed. Stage5 remains in progress.


### October 3 Bound Wine Compiler Proof and Additive Constructor Review

The strengthened final Wine probe passed four actual compile/link commands and
four full-M dependency discoveries, with the original complete graphics build
replayed before/after. Actual full-MD compile dependency sets match their
precompile records; the overwritten depfile preimage, original source/protocol
copies, command streams, producer and selected tools are bound and unchanged.
Control: `9ac5083f6c8f0085b4cfb4cdd7c0b4085e7f5c0caf0b0500a1b33722b8007e6a`.
The two linked fixture PE files have equal complete bytes and timestamp0. Equal
intermediate Wine object timestamps happened in the same clock second; this
still does not establish fixed compiler object timestamps.

The input-qualification sidecar binds this Wine control, the exact original
shader-recipes control and the current complete379-row Metal resource
inventory. Sidecar identity:
`92d1c78c3748641f948407bc4fc6198fdc8fc74b4f520fefc6cf5b34245a9cc3`.
This admits only the reviewed compiler input/resource evidence, not a complete
new construction or native/GPU execution. Historical producer bodies, records
and the26-difference failed reconstruction stay unchanged.

The additive constructor remains a private source candidate. Independent pure
review found temporary inherited module-alias mutation, secondary shader
cleanup errors replacing the primary error, and an insufficiently bound Metal
environment/predecessor. These require explicit source corrections and refusal
controls before promotion. The second private review attempted69 tests with
one relative-import error; it is preserved as partial/failed, not69 passes.
Actual configure CROSSCFLAGS quoting, two fresh complete deterministic builds,
strict unsigned equality and fresh finite native qualification remain open.
No comparison normalization or runtime claim was introduced. Stage5 is in
progress. Only sanitized findings/source are published; private controls, full
paths, diagnostics and tool/source payloads remain local.


### October 3 Additive Constructor Source, Contributor Tests and Configure Refusal

The additive deterministic constructor retains17 captured predecessor bodies
in isolated module namespaces. Closed native source-language/target recipes,
raw source products, old14 producer identities and original failed outputs
remain unchanged. New shader input transport uses exact original source bytes,
each shader's original flags and bound resource/dependency records. New record
kinds do not relabel historical builds. Primary tool errors survive separately
reported cleanup errors; the Metal input environment/predecessor is exactly
source-bound. Constructor source identity:
`019033a3210f2241f90a00a86283f750990377d508587a2fd6dd1282ad28c24c`.

The whole current DXMT suite passed423 tests with seven explicit optional
private-input skips. The selected current-input subset passed80 with zero
skips. Independent clean-checkout review also passed80 attempted/73 successful/
7 optional skips with no build directory or actual tool processes. The final
test-only correction gives the original historical Wine context a finite owned
temporary directory; it does not require this Mac's retained artifacts.
Constructor/helper byte identities stay immutable throughout actual operation.

A direct script invocation under Python3.14 refused before output admission
because the sibling DXMT inspect.py shadowed the standard library inspect
module. Invoke the same source from the repository as
`python3 -B -m tools.dxmt.deterministic_pair`; no historical helper is patched
and no compiler ran in that first invocation.

The first fresh constructor then replayed genuine prerequisites and reached
actual wine.configure, which returned1 before component make/DXMT construction.
Failed control:
`320be8ba6941f87be6ce5b676214b142934a7c6f871a7747d0cb833a9abc9b93`.
The compiler exists: Autoconf expanded CROSSCFLAGS using shell word splitting,
retaining literal quoting around a physical debug-prefix path containing a
space. The three compiler probe errors are preserved; this is not a missing
LLVM toolchain or game failure. No failed output becomes a successful build.

A separately reviewed no-space fixed-compilation-directory flag is now being
verified with two actual selected Wine object recipes and genuine configure.
Those small checks reuse read-only source inputs and precede any new complete
rebuild. Qualification3/constructor6 must bind that actual result independently
and preserve all previous source, controls and receipts. The proposed2GiB
growth ceiling/4GiB reserve is based on the previous675MB observed candidate
growth, not a measured peak; monitoring still refuses the ceiling/reserve.
Two fresh complete products, strict raw comparison, current native admission
and fresh final-candidate39-case verification remain required. Stage5 remains
in progress and every game/distribution claim remains false.


### October 3 Fixed Compilation Directory, Source Admission and Exact Storage Retirement

Two actual selected Wine object compiles and genuine configure passed with
`-fdebug-compilation-dir=/pear/reconstruction/wine/objects`, retaining native
CFLAGS and cross `-g -O2`. Control:
`b1d29c6898b946a7f8fdd9a9f4b277c0d7ec3ca5d9454284017de43b2831f14e`.
Complete object bytes happened to match; coincident intermediate timestamps
remain insufficient reproducibility proof. A separate post-probe binding
checks12,537 current regular byte/mode observations and four generated files.
Initial probe mode observations remain explicitly unperformed; this is not
retroactive provenance. Qualification3 preserves the previous refs and binds
the new control and post-only observation, with native/GPU qualification false.

Constructor6 admits the exact three whitespace-free cross tokens and requires
raw generated configuration equality before component make and on replay. Its
independent review passed93 guarded controls and the full379-resource
qualification replay with zero actual tool routes. A separate test-only
correction moves unittest.main to the true file end so direct invocation also
includes the13 new controls. Only two existing public files changed.

Root's first whole suite attempted436 tests but refused five cases because
actual disk free space was below inherited reserves (four errors/one failure);
the original test streams remain preserved. After exact duplicate reclamation,
the same436 tests passed with eight explicit optional private-input skips.
No runtime reserve was lowered to make tests pass. The distinct native adapter
and coordinator were independently reviewed after fixing executed-source
identity, early source-capture failure records and attached native errors. Root
then passed all33 added portable controls. Exact constructor/helper pinning,
per-image current authorization, the original39-case protocol and immutable
explicit diagnostics review remain required for actual final-candidate use.
Signing, native execution and raw two-product equality remain unperformed.

Requester-authorized storage retirement removed286,307 identical leaves from
23 inactive Wine source copies (9,189,166,762 logical bytes), retaining350
unique leaves,928 controls and the complete current donor. Plan identity:
`612f6437e6fc6d03ab812620f7bfbd4c5af6eb55070771991536a7236753a505`.
A second retirement removed104,443 exact duplicates from inactive tools/LLVM
and older reconstruction payloads (3,801,009,435 logical bytes), retaining
31,101 unique leaves and411 controls. Plan identity:
`2a16806bad814f294c9ea959e7dec3985b4c1ec0ebd770d22f1afac43655f669`.
Current task reference audits found no selected old-root dependency. Original
failures, active donors, private state and current qualification sources remain
intact. Historical payload replay requires exact donor rehydration. Observed
volume free increases were1,296,900,096 and2,599,272,448 bytes, respectively;
APFS physical reclamation is not independently established. Only sanitized
findings/source are published. Stage5 remains in progress; two fresh complete
builds, exact comparison and fresh current native qualification are pending.

### October 3 Shared Storage Preservation Checkpoint

Root completed the shared inactive-object archival: all 104 archive/verify/
prune/retained-verify actions across 26 batches returned zero. The 24,716 leaves
(5,136,652,549 logical bytes, 24,366 distinct payloads) have verified compressed
retention of 1,503,904,568 bytes. Aggregate identity:
`7489e2b1a9825385056c602d1f83c0b358d54d60a23e5e0724d3ecf9349a1517`.
A separate same-build install retirement removed 42,955 exact copies while
retaining 688 unique leaves and the original signed donors. Its observed volume
free increase was 1,555,550,208 bytes during concurrent builder activity;
physical APFS reclamation is not independently measured. Original receipts,
logs and current #5/#7 qualification inputs remain protected, and historical
payload replay requires exact rehydration. The stage6 research candidate is
frozen and unapplied.

The earlier 178.078 GiB project inventory is an observed footprint, not all
necessary live storage. A later inventory observed 156.304 GiB, a 21.774 GiB
lower folder aggregate during construction. Shared APFS extents can be counted
more than once; no unique physical reclamation is established. Nine major
protected roots totaled 14.024 GiB; this
partial grouping is not a complete required minimum. Fresh storage/reserve
checks apply to each operation. The new graphics constructor is replaying current input qualification;
no fresh product has been created at this checkpoint. Complete raw comparison
and current native qualification remain unperformed. These storage observations do not complete Stage5.

### October 3 Preserved Shader Timeout and Bounded Stdin Repair

The fresh constructor6 attempt completed genuine Wine configure, Wine driver
build, fixture compilation and DXMT configure. DXMT compilation then failed:
three selected shaders succeeded and dxmt_command exceeded the original
600-second bound (600093 ms, exit -9, empty logs). The complete failed product
is preserved at identity
`c97567412a4ec2771772c706d22117f4f3df5df76d7decdc5156f2af9189fba9`.
Its shader failure receipt remains
`0fec1ec9a935c731902e43af8be1f1055952afc70045ca114b2a2a122279be78`.

Selected Python3.13's communicate retry omits scheduling remaining stdin bytes
when a timeout is retried with None. Root reproduced that condition with a
controlled delayed consumer: a 20,732-byte payload stalled at 16,384 bytes with
stdin still open. The original Metal call's offset was not measured; this is
separate actual controlled evidence and a likely explanation, not retrospective
proof of that shader's offset. Its control is
`4a4cb698f64f90d40e0574a81fdcc792202842176e1ec76dad5a6230d71af9a6`.

The independently reviewed helper now owns a nonblocking write offset and EOF,
retaining the existing deadline, periodic log bounds and primary/cleanup errors.
Root's fresh small probe delivered all 20,732 controlled bytes, closed stdin and
observed exit 0. All four original Metal recipes returned 0 and whole AIR bytes
matched their original counterparts. The 379 resource facts were identical
before and after. Probe identity:
`f8094bf2513fd259659a7d0fab82c8b797690cad5a2a5e1dc1d3d373c4cbe563`.
This is compiler/transport evidence, not native, GPU, guest or game execution.

The first 489-test regression exposed seven unchanged explicit native-source
pins after helper promotion; its original failure is preserved. The separately
reviewed repair updates only the helper manifest member and its two enclosing
source hash literals, preserving every strict verification guard. The helper
is now `2e5833192d3d3411fa4cfeac4729451ae05ff861ee85c242d07247fd0a5c969e`.
The new manifest, native adapter and coordinator identities are respectively
`de00f6306e49df551efab363f96751a9cdc897ddc12606e976f398c89eac9e2b`,
`7bec079ee92d95f6b0e19f2774d2689731aac58f86f26d74f7a6bc59388b78db` and
`4a05a4a7735e0f57eda5465b10d0a42902163e22381cd5eaecc7dc709ce268e7`.

Root's targeted 155-test run passed with eight explicit optional private-input
skips. The complete 498-test attempt had four errors and one failure because
actual free space fell below inherited storage reserves, plus eight skips;
it is not recorded as a full passing run. No reserve was lowered. Two genuinely
new complete products, strict comparison and fresh final-candidate native
qualification remain pending. Earlier successful native evidence is not
transferred to this new helper/source chain. Stage5 remains in progress.

### Latest User-Requested Storage Inventory

Fresh folder allocation observations totaled 156.882 GiB: primary workspace
4.908 GiB, prior Wine worktree 133.676 GiB, prior source worktree 0.727 GiB,
current FEX worktree 9.292 GiB, current graphics worktree 6.658 GiB and
Pear-named temporary entries 1.622 GiB. Inventory identity:
`94e59a1cbe1bc1702cbc7ce37a4a5aa45479ddc266a1e0752432e217794ee012`.
This observed retention footprint is not a required minimum. APFS shared
extents can be counted repeatedly; unique physical allocation was not measured.
Compared with the earlier 178.078 GiB inventory the folder aggregate is
21.196 GiB lower, including intervening construction. Another builder is active;
volume free-space movement cannot be attributed entirely to Pear. Whole-build
admission floors of 6 GiB for graphics and 8 GiB for FEX are operation policies,
not a claim that the whole project needs only those amounts. Complete minimum
storage remains unmeasured; old repeated build retention is the main reduction
opportunity. Current donors, unique failures and private user state are retained.

### Requester-Approved Cleanup Before Further Development

Root retired 37,768 frozen exact source/tool/install/object duplicates from the
inactive Wine Stage6 research workspace (1,886,081,409 logical bytes). Every
selected leaf and retained donor was rehashed under the shared lock; current
references and original controls were checked again after retirement. Receipt:
`3e09fc0a8305f709bfaab64d6dd627fa53eb0c87322ed6d4560f10b89f30c4f4`.
The journal and unchanged retained donors permit exact byte/mode rehydration;
unique files, original failure records and current build inputs remain present.

Five inactive synthetic Wine run roots contained 19 original fixture prefixes.
Root archived only known Wine builtin ARM64 PE system files, verifying case and
prefix provenance, file identity, ordinary PE format and current non-use. No
registry, account, game, save or user-directory payload was selected. Exact
xattrs and observed ACL absence were recorded with original metadata. Of
12,996 retired copies (19,609,747,456 logical bytes), 3,364 distinct payloads
occupy 852,661,060 compressed bytes. Every gzip payload was fully decoded and
hashed before unlink, and the complete retained set was verified again after.
The restore index and operation producers remain in the private archive.
Receipt: `361aa52843975250ff9c182341144f8e167524998ef18c3d3627286447bff4c5`.
Restore index: `d4e5259ed1b393258e52db9f4dd42708bd9c47c731c2cac89fe2976ee95955e2`.
Historical execution requires exact restoration and new admission; original
inode/ctime/birthtime identities and execution qualification are not recreated.

The combined folder inventory fell from 156.882 to 137.674 GiB, including new
archives and the new source projection; project/worktree roots alone total
136.041 GiB and Pear temporary entries 1.633 GiB. Inventory identity:
`a78a893d6f01ce9e322b983e86f2bbb000fde47bec623397c314d72b859de1f1`.
Observed volume free space rose from approximately 2.5 to 10.4 GiB. APFS shared
extents and another active builder prevent attributing that whole change to
Pear. These are measured observations, not a complete minimum working-set claim.

### Regression Recovery After Storage Cleanup

The shared cleanup above preserved the graphics constructor's current sources,
original Wine donors, failed reconstruction and prior finite native evidence.
With actual space available, the complete 498-test DXMT regression run passed
with eight explicit optional private-input skips. This supersedes the previous
space-constrained regression attempt for the current unchanged graphics source
checkpoint; its five failures remain preserved. No storage reserve was lowered.
Governance and whitespace checks passed. Two genuinely fresh complete products,
raw byte comparison and fresh final-candidate native qualification remain
pending. No prior product is retagged and Stage5 is still in progress.


### 2026-10-04: Actual Construction and Transient Metal Cache Locks

The first fresh deterministic construction completed all ten commands, four
original shader compilations and eight required products. Its original build
record is `66a3f1840d20343efd5a242f9c1506bfa9e2b1cab5d48ba7c23d7c9e49800333`.
The second fresh construction was stopped during DXMT compilation by
`pair_monitor_unlisted_alias`; the supervisor killed and reaped its process
with exit -9. Preserve failure
`847bd57214948c94200d134fd07a622a5e1e4d0574b7765fb7b48ac673f95358`.
The original observer did not record the exact offending alias. A subsequent
small actual compiler probe observed transient absolute sibling links under
the owned Metal module cache, including module PCM and module-index locks.
This establishes a reproducible rejected link family; it does not recover the
specific historical offending path.

Reuse decision: leave the historical `pairing_monitor.py`, supervisor and
receipt interpretation unchanged. Add `deterministic_monitor.py` to the exact
constructor source closure and extend its pre-execution pin set explicitly.
Bind the captured original command adapter to a private globals copy with only
the size observer replaced. Retain process ownership, time/output/storage
bounds, source-bound Wine locale checks and primary failures. Admit only the
observed module-cache lock namespace and absolute same-parent target with an
eight-digit hexadecimal suffix. Never follow a cache link for accounting;
require an ordinary single-link target when it still exists. Reject directory,
external, malformed, hardlinked-target and special-file aliases. Allow exact
lock disappearance during compiler cleanup. Neither renderer behavior nor
signing/permission scope changes.

The actual four-shader probe passed with 1,264 size observations and 80 observed
transient aliases. All four whole AIR products equal the original recipe bytes;
379 selected tool-resource facts are identical before and after. Probe identity:
`34bcc0aee0fdc48ab50885621a61d77692d47d655008ad57757205b1e4295008`.
Portable controls cover accounting, target validation, disappearance/replacement,
legacy interpretation, original locale rejection and actual owned supervision.
The first full regression had one stale expected-source-list failure. After
updating that explicit list, all 514 tests passed with eight optional private
input skips. No historical result was relabeled as a new-constructor result.
Two fresh current-constructor builds, raw comparison and final-candidate finite
native qualification remain pending; game and distribution qualification remain
unperformed. Allowlisted measurements are in
[the partial observation record](../working/task_m1_7_stage5_cache_monitor_observations.json).

### 2026-10-04: Additional Recoverable Storage Reduction

Six inactive synthetic Wine prefixes contributed 4,104 repeated builtin ARM64
PE copies, totaling 6,197,280,768 logical bytes. Their exact payloads and original
metadata were archived in 1,354 compressed payloads (341,147,718 bytes), fully
decoded and hashed before retirement. Preserve the original producer, restore
index, operation journal and failure records privately. No game, account,
registry, save or signing input was selected. The restore index is
`9d47fd1716e64a080e5dd4845f2989a2cf0aeaf864de0b7c2a42f41ebd1567a1`.
Observed volume free space fell by 345,223,168 bytes during this archive step;
logical removal therefore must not be reported as physical recovery.

A subsequent byte-, decoded-hash- and attribute-verified deduplication shared
684 identical compressed payloads between the two private archives without
changing their bytes or restore indices. Shared compressed content totals
170,585,644 bytes; observed volume free space rose by 170,430,464 bytes during
that step. Two earlier maintenance attempts failed before replacing any
payload: an incorrect index filename and unavailable Python xattr API. The
successful attempt uses the macOS xattr command and retains its own journal.
APFS sharing and another builder prevent unique physical attribution. Current
free space is approximately 5.8 GiB, below the unchanged 6 GiB graphics build
admission (2 GiB growth allowance plus 4 GiB reserve). Do not lower that floor
or start a doomed full build; preserve this source/test checkpoint on GitHub.


### 2026-10-04: Fresh Build Admission Restored and First Current Build Passed

The requester confirmed additional space and explicitly continued. Actual free
space was approximately 17 GiB at admission; no growth or reserve floor changed.
The first new current-constructor build completed all ten commands and eight
required artifacts with no stop reason. Build record:
`8298d615a47464b93defa223503abd2d1f9a6808bb47d4b34747883ec031bf01`.
The second fresh build is serialized after that success and source recheck.
Comparison, new final-candidate native execution and completion remain pending.

The reviewed official locations now contain the pinned contributor guide,
index link and dated research/Wine follow-ups. Preserve the original source
mismatch and Stage 4 evidence rather than rewriting them as current results.
The guide explicitly explains private historical qualification prerequisites,
full versus component reconstruction, permissions and unperformed game gates.

A current CLI audit found that the raw native review context contains process-ID
sets. Export only that validated field as sorted JSON lists; keep the in-memory
review API unchanged and refuse malformed identities or unrelated set values.
Update the exact enclosing native source pin. Four new controls include actual
CLI JSON serialization with a fixture adapter; the native and pin suites pass
37 and 9 tests respectively. Full DXMT verification passes 518 tests with eight
optional private-input skips. Wine regression passes 842 tests with ten
conditional skips. These tests do not run the final graphics candidate.

Direct script-path help attempts exposed local `inspect.py` shadowing Python
3.14's standard library during argparse initialization. The three current
`deterministic_*` module entrypoints pass actual `--help` invocation. Document
those module commands separately from historical split tools, which retain
their recorded Python 3.13.5/local-import route; do not relabel the historical
CLI as a tested Python 3.14 package entrypoint or change frozen producers.
Offline governance passes 23 documents and 198 local targets; whitespace checks
pass. The selected Metal-validation reference remains Apple's revision
`4f42344c90be22112f46becc3fb9687f423f2f88`, plugin 1.0.0-beta.1. The planned
current native run keeps the approved environment before device creation and
uses a process-scoped awake-display assertion without changing system settings.


### 2026-10-04: Second Fresh Build and Native Link Difference

The second current-constructor build completed all ten commands and eight
required artifacts. Its build receipt is
`20942faa35582f0990041a98e1dfbf68f22b8cc85105e487d952f3cc9b7aebfe`.
Seven primary artifacts equal the first current build byte for byte. The
47,178,688-byte native winemetal differs at 552 byte positions. Preserve both
whole products and the independent complete-inventory comparison in progress.

Read-only Mach-O inspection attributes those positions to 375 Objective-C stub
LDR instructions and one generic objc_msgSend stub choosing alternate duplicate
GOT slots for the same indirect symbol, the 16-byte LC_UUID, and five 32-byte
CodeDirectory page hashes. The indirect symbol tables and encoded pointers in
both slots agree; all page hashes were independently recomputed. This is a
static description, not qualified runtime equivalence or a comparison waiver.
No product normalization was performed. The private classification receipt is
`c21853b5a9000261f283541c610351b6d0d3e71d4a50bac17dabfd36f1c45800`.

Reuse decision: test the installed Apple ld documented `-reproducible` option
with the exact captured native link inputs before changing the constructor.
A private bounded diagnostic is queued behind the shared compilation lock:
three unchanged baseline links and three links adding only that option, each
in a fresh output directory with the same output basename. Retain original
objects, libraries and products, hash selected inputs before and after, and
preserve raw logs and whole output hashes. This diagnostic does not execute a
library, substitute for a fresh build or authorize final native qualification.
The archival work started in the requester's side chat uses the same lock;
its process and retention plan are not modified here. Stage 5 remains open.


### 2026-10-04: Bounded Link Trials and Storage Coordination

The complete-inventory comparison was deliberately interrupted after the
independently established primary raw mismatch. Its original failure record
retains `KeyboardInterrupt` during `independent_two_product_replay`; no complete
inventory equality or completed comparator failure diagnosis is claimed. The
private operator receipt records the reason. Only the verified owned comparator
was signalled; archive workers were untouched.

The first diagnostic stopped before linker execution because its input collector
mistook an install-name option for an input file. The corrected diagnostic
preserves that failure and uses argument arrays, fresh output directories,
process-group deadlines, bounded logs/output and unchanged disk reserves.
Thirty-one actual links completed with selected input hashes unchanged:

| Link setting | Attempts | Distinct whole output hashes |
|---|---:|---:|
| Original baseline | 3 | 2 |
| `-reproducible` | 3 | 2 |
| `-no_deduplicate` | 3 | 2 |
| Explicit `-lobjc` | 8 | 2 |
| `-ld_classic` | 3 | 2 |
| `-objc_stubs_small` | 11 across two diagnostic batches | 1 |

The small-stub output is 47,162,160 bytes, SHA-256
`8516cf860d674b09634e77edc94a494dd33d94da729a06e12b3480fcd67569c9`.
Baseline trials reproduce both original build hashes. The installed classic
linker emits a deprecation/removal warning and did not solve the difference.
No linked output was loaded or executed. Private original logs retain deployment
target warnings. Counts and selected-input identity do not establish universal
linker determinism, same-source clean compilation or runtime correctness.

Reuse decision: adopt Apple's documented `-objc_stubs_small` as the next
construction candidate, retaining the current native linker and upstream source.
[Apple WWDC22, Improve app size and runtime performance](https://developer.apple.com/videos/play/wwdc2022/110363/)
explains the separate selector/call stubs and their size/performance tradeoff;
reviewed October 4, 2026. This is a reproducibility workaround, not a performance
improvement. Its runtime cost is unmeasured. Apply the option only in generated
native C/C++ linker settings; preserve Windows cross configuration, compilation
flags, shaders, original prerequisite records and every historical producer.
Recipe policy advances to version 3 and binds the option into independent source
comparison. Update the explicit constructor and native source pins. Do not
reinterpret build5/build6 as products of the changed constructor.

Targeted deterministic suites ran 149 tests: 141 passed, eight optional private
input tests skipped. Controls cover exact native-option changes, unchanged
compiler/guest configuration, missing/duplicate/malformed/preconfigured options,
and link-option changes affecting the source signature. The earlier full
518-test DXMT and 842-test Wine runs belong to the preceding source checkpoint.
Current full regression, two fresh constructions, exact final inventories and
same-candidate native qualification remain pending.

A user-authorized request relayed from the storage side chat prioritizes its
ongoing iCloud retention work. Finish the already-running targeted tests, then
start no new build or verification until that cleanup completes. Documentation
and this source checkpoint may be preserved on GitHub. No archive process is
interrupted or modified. Stage 5 remains in progress; no guest/game/distribution
scope changes or qualification claims follow.


### 2026-10-04: Storage Gate Cleared and Current Regression Passed

The storage side chat reported completion of retirement for its 51 approved
historical Task #4 roots and released the shared compilation lock. Local
observation confirmed approximately 43 GiB free. Current #5/#7 and protected
Wine inputs remain selected; pending iCloud synchronization retains its verified
local backup copies and delta bases. This task does not delete those copies.
Existing Stage 5 authorization resumes without a new scope or stage transition.

The current small-stub source checkpoint passed the complete DXMT regression:
521 tests, comprising 513 passed and eight optional private-input skips. Offline
governance passed 23 documents and 199 local targets; the committed source diff
passed whitespace checks. Two new component builds use new output roots, the
unchanged 2 GiB growth allowance and 4 GiB free-space reserve. Full comparison
and new-candidate native execution remain pending until their actual records.
The first builder is performing the original source/tool prerequisite replay;
no historical build is relabeled as a current result.

The parallel #14 owner proposes portable scratch-directory rules without editing
#7 files. Treat hardcoded test temporary roots as a follow-up portability item,
not a reason to mutate the active constructor/test checkpoint. Synthetic path
refusal strings are distinct from actual scratch roots and must not receive a
blanket replacement. #14's documentation proposal is not automatically inherited
as a modified approved #7 recipe.


### 2026-10-04: Two Fresh Small-Stub Constructions Passed

Both new source constructions passed all ten commands and post-build input
checks. The reference build receipt is
`fb5648ddb21836b5f0a80a1e546910ee3f46fb9a563a54c1197fe3743cd5dce1`;
the candidate is `5eb2a22a1e6132043ba3be3985683573e23f81893f91b9729b55ef00fb57a31d`.
All eight primary artifacts match byte for byte. The changed native winemetal
retains the previous architecture, dependency/install-name/rpath metadata and
14,935 external defined symbols. This static interface equality does not replace
native call/lifetime verification. Complete unsigned inventory comparison is
now running against these new roots; final native execution remains unperformed.


### 2026-10-04: Complete Raw Comparison and Independent Replay Passed

The current comparison command finished with exit zero after independently
replaying both constructions. All 2,878 unsigned inventory entries match
(2,785 files, 77 directories and 16 symbolic links), without normalization or
exclusion of linker-generated ad hoc signatures. Both inventory digests are
`b7c16fcbeaa9da509a02a381f3ae3bcb9853d8ddb64e7af1a5b89be23a58fe23`.
Comparison receipt: `fe3ea47e0bb77edbdfebe8c58f6153c238d58864522a655f345a1392f4734007`;
construction receipt: `edd1aa44435ab01e1a47e3c4b9715143865fe343e1613b0c2640bd2abcdfb1a8`.
The root observed actual command termination before admitting the next phase;
receipt creation alone was not accepted as successful completion.

Fresh candidate development admission and the original finite 39-case native
schedule now follow under the shared lock. Explicit raw-log review and final
reconstruction replay remain required. Stage 5, translated/game execution and
ordinary-user distribution are not qualified by this comparison. The immutable
prior mismatch, interrupted comparison and observer failure remain preserved.


### 2026-10-04: Fresh Candidate Development Admission Passed

Preparation of the matching candidate finished with exit zero. The isolated
materialization contains 39 native images and 756 PE images. All 199 signing
commands and 163 current-admission commands passed, followed by independent
source/payload replay. Runtime receipt:
`d278123d23993a527e632411eba7e0eaa166251a7746366d67b4a670006ac6dd`;
current-admission receipt:
`96b077716e18839eddf827987d5aaefb638ab0e6d63c865b2c25d0a2315fc76a`.
Preparation took 2,255,876 ms on this host, including prerequisite replay;
this is a verification-cost observation, not a runtime performance result.

The same-candidate finite native run is now started under the shared lock,
with process-scoped display/idle prevention and the unchanged Metal validation
environment. The run, explicit raw-log review and complete final reconstruction
remain unqualified until their actual completion. Private signatures, profiles,
certificate information and raw diagnostic streams remain outside Git.


### 2026-10-04: Finite Native Run Failed After Case 33

The same candidate passed fresh per-image admission, then the actual ordinary
ARM64 fixture failed. It emitted the first 33 native rows, each with the expected
status and facts=1, ending at `destroy_acquire`; the last six rows and PE terminal
record were not emitted. The loader returned 5 and its owned process-exit event
recorded `0xc0000005` (access violation). The exact failing instruction and root
cause remain unknown. The source sequence places the next operation at window
destruction; this is localization, not proof of a particular component defect.

The case lasted 11,158 ms; the wrapper took 1,272,378 ms including pre-execution
input/admission replay. The graphical session was available, owned cleanup
completed without errors, and the unrelated sentinel survived. Case receipt:
`95fdf884fc593916ea4b4d6537f2eebffb43fca46e3d5b40d96b1115f5bf77d1`;
failure receipt: `960e289a0b362c0ce09a42882aa97f917200d8f1965466b552fb202c1c62f951`.
Do not create passing diagnostics or reconstruction-completion records.

A bounded private diagnostic reuses the signed candidate and unchanged original
39-case body/owned supervisor, with only `WINEDEBUG=-all,+seh` replacing `-all`
in a separate function-global environment copy. Historical sources and records
are untouched. It performs current admission before execution and uses a new
owned output, the existing timeout/output limits and process-scoped caffeinate.
The altered environment is diagnostic-only and cannot qualify the unchanged
finite evidence protocol. Retain all diagnostic failures and raw traces privately.

Read-only section comparison found identical native driver `__TEXT.__text`,
ordinary driver `.text` and original PE fixture `.text` against Stage 4. This
does not establish whole-image equivalence or exclude a runtime/link/teardown
interaction; the native DXMT linker change remains only one hypothesis.


### 2026-10-04: SEH Diagnostic Completed; Original Failure Remains Open

The diagnostic-only `-all,+seh` run returned zero and emitted all 39 expected
status/facts rows. Three views, three layers and one proxy were created and
physically deallocated; owned cleanup and unrelated-sentinel survival passed.
This does not explain or supersede the original `-all` access violation. Logging,
scheduling, process addresses and fresh-prefix state differ; none is established
as the cause. The diagnostic has no qualifying run/completion/review record.

The next bounded investigation uses one unchanged `-all` control and at most
two private observer variants, stopping if an actual fault record is obtained.
A separate ordinary ARM64 PE retains the same 39-case schedule and adds only a
vectored handler that writes a bounded register/step record for a real access
violation, then returns EXCEPTION_CONTINUE_SEARCH. It does not manufacture a
fault, recover an exception, change host permissions or modify the Wine/DXMT
binaries. The handler is quiet on ordinary execution. The private compile
reuses the selected compiler/flags, passed -Werror with empty streams, and its
output was inspected as ordinary ARM64 PE. No observer effectiveness is claimed
until an actual fault is captured.

The private runner derives the unchanged owned run-case body with one explicit
fixture-path assignment for observer cases; its inverse AST equals the captured
original body. Native signatures and runtime remain unchanged. Current live
admission occurs once before this finite diagnostic batch, with no input
mutation between cases, the original per-case time/output/cleanup limits, fresh
prefixes and at least 6 GiB free before each case. These diagnostic results cannot
replace the original complete native admission/run/review gate. All attempts
and the original access violation remain preserved, and Stage 5 stays open.


### 2026-10-04: Quiet Diagnostic Batch Completed Without Reproducing the Fault

One unchanged quiet control and two quiet vectored-observer runs returned zero
and emitted all 39 expected status/facts rows. Each physically balanced three
views, three layers and one proxy. Owned cleanup completed and unrelated
sentinels survived. No access-violation observation was emitted; effectiveness
of the handler on an actual fault remains unproven. The original control passed
its separate assessment; the two changed-fixture runs correctly retain
`pair_launch_changed` refusals and are not qualification runs. Raw `case.json`
records capture `passed=false` before the separate `assessment.json` verdict;
these fields must not be conflated.

Batch receipt: `72d1a062fb6e4c1d3360e5aea7f843aaf71a56a379b5f81d9d23624c4e5d0f1d`.
The three case digests and actual durations are in the partial observations.
The original failure remains immutable and unresolved. At row 33 its layer
witness had observed one deallocation, versus zero in the four successful
SEH/control/observer diagnostics. This small correlation does not establish a
lifetime defect, race, or failing instruction. No source fix or Stage 5
completion follows from successful retries.

### Proposed Amendment: Isolated LLDB Fault Capture — Approval Pending

**Status:** review only. No additional entitlement, re-signing, debugger attach,
or diagnostic rendezvous implementation has been performed. This stays within
Issue #7 Stage 5 diagnosis, but the October 3 approval explicitly reserves
“new security or shared-scope changes” for a separate gate. App-local debugger
permission changes the previously approved exact signing claims.

**Purpose and reuse.** Capture the actual native fault PC, registers, image
identity and thread stacks around detach/window teardown. Reuse the installed
Xcode LLDB, existing native ARM64 bootstrap, owned Wine supervisor, unchanged
39-case operations, selected compiler and development identity. Successful
reruns cannot establish the cause, and the quiet PE exception observer has not
captured an actual fault. A debugger may also perturb timing; failure to
reproduce remains inconclusive.

**Concrete scope proposed for approval:**

1. Under the shared native lock, verify the unchanged candidate and materialize
   a fresh diagnostic-only runtime copy under `.build/task7/`. Use independent
   files or copy-on-write clones, never hard links for any signed/mutable file.
   Preserve the original runtime, all failures and source caches. Bind the
   derivative manifest to runtime receipt
   `d278123d23993a527e632411eba7e0eaa166251a7746366d67b4a670006ac6dd`.
2. Re-sign only the copied Wine loader bundle using the existing authorized
   development identity/profile and existing claims plus the Boolean
   `com.apple.security.get-task-allow=true`. Retain Hardened Runtime, library
   validation, 4 KiB signing page size, cross-architecture and JIT settings.
   Helpers and libraries receive no new claims. Verify exact claim delta,
   current profile/identity, strict signatures, source/payload identities and
   the unchanged original. Do not forge a normal runtime admission receipt or
   loosen its exact-claims verifier; this copy has separate diagnostic records.
3. Add a private diagnostic PE rendezvous immediately before the detach phase
   (step 9), using a bounded, controller-owned release marker in the empty
   diagnostic prefix/output. Preserve the actual native case operations and
   exception semantics. Verify marker containment, unique per-run identity,
   no symlink substitution and a 30-second rendezvous deadline. Compile with
   the same selected ARM64 PE toolchain and inspect the output. Record the
   instrumentation rather than presenting it as the unchanged fixture.
4. Launch through the existing 4 KiB bootstrap and owned supervisor. At the
   rendezvous, attach LLDB only to the registered loader PID after checking its
   executable identity, start identity and private run nonce. Record actual
   ARM64/translation and process-mode observations; LLDB availability alone
   does not prove attach or 4 KiB compatibility. Release the rendezvous only
   after confirmed attachment. If OS authorization is denied or needs user
   interaction, retain that result and use the normal macOS authorization flow;
   do not change SIP, global debugger policy or unrelated processes.
5. Run at most three diagnostic attempts, each bounded by the existing
   180-second case deadline, with debugger output capped at 16 MiB. On a real
   bad-access stop, capture PC/LR/SP/FP/x18, fault information, bounded thread
   backtraces and loaded image UUID/offset mapping. Preserve normal fault
   delivery after capture where supported; record debugger stop/termination
   separately from the program outcome. Stop the batch after a useful capture,
   identity/admission failure, timeout, output limit or cleanup failure.
   Reuse owned cleanup with debugger detach/termination before process cleanup,
   reap every owned child and verify unrelated-sentinel survival.
6. Keep raw captures, signatures, addresses and prefixes private. Publish only
   sanitized provenance and findings. Debugger success is not native/runtime/
   game qualification. Any resulting source repair must be separately verified
   with the unmodified production fixture/signing policy before the ordinary
   reconstruction gate can pass.

**Storage and validation.** The current runtime uses approximately 1.22 GiB
and each completed diagnostic output approximately 1.08 GiB of allocated space.
Use one diagnostic copy, at most three fresh prefixes, a 6 GiB aggregate growth
ceiling and an 8 GiB free-space reserve, rechecked before each operation. No
full Wine/DXMT rebuild is proposed for capture. Validate claim-delta refusal,
wrong/stale PID refusal, rendezvous timeout/containment, debugger output limits
and owned cleanup before the actual attach. Preserve successful and failed
capture receipts and record any unperformed check explicitly.

**Permission rationale and primary references.** The inspected loader does not
currently claim `get-task-allow`. Apple documents debugger access to third-party
apps with this entitlement in [Debugging tool entitlement](https://developer.apple.com/documentation/BundleResources/Entitlements/com.apple.security.cs.debugger).
[TN3125](https://developer.apple.com/documentation/technotes/tn3125-inside-code-signing-provisioning-profiles)
lists macOS `com.apple.security.get-task-allow` as unrestricted, so its absence
from the existing provisioning profile does not by itself require a new profile.
Actual cross-architecture/profile and signature authorization still require
validation. The added claim permits debugging of this development copy and
must never enter a distributed artifact. Approval requested is only for this
bounded diagnostic copy and attach procedure; it does not approve a release,
new system-wide permissions or shared loader/translator source changes.

**Location judgment.** Keep the amendment in this existing implementation plan,
allowlisted outcomes in the existing partial observations and status in the
daily board. Private scripts/manifests live in ignored owned task outputs. No
new product/API/roadmap document location is introduced.


### 2026-10-04: Isolated LLDB Amendment Approved

The requester explicitly continued in the same thread after reviewing the
concrete isolated LLDB amendment. This authorizes its diagnostic-only copied
loader entitlement, signing, bounded rendezvous and owned-process debugger
attachment. The original runtime and production admission rules stay unchanged.
Implementation and actual permission/attach results remain to be recorded;
approval does not establish successful authorization or fault capture.


### 2026-10-04: Diagnostic Signing and Attach Observed; Controller Gate Failed

Original current admission passed in 1,273,951 ms. The independent diagnostic
copy passed 119 signing/verification commands across 39 native images. Only
`Contents/MacOS/wine` changed in the bundle; the original bundle inventory
remained identical. Preparation receipt:
`4bb478cf28c9c70d3c70c1d137199a0857b218b4daac93aeb2bc05e84210e665`.
Five pure refusal/boundary tests, inverse runner-AST comparison and cleanup-error
retention passed. A private socket pair connected directly owned LLDB and
Apple debugserver without a listening network port; their transport and cleanup
checks passed. Existing Wine supervisor sources and exact admission validators
were not modified.

All three allowed Wine diagnostic attempts are preserved:

1. The rendezvous timeout control emitted 27 rows and exited with code 96 after
   approximately 30 seconds without release. Its whole case lasted 37,356 ms;
   Wine cleanup and sentinel survival passed. The normal success assessor
   correctly refused this deliberate negative control.
2. Actual attach succeeded, but an unavailable Python binding method
   (`SetShouldPass`) stopped the diagnostic before release. LLDB acknowledged
   detach; debugger and Wine cleanup passed, sentinel survived. The installed
   API was then inspected and corrected to `SetShouldSuppress(signal, false)`.
3. Actual attach acknowledged an ARM64 target, but the controller failed before
   the release marker. Debugger children were reaped; Wine cleanup failed with
   `owned_identity_unavailable` and `registered_exit_barrier_timeout`. The root
   loader was not reaped by the supervisor. A subsequent read-only audit of all
   recorded PIDs found no live process and one exited zombie parented to init.
   Its exit status and eventual system reaping are unknown. Do not recategorize
   this as successful cleanup, detach, normal execution or an observed game fault.

The third initiating exception was collapsed into `pair_run_operation_failed`
because the private refusal exception lacked a `code` attribute. This evidence
loss is recorded explicitly; later cleanup errors do not identify the initiating
error. Raw streams and all failed producers remain private and immutable.
Additional setup refusals are preserved: system Python AST descriptor mismatch,
a large local PE buffer introducing `__chkstk` under the no-CRT fixture link,
and an immediate state assertion before LLDB's asynchronous connected event.
The buffer was moved to static storage; the corrected PE compiled with the
selected toolchain. None of these setup failures establishes a Wine/DXMT defect.

No fault PC was captured and no original access violation was resolved. The
maximum three Wine attempts has been reached; no further native fixture is
started under this batch. The diagnostic tree occupies about 4.46 GiB, under
its 6 GiB growth ceiling; observed disk free space was about 23 GiB. Current
failure records and the diagnostic copy remain needed for investigation.

### Proposed Follow-up: Explicit Tracer Handoff and Acknowledged Detach

**Status:** review pending for the next bounded native batch. Four pure controls
for the proposed identity transition and primary-error retention pass; actual
handoff, cancellation, exit/reap and fault-capture execution remain unperformed.
The private proposal does not change general Wine process ownership policy.

**Reason.** The prior plan reused a constant-parent process identity throughout
attach. Apple's [XNU source](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/kern/mach_process.c#L285)
explicitly saves the original parent, reparents to the tracer on attach, and
restores that parent on detach. This source review is not proof of the precise
initiating error in the failed run, whose detailed exception was lost. It does
identify a missing diagnostic ownership state. Also, killing the debugger
while its script awaits the release marker provides no acknowledged detach;
normal Wine cleanup cannot assume that the original parent/reaping relationship
has already been restored.

**Concrete proposed change and verification:**

- Keep the original PID/start timestamp, registered nonce and executable identity
  immutable. Before attach, require the original parent. During the explicitly
  observed attach state only, accept the exact directly owned debugserver as
  parent after checking that tracer's own PID/start identity and executable.
  Refuse another parent, reused PID, changed start timestamp or changed image.
  Never relax the shared `tools/wine/` identity checks or rewrite old receipts.
- Add an exclusive nonce-bound cancel marker understood by the LLDB script while
  waiting for release and during capture. Preserve the primary exception code
  and detailed phase. Request detach, await its explicit success receipt, and
  verify the original parent relationship before normal owned cleanup. Preserve
  missing acknowledgment, failed restoration and unreaped exits as failures.
  Emergency termination remains a failed fallback, never proof of detach.
- First use at most three small, explicitly owned native diagnostic children to
  verify normal attach/detach, cancellation before release and target exit/reap
  behavior. Bind their actual signing and source identities before execution;
  use the same approved app-local debugging claim, no new system permission.
  Each control has a 30-second execution bound plus bounded owned cleanup, and
  must leave no unreaped owned process or observation gap before Wine retries.
- Only after those controls pass, permit at most two fresh Wine capture cases,
  each with the existing 180-second deadline and 16 MiB debugger-output ceiling.
  Stop on a fault capture, failed identity/permission check or incomplete cleanup.
  Capture a real bad-access PC/registers/stacks with normal exception delivery
  where supported; a successful or instrumented retry cannot clear the original
  unexplained access violation.
- Reuse the signed diagnostic copy after fresh identity/claim/signature checks.
  Allow at most 3 GiB additional diagnostic growth, require an 8 GiB free-space
  reserve before each case, preserve all existing failures and publish only
  sanitized results. No full rebuild, game run or production-policy change is
  included. Keep this work in the existing plan/partial observations/board and
  private ignored diagnostic outputs; no new official documentation location.

Approval is requested for this corrected ownership/cleanup protocol and its new
finite native batch. The previous signing authorization remains applicable;
no additional debugger entitlement or account/profile setup is requested.


### 2026-10-04: Tracer Handoff Follow-up Approved

The requester explicitly continued after the concrete tracer handoff and
acknowledged-detach proposal. This authorizes its three small native controls
and, only if those pass, up to two Wine capture cases with the stated limits.
The diagnostic-only parent transition does not relax shared Wine ownership
checks or qualify the original runtime. The same app-local debugging claim
applies; no new system setting or additional privilege is requested.


### 2026-10-04: Handoff Controls and Two Wine Diagnostics Completed

The three approved native controls passed: normal attach/detach, cancellation
before release, and target exit/reaping while traced. Each used a source-built
thin ARM64 executable signed with only the approved app-local debugging claim.
Actual native/translation observations, PID/start identities, the exact owned
tracer parent, restored parent where applicable, zero target exit and complete
owned cleanup were recorded. This establishes the finite diagnostic protocol,
not general race freedom or a change to the production Wine ownership policy.
The initial direct Clang command lacked its SDK root and failed before execution;
that failure is retained. The corrected command selected the actual Xcode SDK.

The LLDB script now accepts a nonce-bound cancellation request while waiting
for release and during capture, and records acknowledged detach. The controller
accepts only the exact verified owned tracer as temporary parent while keeping
the original PID/start identity, registered nonce and executable immutable.
Normal cleanup requires restored parent identity or the observed target exit.
Private refusal exceptions retain their specific primary error codes.

Following the successful controls, current diagnostic signature, claims,
certificate availability, profile expiry and byte identity checks passed.
Original and diagnostic bundle inventories were replayed before and after the
finite Wine batch. Two fresh-prefix Wine runs then each returned zero, emitted
all 39 expected status/facts rows and physically balanced three views, three
layers and one proxy. Both debug sessions observed target exit zero; all direct
owned Wine/debugger children were reaped, Wine and debugger cleanup completed,
and unrelated sentinels survived. Actual case durations were 10,639 and 7,624 ms;
these instrumented correctness runs are not performance measurements.

The ordinary verifier retains `pair_launch_changed` for both diagnostic
fixtures. No qualifying run, original-runtime completion or passing formal
Metal-diagnostics review is substituted. No access violation was captured.
Both successful runs observed one deallocated layer at case 33, matching the
original failure's count. That count alone therefore does not explain failure;
this does not exclude a timing or lifetime defect. The original failure remains
unresolved and the prior failed cleanup remains failed in historical evidence.

Current diagnostics have exercised the repaired debugger ownership protocol.
Stage 5 completion still requires resolving the
original unexplained native failure and completing the ordinary unchanged
admission/run/review gate. Neither game execution nor distribution is qualified.
No further native case was started beyond the approved three small controls
and two Wine cases. Private producers, raw traces and failure records remain
outside Git; allowlisted outcomes and receipt hashes are in the existing
partial observations.


### 2026-10-04: Bounded Final-Candidate Verification and Completion Review

The requester continued after the proposal to assess #7 against its original
component-build and paired-interface scope. This authorizes the following
verification work; it does not silently accept the original access violation,
close #7, or change the delivery plan's correctness requirements.

Reuse the existing source-matched deterministic builds 7/8, complete raw
comparison 2 and signed runtime 2. Do not rebuild or re-sign unchanged inputs.
Run at most two ordinary `deterministic_native --run` operations, serially,
with fresh synthetic prefixes and the original fixture, signing, supervisor,
Metal environment and `WINEDEBUG=-all`. Each operation retains its existing
live admission before and after execution. Hold the shared native lock, keep
the graphical session awake, record host and workload observations without
terminating unrelated work, admit at most 3 GiB of new retained output and keep
at least 8 GiB free. No debugger, fault-handler PE replacement, extra logging,
OS setting change, game execution or profiling is authorized by this batch.

Predeclare both runs before starting. Stop the batch at the first operation,
case, cleanup, identity, storage or diagnostics failure; preserve its evidence.
Do not add retries merely to obtain success. Each successful run must contain
all 39 original expected rows, zero guest/loader errors, complete owned cleanup
and surviving sentinel, current native admission, unchanged inputs and an
explicit review of every captured diagnostic stream. Unknown warnings or Metal
API errors fail review. Two passes establish only this finite same-host result,
not environmental causation, arbitrary schedule safety or cross-Mac stability.

Reuse the existing native/evidence/reconstruction verifiers without changing
any acceptance predicate. After explicit raw-log review, bind the final run to
the exact comparison candidate and independently replay the result. A machine
record for finite reconstruction is distinct from requester acceptance of the
historical failure and from task completion. Preserve the original failed run,
all unsuccessful diagnostic attempts and the root-cause uncertainty in public
sanitized observations and the proposed final report.

The previous journal's unconditional demand to resolve the historical fault
is an assistant-added completion interpretation, not wording in Issue #7.
Any proposal to complete #7 with that fault unresolved must explicitly identify
the risk and obtain requester review; until that decision, Stage 5 and #7 stay
in progress even if this finite batch passes. A repeated required-path fault
blocks completion and requires investigation/correction rather than waiver by
this proposal. No source, product requirement or verification rule is relaxed.

Document locations remain the approved task plan, observation sidecar and daily
board; no new official-document location is needed. The existing source-pinned
Apple `using-metal-validation` guidance applies to log review. Existing direct
owned-process launch and pre-device validation settings remain unchanged;
no LaunchServices substitution or new graphics subsystem is introduced.


### 2026-10-04: Single Incident Handoff and Deferred Investigation

The user-requested side-chat recommendation was delivered during final
verification. It does not authorize automatic completion, a verification waiver
or deletion. Apply its evidence/prioritization distinction: keep the historical
failure unknown and uncorrected, defer additional speculative investigation,
and reopen on recurrence, useful new fault evidence or a concrete related defect.
The current predeclared ordinary verification continues; a fresh failure stops
it. No additional debugger expansion or whole rebuild is introduced.

Location judgment: `mydocs/troubleshootings/task_m1_7_initial_access_violation.md`
is an Issue-specific incident/recurrence artifact under the existing document
structure guide and troubleshooting template, not a new product specification.
It centralizes the original input/receipt identities, reproduction procedure,
unknown cause, lack of a confirmed fix and retention/reopening rules. The
already approved DXMT guide links this incident; daily updates need only its
short reference. Historical plan/JSON observations are preserved, not rewritten
to imply resolution. #7 completion remains subject to actual required evidence
and review, rather than automatic approval through the side-chat message.

### 2026-10-04: Required Run Failed; Target the Newly Observed Exit Path

The first ordinary run passed fresh admission but failed `pair_guest_exit_missing`:
33 rows through `destroy_acquire`, no PE terminal and no loader-role guest/process
exit event, despite observed OS loader exit zero. This reopens the incident's
same-boundary incomplete-execution investigation; it does not prove that the
original access-violation code recurred. The second ordinary run is cancelled.
All 20 raw stream hashes and all 2,788 signed bundle inventory entries survived
postflight replay. The new admission's 163 commands passed; cleanup and sentinel
checks passed. A nine-second loader-only system-log query yielded no confirmed
cause. No passing formal evidence or reconstruction completion was produced.

The current continuation and incident reopening rule support one narrow
termination-stack diagnostic using the already authorized debugger copy and
validated handoff. Reuse its app-local claim, signing, rendezvous fixture and
owned cleanup; add LLDB breakpoints for `exit`, `_exit`, `abort_process` and
`exit_process`, requiring at least one resolved location before release. Capture
bounded thread stacks on a matching exit breakpoint or the existing bad-access
stop, then acknowledge detach and clean up. Keep the existing nonce/parent/PID,
deadline and output guards. One Wine diagnostic case is permitted by this
follow-up; do not run the cancelled ordinary repeat or add a pass-seeking loop.

Original production inputs and verifier predicates remain unchanged. The copy
and rendezvous are explicitly diagnostic and cannot qualify #7. Keep at least
8 GiB free and the combined new verification/diagnostic outputs below 3 GiB;
reuse the existing signed copy and keep all failures. No new build tool, global
setting, entitlement, whole-runtime reconstruction or game execution is added.
If no causal stack is captured, record that limit rather than infer a fix.


### 2026-10-04: Termination Capture Completed Without a Causal Failing Stack

The one targeted diagnostic completed all 39 rows, balanced physical lifetimes
and returned zero. LLDB captured `exit_process` with `NtTerminateProcess` as
caller and a zero exit argument after normal diagnostic completion. Acknowledged
detach, Wine/debugger cleanup and the unrelated sentinel all passed. Existing
nine portable ownership controls passed and installed LLDB breakpoint APIs and
script loading were checked before execution. Original and diagnostic bundle
byte/signature replay passed before and after. The normal verifier retains
`pair_launch_changed`; this modified diagnostic cannot qualify the original.

No fault or causally useful failing stack was captured. The ordinary candidate
failure remains a required-verification blocker, distinct from the historical
access violation's unconfirmed cause. No second ordinary run or further Wine
diagnostic was executed. Combined new retained output is approximately 2.17 GiB,
within the 3 GiB bound; more than 17 GiB remains free. No whole build, new signed
runtime, security change, game operation or deletion was performed.

The incident document owns the failure signature, retention and reopening
context. Read-only teardown inspection did not establish a concrete correction;
no production source was patched. Preserve the incomplete stage and failed
records. A completed Stage 5/final report, reconstruction completion, PR or
Issue closure is not warranted by the current evidence.


### 2026-10-04: Read-Only Network and Power Timeline Review

The requester reported an internet outage followed by lid closure and supplied
an app-reconnection screenshot. Continue the approved incident investigation
with existing source/receipt inspection and a read-only power-log query. Reuse
`pmset` and existing Wine/Pear source; do not alter network, power or security
settings or run another native test solely to check this hypothesis.

The power log places the next display-off at 14:43:57 KST, after the failed
14:36:45–14:36:52 case, with no sleep/wake/display transition found during that
case. The test uses local IPC; no direct internet dependency or supervisor
interruption was observed. Exact outage and physical lid-close times remain
unknown. Local EOF/EPIPE and SIGQUIT zero-exit paths are source-only leads,
not a diagnosis. Keep the existing incident and sanitized observations as the
approved Issue-specific evidence locations; retain raw logs privately. No
source or public product-documentation change is needed. Stage 5 remains
incomplete, with no new execution, rebuild or deletion in this review.

### 2026-10-04: Separate Window Teardown from Metal Teardown

The requester explicitly continued toward Megabonk execution after the network
review. Within the reopened #7 incident, run two distinct diagnostic controls:
one original Win32 window sequence with pairing calls bypassed, then one full
pairing sequence with small PE-side boundary markers. Each runs once in a fresh
synthetic prefix against the unchanged signed runtime. Mark before/after native
control, DestroyWindow, WM_DESTROY/WM_NCDESTROY, and terminal cleanup. Preserve
GetLastError around diagnostic writes. Do not install exception handlers, attach
a debugger, rebuild Wine, replace signatures, or change verifier predicates.
Reuse the pinned original fixture/compiler, local owned supervisor, signed
bundle inventory and Apple Metal-validation settings. Source/producer hashes,
compile output and raw execution receipts remain private and immutable.

Replay original bundle bytes/modes/links and current signature/profile/identity
before and after diagnostics. This limited diagnostic admission is explicitly
not a fresh full component provenance/qualification replay. Keep actual 4 KiB
and native-process observations through the existing runner. The ordinary
verifier must refuse the changed fixture; no qualifying run receipt is created.
Inspect all diagnostic streams and assess phase markers separately. Abort the
batch on operational/cleanup failure or a useful new incomplete-execution
signature; no retry seeks a pass. Limit new output to 3 GiB and retain at least
8 GiB free. Do not delete existing evidence. The existing incident/observation
locations hold sanitized outcomes; no product-documentation location changes.
Two successful diagnostic controls would narrow the tested conditions only,
not repair or waive the unchanged-candidate failure. Further production changes
require a concrete defect or a separately scoped implementation decision.

Both declared diagnostics completed: window-only returned from destruction
callbacks, and full Metal emitted all 39 rows. Normal terminal/guest/process
exit evidence, cleanup and sentinel checks passed. Raw-log review initially
refused notices because its helper considered only direct children; attribution
to the existing source-registered descendants fixed that review error. The
review then found no unclassified lines or API errors. Before/after byte and
current authorization checks passed. Qualification stays refused for modified
fixtures; root cause is unknown. No third run, production fix or completion
claim was made. Retained output is approximately 2.17 GiB. Continue separately
approved #5 Stage 3 work without waiving the #7 gate.


### 2026-10-04: Dedicated Session Exit Review and Pending First-Thread Capture

The requester assigned continued #7 ownership to a separate session using the
existing clean `codex/task7` checkout at `ead92e3`. Live Issue #7 remains open;
its component-build/pairing scope is unchanged. #5 and its retained compiler/
runner inputs remain independently owned and untouched. Read-only inspection
used the retained failed case and build-8 Wine source; see the incident's
independent exit-path review for findings. Twenty raw streams and 39 captured
producers matched their recorded digests. Available space was approximately
23 GiB at review; no heavy operation or lock acquisition occurred.

Reuse decision: retain the source-matched Wine implementation, original runtime,
existing signed debugger copy, acknowledged detach controller and owned runner.
Do not invent a replacement supervisor or production exit behavior. Read the
pinned Apple `using-metal-validation` skill at revision
`4f42344c90be22112f46becc3fb9687f423f2f88` (plugin reference `1.0.0-beta.1`)
for preservation of pre-device diagnostic settings; no new Metal configuration
or validation execution was performed. No other Apple expert is needed for
this Wine thread/IPC source review.

**Proposal; requester approval pending.** Extend only a new private copy of the
existing LLDB diagnostic controller to capture the first `abort_thread` or
ARM64 `quit_handler` stop in the owned loader. Keep the previous normal-exit and
bad-access stop paths for classification. Require `abort_thread` to resolve in
the selected ntdll image before releasing the existing rendezvous; resolve and
record `quit_handler` where available, otherwise explicitly record its absence.
Capture the breakpoint identity, bounded all-thread stacks, PC/LR/SP/x0-x8/x18,
and module UUIDs with the existing limits. Do not evaluate inferior expressions,
read arbitrary guest memory, suppress signals, or resume repeatedly to seek a
failure. A first thread-exit stop may also be normal teardown; correlate it with
captured phase rows and caller context, and never label the breakpoint alone a
cause. If it completes normally, record the evidence gap and stop the batch.

Before the one Wine case, review and run the existing portable ownership/detach
controls with the controller copy and verify symbol/module resolution. Reuse
the original and debugger bundle byte inventories and current authorization
checks before/after; fail closed on mismatch. Keep one fresh task-owned prefix,
unchanged Metal settings, existing deadlines, acknowledged detach and complete
owned cleanup/sentinel checks. Hold `/private/tmp/pear-native-compilation.lock`
using its established protocol; do not contend with active #5 native work or
steal its lock. Cap additional retained output at 3 GiB and preserve at least
8 GiB free. Preserve failed evidence and all #5 dependencies.

This proposal permits at most one new diagnostic Wine case only after explicit
approval. It authorizes no ordinary retry, new fixture, runtime rebuild/re-sign,
production patch, global setting, qualification waiver, Stage 5 completion or
final PR. The diagnostic still fails ordinary qualification with
`pair_launch_changed`. The existing approved plan/incident/observation locations
hold this review; no official product-document location changes are proposed.


### 2026-10-04: First-Thread Capture Approved

The requester explicitly said to proceed in this dedicated session after the
one-case proposal above. That authorizes the private controller extension and
one diagnostic Wine case; all stated bounds and qualification exclusions remain.
Nine existing portable ownership/detach tests passed with the controller copy.
Installed LLDB found both selected ntdll symbols in an offline module inspection;
actual loaded breakpoint resolution remains a pre-release execution gate. The
first offline helper import refused a hyphenated Python module name; renaming
that private helper resolved the import before any inferior execution.
Reuse the byte-verified prior rendezvous PE fixture without recompiling it.


### 2026-10-04: One First-Thread Capture Completed Normally

The approved single Wine diagnostic completed 39 rows and its zero-error PE
terminal. Both `abort_thread` and `quit_handler` resolved in the exact loaded
ntdll image before release. The first selected stop was instead `exit_process`
called by `NtTerminateProcess` with exit argument zero. No bad access, SIGQUIT
or first-thread-abort stop was captured. This observes normal diagnostic
completion and does not establish the failed formal run's path or exclude an
intermittent thread/IPC defect. The one-case budget is exhausted; do not repeat
this diagnostic merely to seek a failing stack or additional passes.

The original and debugger bundle inventories, strict signatures, current
identity, claims and profile expiry passed before and after. The retained
rendezvous PE was byte-verified and reused without compilation or re-signing.
The shared native lock serialized the case. Acknowledged debugger detach,
Wine/debugger cleanup and sentinel survival passed. The ordinary assessor
retains `pair_launch_changed`. Independent review verified all 20 case streams
and four debugger streams, all 39 row predicates, balanced physical lifetime
and the PE terminal. Captured nonfixture diagnostics were three exact known
fresh-prefix warnings, six API/six GPU notices attributable to registered
processes and one expected rendezvous marker, with no API error or unclassified
line. Shader workload qualification remains unperformed.

A review helper initially refused the known warning because its Python literal
expected single rather than printed doubled path separators. Exact comparison
with the retained earlier warning resolved that review-only error. No runtime
execution or raw record changed. Nine portable ownership controls and installed
LLDB offline APIs/script loading passed; no additional native lifecycle test
was run because ownership/detach implementation and retained controls were
unchanged. New retained output was 1,165,398,016 bytes at postflight and free
space was 19,176,091,648 bytes. Raw diagnostics and the review producer remain
private under `.build/task7/stage5-lldb2/wine-first-thread1`; sanitized receipt
hashes and results are in the Stage 5 observation sidecar.

No production correction, complete Stage 5 report, qualification, final PR or
Issue closure follows. Required unchanged-candidate verification remains failed
at row 33, and the root cause remains unknown. #5 inputs and work are untouched.
