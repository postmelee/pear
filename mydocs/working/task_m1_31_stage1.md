# Task #31 Stage 1: Existing build timing evidence

GitHub Issue: [#31](https://github.com/postmelee/pear/issues/31)
Implementation plan: [task_m1_31_impl.md](../plans/task_m1_31_impl.md)
Stage: 1 — complete; Stage 2 awaiting explicit continuation.
Date: October 4, 2026 (Asia/Seoul).

## Stage Purpose

Preserve a bounded, sanitized projection of two existing #7 construction runs,
verify its source identities and arithmetic, and explain the timing boundaries.
This prepares subsequent diagnostic guidance without changing active builders.

Context: the [approved task plan](../plans/task_m1_31.md), implementation plan,
root documentation/evidence rules and existing technical-note template. Reuse
existing Python elapsed_ms records and pinned #5/#7 source. The task-stage-report
skill governs this bundled report/commit; no Apple technical skill is applicable
to host-only timing record analysis. All approved document locations are unchanged.

## Artifacts

| File | Change summary |
|---|---|
| mydocs/tech/20261004_build_timing_analysis.md | Dated findings, timer boundaries, source identity distinction and deferred questions |
| mydocs/tech/20261004_build_timing_analysis.json | Allowlisted two-run projection: 20 command durations, receipt/source hashes and derived values |
| mydocs/plans/task_m1_31.md | Record implementation-plan approval and Stage 1 completion |
| mydocs/plans/task_m1_31_impl.md | Record approved Stage 1 and verification outcome |
| mydocs/orders/20261004.md | Update only #31 status |
| This report | Performed verification, limitations and next-stage approval gate |

## Body Change Scope / Lossless Preservation

New research artifacts use the approved mydocs/tech location. Existing plans
retain their purpose, scope, location decisions and original dated observations;
only approval/status text changes. No official guide/index, agent rule, build
recipe, validator, CI, other task checkout, process or immutable evidence changes.
No other-thread communication or integration action occurred.

A selected-field projection is intentionally not a lossless copy of private
receipts. Raw paths, arguments, environments and diagnostics are excluded. Source
record hashes distinguish the projection from its originals. Publishing it does
not make full private provenance replayable.

## Verification Results

Execution context: Python 3.14.4, local Git and the existing offline governance
checker in the isolated codex/task31 checkout. This work performed source/record
inspection and arithmetic, not compiler/Ninja, host fixture, game or benchmark
execution. #7 source commit: e41b7bd7daaab707c3609693ff11e14af6f2d085.

### Source identity and values

- Both original build records and both wrapper receipts match the SHA-256 values
  already recorded in the task plan. All 20 selected command rows match both
  original build records and the pinned observation file.
- Four producer files from each original build (eight retained copies) match
  the receipt digests and corresponding pinned Git objects. The analysis records
  the four distinct source-file identities.
- The pinned observation file digest is 4c7bac2dbb731ddeaf40db01308d0a2a168c19d77b3c8e404342cb6ac26dece1.
  It differs from the historical working-copy digest in the plan. Investigation
  distinguishes those snapshots rather than replacing an expected digest. The
  original two runs and their measured values are unchanged. The old whole
  working-copy snapshot is not retained here; that limitation remains explicit.
- Source inspection confirms serial command spans and that shared-lock waiting
  and later qualification fall outside the wrapper timers. Supervision costs
  partly fall inside command times; log evidence bookkeeping partly falls outside.
- Independent Decimal arithmetic and Markdown row checks reproduce:
  902376 - 132326 = 770050 ms (85.34%), and
  893511 - 119568 = 773943 ms (86.62%).

### Performed checks

```sh
python3 -B tools/check_governance.py
git diff --check
```

Results: PASS: 22 documents, 172 local targets; skill routing and source inventory
consistent (offline). Whitespace checks passed. The checker has limited scan and
Markdown coverage, so the new analysis/projection and changed task artifacts were
also reviewed separately.

An in-memory Python audit checked closed field allowlists, original/pinned values,
producer hashes, Decimal percentages, exact Markdown table rows, local link
existence, trailing whitespace and private-path/credential markers. All passed.
Manual review confirmed no copied raw arguments/environments, qualified-support
claim, changed validation policy or out-of-scope source file.

The central arithmetic can be repeated using only the retained projection:

```sh
python3 -B - <<'PYTHON'
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
p = Path('mydocs/tech/20261004_build_timing_analysis.json')
for run in json.loads(p.read_text())['runs']:
    total = run['operator_receipt']['elapsed_ms']
    commands = sum(c['elapsed_ms'] for c in run['commands'])
    remainder = total - commands
    percent = (Decimal(remainder) * 100 / Decimal(total)).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP)
    assert run['derived']['command_sum_ms'] == commands
    assert run['derived']['unattributed_ms'] == remainder
    assert Decimal(str(run['derived']['unattributed_percent'])) == percent
    print(run['label'], commands, remainder, percent)
PYTHON
```

### Unperformed or unavailable

- Full source/toolchain provenance replay and all new builds, timing instrumentation,
  diagnostic Ninja runs, benchmarks, signing, native/game tests and CI were
  unperformed because they are outside this stage's scope.
- Individual preparation/verification region costs remain unmeasured. The
  remainder is not hashing time or a prediction of an achievable speedup.
- Immutable external source links were constructed from inspected local Git
  objects; remote availability is left to the subsequent documentation review.
- The original historical working-copy snapshot is unavailable as a retained
  artifact here; selected original build/receipt identities were verified instead.

A file-install permission review timed out before execution; it did not produce a
safety finding or alter files. A single shorter retry installed the five prepared
Stage 1 files successfully after checking destination originals were unchanged.
This operational retry did not change the analysis inputs or validation criteria.

## Residual Risks

- Two uncontrolled observations are not a representative performance benchmark.
- Receipt digests and selected fields do not establish full provenance qualification.
- The local originals may later be retired; the sanitized projection preserves
  its facts but cannot replace those originals for a full replay.
- Individual unmeasured phase costs and measurement overhead remain unknown.

## Impact on Next Stage

Write the guide only after approval. Start with attribution, preserve the timer
boundary caveats, verify Ninja examples against the pinned 1.13.1 source, and
separate targeted diagnosis from mandatory final fresh-build checks. No builder,
validator, CI or active task must be modified to write that guidance.

## Approval Request

Approve this Stage 1 evidence and verification to proceed to Stage 2: the official
build diagnostic guide and one docs-index link. Other-task messaging, integration,
merging and Issue closure remain deferred.
