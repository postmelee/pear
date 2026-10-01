# Task #4 Final Report — ARM64 Wine Host and macOS ABI Boundary

GitHub Issue: [#4](https://github.com/postmelee/pear/issues/4)

Milestone: M1 — Megabonk on Apple Silicon without Rosetta

Verification date: October 1, 2026

## Work Summary

- Target Issue: #4, `[P04] Bring up the ARM64 Wine host and macOS ABI boundary`.
- Milestone: M1; six implementation stages completed and committed.
- Purpose: establish an attributable native ARM64 Wine development component with tested loader, Windows API, callback, thread, memory, exception and Mac-driver boundaries for subsequent translator and renderer integration.

The final selected component was reconstructed from pinned sources into two fresh native build directories and a separate compile-only ARM64EC companion. All fourteen reconstruction operations and independent full verification passed. The freshly signed native candidate passed the required bootstrap and cumulative original ARM64 Windows fixtures. This completes #4's scoped host acceptance; it does not run x64 games, complete M1 or qualify Rosetta-free Megabonk for users.

Context and approval are recorded in the [task plan](../plans/task_m1_4.md), [implementation plan](../plans/task_m1_4_impl.md) and six stage reports below. The [architecture](../../docs/architecture.md), [delivery plan](../../docs/delivery-plan.md), applicable root/runtime/host/tests/docs rules and Hyper-Waterfall v0.3.0 task/report procedures governed the work. Final reporting uses the central [template](../_templates/final_report.md), [task-final-report skill](../skills/task-final-report/SKILL.md) and existing [daily board format](../skills/todo/SKILL.md). Pear Apple-tooling was not applicable to this host-only work.

Reuse decision: preserve upstream Wine C, Objective-C/manual ownership and assembly, its loader/Unix-call, thread/exception and Cocoa mechanisms, with attributable ordered patches. Retain the existing Pear source, build, signing and fixture owners; Python coordinates and independently verifies their evidence. No Rust rewrite, new CPU translator or general Windows API implementation was introduced. Source, notices and license obligations remain recorded rather than replaced by a new Pear license claim.

## Changed Files and Impact Area

| Path | Change Summary | Impact Area |
|---|---|---|
| `runtime/AGENTS.md`, `runtime/wine/{inputs,toolchain,build-config}.json`, `runtime/wine/patches/` | Scoped upstream/tool/configuration pins and 23 ordered attributed patches | Native loader/page geometry, x18 transitions, PE publication and finite memory/thread/Cocoa ownership |
| `tools/wine/` | Materialization, compiler checks, build/module/ABI inspection, signing, owned fixture execution, strict comparison and independent reconstruction readers | Reproducible development component and explicit failure rejection |
| `tests/wine/` | Original ARM64 fixtures, architecture/refusal controls, evidence regressions and licensed source-bound startup baseline | Runtime boundaries and evidence integrity; 881 repository tests |
| `docs/development/wine-host.md` and three existing official documents below | Build/permission instructions, bounded observations and typed downstream handoff | Contributor guidance without promoting game support |
| `mydocs/plans/`, `mydocs/working/task_m1_4_stage*.md`, observation sidecars, active-date boards and this report | Approval, six stage commits, sanitized evidence, acceptance and retained limits | Reviewable task history; private outputs remain ignored |

## Document Location Verification

The approved [task-plan location judgment](../plans/task_m1_4.md#document-location-judgment) and Stage 6 amendments selected the following four official locations. No product documentation moved to task-history directories, no second roadmap was created, and the original source-audit snapshot was preserved with dated component links.

| File | Planned Location | Actual Location | Result | Evidence |
|---|---|---|---|---|
| Wine host contributor guide | `docs/development/wine-host.md` | [Wine host guide](../../docs/development/wine-host.md) | OK | Approved host guide and typed integration handoff |
| Documentation index | `docs/README.md` | [Index](../../docs/README.md) | OK | Narrow guide/evidence entry |
| Source qualification | `docs/source-qualification.md` | [Source qualification](../../docs/source-qualification.md) | OK | Dated scoped #4 result; combined #1 audit remains blocked |
| Runtime audit | `docs/research/macos-runtime-audit.md` | [Runtime audit](../../docs/research/macos-runtime-audit.md) | OK | Native-component follow-up without rewriting original audit |

Plans, stage reports, final report and boards stay in their approved `mydocs/` locations. Proprietary games, authenticated prefixes, credentials, saves, raw diagnostics and private signing material are excluded from Git and publication.

## Quantitative Before/After Comparison

Counts describe scope and successive suite sizes, not performance, code quality or disjoint test totals.

| Metric | Before | After |
|---|---|---|
| #4 native Wine acceptance | No #4 Wine fixture acceptance entering the task | Authorized bootstrap and original ARM64 API/ABI/thread/memory/exception/window cases on one final signed component |
| Attributed Wine patch series | 0 at selected Stage 1 input | 23 ordered patches; final series SHA-256 `39371f21f25cf153437fd523951be9f938cc1161bed5c4ef923583c74c89d086` |
| Fresh final build roles | Historical outputs were not final-source reproduction | Two native builds and one compile-only ARM64EC companion, 44 commands each |
| Final native unsigned comparison | Historical absolute-source builds contain rejected ICU code/data layout differences | 2,729 files: 1,959 exact and 770 narrowly explained metadata differences; zero unexplained, missing, extra or mode differences; equal symlinks |
| Final artifact inspection | No final three-build inventory | 38 ARM64 native artifacts per role; 755 PE artifacts per native build, 758 in companion; seven selected module inventories per build |
| Actual same-signed runtime checks | Earlier stages had smaller suites | Three bootstrap controls and four cumulative cases: API, ABI, threads/memory/exceptions and windows |
| Final window lifecycle observation | Stage 5 result was on its historical artifact | 20 lifetimes, application callbacks, native reentries and post-super deallocations; 153 paired event turns; 173 barriers/drains |
| Repository regression suite | 95 tests at completed Stage 1 | 881 tests, zero skips, 38.481 seconds at final Stage 6 |

The unsigned comparison does not establish byte identity: eleven source/format-bound explanation policies account for the 770 differences. Signed-byte determinism is not claimed. Native installs include compiled x64/i386 refusal controls, which were not executed; their presence does not establish Intel host execution. The companion is inspected and compiled only.

## Verification Results

| Acceptance Criterion | Result |
|---|---|
| Clean ARM64 Wine host build and minimal PE/API fixtures under documented normal permissions | OK within #4: three fresh build roles, actual per-executable development grants and all required same-signed native bootstrap/API cases passed. Reference and companion were compile/inspect only; ordinary-user permission is unqualified. |
| Recorded source, patches and commands without silent Intel host fallback | OK within #4: pinned input/tool/configuration identities, attributed series, exact build commands, strict complete native comparison and required ARM64/nontranslated process/image observations passed. These are bounded fixture snapshots, not a full game/runtime load timeline. |
| Targeted thread entry, nested callbacks, error exits and exception-context capture | OK within #4: original API/ABI/thread/memory/exception/window fixtures and source-bound routing/ownership regressions passed. General translated contexts/unwind and a new corrected system-thread native fatal-route test remain unperformed. |

### Final integrated evidence and identity

The actual host was Apple M4 Pro/ARM64, macOS 26.5.2 (25F84), Xcode 26.6 (17F113), SDK 26.5, LLVM-MinGW 20260908/LLVM 23.1.1 and Bison 3.8.2. Wine commit was `4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf`, tree `10b47b2965a7b3e1e9694ec506a3d13525211892`, archive SHA-256 `f5d89a11b33ca5db93576d8e53fd3bbe86d68f18a3d711ef5e21ed994bf8c662`. Source/tool preparation and compile/inspect/runtime roles are separately recorded in [Stage 6](../working/task_m1_4_stage6.md).

Final reconstruction used fresh `reproduction3` directories, 26.100 GiB available at the unchanged 26 GiB preflight, stable relative configure invocation and four bounded jobs per serial build. The reused compiler cache was reverified with 34 checks/58 commands; it was not independently rebuilt. No prior compiled Wine payload was an input. The standalone native page-W^X prerequisite was separately rebuilt, signed and rerun: two positive lifecycle variants and four original protection controls. It does not substitute for integrated Wine or the unperformed native fatal-route test.

The candidate alone used verified device-bound development authorization, Hardened Runtime and library validation, with 38 signed native images and 4 KiB loader signature pages. Restricted/public JIT claims apply to the actual loader, not ordinary helpers. Required observed native processes/images were ARM64/nontranslated; finite observations are not a claim about every future descendant or library.

All three bootstrap controls and the four cumulative cases passed on that same signed candidate. The ABI fixture retained 64 round trips, 32 nested callbacks, 16 error returns, 128 gateway/native/TEB checks and 256 host-mode checks. The memory fixture retained eight 64 KiB dynamic slots in the existing single owner; this is address-space policy, not measured resident memory or performance. Window cleanup and sentinels passed, with zero observed late callbacks through the final recorded barrier.

The separately assessed display sidecar had 443 pre/periodic/post awake/active/online samples, maximum observed gap 5.021 seconds; its finite temporary assertion was reaped. It is not continuous, asleep-session or headless qualification, and the public exporter does not independently validate that private sidecar.

| Verification | Actual Result | Retained Evidence |
|---|---|---|
| Serial final reconstruction and independent full replay | All fourteen operations passed; verifier exited zero | [Stage 6 commands/receipts](../working/task_m1_4_stage6.md#commands-and-result-binding); terminal SHA-256 `fb39c578ae50030703b10ca718af63e76786c42bc02ffc231d4e0b4f40fdffff` |
| Sanitized public export | Canonical, allowlisted 109,425-byte record; fourteen passing operation bindings | [Stage 6 observations](../working/task_m1_4_stage6_observations.json); SHA-256 `4502be49cc33fdac6c20d22c832a719c51e7378176d50aab211f14948023ab77` |
| Final repository regression | 881 tests passed, no skips, 38.481 seconds | Stage 6 regression log SHA-256 `c001e9331e57aaa898f5b68603f5f386c58b45ce82f33b1fd3f8c75b1be29610` |
| Stage 6 governance and whitespace | 22 documents/172 local targets, routing/source inventory and staged whitespace passed | [Stage 6 report](../working/task_m1_4_stage6.md); governance log SHA-256 `dd95a5814f622da87a395e1033ff37ba69ec9d16d3bb2156e056d3dcaaf658ec` |
| Final-report identity check | Current 54 producer files, four configurations, all fourteen receipt digests, start/terminal/export and regression/governance log identities passed | Private `final-report-binding-review.json`; check only, no repeated native execution or full replay |
| Final-report documentation verification | Governance passed: 22 documents/172 targets; 35 governance-checker tests passed; all 23 local report links/anchors and six stage commit/report pairs checked; whitespace passed | Actual final-report-phase checks on October 1, 2026; no runtime code changed |

The final-report phase changes reporting and board state only. It reuses the completed integrated verification after checking current producer/configuration identities; it does not repeat three builds, the full replay or the 881-test suite solely to publish unchanged runtime code. Documentation governance, governance-checker tests, local links and whitespace were checked again for this report before publication. Actual GitHub checks are recorded in the PR after publication rather than predicted here.

### Stage Verification Results

| Stage | Committed Report | Commit | Historical Verification |
|---|---|---|---|
| 1 — Inputs and toolchain | [Stage 1](../working/task_m1_4_stage1.md) | [8cd7702](https://github.com/postmelee/pear/commit/8cd77027c481e192999cd25df32fd889343398bc) | 34 tool checks/58 commands and 95 repository tests; no Wine/PE execution |
| 2 — Authorized bootstrap | [Stage 2](../working/task_m1_4_stage2.md) | [5c948a6](https://github.com/postmelee/pear/commit/5c948a6f567a978906458b290da6b5b820d20414) | Native/companion builds, actual signature/page checks, three bootstrap controls and 236 tests; before PE entry |
| 3 — PE/API and nested x18 transitions | [Stage 3](../working/task_m1_4_stage3.md) | [96bcf55](https://github.com/postmelee/pear/commit/96bcf55e31f2778330b08354309482d4f4983f35) | API/child execution, nested callbacks/errors, relocation/import ownership; 17 patches and 558 tests |
| 4 — Threads, memory and exceptions | [Stage 4](../working/task_m1_4_stage4.md) | [0f59a42](https://github.com/postmelee/pear/commit/0f59a42ccc7264068fed40c020dbd40ae7b81c4c) | Workers, finite signal/context/protection checks and mutable ARM64 code; 19 patches and 688 tests |
| 5 — Mac-driver boundary | [Stage 5](../working/task_m1_4_stage5.md) | [f2c0d46](https://github.com/postmelee/pear/commit/f2c0d4667f904591fbd5d1260e6bfd26916f047a) | Twenty Win32/Cocoa lifetimes, native ownership handoff; 21 patches and 779 tests |
| 6 — Fresh reproduction and handoff | [Stage 6](../working/task_m1_4_stage6.md) | [496c7f5](https://github.com/postmelee/pear/commit/496c7f5367a935ae2f4abb3b7477d37bc13bea9b) | Three fresh builds, strict unsigned comparison, same-signed suites and startup ownership correction; 23 patches and 881 tests |

These stage results belong to their dated artifacts. Stage 6's independently checked final candidate, rather than a sum of historical passes, is the current #4 acceptance evidence.

## Residual Risks and Follow-up Work

### Residual Risks

- FEX/x64 dispatch, CHPE/ARM64EC execution, D3D/DXMT/Metal pairing, Steam, Megabonk, ordinary-user installation/recovery and distribution are unqualified. #1's combined source decision remains blocked; #2 retains its original finite scope. No runtime lock or M1 closure follows.
- This was same-host fresh-directory Wine reconstruction with a reverified compiler cache, not clean-machine, independent compiler, second-Mac or native-Windows-reference qualification. The configured upstream Wine conformance suite and selected optional network/authentication/audio/codec/Vulkan/external-font features were disabled; EGL was unavailable. The 881 tests are Pear repository regressions, not the full Wine suite.
- The newly proposed deliberate native-fault test was blocked before execution by automatic safety review for possible cybersecurity risk and was not retried. Source-bound routing checks and production object compilation support the no-TEB guard; its corrected native fatal termination remains unperformed. The earlier approved protection controls are distinct.
- Finite process/image/callback/exit observations do not qualify arbitrary descendants, full load timelines, general foreign callbacks/unwind, simultaneous JIT mutation or later display state. No performance, power or thermal advantage was measured.
- Startup-request ownership was corrected without changing the existing five-second wait or publication before `NSApp.run`. An empty CF envelope/source may remain held by an active callback frame while the application loop does not return. Finite success does not prove general startup reliability or isolate every historical AppKit fault.
- Failed attempts were retained: initial final reconstruction failed window deallocation; a later normal run exited before required window results; diagnostic-only successes remained ineligible. `reproduction2` stopped before configure because a private wrapper passed umask 077; the fresh final run restored only its coordinator child to 022 without weakening source-mode checks. Default 16 KiB AppKit controls also trapped, so no 4 KiB-only framework cause is claimed.
- Development signing is not a release/distribution grant. Shipped source/license obligations, ordinary-user authorization and notarization remain separate requirements. Private evidence remains retained outside Git; public hashes do not make that private material a release artifact.

### Follow-up Candidates

No new Issue is proposed; necessary work is already tracked.

| Existing Owner | Reusable #4 Result | Required Follow-up |
|---|---|---|
| [#5](https://github.com/postmelee/pear/issues/5) / [#6](https://github.com/postmelee/pear/issues/6) | Source-matched module/Unix-call boundaries, x18 helpers, finite thread/exception and executable-memory fixtures | Darwin FEX services, actual x64 dispatch, translated contexts/unwind and coordinated memory lifetime; native CHPE/non-ARM64 publication remains refused, selected xtajit64 emulation unimplemented, companion ARM64X does not fit native arena limits |
| [#7](https://github.com/postmelee/pear/issues/7) / [#8](https://github.com/postmelee/pear/issues/8) | Twenty native Win32/Cocoa lifetimes and [typed driver handoff](../../docs/development/wine-host.md#native-driver-interface-handoff-to-7) | Resolve Wine client-view offset 16 versus pinned DXMT copied offset 24, exports/table and borrowed/no-view/null/error/resize/detach/destroy behavior on an actual renderer pair |
| [#10](https://github.com/postmelee/pear/issues/10) | Owned process/image registration, byte binding, exits, cleanup and sentinels | Complete runtime load timeline, future callbacks and arbitrary descendant coverage |
| [#13](https://github.com/postmelee/pear/issues/13) | Reconstructable build/patch records, notices and actual per-executable development signatures | Shipped source/license compliance, ordinary-user authorization, packaging/notarization, installation/recovery and release qualification |

Fixture Unix-call indexes are not a stable public translator interface. Matching Cocoa BOOL spelling alone is not a demonstrated ABI defect. The downstream tasks require their own approvals and qualification.

## Approval Request to Task Requester

On October 1, 2026, the requester explicitly continued after the Stage 6 approval question that included final-report writing and PR publication. That authorization covers this report and an Open PR from `codex/publish-task4` to `master`; no repeated publication approval is needed. Preserve the six stage commits and all prior failed evidence.

Review and merge approval will be requested against the concrete published PR. Merge, Issue closure, branch/worktree cleanup and implementation of another Issue are not authorized by this report. The daily board marks implementation/report completion; GitHub Issue #4 remains open until approved closure or confirmed PR merge.
