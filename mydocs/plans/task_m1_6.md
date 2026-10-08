# Task #6 Plan — CPU Semantics and the Wine Translation Boundary

GitHub Issue: [#6](https://github.com/postmelee/pear/issues/6)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta
Planning date: October 8, 2026. Status: task plan approved; detailed implementation plan awaiting approval.

## Purpose

Qualify a declared, reproducible set of x64 CPU and Windows-boundary behaviors on
Pear's actual ARM64 Wine/FEX path. Compare defined register, flag, memory and
fault outcomes with native x86-64 or a validated independent reference. Test
ordering and concurrency under the real per-thread policy, and reduce any failure
to the responsible boundary. The result enables #8's relevant translated graphics
qualification; it does not by itself qualify Megabonk.

## Background

[#5](https://github.com/postmelee/pear/issues/5) closed after [PR #37](https://github.com/postmelee/pear/pull/37),
merge `2e0985baafce3d8842bb571bb690218bba42be5c`. Its [final report](../report/task_m1_5_report.md)
records five fresh cold-prefix x64 cases, native refusal and service checks on
macOS 26.5.2 ARM64. CPU conformance, independent-reference comparison and broad
ordering stress remain unperformed. The demonstrated profile has one Context
and up to three participating EC threads; it does not establish a maximum runtime
capacity or excuse a required-path failure.

Read the root, runtime, FEX, tests and documentation rules;
[architecture](../../docs/architecture.md), [delivery plan](../../docs/delivery-plan.md),
[runtime contracts](../../docs/runtime-contracts.md), [FEX development guide](../../docs/development/fex-host.md)
and [reuse review](../../docs/research/platform-reuse.md). Inspected current open
Issues #6/#8–#21 and worktrees: #5 is retained detached for source/tool/runtime
receipts; #7 is completed and retained; no #6 plan or active branch existed.
#8 needs #6/#7; #10 owns full host-image observation; #11 owns actual Steam helpers.

## Scope

### Included

- Declare a finite required corpus with meaningful partial-register, flags,
  SIMD/float, atomics, memory-order, TLS/callback, fault/SEH, guard and executable
  code-change coverage. Enumerate unselected/unsupported features explicitly.
- Reuse suitable upstream assembly bodies and the Madeira ASM-to-PE design, with
  exact source, licenses and independent reference records. Do not invent a new
  CPU engine or replace upstream languages.
- Execute the same selected PE cases on a real x64 reference where practical and
  through the unchanged #5 runtime. Add the smallest missing adapters and fixture
  boundaries; keep absent reference evidence explicitly unavailable.
- Exercise multiple actual translated workers and finite ordering/stress batches;
  record per-thread software-TSO configuration, iteration counts and outcomes.
- Reduce observed failures, fix required Wine/FEX/Darwin integration defects within
  the current architecture, and rerun affected checks. A new owner design or
  larger ABI redesign requires a separately reviewed amendment.
- Declare i386/WoW64 execution unsupported unless actually tested. Identify the
  #11 helper dependency; never use an optional label to waive a known required
  helper or instruction failure.

### Excluded

- Steam login, proprietary game data, gameplay, GPU integration, performance or
  thermal comparison, player UI/installer and general distribution qualification.
- A new translator, Rust/Cranelift conversion, Linux userspace port, security
  bypass, unreviewed native fatal-fault probes or a blanket project license change.
- Exhaustively running every upstream test irrespective of relevance or recreating
  unchanged #5 evidence solely to produce new logs.

## Design Direction

Keep the pinned FEX `59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa` and Wine
`4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf` with #5's exact supplement set as the
initial candidate. Use C/assembly for guest fixtures and Python for small host
orchestration, matching existing code. Reuse current signing, bounded process
supervision, native observation, cleanup and admission functions. New #6 outputs
belong to `.build/task6/`; #5 inputs remain immutable and are referenced by hash,
not copied into another full build. A selected boundary change invalidates its
related evidence and requires revalidation.

| Candidate | Planning decision | Reason and adaptation boundary |
|---|---|---|
| Pinned FEX `unittests/ASM` | Adapt selected test bodies and CONFIG expectations under original MIT notices | Current source contains 2,270 ASM files; 946 have HostFeatures and 2,241 contain RegData. Counts are source inventory, not test results. Golden values alone do not satisfy independent-reference validation |
| Madeira `tests/x64/gen_asmconf.py`, `asmconf-x64.c` at `48f976429c189f8396e23d251d8a82f43c705922` | Adapt the per-test object generation and expected-count model; retain Python/C and applicable GPL-3.0-or-later tooling notices | Reviewed sources skip all HostFeatures, omit flags/MM registers and upper SIMD lanes, and assume fixed scratch/stack addresses. They do not fully implement CONFIG MemoryRegions/MemoryData/Env semantics. Its resumable driver can return zero for an incomplete resumed run; Pear must reject incomplete results |
| FEX native ASM runner and Hangover `56e385b7ff490edd281b288f420677093563560b` | Inspect feature/config/reference and module selection before new equivalents | Linux runner and syscall assumptions cannot directly qualify Windows PE; complete relevant-function review belongs in Stage 1 |
| #5 five x64 and native service fixtures | Reuse unchanged scoped evidence and extend only missing contracts | Exact final receipts and sources re-admitted after merge; no broad repeat. Ordering is not established by a single-thread API pass |
| Native x86-64 reference | Prefer independently recorded Windows x64 PE execution on a native hosted runner; Linux x64 is suitable only for normalized instruction bodies with equivalent setup | Runner availability, actual architecture/features and oracle reproducibility must be checked. No Rosetta reference and no self-comparison with FEX |

Keep optional GPL-derived fixture tooling separate from the runtime patch series,
retain the complete applicable source/license notices, and record the exact
combination before importing. No FEX upstream AI-generated submission. Metal
skills are not applicable to this CPU task; use task-start, stage-report, final-report
and cleanup procedures at their corresponding checkpoints.

The harness must preserve Windows nonvolatile state, initialize scratch and FP
state, capture every required outcome without modifying it, and reject unsupported
CONFIG keys/expectations before execution. Use independent per-case process
isolation where stack/fault behavior makes recovery unsafe. Guest executable
scratch is not permission for native RWX; reuse #5's guest/host memory separation.
No silent feature drops, empty comparisons, resumed skips or missing final records
may produce a passing aggregate. Undefined flags and platform-dependent values
must be excluded by an explicit case contract, not post-failure filtering.

## Document Location Judgment

| File | Classification | Audience | Selected Location | Alternative Location | Reason |
|---|---|---|---|---|---|
| CPU reproduction and coverage guidance | Official technical guide | Contributors/testers | Extend `docs/development/fex-host.md` | New `docs/development/cpu-tests.md` | Existing CPU guide avoids another overlapping page; split only if later justified |
| Upstream adaptation decisions | Official research | Contributors | Existing `docs/research/platform-reuse.md`, only if selection changes | Duplicate research page | Keep exact revision/license decisions in existing source of truth |
| Corpus manifest and third-party notices | Executable fixture metadata | Test tooling/contributors | `tests/cpu/` | `mydocs/` | Source-bound machine-readable test input belongs with fixtures |
| Plans, stage results and final report | Task artifacts | Reviewers | `mydocs/plans/`, `working/`, `report/` | `docs/` | Preserve task evidence without a second product specification |

## Expected Changed Files

New: selected fixtures/manifest/notices and harness regression cases under
`tests/cpu/`; minimal generation/reference/comparison orchestration under
`tools/cpu/`; a native-reference workflow only if needed after runner inspection.
Do not duplicate the runtime or import the whole upstream application.

Modified as required: narrow existing FEX fixture-admission/supervisor adapters;
ordered runtime supplements only for reproduced required defects; the existing
CPU guide and reuse record within the location judgment above. Never alter the
recorded #5 receipts or historical passing reports to qualify changed inputs.

Task artifacts: `mydocs/orders/20261008.md`, this plan,
`mydocs/plans/task_m1_6_impl.md`, `mydocs/working/task_m1_6_stage{N}.md`,
`mydocs/report/task_m1_6_report.md`. Private receipts stay ignored.

## Tentative Stages

1. **Corpus and reference contract:** review selected FEX/Hangover/Madeira functions
   and licenses; select representative required cases; validate CONFIG/setup and
   tool/reference availability; freeze expected comparison and unsupported matrix.
2. **Instruction and ABI comparison:** adapt the generator/capture/PE runner,
   obtain an independent reference, run the declared instruction/SIMD/float and
   Windows-boundary cases on Pear; reduce and fix required failures.
3. **Ordering and lifecycle stress:** execute bounded multiple-worker atomics,
   memory-order and repeated lifecycle/code-change cases under actual per-thread
   policy; add required faults/SEH/guard boundaries not already covered. Fix
   reproduced failures; preserve explicit i386 and feature gaps.
4. **Integrated qualification and handoff:** bind the final corpus/reference and
   relevant results to one candidate, rerun only invalidated checks, document
   reproduction/coverage, and complete the final report for review/publication.

## Verification Plan

### Availability during planning

- #5's final Wine/FEX source trees, receipts and signed runtimes are retained;
  current source/log/output admission passed before #5 publication.
- Native ARM64 Mac and about 50 GiB free observed. Existing LLVM-MinGW tools are
  recorded in #5; NASM is not on the current PATH. Locate a trusted cached/native
  assembler or explicitly prepare a pinned source tool if needed.
- Native x64 hardware/reference runner is not yet verified. The repository's
  Linux GitHub Actions ran #5 portable tests successfully; that does not establish
  a native Windows execution oracle or qualification of any CPU fixture.
- No new fixture, stress test or guest execution was performed during planning.

### Stage Verification

| Stage | Method and expected result | Evidence retained |
|---|---|---|
| 1 | Exact source/license/config review; every selected case has a defined oracle and setup; required unavailable features block their qualification | Corpus hash, source provenance, required/unsupported matrix and reference/tool availability |
| 2 | Compare defined register/flag/memory/fault outcomes against independent native reference; inject one expected-result discrepancy and one missing-result case to ensure rejection | Same fixture identities, host/features, results and minimal failures; no proprietary content |
| 3 | Multiple translated workers, observed thread policy, finite iteration budget and actual outcome counts; do not treat an x86-permitted store-buffer outcome as a failure | Per-thread policy/config identity, litmus contracts, forbidden outcomes, lifecycle outcomes and cleanup |
| 4 | Final relevant corpus passes with explicit unsupported categories; required failures remain blocking; unchanged-input evidence reused | Candidate/reference/corpus hashes, validation report, complete counts and limitations |

### Integrated Verification

- All three #6 Issue criteria are mapped to actual evidence: declared suite,
  real per-thread ordering/stress, and reproducible boundary reductions.
- A FEX test with TSO disabled cannot prove production TSO. Unsupported CPUID
  features are recorded against the actual exposed profile; required paths cannot
  be relabeled optional after failure. Unknown oracle/setup remains unavailable.
- Preserve authorization, owned process cleanup and unrelated sentinel survival
  for host runs. Reuse #5 admission/readers only when their input and claim scope
  match; narrow bridge changes get targeted rejection tests.
- No full Wine/FEX rebuild unless runtime source/tool/config changes require it.
  Serial heavy work; keep source caches, unique failures and current downstream
  artifacts, remove disposable completed prefixes after recorded/live checks.
- Governance/local links, relevant harness tests and `git diff --check` pass;
  worktree is clean before publication. No broad unrelated test reruns.

## Risks

- **Oracle availability:** absence of a native reference blocks comparison claims;
  prepare the hosted/reference route without asking for credentials in chat.
- **Harness distortion:** register/flags clobbering, fixed addresses, invalid test
  stacks and ignored CONFIG fields can cause false success/failure; validate these
  in the smallest representative subset before expanding the corpus.
- **Ordering false confidence:** stress cannot prove every interleaving; record
  policy and forbidden outcomes, avoid synchronization that removes the behavior
  under test, and distinguish finite evidence from universal correctness.
- **Scope and integration:** CPU defects may demand source fixes; retain the current
  architecture and inspect upstream before local protocols. Owner/ABI redesign
  or feature expansion beyond required paths needs an explicit amended plan.
- **Storage and immutable evidence:** #5 still has absolute-path-bound inputs.
  Do not archive/remove its worktree until consumers have migrated and verified.

## Approval Request

Approve this finite CPU/reference/ordering scope, reuse choices, four stages and
existing official document locations. The requester authorized starting #6;
this concrete task plan is newly prepared. Under task-start, approval of this
plan precedes its detailed implementation plan and source changes. Later stage
reports and continuation checkpoints remain in effect. No implementation plan
or new CPU source has been written during this planning step.

## Approval Record

On October 8, 2026, the requester explicitly approved this task plan in this
thread. Scope, reuse direction and document locations are approved. Detailed
implementation planning is authorized; Stage 1 starts after its concrete plan
is approved under the task workflow.
