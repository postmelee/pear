# Task #9 Stage 1: Reuse native foundations and version profile contracts

GitHub Issue: [#9](https://github.com/postmelee/pear/issues/9)
Implementation plan: [task_m1_9_impl.md](../plans/task_m1_9_impl.md)
Stage: 1
Date: October 8, 2026 (Asia/Seoul)
Status: complete; Stage 2 awaits explicit continuation.

## Stage Purpose

Establish the approved native Rust foundation and version 2 contract/oracle structure while reusing #3's implementation and preserving its v1 behavior and evidence. The requester approved this stage through the originating chat, with three narrow review supplements: purpose-specific admission, bounded observer transport and declared dynamic-library verification. Plans now contain the latter two stages' concrete required tests; they are not implemented or claimed as passed here.

Context used: root/runtime/host/tests rules; README, official index, architecture, delivery plan, runtime contracts, manager decision; approved plans, #3 Stage 5/final report and implementation; task/Git/conflict/document-location procedures and central stage template. `task-stage-report` and repository `todo` procedures apply, with root Codex branch naming (`codex/task9`). Apple Metal tooling is not applicable to this host/contract work. The supplied Apple run-path reference was inspected for Stage 2 planning, without adding a Mach-O framework.

The latest work inventory showed #9 open, #6 merged into master at `d019a6e`, and #8 active in its own worktree at `736b613`. Task9 remains on its approved base plus planning commits. No merge/rebase or other-task source/artifact change occurred.

## Artifacts

| File/group | Change Summary |
|---|---|
| `manager/AGENTS.md`, manifests, dependency inventory | Scoped native rules, unchanged exact #3 dependency/build profile and recorded reused review |
| `manager/src/`, `manager/native/` | Byte-identical strict parser; closed diagnostics; safe caller-owned identity/staging/hash wrappers; native ABI tests |
| `manager/examples/foundation.rs` | Bounded API test probe; not a product launch CLI |
| `runtime/contracts/v2/` | Seven closed schemas/common definitions, local registry and non-executable research/fixture examples; nullable profile selection facts and bounded metadata |
| `tests/contracts/validate_v2.py`, `v2_fixture.py`, `test_v2.py` | Version adapter over original parser/graph/policy; 35 v2 shape, purpose, privacy, version, path and budget tests |
| `tests/manager/` | Existing-helper build/capture adapter and 12 native/API/output-ownership tests |
| [Reuse record](../tech/task_m1_9_reuse.md) | Actual file/function reuse, system choices, small upstream decisions and remaining implementation boundaries |
| [Sanitized evidence](task_m1_9_stage1_evidence.json) | Exact current source/binary identities, observed tools, executed test inventories and historical/development limitations |
| Plans and daily board | Three approved review supplements, authorization record and Stage 1 completion checkpoint |

## Body Change Scope / Lossless Preservation

Locations match the approved plan. Existing public documentation was not edited in this stage; official interface guides remain scheduled for Stage 5. Added scoped rules accompany real manager code. The original v1 schema/registry/examples, `tests/contracts/validate.py`, original fixture factory and every #3 experimental source/history file remain byte-identical.

V2 reuses purpose-specific evaluation: a complete synthetic runtime candidate without prior game qualification is eligible for `qualification_run`; the same candidate is refused for `supported_launch` without matching qualification. Missing host, signing, source/build, observer, independent policy or owned-root/family prerequisites refuse. Fixture/research promotion, mixed versions, reserved environment overrides and arbitrary operations refuse. All such results are read-only synthetic evaluation, never authenticated runtime authorization.

The new profile metadata remains bounded and declarative. Unknown runtime family/renderer is inspectable; unknown save inventory cannot declare a writable mapping. Path observations and feature success cannot grant ownership or qualification. V2 allows streaming blob bounds of 8 GiB each/64 GiB aggregate; original v1 limits remain unchanged.

## Verification Results

Execution context: ARM64 macOS 26.5.2 (25F84), Xcode 26.6 (17F113), SDK 26.5, Apple clang 21.0.0, Rust/Cargo 1.94.1 and CPython 3.14.4. Native target is `aarch64-apple-darwin`, macOS deployment flag 26.0. These are observed development inputs, not a supported minimum OS or release/distribution result.

### Required setup and commands

```sh
python3 -m venv .build/task9/venv
.build/task9/venv/bin/python -m pip download --only-binary=:all: --require-hashes --no-deps -r tests/contracts/requirements.lock --dest .build/task9/wheels
.build/task9/venv/bin/python -m pip install --no-index --find-links .build/task9/wheels --require-hashes --no-deps -r tests/contracts/requirements.lock
cargo fetch --manifest-path manager/Cargo.toml --locked
python3 -B tests/manager/build.py --output .build/task9/stage1 --locked
.build/task9/venv/bin/python -B tests/contracts/validate.py --check-schemas --check-examples
.build/task9/venv/bin/python -B tests/contracts/validate_v2.py --check-schemas --check-examples
.build/task9/venv/bin/python -B -m unittest discover -s tests/contracts -p 'test_*.py'
python3 -B -m unittest discover -s tests/manager -p test_foundation.py
python3 -B -m unittest discover -s experiments/manager -p 'test_*.py'
python3 -B tools/check_governance.py
git diff --check
```

| Check | Actual result / claim |
|---|---|
| Dependency setup and locked/offline build | Passed; exact libc archive and 360 extracted source members checked; five reviewed wheels installed in task9 environment |
| Native Rust ABI tests (executed by builder) | 3 passed, zero ignored: preserved descriptor offset, invalid descriptor errno/cleared outputs, invalid staging template refusal |
| V1 + V2 contract suite | 154 passed, zero failures/errors/skips: original 119 plus new 35; synthetic policy evaluation only |
| Native foundation suite | 12 passed: actual hash vectors/multichunk/bounds/errors, 0700 staging, process identity, closed errors/parser controls, std lease contention/release/advisory write and safe build output scope |
| Existing experiment regressions | 60 passed; no new Rust/Swift comparison or full corpus execution |
| Both versioned schema/example CLIs | Passed; `evaluation_only: true` |
| Native package inspection | ARM64-only foundation executable, direct system dependencies libiconv/libSystem, linker ad-hoc signature verification/inspection; no provisioning/distribution authorization |
| Governance and whitespace | Passed; governance checked 25 documents / 231 local targets |

Native foundation SHA-256: `1b3d0a57437c5d837e270f7c14e4f38113a6c4d8ad0d4462a54ebc51f469c2ed`. The final build metadata binds 84 source inputs and actual compiler/linker settings. Current native tests verify receipt/source/binary agreement before execution. Local records are retained under `.build/task9/stage1/`; unique build logs and metadata remain available alongside the current `build.json`. Preserve these task-owned outputs through later stages/review; cleanup must not touch another task's artifacts. Public evidence contains summarized results and identities, not private tool paths or raw streams.

Development correction: the initial v2-only run had one test setup error among 35 tests: the aggregate budget was changed before constructing its schema registry, so registry validation correctly refused. Constructing the registry before the controlled budget reduction fixed the test. The subsequent full suite passed. The initial uncommitted snapshot was not retained; the tool output and summarized failure remain recorded. No failed run is presented as passing evidence.

### Historical evidence consistency

```sh
python3 -B experiments/manager/reproduce.py --check-report experiments/manager/results/reproduction.json
python3 -B experiments/manager/compare.py --check-report experiments/manager/results/comparison.json
```

The original comparison record remains consistent. The reproduction current-input check reports `source_or_history_identity` and `unit_test_accounting`: three new contract Python files and 35 tests expand its original inventory. This is the planned evidence-scope invalidation, not a waived implementation failure. Independently compared all 58 original input hashes and all ten retained history records: unchanged. The historical reproduction JSON still hashes to `a214a305dde1d3c05aed9eb4409cd7d12495c3c58d2acf83126e37830f7e291a`; it was not rewritten. Current Stage 1 evidence is separate.

## Residual Risks

- Native v2 admission, real host/signing/ownership/observer authorization and actual runtime execution are unperformed. Synthetic oracle inputs cannot supply those grants.
- Read-only payload mounting, at-use entry resolution, executable/dylib replacement controls and dependency admission are unperformed Stage 2 gates. Static inventory is not #10 complete loaded-module observation.
- Observer deadlines/partial frames/backpressure, cancellation, owned cleanup and crash refusal are specified but unimplemented Stage 3 work. Std file lock release is not proof that children were cleaned up or arbitrary writers were prevented.
- The actual current-manager 55 cases and both pipe faults remain required in Stage 3. Their original source/history is preserved; earlier #3 startup failures remain unresolved.
- This foundation does not qualify Wine, Steam, Megabonk, full Rosetta-independent execution, saving/recovery or ordinary-user distribution. No GUI, updater, custodian or game-specific branch was added.

## Impact on Next Stage

Stage 2 can reuse the verified native wrappers/parser and exact locked build inputs. It must implement generic native contract/policy consumers with the purpose table, independently granted actual execution conditions and actual immutable read-only entry/dependency tests. The approved small executable/dylib cases must show the selected internal bytes execute and writable/external/replaced candidates refuse or retain those bytes. Unsupported dynamic loading remains an explicit limitation; #10 owns actual module observation.

Stage 3 inherits the absolute 1,500 ms observer deadlines, bounded frames/queues and nonblocking loop requirements from the supplemented plan. These were not pulled into Stage 1. Later integration must preserve master/#6/#8 and concurrent board/doc changes under the repository's explicit integration decision.

## Approval Request

Approve the Stage 1 artifacts and verification results, then authorize Stage 2: native admission and immutable payload activation, including the approved purpose and dynamic-library controls. No later stage is authorized by this report.
