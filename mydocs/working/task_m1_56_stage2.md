# Task #56 Stage 2: imported component histories and source packages

GitHub Issue: [#56](https://github.com/postmelee/pear/issues/56)
Implementation plan: [task_m1_56_impl.md](../plans/task_m1_56_impl.md)
Stage: 2. Local import completed October 16, 2026 (Asia/Seoul).

## Stage Purpose

Establish independent, attributed source repositories and the common contract/diagnostic package, preserving exact selected source bytes and upstream ancestry. This stage does not activate a runtime or transfer final source authority.

Context: the approved six-stage implementation plan, root/runtime/test/docs rules, artifact-retention procedure, current source-owner acceptance for isolated import, and the recorded upstream license/contribution boundaries. The task-stage-report procedure applies with the requester's continuous-stage authorization.

## Artifacts

| Repository | Imported scope |
|---|---|
| [pear-wine](https://github.com/postmelee/pear-wine) | Full Wine ancestry; accepted baseline and selected diagnostic checkpoint; 58 changed source units; provenance, source checker, README and test ownership |
| [pear-fex](https://github.com/postmelee/pear-fex) | Full FEX ancestry and six enabled pinned submodules; accepted and D36 candidate layers; 83 source units plus 16 generic payloads; diagnostic tests and ownership records |
| [pear-dxmt](https://github.com/postmelee/pear-dxmt) | Full DXMT ancestry and pinned DirectX submodule; separate baseline/selected layers; six units; provenance, README and test ownership |
| [pear-runtime](https://github.com/postmelee/pear-runtime) | 62 exact v1/v2 contract files, shared Abort schema/generator/header, tests, notices and sanitized future fixture extraction map |
| `task_m1_56_stage2.json` | Exact component commits, ancestry, test/interface checks and evidence digests |

All four repositories are private and require collaborator access. The recorded branch is `codex/task56`. Wine's first full-history upload is still active; its remote commit is explicitly unverified. The other three remote branch tips match their recorded local commits. Independent recipe implementation may continue under the updated scheduling clause; remote identity remains a mandatory final-lock/handoff check.

## Body Change Scope / Lossless Preservation

Original upstream commit history and attribution were not rewritten. Source imports preserve bytes, executable modes, gitlinks and notices, with accepted and selected layers in separate commits. Imported generated/working files are identified by exact content and checkpoint provenance, never falsely represented as committed upstream blobs. No historical generator was executed during import.

Wine owns the request ABI and Metal provider headers; DXMT owns the reverse winemetal interface exports; runtime owns the shared Abort schema and generated header. FEX's other 16 generic payloads have one canonical source. Private phase selectors and game/account/signing data are excluded even from private Git.

The runtime contract package preserves relative validator/schema paths. Pear's current copies and manager dependency remain unchanged pending the final export/authority record. Test maps enumerate 185 unique component/runtime records with no conflicting destinations. Deferred adaptations and unperformed historical controls are explicit. Runtime also preserves a sanitized 52-source fixture/helper extraction map; this is not a runnable runner package yet.

## Verification Results

Execution context: local Git/Python source and portable synthetic tests, plus authenticated private GitHub publication/metadata checks. No compiler, runtime signing, host fixture or game execution occurred.

- Wine/FEX/DXMT are non-shallow, independent object stores, with 185,803 / 15,210 / 1,360 upstream ancestors respectively. Pinned trees and connectivity match. All seven materialized dependency submodules match their pinned commits and are non-shallow. No alternates point at old caches.
- Parent independently checked 58 Wine, 99 FEX (83 source + 16 payload) and six DXMT paths: exact hashes, sizes, executable modes and tracked status. Importer whole-tree checks also preserve unchanged upstream files and original README content.
- Wine/DXMT peer-header checks pass in both directions. The Wine/FEX ABI and shared Abort header match their recorded provider digests.
- Portable suites: 154 contract, 11 shared diagnostic, 45 FEX and nine source-admission tests in each of Wine/DXMT passed (228 total). Their scope is source/contract/refusal/diagnostic logic, not native runtime behavior.
- Source notices are checked for new/adapted code. Exact legacy source with missing inline notices remains covered by explicit path-specific provenance/manual review; no blanket inline SPDX compliance or distribution clearance is claimed.
- Strict new metadata/adaptation whitespace checks pass. The raw full DXMT import retains 16 pre-existing trailing-whitespace findings in frozen source; every line matches the selected checkpoint. These were recorded rather than normalized and silently changing the source hash. The plan now states this exact-import exception.
- Added content was reviewed and scanned for personal absolute paths, private-key/token markers and forbidden private selectors. No such payload was imported. Scans supplement explicit provenance review.
- All 29 protected critical input/runtime identities remain unchanged. Pear Preview, manager and profile tracked paths have no task diff. No original checkout, selection, prefix or save was modified.
- Pear `git diff --check` passes.

Evidence reuse: unchanged source/patch replay and portable test inputs support the stated source claims only. Existing D36 runtime results remain historical; newly built bytes still require affected controls. The retained Task3 Python environment matched locked versions for the contract suite; a new dependency environment was not installed.

## Artifact Disposition

| Artifact | State / owner | Retention and release condition |
|---|---|---|
| Four component source repositories and exact commits | Retained source; component/runtime owners | Required for ongoing development; no deletion |
| Original shallow caches, sources, selected runtime/private graph | Retained unchanged; prior owners | Recovery, input staging and final comparison; no release authorized |
| Local detailed import/replay/ownership receipts | Retained evidence; #56 | Preserve through final reconstruction and owner acceptance; sanitized digests recorded here |
| Contract test dependencies | Existing retained Task3 environment used read-only | Existing owner/consumer holds remain |
| Task4 approved cleanup receipts | Historical evidence; #56 | Previous 3,030-file deletion is complete; no further deletion here |

Initial history+checkout displayed allocation was 1,902,864 KiB across the three forks (about 1.81 GiB), before small metadata additions. Acquisition free-space observation was 31,012,356,096 bytes. These are different quantities, and concurrent filesystem changes prevent attributing all free-space movement to this task. Initial Wine upload may use transient pack buffers; no large build overlaps it.

The bounded next-stage plan budgets 11,909,044,727 additional bytes (about 11.1 GiB) for preserved inputs, component outputs, one candidate bundle, a synthetic seed, all seven full logical prefix copies, logs and uncertainty. A separate 6 GiB host floor is retained. Toolchains/SDKs remain explicit admitted external prerequisites. Recompute actual inputs/free space before each heavy operation; full historical rebuild thresholds are not waived.

## Residual Risks

- Wine initial remote upload/ref equality remains pending; it must be completed before final lock publication/handoff.
- Portable input staging, compilation/linking, signing/admission and required host controls remain unperformed.
- Pending component tests and the fixture runner need reviewed adaptation; old path-bound producers cannot be run unchanged against new forks.
- Original source ownership remains active until exact final owner acceptance. Repository creation does not imply gameplay, Steam or player distribution qualification.

## Impact on Next Stage

Implement explicit-input reconstruction using fixed component commits and preserved immutable operands/configuration. Keep original D25 recovery evidence distinct from the successor procedure. Compile selected units from the forks, audit actual dependencies, compare output bytes/sections and assemble an isolated candidate. Preserve all seven original fixture oracles and APISession ownership.

## Approval Record

Continue within the requester's explicit continuous-stage authorization. Verification, reports and commits remain required. No new deletion, public visibility, Preview/default activation or existing-environment change is authorized.
