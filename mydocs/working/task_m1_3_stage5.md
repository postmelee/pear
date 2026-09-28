# Task #3 Stage 5: Clean-output reproduction and final handoff

GitHub Issue: [#3](https://github.com/postmelee/pear/issues/3)
Implementation plan: [task_m1_3_impl.md](../plans/task_m1_3_impl.md)
Stage: 5
Date: September 28, 2026

## Stage Purpose

Rebuild the contract validator environment and native experiments in empty outputs, verify the declared behavior against retained Stage 4 evidence, and finalize the source/manager/observer handoff. This completes Issue #3's contract and language-decision work, not a production manager or Rosetta-free game runtime.

Context used: the approved task/implementation plans, [runtime contracts](../../docs/runtime-contracts.md), [manager decision](../../docs/decisions/manager-language.md), Stage 1–4 reports, actual #1 inventory and source guide, and the root workflow rules. The newly merged #25 root/docs/tests rules and updated report template were also read for final integration. Reuse: existing `build.py`, `run_cases.py` and `compare.py` supply locked builds, owned fixtures, bounded command capture, package inspection and the retained comparison checker. Upstream runtime languages and dependencies are unchanged. No Metal work is performed, so the Apple Metal expert skill is not applicable. Stage reporting follows Hyper-Waterfall v0.3.0.

## Artifacts

| File | Change Summary |
|---|---|
| `experiments/manager/reproduce.py` | Restricted empty-output runner, fresh offline validator setup, locked native rebuild, complete checks and sanitized report consistency validation. |
| `experiments/manager/test_reproduce.py` | 20 meaningful path-preservation, input-identity, missing/contradictory-evidence and privacy regressions. |
| `experiments/manager/results/reproduction.json` | Reviewed same-Mac result with 58 input-file hashes, ten retained historical JSON hashes, exact test IDs, all native case outcomes, binary identities and limits. |
| `docs/runtime-contracts.md` | Actual blocked #1 handoff; opaque audit-reference boundary; distinct readiness/backend replies and production ownership. |
| `docs/decisions/manager-language.md`, experiment README | Reproduction commands/results, unchanged language choice, measured versus unmeasured scope and payload differences. |
| `docs/README.md`, `docs/architecture.md` | Narrow links and current manager/contract status. |
| Implementation plan, daily board and final report | Authorization, completed verification, Issue acceptance mapping and publication checkpoint. |

## Body Change Scope / Lossless Preservation

All artifacts use the approved locations. No existing native implementation, corpus budget, schema, reference validator, dependency lock or comparison plan changed in this stage. Prior comparison results and startup failures remain byte-for-byte retained. Stage 1–4 reports, #1 source findings and #2 host evidence are preserved. No actual runtime lock is manufactured from the source inventory.

Only reviewed structured text is committed. Raw command streams, private paths, fixture bundles, executables, wheels, venv and Cargo build products remain ignored. The runner rejects broad/absolute/traversing or symlink output paths and nonempty destinations, including internal suite-output overrides; it never deletes an old attempt. Existing installed toolchains and verified Cargo source caches remain shared inputs. This fixture harness is not a hostile-code sandbox or a production supervisor.

## Verification Results

Execution context: the same Apple M4 Pro Mac, CPython 3.14.4 on Darwin ARM64, macOS 26.5.2 (25F84), Xcode 26.6 (17F113), SDK 26.5, Apple clang 21.0.0, Swift 6.3.3 and Rust/Cargo 1.94.1. These are recorded experimental inputs, not release requirements. Correctness checks were run separately from the Stage 4 timing comparison.

The planned commands passed:

```bash
python3 experiments/manager/reproduce.py --output .build/task3/reproduction --require-empty
python3 experiments/manager/reproduce.py --check-report experiments/manager/results/reproduction.json
git diff --check
git status --short
```

The first reproduction attempt completed from **14:37:22 to 14:38:16 UTC**. There was no failed native-reproduction attempt, retry or benchmark rerun in Stage 5. Implementation review and focused tests preceded the run.

| Check | Actual result and scope |
|---|---|
| Dependency reconstruction | Five pinned wheels rehashed, copied and installed with `--no-index --require-hashes --no-deps` into a fresh venv; installed versions match the lock. Exact `libc` archive/extracted sources reverified; Cargo builds/tests use `--locked --offline`. Swift has no external packages. No dependency acquisition requested. |
| Schema/example CLI | Exit 0; valid and eligible for evaluation, `evaluation_only: true`. |
| Contract reference suite | **119/119 passed**, with every test ID recorded; no skipped or omitted test. |
| Experiment suite | **60/60 passed**: 40 existing tests and 20 new reproduction checks, with exact IDs. |
| Native builds and package inspection | C child, Rust manager and Swift manager rebuilt in new outputs. Each has only ARM64, macOS 26.0/SDK 26.5 metadata and passing read-only strict linker ad-hoc signature checks. No Developer ID or distribution qualification. |
| Common native corpus | **55 cases × two candidates = 110/110 passed**. Each expected rejection, success/failure classification, independent oracle outcome, bound, native state, owned cleanup and sentinel assertion passed. |
| Fault injection | **2/2 Rust tests passed**: each failed pipe-setup position closes descriptors, bounds cleanup, reaps the direct child and preserves the unrelated sentinel. |
| Semantic reproduction | All projected outcomes match the retained final Stage 4 corpus. Ordinary functional budget remains 5,000 ms; deliberate timeout 1,500 ms; cleanup two seconds; outer watchdog ten seconds. Required traces are not waived. |
| Retained comparison | Existing comparison checker passes; all prior result hashes and 82 timing rows remain unchanged. Scored 1,500 ms measurements were not repeated or pooled. |
| Report consistency | Both local and committed report checks exit 0, `report_valid: true`; current input/history identity, full test/case coverage, semantics, dependency and package fields pass. This is not independent authenticity verification. |
| Independent review | Output-path bypass, interpreter-path normalization and exact trace accounting were corrected before execution; regression tests cover them. Source/ownership document review accepted the final boundaries. |

The public record SHA-256 is **`a214a305dde1d3c05aed9eb4409cd7d12495c3c58d2acf83126e37830f7e291a`**. It is the same byte content as the checked local `.build/task3/reproduction/reproduction.json`; raw logs remain in that ignored directory. Its input map identifies the exact runner, tests, reference implementation, schema/example bytes and native sources. Report checking does not rerun those observations.

### Payload differences

| Rebuilt payload | Bytes | SHA-256 |
|---|---:|---|
| Owned C child | 34,720 | `0a12bd061ad26750cfc45d9eefaed6d314cfc89999e1224599056ba7b5223e47` |
| Rust manager | 544,816 | `4e4112403caeb997f8f17c1abf457f39c2b9919f0c8b96105a8bae792a84dbdf` |
| Swift manager | 246,416 | `23f345166669750f044acdf5712ea6adfc2a9ef52f74d876605adcf4f2975f98` |

Both manager hashes differ from Stage 4's measured outputs. Rust's size is unchanged; Swift's measured output was 246,608 bytes. Build location, compiler metadata, linker UUIDs and ad-hoc signatures can affect binary identity; their individual contribution was not measured. The approved criterion is matching semantic behavior on recorded payloads, not byte-identical signatures. These results do not establish a byte-reproducible toolchain.

### Actual source and ownership handoff

PR #26 merged at `3ad083075ba46522d4d01764e2ba453a89a1436d`, and #1 is closed. Its manifest SHA-256 is `535cdcb7b2e76d4bc536d63ad7d17d31f562f438b7850a75a0ace1b9c88466b8`: `audit_complete: true`, `decision: blocked`, `source_ready: false`; runtime/game/distribution remain unassessed. This is read-only field/evidence review, not another acquisition/build or an automatic import. The product validator checks the typed `source_inventory_ref` bytes but does not interpret the audit decision. The independent authority approving exact runtime inputs must review source readiness; a completed audit does not establish component closure, an artifact or support.

#9 alone owns spawning/reaping/termination, immutable artifact activation and mutable-state recovery. #10 owns attributable observation and gaps. Its exact-request `ready_ack` is separate from backend synchronous replies and child startup progress. Real coverage, bounded callback work, cancellation/crash handling, detached helpers and at-use ownership remain their implementation obligations.

## Residual Risks

- This reused installed toolchains, SDK, machine caches and hash-verified Cargo sources on the same Mac. It is not a clean-machine, external-host, older-OS or source rebuild of third-party wheels.
- Historical 1,500 ms startup failure remains unexplained. Wider functional success does not guarantee startup deadlines or demonstrate that an OS/monitor issue was fixed.
- Native prototypes implement a four-record fixture subset; Python evaluates all seven contracts. Neither is the full production manager, source approval authority or observer.
- Concurrent mutation/pathname execution races, real helper ownership, trust distribution, ordinary-user signing and game behavior are not qualified.
- No Wine/FEX/DXMT port/build, Steam sign-in, Megabonk run, power/FPS comparison or complete Rosetta-free runtime verification occurred.

## Impact on Next Stage

All five #3 stages are complete. Rust remains the selected implementation direction for the new #9 supervisor; Swift UI and upstream implementation languages remain independent. Actual runtime/source blockers and #9/#10 obligations stay visible. The [final report](../report/task_m1_3_report.md) maps acceptance to evidence; publication is the next approval checkpoint.

## Approval Request

Review the final report and approve #3 PR publication. This report does not authorize self-merge, Issue closure or a new production implementation stage.
