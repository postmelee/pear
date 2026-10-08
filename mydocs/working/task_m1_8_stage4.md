# Task #8 Stage 4 — Integrated Graphics Qualification and Game Handoff

GitHub Issue: [#8](https://github.com/postmelee/pear/issues/8)
Implementation plan: [task_m1_8_impl.md](../plans/task_m1_8_impl.md)
Stage: 4 — complete, October 9, 2026.

## Stage Purpose

Bind the complete finite D3D11 acceptance suite to one final candidate, replay
existing valid evidence, document reproduction and locate the next game-start
failure without extending fixture results into a game support claim.

Context used: approved Stage 4 continuation; root/runtime/DXMT/tests/docs rules;
Issue #8 and open dependent Issues; README, architecture, delivery plan, task and
implementation plans and Stage 3 report. Reused the existing pinned Apple guidance
and runtime implementation; no new Metal design or Apple tool was introduced.
Stage-report, final-report and daily-board procedures apply to this local handoff.
GitHub publication and merge remain unapproved. #9 and #10 have independent active
worktrees; this stage does not change their sources or contracts.

## Artifacts

| File | Change Summary |
|---|---|
| `tools/dxmt/translated_qualification.py` | Exact six-reference final index; re-admit candidate and replay existing device/presentation/rendering/pairing/CPU/ordering readers |
| `tools/dxmt/translated_check.py` | Route `--qualification --require-stage 4` to the integrated reader |
| `tests/dxmt/test_translated_qualification.py` | Changed bytes, missing scope and prior-stage promotion refusal controls |
| `tools/dxmt/translated_game_diagnostic.py` | Separate proprietary-input startup adapter retaining existing bounded ownership/security primitives |
| [DXMT guide](../../docs/development/dxmt-build.md) | Approved existing destination: final scope, constructor chain, replay/execution recipes and limits |
| [Allowlisted observations](task_m1_8_stage4_observations.json) | Exact private evidence hashes, finite results and game failure without private paths or raw diagnostics |
| [Final report](../report/task_m1_8_report.md) | Whole-issue acceptance and next integration work |

## Body Change Scope / Lossless Preservation

The signed runtime and all frozen producers, proprietary originals and historical
failures remain unchanged. No native rebuild or repeat GPU/CPU fixture execution
was needed for the reader/documentation addition. The optional game adapter
adapts the existing #8 runner and reuses APISession, restricted bootstrap, current
signature/profile admission, output bounds, owned cleanup and sentinel. It does
not add Steam bypasses, a new manager ABI or a qualified-game record.

The existing DXMT guide is the only official document changed, matching the
approved location judgment. Earlier native-only evidence remains intact. No CPU
guide change is needed: the final report and existing graphics handoff own this
combined-candidate evidence. Task plans/reports remain under `mydocs/`.

## Verification Results

Execution context: M4 Pro, ARM64 macOS 26.5.2 (25F84), Xcode 26.6 (17F113), existing
development authorization. Validation remains enabled for correctness. This stage
replayed prior fixture evidence and separately executed one game-start diagnostic;
neither is performance qualification.

Evidence reuse: final `surface-runtime4` receipt
`f90b2a601f556595a07b38bfa695def75b7f1def9bb1018e7dacb73bf7444f5f`.
The integrated reader checks exact source/build/patch/tool/payload references,
reopens raw result streams and images, and recomputes original fault recovery and
CPU/native reference comparisons. It does not trust a saved assessment flag or
launch a missing fixture. Device, all seven readbacks, 18 individual frames, native
39 + v2 23 controls, physical teardown and full declared CPU/ordering checks pass.
AVX remains unsupported/not exposed; no required graphics feature is waived.

```sh
python3 -B -m tools.dxmt.translated_check --qualification .build/task8/qualification4.json --require-stage 4
python3 -B -m unittest discover -s tests/dxmt -p 'test_translated_*.py'
python3 -B tools/check_governance.py
git diff --check
```

- Integrated replay: `passed: true`, `stage: 4`; no native fixture re-execution.
- Portable changed-area checks: 29 passed, including four new index refusal checks.
- Governance: 25 documents / 241 local targets passed; `git diff --check` passed.
- Independent machine/release reconstruction, complete process observation,
  official Steam login, gameplay/save and performance remain unperformed here.

### Owned Megabonk startup diagnostic

The adapter verified and APFS-cloned the 69 original depot files from the owner's
September 27 snapshot (App 3405340, depot 3405342, manifest 446680890915713051).
It cloned a same-candidate synthetic device prefix and used an isolated home,
without authenticated Steam state, saves, API stubs or app-id overrides. Startup
used `-force-d3d11`, a 960x540 window and a private Player log, with a 120-second
launch deadline. This is an older owned snapshot, not a claim about today's build.

Unity printed its memory initialization settings and 51 delivered scalar repair
records succeeded. `GameAssembly.dll` image mapping then returned
`STATUS_NOT_SUPPORTED` (`0xc00000bb`); the failure path opened message-box
resources and remained alive until the deadline. The adapter classified a timeout,
not a successful exit. Cleanup took the total measured interval to 125,113 ms;
all owned children were reaped, the unrelated sentinel survived, signature/profile
checks passed before/after, and originals/runtime were unchanged. Player.log was
empty. Menu entry, Steam account initialization and gameplay were not established.

Read-only source/PE inspection found `SizeOfImage = 57,647,104` bytes while
`PEAR_ARENA_MAX_IMAGE_BYTES = 38,993,920` bytes. The retained Wine parser rejects
that size with the observed status. This is a concrete admission incompatibility;
the first runtime branch was not instrumented, so it is not claimed as the only
failure. Next work should trace image admission and review the arena/metadata,
relocation and publication limits together, then rerun the same unchanged game
DLL. Do not patch the proprietary image or merely suppress the refusal.

The game failure is separate from the finite #8 graphics suite. It does not erase
the passing fixture results or qualify Steam/game execution. The exact duplicate 69-file game clone was removed after rechecking every retained
original and cloned byte identity. Failure logs and the isolated prefix remain;
522,734,781 logical duplicate bytes were retired, with physical APFS savings
unmeasured. No new GitHub issue, comment, push or PR was created in this stage.

## Residual Risks

- Retained build trees and original failure artifacts are needed for this replay;
  independent clean-machine assembly remains #13.
- Development signing only; complete late-load coverage remains #10.
- Unqualified AVX/WoW64, arbitrary concurrency/workload scale and drawable timing.
- Actual game admission remains blocked as described; #11/#12 must preserve normal
  Steam ownership and validate gameplay, input/audio, save/relaunch and all helpers.
- Raw evidence remains private and input-bound. A new runtime invalidates affected
  evidence; a report alone cannot substitute for revalidation.

## Impact on Next Stage

All four #8 stages are ready for final review. Preserve the final candidate,
source/build chain and original failures for #9/#10 and game-integration work.
Address the actual game DLL admission before interpreting FPS or thermal behavior.

## Approval Request

Review the local final report and PR draft before GitHub publication. Publication,
merge and Issue closure have not been performed.
