# Task #5 Final Report — FEX Darwin CPU Integration

GitHub Issue: [#5](https://github.com/postmelee/pear/issues/5)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta

## Work Summary

- Target Issue: #5; six completed implementation stages.
- Purpose: execute small x64 Windows programs through the recorded FEX CPU module
  in ARM64 Wine on macOS, with explicit Darwin services and execution ownership.
- Result: the fresh final pair passed five x64 fixtures from empty synthetic
  prefixes, the native caller refusal, and both native UnixLib service suites.
- Scope: component integration on the declared development Mac. This is not
  general CPU conformance, Steam/Megabonk support or an ordinary-user release.

Wine C and FEX C++/assembly are retained. The pinned FEX Windows frontend/core,
Wine ARM64X/CHPE handling, exception/context reconstruction and existing Pear
build/signing/supervision readers are reused. Local supplements supply Darwin
services, checked role selection and the single-address executable-memory owner.
FEX's MIT reuse permission is separate from its prohibition on AI-generated
upstream submissions; no upstream submission or project-wide license decision
was made. See the [task plan](../plans/task_m1_5.md), [implementation plan](../plans/task_m1_5_impl.md)
and [memory design](../tech/task_m1_5_memory_design.md).

## Changed Files and Impact Area

| Path | Change Summary | Impact Area |
|---|---|---|
| `runtime/fex/` | Pinned dependencies/tools, ordered Darwin, memory and integration supplements; source graph and attribution | Source construction and translator/host boundary |
| `tools/fex/` | Preparation, build, admission, signing orchestration, bounded execution and evidence readers | Developer reconstruction and validation |
| `tests/fex/` | Original native/PE fixtures, source-bound lifetime tests and negative verifier controls | Required component behavior and refusal paths |
| `docs/development/fex-host.md` and existing cross-references | Actual reconstruction recipe, ownership and qualification limits | Contributor guidance |
| `docs/research/platform-reuse.md`, `docs/delivery-plan.md` | Approved upstream reuse review and downstream integration responsibilities | Existing research and single roadmap |
| `mydocs/plans/`, `working/`, `tech/`, `troubleshootings/`, `orders/` | Plans, scoped results, exact sanitized observations, retained history and board | Review and handoff |

The large source-graph record preserves ordered source provenance; it is not a
binary, prefix or game payload. Proprietary files, credentials, profiles, private
signing material, raw diagnostics and authenticated prefixes are not published.

## Document Location Verification

| File | Planned Location | Actual Location | Result | Evidence |
|---|---|---|---|---|
| FEX contributor guide | `docs/development/fex-host.md` | Same | OK | Task-plan approved official guide |
| Index, Wine guide, source qualification and runtime audit | Existing `docs/` files | Same | OK | Implementation-plan approved cross-references |
| Reuse review and delivery guidance | Existing `docs/research/platform-reuse.md`, `docs/delivery-plan.md` | Same | OK | October 8 approved location judgment; commit e3f6b0a |
| Plans, design, stage/final evidence and history | `mydocs/` task artifacts | Same | OK | Approved October 7 separation; no second product roadmap |

## Quantitative Before/After Comparison

| Metric | Before #5 | After #5 |
|---|---|---|
| Actual x64 PE execution through this FEX/Wine pair | Unverified | Five final cold-prefix cases returned expected exit 42 |
| Final Wine construction | No integrated candidate | 21 successful build/install/fixture/inspection commands |
| Final FEX construction | No Darwin module candidate | 10 successful commands; 32 inspected artifacts |
| Native UnixLib checks per role | Unverified | 8 services, 7 mapping controls, 26 policy controls, 2 joined workers |
| Final ordinary native caller refusal | Unverified | Expected unavailable status and exit 68 |
| Finite EC lifetime evidence | Unverified | Earlier source-bound 62-check case and 2 simultaneous EC workers passed |

The reviewed bookkeeping profile is 12.5 MiB within 16 MiB for one Context and
up to three participating EC threads. The 1,588,985,856-byte JIT/PE reservation is
virtual address space, not measured RSS. No performance or power comparison is
claimed, and the finite thread profile is not game capacity.

## Verification Results

| Acceptance Criterion | Result |
|---|---|
| Small x64 PE executes through recorded FEX in ARM64 Wine without Rosetta fallback | OK, finite scope: five same-pair cases, expected results, ARM64 process/image observations, current authorization before/after, owned cleanup and sentinel survival; no complete late-load timeline claim |
| Required host services have regression tests and documented thread/JIT/exception ownership | OK, representative component scope: native services plus worker/TLS, callback, invalidation, handled exception/data guard and suspend/context cases; ownership/refusal documented; broader CPU qualification remains #6 |
| Patch series builds from the recorded P01 source lock and respects contribution policy | OK: fresh objects from verified source/tool preparations at the locked Wine/FEX revisions; original languages/notices retained; no FEX upstream submission. Clean-machine reproduction is not established |

### Stage Verification Results

1. [Stage 1](../working/task_m1_5_stage1.md), `cf58fce`: source/dependency/tool closure and real target compile/link contracts.
2. [Stage 2](../working/task_m1_5_stage2.md), `51ab581`: Darwin host services and complete ARM64EC/WoW64 module construction; module construction is not i386 guest execution.
3. [Stage 3](../working/task_m1_5_stage3.md), `91fc9b3`: actual Wine/FEX memory ownership, finite EC lifetimes, retirement/reuse and native refusal controls.
4. [Stage 4](../working/task_m1_5_stage4.md), `1a29f18`: actual x64 entry, native API transition and callback return.
5. [Stage 5](../working/task_m1_5_stage5.md), `0055277`: translated worker/TLS teardown, cross-thread invalidation, ordinary exceptions and cooperative suspend/context editing.
6. [Stage 6](../working/task_m1_5_stage6.md), `95f9c3a`: fresh final reconstruction, five cold-prefix x64 cases, native refusal and service regressions. [Sanitized observations](../working/task_m1_5_stage6_observations.json) bind exact sources, artifacts and results.

Final execution host: native ARM64 Apple Silicon, macOS 26.5.2 (25F84), SDK 26.5;
recorded native/cross compiler caches. Wine `4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf`,
FEX `59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa`. Software TSO remains enabled;
persistent code caches are disabled. Development authorization and normal macOS
protections remain required.

### Publication Review and Integrated Verification

Latest master `a29d600` was integrated in `ddb0a1f`. Conflicts affected only the
documentation index and four daily boards; retain #5's current rows and the other
tasks' master records. No FEX source, tests, tools or integration series changed
from Stage 6. Master's separate #7 native-heap patch remains a graphics integration
input, not silently applied to or qualified by the final #5 CPU artifacts.

The following checks passed again after integration on October 8:

- `tools/check_governance.py`: 25 documents and 231 local targets.
- Documentation checker tests: 35 passed.
- Targeted fresh-build admission and service-reader tests: 4 + 7 passed.
- `reconstruction_check.components`: current source inventories, saved commands,
  logs, module outputs, wire header and producer hashes still match the final pair.
  Wine receipt `f590ffab548efbc06a9f53486e93212431fb1c7f6fd32dd6f17e9962171e56e1`;
  FEX receipt `a91d836a6a9c915be98ff4a3a7ad759f0a928d9018a98fee726b2191891048cd`.
- `git diff --check` and tracked-payload review: passed; no private runtime or
  account payload is included. PR CI results are recorded in the PR after execution.

Unchanged Stage 6 execution evidence is reused within its original scope; no
repeated heavy build or guest execution was needed for documentation integration.
Historical failures remain recorded, including the collection-only Wine result
repair and installed-mode/policy-fixture corrections. They are not relabeled as
successful original attempts. Earlier instrumented evidence is not claimed to
have executed again on final bytes.

## Residual Risks and Follow-up Work

### Residual Risks

- Prepared-source/receipt workflow on one development Mac; no one-command clean
  checkout build, independent Mac reproduction or player installer.
- One Context/up-to-three-thread fixture profile. Broad CPU/ordering stress,
  forced foreign termination, arbitrary unwind, inline SMC/unaligned repair and
  JIT-guard recovery remain unqualified; finite capacity failures stay explicit.
- i386/WoW64 construction does not qualify required Steam helper execution.
- No complete process/module timeline, translated graphics pairing, Steam or
  Megabonk execution, gameplay, performance or ordinary-user distribution claim.

### Follow-up Candidates

Existing #6 owns independent-reference CPU/ABI/ordering coverage and reduced
failures. #8 pairs translated D3D11 with the completed #7 component; #10 covers
complete host observation; #11 inspects and qualifies actual Steam helpers.
Later reproduction, gameplay and packaging gates retain their own criteria.
No new Issue is required for these existing responsibilities.

Preserve the #5 artifact worktree for #6/#8: the signed runtime bundles, tool/source
caches and private receipts contain absolute path bindings. Completed synthetic
prefixes were already removed after cleanup and process checks (4,992,257,066
logical bytes inventoried). Removing the remaining worktree would break the
handoff. Reclaim only verified disposable duplicates; no release uploads of raw
runtime payloads or private records.

## Approval Request to Task Requester

The requester explicitly directed final report/PR preparation, review, merge,
Issue completion and then #6 execution on October 8, 2026. This authorizes #5
publication and merge after verification and supersedes the earlier local-only
restriction for this work. Merge and closure are reported only after GitHub
confirms them. #6's concrete plan follows the task-start procedure.
