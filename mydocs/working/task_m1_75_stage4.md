# Task #75 Stage 4 — Complete FEX notices and publish review handoff

GitHub Issue: [#75](https://github.com/postmelee/pear/issues/75)
Implementation plan: [task_m1_75_impl.md](../plans/task_m1_75_impl.md)
Stage: 4

## Stage Purpose

Resolve the specific adjacent-notice prerequisite for three FEX diagnostic
headers, verify the exact successor and publish the completed Task75 work for
review. The requester authorized this extension on 2026-10-21, while excluding
visibility conversion, merge, game execution and artifact deletion.

Context used: the approved Stage4 location/reuse/retention decisions, existing
source-notice rules, upstream FEX policy, original MIT-marked source captures,
and the repository's task-stage-report/task-final-report procedures. Existing
upstream license text and generation evidence are reused; no subsystem or
generator implementation is introduced.

## Artifacts

| File / output | Change summary |
|---|---|
| FEX `Pear/Diagnostics/include/NOTICE.md` and existing README | Exact provenance, MIT clauses and missing-attribution disclosure |
| FEX `mydocs/working/task_m1_75_stage4.md` | Component verification and preservation record |
| Current Pear readiness/final report | Updated successor decisions and four component PR links |
| Plans, this report and daily board | Explicit extension, verification, retention and publication handoff |
| Four private component PRs; coordinating Pear PR | Review branches with unchanged integration defaults |

## Body Change Scope / Lossless Preservation

FEX commit `97a52dd11128ffc866a127dc43fdca9e8a1c5dd9` changes three Markdown
files only, based on `4ae26ddf9a21b52cd50d096504c4d0ea5ab49204`. The notice
documents three exact outputs and six retained MIT-marked source/schema inputs,
including the 56-byte target-header addition. It preserves the absent original
holder and introducing-commit facts rather than inventing either. Existing MIT
clauses are reproduced exactly without attributing FEX upstream copyright to
the Pear templates or asserting a new grant.

The frozen headers, all ten provenance files, upstream README/license/policy and
notice-exception policy are unchanged. Pear's dated Stage1–3 reports and
publication-detail JSON remain intact; current summaries explicitly label their
older unpushed/zero-PR state as snapshots. Document locations match the approved
plan. WGI source, build inputs, selected runtime pins and product resources are
unchanged in Stage4.

## Verification Results

Execution context: existing Apple Silicon macOS 26.5.2 host. FEX checks used
Python 3.13.5; Pear document checks used Python 3.14.4 and Git 2.53.0. These are
source/documentation and synthetic checks, not native or gameplay qualification.

Evidence reuse: the five runtime Stage3 delta files at
`db95ed3278d9d20233fbd395665f3d39c3a4b13d` match their previously reviewed
hashes. The 43 guarded methods and successful 66-command reconstruction are
reused within their exact recorded input/scope boundary; neither was rerun in
Stage4. Test receipt: `6b8c4c3ae80c30d881b9c9bd9baaab543a4ffd2bdf433d8a0cacc83c58c1b791`.
No pass flag substitutes for live ownership or publication authorization.

Commands run in the relevant isolated checkout:

```sh
python3 -B Pear/Tools/check_source.py \
  --runtime-root "$RUNTIME_SOURCE_ROOT" --wine-root "$WINE_SOURCE_ROOT"
python3 -B tools/check_governance.py
python3 -B -m unittest discover -s tests/docs -p 'test_*.py' -v
python3 -B tools/check_source_notices.py --base 2c151f1d074fab5a55bc2d77e25b5fb81aedc257
git diff --check
```

The component notice check used its own FEX base `4ae26dd...` with Pear's existing
checker. Explicit provider pins are runtime `6f0202b...` and Wine `007291b...`.

- All 99 FEX selected files/modes, upstream ancestry, private-selector exclusion
  and shared-provider hashes pass. Rehashed 42 retained origin references and
  99 selected Git blobs. All 17 protected source/metadata paths remain exact.
- Independent three-document review passes: receipt
  `becf12c57ca66f35cb8c8b4aa40670e0b87e61c47bba9fb0eb4a87c4831f66d1`.
  The missing-holder limitation is disclosed; notice checks are not exhaustive
  legal clearance.
- Pear: 121 document tests pass (11.274 seconds test interval; 11.406 seconds
  subprocess wall interval), governance passes 40 documents / 386 local targets.
  Incremental notices pass with zero Pear executable-source candidates.
  Final changed-document links, bounded privacy and whitespace pass.
- Prepublication remote inventory passes at 2026-10-20T15:28:54Z, receipt
  `1c2d834c99af81f3858a10aeaa3bbc214a08afce4a30197897060a787c2a35c1`.
  The separate post-publication review at 2026-10-20T15:43:36Z
  passes: receipt `109a875b57c096d43ea427be57aa814fe32c99fb71e7b4823e4f8016607086be`.
  Four OPEN/non-draft private PRs have exact heads/base refs, 16 matching changed
  Git blobs, five commits across four matching histories and matching prepared bodies. Each
  repository has two branches, zero tags and its unchanged `codex/task56` default.
  No workflows, runs, check runs or status contexts are present; no remote CI
  pass is claimed. New exposure is limited to the private branches/PR entries.
- Main/source/tool root HEAD/status observations retain the earlier identities,
  including the pre-existing dirty historical runtime checkout. No old
  environment, input, output or private state is targeted by a write operation.
  A complete app/game/private-state content rehash was not performed.

No compiler, original generator, native fixture, guest/game, installation,
signing or cleanup runs in Stage4. No interactive-window latency is measured.
Remote CI absence does not count as a passing CI run. The coordinating Pear
PR's actual head, checks and URL are recorded in Issue #75 after creation from
this bundled final commit.

## Artifact Disposition

| Artifact/root | Actual state and consumer | Identity/recovery | Retain reason / release condition |
|---|---|---|---|
| Task75 Pear/component worktrees | Retained for PR review and successor work | Exact component heads in current final report | Keep through review/merge and dependency check |
| Stage4 notice/source/remote review records | Private indexed copy retained | 67-record index `51579f015d27783356b33a4490e297766c8bfd773eb2326c023738bcd10b90e6` | Preserve for later visibility review and source provenance |
| Earlier WGI inputs, both output attempts and indexed audits | Retained unchanged | Existing Stage3 input/build/index hashes | Required for next natural-call/control work; no release here |
| Original selected runtimes, producers and #47/private state | Preserved | Original locks and consumer paths | No cleanup or activation authorization |

Measured Stage4 scratch, new sparse FEX checkout and private audit snapshot:
3,222,212 logical / 3,874,816 stat-allocated bytes, excluding the shared
existing Git store. A separate 2 MiB final-text/closeout allowance keeps the
forecast below the approved 32 MiB ceiling. Observed free space was
15,652,495,360 bytes; concurrent activity prevents attribution of free-space
changes. No old artifact, branch or worktree was deleted. The WGI campaign's
original 128 MiB accounting is unchanged and separate from this allowance.

## Residual Risks

All four reviewed PR successors are READY WITH LIMITS, but defaults are not yet
integrated. FEX's former default lacks the new adjacent notice. Actual public
conversion requires the requester's decision and a fresh review of integrated
refs and exposure surfaces. The absence of original holder information remains
explicit. Inherited-history/submodule/hidden-surface limits and retained-input
build prerequisites remain. Natural WGI invocation and its causal relationship
to D36 remain unproven.

## Impact on Next Stage

Review and integrate the five PRs under separate merge authorization. The next
implementation investigation remains bounded observation of the existing WGI
call, with a newly bound PE/candidate and affected controls. Source publication,
behavior repair and game qualification are separate decisions.

## Approval Record

The requester authorized correction, verification and continuous progression
to PR publication. This verified Stage4 and final report are committed together.
No repeated stage approval is needed within that scope. Merge, Issue closure,
visibility conversion and artifact cleanup remain outside this extension.
