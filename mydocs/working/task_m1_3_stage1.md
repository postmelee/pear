# Task #3 Stage 1: Contract boundaries, identity and handoff

GitHub Issue: [#3](https://github.com/postmelee/pear/issues/3)
Implementation plan: [`task_m1_3_impl.md`](../plans/task_m1_3_impl.md)
Stage: 1
Date: September 28, 2026

## Stage Purpose

Define the seven planned product-record kinds and their ownership, source handoff, content identities, execution boundaries and evidence meaning before writing schemas or manager prototypes. Stage 1 implements only design documentation and honest draft JSON artifacts; it does not establish executable validation or a working runtime.

## Artifacts

| File | Change Summary |
|---|---|
| `docs/runtime-contracts.md` | New 143-line proposed specification covering the seven kinds, layered validity/eligibility, exact-byte identity, acyclic references, #1 handoff, #9/#10 ownership/readiness, mutable storage and privacy. |
| `runtime/contracts/contract-index.json` | New 78-line registry listing seven unique planned version 1 schemas and shared definitions; schemas and validator explicitly marked not implemented. |
| `runtime/contracts/examples/research-lock.json` | New 129-line incomplete research example for intended Wine/FEX/DXMT labels. It selects no actual source URL, revision, hash, toolchain, target or verified terms; unknowns have reasons. |
| `mydocs/working/task_m1_3_stage1.md` | This Stage 1 verification and handoff report. |

## Body Change Scope / Lossless Preservation

The stage adds three approved artifacts without rewriting existing architecture, research, delivery plans, shared indexes or operating manuals. Issue #1's source inventory remains separately owned, and Issue #2's source/evidence stays unchanged. The coordinator separately manages approval-status and daily-board updates; this report does not claim those edits as contract implementation.

The specification explicitly refines architecture section 7's qualification presentation: a later `qualification` record supplies the status overlay for an immutable artifact/profile. Adding the qualification digest to the artifact that it qualifies would create an identity cycle, so this stage prohibits that forward reference. No architecture-file modification was made.

Independent review requested two clarifications, both incorporated before final checks: redacted exports have distinct immutable derivative identities and explicitly incomplete public disclosure; consumer trust/reviewer/evidence policy comes from outside supplied JSON. These are design boundaries, not a new trust service, PKI or export implementation.

## Verification Results

Exact Stage 1 commands were run from the `codex/task3` worktree and repeated after the review clarifications:

```bash
python3 -m json.tool runtime/contracts/contract-index.json > /dev/null
python3 -m json.tool runtime/contracts/examples/research-lock.json > /dev/null
git diff --check
```

| Check | Actual result | Scope |
|---|---|---|
| Registry JSON command | Exit 0; no output | JSON syntax parses; no schema validation is implied. |
| Research-example JSON command | Exit 0; no output | JSON syntax parses; no executable lock or semantic pass is implied. |
| `git diff --check` | Exit 0; no warnings | Tracked diff whitespace check. New untracked artifacts were additionally inspected directly, as below. |
| Read-only design-inventory inspection | Passed | Exactly seven unique planned kinds; all use schema version 1, no listed schema files exist, and no schema/validator implementation is claimed. |
| Research-example inspection | Passed | Research context, null source-inventory reference, incomplete coverage, null upstream refs/hashes and empty evidence remain explicit. |
| Direct file/link inspection | Passed | All three new files have no trailing whitespace. The specification's local Markdown targets exist; planned schema paths remain plain metadata, not links claiming existing files. |
| Independent design review | Clarifications incorporated | No identified remaining ownership, source-handoff, identity-cycle, qualification-bootstrap or draft-status blocker. |

Design review traced an incomplete research lock through the intended rejection: absent verified identities, compatibility family, dependency coverage, host/signing requirements and evidence prevent runtime launch and qualification. This was a specification review, not an executed semantic-validator test. Changing the context string cannot supply those facts.

The handoff preserves #1's factual audit and local format, while #3 owns product representation. Its `go`/`needs-port`/`blocked` result is not a built-runtime or support result. The supervisor alone owns creation/reaping/termination and mutable state; the observer owns attribution/readiness/coverage and cannot signal or reap the supervisor's children. Process attribution requires more than a reusable PID.

No schema, production validator, prototype, package installation, build, signing operation, restricted host probe, Steam/game launch, or runtime qualification was performed in this stage. No source hash or upstream version was invented.

## Residual Risks

- The registry is still a draft inventory: planned schemas and semantic checks do not exist. JSON parsing cannot detect or enforce all intended rejection rules.
- Exact field constraints, parser/collection limits, stable error codes, disclosure representation and consumer trust-policy integration still require Stage 2 design details and tests within the approved scope.
- Actual #1 source/build integration and complete #9/#10 lifecycle/observation behavior are unverified. This stage's interface design cannot prove that short-lived or detached Steam helpers will be observed.
- The qualification overlay and public derivative rules need consumer enforcement; self-asserted JSON and matching digests cannot establish trustworthy support by themselves.
- No manager language is selected, and no Rosetta-free runtime, game support or ordinary-user distribution capability is established.

## Impact on Next Stage

- Stage 2 must implement the seven schemas plus shared definitions and an independent reference validator with separate structural, semantic and requested-use outcomes.
- Preserve exact-byte digest scope, acyclic references, research/fixture/runtime separation and the qualification-run versus supported-launch distinction. Test duplicate raw keys before parsing loses them, bad identities, incompatible records, unsafe paths, wrong evidence and incomplete disclosure.
- Accept the research example as an honest incomplete record only after the actual schema/semantic tests establish that behavior; separately prove it cannot authorize execution or qualification.
- Resolve and verify exact JSON Schema tooling versions and wheel hashes in a task-local environment before use. No dependency setup occurred in Stage 1.
- Continue #1 coordination at the field-meaning level without adding a completion dependency or importing guessed pins. Leave #2 evidence unchanged and leave production #9/#10 behavior to its owning issues.

## Approval Request

Review the Stage 1 design artifacts and the limited verification above. Approval to proceed authorizes Stage 2's versioned schemas, reference eligibility validator and rejection fixtures under the approved implementation plan; it does not authorize a production manager or game execution. Stage 2 has not started.
