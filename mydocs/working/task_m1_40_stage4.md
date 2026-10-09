# Task #40 Stage 4 — Reproduction and Handoff

GitHub Issue: [#40](https://github.com/postmelee/pear/issues/40)
Implementation plan: [task_m1_40_impl.md](../plans/task_m1_40_impl.md)
Stage: 4 — complete, October 10, 2026 (Asia/Seoul).

## Stage Purpose

Document the bounded loader correction, replay final evidence and prepare the
final report and PR for review. #40's five acceptance criteria pass; the later
pre-menu startup stall remains #11's responsibility, not a gameplay success.

Context used: approved task/implementation plans and October 9 continuation,
root/docs rules, README, official index, architecture, delivery plan, existing
Wine/FEX guides and Stage 1-3 reports. GitHub #40 is still OPEN. Read-only worktree
inspection found separate #10 (`37395ee`) and #11 (`09ea427`) work; neither was
modified. Stage-report and repository todo procedures and central report templates
apply. No new Metal work or Apple expert selection is required for documentation
and existing evidence replay.

## Artifacts

| File | Change Summary |
|---|---|
| `docs/development/wine-host.md` | Dated capacity, reconstruction, replay and downstream-boundary guidance |
| `mydocs/plans/task_m1_40_impl.md` | Stage 4 approval and exact implemented verification commands |
| `mydocs/report/task_m1_40_report.md` | Five acceptance criteria, four-stage outcome, limits and handoff |
| `mydocs/orders/20261009.md`, `20261010.md` | Local implementation complete; publication and merge pending |

## Body Change Scope / Lossless Preservation

The approved official location is the existing Wine guide. Its historical body
is preserved with a dated addition and navigation link. FEX source/ABI/reconstruction
did not change, so its guide requires no duplicate result section. No new roadmap,
product contract, runtime code, test producer, native binary or signing change.
Original failures, owned game files, consumer inputs and exact-byte producers stay
unchanged; raw logs and local PR draft remain outside Git.

## Verification Results

The retained native evidence is from M4 Pro/macOS 26.5.2 (25F84), Xcode 26.6
(17F113), recorded LLVM-MinGW and the actual development authorization. Stage 4
runs Python readers and Clang UBSan parser checks; no new restricted game or
fixture execution and no performance measurement. Source/test identities and
candidate scope still match. The final replay recomputes raw game, CPU/ordering,
render/readback/frame and scalar-recovery assertions, rather than trusting saved
pass flags. Current future execution authorization must still be checked at launch.

```sh
python3 -B -m tools.wine.image_initialization_qualification --index .build/task40/stage3-index.json --verify-only
PEAR_IMAGE_ADMISSION_BUILD=.build/task40/diagnostic-build2 PEAR_IMAGE_CORRECTION_BUILD=.build/task40/correction-build1 python3 -B -m unittest discover -s tests/wine -p 'test_image_admission*.py' -v
python3 -B -m unittest discover -s tests/wine -p test_image_initialization.py -v
python3 -B tools/check_governance.py
git diff --check
```

- Final raw-evidence replay: passed; DLL initialized, named next phase confirmed,
  gameplay false. The qualification receipt remains SHA-256
  `8fe4b084ee3cd99935062377a22ce5ac897cdd8160ac71e3edc7d83e2e650ff2`.
- Admission/parser/owner controls: **27 pass, zero skips**. Initialization and
  candidate-binding controls: **4 pass, zero skips**.
- Documentation governance and whitespace checks pass. Local logs are retained
  in `.build/task40/stage4-verification/`.
- Prior native loader runs, 18 CPU passes plus unsupported AVX, ordering and all
  required graphics execution remain reused Stage 2/3 evidence. No new native
  matrix, full build, Steam login, gameplay or CI execution is claimed here.

The plan's placeholder qualification command was replaced by the actual frozen
Stage 3 reader. Explicit build variables ensure parser tests do not skip their
required composed-source inputs; no acceptance check was removed.

## Residual Risks

Later initialization still exceeds the observation bound; its cause is unknown.
No responsive menu, Steamworks, gameplay, M1, presentation timing or distribution
qualification. Replay needs the retained private source/build/fixture dependencies;
clean-machine assembly is separate. See the final report for exact handoff scope.

## Impact on Next Stage

There is no further implementation stage in #40. Review the final report and PR
draft, then publish the task branch as `codex/publish-task40` when authorized.
Preserve the worktree and immutable candidate for #11 even after eventual merge.
Do not delete consumer evidence as routine branch cleanup.

## Approval Request

Approve the final report and PR publication. Merge and Issue closure remain a
separate decision after review and required CI.
