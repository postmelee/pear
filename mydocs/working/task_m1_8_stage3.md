# Task #8 Stage 3 — Presentation, Surface Ownership and Delivered Scalar Repair

GitHub Issue: [#8](https://github.com/postmelee/pear/issues/8)
Implementation plan: [task_m1_8_impl.md](../plans/task_m1_8_impl.md)
Stage: 3 — complete, October 9, 2026. Issue #8 remains open.

## Stage Purpose

Qualify three translated device/window cycles, resize, 18 actual visible frames,
GPU completion and physical resource teardown. Resolve the missing Wine client
surface and the two preserved delivered scalar-alignment faults needed to reach
this path. These are bounded synthetic results; Megabonk has not been launched
or qualified by this stage.

Context used: approved #8 plans and surface/CPU amendments; root/runtime/FEX/DXMT/
test rules; architecture and runtime evidence boundaries; pinned #5/#6/#7 sources.
The Pear Apple-tooling router selected `presenting-metal-drawables` at
`4f42344c90be22112f46becc3fb9687f423f2f88` (plugin `1.0.0-beta.1`), with the installed
SDK's drawable callbacks and existing validation settings. Existing
`using-metal-validation` guidance remains applicable. Stage-report and daily-board
procedures apply. No new toolchain, plugin or macOS permission was installed.

## Artifacts

| File group | Change Summary |
|---|---|
| `runtime/dxmt/patches/.gitattributes` | Extend the existing unified-diff context whitespace rule to root-level patch files; preserve exact upstream context bytes |
| `runtime/dxmt/patches/0003-*` and `0004-*` | Read-only native presentation, physical lifetime and registry observations |
| `runtime/dxmt/patches/0005-*` and `0006-*` | Versioned managed Wine surface and actual DXMT v2 consumer; source-matched internal Wine registration export |
| `runtime/dxmt/patches/0007-*` and `0008-*` | Finite v2 controls, explicit fixture-only v1 consumer regression and drawable-size observation |
| `runtime/fex/patches/graphics/0004-delivered-unaligned-repair.*` | Actual Windows reset-path scalar preparation, checked ownership/publication and native resumption |
| `tests/dxmt/translated_presentation*.cpp` | Original 18-frame fixture and per-frame alternating-color observation variant |
| `tools/dxmt/translated_present_*`, `translated_frames_build.py` | Fixture/native construction, signed overlay, capture and completion readers |
| `tools/dxmt/translated_repair_*`, `translated_surface_*` | Repaired CPU/native builds, exact original PE retention, coherent signed candidate and v2 reader |
| `tools/dxmt/translated_run.py`, `translated_check.py`, `translated_render_check.py`, `translated_regression.py` | Existing owned execution protocol, original-PE selection and full repaired CPU/ordering admission |
| `tests/dxmt/test_translated_results.py`, `test_surface_controls.py`, `test_present_frames.py` | Missing/incorrect completion, ownership, rollback and visible-frame refusal checks |
| [Allowlisted observations](task_m1_8_stage3_observations.json) | Exact evidence hashes and bounded outcomes without private paths, signing material or raw images |
| [Investigation notes](task_m1_8_stage3_notes.md) | Preserved failure sequence and rejected timing hypothesis |

## Body Change Scope / Lossless Preservation

All changes remain in approved runtime-patch, test/tool and task-document roots.
No official product guide, manager contract or other worktree was changed.
Retain upstream C/C++/Objective-C, source notices and contribution boundaries.

The v1 getter/table/statuses remain. V2 adds managed surface acquisition, keeps
Wine structures internal and refuses foreign owners. The adapter reuses Wine's
active surface list and final-reference detach/destruction; it does not leave an
unused-cache reference. Reservation locks never span Wine/Cocoa work. Native layer
operations stay on the Cocoa main thread. Allocation/registration failure, shared
leases and invalidated leases are checked. The actual swapchain requires v2;
only the explicit regression fixture can invoke the preserved v1 consumer path.

The CPU adapter reuses upstream scalar instruction preparation and #5/#6 retained
source objects, RX snapshots, quiescence, owner W^X publication and EC re-entry.
After leaving active execution, it obtains the mutation turn and checks the exact
captured allocation/dispatcher identities and epochs before writing. That turn
spans publication and re-entry. Native register state is retained; no guest
instruction restart, raw upstream JIT write or owner wire ABI change is introduced.
Unsupported preparation families retain their existing fault path.

Both original failed PE files and their exact source/input records are preserved.
They now each record an actual delivered repair and exit 42 in the final candidate.
Aligned/static GPU fixtures are not used as proof that those original faults were
fixed. Earlier failures remain failures in their original records.

## Verification Results

Execution context: M4 Pro, ARM64 macOS 26.5.2 (25F84), Xcode 26.6 (17F113), existing
authorized development profile/signing and normal macOS protections. All 41 native
images have ARM64 closure/signature evidence. The observed FEX/DXMT/native Metal
execution route is Rosetta-free within its recorded process/image scope; complete
late-load coverage remains #10 work. API/shader validation is enabled. The visible
fixture intentionally holds frames for capture; this is not a performance test.

Evidence reuse: unchanged Windows x64 references and the pinned Wine/FEX/DXMT
sources, retained archives and build recipes are reused. Only affected native
objects and the repaired ARM64EC FEX component were rebuilt. Since CPU code changed,
its full declared corpus and ordering checks were rerun. The final signed candidate
also reran native pairing/v2, both original failure PEs, rendering and presentation.
Historical candidates are not substituted for final-candidate checks.

| Required result | Outcome |
|---|---|
| 18 visible frames / three cycles | All 18 owned-window images independently match alternating colors and expected sizes; 64x64 -> 96x80 -> 64x64 per cycle |
| Actual native completion | 18 submitted presents, 18 drawable callbacks and 18 GPU completions; no required validation error |
| Resize/window callbacks | Three complete cycles with required size/destroy callbacks and original owner-thread checks |
| Physical lifetime | Nine observed view/layer/proxy creations and nine deallocations; zero final leases/attachments |
| Original 2-byte fault | Unchanged original PE, one delivered repair, exit 42, all seven readbacks correct |
| Original 8-byte fault | Unchanged original PE, one delivered repair, exit 42, all original frame/cycle terminal checks complete |
| CPU comparison | 18 passed; AVX lane case remains unsupported/not exposed, not counted as a pass |
| Memory ordering/lifecycle | 32,768 measured pairs, four rounds, eight workers and eight checked worker retirements; declared per-thread policy observed |
| Native regression | Original 39 assertions pass; physical lifetime balanced |
| V2 controls | 23 pass, including source allocation/registration rollback, sharing, recreation and live-lease Wine detach/stale release |
| Rendering | Five cases and seven readbacks pass; actual fixture pipelines are validated |
| Process/security | Owned cleanup, unrelated sentinel and before/after authorization pass |
| Portable checks | 25 translated tests, four v2 reader tests and three individual-frame reader tests pass |

Metal's callback time needs a separate limit: only two of the per-frame run's
18 `presentedTime` values were positive; sixteen were zero. Apple documents zero
as unpresented/dropped ([reference](https://developer.apple.com/documentation/metal/mtldrawable/presentedtime)).
Here, each frame's distinct actual window pixels were independently captured
before its differently colored successor. The images establish visible output;
they do not turn zero times into valid timing data. The callback timing is therefore
unqualified on this setup. A prior force-flush experiment did not resolve the
observation and was removed. The upstream presentation API remains unchanged.

Final candidate: private `surface-runtime4`, receipt SHA-256
`f90b2a601f556595a07b38bfa695def75b7f1def9bb1018e7dacb73bf7444f5f`.
The aggregate reader returned `passed: true`, `stage: 3`. Exact hashes are in the
allowlisted observations; private source/build/run records remain under the
ignored task output root.

Verification commands:

```sh
python3 -B -m tools.dxmt.translated_check --run .build/task8/device15 --runtime .build/task8/surface-runtime4
python3 -B -m tools.dxmt.translated_check --run .build/task8/presentation-frames1 --runtime .build/task8/surface-runtime4 --pairing .build/task8/pairing10 --rendering .build/task8/surface-original-render1 --cpu-boundaries .build/task8/stage3-dependencies1.json --require-stage 3
python3 -B -m unittest discover -s tests/dxmt -p 'test_translated_*.py'
python3 -B -m unittest discover -s tests/dxmt -p 'test_surface_controls.py'
python3 -B -m unittest discover -s tests/dxmt -p 'test_present_frames.py'
python3 -B tools/check_governance.py
git diff --check
```

Twenty completed owned CPU/ordering prefixes were retired as their checks finished.
Approximately 15 GiB remained free afterward. Original failures, required inputs,
current candidate and review evidence remain. No proprietary game data, authenticated
prefix, save or other-task artifact was removed. There was no GitHub publication.

## Residual Risks

- Megabonk, official Steam/i386 helpers, full gameplay, input/audio/save and
  ordinary-user distribution remain unqualified.
- Scalar recovery is demonstrated on the two exact original faults. Other
  instruction families and universal concurrent repair are not established by this
  finite corpus. AVX remains unexposed; ordering is not a universal proof.
- Presentation timing is not qualified; no frame-rate, latency or power claim.
- One Mac/development configuration is covered. Existing optional winegstreamer
  media dependency and complete late-load observation gaps remain.
- Detach refusal uses Wine's actual detach operation with a live v2 lease; it does
  not claim arbitrary cross-thread window races or all rendering backends are covered.

## Impact on Next Stage

Stage 4 must re-admit this coherent candidate, bind the final source/reference/
artifact coverage and document reproducible scope and gaps. Reuse still-valid
checks. The approved optional bounded owned Megabonk diagnostic can locate the next
integration blocker using normal Steam/account requirements; no stub, bypass,
binary patch or save modification. Do not claim #11/#12 or game qualification from
these synthetic results.

## Approval Request

Review the Stage 3 results and approve continuation to Stage 4. Issue #8 remains
open; PR publication and merge are not performed by this stage.
