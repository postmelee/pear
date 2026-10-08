# Task #6 Implementation Plan — CPU Boundary Qualification

Task plan: [task_m1_6.md](task_m1_6.md), approved October 8, 2026.
GitHub Issue: [#6](https://github.com/postmelee/pear/issues/6)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta
Status: implementation plan approved; Stages 1–3 completed locally; Stage 4 awaits explicit continuation.

## Stage Overview

| Stage | Title | Main Output | Verification |
|---|---|---|---|
| 1 | Corpus and independent-reference contract | Source-bound case manifest, provenance and explicit coverage/oracle matrix | Exact source/config/license checks and meaningful manifest refusal tests |
| 2 | Instruction and ABI comparison | Adapted ASM/PE harness and native reference results | Same-fixture native x64 versus actual Pear outcomes; false-pass controls |
| 3 | Ordering and lifecycle stress | Actual translated-worker ordering and boundary records | Thread policy, bounded litmus/outcome counts, required lifecycle behavior |
| 4 | Integrated qualification | Final coverage record and contributor recipe | One candidate/corpus/reference identity; affected checks pass; gaps explicit |

Read the approved task plan and its linked rules/specifications. #5's exact final
candidate and its limited evidence are the starting point. No engine language
change or new owner design is planned. Root/runtime/tests/docs rules remain in
force. Use Hyper-Waterfall v0.3.0 stage-report and todo procedures at each stage
boundary. Metal expertise is not applicable to this CPU work.

## Document Location Check

| File | Approved Location | Stage Artifact Path | Match | Notes |
|---|---|---|---|---|
| Corpus/provenance/notices | `tests/cpu/` | `tests/cpu/corpus.json`, `sources.json`, `LICENSES/` | OK | Executable metadata; import notices with selected upstream material |
| CPU contributor recipe | Existing CPU guide | `docs/development/fex-host.md` | OK | Update after actual qualification |
| Changed upstream selection | Existing reuse record | `docs/research/platform-reuse.md` | OK | Only if the Stage 1 review changes a decision |
| Stage observations/reports | `mydocs/working/` | `task_m1_6_stage{N}.md` and sanitized JSON where needed | OK | No raw logs in Git |
| Final report | `mydocs/report/` | `task_m1_6_report.md` | OK | Scope and residual failures explicit |

## Stage 1 — Corpus and Independent-reference Contract

### Artifacts

- `tests/cpu/sources.json`: repository/revision/file digests, copyright/license
  references and adopt/adapt/reject decisions for selected upstream material.
- `tests/cpu/corpus.json`: stable case IDs, category, source/config digest,
  setup/initial state, required outcome masks, feature/profile requirements,
  reference route and required/unsupported status with reasons.
- `tools/cpu/corpus.py`: bounded source/config inventory and manifest validation;
  no guest execution or source generation in this stage.
- `tests/cpu/test_corpus.py`: focused rejection/coverage checks.
- `mydocs/working/task_m1_6_stage1.md`: source review, actual tool availability,
  oracle route and declared limits. Heavy evidence remains `.build/task6/`.

### Changes

1. Read the pinned FEX ASM CONFIG reader/native HostRunner and relevant Hangover
   module selection. FEX's runner includes Windows conditionals, but its CMake
   excludes HostRunner for MinGW; the x64 HostRunner uses Linux signals/ucontext
   and modify_ldt. Reuse its semantic/configuration contracts, not its Linux
   execution plumbing in Wine.
2. Review Madeira's complete generator/driver at the task-plan pin, including
   GPL notices. Reuse per-case NASM object generation and capture-table ideas.
   Do not silently inherit HostFeatures/flags/MM/upper-lane skips, broad RWX
   scratch, shared-state leakage or a resumable incomplete-success exit.
3. Inventory the 2,270 pinned ASM files and classify rather than mass execute.
   Select a compact representative corpus covering the approved categories;
   case count is a consequence of coverage, not a pass quota. Include required
   feature-gated cases when actually exposed/needed. Keep a complete exclusion
   census with explicit reasons, including unsupported CONFIG keys.
4. Freeze defined outputs before running Pear. Mark undefined flag bits, exact
   FP/NaN/rounding expectations and address-dependent values case by case.
   Reject missing or empty expected comparisons; do not derive reference values
   from Pear's own execution or relax them after a mismatch.
5. Locate/verify native NASM or a pinned assembler preparation; record existing
   LLVM-MinGW tool hashes without rebuilding Wine/FEX. If installation is needed,
   identify the exact input and disk budget before executing it in Stage 2.
6. Select native Windows x64 as the primary independent same-PE reference route.
   The official GitHub runner matrix lists `windows-2022`/`windows-2025` as x64;
   actual native architecture, CPU features and image/tool versions still must be
   measured in Stage 2. No native reference execution occurs in Stage 1.

A Linux native x64 reference is acceptable only for normalized instruction
fixtures whose setup/outcome contract is equivalent; it does not validate Windows
SEH or callbacks. FEX golden values are upstream expectations, not independently
validated native results by themselves.

### Verification

Inputs: pinned FEX and Madeira sources, #5 final source receipts, approved coverage
categories. Python 3.13 is available locally; source inspection uses read-only
caches. Native reference and NASM remain unverified until recorded checks.

Planned interface and checks:

```sh
python3 -B tools/cpu/corpus.py --source "$PEAR_FEX_SOURCE" --manifest tests/cpu/corpus.json --output .build/task6/stage1-corpus
python3 -B -m unittest discover -s tests/cpu -p test_corpus.py
python3 -B tools/check_governance.py
git diff --check
```

Verify altered source/config, unknown fields, duplicate/missing cases, empty
expectations, conflicting Env policy and incomplete census are rejected. Test
observable admission contracts, not exact prose or internal function layouts.
Output must distinguish required, unsupported, unavailable and unperformed.
A source-only Stage 1 may complete with unavailable native execution explicitly
recorded; Stage 2 cannot claim a reference comparison without that execution.

### Commit

`Task #6 Stage 1: define the source-bound CPU corpus and reference contract`

## Stage 2 — Instruction and ABI Comparison

### Artifacts

- Adapted `tools/cpu/generate.py`, PE capture/runner under `tests/cpu/`, and exact
  GPL/MIT source notices; `tools/cpu/run.py` and `compare.py` use existing Pear
  runtime authorization/supervision/observation functions.
- A narrowly scoped native-reference workflow if needed; sanitized immutable
  PE/corpus/reference records, original command logs retained privately.
- Targeted comparator/capture tests and Stage 2 report.

### Changes

Generate isolated per-case objects and capture buffers with a known Windows ABI,
nonvolatile GPR/XMM preservation, initialized FP/scratch state, explicit flags
capture and defined masks. HostFeatures are eligibility inputs, not a blanket
skip switch. Preserve all required SIMD lanes for selected features. A faulting
case cannot skip itself and later produce aggregate success. Prefer process
isolation for invalid-stack/exception cases; use allowed guest memory mappings.

Run redistributable PE fixtures on the independently observed native Windows x64
reference and retrieve the exact PE bytes/results for Pear. Compare exact defined
outcomes and bind source, generated assembly, compiler, binary, host features and
result identities. Collect native Windows ABI/fault behavior where it is the
reference requirement. Native x64 hosted execution is distinct from a Mac run.

If no existing reference executor is available, a narrow workflow publication is
needed before final task PR publication: manual dispatch requires a workflow on
the default branch. Prepare an explicitly reviewed task-branch `push` workflow
for the reference only (read-only token, pinned actions, no private inputs, bounded
jobs), publish `codex/publish-task6` solely for this execution, then use the normal
final-report/PR procedure after all stages. This operational exception must be
confirmed at the Stage 2 continuation checkpoint with the actual workflow diff;
Stage 1 approval does not authorize an early source push or default-branch change.

Reuse immutable #5 artifacts through explicit source/receipt admission. New #6
fixture adapters must not weaken #5's fixed-case receipts or overwrite its output.
Reduce mismatch to one case and distinguish harness, translator, Wine and Darwin
failures before a patch. Rebuild only changed components and rerun affected cases.

### Verification

Expected: every required case completes on both routes and defined outcomes
match; deliberately changed expected data and missing final/case records fail.
Reference-unavailable, feature-unsupported and source mismatch never equal pass.
Actual authorization before/after, ARM64 process/image observations, bounded
execution, owned cleanup and sentinel survival remain required for Pear runs.

```sh
python3 -B -m unittest discover -s tests/cpu -p test_harness.py
python3 -B tools/cpu/compare.py --manifest tests/cpu/corpus.json --build "$PEAR_CPU_BUILD" --reference "$PEAR_NATIVE_REFERENCE" --candidate "$PEAR_CPU_RUN" --output .build/task6/stage2-comparison
git diff --check
```

Tool hashes and host CPU/OS/image settings are recorded at execution, not assumed
from workflow labels. Keep incomplete or failing attempts with the smallest
necessary diagnostic. #5 unchanged engine evidence retains only its original
scope; new corpus execution is mandatory for the new comparison claim.

### Commit

`Task #6 Stage 2: compare declared x64 semantics across native and Pear execution`

## Stage 3 — Ordering and Lifecycle Stress

### Artifacts and Changes

Add only missing representative atomic/ordering and repeated lifecycle fixtures.
Use at least two actual guest workers, with the coordinator fitting the existing
three-participant demonstrated profile. Choose explicit bounded iteration counts
and timeouts from a small calibration, then record them before the qualification
run. Do not treat three participants as proof of arbitrary concurrency support.

Use assembly/defined atomic operations to avoid C data-race undefined behavior.
Distinguish permitted x86 store-buffer outcomes from forbidden message-passing
or locked-RMW outcomes. Keep synchronization outside the measured operation where
it would otherwise mask weak ordering. Observe the actual per-thread effective
software TSO/vector/memcpy policy and relate it to generated-code settings.
Upstream fixtures overriding `FEX_TSOENABLED=0` cannot establish this criterion.

Reuse #5's proven API/thread/invalidation/exception/context cases when unchanged;
extend only missing repeated ownership, SEH/guard or code-change boundaries.
Any known required failure blocks completion. Reduce failures and use upstream
functions/dependencies before introducing local protocols. i386 remains explicitly
unsupported unless a relevant required helper is identified and actually qualified.

### Verification

Retain native/reference identities where appropriate, actual policy per worker,
iteration/outcome counts, exact forbidden conditions and resource cleanup. Run
changed-boundary regressions for fixes, not an unrelated full historical suite.
A zero forbidden-outcome count is finite stress evidence, not universal proof.

```sh
python3 -B -m unittest discover -s tests/cpu -p test_ordering_results.py
python3 -B tools/cpu/compare.py --manifest tests/cpu/corpus.json --reference "$PEAR_NATIVE_REFERENCE" --candidate "$PEAR_STRESS_RUN" --output .build/task6/stage3-comparison
git diff --check
```

### Commit

`Task #6 Stage 3: qualify actual translated ordering and lifecycle boundaries`

## Stage 4 — Integrated Qualification and Handoff

### Artifacts and Changes

Bind final fixture manifest, native reference, actual Pear runtime and passing
required results. Explicitly list unsupported/unavailable/unperformed categories,
known remaining defects and #8/#10/#11 dependencies. Update the approved existing
CPU contributor guide; leave historical #5 claims unchanged. Apply final-report
procedure only after all stage criteria pass.

### Verification

- Independently read current hashes and complete required result counts; reject
  mixed candidate/config/reference records or unexplained native mismatches.
- Reuse unchanged same-input records; rerun only affected cases when runtime,
  corpus/capture/compiler/configuration or source changes invalidate them.
- Check document links/governance and `git diff --check`; do not rerun large builds
  for report wording. Preserve required execution safety and cleanup gates.
- Preserve current cross-task inputs and unique failure evidence; remove only
  completed disposable task-owned prefixes after live ownership checks.

### Commit

`Task #6 Stage 4: record CPU qualification and the integration handoff`

## Commits, Dependencies and Approval

Each stage commits its source and `mydocs/working/task_m1_6_stage{N}.md` together.
No stage is complete with a required failing check. Stage 2 follows completed
Stage 1 and explicit continuation; Stages 3/4 follow the same rule. Routine fixes
inside the approved boundary do not need repeated permission. A new owner/ABI,
unreviewed feature expansion or official document relocation needs an amendment.

Approve this four-stage implementation and Stage 1 source/corpus contract work.
No new Wine/FEX build, guest run, new system component, runtime permission change
or remote reference workflow is needed for Stage 1. Native reference execution
and its concrete workflow publication are reviewed at Stage 2.

## Reference Execution Sources

Checked October 8, 2026: [GitHub-hosted runner matrix](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
and [manual workflow requirements](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow).
These establish offered x64 labels and dispatch constraints, not a completed or
available reference run for this repository. Private-repository jobs use the
account's Actions allowance; no larger runner or new paid service is selected.

## October 8 Approval and Stage 1 Checkpoint

The requester explicitly continued the detailed-plan/Stage 1 approval request.
Stage 1 is complete: 12 source-bound ASM selections, 10 boundary contracts and
14 passing validator checks. Full source census and actual limitations are in
[the Stage 1 report](../working/task_m1_6_stage1.md). Python 3.14.4 was actually used.
No guest/reference execution, remote workflow or runtime changes occurred.

## Stage 2 Continuation

The requester explicitly continued on October 8. Local harness implementation is
authorized. The concrete early reference-workflow push remains subject to the
review described above. NASM 3.02 was built as native ARM64 in a task-owned
35 MiB temporary tree, below the 256 MiB preparation budget; no system install.

Local Stage 2 preflight: 19 PEs built, 12 harness refusal checks and 14 corpus
checks passed. The [reference publication review](../working/task_m1_6_stage2_reference_review.md)
was approved by the requester, including confined corrections and reruns.
This is not native execution or Stage 2 completion.


### Stage 2 Fixture-hosting Correction

The original absolute-displacement setup failed before guest instructions: the
unchanged Wine/FEX image arena occupied `0x7fff0000`, including the requested
`0x7ffff000` page. Treat this as a fixture/loader address-space precondition,
not an ISA result or a required-path waiver. The recorded Stage 2 adaptation
moves data loads/stores to `0x1000f000`, keeps every upstream register expectation,
and adds an exact `R8 = 0x7ffffff8` LEA check for the original upper disp32 edge.
The original source manifest and failure remain intact; a separate hashed
`tests/cpu/adaptations.json` binds the generated execution inputs. Native Windows
must validate the changed PE before a new Pear comparison. No owner allocation,
Wine/FEX implementation, runtime permission or expected-value relaxation occurs.


### Stage 2 Required-path Correction

The same ABI PE passed native Windows but reached FEX's `Unhandled long bind`
on Pear. Logging-only diagnostics identified Pear's earlier 16-additional-reference
label limit, rather than an architectural branch-distance failure. The current
#5 design already stages JIT output in ordinary NX memory before owner publication.
The #6 correction therefore reuses upstream `fextl::vector` for excess references
only during that checked private staging path. Direct owner emission stays fixed,
allocation-free and fail-closed; changing its buffer resets spill permission.
No owner wire ABI, guest golden value, permission or Wine implementation changes.
The source correction is independently ordered and hashed under existing
`runtime/fex/patches/cpu/`; preparation/admission and focused controls remain in
the approved `tools/cpu/` and `tests/cpu/` locations. No official document moves.

Only ARM64EC FEX is rebuilt; the original #5 inputs and Windows PE reference stay
unchanged. The changed engine invalidates earlier Pear corpus results, so the
whole declared Stage 2 corpus must be checked once on this new candidate. Native
Windows needs no repeat when its exact PE bytes, capture and oracle are unchanged.
The added header control checks 256 actual branch fixups and the retained direct
emission refusal. Correction admission checks exact patch pre/postimages, because
`git apply` from an ignored nested directory was observed to skip every file while
returning zero. That failed preparation and its stopped runtime remain failures.

Stage 2 is complete locally: 18 native-matching Pear cases, one explicitly
unsupported AVX case and zero required failures. The [Stage 2 report](../working/task_m1_6_stage2.md)
and sanitized observations own the final identities, failures and retained limits.

## Stage 3 Continuation and Reuse Decision

The requester explicitly continued after the Stage 2 report. Stage 3 is now
authorized. Keep all new implementation in the already approved `tests/cpu/`,
`tools/cpu/` and `runtime/fex/patches/cpu/` locations; no official document moves.
Pinned FEX's `0F_C0_Atomic64.asm` covers single-thread unaligned operations, and
`MultiInst_TSO.json` covers generated instruction counts; neither supplies a
Windows two-worker ordering oracle. Adapt Pear's existing CreateThread/TLS/join
fixture and reuse FEX's actual Context policy getters. Add original MIT assembly
for aligned locked RMW, message passing, plain store buffering and fenced store
buffering, with epoch synchronization outside measured operations. Plain SB 00
is allowed and need not occur. Record worker IDs, outcome counts and normal joins.

Calibration uses 64 iterations per case and two sequential pairs of workers.
Qualification counts will be frozen after calibration. Each run retains the
existing 180-second owned supervisor bound. Log effective scalar/vector/memcpy
policy at actual FEX thread creation, then map its state address to the Windows
thread ID at publication. This changes observation only, with no owner ABI or
hardware-TSO permission change. Preserve the Stage 2 candidate and records.

### Stage 3 Required-path Link Correction

The first 64-iteration calibration failed in `ExitPearFunctionLink`, before
completing an ordering round. Diagnostic reproduction kept every owner guard and
showed thread/revision/map/entry/bytes valid but a different shared target address.
FEX's upstream shared map permits replacement while a thread-local L1 hit can
still name an older retained block. Reuse `GuestToHostMap::FindBlock` with its
read-lock token under the existing source mutation turn before minting a link.
Also require the source write epoch to match the pre-handoff RX snapshot: absence
of waiting in `Contended()` does not exclude an earlier peer publication. Preserve
the existing indirect path on epoch changes; do not relax `PatchPrepared`,
publication, invalidation, retention, signing or owner wire checks. The correction
and diagnostic have separate ordered source/patch identities. Calibration remains
failed until actual corrected execution and complete counts are observed.

### Frozen Stage 3 Qualification Budget

Corrected calibration completed 64 iterations per mode across two worker pairs
(512 measured pairs), exit 42, in 7,228 ms including cold-prefix execution. All
five participant lifetimes had actual scalar/vector/memcpy TSO enabled; owned
cleanup and sentinel checks passed. The qualification budget is frozen before
execution: 2,048 iterations per mode, four sequential worker pairs (32,768
measured pairs), at most three concurrent participants, 45 seconds per round,
120 seconds for native capture and the unchanged 180-second Pear supervisor.
Two prior failed calibration records remain failures. The existing reference
workflow will run only this new exact PE; unchanged 19-PE native results are
reused from Stage 2. This remains the approved branch-only reference harness,
ordinary runners, pinned tools, read-only token and 14-day artifact retention.

The first native qualification execution hit its 45-second round bound (exit
106), without a completed round; it is not an ordering pass. Add scheduler yield
only to the existing epoch/completion wait loop, outside measured ASM, so three
participants can progress on a smaller native runner. Retain the frozen operation
counts and timeouts. Recalibrate the changed PE on Pear and native Windows before
using its qualification result. Record native logical CPU count and bounded wait
progress; require one successful checked FEX ThreadTerm for every joined worker.

Stage 3 is complete: see [the Stage 3 report](../working/task_m1_6_stage3.md) and its sanitized observations for final input identities, failures, finite ordering results and Stage 4 integration requirements.
