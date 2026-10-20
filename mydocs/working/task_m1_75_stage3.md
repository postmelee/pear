# Task #75 Stage 3 — WGI source and development PE correspondence

GitHub Issue: [#75](https://github.com/postmelee/pear/issues/75)
Implementation plan: [task_m1_75_impl.md](../plans/task_m1_75_impl.md)
Stage: 3

## Stage Purpose

Establish the selected WGI module's original producer, exact source/input closure
and reproducible module relationship before natural-call debugging. Context:
approved continuous three-stage plan, root/docs/test rules, artifact retention,
source notice and stage-report procedures, original Task5 build records and
existing common-runtime Wine recipe. Reuse the executor, strict PE/COFF comparison
and dependency/trace validation; do not replace upstream WGI or shared tooling.

## Artifacts

| File | Change summary |
|---|---|
| `mydocs/tech/task_m1_75_wgi_binding.md` | Producer/input join, reconstruction and next natural-call observation |
| `docs/development/rosetta-free.md` | Current WGI result, exact build-role clarification and future candidate scope |
| Runtime `pear_runtime/recipes/wgi.py` | Bounded sealed-input module adapter and failure-safe accounting |
| Runtime `recipes/wine/wgi-v1.json`, `tests/build/test_wgi.py`, existing recipe README | Explicit 9,152 inputs / 65 original actions, regression controls and entrypoint |
| Publication note / final report / task board | Final delta review, retained evidence and completion handoff |

## Body Change Scope / Lossless Preservation

The original Wine sources, shared runtime executor/Wine driver, selected candidate,
runtime12, original producer/toolchain inputs and #47 environment are unchanged.
Only the isolated Task75 runtime branch receives new build tooling. Raw generated
objects/PEs and failed attempt records survive. The final source/recipe identities
match those actually executed; later report/README changes do not rebuild or
requalify the selected runtime. Documentation stays at approved existing guide
and `mydocs/` locations. No public visibility conversion or upstream submission.

## Verification Results

macOS build-only execution with exact ARM64 helper/LLVM inputs and Python 3.13.5;
portable tests and Pear document checks are distinct. Existing source/static
records establish provenance, not a game result. Historical native/game controls
were not rerun or relabeled for this module.

```sh
python3 -B -m pear_runtime.recipes.wgi --recipe recipes/wine/wgi-v1.json \
  --bindings "$PRIVATE_WGI_BINDINGS" --output "$FRESH_WGI_OUTPUT"
python3 -B -m unittest discover -s tests/build -p 'test_wgi.py' -v
python3 -B tools/check_governance.py
python3 -B -m unittest discover -s tests/docs -p 'test_*.py' -v
python3 -B tools/check_source_notices.py --base 2c151f1d074fab5a55bc2d77e25b5fb81aedc257
git diff --check
```

The component report records its guarded portable test runner and incremental
notice command against runtime Stage1 `17516d7`. It covers 26 WGI and 17 existing
Wine tests, with no forbidden child/native/network events. Qualified collection
and documented discovery work. Rejection controls cover mismatched inputs,
unknown dependencies/tools, source drift, recipe changes, non-timestamp PE changes,
final receipt overflow and interrupted accounting.

- Original selected DLL copies are equal, and 173 source/header inputs match
  historical records and three exact Wine trees. Task56's bounded Wine recipe did
  not build WGI; the retained module's original producer is Task5.
- First control link succeeded, but its strict trace check failed. The failed
  receipt remains failed. A reviewed WGI-only adaptation of one known executable
  field in derived logs passed pure actual-trace replay before the fresh retry.
- Retry: exit 0, successful/finalized build, exact operation released; all 66
  commands exit 0, 36 generated files exact, 28 fresh objects equal outside COFF
  timestamps, 28 depfiles / 133 actual unique paths admitted. Both links admit
  all 39 required operands, 41 actual reads and three tools.
- Both raw PEs differ from the original only in six bytes inside two independently
  parsed four-byte timestamp fields. Every other byte matches. Raw hashes,
  timestamps and derived comparison identities remain separate.
- Independent review rehashed 1,308 distinct identities and confirmed actual
  commands, environment/directory joins, input/output preservation, comparisons,
  completion and storage. Record SHA-256:
  `e6bf558029cea130430867187a9685ab169d35dd9a70375fa935f17ff53766b1`.
- Pear: 121 document tests pass (11.579 seconds); governance passes 40 documents /
  386 local targets; notice/diff/privacy/link checks pass. Final runtime five-file delta privacy/notice review passes at `db95ed3278d9d20233fbd395665f3d39c3a4b13d` (receipt `990b954d3c333fff63624312b013921eefc0c9f53933ec3b8976cb10744b9251`); JSON identities/actions are explicitly reviewed data.
- Protected source HEAD/status comparisons match Stage1, including the previously
  dirty historical runtime checkout. All 281 original pack-source files and
  admitted builder sources remain unchanged; complete private app/game state
  hashing was not performed and is not claimed.
- No native fixture, guest/PE/game execution, window, installation or signing.
  No user-operable-window latency or gameplay qualification.

The successful external build interval is 15.576 seconds with wall/monotonic
phase boundaries, including 15.462 seconds of child-process time. Generation,
compilation, linking, preparation, admission, comparison and coordination are
separately recorded; their sums are not an interactive latency measurement.

## Artifact Disposition

| Artifact/root | Actual state/outcome | Consumer | Identity/recovery | Retain/release condition |
|---|---|---|---|---|
| Task75 runtime source and tests | Committed separately | Module reproduction / next debugging task | `db95ed3278d9d20233fbd395665f3d39c3a4b13d` | Retain through review and successor validation |
| Original and fresh WGI inputs/outputs | Immutable raw inputs and both attempts retained | Source correspondence / next controls | Build receipt `8a8f24211bb990e81d881409de870b5ca59d17c0bdc94e61fc1a6b6874c82ff2` | No release authorized in #75 |
| Private audit/verification records | Durable indexed copy | Publication and next implementation | private Stage3 index `7c906b6314884c19924aad333067526f9a4e38f3b8cc599c2aab3558ca6955e8` (95 copied records) | Keep until accepted successor evidence |
| Original runtime/tool/producer worktrees | Preserved | Existing exact-path consumers | Task56 locks and Task75 inventory | Do not clean, move or replace |
| Historical frame request | Already absent before #75; restore-required | Future game admission | Exact 494-byte retained recovery copy | Current task does not restore or consume it |
| #47 installed app / game / private state | No operation performed | Existing owner | Existing environment | Preserve |

Final retained build campaign including both attempts, pack and archived verification records: 112,761,053 logical / 115,204,096 stat-allocated bytes, below the unchanged 134,217,728-byte aggregate ceiling. Separate filesystem free-space observations cannot be attributed
solely to this task amid concurrent work. No existing file, branch, worktree or
artifact was deleted.

## Residual Risks

Lower-layer libraries and exact helper/toolchain inputs remain required; a clean
public clone does not provide them. This is timestamp-only whole-module equality,
not identical raw output or full Wine bootstrap. Natural WGI failure and D36
causation remain unproven. FEX's generated-header notice prerequisite remains.

## Impact on Next Stage

The three planned stages are complete. Next implementation belongs in Wine's
existing provider/public reading paths with bounded, behavior-preserving
observation, component tests, a new module/candidate and affected controls.
Game execution, any behavior repair and visibility conversion require their own
reviewed scope. The final report records exact commit roles and recovery limits.

## Approval Record

All three stages were approved continuously. This verified Stage3 and final
report are committed together in Pear, following the separate component commit.
PR publication/merge and repository visibility are separate actions.
