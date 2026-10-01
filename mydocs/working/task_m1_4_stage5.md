# Task #4 Stage 5 — Native Wine Mac-driver Boundary

GitHub Issue: [#4](https://github.com/postmelee/pear/issues/4)

Implementation plan: [`task_m1_4_impl.md`](../plans/task_m1_4_impl.md)

Stage: 5

Verification date: October 1, 2026 (Asia/Seoul)

## Stage Purpose

The approved Stage 5 establishes a finite Win32/Cocoa callback and teardown path in the actual ARM64 Wine host. Twenty original Windows window lifetimes passed: Cocoa close event, Wine event-queue dispatch, guest application callback, native title reentry, destruction and actual post-super object deallocation. The complete API/ABI/thread/window suite and three native bootstrap controls passed on the same signed bytes. This completes Stage 5 of #4; it does not complete the Wine port or the Rosetta-free Megabonk milestone.

Context used: the approved [task plan](../plans/task_m1_4.md), [implementation plan and reuse decisions](../plans/task_m1_4_impl.md), [Stage 4 report](task_m1_4_stage4.md), [root rules](../../AGENTS.md), [runtime rules](../../runtime/AGENTS.md), [test rules](../../tests/AGENTS.md), [host rules](../../host/AGENTS.md), [documentation rules](../../docs/AGENTS.md), [architecture](../../docs/architecture.md), [delivery plan](../../docs/delivery-plan.md) and [runtime contracts](../../docs/runtime-contracts.md). Reporting follows Hyper-Waterfall v0.3.0 [stage-report](../skills/task-stage-report/SKILL.md) and [daily-board](../skills/todo/SKILL.md) procedures and the central stage-report template. Metal execution and capture are outside this stage.

Upstream reuse: retain Wine commit `4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf` and its C/Objective-C driver, `OnMainThread`, `WineWindow`, `WineEventQueue`, win32u callback dispatch and existing x18 gateways. The fixture reuses Wine's ordinary windowless application-defined wake pattern. It adds no persistent target retain, forced release, new translator or language replacement. The final correction concerns fixture event-loop progress; it is not a demonstrated production ownership repair.

## Artifacts

| File | Change Summary |
|---|---|
| `runtime/wine/patches/0005-darwin-mac-driver-observation.patch` | Explicitly gated driver observations, real event/callback bridge, paced AppKit turns, queue predicates and bounded private owner diagnostics |
| `runtime/wine/patches/0005a-window-fixture-capacity.patch`, `series.json` | One additional finite PE slot and 128 KiB capacity allowance; attributable ordered patch identities |
| `tests/wine/fixtures/{window_pe.c,window_control_pe.c,window_native.m,stage5_protocol.h,stage5_census.h}` | Original ARM64 Windows fixture, PE/native control and bounded native observation protocol |
| `tests/wine/cases-stage5.json`, Stage 5/window tests and C/Objective-C harnesses | Twenty lifetimes, malformed/incomplete evidence rejection, production-argument compile checks, bounded census and maximum-shaped serialization tests |
| `tools/wine/{build.py,signing.py,abi_review.py}` | Build and bind the actual window fixture/driver bytes and validate scoped development authorization |
| `tools/wine/{api_runner.py,run_fixtures.py,verify.py,dynamic_evidence.py,window_evidence.py}` | Complete suite selection, independent lifecycle replay, fixed trusted window-only capacity and historical-scope preservation |
| `tools/wine/stage5_evidence.py`, [`task_m1_4_stage5_observations.json`](task_m1_4_stage5_observations.json) | Revalidated allowlisted public results with exact producer/input/output identities |
| [`wine-host.md`](../../docs/development/wine-host.md), plans and daily boards | Approved driver protocol, #7 ABI/ownership handoff, retained failures and current stage status |

## Body Change Scope / Lossless Preservation

The only official-document destination changed is the approved existing `docs/development/wine-host.md`. Plans, reports, observations and daily boards remain under `mydocs/`. Prior stage reports, the original source audit, architecture and delivery milestones are preserved. The first 19 ordered patches are unchanged. Original fixtures retain MIT notices; Wine integration retains its LGPL terms.

The observer is enabled only for the owned window fixture. Twenty application callbacks remain exactly twenty even when additional AppKit wake events are needed. Each wake carries a safe-integer tag/cycle/ordinal, is windowless, and is consumed by normal AppKit dispatch. At most one is pending. The first turn is mandatory; later posts stop after observed deallocation. Completion requires all posted turns consumed, a strictly later main-thread barrier, actual post-super deallocation and all four independently observed idle facts: empty signaling FD, empty event array, no active Wine event and the matching owner queue. Finalization repeats those queue checks. A missing queue, late callback or observation error fails.

The existing five-second/100-drain bound and twenty lifetimes are preserved. Only the trusted window loader receives 12 MiB of event capacity; only its saved case receives 32 MiB/2,000,000 JSON nodes. Other per-process and case limits, the aggregate 32 MiB event limit, per-line limits, process ownership and cleanup remain unchanged. The finite protocol has at most 16,527 atomic parts; the portable maximum-shaped regression exceeds the old limits and passes the new scoped limits. Saved JSON cannot grant itself a larger allowance.

Private diagnostics, game files, credentials, authenticated prefixes, saves, profiles and signing material are excluded from Git. Audited APFS clones reclaimed duplicate public source, unsigned-install and completed unauthenticated fixture-prefix blocks without deletion. All protected records, failed attempts, signed originals, complete inventories and excluded files were verified unchanged; independent clone inodes and destination metadata were checked. Replacement inode/ctime changes and parent-directory timestamp changes are explicitly recorded. The [implementation plan](../plans/task_m1_4_impl.md#stage-5-retained-diagnostic-history) retains every pass and receipt hash. The final two passes covered 8,506 replacements and recovered approximately 4.406 GiB; both received independent postverification before the final full suite.

## Verification Results

### Execution context and identity

Actual host: Apple M4 Pro, ARM64 macOS 26.5.2 (25F84), Xcode 26.6 (17F113), SDK 26.5. The pinned LLVM-MinGW 20260908 tools select ARM64 host slices. These are instrumented correctness fixtures in real Wine processes on this Mac. The full and bootstrap suites were invoked with separate owned process groups and temporary environments; their overall execution intervals overlapped. No performance or power conclusion follows.

The existing device-bound Wine-loader development authorization was revalidated. Hardened Runtime and library validation remained enabled. The loader's signature uses 4 KiB pages; `allow-jit` remains loader-only. All 38 native artifacts are ARM64. Validated process and loaded-image snapshots report ARM64 and no translation; snapshots do not establish a complete future load timeline. These development results do not establish distribution authorization.

| Retained record | SHA-256 |
|---|---|
| Final build, `build-stage5-attempt6` | `a9d43c3f7fe1f922fba8319dc286b6d456e4dc1a704b2bf7253a125f33de115e` |
| Signed runtime, `signed-stage5-attempt6` | `24c0cc21895d1d69d0d5d07329f1bb0e6b82bf1668448d0741db68560a0c132c` |
| Actual assembly review | `fd9d93f65ba0ddfb01f28e30c44115e6b8ec601abd3999a270b67195820ee212` |
| Full suite, `runs-stage5-attempt6` | `3503a25271f6df817fd514af6c174d86ccabd7c2e9343d71bc2c4e55fcce5d63` |
| Bootstrap, `runs-stage5-bootstrap-attempt6` | `deda75c29e392c5fb3b8ae6aaae71a092709669a3bfd5d57259bed3fdf6baac9` |
| Public Stage 5 observations | `91540517e5150d26217ba765c65e4b3aa9c15bd9d4cf47f82072a517bfc66c55` |

The actual window fixture SHA-256 is `97f8d581358ce08cfc46480a54e7f043581ec5815284d4b72cf6edb332d2aa30`; the driver PE is `71f5d8d6d4dbe57b9b5c46d258d4cb73187da109a15eb95c7eac22c1a89b6250`; its native driver is `e93c561f5eb6da851230fb41ae7063e6d6c4f5680248c479c1f46a4a91ca5aa9`. All source, producer, patch and build identities are in the public observations.

### Actual commands and outcomes

These are the actual retained output names. Choose fresh output directories for a later reproduction; do not overwrite the failed or successful originals.

```sh
python3 tools/wine/build.py --variant arm64 --inputs .build/task4/inputs --tools .build/task4/tools --output .build/task4/build-stage5-attempt6 --jobs 4
python3 tools/wine/abi_review.py --build .build/task4/build-stage5-attempt6 --output .build/task4/build-stage5-attempt6/abi-review.json
python3 tools/wine/signing.py prepare --build .build/task4/build-stage5-attempt6 --local-input .build/task4/private/signing.json --output .build/task4/signed-stage5-attempt6 --require-empty
python3 tools/wine/run_fixtures.py --suite mac-driver --runtime .build/task4/signed-stage5-attempt6 --output .build/task4/runs-stage5-attempt6 --require-empty
python3 tools/wine/verify.py runs --root .build/task4/runs-stage5-attempt6 --suite mac-driver --require-complete
python3 tools/wine/run_fixtures.py --suite bootstrap --runtime .build/task4/signed-stage5-attempt6 --output .build/task4/runs-stage5-bootstrap-attempt6 --require-empty
python3 tools/wine/verify.py runs --root .build/task4/runs-stage5-bootstrap-attempt6 --suite bootstrap --require-complete
python3 tools/wine/stage5_evidence.py --build .build/task4/build-stage5-attempt6 --runs .build/task4/runs-stage5-attempt6 --bootstrap-runs .build/task4/runs-stage5-bootstrap-attempt6 --output mydocs/working/task_m1_4_stage5_observations.json
python3 -m unittest discover -s tests/wine -p 'test_*.py'
python3 tools/check_governance.py
git diff --check
```

Build, signing, both execution suites, independent run verification and public export passed. The build completed 42 commands with all 21 patches and produced 38 ARM64 native artifacts and 755 PE artifacts (753 ARM64 and two unexecuted x64/i386 controls). Both controls were refused before execution because no translator is qualified. All **779 regression tests passed with no skips**. Governance verification passed for 22 documents and 162 local targets; `git diff --check` passed.

The actual final driver layout and relocation fixture were also checked using the retained private `final-static-checks.py` adapter and public relocation checkers. Three source-remapped native production compiles and the actual ARM64/ARM64EC PE adapter recipe passed before the full build. These are compile/assembly checks, not ARM64EC execution or a fresh complete companion build. Private static-check receipts remain under `stage5-research/final-build-static-attempt6`; Stage 6 must provide fresh reconstruction rather than treating those historical receipts as reproducibility.

| Actual execution gate | Result |
|---|---|
| API and ABI | Both passed, retaining original arguments/imports, guest/native x18 transitions, callbacks and relocation checks |
| Threads, memory and exceptions | Passed the unchanged finite worker/TLS, protection, dynamic-code, fault, signal and suspension controls |
| Win32/Cocoa lifetimes | 20 creations, Cocoa closes, application callbacks, native reentries, destructions and actual post-super deallocations |
| Event progress and teardown | 160 paired AppKit turns, 180 barriers and 180 drains; 943 logical native observations / 1,887 atomic parts |
| Per-lifetime scope | 7–9 turns and 8–10 drains; all posted turns consumed before the qualifying later barrier |
| Ownership and loaded images | Actual driver, AppKit and CoreFoundation bound; one observed main thread and one Wine callback thread; all host mode samples zero |
| Final state | Zero observed late callbacks, active owned windows or pending owned events; final queue check passed; window class unregistered |
| Bootstrap controls | Normal stop, bounded timeout cleanup and wrong-prefix server refusal all passed |
| Containment | Owned cleanup complete, no observation gap and unrelated sentinel survived in every case |

Independent review matched the window case's raw logs to saved rows and checked lifecycle order, all four idle bits, event identities, post-deallocation behavior and cleanup. The final public exporter revalidated both suites against the same signed build and current producers; diagnostic-only results cannot pass its gate.

### Retained failures and diagnosis

The initial integrated build exposed a missing `<stdarg.h>` prerequisite in the PE adapter; a production-argument compile regression now covers it. Attempts 2–5 built but did not observe the first closed window's deallocation within the unchanged bound. Callback/reentry/destruction success alone was never accepted. A first single AppKit wake, direct queue checks and the bounded owner census did not resolve those runs; all failed records remain intact. The census-header exporter omission found by regression tests was corrected before the passing final suite.

Two owned stack-sampling attempts produced no report and remain failed diagnostics. Earlier ordinary AppKit probes did not consistently reproduce retention. A separately signed, geometry-measured comparison then reproduced it in both default 16 KiB and requested 4 KiB modes. With a second ordinary event, the window deallocated before shutdown. A paced control passed with eight turns in both modes; the actual Wine diagnostic subsequently passed twenty lifetimes, followed by the independently verified final full suite above. This supports finite fixture event progress. It neither identifies a private AppKit retaining owner nor proves a general Wine leak or a 4 KiB-specific defect.

## Residual Risks

- FEX/x64 translation, Steam, Megabonk, Metal/D3D/DXMT rendering and ordinary-user installation/distribution remain unperformed or unqualified. No game support claim changes.
- The no-late-callback observation ends at the final barrier/drain. General callbacks, native-created guest callback threads, arbitrary asynchronous behavior and future loaded images remain outside the finite evidence.
- The observer and owner census are diagnostic instrumentation. Pre-INIT and indirect/framework ownership limits remain explicit; draw-body completion is not proof of block disposal. No performance conclusion follows.
- A separate source inspection found `run_cocoa_app` reading caller-owned startup state after signaling the caller to return. That unresolved storage-lifetime ordering was not linked to the retained-window behavior and was not repaired here; broader startup qualification needs focused lifetime/error-path review.
- The pinned DXMT private layout expects `client_view` at offset 24; the selected Wine ARM64 layout places it at 16. Exporting names alone cannot repair this mismatch. #7 needs a source-matched, typed interface and actual view/layer lifetime tests.
- Stage 2's full ARM64EC companion is historical. This stage only compiled the changed PE adapter for ARM64EC. Fresh native and companion reconstruction, independent-machine testing and distribution evidence remain incomplete.

## Impact on Next Stage

Stage 6 must reconstruct the final ordered sources into empty native and companion build directories, verify actual tool/input identities, explain unsigned-byte differences, and rerun all required native suites on one final signed runtime. Preserve this stage's exact artifacts and failures as comparison inputs. The compiler tool cache may be reused only after verification; this is not an independently rebuilt compiler claim.

Carry the concrete ABI/ownership handoff in the [Wine guide](../../docs/development/wine-host.md#native-driver-interface-handoff-to-7), the startup lifetime review item, finite observation limits, signing scope and original blocked combined source decision to #5/#7/#10/#13. Completion of Stage 5 does not authorize the next stage, close #4, publish a PR or qualify a game.

## Approval Request

Approve the Stage 5 artifacts and verified results, then authorize the planned Stage 6 fresh reproduction and integration handoff. Stage 6 and PR publication have not started.
