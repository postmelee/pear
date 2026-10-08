# Task #8 Stage 3 Investigation — Presentation Integration

Stage 3 is now **complete**; see [the completion report](task_m1_8_stage3.md).
This note preserves the investigation and earlier incomplete observations.
The requester approved Stage 3 and the v2 surface amendment on October 9, 2026.
The coordinating chat also delivered explicit authorization for the real delivered
unaligned CPU repair. No Stage 4, game qualification or GitHub publication is claimed.

## Current implementation

- Preserve the v1 48-byte ABI and its four methods. The new 56-byte v2 interface
  adds managed window acquisition; the real DXMT swapchain requires v2.
- Reuse Wine's client-surface allocation, active list, update, detach and final
  reference release. A small reservation mutex never spans Wine or Cocoa work.
  Final release detaches directly, avoiding the optional unused-cache reference.
- Expose the existing `use_window_client_surface` implementation only between
  source-matched Wine components. No private Wine layout crosses the Pear ABI.
- Handle allocation/registration rollback, foreign ownership, shared references
  and stale leases. Guard the upstream null allocation before dereference.
- Reuse FEX's scalar instruction preparation, checked RX snapshot, retained
  source objects, quiescence, owner W^X write/publication and managed re-entry in
  the actual Windows exception reset path. No owner wire ABI or security change.
- Record actual Metal submission, presented callbacks, GPU completion and physical
  view/layer/proxy lifetime. Capture only the owned synthetic test window.
- The original 39 native assertions remain. An explicit fixture-only v1 consumer
  entry preserves that regression; the production swapchain has no v1 fallback.
  Twenty-three v2 controls cover ABI refusal, context, allocation/registration
  rollback, shared leases, recreation, Wine's window-detach operation, stale
  query/release and foreign ownership. Detach controls call the exact upstream
  operation while a lease is live; they do not claim a separate OS window was closed.

## Actual evidence

All directories below are ignored private `.build/task8/` outputs. Source snapshots,
producer snapshots, input hashes, binaries, authorization and raw logs remain there.
Earlier observations retain their original input scope; edited producer/patch files
can make an earlier candidate historical rather than replayable with current tools.

| Candidate / run | Observation |
|---|---|
| `rendering1` / original `render-build1` PE | Retained Stage 2 failure: 2-byte x64 store crosses a 16-byte boundary; delivered exception was not repaired. |
| `presentation1` / original `present-build1` PE | Retained 8-byte store failure at RVA 0x1612, target offset 12; debugger reached the owned 180s bound. |
| `present-runtime2` / `presentation2` | Aligned fixture reaches actual swapchain creation but v1 refuses NO_CLIENT; exit 3. |
| `repair-runtime1` / `repair-original-render1` | Exact original 2-byte-store PE: one delivered recovery, exit 42 and seven independently checked readbacks. |
| `repair-runtime1` / `repair-original-present1` | Exact original 8-byte-store PE: one delivered recovery, then the separate NO_CLIENT refusal; exit 3. |
| `surface-runtime1` / `presentation3` | Original PE completes 18 presents, all GPU completions, three resize/destroy cycles and physical cleanup. Nine phase captures have correct dimensions/colors. Seven presented times are zero; strict all-positive-time check refuses qualification. |
| `surface-runtime2` / `presentation4` | Explicit Core Animation flush experiment still has six zero presented times. Removed the ineffective flush from the next candidate. |
| `surface-runtime2` / `pairing8` | Original 39 native assertions and first 20 v2 controls pass; physical lifetime balanced. |
| `surface-runtime3` / `presentation5` | Actual drawable texture dimensions match all requested sizes. Seven zero presented times remain; no stale-size drawable was observed. |
| `surface-runtime3` / `pairing9` | Original 39 assertions plus all 23 v2 controls pass, including live-lease detach and final release. |

`present-native1` and `present-native2` retain their build-recipe preparation
failures (blank Makefile variable parsing and missing inherited SDKROOT).
`surface-native1` retains the discovery that the needed existing Wine registration
function was private. Subsequent builds expose/reuse it without replacing its logic.
Current compilation reuses retained recipes and recompiles only affected objects.

All completed runtime observations above preserve original failures, owned cleanup,
unrelated-sentinel survival and before/after development authorization. They are
synthetic fixture results, not owned-game or ordinary-user distribution qualification.

## Remaining verification

Apple documents a zero presented time as unpresented/dropped; do not relabel it as
positive timing evidence ([MTLDrawable.presentedTime](https://developer.apple.com/documentation/metal/mtldrawable/presentedtime)).
A flush was only a hypothesis and had no demonstrated benefit; Apple also recommends
normal run-loop transaction processing ([CATransaction.flush](https://developer.apple.com/documentation/quartzcore/catransaction/flush%28%29)).

A separate bounded fixture now alternates each frame's color and holds it for 1.5s
so each of the 18 actual window images can be checked before its differently colored
successor. This distinguishes real frame loss from ambiguous timestamp observation.
It keeps the three cycles, dimensions, frame count, callbacks, GPU and lifetime
checks; the exact original failure PEs remain separate recovery requirements.
Missing/wrong images still fail. Zero timestamps remain explicitly reported even
if independent per-frame images prove display; no timing/performance claim follows.

`surface-runtime4` / `presentation-frames1` passed all 18 independent window-image
checks, all 18 GPU completions and nine physical creations/deallocations, with zero
final leases/attachments. Two callback timestamps were positive and sixteen zero.
Every adjacent displayed frame had a different expected color, so a previous or
successor frame cannot explain a passing image. This establishes visible output
for this bounded run, but does not establish trustworthy presentation timing on
this setup. The unmodified upstream presentation API remains in use.

The repaired candidate must also pass the full 19-case CPU comparison and multiworker
ordering checks using unchanged Windows references, final native/v2 checks, rendering
and the two exact original failure PEs. The aggregate reader now requires these
inputs and cannot substitute only two CPU boundary checks for the repaired corpus.
Twenty-five translated portable tests and four surface-reader refusal tests pass.
No completion report or stage commit has been made.

Final `surface-runtime4` qualification passed: 39 native assertions, 23 v2 controls,
18 visible frames, five rendering cases/seven readbacks, both exact original CPU
failures recovered, 18 CPU cases passed plus one AVX-not-exposed result, and 32,768
ordering pairs across eight workers. Twenty completed CPU prefixes were retired.
The final aggregate and 32 focused portable tests passed; no game claim follows.
