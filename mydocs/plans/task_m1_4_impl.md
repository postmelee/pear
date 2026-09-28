# Implementation plan: ARM64 Wine host and macOS ABI boundary

Task plan: [task_m1_4.md](task_m1_4.md)

GitHub Issue: [#4](https://github.com/postmelee/pear/issues/4)

Milestone: M1 — Megabonk on Apple Silicon without Rosetta

Work branch: `codex/task4`

Status: proposed on September 29, 2026. The requester approved the task plan and document locations and authorized this detailed planning. Implementation and Stage 1 await approval. All commands below are planned interfaces/work, not completed results; new scripts do not exist yet.

## Stage Overview

| Stage | Title | Main Output | Verification |
|---|---|---|---|
| 1 | Wine inputs and toolchain | Scoped input/configuration/tool records, safe preparation, compiler fixtures | Actual source/tool identities, target features, dependencies and rejection checks |
| 2 | Native build, loader and authorization | ARM64 Wine build, startup/layout patches and local authorized bundle | Native bootstrap, actual child geometry, signatures, process/image evidence and cleanup |
| 3 | PE/API and x18 callbacks | Actual ARM64 PE execution and Wine boundary patches | API results, register/mode restoration, nested callbacks and error exits |
| 4 | Threads, faults and exception contexts | Thread/signal/exception and memory tests/patches | TLS, finite SEH/context, page/guard semantics, executable memory and suspend/resume |
| 5 | Mac-driver boundary | Native window/message fixture and driver ABI handoff | Real event callback/re-entry, main-thread ownership and repeated teardown |
| 6 | Fresh reproduction and handoff | Rebuilt tested component and contributor guide | Matching inputs, explained output differences, repeated suite and Issue acceptance map |

Each stage uses the approved task plan's [specifications and scoped rules](task_m1_4.md#background). Preserve Wine's implementation languages and reuse its actual host paths. The Pear Apple-tooling skill remains **Not applicable**: this task does not perform Metal rendering, validation, captures or shader compilation. Linking the SDK Metal framework required by the Mac driver does not itself add graphics qualification work.

## Document Location Check

| File | Planned Location in Task Plan | Stage Artifact Path | Match | Notes |
|---|---|---|---|---|
| Contributor instructions | `docs/development/wine-host.md` | Same | OK | Start with experimental input/build instructions; add verified execution evidence by stage. |
| Scoped build records and patches | `runtime/wine/` | `inputs.json`, `toolchain.json`, `build-config.json`, `patches/series.json`, ordered patch files | OK | Component-only provenance; not a new full-runtime contract or replacement audit. |
| Implementation rules | `runtime/AGENTS.md` | Same | OK | Add with Stage 1's real build inputs; preserve existing contracts/source ownership. |
| Build and evidence tools | `tools/wine/` | Python helpers listed by stage | OK | Use standard library unless an exact reviewed dependency becomes necessary. |
| Fixtures and tests | `tests/wine/` | `fixtures/`, `cases.json`, `test_*.py` | OK | Redistributable source; generated PE/Mach-O files remain ignored. |
| Official links/follow-ups | `docs/README.md`, `docs/source-qualification.md`, `docs/research/macos-runtime-audit.md` | Same | OK | Narrow dated links in Stage 6; preserve historical decisions. |
| Task history | `mydocs/plans/`, `working/`, `report/`, `orders/` | `task_m1_4*` artifacts and active-date boards | OK | Sanitized execution evidence accompanies each stage report. |

No change to #1's manifest/evidence, #2's code/evidence, #3's schemas, manuals or roadmap is included. `.build/` already excludes task output; alter `.gitignore` only if an actual approved output path needs it.

## Shared Implementation Decisions

### Input, target and tool identity

- Adopt Wine commit `4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf`, tree `10b47b2965a7b3e1e9694ec506a3d13525211892`, as this component's starting base. Preserve the original #1 inventory SHA-256 `535cdcb7b2e76d4bc536d63ad7d17d31f562f438b7850a75a0ace1b9c88466b8` and its `blocked` decision. The comparison Wine/DXMT source and incompatible historical export patch are not build inputs.
- `inputs.json` records version/kind/scope, exact audit reference, selected source and dependency identities, acquisition/digest scopes, terms, configuration coverage and named unresolved requirements. `toolchain.json` records actual selected tool versions, native targets, source/artifact URLs and hashes, recipe identities and capability-check results. `build-config.json` records named variants, compiler roles, SDK/deployment settings, enabled/disabled features and tool argument arrays. `patches/series.json` records the ordered patch bytes, base/result identity, provenance, rationale and regression IDs; start with an empty series.
- These are Wine-scoped build records. Separate input completeness, tool capability, build completion, authorization and execution outcomes. A data-format match or boolean assertion does not authorize a build/run. Required unknown, failed or unavailable observations fail the requested gate; successful acquisition does not resolve an unimplemented port. No new global `source_ready` result is emitted.
- Use SHA-256 of exact stored JSON/patch/artifact bytes, and the existing explicit Git object/tree-listing scopes. Do not invent values or embed self-referential digests. Bind every result to the exact consumed records and output bytes. Changed patches/settings invalidate affected results.

| Variant/check | Native host | PE targets and role | Required #4 evidence |
|---|---|---|---|
| `arm64` | ARM64 macOS | `--enable-archs=aarch64` | Clean build and all executable #4 fixtures |
| `arm64ec-build` | ARM64 macOS | `--enable-archs=aarch64,arm64ec`; auxiliary x86_64 PE compiler required by configure | Build/module/import/export inventory and consistency with the tested host patches; translator-dependent execution remains unqualified |
| Compiler-only x64/i386 controls | ARM64 tools | Compile/link small x64 and i386 PE inputs | Correct PE machine type and explicit no-execution/unsupported boundary; no Intel Mach-O runtime |

The companion variant retains aarch64 because Wine bootstrap helpers such as wineboot, services and RPCSS default to the host architecture. ARM64EC-only is not assumed to be a self-contained runtime. Required PE/host modules and excluded optional features must be listed; no silent omission when a compiler feature test fails. The final Stage 6 handoff identifies which exact variant and modules later #5/#7 may integrate; any unexecuted combination still requires integration tests.

### Planning observations and acquisition policy

Read-only September 29 observations confirm an ARM64 host, macOS 26.5.2 (25F84), Xcode 26.6 (17F113), SDK 26.5 and about 20 GiB available disk space. PATH contains make, Bison, Flex, Autoconf, pkg-config and Python. CMake, Ninja, lld, llvm-dlltool and LLVM-MinGW target clang wrappers were not found on that PATH; this is not a whole-disk absence claim. #1 recorded Bison 2.3, below Wine's >=3.0 requirement, and Apple clang 21.0.0. Actual #4 compilation and current signing authorization are not checked.

Stage 1 must select exact usable tool inputs before executing them. Prefer an inspectable public native ARM64 tool artifact when available within the storage budget, recording release/source provenance, downloaded-byte hashes, contained tools/terms and host architecture. Availability is not assumed. The audited LLVM-MinGW/LLVM/MinGW source pins in the task plan are the source-build candidates; an alternative compiler baseline that changes the approved ABI assumptions requires review. A public tool binary is a build dependency, not permission to introduce an opaque play-time Wine/FEX component.

For missing Bison and other build prerequisites, choose exact official source/artifact versions and complete dependency identities during Stage 1, record the choice before use, inspect scripts and use task-local installation paths. Do not guess release hashes or run global package installation/upgrade. The chosen versions must pass the feature checks below. Existing Apple SDK/tools remain identified external prerequisites; do not claim an independently rebuilt Apple toolchain.

Inspect the pinned LLVM-MinGW scripts before choosing commands. Do not execute `release-macos.sh`: its output deletion and default universal ARM64/Intel build do not match this task. Do not blindly invoke `build-all.sh`: unquoted prefix handling does not establish support for the checkout path containing spaces. Use reviewed, quoted argument arrays or a small recorded adapter for the needed targets. No user-directory cleanup or replacement is part of tool acquisition.

Estimate unpacked source, tools, build objects and retained reproduction outputs before heavy work. Record the estimate and available space, build with at most four jobs initially, and do not launch two large builds concurrently. If the required route does not fit, preserve current data and report the concrete space/tool-input gap; do not delete unrelated files, silently reduce acceptance or switch to an unproven compiler.

### Isolation, records and commands

- All task-managed inputs, builds, bundles, prefixes and raw records use fresh named directories under `.build/task4/`. Copy/materialize selected #1 source objects into a separate workspace; never build in or mutate original audit caches. Refuse an occupied destination unless it is an explicitly verified task-owned resume with matching input identities.
- Wine additionally creates an OS temporary server namespace for the owned prefix. In the selected source it is derived from `/tmp/.wine-<uid>/server-<prefix-device>-<prefix-inode>`; `TMPDIR` alone does not relocate it. Track that exact namespace and ownership. Never remove the shared `/tmp/.wine-<uid>` parent or another prefix's entries.
- Use absolute resolved tool paths, argument arrays, a scoped environment and isolated library/pkg-config discovery. Reject unexpected Intel Mach-O dependencies, outside-root source/output aliases, path traversal and substitution of commercial Wine binaries. A universal tool/library needs evidence of the selected native slice; prefer ARM64-only produced host artifacts.
- `tools/wine/common.py` owns bounded record parsing, exact-byte identity and error serialization. Reject duplicate JSON keys, unsupported record versions, invalid hashes, mismatched input/configuration identities and absent required facts. Proposed CLI outcomes: 0 = requested gate passed, 1 = invalid input/operation failure, 2 = usage error, 3 = valid observation but requested qualification gate unmet. Retain actual subprocess/OS codes separately.
- `tools/wine/verify.py` assesses inputs, toolchain, build or run records using named expected checks. It must not trust self-asserted success. `tools/wine/evidence.py` exports allowlisted sanitized observations and referenced hashes to `mydocs/working/task_m1_4_stage{N}_observations.json`; raw paths, PIDs, environments, certificates, profiles and logs stay ignored. Public fault addresses use owned-region offsets or module/RVA references, and public processes use run-local role/sequence identifiers; do not expose device/team identifiers. Failed attempts are retained and linked, not replaced by a later success.
- Build commands may take substantial time; record the full local command/configuration and stream bounded progress without filling memory. Enforce a preflight storage budget and record interruption/failure. Correctness fixture deadlines below are safety bounds for test processes, not a promised development schedule.

## Stage 1 — Wine Inputs and Toolchain

### Artifacts

- `runtime/AGENTS.md`; `runtime/wine/inputs.json`, `toolchain.json`, `build-config.json`, `patches/series.json`.
- `tools/wine/common.py`, `prepare.py`, `toolchain.py`, `verify.py`, `evidence.py`.
- `tests/wine/fixtures/toolchain_native.c`, `toolchain_pe.c`, `toolchain_seh.S`, and `toolchain_cpp.cpp`; `test_inputs.py`, `test_preparation.py`, `test_toolchain.py`.
- `docs/development/wine-host.md`, initially limited to input/tool setup and explicit unimplemented runtime gates.

### Changes

1. Inspect the complete selected Wine build paths and freeze the two variant configurations. Include dependencies sufficient for the Stage 5 Mac driver, not only a console executable. Record SDK frameworks, headers, link libraries and optional features with reasons. The pinned driver links AppKit, Carbon, Foundation, IOKit, Metal, OpenGL, QuartzCore and Security; win32u also uses CoreText/AppKit and conditional FreeType/Fontconfig. The SDK Metal framework is distinct from offline Metal shader tools. Decide and test actual font dependencies rather than assuming CoreText replaces FreeType; a fixture without font-rendering coverage must state that limit. Supported disable candidates include X11, Wayland, Vulkan, GStreamer, FFmpeg, Fontconfig and, for these non-network fixtures, GnuTLS. Record the final exact flags and exclusions after source inspection, without removing required host/PE components.
2. Recheck the audited source bytes and materialize a clean working source tree. Acquire any additional public tool/dependency inputs by exact recorded identity. Inspect archive paths, symlinks, expansion size and executable scripts before extraction/use. Reject malformed or mismatched inputs rather than updating expected hashes to fit them.
3. Prepare the native compiler/cross-tool closure and compile/link target fixtures. Verify ARM64 Mach-O, ARM64 PE, ARM64EC PE, x64 PE and i386 PE headers as applicable; exercise PE linker/import/export/resource/SEH support and C++17 feature requirements from `configure.ac`. Run only the ordinary native ARM64 compiler fixture; do not execute PE files, Wine or restricted capabilities in Stage 1.
4. Test compiler discovery and configure/generated-make handling of the actual checkout/tool paths, including spaces; Python argv quoting alone is insufficient for upstream shell scripts. Reject an unverified path adapter or tool substitution. Account for actual configure dependencies and use tracked `configure` initially. If a later patch changes `configure.ac`, record exact Autoconf regeneration and generated-file provenance. SDK/tool availability does not count as a successful Wine configure/build.
5. Preserve upstream notices and review terms for each selected tool/dependency and planned payload. Portable tests cover wrong commits/digests/targets, ambiguous tools, duplicate fields, escaping archives/paths, existing destinations, polluted discovery paths and unverified component promotion. Do not simulate actual x18 execution with fake authorization.

### Verification

Planned commands run from the task worktree; initial inspection may produce an explicit unmet gate until exact tool entries are filled and validated:

```sh
python3 tools/wine/toolchain.py inspect --output .build/task4/tool-inspection.json
python3 tools/wine/prepare.py --inputs runtime/wine/inputs.json --source-cache .build/task1-sources/inputs --output .build/task4/inputs --require-empty
python3 tools/wine/toolchain.py prepare --lock runtime/wine/toolchain.json --output .build/task4/tools --require-empty
python3 tools/wine/toolchain.py check --lock runtime/wine/toolchain.json --inputs .build/task4/inputs --config runtime/wine/build-config.json --tools .build/task4/tools --fixtures tests/wine/fixtures --output .build/task4/toolchain-check.json
python3 tools/wine/verify.py inputs --inputs runtime/wine/inputs.json --config runtime/wine/build-config.json --toolchain .build/task4/toolchain-check.json --require-complete
python3 -m unittest discover -s tests/wine -p 'test_*.py'
python3 tools/check_governance.py
git diff --check
```

Completion requires real selected source/tool identities, passing compiler/target feature checks, the declared native/PE dependency and terms matrix, meaningful rejection tests, and a reproducible local setup. Required missing tools or incomplete dependencies cannot pass Stage 1. Retain prepared source/tool hashes, actual commands/versions, feature results and unavailable/failed attempts. Wine port requirements remain explicit later-stage gates, not falsely resolved input fields.

### Commit

`Task #4 Stage 1: qualify Wine inputs and native cross-toolchain`

## Stage 2 — Native Build, Loader and Authorization

### Artifacts

- `tools/wine/build.py`, `signing.py`, `run_fixtures.py`; extend verification/evidence helpers.
- `runtime/wine/patches/0001-darwin-loader-layout.patch` and `0002-native-bootstrap-evidence.patch`, with actual series metadata; filenames describe intended concerns, not existing patches.
- `tests/wine/fixtures/bootstrap_native.c`, `sentinel.c`, `cases.json`, `test_build.py`, `test_signing.py`, `test_runner.py`.
- Stage 2 additions to the contributor guide: actual configuration, build, bundle/permission and controlled bootstrap instructions.

### Changes

1. Build both declared variants from the same ordered patch base in separate output directories. Treat the prepared base inputs as read-only; materialize a fresh source copy for each build and verify/apply the current recorded patch series there. Refuse stale patch/input identities rather than reusing a previous stage's patched source silently. `build.py` expands only the recorded variant and resolved tools into configure/make invocations; preserve `config.log`, exact arguments and enabled/omitted modules. Install into task-local staging, never system locations. No opportunistic external library discovery.

   The initial configure invocation is a source-supported candidate, not a successful build result: from an empty variant directory run the verified tracked Wine `configure` with `--prefix=<task-local-install>`, `--enable-archs=aarch64` (or `aarch64,arm64ec`) and `--with-mingw=<verified-cross-tools>/bin/clang`, plus the exact recorded feature flags. Keep native ARM64 `CC`/`CXX` separate from PE tools. Run the verified make with bounded jobs, then task-local `make install`. Do not use a Windows `--host` triplet for the macOS host or `--enable-win64` as an ARM64 selector. Outer calls use argument arrays, but that alone does not make Wine's internal shell/make expansion safe for paths containing spaces: the pinned configure logic splits compiler command strings. Stage 1 must test the selected configure/generated-make tool-path handling. Prefer verified tool names under a strictly controlled PATH where appropriate, or a reviewed task-owned path adapter/arrangement; record both invoked and resolved tool identities and do not move/delete user data. These fully expanded arguments and any configure regeneration are retained in the build record.

2. Adapt actual Darwin loader paths and link layout for the measured host configuration. Selected `configure.ac` has a 4 KiB PAGEZERO and does not select the legacy preloader for AArch64; reconcile this with the proven 64 KiB null guard and emulation layout. Inspect `dlls/ntdll/unix/loader.c` spawn/exec and `process.c` double-fork/loader calls. Implement requested child page mode for every relevant route, with errors retained and no default-mode fallback.
3. Add a narrow diagnostic hook that stops at native Wine bootstrap before PE entry. It reports its own executable/slice/translation query, page geometry, mappings and actual selected native modules. Required hooks may supply a minimal safe transition prerequisite; do not enter foreign mode merely to reach a logging function. Review Wine's native main-thread/initialization-thread ownership.
4. Establish real per-executable signing before restricted execution. `signing.py inspect` maps each actual executable and native dependency to needed claims, App ID/profile/certificate/device checks and packaging layout. Borrow pure validation logic from #2 only with recorded provenance; do not copy its single-probe `_variant()` as a Wine signing solution. Existing probe authorization is not a Wine authorization. Request a concrete missing profile only after producing this requirement map; passwords/private keys never enter chat or Git.
5. Sign task-local copies inside out with actual matching development authorization and required claims only; verify effective claims and strict signatures separately from profile authorization. Keep Hardened Runtime and normal system protections. If the selected JIT path uses `pthread_jit_write_protect_np`, do not also enable `jit-write-allowlist`. Do not default to disabling library validation or broad entitlements to make loading work. Signed bytes and their unsigned origins are recorded separately.
6. Start the selected built `wineserver -f` as a directly owned foreground child. Confirm readiness through the actual selected server/prefix handshake, not socket existence or a fixed sleep. Prevent unnoticed fallback to an unowned server and verify server/prefix generation identities. Control bootstrap/re-exec processes with explicit executable/parent/generation and prefix ownership; do not assume process groups include every detached Wine child.
7. For every fixture run, use a new synthetic prefix and nonce, allowlisted environment, no inherited authentication state and stdin closed. Initial bounds: bootstrap 120 seconds, ordinary fixture 30 seconds, GUI fixture 60 seconds; stdout and stderr each 256 KiB, evidence events at most 2 MiB. On completion/error, request bounded owned shutdown (3 seconds), then terminate verified owned identities (2 seconds), escalate if necessary (5 seconds), drain pipes (1 second) and record reaping/observation gaps. Any refused cleanup or surviving owned process fails the run. Never signal based only on a process name or stale PID; an unrelated sentinel must survive. An intentional timeout control uses a separate declared short deadline.

### Verification

```sh
python3 tools/wine/build.py --variant arm64 --inputs .build/task4/inputs --tools .build/task4/tools --output .build/task4/build-arm64 --jobs 4
python3 tools/wine/build.py --variant arm64ec-build --inputs .build/task4/inputs --tools .build/task4/tools --output .build/task4/build-arm64ec --jobs 4
python3 tools/wine/verify.py build --root .build/task4/build-arm64 --companion .build/task4/build-arm64ec --require-complete
python3 tools/wine/signing.py inspect --build .build/task4/build-arm64 --output .build/task4/signing-requirements.json
python3 tools/wine/signing.py prepare --build .build/task4/build-arm64 --local-input .build/task4/private/signing.json --output .build/task4/signed --require-empty
python3 tools/wine/run_fixtures.py --suite bootstrap --runtime .build/task4/signed --output .build/task4/runs-stage2 --require-empty
python3 tools/wine/verify.py runs --root .build/task4/runs-stage2 --suite bootstrap --require-complete
python3 -m unittest discover -s tests/wine -p 'test_*.py'
git diff --check
```

The signing preparation/execution commands are conditional on a passing actual authorization gate. The local input file contains only local references to matched signing inputs; public examples do not contain real identifiers. Its creation follows the concrete signing-requirements inspection.

Required bootstrap observations: every tested native process runs ARM64 with its own untranslated evidence; unknown/denied queries fail coverage. Inspect actual mapped images, relevant PE output machine types, null guard, owned low mappings and child re-execution. Require 4 KiB user/16 KiB kernel geometry for the declared guest-host loader/process roles; pure native server/helpers record their expected per-role geometry and need no extra grant solely to force them into a guest page mode. Capture the produced binaries and dynamic dependency closure, and verify deliberate wrong-slice, missing mode-setter, denied-signing, wrong-prefix-server, spawn/timeout/output-limit and cleanup failure controls. Non-runtime tests may inject failures; actual restricted calls never run under simulated grants. A native bootstrap success is not yet PE/API success.

### Commit

`Task #4 Stage 2: build the authorized ARM64 Wine host and loader`

## Stage 3 — PE/API Execution and x18 Callbacks

### Artifacts

- `runtime/wine/patches/0003-darwin-x18-transitions.patch`; update the input/series records with actual bytes and tests.
- `tests/wine/fixtures/api_pe.c`, `abi_pe.c`, `abi_native.c`, `abi_gateway.S`; case definitions and `test_abi.py`.
- Extend build/runner/verification helpers and the guide for real PE/API execution.

### Changes

1. Add self-owned ARM64 PE fixtures for entry/exit code, basic Windows API results, allocation/TLS access and a child-process round trip. Bind expected values to fixture inputs and reviewed Wine/Windows ABI behavior. Include Unicode/space argument and allowlisted-environment round trips, owned-file write/read/hash, missing-file errors and deterministic nonzero exits. Compile controls for x64/i386, but do not execute translator-dependent instructions to test a missing translator.
2. Integrate x18 handling in the actual Wine thread entry, Unix dispatcher, return and callback paths (starting with `signal_arm64.c` and relevant loader/callback code). Save guest TEB/x18 before switching out, call normal C/POSIX/framework code only in host mode, then restore foreign mode/state in the permitted order. Resolve required APIs safely before foreign windows. Inspect compiler prologues, stack/register ABI and disassembly.
3. Exercise a genuine Wine guest-to-native boundary and a native-to-guest callback that nests the same transition. Use a bounded test bridge through the selected Wine boundary, not a standalone copy of #2's demonstration. Start from the selected `KeUserModeCallback`, `NtCallbackReturn`, `__wine_syscall_dispatcher` and `__wine_unix_call_dispatcher` paths. Record the exact entry function/export, ownership and calling convention in the fixture metadata; an invented FFI adapter that bypasses Wine cannot qualify the boundary.
4. Run 64 round trips and 32 nested callbacks per declared mode, with 16 deterministic injected error returns. Assert the real expected per-thread TEB/x18 identity at each guest return, distinct nested-frame/callee-saved sentinels, expected callback counts/results and restored host mode. Do not replace x18 with an arbitrary sentinel before calling Wine APIs: actual ARM64 PE code needs its TEB pointer. Include `NtCallbackReturn` outside an active callback returning `STATUS_NO_CALLBACK_ACTIVE`, following the pinned upstream exception test. These are correctness repetitions, not statistical performance samples.
5. Verify that absent emulator modules/unsupported guest targets are rejected explicitly before execution; inspect the selected Wine emulator lookup/module names for #5 without providing a fake FEX implementation or choosing Intel Wine.

### Verification

```sh
python3 tools/wine/build.py --variant arm64 --inputs .build/task4/inputs --tools .build/task4/tools --output .build/task4/build-stage3 --jobs 4
python3 tools/wine/signing.py prepare --build .build/task4/build-stage3 --local-input .build/task4/private/signing.json --output .build/task4/signed-stage3 --require-empty
python3 tools/wine/run_fixtures.py --suite api-abi --runtime .build/task4/signed-stage3 --output .build/task4/runs-stage3 --require-empty
python3 tools/wine/verify.py runs --root .build/task4/runs-stage3 --suite api-abi --require-complete
python3 -m unittest discover -s tests/wine -p 'test_*.py'
git diff --check
```

Rerun the affected bootstrap checks on these new bytes. Every expected PE/API and transition result, per-process evidence and owned cleanup must pass. Retain exact machine code/disassembly around patched boundaries, input/binary hashes and outcome counts. Fake setter calls must never authorize x18-writing instructions. Changed patches invalidate earlier binary-bound results; retain rather than overwrite those records.

### Commit

`Task #4 Stage 3: validate Wine PE entry and nested x18 transitions`

## Stage 4 — Threads, Faults and Exception Contexts

### Artifacts

- `runtime/wine/patches/0004-darwin-threads-signals-memory.patch`, split into additional ordered patches if separate fixes improve review without changing scope.
- `tests/wine/fixtures/threads_pe.c`, `memory_pe.c`, `exceptions_pe.c`, `signal_native.c`; case definitions and `test_exception_evidence.py`.
- Targeted runner/evidence/guide updates.

### Changes

- Run two actual Wine-created workers with distinct TLS/TEB state and synchronized entry/exit; include a native-created callback thread if required by the selected boundary. Verify initialization before guest code and restoration/joins after error paths. Any needed compatibility-policy requests are explicit per thread with raw status; accepted requests are not an independent getter or universal TSO evidence.
- Test software `RaiseException` plus a deliberate controlled access fault through Wine's exception machinery. Assert exception code/access kind, fault address relative to the owned region, a labeled fault instruction/RVA, register context, handler ordering and a declared recovery label/exit. An unrelated crash cannot satisfy the expectation. Separately deliver a controlled asynchronous signal during a verified guest window and during host mode, checking the captured guest state, safe handler host mode and resumption. Do not equate SIGUSR1 with complete SEH/unwind coverage.
- Exercise actual Windows reserve/commit/protect/decommit/recommit on an owned three-page region: only the middle 4 KiB changes, neighboring sentinels remain intact, re-commit reads zero before writing, and protection/guard faults match declared outcomes. Verify first guard handling and subsequent access according to the fixture's Windows semantics.
- Test fixed owned ARM64 executable bytes returning 42, publish through `VirtualProtect`/`FlushInstructionCache`, change the code to return 84 under the declared write/execute protocol, republish and execute through the selected Wine path. Keep immutable PE mapping, dynamic executable memory and FEX's future JIT lifetime distinct. Record required permissions and unsupported operations instead of relaxing protections.
- Add one handshake-controlled suspend/resume case with explicit target thread/context checks; avoid arbitrary asynchronous suspension of unrelated host threads. Bound all fault/timeout trials and verify server/child cleanup after both recoverable and terminating faults.

### Verification

```sh
python3 tools/wine/build.py --variant arm64 --inputs .build/task4/inputs --tools .build/task4/tools --output .build/task4/build-stage4 --jobs 4
python3 tools/wine/signing.py prepare --build .build/task4/build-stage4 --local-input .build/task4/private/signing.json --output .build/task4/signed-stage4 --require-empty
python3 tools/wine/run_fixtures.py --suite threads-memory-exceptions --runtime .build/task4/signed-stage4 --output .build/task4/runs-stage4 --require-empty
python3 tools/wine/verify.py runs --root .build/task4/runs-stage4 --suite threads-memory-exceptions --require-complete
python3 -m unittest discover -s tests/wine -p 'test_*.py'
git diff --check
```

Rerun affected Stage 2/3 cases against the new build. All specified observations and expected fault assessments must pass; a matched negative control preserves its original failure/status. Record untested SEH/unwind forms and translated-state semantics explicitly. No native Windows reference execution is currently available; expected synthetic values and source/ABI-derived semantics must be documented, with any ambiguous behavior resolved before calling its test accepted. Do not claim differential Windows or x64 correctness.

### Commit

`Task #4 Stage 4: verify Wine thread memory and exception boundaries`

## Stage 5 — Mac-driver Boundary

### Artifacts

- `runtime/wine/patches/0005-darwin-mac-driver-boundary.patch` only if an actual failing case requires a fix; no empty patch to match a filename.
- `tests/wine/fixtures/window_pe.c`, relevant case definitions and `test_window_evidence.py`.
- Driver ABI/ownership and #7 handoff section in the approved contributor guide.

### Changes

- Use the real `winemac.drv` and local graphical session to create a minimal Win32 window, deliver a deterministic application message, invoke a guest callback that re-enters the native path, and close/destroy it. Repeat create/message/destroy 20 times, checking counts, return values, thread ownership and resources. A guest-only `SendMessage` loop is insufficient: observe the actual Cocoa/event boundary and assert no late callback after teardown. Do not introduce Metal rendering or screenshot assertions as a substitute for event behavior.
- Preserve AppKit main-thread/run-loop ownership and Wine's initialization-thread design. Inspect/fix only needed driver boundary code and attribute any reused upstream changes.
- Record precise relevant source types, function signatures, calling convention, object lifetime and view ownership for #7. Keep the DXMT view-structure mismatch and individual export versus function-table integration unresolved until #7 tests the actual pair. Window success is not DXMT/D3D success.

### Verification

```sh
python3 tools/wine/build.py --variant arm64 --inputs .build/task4/inputs --tools .build/task4/tools --output .build/task4/build-stage5 --jobs 4
python3 tools/wine/signing.py prepare --build .build/task4/build-stage5 --local-input .build/task4/private/signing.json --output .build/task4/signed-stage5 --require-empty
python3 tools/wine/run_fixtures.py --suite mac-driver --runtime .build/task4/signed-stage5 --output .build/task4/runs-stage5 --require-empty
python3 tools/wine/verify.py runs --root .build/task4/runs-stage5 --suite mac-driver --require-complete
python3 -m unittest discover -s tests/wine -p 'test_*.py'
git diff --check
```

A missing graphical session is unavailable, not a passed test; repeat in the declared authorized local session. Inspect actual native driver/framework images and observations, message/re-entry results and cleanup. Rerun affected ABI/thread tests after driver fixes. Preserve normal user's windows and applications.

### Commit

`Task #4 Stage 5: validate the native Wine Mac-driver callback boundary`

## Stage 6 — Fresh Reproduction and Handoff

### Artifacts

- `tools/wine/reproduce.py`; final scoped input/tool/configuration/patch records and contributor guide.
- Narrow evidence links in the approved existing official documents.
- `mydocs/working/task_m1_4_stage6_observations.json` and final acceptance mapping in `mydocs/report/task_m1_4_report.md`.

### Changes

Reconstruct both variant builds from the original pinned sources and final ordered patches into empty directories, using verified local input caches or exact reacquisition. Do not copy previous built Wine libraries into the new outputs. Recheck source/dependency/tool identities and runtime build variants; any required configuration not reproduced remains unmet. Recreate signatures from the actual authorization and run all executable suites on the final native ARM64 variant. Compile/inspect the companion ARM64EC variant with the same final patches; it remains translator-unqualified.

Compare unsigned bytes and explain differences such as recorded build paths/timestamps with evidence; signed bytes are separate identities. Do not require or imply identical signatures. Storage preflight must accommodate retained earlier evidence and a second output; a space gap cannot be solved by silently deleting the earlier comparison inputs.

Map #4's three Issue criteria to actual passing evidence. Provide #5 exact Wine module/export/Unix-call, thread/exception and unresolved translator requirements; #7 driver ABI/ownership and unresolved renderer pairing; #10 bounded observation limitations; #13 build/signing/distribution limits. Preserve #1's blocked aggregate and #2's finite original results. No final runtime lock or game compatibility claim is manufactured from these component records.

### Verification

```sh
python3 tools/wine/reproduce.py --inputs runtime/wine/inputs.json --toolchain runtime/wine/toolchain.json --config runtime/wine/build-config.json --source-cache .build/task1-sources/inputs --tools .build/task4/tools --local-signing .build/task4/private/signing.json --output .build/task4/reproduction --require-empty
python3 tools/wine/verify.py reproduction --root .build/task4/reproduction --require-complete
python3 -m unittest discover -s tests/wine -p 'test_*.py'
python3 tools/check_governance.py
git diff --check
git status --short
```

Reproduction requires all named native suites, complete bounded process/image observations and cleanup against the same final artifact/configuration. A dependency tool cache may be reused only after identity verification and must be identified as reused; this is Wine rebuild reproduction, not a repeated source build of every external compiler or a second Mac. Preserve remaining independent-tester/clean-machine and distribution gaps. Review public output for private paths/identifiers, profile material and proprietary content before committing sanitized evidence.

### Commit

`Task #4 Stage 6: reproduce the Wine host and document integration handoff`

## Verification and Commits

- Every stage commit bundles its verified artifacts with `mydocs/working/task_m1_4_stage{N}.md` and sanitized observations. Commands, actual outcomes, source/tool/output identities, signing scope and unresolved checks belong in those records. Update the active-date board without altering another task's rows.
- Portable unit tests exercise real rejection/lifecycle semantics and evidence interpretation; hardware tests execute the actual Wine path. Mocks do not qualify restricted behavior. Do not test exact documentation wording or substitute an unrelated probe for Wine execution.
- A build that compiles but fails required runtime checks remains incomplete. Preserve failed artifacts/logs and fix within the approved stage; scope expansion needs an amended plan and requester approval. No stage advance on unavailable required checks.
- Final report approval and PR publication remain separate from Stage 6 verification. Use the existing final-report workflow when all stages pass; do not close #4 from this plan or from a partial host build.

## Stage Dependencies

Stage 1 begins only after this implementation plan and Stage 1 execution are approved. Stage 2 requires Stage 1's closed inputs/tools and approved report. Stage 3 requires real native bootstrap/permissions; Stage 4 requires passing PE/ABI behavior; Stage 5 requires the necessary thread/callback foundation. Stage 6 rebuilds the final combined changes. Each transition retains requester approval.

Within an approved stage, read-only investigation, independent fixture authoring and patch review may run in parallel. One task owner controls shared records, patches, the board and commits; large builds and live ABI tests are serialized on this Mac. #5/#7 and #9/#10 implementation are not authorized by this plan.

## Risks and Responses

- **Limited storage/tool availability:** approximately 20 GiB was free during planning. Inspect actual artifacts and estimate peak disk use before extraction/build; select a verified compact tool route if available. Report a concrete deficit rather than deleting user files or assuming a full LLVM build fits.
- **Unusable upstream automation/path handling:** review each executed recipe and quoted path, especially LLVM-MinGW release/build scripts. Keep intentional adapter changes attributable; never run a script with broader deletion/install effects just because it is upstream.
- **Signing/package mismatch:** a probe profile and a successful signature do not authorize Wine. Produce per-executable requirements first, validate actual grants and keep failures explicit. General-user distribution remains outside #4.
- **Mode, exception and lifecycle bugs:** simple ARM64 execution can conceal lost x18, a wrong child page mode, stale-server reuse or escaping helpers. Require genuine boundary observations, deterministic fault cases, owned identity checks and cleanup/sentinel tests.
- **Configuration or evidence overclaim:** optional configure failures, skipped GUI checks and an unexecuted ARM64EC build must remain visible. Only the declared tested combination passes its scoped gate; no x64, graphics, game or global source-readiness promotion follows.

## Approval Request

- Approve the six detailed stages, artifact paths, target matrix, dependency acquisition rules, verification commands and commit messages within the approved task-plan scope.
- Authorize **Stage 1 only**: scoped records/tools/fixtures and contributor instructions, public source/tool acquisition into isolated directories, needed task-local tool builds and compiler feature checks. No Wine PE execution or restricted-capability trial occurs in Stage 1.
- Retain later stage/report checkpoints, the actual Wine signing-input gate, and the exclusions for FEX/DXMT integration, Steam/game work, general distribution and unrelated repository changes.
