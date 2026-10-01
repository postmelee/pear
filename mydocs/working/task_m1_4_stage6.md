# Task #4 Stage 6 — Fresh Wine Reproduction and Integration Handoff

GitHub Issue: [#4](https://github.com/postmelee/pear/issues/4)

Milestone: M1 — Megabonk on Apple Silicon without Rosetta

Implementation plan: [`task_m1_4_impl.md`](../plans/task_m1_4_impl.md#stage-6--fresh-reproduction-and-handoff)

Stage: 6

Verification date: October 1, 2026

## Stage Purpose

Reconstruct the final selected Wine component from pinned source and ordered patches, compare two fresh native builds, account for the ARM64EC companion, and repeat bounded executable checks on one freshly signed native candidate. All fourteen operations and independent reconstruction verification passed. This is a development-component result; x64 translation, Steam, Megabonk, graphics and ordinary-user distribution remain unqualified.

Context used: the approved [task plan](../plans/task_m1_4.md), detailed implementation plan and Stage 6 authorization; [Stage 5 report](task_m1_4_stage5.md); applicable root/runtime/tests/host/docs rules; the [architecture](../../docs/architecture.md), [delivery plan](../../docs/delivery-plan.md) and [runtime contracts](../../docs/runtime-contracts.md); selected upstream Wine/CF source; central [stage template](../_templates/stage_report.md), [task-stage-report skill](../skills/task-stage-report/SKILL.md) and [board format](../skills/todo/SKILL.md), from Hyper-Waterfall v0.3.0. Pear Apple-tooling is not applicable to this host-only work.

Reuse decision: retain Wine C, Objective-C/MRC and assembly, its entry/callback/thread machinery and CF startup mechanism. Reuse the existing materializer, tool verifier, builder, inspectors, signer and fixture runner. New Python code coordinates and independently replays these owners; it is not a replacement runtime engine or language rewrite.

## Artifacts

| Files | Change Summary |
|---|---|
| `tools/wine/reproduce.py`, `reproduction_evidence.py` | Serial empty-directory reconstruction, fourteen operation receipts, independent replay and allowlisted public observations |
| `tools/wine/unsigned_compare.py` | Complete native unsigned-install inventory and strict byte/format comparison; unexplained code/data differences remain rejected |
| `tools/wine/arena_reproduction.py` | Fresh build/sign/run/replay of the existing six-case standalone page-W^X prerequisite, separately from Wine |
| `tools/wine/build.py`, `verify.py` | Stable relative configure source policy and explicit native/compile-only companion assessment |
| `tools/wine/toolchain.py` | Preserve bounded, validated archive regular-file mtimes rather than accidentally entering unavailable maintainer regeneration |
| `runtime/wine/patches/0006-system-thread-exception-order.patch` | Guard the optional TEB read before reusing upstream registered-system-thread exception handling |
| `runtime/wine/patches/0006a-cocoa-startup-request-lifetime.patch`, `series.json` | Independently owned caller/callback request, atomic pending claim/cancellation, source invalidation and timeout-safe cleanup |
| `tests/wine/test_reproduce.py`, `test_reproduction_evidence.py`, `test_reproduction_integration.py`, `test_unsigned_compare.py`, `test_arena_reproduction.py`, affected build/tool tests | Required-gate, identity, scope, comparison and failure rejection coverage |
| `tests/wine/test_cocoa_startup.py`, `fixtures/cocoa_startup/` | Exact ordered source reconstruction, Foundation/CF ownership checks, upstream LGPL baseline/license and two safe semantic controls |
| [Wine host guide](../../docs/development/wine-host.md), [documentation index](../../docs/README.md), [source qualification](../../docs/source-qualification.md), [dated runtime audit](../../docs/research/macos-runtime-audit.md) | Approved narrow result links, actual execution preconditions and typed integration handoff |
| [Public observations](task_m1_4_stage6_observations.json), plans and active-date board | Exact hashes/counts, bounded acceptance map, preserved failure history and current checkpoint |

## Body Change Scope / Lossless Preservation

Official guidance remains in the four approved existing `docs/` locations; task history stays in `mydocs/`. The original source audit, #2 results, previous reports and roadmap remain intact. New dated addenda preserve #1's blocked aggregate rather than replacing it with component success. No runtime lock or support claim is introduced.

The patches preserve upstream notices and LGPL terms. The durable Cocoa baseline retains its original header and full `COPYING.LIB` wording (two trailing spaces on one blank license line were normalized); the comparator retains pinned XXH3 attribution and BSD terms. No game files, authenticated prefixes, credentials, saves, signing/profile material or raw private diagnostics are committed. Independent source and public-output privacy/attribution review found no actionable issue.

All old successes, failed attempts and raw diagnostics remain local. Reviewed exact APFS clones shared duplicate public-source/unsigned-install/fixture blocks without deleting artifacts, modifying signed originals or treating local private evidence as Git-backed. Content and required metadata were independently rechecked; replacement inode/ctime and parent timestamp changes are recorded. Detailed storage receipts remain in the implementation plan.

Behavior changes are narrow: stable relative source arguments prevent temporary absolute paths from altering anonymous-namespace names; archive mtimes preserve release ordering; the exception guard avoids a TEB access in a legitimate no-TEB system-thread state. Cocoa startup now has defined caller/callback ownership across completion and timeout, with no post-deadline join or success upgrade. The five-second wait, publication before `NSApp.run` and existing callback-local run decision remain unchanged. No launch-notification readiness barrier was selected.

## Verification Results

### Actual execution context

- Apple M4 Pro, ARM64; macOS 26.5.2 (25F84); Xcode 26.6 (17F113), macOS SDK 26.5; locked LLVM-MinGW 20260908 / LLVM 23.1.1 and Bison 3.8.2. The compiler/tool cache was reverified, not independently rebuilt for reconstruction.
- Wine commit `4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf`, tree `10b47b2965a7b3e1e9694ec506a3d13525211892`; archive `f5d89a11b33ca5db93576d8e53fd3bbe86d68f18a3d711ef5e21ed994bf8c662`; final ordered 23-patch series `39371f21f25cf153437fd523951be9f938cc1161bed5c4ef923583c74c89d086`.
- Fresh `reproduction3` source/reference/candidate/companion directories; 26.100 GiB free at the unchanged 26 GiB start gate. All three builds use `stable_relative_v1`, `/bin/sh ../source/configure` and four bounded build jobs, serially. No earlier compiled Wine output is an input.
- Real device-bound development authorization, Hardened Runtime and library validation enabled, 38 signed native images, 4 KiB loader signature pages. Restricted and public JIT claims are confined to the actual loader; ordinary helpers have no restricted claims. This is not general-user permission or notarization.
- The private launcher retained restrictive parent record creation and explicitly gave only the coordinator child umask 022. Wrapper SHA-256 `1147af340d0b6dee9f398941db7e1f92abe3265164c0019e0e311adca8cde9e8`; coordinator bytes stayed unchanged.
- A finite owned `caffeinate -d -u -t 7200` assertion and separate CoreGraphics observation kept the accepted local session described precisely: initial/pre-run, 441 periodic and post-run observations were awake, active and online. Pre/periodic/post interval has 443 samples; maximum observed gap 5.021 seconds. The assertion was terminated and reaped (status -15). Its expiry was not a job deadline or proof of continuous state between samples. Display record SHA-256 `2be296eb4a62936505ddad2d5591f9d82c380427677bf147b2dedb9741f7346c`. The public exporter does not validate this private sidecar; root reviewed it separately.
- Normal production fixture observers and environment policies only: no extra Wine trace override, sampler, private fault observer or replacement window workload. This is correctness instrumentation, not a power/performance benchmark.

The fixture configuration explicitly disables the upstream Wine conformance suite and selected optional networking/authentication, audio, codecs, Vulkan and external font features. EGL was unavailable. The repository regression count below is not the full upstream Wine test suite; rendering/font support remains unqualified.

### Commands and result binding

The corrected private wrapper launched this unchanged coordinator command with child umask 022 and the measured display context above:

```sh
python3 -B tools/wine/reproduce.py --inputs runtime/wine/inputs.json --toolchain runtime/wine/toolchain.json --config runtime/wine/build-config.json --source-cache .build/task1-sources/inputs --tools .build/task4/tools-stage6-mtime --local-signing .build/task4/private/signing.json --output .build/task4/reproduction3 --require-empty
python3 -B tools/wine/verify.py reproduction --root .build/task4/reproduction3 --require-complete
python3 -B -m unittest discover -s tests/wine -p 'test_*.py'
python3 tools/check_governance.py
git diff --check
git status --short
```

All fourteen operation records passed and were independently replayed:

| Operation | Result | Record SHA-256 |
|---|---|---|
| `prepare_inputs` | Passed | `9f262d355f6148a66b3eefb74f3f0bee2f39f8168691aadfaeb02dabddf6b5bc` |
| `toolchain_check` | Passed | `0b0b3b1041638051b79c4e8a5fde8f8f9a1f2b2c4c132dcc0fa724f29b49d937` |
| `native_arena` | Passed | `2e47917896d2a1d0aeca73f42c047f619a4883d11f44c2e6649d75b279e84f6f` |
| `native_reference_build` | Passed | `2d824a65849954543ef87124a888bf4cca8d87b370257bcacff30483023e12e9` |
| `native_reference_modules` | Passed | `8c6517344e34e96f8b9c2e16dc4f22fda11ee9c113f79c779dbe2cbfff0b5023` |
| `native_build` | Passed | `f7041374d7cdc86ea2991f859c8c102e369ed2247cb69a3647f4b9ddfae2f1eb` |
| `native_modules` | Passed | `3342ba3946e7a4b81d44f29db98befa0901f13830c6e5d5c125602eb50c0435d` |
| `native_abi` | Passed | `e36fb4587742459598f71cc72ec7e9b9af90e963de8f0b32abfe43dabeeef284` |
| `companion_build` | Passed | `d71d69ab5b5612d33b5fd73997d1e38f09b2a72a9625cd9c954817bbf05c77ad` |
| `companion_modules` | Passed | `1a87fcb537dea3e5e21dd21d30d6e650c2c553786e79bdfd8eec61d25c2332dc` |
| `unsigned_compare` | Passed | `5ddb7ee59e41beee1c334ef33ffd36b8d2094fd4bc3e2720f85e5373be41bec1` |
| `signing` | Passed | `e1b99402ed15b84a03fe27ef1403974a338812a2508618761dc89f9d9f487764` |
| `bootstrap` | Passed | `008cf4a212215a8f2835586deffd5ace362b7a215b1aae0367a3c7c0c666377d` |
| `mac_driver` | Passed | `e53d36ee00ba31252bd9a47c17b1a3dc7141a6085d0eecc1c3fbbc8d63b156be` |

The terminal reconstruction is `fb39c578ae50030703b10ca718af63e76786c42bc02ffc231d4e0b4f40fdffff`; start record is `550e17fcf33e21689b5ed759ea36c7e6e781a4e0bded4df20bdea92161cdd6ff`. The full independent verifier exited zero. Its 109,425-byte allowlisted output was preserved unchanged as the public observations, SHA-256 `4502be49cc33fdac6c20d22c832a719c51e7378176d50aab211f14948023ab77`. Before preserving the output, the export step rechecked canonical encoding, exact fourteen operations, scope/qualification flags and current producer/configuration identities, then used the existing exclusive public writer. No second validation was run solely to export already validated identical bytes.

| Build role | Commands | Native artifacts | PE artifacts | Execution |
|---|---|---|---|---|
| Fresh ARM64 reference | 44/44 passed | 38 ARM64 | 755 | Compile/inspect only |
| Fresh ARM64 candidate | 44/44 passed | 38 ARM64 | 755 | Sole newly signed Wine runtime |
| ARM64EC companion | 44/44 passed | 38 ARM64 | 758 | Compile/inspect only |

The native PE inventory includes compile-only x64/i386 refusal controls; their presence is not an Intel host or translated execution result. Seven selected PE modules per build were inspected. All three patched-source manifests are `2c0c861669f9fd8853f8899eaeb08b18207b0cf26b34dae9efe707919e447bc7`. Installed/module/fixture identities and PE-machine distributions are in the public observations. The companion's ARM64X requirements do not fit the native publication arena; that separate measured fact neither enlarges the native gate nor qualifies companion execution.

Native unsigned comparison covered 2,729 complete installation files and equal symlinks: 1,959 exact, 770 explained metadata differences, zero unexplained, missing, extra or mode differences. Eleven format/path policies were independently replayed. Raw code/data or symbol-value changes are not discarded. Unsigned byte identity is false, and deterministic signed identity is not claimed. The retained absolute-path Stage 5 ICU differences remain rejected historical evidence, not an equivalence baseline for these two stable-relative builds.

The standalone native prerequisite freshly passed two lifecycle variants and four original matched protection controls, with owned cleanup and sentinel survival. It is a separate native fixture, not proof of integrated Wine exhaustion/fault injection. Tool verification passed 34 checks and 58 commands. All actual Wine suites bind to the same signed-record hash `e1b99402ed15b84a03fe27ef1403974a338812a2508618761dc89f9d9f487764`:

| Case | Result | Elapsed ms |
|---|---|---|
| `bootstrap` | Passed | 2641 |
| `bootstrap-timeout` | Passed | 2606 |
| `wrong-prefix-server` | Passed | 2427 |
| `abi` | Passed | 7000 |
| `api` | Passed | 6727 |
| `threads` | Passed | 7769 |
| `window` | Passed | 14065 |

The window case observed 20 complete Win32/Cocoa lifetimes, application callbacks, native reentries and post-super deallocations; 153 posted/consumed event pairs and 173 barriers/drains; zero observed late callbacks through the final barrier. Native x18/thread/image bindings and real queue/FD emptiness passed. Owned process cleanup completed and sentinels survived. Image/process observations were ARM64 and nontranslated for this bounded suite; they are not a full load timeline or game process-tree claim.

Final regression: **881 tests passed, no skips, 38.481 seconds**. Retained log SHA-256 `c001e9331e57aaa898f5b68603f5f386c58b45ce82f33b1fd3f8c75b1be29610`. Included source-bound Cocoa tests reconstruct the actual ordered patch and run the 429-check Foundation/CF harness plus two safe semantic controls. They use deterministic wait outcomes and mocked AppKit selectors, not an actual five-second live-AppKit timeout; their 64 KiB stream checks occur after capture rather than imposing live pipe caps.

Final governance passed for **22 documents and 172 local targets**, with consistent skill routing and source inventory (offline); log SHA-256 `dd95a5814f622da87a395e1033ff37ba69ec9d16d3bb2156e056d3dcaaf658ec`. `git diff --check` passed. The tracked/untracked file list was reviewed as the owned Stage 6 scope; private build/sign/run evidence remains ignored.

### Preserved failed and diagnostic history

- Initial three-build reconstruction `8367323eff57c4b0814fc7fa88a4bf338d3fa6b626172b9bad965903a363923e` failed required window deallocation. Its other passing steps did not make the reconstruction pass.
- Asleep/awake AppKit controls identified a relevant display condition, but awake state alone did not resolve later Wine failures. Three awake Wine diagnostic trials sampled a native framework fault followed by the TEB-dependent exception access; the initiating fault/register context remained unknown. Later ordinary default 16 KiB controls also trapped, so a 4 KiB-only root cause is unproved.
- The 22-patch normal cumulative run `ada35a61f703501b99d3d8eadccec8dec88725c07e947a1cd9b5ab60519244c9` exited zero after one lifetime with missing terminal output and was correctly rejected. Tracing/private-observer successes stayed diagnostic-only; they did not replace normal failures.
- The subsequent 23-patch single-native normal pass is retained separately. Neither that pass nor this final reproduction proves the cause of all historical AppKit faults or broad reliability.
- `reproduction2` terminal `1438bb59f4a6156c47c21c3fde236185e908f08490eddfaa6acd2576e8256bda` stopped before configure: inherited private umask 077 caused twelve 0600/0644 source-mode mismatches while all 12,469 paths/content hashes/kinds/order otherwise matched. Comparison receipt `9c6fd13fd9cc697f50a70e0be4c8183abf739341cd3ee2d75d872cf83edc6469` and original wrapper remain retained. The corrected run used a new layout and did not relax the source-mode gate.

See the [implementation history](../plans/task_m1_4_impl.md#stage-6-retained-reconstruction-and-runtime-diagnostics) for exact prior records and failed preparation/compile drafts.

### Issue #4 acceptance map

| Criterion | Actual passing evidence | Boundary |
|---|---|---|
| Clean ARM64 host build and minimal PE/API fixtures under documented normal permissions | Empty-directory source reconstruction, all required build roles, actual development authorization, six-case prerequisite and same-signed bootstrap/cumulative execution | Same development Mac; no clean-machine, general-user or translator claim |
| Recorded patches/sources/commands without silent Intel fallback | Ordered attributed patches, exact tool/config/producer inventories, finite linked-byte ABI review and required native process/image observations | Bounded fixture snapshots; x64/i386 controls refused before execution |
| Targeted thread entry, nested callbacks, error exits and exception-context capture | Actual original API/ABI/thread/exception/memory cases, final Win32/Cocoa boundary and source-bound regressions | General translated unwind/callback/JIT semantics remain unqualified; additional no-TEB fatal-route test is unperformed |

## Residual Risks

- FEX/x64 translation, CHPE/ARM64EC runtime execution, DXMT/Metal/D3D, Steam, Megabonk and ordinary-user installation/recovery/distribution are not qualified. The combined #1 source decision remains blocked; #2 retains its original finite scope.
- The new deliberate native-fault test for the corrected registered-system-thread fatal route was blocked before execution by automatic safety review for possible cybersecurity risk. It was not retried, run, hidden as a pass or substituted with the existing standalone protection controls. Source-bound routing checks and actual object compilation support the guard; corrected native fatal termination remains unperformed.
- Sleeping/inactive/headless sessions, arbitrary later display changes, full process/load timelines, arbitrary foreign callbacks, general unwind and concurrent JIT mutation remain unqualified. Finite no-late-callback observation ends at the recorded barrier; normal exit is checked separately.
- Startup ownership is corrected, but launch readiness still publishes before `NSApp.run`. An empty CF envelope/source may remain held by an active perform frame while the application loop does not return. No framework-retainer identity, single historical fault cause or general startup/timeout reliability is established.
- This is same-host reconstruction with reused compiler tools, not an independent compiler build, second-Mac test, release notarization or ordinary-user authorization. No performance, power or thermal advantage follows from instrumented correctness runs.

## Impact on Next Stage

Stage 6 is the final implementation stage of #4. Its scoped acceptance evidence is ready for the separate final-report/PR checkpoint; #4 remains open and no publication/merge or next Issue implementation is implied.

| Owner | Reusable result | Required next evidence |
|---|---|---|
| #5 / #6 | Final selected modules/imports/exports, native Wine Unix-call boundaries, x18 helpers and finite thread/exception/memory fixtures | Darwin FEX host services, actual x64 dispatch, translated contexts/unwind and coordinated executable-memory lifetime; CHPE/non-ARM64 publication remains refused and selected xtajit64 emulation unimplemented |
| #7 / #8 | Twenty real Win32/Cocoa lifetimes and source-matched native signature/ownership table | Repair Wine client_view offset 16 versus pinned DXMT copied offset 24, missing exports/table pairing, borrowed/no-view/null/error and detach/resize/destroy races on an actual renderer pair |
| #10 | Owned process/image registration, signed-byte binding, exit/cleanup and sentinel evidence | Complete load timeline, future callbacks and arbitrary descendant coverage |
| #13 | Attributable build/tool/patch records, preserved notices and per-executable development signatures | Shipped source/license obligations, general-user authorization, packaging/notarization, installation/recovery and release qualification |

The detailed typed driver handoff is in the approved [Wine host guide](../../docs/development/wine-host.md#native-driver-interface-handoff-to-7). Fixture Unix-call indexes are not a stable public translator interface. Matching native Cocoa BOOL spelling alone is not a demonstrated ABI mismatch.

## Approval Request

Review the Stage 6 artifacts and verification, then explicitly authorize the separate final-report and PR-publication procedure. Preserve all six stage commits/reports and the scoped limits. No Issue closure or merge is requested from this report.
