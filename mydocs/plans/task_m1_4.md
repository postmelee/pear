# Task #4 — ARM64 Wine host and macOS ABI boundary

GitHub Issue: [#4](https://github.com/postmelee/pear/issues/4)

Milestone: M1 — Megabonk on Apple Silicon without Rosetta

Planning date: September 29, 2026

Status: the requester approved this task plan and its document locations on September 29, 2026. The implementation plan and Stage 1 were subsequently approved. [Stage 1 is complete](../working/task_m1_4_stage1.md); the requester approved its report and Stage 2. [Stage 2 is complete](../working/task_m1_4_stage2.md); its report and Stage 3 were approved on September 29, 2026. [Stage 3 is complete](../working/task_m1_4_stage3.md); Stage 4 requires requester approval. The [executable-memory design amendment](task_m1_4_impl.md#approved-stage-3-amendment-native-pe-code-publication) was approved for implementation on September 29, 2026. The technical statements below preserve the original task-planning context.

## Purpose

Build a source-derived ARM64 macOS Wine host and demonstrate minimal Windows PE/API fixtures through its actual loader, thread, exception and native-callback boundaries under normal macOS protections. Preserve attributable patches and enough build, signing and execution evidence for the FEX and DXMT integration tasks to use the result.

This is the Wine contribution to the first runtime milestone. A passing native Wine fixture does not establish x64 translation, Steam, Megabonk, ordinary-user installation or the complete G1 runtime gate. The intended end-user goal remains unchanged.

## Background

The requester explicitly started #4 after the prerequisite investigations and contracts were merged. The work branch is `codex/task4`, based on `master` commit `1f229dab08e30afb01080e7664240e317e5df2ef`. A free worktree retains #1's ignored public-source cache; reuse the checkout while preserving those original audit inputs.

Applicable context:

- [Root rules](../../AGENTS.md), [host rules](../../host/AGENTS.md), [test rules](../../tests/AGENTS.md), [documentation rules](../../docs/AGENTS.md), and the [task workflow](../manual/task_workflow_guide.md).
- [Architecture](../../docs/architecture.md), [delivery plan](../../docs/delivery-plan.md), and the dated [macOS runtime audit](../../docs/research/macos-runtime-audit.md).
- [#1 source qualification](../../docs/source-qualification.md), its [inventory](../../runtime/sources/manifest.json), and [final report](../report/task_m1_1_report.md).
- [#2 host capability guide](../../docs/host-capabilities.md) and [final report](../report/task_m1_2_report.md).
- [#3 runtime contracts](../../docs/runtime-contracts.md), including the difference between a source reference, an approval decision, an artifact and qualification.

The #1 investigation is complete with `decision: blocked` and `source_ready: false`. Its reproduced public inputs are reusable evidence, not an executable dependency closure. Wine loader/layout, x18 entry, thread/signal handling, toolchain selection and configured dependency closure still require work. Its historical Mac-driver export patch fails on both selected Wine source candidates.

The #2 host gate passed on M4 Pro/macOS 26.5.2 (25F84), with SDK 26.5, a validated development profile granting cross-architecture support, an emulation layout with a protected 64 KiB PAGEZERO, and requested 4 KiB user pages. Kernel pages remain 16 KiB. Those finite probes do not prove Wine's layout, Windows SEH, arbitrary native callbacks, or permission for a different executable. The probe App ID/profile is not automatically transferable to Wine or its helpers.

## Scope

### Included

- Select and record the Wine build input/configuration boundary, using audited public source as the starting point; resolve the source, tools, enabled dependencies and terms required for that boundary.
- Build native ARM64 host tools, loader, server and required host libraries, with the applicable native ARM64 PE and ARM64EC/WoW64 build variants and matching tools explicitly distinguished.
- Implement or adapt attributable Wine patches for necessary Darwin loader/layout, process launch, x18 transitions, thread/signal/exception handling and basic Mac-driver operation.
- Verify real signing/provisioning authorization for each executable that needs restricted capabilities, before running the affected operation.
- Exercise redistributable PE/API fixtures, nested host/guest callbacks, thread entry/exit, controlled error/fault paths and exception-context capture in the actual Wine host.
- Record bounded process and native-library architecture/translation evidence for these fixtures, with unknown observation coverage preventing a no-Rosetta claim.
- Rebuild from fresh source/output directories and rerun the declared suite; publish contributor instructions, sanitized evidence and the remaining #5/#7 integration obligations.

### Excluded

- FEX's Darwin services, translated x64/x86 execution and CPU semantic qualification (#5/#6); a Windows PE target in a build is not evidence that it can execute.
- DXMT, D3D11/Metal rendering and its complete private Wine-driver interface (#7/#8). Basic Cocoa window/message callbacks are included only to qualify the Wine host boundary.
- Production manager/observer implementation (#9/#10), Steam/game execution (#11/#12), general runtime release packaging (#13), game performance, app UI, and ordinary-user distribution.
- Rust rewrites, a new translator, VM architecture changes, commercial runtime binaries, upstream patch submission, and changes to the established roadmap or runtime-contract schemas.
- Promotion of the combined #1 inventory to `go` or modification of its historical evidence. No new global source-readiness claim is part of #4.

## Design Direction

### Source selection and build scope

Use Wine upstream commit `4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf` (tree `10b47b2965a7b3e1e9694ec506a3d13525211892`) as the proposed port base. The audited Wine/DXMT-interface commit `87ba10bb3aa8ea636dff5c2030b376da1627910a` is a comparison source, not a drop-in runtime. Do not apply the incompatible historical export patch or mix the bases without a reviewed, attributable change.

Create a Wine-scoped input/build record under `runtime/wine/`, linking the exact #1 inventory bytes and relevant requirements. Record every selected source, tool, configuration, dependency, patch order/hash, output role and unresolved gate. This record is a component build record, not a second game/runtime contract or an executable full-runtime lock. It can demonstrate resolution of named Wine gaps using new evidence while the combined #1 decision remains blocked. Preserve the original inventory and evidence byte-for-byte.

Preparation and experimental port builds may investigate missing behavior. Positive build acceptance requires the inputs for that actual configuration to be closed and the required port behavior to pass. A smaller configuration must declare its exclusions; it cannot satisfy an omitted Issue requirement or silently become the complete runtime. Separate build readiness, execution permission and fixture qualification.

Select a native ARM64 build toolchain and Windows cross-compiler with verified feature support. The audited LLVM-MinGW build-source commit `030097eeee87fcfd0f3bfe536b21cbd6e5d3b324`, LLVM commit `6dfe1677ab8dffbc6ec13d53a1e0215d75147689`, and MinGW-w64 commit `9f55f4a2d3b9783dab76d9808be3d6279b99ec2a` are candidates, not proven installed tools. Source-build required tools where necessary; record any alternative artifact's exact provenance and terms. Resolve Wine's Bison >=3.0 requirement rather than using the previously observed 2.3. Record make and PE linker/resource/assembly-tool support explicitly. CMake/Ninja may be needed to build the selected LLVM tools; they are not intrinsic Wine requirements. Do not install FEX/DXMT-only dependencies just to complete a tool checklist. The selected enabled dependencies must support the later Mac-driver window fixture, not only a console build.

Use separate ignored `.build/task4/` source, tool, build, signed-artifact, prefix and raw-evidence directories. Do not build in #1's original bare repositories or overwrite retained caches. Use explicit tool paths and isolated discovery settings so a commercial CrossOver installation, Intel library or unrelated prefix cannot silently supply a dependency. Record bounded build parallelism, available storage and resource use without assuming an installed compiler is compatible.

### Reuse, languages and attributable patches

Retain Wine's existing C, assembly, Objective-C and build machinery. Reuse its ARM64/ARM64EC, Apple signal-context and Mac-driver paths before adding replacement code. Use small Python/build helpers where needed for preparation and evidence, following the existing source and host tools. #3's Rust choice applies to the future manager; it is not a reason to rewrite Wine.

Keep ordered, reviewable port patches under `runtime/wine/patches/`, with base identity, rationale, attribution, relevant tests and applicable notices. Review enabled dependencies and corresponding-source obligations for the produced development payload. Wine's audited LGPL-2.1-or-later terms do not blanket-license all dependencies or establish a Pear-wide license. Upstream contribution rules must be reviewed before any separately authorized submission.

Reuse #2's authorization checks, assembly reasoning and isolation techniques only after adapting their assumptions to Wine's actual process model. Avoid turning the fixed host probe into a production launcher. Add scoped runtime build/patch rules alongside the implementation; preserve existing host tests and their historical claims.

Technical guidance: the pinned Wine source and #2's SDK/host evidence are the initial authorities, rechecked for the actual build. The Pear Apple-tooling skill is **Not applicable** to this host-only task: no Metal validation, GPU capture, drawable presentation or metal-cpp work is planned. A need for those operations belongs to the separately reviewed graphics scope.

### Native and guest ABI boundaries

The first executable fixtures are native ARM64 Windows PE programs using Wine's Windows APIs. At the pinned source, `--enable-archs=aarch64` is the initial configuration candidate; it has not been built or verified. Adding `arm64ec` also probes an auxiliary x86_64 PE compiler when x86_64 is not explicitly selected; this does not automatically add x86_64 to the PE output architecture list (`configure.ac`, architecture/tool checks). Record separately which ARM64EC, x64 and i386 PE modules are built and which need #5's translator to run. Match required Wine-generated tools to the Wine source. A missing translator must yield an explicit unsupported/rejected result, never select Intel macOS Wine.

Treat x18 as an execution-mode boundary: preserve foreign register state, switch to the permitted host mode before normal macOS/C/POSIX work, and restore state in the correct order for return, nested callbacks, asynchronous entry and error paths. Redundant mode setters and state loss are correctness bugs. Review compiler-generated prologues and assembly, not just source-level wrapper calls. Test actual Wine transitions; copied standalone probe success is insufficient.

Reconcile Wine's reservations and PAGEZERO with the measured host configuration. Verify actual parent/child page geometry, image mappings, null guard, owned low-address reservations and independent 4 KiB protection/decommit/recommit behavior. A 64 KiB PAGEZERO is a guard/layout choice, not a 64 KiB page-size claim. A successful spawn-attribute setter alone does not prove the child received the requested mode. The selected source has spawn, exec and double-fork paths in `dlls/ntdll/unix/loader.c` and `process.c`; inspect each relevant re-execution/child path. An external wrapper's initial settings cannot establish later Wine-created children's configuration. AArch64 does not select the legacy Mac preloader in this source, so port the actual loader path rather than assuming that preloader is used.

Verify Windows thread setup/TLS, native callback thread entry, controlled signals/faults, context capture and restoration, executable-memory protection/cache visibility, guard-page behavior, and a bounded suspend/resume case. Any per-thread compatibility policy needed by the selected host path must be initialized explicitly and retain raw errors; do not infer inheritance or an independently observed policy state from a setter. Translated instruction state, FEX JIT lifetime and full x86 memory ordering remain #5/#6 obligations.

For the Mac driver, preserve native main-thread/run-loop ownership and Wine initialization-thread behavior, and test a minimal Win32 window, message delivery, a callback that re-enters the guest, and clean teardown. Record the relevant ABI types, ownership and calling conventions for #7. Do not declare DXMT compatibility from matching symbol names; its `cocoa_view`/`client_cocoa_view` versus `client_view`/`rects` mismatch requires its own integration evidence.

### Signing, execution and evidence

Before restricted Wine execution, identify the real bundle/executable layout, App ID, profile/device/certificate match and effective grants for every affected process. Helpers do not inherit their parent's authorization automatically. Reuse existing signing material only when its actual authorization matches; otherwise prepare the exact missing configuration and request that input. Keep SIP, Gatekeeper and other platform protections enabled. Development execution and ordinary-user distribution remain separate results.

Use fresh synthetic prefixes and owned fixture processes. Preserve deadlines, bounded logs, process-generation/ownership checks, cleanup and unrelated-process survival. Wine's server/child lifecycle needs an explicit containment and shutdown design; a direct-child harness alone may miss detached helpers. Do not invoke broad process-name termination or touch live Steam prefixes.

Bind observations to source/patch/tool identities, actual output hashes, signature configuration, host/OS and fixture identity. Distinguish Mach-O ARM64 execution from guest PE architecture, inspect actual loaded native images and collect process-local translation observations where required. A launcher's `sysctl.proc_translated` result does not cover its children. This is a bounded #4 harness, not a replacement for #10's full runtime observer.

Retain original errors, failed cases and unperformed checks. Publish only allowlisted, sanitized evidence; private profiles, identifiers, authenticated prefixes, saves, raw diagnostics and game files stay outside Git. Correctness instrumentation does not support performance comparisons.

## Document Location Judgment

`docs/` is already the approved official root. This task proposes one reusable Wine build/host guide and narrow links; task history remains in `mydocs/`. No operating-manual or roadmap rewrite is proposed.

| File | Classification | Audience | Selected Location | Alternative Location | Reason |
|---|---|---|---|---|---|
| `docs/development/wine-host.md` | Official experimental contributor guide with reproducible build, signing, fixture and limitation instructions | Wine/runtime contributors | `docs/development/wine-host.md` | `mydocs/manual/`, `runtime/wine/README.md` | Keeps reusable technical instructions in the official root, distinct from workflow and one-time reports. |
| Wine input/build records, patch metadata and scoped rules | Machine-readable build provenance and implementation-local constraints | Build tools, port maintainers and reviewers | `runtime/wine/`, `runtime/AGENTS.md` | `runtime/sources/manifest.json`, `docs/` | Keeps new component build facts adjacent to attributable patches without rewriting the completed #1 audit or duplicating #3 contracts. |
| `docs/README.md`, narrow follow-ups in `docs/source-qualification.md` and `docs/research/macos-runtime-audit.md` | Existing official index, source guide and dated research | Contributors and maintainers | Existing paths | New overview or roadmap copy | Links actual #4 evidence while preserving old decisions, dates and unresolved combined-runtime gates. |
| Plans, reports and sanitized stage evidence | Issue-specific work artifacts | Requester, reviewers and agents | `mydocs/plans/`, `mydocs/working/`, `mydocs/report/` | `docs/` | Preserves approvals and execution history without making them a competing specification. |

## Expected Changed Files

New; exact filenames and interfaces will be fixed in the implementation plan:

- `runtime/wine/` — scoped source/configuration/tool input records, patch series and patch provenance.
- `runtime/AGENTS.md` — scoped rules introduced with the runtime build/port implementation.
- `tools/wine/` — preparation, build, local signing preflight and bounded fixture/evidence helpers.
- `tests/wine/` — redistributable PE/native fixtures and meaningful build, ABI, lifecycle and failure tests.
- `docs/development/wine-host.md` — contributor guide.

Modified only as needed and after reading the current content:

- `docs/README.md`, `docs/source-qualification.md`, `docs/research/macos-runtime-audit.md` — narrow evidence links/follow-ups.
- `.gitignore` — only if the existing `.build/` exclusion is insufficient for new generated/private outputs.

Do not change #1's inventory/evidence, #2's probe source/evidence, #3's schemas, unrelated operating manuals or existing Steam experiments. If a shared implementation change becomes necessary, record the concrete need and obtain a scope amendment before editing it.

Task artifacts:

- `mydocs/orders/20260929.md` and subsequent active-date board entries as required.
- `mydocs/plans/task_m1_4.md`.
- `mydocs/plans/task_m1_4_impl.md`, only after task-plan approval.
- `mydocs/working/task_m1_4_stage{N}.md` and sanitized evidence sidecars using the same milestone/Issue prefix.
- `mydocs/report/task_m1_4_report.md`.

## Tentative Stages

1. **Stage 1 — Wine inputs and toolchain**
   - Close the scoped source/configuration/terms inventory; prepare isolated inputs and required native build/cross tools; define the host/PE variant matrix.
   - Verify source identities, patch applicability, compiler output targets and dependency discovery; retain unresolved port requirements explicitly.
2. **Stage 2 — Native host build, loader and permission path**
   - Build the ARM64 host components and required PE variants; implement necessary Darwin startup/layout changes and actual signing preflight.
   - Verify output architecture/dependencies, authorized native bootstrap and parent/child page/address observations. This stage targets bootstrap before PE execution; if that path needs a minimal safe x18 gateway, include and verify that prerequisite here. Full PE/API and nested-callback acceptance remains Stage 3.
3. **Stage 3 — PE/API execution and x18 callbacks**
   - Run small ARM64 PE/API fixtures; implement and audit actual guest/host transitions, nested callbacks and injected error returns.
   - Assert expected Windows results, register/mode preservation and explicit refusal of an unavailable translator path.
4. **Stage 4 — Threads, faults and exception contexts**
   - Integrate Wine thread/TLS and asynchronous signal/exception paths, bounded guard/protection and suspend/resume coverage.
   - Check fault identity/context, restoration, cleanup and failures without inferring translated x64 correctness.
5. **Stage 5 — Mac-driver boundary**
   - Bring up a minimal window/message/callback fixture on the native driver; record the ABI and ownership handoff for #7.
   - Verify nested host/guest event delivery and repeated create/destroy cleanup without claiming D3D/Metal rendering support.
6. **Stage 6 — Fresh reproduction and handoff**
   - Recreate source/output directories, rebuild and rerun the suite using the documented inputs and actual signing route.
   - Map every #4 acceptance criterion to evidence and finalize contributor instructions and remaining #5/#7/#10/#13 obligations.

Stages are tentative, with no implied schedule. The implementation plan must make each stage a bounded reviewable cycle. If a port needs more work than its approved scope, propose a concrete subdivision or amendment before expanding it. A failed acceptance check remains unresolved; stage completion requires its planned verification to pass. Complete, report and commit each stage before requesting approval for the next.

## Verification Plan

### Planning-time availability

| Requirement | Observation and remaining verification |
|---|---|
| Host and Apple tools | Read-only checks on September 29 confirm `arm64`, macOS 26.5.2 (25F84), Xcode 26.6 (17F113), SDK 26.5. M4 Pro is the #2 recorded host. Wine compilation is not checked. |
| Source identities and caches | #1 manifest pins and retained public cache are available; Stage 1 will revalidate selected bytes before copying/building. No new acquisition/build is claimed by this plan. |
| Build/cross tools | #1 observed Apple clang 21, ld 1267, Autoconf 2.73, Flex 2.6.4 and incompatible Bison 2.3. Required cross-tool compatibility and configured dependency closure are not checked for #4; missing tools must receive exact pins/provenance. |
| Restricted execution | #2's development route passed for its probe. Current profile validity and authorization for the actual Wine executables are not checked; inspect at the restricted-execution gate. |
| GUI/reference environments | Local graphical session, ARM64 PE references and applicable upstream tests must be selected in the implementation plan. Native Windows comparison and a second Mac are not currently established. No such execution is claimed. |

### Stage Verification

| Stage | Method and expected result | Evidence to retain |
|---|---|---|
| 1 | Verify selected source/tool identities; compile/inspect small native and PE toolchain fixtures; reject mismatched pins, wrong host architecture and incomplete configured dependencies. Audit enabled features and terms. | Scoped input/target matrix, source and tool identities, configuration and rejection results; unresolved port list. |
| 2 | Build from isolated inputs; inspect Mach-O/PE outputs and loaded native dependencies; validate real per-executable authorization; observe Wine native bootstrap, child mode and address geometry. Verify any minimal transition needed to reach that boundary; do not claim PE/API acceptance here. | Expanded build commands/log digests, patch order, binary inventory, sanitized signing checks and in-process observations. |
| 3 | Run deterministic PE/API calls, host/native callbacks with nested re-entry, and injected errors; inspect entry assembly and verify registers/modes. Test unavailable-translator refusal. | Fixture source/hash, expected result rationale, per-case outputs, actual host image/translation evidence, failure classifications. |
| 4 | Exercise new threads/TLS, controlled asynchronous entry, deliberate faults, Windows exception-context capture, executable-memory protection/cache visibility, guard/protection and a finite suspend/resume case. Assert restoration and owned-process cleanup. | Fault type/PC/register assertions, thread outcomes, raw OS error domain/code, exact execution/cleanup results and explicit untested cases. |
| 5 | Create a window, exchange deterministic messages through the Mac-driver boundary, re-enter the guest from a callback and destroy/repeat. | Event/callback trace, ABI type/ownership review, loaded host-image evidence and resource/process cleanup. |
| 6 | Fresh source/output reconstruction and repeat of applicable checks. Compare unsigned payload identities or explain nondeterminism separately from signing; preserve earlier outputs. | Reproduction commands, input and result comparison, source/build/fixture acceptance map, contributor guide review. |

Only Wine-relevant existing regression suites are rerun when shared behavior is affected. Documentation verification uses `python3 tools/check_governance.py` plus review of task-document links and `git diff --check`. Do not add tests that merely assert plan wording. Exact execution commands, fixture count, deadlines and expected failure controls belong in the separately approved implementation plan.

### Integrated Verification

- **Issue criterion 1:** the declared ARM64 Wine build can be recreated from its complete selected inputs, and minimal PE/API fixtures execute under documented normal permissions. All required #4 build variants and host components are accounted for; omissions prevent completion.
- **Issue criterion 2:** every port patch has a base, ordered bytes, rationale, attribution and regression evidence; exact build commands and tool/dependency identities are recorded. Every required host process/image for the bounded suite has native execution evidence. Unknown coverage cannot pass; no Intel host fallback is accepted.
- **Issue criterion 3:** actual Wine thread entry, nested callbacks, error exits and exception-context capture pass targeted tests, with the finite scope and remaining translator/graphics obligations explicit.
- Relevant #1 Wine input gaps are resolved by the new scoped evidence and #2 prerequisites are rechecked in Wine. The old blocked aggregate is preserved, and no game/runtime/distribution status is promoted automatically by schema validation or successful compilation.
- Fresh-directory reproduction passes on the declared host. Same-host rebuilding is not represented as independent-tester, clean-machine or ordinary-user distribution evidence.
- Generated payloads, raw/private diagnostics and signing material remain excluded. The task's tracked paths are clean before PR preparation; `git diff --check` passes. Preserve unrelated files rather than deleting/staging them to obtain a clean status.

## Risks

- **Port size and source gaps:** upstream contains useful ARM64/Darwin code but no complete validated Pear port. Minimize named failures against pinned inputs, maintain attributable patches and amend stage scope when necessary; do not substitute opaque binaries.
- **Toolchain/ABI mismatch:** native compiler success does not qualify ARM64EC or required Wine-generated tools. Verify actual targets/features and all enabled dependencies; keep build-only tools distinct from play-time host requirements.
- **Authorization:** a probe's grant may not fit Wine's process/package layout. Resolve actual grants before restricted execution; do not disable protections or relabel denial as success. Ordinary-user distribution remains a separate risk.
- **Asynchronous state corruption:** mode transitions, compiler-generated code, callbacks, signals and unwinding can lose state even when a simple launch works. Require actual boundary tests, assembly review and retained failure evidence before downstream acceptance.
- **Memory assumptions:** page mode, loader reservations, null guard and Windows 4 KiB semantics are related but distinct. Verify each in the actual parent/child configuration and preserve rejected alternatives.
- **Dependency and lifecycle drift:** a build can accidentally discover Intel libraries or a fixture can leave Wine server helpers alive. Use isolated discovery/prefixes, explicit architecture evidence and owned-process cleanup; preserve unrelated applications.
- **Premature acceptance:** #1 closure, #2 probes, an ARM64 launcher or a successful window cannot establish the full runtime. Keep the Wine scope and remaining #5/#7 integration gates explicit in every handoff.

## Approval Request

- Approve the #4 scope, six tentative stages and Wine upstream starting base, retaining existing implementation languages and the stated downstream boundaries.
- Approve the proposed documentation and artifact locations, including `docs/development/wine-host.md`, `runtime/wine/`, `tools/wine/` and `tests/wine/`.
- Approve a separate Wine-scoped build record that resolves named inputs/ports through new evidence while preserving #1's original blocked inventory and all historical results.

After task-plan approval, `task_m1_4_impl.md` will specify the exact stage artifacts, build/verification commands, signing prerequisites and commit messages for a separate implementation-plan review. This draft does not approve implementation or restricted Wine execution.

## Approval Record

On September 29, 2026, the requester explicitly approved this plan, its six stages and document locations, and proceeding with detailed implementation planning. This authorizes preparation of `task_m1_4_impl.md`. That implementation plan and Stage 1 execution retain their separate review checkpoint; no source implementation or restricted Wine execution is authorized by this approval alone.
