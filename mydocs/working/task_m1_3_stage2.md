# Task #3 Stage 2: Versioned contracts and semantic eligibility

GitHub Issue: [#3](https://github.com/postmelee/pear/issues/3)
Implementation plan: [`task_m1_3_impl.md`](../plans/task_m1_3_impl.md)
Stage: 2
Date: September 28, 2026

## Stage Purpose

Implement and test the seven version 1 record contracts, separating readable/consistent records from eligibility for a requested use. Preserve incomplete research, exact byte identity, independently supplied trust policy, process observation and privacy boundaries before native manager experiments.

## Artifacts

| File or directory | Change Summary |
|---|---|
| `runtime/contracts/v1/` | Seven closed Draft 2020-12 schemas plus common definitions. Launch request/event are variants of one kind. |
| `runtime/contracts/contract-index.json` | Experimental registry now identifies implemented schemas and the bounded Python reference validator. |
| `runtime/contracts/examples/` | Updated valid incomplete research example; owned non-executable fixture blobs and an acyclic record bundle. |
| `tests/contracts/validate.py` | Read-only parsing, schema/reference checks, byte verification, semantic consistency and purpose-specific eligibility evaluation. |
| `tests/contracts/fixture_factory.py` | Generates independent owned temporary fixtures and repairs declared test references after deliberate mutations. |
| `tests/contracts/test_structure.py`, `test_eligibility.py`, `test_paths_and_privacy.py` | 119 tests, including 39 independently authored path/privacy cases. |
| `tests/contracts/requirements.lock`, `dependencies.json` | Exact five-wheel dependency lock and source/notice/setup observations for CPython 3.14 on macOS ARM64. |
| `docs/runtime-contracts.md` | Updated implementation status, setup/CLI, exact limits, external policy, module attribution, causal events and remaining work. |
| Plan, daily board and this report | Stage authorization/completion and the next approval checkpoint. |

Negative fixtures are generated in owned temporary directories by `fixture_factory.py`; committed reusable examples remain in the approved `runtime/contracts/examples/` location. There is no duplicate static negative-fixture corpus. Wheels, venv, bytecode and raw outputs remain ignored under `.build/task3/` or existing bytecode exclusions.

## Body Change Scope / Lossless Preservation

Changes stay within the approved contract, test, contributor-specification and workflow-record locations. The existing ownership/identity specification was read before updating its stale Stage 1 status and adding the implemented interface details. Stage 1 report, architecture/delivery plans, Issue #1 inventory, Issue #2 source/evidence and operating manuals remain unchanged.

The reference tool does not launch anything. It does not implement the production supervisor, trust service, observer, file installer, Steam authentication, binary architecture inspector or signing verifier. Synthetic runtime-policy tests deliberately model independently trusted declarations using owned text bytes; those bytes are not real Mach-O images, source archives, signatures or game evidence. No manager language is selected.

## Verification Results

The exact setup procedure in the approved plan completed in the task-local environment after reviewing official package metadata, wheel hashes, active dependency markers and packaged license texts:

```sh
python3 -m venv .build/task3/venv
.build/task3/venv/bin/python -m pip download --only-binary=:all: --require-hashes --no-deps -r tests/contracts/requirements.lock --dest .build/task3/wheels
.build/task3/venv/bin/python -m pip install --no-index --find-links .build/task3/wheels --require-hashes --no-deps -r tests/contracts/requirements.lock
```

Actual setup: CPython **3.14.4**, Darwin ARM64; `jsonschema 4.26.0`, `attrs 26.1.0`, `jsonschema-specifications 2025.9.1`, `referencing 0.37.0`, `rpds-py 2026.6.3`. Five wheel byte hashes/sizes and dependency metadata were independently checked; declared license files were read. Exact URLs/hashes and active package versions are in `dependencies.json`. Its setup observations and tool transcript record the commands; no separate persisted raw installation log is claimed. The native `rpds-py` wheel is platform/interpreter-specific, and no source-build reproducibility or independent attestation is asserted.

After freezing the final implementation and tests, the following planned commands ran together:

```sh
.build/task3/venv/bin/python tests/contracts/validate.py --check-schemas --check-examples
.build/task3/venv/bin/python -m unittest discover -s tests/contracts -p 'test_*.py'
git diff --check
```

| Check | Actual result | Scope |
|---|---|---|
| Schema registry, local references and examples | Exit 0; `record_valid: true`, `eligible: true`, empty outcome codes, `evaluation_only: true` | Experimental schema/example checks; the eligible requested use is evaluation, not real execution. |
| Full frozen unit-test suite | **119 tests passed in 20.219 seconds**, exit 0 | Structure, semantics, external-policy evaluation, paths/privacy and resource bounds. Duration is not a performance comparison. |
| Independent path/privacy suite | 39 tests passed; case-folding and hard-link cases exercised on this Mac | Real CLI checks, bounded diagnostics, no source/system/game execution. Included in the 119 total. |
| Additional independent semantic probes | Three positive controls and six contradictory variants behaved as expected | Exact selected entry, artifact module identity, separately attributed system modules and required-process accounting. Owned temporary data only. |
| Wrong causal-ready target probe | Rejected with `invalid_ready_ack` | A renamed gap event cannot serve as the launch acknowledgement. Durable regression included. |
| JSON and document-link review | 24 JSON documents parsed; relative Markdown targets resolve | Supplemental artifact consistency check. |
| Whitespace and final file review | `git diff --check` exit 0 | Only owned text fixtures/source/docs staged; private payloads and local environment stay ignored. |

Final command outputs are retained locally in `.build/task3/stage2-final/verification.json` and the paired `check-*.stdout` / `check-*.stderr` files. Earlier development exposed an aliased-record error-precedence assertion and a targeted-test import-path invocation error; both were corrected before the final combined passing run. Neither is presented as a runtime failure or passing test.

### Reviewed boundaries and fixes

- Research records can be inspected without complete source/build identity, but cannot authorize execution. Fixture context cannot be promoted into real qualification. Runtime evaluation requires attributable source inventory, explicit build configuration/triples, compatible native declarations and independently approved inputs.
- Records use exact stored-byte SHA-256 and typed reference scopes. Duplicate keys/IDs, malformed UTF-8 or Unicode scalar values, unsupported numbers/versions/fields, cycles, wrong kinds, corrupt bytes and signature-versus-payload confusion are rejected.
- Input bounds cover per-file/aggregate JSON and blobs, depth, nodes, records and references. Symlinks/nonregular references are rejected without following external paths or waiting on FIFOs. Diagnostics omit private paths, arguments, raw input and environments.
- Independent review reproduced mutable paths overlapping immutable blobs, including case-folded paths and existing hard-link aliases. The implementation now rejects these with `immutable_path_overlap`, using bounded metadata checks. This does not eliminate future filesystem races; #9 must enforce ownership again at use time.
- A supported request must select the same host entry exercised by its qualification. Required module expectations bind ID, kind, origin and observed hash; artifact modules also match the selected artifact file. System/game observations retain evidence and hashes without copying their binary payloads into the fixture or public bundle.
- Required-process accounting includes the profile, external policy and the run's own declarations. Missing required helpers cannot disappear by shrinking a submitted list. Host ARM64/translation observations remain distinct from expected guest x64/i386 execution.
- `ready_ack` and `completed_exits` provide causal references across observer/supervisor streams. Missing/wrong acknowledgements, gaps, omitted events, wrong process generations, incomplete shutdown and stale/mismatched qualification are rejected. Shared timestamps alone are insufficient.
- The external policy is caller-selected outside the bundle; record digests, reviewer names and support labels cannot grant their own trust. Every response remains `evaluation_only: true`. Public partial derivatives are inspectable but cannot supply full execution/qualification evidence.

## Residual Risks

- This checks supplied records and declared facts under a caller policy. It does not independently establish observer authenticity, executable architecture, signature validity, license suitability or actual gameplay. Trust distribution and production producers remain unimplemented.
- The bounded corpus, 128-record/64-reference limits and shared-clock event model are reference constraints. Full Steam/process/module traces may need an explicit versioned extension after real integration requirements are measured; they must not silently drop required evidence to fit these limits.
- Filesystem state can change after validation. #9 must repeat identity/ownership enforcement during actual operations; the current evaluator performs no writes.
- The Python dependency lock is scoped to the recorded platform/interpreter, includes one native wheel and is not the eventual manager's dependency choice.
- No Rust/Swift prototype, restricted host probe, actual source build, Steam/game execution, performance qualification or ordinary-user distribution test occurred.

## Impact on Next Stage

Stage 3 can now use a shared tested contract corpus and reference outcomes for equivalent bounded Rust and Swift experiments. Preserve raw parser rejection, explicit native host identity, ownership, event-causality and privacy requirements across both implementations. Dependency selection must follow the approved pin/review procedure. Stage 4, not these Python tests, makes the measured manager-language decision.

## Approval Request

Review the Stage 2 specification, implementation and passing results. Approval to proceed authorizes Stage 3's equivalent native Rust/Swift experiments within the existing plan and document locations. Stage 3 has not started; no production manager, runtime port or game qualification is authorized by this report itself.
