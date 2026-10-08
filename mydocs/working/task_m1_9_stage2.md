# Task #9 Stage 2: Verify immutable runtime admission and activation

GitHub Issue: [#9](https://github.com/postmelee/pear/issues/9)
Implementation plan: [task_m1_9_impl.md](../plans/task_m1_9_impl.md)
Stage: 2
Date: October 9, 2026
Status: Implemented and verified; Stage 3 awaits explicit continuation.

## Stage Purpose

Implement native contract/policy consumers and local immutable payload admission before general supervision. Verify actual descriptor-relative entry and dylib lookup, read-only enforcement, retained version use, and atomic selection under operational faults, interruption and concurrent activation. The requester explicitly approved this stage on October 9, 2026. No later stage is implied.

Context used: root, manager, runtime, tests and host rules; README, official index, architecture, delivery plan and runtime contracts; Issue #9, the approved task/implementation plans and three review supplements; the Stage 1 report and reuse record; task/Git workflow and document-location rules. The task-stage-report and repository todo skills were applied with the central stage-report/orders templates. The existing worktree and `codex/task9` were preserved. Relevant open work and branch/worktree state were inspected before implementation; no additional upstream investigation or other task's cache/build/prefix was used.

## Artifacts

| File/group | Change Summary |
|---|---|
| `manager/src/fs.rs`, `contract.rs`, `policy.rs` | Descriptor-relative no-follow traversal, bounded state scan and streamed hashes; closed native v1/v2 shapes/relationships and purpose-specific evaluation, adapted from #3 and the oracle |
| `manager/src/activation.rs` | Actual read-only UDRO admission, owned backing-media identity/hash, strict native signature/dependency inspection, retained root/lease, staged atomic selection metadata |
| `manager/src/tools.rs`, `encoding.rs`, `main.rs` | Existing nonblocking drain pattern for bounded system-tool inspection, small local metadata encoding, initial inspect/evaluate/activate CLI; no runtime launch command |
| `manager/native/bridge.c/.h`, `src/native.rs` | Header-checked `fstatfs` wrapper retaining flags/filesystem identity and numeric errors |
| `manager/examples/activation_probe.rs`, `tests/manager/fixtures/` | Finite native fixture entry and approved/alternate dylibs; explicit barrier/fault harness distinct from the product CLI |
| `tests/manager/build.py`, `test_admission.py`, `test_activation.py` | Existing locked/offline build/capture adapter extended; native/oracle differential scenarios and actual immutable activation controls |
| [Sanitized evidence](task_m1_9_stage2_evidence.json), reuse record, plan and daily board | Current input/output identities, actual results, reuse/scope update and next approval checkpoint |

## Body Change Scope / Lossless Preservation

Actual artifact locations match the approved plan. No product-documentation root, v1 contract, v2 schema, original experiment source, dependency manifest/lock or original strict-parser bytes changed. Existing master/#6/#8 work remains outside this task's changes. The October 8 board is preserved; only the October 9 #9 row is added. Task documents remain under `mydocs/`; no official documentation is added during this stage.

The native policy path preserves the separate purposes: a complete synthetic runtime candidate can pass `qualification_run` evaluation without prior game qualification; `supported_launch` additionally needs current exact matching qualification. Neither outcome authenticates the submitted evidence. Actual runtime-context activation refuses with `runtime_authorization_unavailable` because the independent host/signing/observer grant producer is not available. Real host execution in this stage is restricted to the explicitly selected, owned finite fixture controls.

The manager uses existing `hdiutil info/imageinfo`, `plutil`, `codesign --verify --strict`, and `otool -L/-l` for inspection only. It does not create/attach/detach volumes, install software or sign executables. The test harness manually prepares and cleans its own images. The selected mount must be read-only and executable; backing media must be unambiguous, current-user-owned, non-group/world-writable UDRO. Root device/inode, filesystem identity, media hash and all selected record/blob hashes are retained/rechecked. Native entry uses `./<declared entry>` after `fchdir` on the held root, with an empty inherited environment.

The closed dependency subset accepts the selected thin ARM64 executable/dylibs, entry-anchored local RPATHs, declared internal candidates and the separately classified `/usr/lib/libSystem.B.dylib`. External RPATHs/dependencies, undeclared existing candidates, ambiguous candidates and unsupported load forms refuse. This is declared dependency admission for reviewed finite fixtures, not full #10 observation or support for arbitrary `dlopen`.

Selection publication writes a private staged descriptor, syncs it and its stage directory, renames relative to held descriptors, then syncs the state directory. An exclusive activation lock coordinates publishers; a shared artifact-version lease spans actual fixture use and child reap. Previous media are never deleted. Prepublication failures preserve the old pointer. Failure after rename is `selection_commit_uncertain`; it cannot truthfully promise rollback. Interrupted private staging may remain and is not interpreted as a committed selection.

## Verification Results

Execution context: ARM64 macOS 26.5.2 (25F84), Xcode 26.6 (17F113), SDK 26.5, Apple clang 21.0.0, Rust/Cargo 1.94.1; native target `aarch64-apple-darwin`, minimum build deployment target 26.0. Cargo was locked/offline with the unchanged exact libc input. Current build receipt covers 96 source inputs. No timing result is a performance claim.

Approved commands executed successfully against the final inputs:

```sh
python3 -B tests/manager/build.py --output .build/task9/stage2 --locked
PEAR_MANAGER_BUILD=.build/task9/stage2 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_admission.py
PEAR_MANAGER_BUILD=.build/task9/stage2 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_activation.py
git diff --check
```

| Verification | Actual result and scope |
|---|---|
| Native admission | 133 tests passed: 130 applicable original scenarios exercised against both native and independent oracle evaluation, plus generic identity/version, real-runtime refusal and schema boundary tests. Validity/eligibility agree; valid records also require matching policy codes. Invalid structural diagnostic wording need not match. |
| Actual activation | 16 tests passed, zero skips. Four owned UDRO images were created, mounted read-only and detached. Both executable and dylib writes failed with actual `EROFS`. Approved and alternate dylibs produced independently distinguishable stdout markers. |
| At-use substitution | After the admission barrier, the mounted payload's ancestor was renamed and its former path replaced with the alternate fixture. The old descriptor executed `approved!` with exit 0; no alternate marker occurred. Concurrent activation selected the alternate version while the retained old invocation still executed `approved!`. |
| Dependency controls | Actual internal RPATH execution passed. A populated writable external RPATH and an undeclared internal library refused before entry. Both payload inventories and image hashes were independently checked before/after. |
| Publication/fault controls | Prepublication injected errors and SIGKILL preserved old selection bytes. Injected ENOSPC/EIO write/sync failures retained numeric errors. Postpublication error reported uncertain commit; postpublication SIGKILL left a complete new descriptor. Busy activation, corrupt policy, unsafe state permissions/lock symlink and writable backing media refused; unrelated sentinel bytes remained intact. |
| Foundation/native ABI | 12 foundation tests and three Rust ABI tests passed against the final build. |
| Original contracts | All 154 tests passed (119 original plus 35 v2); these contract sources stayed unchanged after this run. |
| Original experiment regressions | All 60 tests passed; original experiment sources stayed unchanged. |
| Governance/format | Offline governance check passed; `git diff --check` passed. |

Additional executed regression commands:

```sh
PEAR_MANAGER_BUILD=.build/task9/stage2 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_foundation.py
.build/task9/venv/bin/python -B -m unittest discover -s tests/contracts -p 'test_*.py'
python3 -B -m unittest discover -s experiments/manager -p 'test_*.py'
python3 -B tools/check_governance.py
```

The [sanitized evidence](task_m1_9_stage2_evidence.json) records exact current source/binary hashes, independent markers, original/current inventory identities, test counts and local retained evidence locations. Private scratch paths/raw tool logs stay in ignored Task #9 evidence. Mounted images and disposable state were cleaned after relevant evidence was saved; no task data from another worker was removed.

Evidence reuse: all 58 original #3 input hashes and ten historical records remain unchanged. Its reproduction current-input checker still reports `source_or_history_identity` and `unit_test_accounting` because Stage 1 expanded its covered inventory; the historical JSON was not rewritten. Comparison consistency passes. These historical claims do not replace the current-manager 55 lifecycle cases or two pipe faults, which remain Stage 3 work.

Development failures are retained explicitly: an initial compile caught an incorrect use of the parser's string-validation method as an encoder; a small bounded metadata encoder fixed it. The first 133-case differential attempt had two failures: native module-content scope was overly strict and was corrected; one Python version-specific API refusal did not apply to native auto-version dispatch and was removed from that comparison, with both native versions independently tested. Later schema-edge coverage brought the final total to 133. Final required gates have no failures or skips.

## Residual Risks

- No real Wine/FEX/Steam/Megabonk execution, game qualification, signing/provisioning authorization or ordinary-user distribution claim follows. Synthetic policy acceptance cannot authorize real runtime execution.
- Admission is conservative: mutable-root names are currently ASCII, relative traversal has at most 32 components, and hard-linked selected files are refused. Unknown or unsupported forms fail closed; this is not every possible valid contract/path representation.
- Read-only media and cooperative leases protect the declared normal-user workflow. They do not constrain an administrator, hostile same-user backing-media/mount substitution, or arbitrary code outside the declared storage boundary. Backing-media ownership and digest checks do not establish stronger isolation.
- The declared dependency subset does not establish complete loaded-module coverage or arbitrary dynamic loading. #10 remains the independent observer integration dependency.
- ENOSPC/EIO were injected at explicit publication boundaries, not produced by exhausting a real disk or forcing physical storage failure. SIGKILL is not a power-loss durability test. A forced noexec remount was not performed; native mount-flag checks and real executable read-only mount use were performed.
- SIGKILL can leave private staging debris. Full child cleanup, dirty-run refusal/recovery, observer framing and durable lifecycle journals remain unimplemented Stage 3 work. No released lease/PID observation is presented as cleanup proof.

## Impact on Next Stage

Stage 3 can integrate the actual #3 foreground supervisor with the verified admission object and held version lease. It must retain the final native error propagation and selection identity checks, implement durable run-state refusal after abrupt death, and meet the approved observer frame/queue/deadline bounds. Keep the current-manager 55-case corpus and both pipe faults mandatory, with independently owned finite children, cleanup and unrelated-sentinel controls. Preserve the production runtime authorization refusal until real independent grants/observation are available.

## Approval Request

Review the Stage 2 implementation and evidence, then explicitly authorize Stage 3: foreground supervision, durable run-state handling, and bounded observer integration. This report does not authorize Stage 3, PR publication or merge.
