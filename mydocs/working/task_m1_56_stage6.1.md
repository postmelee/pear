# Task #56 Stage 6.1 — runtime admission and manual confirmation fixes

GitHub Issue: [#56](https://github.com/postmelee/pear/issues/56)
Implementation plan: [task_m1_56_impl.md](../plans/task_m1_56_impl.md)
Stage: 6.1

## Stage Purpose

Correct PR #58's reproduced P1 runtime-import mismatch and inherited P2 manual
confirmation failure under the requester's October 17 continuous authorization.
Context: root/test rules, the approved remediation plan, source-notice and artifact
retention procedures, and `task-stage-report`. Existing frozen runtime/producer
paths remain preserved; this stage changes a separate mutable Pear checkout.

## Artifacts

| File | Change summary |
|---|---|
| `tools/development/runtime_candidate.py` | Always promote admitted roots, preflight ordinary bootstrap source/package specs, preserve loaded-origin refusals and recheck imported modules |
| `tools/development/game/handoff.py` | Verify a deep copy, enforce its derived expiry and retain original control identity for repeat/finish |
| Two affected test files | Nine selector methods and three manual methods (seven scenarios); generated fixture notices included |
| `tools/development/game/import-provenance.json` | Explicit behavioral adaptation and new-test identities; original provenance retained |
| `.github/workflows/documentation.yml` | Add the self-contained selector suite to existing portable CI |
| Plan, daily board and [machine-readable results](task_m1_56_stage6.1.json) | Approved scope, measured sequential checks and frozen source facts |

## Body Change Scope / Lossless Preservation

The selector retains its CLI/schema and complete producer validator; intentional
FEX namespaces are unchanged. Bootstrap checking uses standard Python import
machinery. Manual verification/adapter bodies stay unchanged. Reversing exactly
three AST changes in the handoff restores its entire previous module AST. The
original three joint-test bodies and all earlier expiry, terminal, identity,
stop/join and cleanup oracles remain intact. Imported MIT terms are preserved;
new selector/CI source and generated fixtures retain GPL notices.

No component runtime, candidate, old producer source, Preview resource or existing
selected state changed. New metadata binding is a separate next checkpoint.

## Verification Results

Execution context: Python 3.14.4 on ARM64 macOS; source and synthetic fixtures only.
The exact source/receipt hashes and UTC/monotonic intervals are in the JSON report.
Commands ran serially from the new checkout:

```sh
python3 -B -m unittest discover -s tests/development -p 'test_runtime_candidate.py' -v
PYTHONPATH="$PEAR_RUNTIME_SOURCE:$FEX_SOURCE" python3 -B -m unittest discover -s tests/development/game -p 'test_*.py' -v
python3 -B -m unittest discover -s tests/docs -p 'test_*.py' -v
python3 -B tools/check_source_notices.py --base 914725732a17b9e13886bc906625df9ca9ba07b3
git diff --check
```

- Selector: **47 passed**, including fresh CLI precedence and source/spec/path
  refusals. The final fixture-header revision was rerun (6.551 seconds).
- Game policy/context: **133 test executions passed**, including repeat → hold →
  matched finish, altered control/finish refusal and expiry after verification,
  stop and probe (1.141 seconds). Inherited methods are not counted as new bodies.
- Documentation/source-notice tooling: **94 passed** (6.224 seconds).
- Both new positive regressions were also run against preserved `9147257` source:
  P1 returned the unadmitted context; P2 raised `play_finish_identity` on the next
  tick. The negative-control assessments confirmed those expected old defects;
  they are not failures of the corrected source.
- Static provenance audit: 21 original file records, 149 destination unit
  identities and seven unchanged new-source refs; all original joint methods
  exact. Independent source reviews found no further blocker.
- Incremental source notices and whitespace passed. Protected inspection found
  no differences in 34,182 original analysis/research files, 190 Preview/#47 files,
  92 old producer facts, ten builders, three ignored old worktree records and
  three existing selection records.

Evidence reuse: earlier native/control results remain historical because their
runtime sources, payloads and candidate are unchanged. They do not establish the
corrected selector's admission, which receives fresh real metadata checks in
Stage 6.2. No build/signing, native fixture, game, user input or interactive latency
measurement occurred here. The new manual source has portable evidence only.

## Artifact Disposition

| Artifact | State and consumer | Release condition |
|---|---|---|
| Original Pear `9147257` producer checkout | Same files/path, detached and locked; v5 diagnostics and ignored evidence still depend on it | Explicit replacement of every consumer |
| New correction checkout | Source on `codex/task56`; will become a new producer root in Stage 6.2 | Keep if new bindings depend on its path |
| Existing component roots/candidates/input packs/state | Retained unchanged | Existing recorded consumer/recovery release events |
| Private regression/provenance receipts | Retained, compact; original defect evidence preserved | Subsequent evidence/dependency review |

Source-only planning allowed 512 MiB additional plus 1 GiB reserve. No full runtime
copy or substantive build occurred and no artifact deletion was performed.
Original filesystem free space was 22,887,006,208 bytes, a dated whole-filesystem
observation rather than recovered space. Per-suite timing is diagnostic, not a
performance claim.

## Residual Risks

New actual fixture/game metadata has not yet been admitted. The absent historical
494-byte frame request needs bounded exact restoration. Megabonk loading/EC-gate,
WGI causality, complete no-Rosetta coverage and player qualification remain outside
this correction's claims.

## Impact on Next Stage

Bind this committed source in separate developer metadata, check actual admission,
preserve old selection/environment, update the final handoff and review current CI
before the conditional merge.

## Approval Request

The requester already approved fixes, regression, subsequent validation and
conditional merge/Issue closure/limited branch cleanup. No repeated stage approval
is pending; expanded deletion or existing-environment changes remain excluded.
