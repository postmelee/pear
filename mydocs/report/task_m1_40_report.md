# Task #40 Final Report — GameAssembly Image Loading

GitHub Issue: [#40](https://github.com/postmelee/pear/issues/40)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta

## Work Summary

- Target Issue: #40; all five acceptance criteria satisfied locally.
- Stage count: four; publication, PR review, merge and Issue closure pending.
- The original owned GameAssembly exceeded Wine/Pear's per-image admission limit.
  Exact runtime tracing attributed the refusal before a bounded 64 MiB correction.
- The unchanged DLL now completes process attach, then opens IL2CPP metadata and
  starts its GC finalizer thread. The game still does not reach a verified menu.
  #11 owns that later startup integration; #12 owns gameplay and persistence.

The correction retains Wine C, existing FEX C++/assembly and the current owner.
No replacement engine, allocator ABI, aggregate mapping expansion, game edit,
Steam stub or new macOS permission was needed. Only two native ntdll objects were
rebuilt; retained upstream implementations and licenses remain applicable.

## Changed Files and Impact Area

| Path | Change Summary | Impact Area |
|---|---|---|
| `runtime/wine/patches/gameassembly/` | Opt-in diagnostics and exact-preimage 64 MiB correction with provenance | PE admission |
| `tools/wine/image_admission*.py` | Input closure, bounded accounting, isolated native build/signing, fixture execution and refusal assessment | Developer construction and loader evidence |
| `tools/wine/image_initialization*.py` | Original DLL attach/next-phase checks and reuse of CPU/graphics oracles | Same-candidate regression and handoff |
| `tests/wine/test_image*.py`, `tests/wine/fixtures/image_admission_pe.c` | Real composed-parser controls, redistributable large DLL and evidence rejection | Loader ownership, boundaries and evidence |
| `docs/development/wine-host.md` | Budget, exact retained native origin, construction/replay and limits | Contributor guidance |
| `mydocs/plans/`, `mydocs/working/`, `mydocs/orders/` | Approved scope, four reports and allowlisted observations | Task history |

## Document Location Verification

| File | Planned Location | Actual Location | Result | Evidence |
|---|---|---|---|---|
| Wine guidance | Existing official Wine guide | `docs/development/wine-host.md` | OK | Approved task-plan location; dated addition preserves historical body |
| Optional CPU guidance | Existing FEX guide if affected | Unchanged | OK | No FEX source/ABI/reconstruction change; avoids duplicate result section |
| Stage/final reports | `mydocs/working/`, `mydocs/report/` | Same | OK | Four stage reports and this report |

Requirements, scoped rules, upstream reuse and selected skill decisions are in
the [task plan](../plans/task_m1_40.md), [implementation plan](../plans/task_m1_40_impl.md)
and linked stage reports. Metal validation in Stage 3 reused the pinned Apple
expert and existing pre-device environment; it was not a new graphics design.
No architecture, roadmap, profile or manager contract was changed.

## Quantitative Before/After Comparison

| Metric | Before | After |
|---|---|---|
| Per-image limit | 38,993,920 bytes | 67,108,864 bytes (64 MiB) |
| Required GameAssembly image | 57,647,104 bytes, rejected at `parser.return08` | Admitted; 57,671,680-byte aligned slot and 429,566 relocations |
| GameAssembly process attach | Not reached in the attributed failure | Matching call, successful return 1 and attach end |
| Named subsequent phase | Not established | Exact metadata file read-open followed by GC finalizer startup |
| PE interior / total MAP_JIT | 1,050,345,472 / 1,588,985,856 bytes | Unchanged |
| Stage 4 local checks | Historical native results available | Raw-evidence replay and 31 controls pass, zero skips |
| Menu, Steamworks, gameplay | Unqualified | Still unqualified |

The reviewed maximum temporary payload is 100,679,768 bytes, excluding allocator
overhead and other process memory. Reservation size is not resident usage. No
power, heat, frame-time or performance improvement is inferred.

## Verification Results

| Acceptance Criterion | Result |
|---|---|
| Attribute first refusal to exact image/runtime | OK — Stage 1 binds file identity and caller/parser events to the size gate; original failure retained |
| Correct required layout with bounded ownership/publication | OK — 64 MiB correction, 27 parser/evidence controls, native and x64 large-DLL lifecycle fixtures; aggregate geometry unchanged |
| Initialize unchanged DLL and reach named next phase | OK — successful GameAssembly process attach, IL2CPP metadata read-open and GC finalizer startup |
| Required regressions, security and cleanup | OK — same-candidate CPU/ordering/graphics, before/after authorization, immutable bytes, owned-child reaping and sentinel survival |
| Record next blocker and owner without gameplay claim | OK — unresolved post-attach startup belongs to #11; gameplay/persistence remains #12 |

### Stage Verification Results

- [Stage 1](../working/task_m1_40_stage1.md), commit `8487781`: first-refusal
  attribution and nine controls. Wrong-origin control relink initially failed and
  was retained; the source ledger identified the actual #5 native origin.
- [Stage 2](../working/task_m1_40_stage2.md), commit `7ef56cd`: 27 controls;
  ARM64 and x64/FEX each pass eight loader conditions including actual attach,
  relocation, unload/reuse and rejected-attach cleanup. Only ntdll code changes.
- [Stage 3](../working/task_m1_40_stage3.md), commit `da9ff6b`: 18/19 declared CPU
  cases pass; AVX remains unsupported/not exposed. Ordering passes 32,768 measured
  pairs and eight worker lifetimes. Graphics passes device, 39 native and 23 v2
  surface controls, five rendering cases/seven readbacks, 18 visible frames,
  resize/teardown and both original scalar-fault recoveries. Four evidence controls
  pass. Initial assessor errors and their narrow corrections remain documented.
- [Stage 4](../working/task_m1_40_stage4.md), this report's enclosing commit:
  final raw-evidence replay, 27 admission/parser controls, four initialization
  controls, documentation governance and whitespace pass. Native runs were reused,
  not repeated for documentation-only changes.

Native evidence: M4 Pro, ARM64 macOS 26.5.2 (25F84), Xcode 26.6 (17F113), pinned
LLVM-MinGW and verified development provisioning. Original snapshot: App 3405340,
depot 3405342, manifest `446680890915713051`; 69 owned files unchanged. This is the
September 27 snapshot, not a current-game-version claim. The original DLL SHA-256
is `4350a7ae25ba7aec35677c213fdceabbb638676bb00ab59131d7d9c37b6e3d9e`.

Final runtime receipt SHA-256:
`d6d053e73eb0a7625177e1901936efeed4ee7eddadd9e822a0094398e8505808`.
Build: `2669cf597681ba30c96bcb73395c132c71c53db3951732741b5171a1a1f89878`.
Qualification: `8fe4b084ee3cd99935062377a22ce5ac897cdd8160ac71e3edc7d83e2e650ff2`.
The [allowlisted observations](../working/task_m1_40_stage3_observations.json)
contain public outcomes; raw private inputs remain local. All 41 native images
have ARM64 closure; this does not replace #10's complete late-load observation.

## Residual Risks and Follow-up Work

### Residual Risks

- Both real-game observations time out after 120 seconds following the named next
  phase; cleanup-inclusive intervals are 125,121 and 125,111 ms. Loader exit -15
  is owned termination, not demonstrated normal game exit. Player.log is empty.
  No authenticated Steam prefix was used. The cause remains unresolved; GC thread
  startup and repeated continuation lines do not prove GC deadlock or a Steam bug.
- Eighteen visible frames pass correctness checks; only one presentation timestamp
  is positive and 17 are zero. Drawable timing remains unqualified.
- Finite tests do not establish arbitrary PE/x64/graphics support. AVX is not
  exposed, and this task does not qualify i386/WoW64 or complete process coverage.
- Retained private dependency receipts are required. Same-host component correction
  is not independent clean-machine reproduction or ordinary-user distribution.
- No #40 remote CI or independent maintainer review yet; publication is pending.

### Follow-up Candidates

No new Issue is needed. Existing #11 owns the post-attach startup, official Steam
and responsive menu; #12 owns combat/input/audio/save/relaunch, #10 complete
observation, #13 assembly/reproduction and #15 controlled performance measurements.

The [Stage 3 handoff](../working/task_m1_40_stage3.md#11-handoff-later-startup-stall)
identifies the exact frozen candidate and minimum next diagnosis. Local
`.build/task40/stage3-handoff.json` binds the consumer, paths and committed producer
sources. Consumers must inspect these read-only and make separate experimental
outputs; current #40 qualification does not transfer to modified candidates.

Before another diagnostic option, use a narrowly reviewed shared callable with
separate candidate admission and a fixed option allowlist, binding source and
settings hashes. Do not add a full runner copy or rewrite historical producers.
Do not rerun the native matrix merely to refactor Python.

Completed loader/CPU/ordering scratch prefixes were already removed after replay.
Preserve original failures, game contexts, required graphics prefixes, final
candidate and dependency trees. No additional native build or runtime output was produced
in this documentation-only stage; no consumer evidence was deleted.

## Approval Request to Task Requester

Approve this final report and PR publication. All local #40 stages are complete;
merge and Issue closure remain pending review. This does not approve or claim
menu, Steamworks, gameplay, M1 or ordinary-user release success.
