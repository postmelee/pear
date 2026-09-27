# Task Plan: Probe macOS ABI, memory, JIT and signing capabilities

Status: task plan approved by the maintainer on September 27, 2026. The approved review copy was prepared before source changes; this repository record preserves its scope. Implementation details and stage results are recorded separately.

GitHub Issue: [#2](https://github.com/postmelee/pear/issues/2)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta

## Purpose

Establish which macOS host facilities the proposed ARM64 Wine/FEX runtime can actually use on the declared Mac/OS under normal security protections. Deliver a reproducible native diagnostic and isolated probe harness, followed by authorized signed ABI/memory/JIT tests, with explicit passing, failed, and unavailable outcomes.

Keep developer execution separate from general end-user distribution. Passing this task does not establish Wine/FEX integration, Megabonk compatibility, a consumer release, or a performance advantage.

## Background

The existing game experiment uses Rosetta. The published architecture identifies x18 ABI transitions, Windows page semantics, low mappings, per-thread memory-order behavior, executable-memory publication, and signing/provisioning as host gates before a direct macOS runtime can be qualified. SDK declarations and a vendor demonstration do not prove that Pear has the needed implementation or permissions.

References are the existing [runtime architecture](https://github.com/postmelee/pear/blob/master/docs/architecture.md), [host audit](https://github.com/postmelee/pear/blob/master/docs/research/macos-runtime-audit.md), [delivery plan](https://github.com/postmelee/pear/blob/master/docs/delivery-plan.md), and #2 acceptance criteria. Source qualification in #1 and manager-language/contracts evaluation in #3 are independent workstreams; this task supplies host evidence to later Wine and FEX integration.

The recorded development baseline is M4 Pro with macOS 26.5.2. The current inspection reports Apple Clang 21, SDK 26.5, Swift 6.3.3, and Rust 1.94.1. These are observed inputs, not approved release toolchain pins. Zero valid signing identities were visible in the current inspection context. A denied sysctl query in the tool sandbox is an unavailable observation, not proof that the host lacks the queried capability or that an Apple account is absent.

## Scope

### Included

- A small C-based ARM64 diagnostic and subprocess harness; isolated assembly thunks only where required to test the ABI accurately.
- OS/toolchain/process architecture, runtime API availability, process-local translation state, page geometry, signature metadata, and capability result records with privacy-conscious output.
- Isolation, timeouts, controlled fault reporting, and clean child termination so a failing probe does not crash the supervisor or affect unrelated processes.
- Separate tests for low mappings, 4 KiB process/page behavior, protection/decommit semantics, JIT publication and cache invalidation, x18 state transitions, callbacks/signals, and per-thread memory-order policy.
- Authorized signed execution with normal macOS protections, and a clear statement of what has or has not been established for ordinary-user distribution.
- Contributor-facing build/run/evidence documentation and task reports in English.

### Excluded

- Wine/FEX/DXMT implementation, Steam login, proprietary game execution, the launcher UI, and automatic save recovery.
- Selecting Rust or Swift for the manager; C here follows the host ABI being measured.
- Broad claims that all M-series Macs or all macOS versions work.
- Security-policy changes, invented entitlements, copying commercial runtime binaries, or treating ad-hoc signing as authorization for restricted capabilities.
- Collection of Apple credentials, private signing keys, Steam credentials, personal saves, or private diagnostic files into Git.

## Design Direction

- Start with a native diagnostic that can make useful observations without restricted capability transitions. Each result identifies its process, test version, observed value, status, and reason; missing permissions remain unavailable.
- Execute state-changing, faulting, or potentially aborting tests in disposable child processes. Distinguish a correct rejected request from a passing positive capability test. Restrict termination to children started by this harness.
- Keep x18 foreign-mode code separate from normal C/macOS calls. No logging, allocation, POSIX, or framework call may accidentally execute while foreign ABI mode is active. Preserve guest state across mode changes, and validate nesting/error paths with explicit fixtures.
- Treat JIT code-cache allocation separately from guest PE image/memory allocation. A successful aligned allocation does not prove 4 KiB protection or decommit behavior; a successful API call does not prove the required memory semantics.
- Record signing/provisioning context without private material. Obtain and verify any required identity/profile through the ordinary platform process before the signed capability stage. Do not reinterpret absence in the current keychain/sandbox as a universal platform denial.
- Keep this harness independent of Steam and game files, and retain clear interfaces so its eventual results can inform #3 without defining an unrelated launcher-wide schema here.
- Preserve the existing technical milestone's distinction: developer execution can qualify M1 if all its prerequisites pass; proposed M2/U01 must separately establish ordinary-user distribution. A failed required host test keeps #2 open.

## Document Location Judgment

This location decision was approved with the task plan. Existing `README.md` already links the current `docs/` architecture and research; reusing that root avoids moving established references. This draft does not select a documentation root during Hyper-Waterfall adoption.

| File | Classification | Audience | Selected Location | Alternative Location | Reason |
|---|---|---|---|---|---|
| `docs/host-capabilities.md` | Proposed official contributor guide; only validated outcomes become normative | Runtime contributors and testers | `docs/host-capabilities.md` | `host/probe/README.md` | Keep host prerequisites, execution instructions, evidence interpretation, and limitations beside the architecture that depends on them. |
| Existing host audit and documentation index | Published technical research/index; preserve historical observation dates | Contributors and maintainers | `docs/research/macos-runtime-audit.md`, `docs/README.md` | `mydocs/tech/` | Add a narrow link or dated qualification update when warranted; do not relocate or rewrite historical findings. |
| Task plans and execution reports | Work artifacts; not a public compatibility promise | Task requester, contributors, and agents | `mydocs/plans/`, `mydocs/working/`, `mydocs/report/` | `docs/` | Preserve per-Issue decisions and progress separately from reusable contributor instructions. |

## Expected Changed Files

New, to be detailed in the implementation plan:

- `host/probe/` — C diagnostic, isolated probe modules, narrowly scoped assembly where necessary, and build definition.
- `tests/host/` — redistributable harness/failure fixtures and semantic result checks.
- `docs/host-capabilities.md` — contributor instructions and explicit capability/distribution status.

Modified only as needed:

- `docs/README.md` — link the new contributor guide.
- `docs/research/macos-runtime-audit.md` — preserve historical research and link dated implementation evidence.
- `.gitignore` — exclude generated probe binaries and local/private results if new paths require it; preserve existing user files.

Task artifacts:

- `mydocs/orders/20260927.md`
- `mydocs/plans/task_m1_2.md`
- `mydocs/plans/task_m1_2_impl.md` — created only after approval of this task plan.
- `mydocs/working/task_m1_2_stage{N}.md`
- `mydocs/report/task_m1_2_report.md`

## Tentative Stages

- **Stage 1 — Native host diagnostics and result contract**
  - Build the minimal ARM64 C diagnostic and record available host, SDK, process, and signature observations.
  - Verify that denied queries, missing APIs, and absent identity observations cannot be mistaken for positive capability results.
- **Stage 2 — Isolated harness and baseline memory/JIT probes**
  - Add child isolation, bounded execution, exit/signal reporting, deterministic success/failure fixtures, and baseline memory/JIT probes that are valid in the available context.
  - Verify containment, failure classification, low-mapping observations, protection behavior, and generated-code visibility without using unsigned baseline success to claim restricted ABI permissions.
- **Stage 3 — Authorized signing and process capability tests**
  - Establish the actual supported identity/profile/entitlement route, validate signatures, and run the required signed process/page/JIT cases under normal protections.
  - Record the exact authorization prerequisite if this stage is unavailable; do not proceed to dependent positive ABI qualification on an unqualified context.
- **Stage 4 — ABI, callback, signal, and thread correctness**
  - Exercise x18 state preservation, nested guest/host transitions, error exits, callback/signal entry, and the selected per-thread memory-order policy in the qualified signed context.
  - Verify required semantics and failure handling. Record a returned success code separately from behavioral evidence; explain bounded test coverage and remaining integration obligations.
- **Stage 5 — Reproduction and capability decision**
  - Repeat the documented probe suite from a clean build, consolidate sanitized evidence, and publish the contributor guide and task report.
  - Decide whether every #2 prerequisite for the stated M1 configuration passes; document the separate ordinary-user distribution status and unresolved requirements without closing a failed gate.

## Verification Plan

### Stage Verification

- Stage 1
  - Inspect compiled Mach-O slices and execute the diagnostic natively. Confirm each observation describes its own process and context; sandbox-denied queries remain unavailable.
- Stage 2
  - Exercise controlled success, nonzero exit, signal termination, timeout, and malformed/missing child output. Check that the parent remains responsive and no unrelated process is signaled. Verify actual memory/JIT behavior, not just declared header availability.
- Stage 3
  - Inspect signature/provisioning metadata and platform execution results for the exact artifact. Compare applicable baseline and authorized signed cases while system protections remain enabled. Record 4 KiB mapping/protection/decommit and JIT evidence separately.
- Stage 4
  - Use deterministic ABI state fixtures for nested calls, callbacks, signals, and error exits. Confirm host calls occur in host mode and thread initialization follows the chosen policy for every relevant test thread.
- Stage 5
  - Rebuild and rerun from the documented source/toolchain, compare outcomes, validate redaction and report completeness, and map each #2 acceptance criterion to passing evidence or an explicit unresolved item.

### Integrated Verification

- Required host capability tests pass for the declared M1 configuration through a documented authorized execution path, or #2 remains incomplete with the exact unmet prerequisite recorded.
- Diagnostic availability, successful compilation, successful developer execution, and ordinary-user distribution are distinct outcomes; none is inferred from another.
- Results identify source/test revision, toolchain, Mac/OS, process architecture, signing context, commands, expected/actual behavior, and coverage limits without secrets.
- Reproducibility and source inspection do not launch Steam, modify the existing experimental prefix, or access game files.
- The task's committed paths are clean before PR preparation. Existing unrelated untracked `analysis/` and `research/` content is recorded and preserved; an empty global `git status --short` is not achieved by deleting or committing those files.
- `git diff --check` passes without warnings.

## Risks

- **Source and permission feasibility:** #1 may reveal missing runtime patches, and a required identity/profile may not be available. Keep independent probe preparation useful, but do not claim a successful runtime or mark missing prerequisites as passed.
- **Unsafe ABI transitions:** a stray host call in foreign x18 mode can abort or corrupt state. Use narrow audited thunks, explicit state handling, and disposable children before broad integration.
- **Misleading observation context:** sandbox restrictions, API return values, header declarations, and the supervisor's translation state can be mistaken for host-wide evidence. Report scope and unknowns explicitly.
- **Behavior beyond finite tests:** passing bounded callback/memory-order cases does not prove Wine/FEX correctness. Later integration and CPU suites remain required.
- **Distribution mismatch:** development execution may work while ordinary-user execution does not. Keep M1 and M2/U01 decisions separate and surface this risk early.
- **Privacy and signing material:** logs or identity output may contain personal information. Store raw results locally and review/redact evidence before publication; never request private keys or credentials in chat.

## Approved Scope

- The approved bounded #2 scope, C diagnostic/isolated harness direction, five tentative stages, and separation of baseline observations, authorized ABI execution, and ordinary-user distribution.
- The approved use of existing `docs/` for reusable contributor instructions and `mydocs/` for Issue-specific work artifacts, without moving existing research.
- Retain the listed exclusions and evidence gates; no Wine/FEX/game or general-release success is implied by approving this plan.

The maintainer explicitly approved this plan together with merging the framework adoption PR. `task_m1_2_impl.md` records concrete artifacts and verification commands. This task plan does not claim implementation or passing capability results.
