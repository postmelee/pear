# Task #62 — Sparkle app updates

GitHub Issue: [#62](https://github.com/postmelee/pear/issues/62) · Milestone: M3

## Work Summary
Three implementation/verification stages, with Stage 3 admission/recovery/delivery
substages. Pear now checks for a signed app update before opening Steam, offers
Update and launch / Later, and continues on bounded-check failure. The requester
approved implementation, accepted the local UI, approved protected signing and
approved the final local website before public deployment.

## Changed Files and Impact Area
| Area | Files / outcome |
|---|---|
| Launch/update | preview/Launcher.swift, SparkleUpdate.swift, UpdateLaunchPolicy.swift, UpdateEnvironment.swift; bounded launch gate, active-session deferral and one-use relaunch receipt |
| Release notes | UpdateReleaseNotes.swift; restricted nonpersistent WebKit, version display and fallback |
| Input/signing | sparkle_input.py, sign_sparkle.py, configure_update.py, update_baseline.py, packaging and protected CI |
| Delivery | preview/updates, existing catalog renderer/workflow, README and player/release guides |

## Document Location Verification
Approved plan destinations match actual changes: official guides in docs/, website
in existing tools/catalog and compatibility.py, release feed in preview/updates,
plans/reports in mydocs/. No product guidance was added to mydocs/manual.

## Quantitative Before/After Comparison
| Criterion | Before | After |
|---|---|---|
| App update path | Manual installation | Signed Sparkle feed/archive, explicit choice and relaunch |
| Launch check bound | No updater | Eight-second check deadline; one Steam launch gate |
| Qualified update pair | None | Real signed/notarized build 6 -> 7; final stable-feed build 8 admitted |
| Portable candidate fixtures | Prior scope | 74 passing, zero skips in protected candidate CI |

## Verification Results
| Acceptance criterion | Evidence / result |
|---|---|
| Actual replacement | Signed build 6 -> 7 installed/relaunched without an external launch command; 123 target entries matched |
| Existing data | All 11 checked save files and semantic history/consent/shared mappings retained; requester confirmed login/library |
| Decline/active session/no update | Later retained 6; active Steam PID reused; current 7 opened Steam without an offer |
| Failure/cancel | Real unavailable/network-denied feed fallback, corrupt archive rejection and pre-install cancellation; no blanket process termination |
| Deadline/installer errors | Native watchdog and injected installer/auth/relaunch errors and restart-store denial passed; fixture scope retained |
| Security | Required signed feed/pre-extraction archive check, disabled Sparkle profiling, protected signing; public key only in source |
| Homebrew | Conservative Caskroom/alias checks defer in-app replacement; tests and public guidance; no live brew upgrade claimed |
| Final candidate | Build 8 at 51fbe6f2: app/CLI/DMG checksums, Developer ID, notary acceptance, macOS 15.7.9 startup and local Steam launch passed |
| Delivery preparation | Same GitHub/HTML note source, independently verified Ed25519 feed/archive, 1,630 exact source entries, 116 docs/catalog and 7 Worker tests passed |

### Stage Verification Results
- [Stage 1](../working/task_m3_62_stage1.md): upstream choice and policy.
- [Stage 2](../working/task_m3_62_stage2.md): integrated adapter, notes and local UI.
- [Stage 3.1](../working/task_m3_62_stage3.1.md): protected qualification pair.
- [Stage 3.2](../working/task_m3_62_stage3.2.md): actual replacement and corruption.
- [Stage 3.3](../working/task_m3_62_stage3.3.md): recovery and stable configuration.
- [Stage 3.4](../working/task_m3_62_stage3.4.md): final signed build 8 admission.
- [Stage 3.5](../working/task_m3_62_stage3.5.md): feed/docs/source delivery preparation.

## Retention Handoff
| Artifact | State / owner | Release condition |
|---|---|---|
| Exact signed builds 6/7/8 and manifests | Retained, .build/task62; delivery/recovery | Public download verification and final handoff |
| Private save/history/original-app recovery | Ignored/local; requester | Preserve until recovery need explicitly ends; never release |
| Keychain Ed25519 key | Private, updater publisher | Retain across future releases |
| Runtime inputs | Unchanged/shared user installation | Not disposable task output |
| Qualification release | Public prerelease, normal feed restored | Retire separately after delivery; no broken test feed remains |
| Local preview/release/source staging | Retained, final delivery | Stop server/release disposable copies after handoff |

Worktree contains ignored evidence and is retained through delivery. No blanket
cleanup or inferred storage recovery. Source/notary receipts remain bound to exact
inputs; unavailable continuous source-to-human-response latency is not invented.

## Residual Risks and Follow-up Work
Stable public asset/feed/Homebrew verification belongs to the final delivery step
and is not claimed complete by this pre-publication report. Legacy previews need
manual bootstrap. macOS 15 CI is startup, not Steam UI/gameplay qualification.
Network-denied test qualifies updater recovery and Steam handoff only. Injected
installer failures do not establish all filesystem/power-loss recovery. No new
runtime gameplay/performance or cross-hardware claim.

## Approval Request to Task Requester
The requester already authorized implementation, verification and release, and
approved the local public page. Proceed with the authorized integration and
publication; preserve GitHub protections and record actual public outcomes.
