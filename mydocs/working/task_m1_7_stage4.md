# Task #7 Stage 4 — Typed Wine Metal Pairing and Finite Native Verification

GitHub Issue: [#7](https://github.com/postmelee/pear/issues/7)
Implementation plan: [`task_m1_7_impl.md`](../plans/task_m1_7_impl.md)
Stage: 4 — completed October 3, 2026; Stage 5 is not started.

## Stage Purpose

Replace the selected DXMT bridge's copied private Wine window layout with a typed, versioned ownership boundary. Build the actual paired Wine/DXMT artifacts and verify native layer operations, error handling, invalidation and physical reference lifetime through an original ordinary ARM64 PE fixture. This completes the approved finite native pairing gate; translated Direct3D and Rosetta-free Megabonk remain unqualified.

Context used: approved task/implementation plans and October 3 continuation, root/runtime/DXMT/host/tests rules, architecture/runtime/source contracts, graphics research and #4's final Wine receipts. Reuse retains Wine C/Objective-C and DXMT C/C++/Objective-C, existing callback scheduling, immutable source/build readers and owned-process supervision. Reporting follows the [stage procedure](../skills/task-stage-report/SKILL.md), [daily board procedure](../skills/todo/SKILL.md) and central template. The [Pear Apple-tooling skill](../skills/pear-apple-tooling/SKILL.md) selected only `using-metal-validation` at Apple guidance commit `4f42344c90be22112f46becc3fb9687f423f2f88`, plugin reference `1.0.0-beta.1`; the installed validation manual and SDK header semantics were reconciled with this finite source-built Wine route. No capture or plugin/toolchain installation occurred in this stage.

## Artifacts

| File | Change Summary |
|---|---|
| `runtime/dxmt/patches/series.json`, `wine/`, `dxmt/`, `include/`, `payloads/` | Exact source-matched supplements, shared 48-byte native ABI, Wine-owned generation/lease registry and retainable DXMT proxy; unchanged PE thunks/exports |
| `tools/dxmt/pairing_source.py`, `pairing_build.py`, `pairing_reuse.py`, `pairing_monitor.py` | Ordered source replay, targeted Wine driver and DXMT construction, preserved prerequisites and bounded source/tool/file admission |
| `tools/dxmt/pairing_check.py` | Independent actual artifact, configuration, export and source-to-binary pairing replay |
| `tools/dxmt/pairing_runtime.py` | Full development-only materialization, current profile/certificate/claim admission, source origins and per-image signing evidence |
| `tools/dxmt/run_pairing.py`, `pairing_evidence.py` | Owned ordinary ARM64 PE/native supervisor, exact finite schedule replay and separate immutable root-authored diagnostics review |
| `tests/dxmt/pairing/`, six `test_pairing*.py` / `test_run_pairing.py` files | Original native/PE/control fixtures, unchanged pinned DXMT thunk headers and 89 added portable controls |
| [Observations](task_m1_7_stage4_observations.json) | Allowlisted capacities, counts, formats, outcome boundaries and receipt digests |
| `mydocs/plans/task_m1_7_impl.md`, `mydocs/orders/20261003.md` | Explicit Stage 4 approval, finalized CLI and current status |

The eight new pairing tools total 2,591 lines. The original fixture/control/protocol sources total 348 lines; copied upstream headers retain their exact pinned bytes and notices.

## Body Change Scope / Lossless Preservation

Changes use the approved graphics patches, tools, tests and internal `mydocs/` locations. No official product/API document changes or stable upstream API claim is introduced. The historical Wine 23-patch series (`39371f21f25cf153437fd523951be9f938cc1161bed5c4ef923583c74c89d086`), final source/install receipts, earlier DXMT producer files and original source caches remain unchanged. No failure artifact was removed for storage. Scoped Git attributes preserve required unified-diff context spacing and exact copied upstream notice bytes; ordinary source/test/document whitespace checks remain active.

The version-1 native C interface validates size/features and clears outputs before failure. Its opaque lease tokens are monotonically assigned and bounded to 64 live slots. Wine snapshots and retains its actual client surface under the existing driver lock, then releases that lock before any main-thread wait. Attachment, invalidation and Objective-C operations use Wine's main-thread scheduling; callback reentry is refused. Surface replacement, detach and destroy invalidate the source generation before disposal. Each lease owns native references, while the bridge balances one attachment ownership. A transient reference protects the selected layer callback.

DXMT uses an original retainable proxy owning one lease. All six selected layer consumers use the checked callback rather than a copied private field: drawable acquisition, property get/set, color space, EDR and display settings. Upstream conversions and native thunks remain intact. The fixture witnesses the actual WineMetalView delegate and independently counts physical view/layer/proxy deallocation after finite autorelease/main/event/CA drains; zero registry counts alone are insufficient.

Actual construction rebuilds the affected Wine driver and DXMT against byte-verified retained shader/tool prerequisites. The development runtime preserves the full Wine payload and adds only the selected rebuilt driver, native winemetal and original ordinary ARM64 fixture. The ARM64X DXMT DLLs are inspected, but are not admitted or executed by this fixture route. Profile/CMS, certificate bytes, raw commands/logs, prefixes, addresses and process identities remain private and ignored. Signing does not establish ordinary-user distribution authorization.

## Verification Results

Execution context: Apple M4 Pro, 24 GiB, macOS 26.5.2 (25F84), Xcode 26.6 (17F113), SDK 26.5, Apple Clang 21, Python 3.13.5, source-built LLVM 15.0.7, LLVM-MinGW 20260908 / LLVM 23.1.1 and the previously qualified Metal Toolchain 17F109. Native operations were serialized. The owned loader explicitly requested the actual 4 KiB process mode; the kernel page size is 16 KiB. Every observed required host image/process in this finite route is native ARM64 without Rosetta.

Commands executed (the profile and exact Wine role/tool handles remain private):

```sh
python3 -B tools/dxmt/pairing_build.py --artifact .build/task7/stage3-build --output .build/task7/stage4-build6 --max-growth-bytes 8589934592 --reserve-free-bytes 4294967296 --require-empty
python3 -B tools/dxmt/pairing_check.py --artifact .build/task7/stage4-build6 --require-native-abi
python3 -B tools/dxmt/pairing_runtime.py --artifact .build/task7/stage4-build6 --profile "$pear_wine_profile" --output .build/task7/stage4-runtime1 --require-empty
python3 -B tools/dxmt/run_pairing.py --runtime .build/task7/stage4-runtime1 --output .build/task7/stage4-pairing1 --require-empty
# Root explicitly reviewed every captured nonfixture stderr line and wrote the separate immutable diagnostics-review.json.
python3 -B tools/dxmt/pairing_evidence.py --run .build/task7/stage4-pairing1 --require-complete
python3 -B -m unittest discover -s tests/dxmt -p 'test_*.py'
python3 -B -m unittest discover -s tests/wine -p 'test_*.py'
python3 tools/check_governance.py
git diff --check
```

Results:

- The completed construction and independent native ABI/artifact gate exited 0. All ten commands succeeded: Wine configure/driver, ordinary fixture compile, DXMT configure/compile, four builtin operations and install. Eight actual artifacts include two thin ARM64 native libraries, the ordinary ARM64 driver/fixture and four inspected ARM64X DLLs. Build receipt SHA-256: `e2ebeab2e7e26c4b15dbd483b45c4a970e7439ad8071a21a9faf10a21771c682`.
- Fresh development admission passed for 39 native images and 756 PE images, the current WineLoader App ID/profile, device/expiry/claims and the actual leaf certificate of each signed image. Only the loader receives its authorized cross-architecture/JIT claims; ordinary libraries, server and helpers retain zero entitlements. Hardened Runtime and library validation remain enabled. Structural receipt replay is separate from fresh live Apple admission.
- The actual ordinary ARM64 PE fixture and native source functions passed all 39 cases. They cover getter version/size/features/output refusal, null device/window/no-client/foreign ownership, multiple leases, stale/double release, selected six DXMT layer operations, owned native exception/reentry, resize, replacement, detach, destroyed window, native library close and physical lifetime. The final three views, three layers and one proxy were each physically deallocated; final live leases/attachments are zero. The observed schedule is finite, not general race freedom.
- The terminal PE record has primary error 0, cleanup error 0, six completed phases and cleanup flags 7. Seven source-registered PE processes reached publication observations; owned descendants/server were accounted for and cleaned up, and the unrelated sentinel survived. Passive PE arena publication/retirement/reuse and the preserved eight-slot/524,288-byte dynamic budget passed. Dynamic-code execution was unperformed.
- API and shader-validation variables were set before device creation. Root reviewed all captured stderr: three fresh-prefix working-directory fallback warnings and twelve exact API/GPU validation-enabled notices from independently accounted Wine processes. No Metal API validation error was observed. Shader-validation configuration/notices do not qualify a shader workload. The separate immutable review preserves the original run's `diagnostics_review=unperformed` record; the independent evidence gate confirms `finite_native_scope_complete=true` and `metal_api_validation=reviewed_no_errors`.
- All 284 DXMT portable tests passed in 26.990 seconds. The Wine suite passed 842 tests in 37.892 seconds with ten conditional skips; skipped cases remain unperformed. The first sandboxed Wine run failed two owned socket/file-mode controls because those operations were restricted; the approved local rerun passed with those controls available. No production reader or skip rule was weakened. Governance before this report passed 22 documents / 172 local targets; final report links and whitespace are checked again for the bundled commit. The full staged check initially identified preserved patch context/source spacing and an exact upstream notice; narrow attributes classify those provenance files without changing qualified source/binary bytes.
- Earlier build attempts and reader failures were preserved: patch-mode admission, tool alias admission, generated locale alias monitoring and actual native source compile defects. Narrow fixes added the real main-thread declaration, scoped an upstream typedef collision and retained correct Wine callback declarations. Reader limits were increased only locally for the actual bounded build receipt/Makefile. A historical wrapped failure did not retain its original OS errno; it remains unavailable rather than invented. Current failure wrappers preserve original domains/codes separately from evidence/cleanup failures. A root-only review-context serialization attempt failed on an in-memory set; no runtime, logs or receipt changed, and the subsequent explicit review and independent gate passed.
- Construction logs contain 69 warning occurrences from retained source/deployment behavior. General execution defects, older macOS compatibility and renderer recovery are not resolved by successful compilation or this finite boundary test. Independent source-only review found no remaining selected pairing/evidence defect.

FEX initialization, hybrid/translated guest dispatch, general Direct3D/shader rendering, Steam, Megabonk, performance/thermal measurements, final fresh reconstruction and ordinary-user distribution are unperformed. `runtime_eligible`, `game_qualified` and `distribution_qualified` remain false.

## Residual Risks

- The finite native API/lifetime schedule does not establish arbitrary concurrent callback safety, general swapchain recovery, rendering correctness, GPU performance or shader semantics.
- #5/#6 still own translated execution and the memory/context/CHPE prerequisites. The original native-only publisher guard remains in force; ARM64X construction does not qualify loading or dispatch.
- Retained prerequisites were byte-verified rather than independently rebuilt in this stage. Stage 5 must reconstruct the final candidate, account for raw differences and reexecute affected pairing when bytes/settings change.
- Development signing/profile admission is specific to the observed host/date. Fresh permission, distribution signing/notarization, source/license closure, broader hardware/macOS coverage and ordinary-user installation remain later gates.

## Impact on Next Stage

Stage 5 can reconstruct these selected Wine/DXMT supplements in fresh owned outputs, compare unsigned installs and document the exact contributor/handoff procedure in the already approved official locations. Preserve the immutable baseline, this finite native evidence and every failure. Reexecute affected same-artifact pairing only when changed inputs invalidate it. Full translated D3D, Steam, games and distribution are outside that stage's gate.

## Approval Request

Review Stage 4 and approve continuation to Stage 5 fresh reconstruction and integration handoff. This does not authorize translated guest/game execution, PR publication or distribution. Task #5 Stage 3 remains in progress under its separate explicit approval.
