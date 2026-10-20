# Task #62 Stage 3.4 — Stable-feed signed candidate admission

GitHub Issue: [#62](https://github.com/postmelee/pear/issues/62)
Approved consolidated plan: [task_m3_62.md](../plans/task_m3_62.md)
Stage: 3.4 — exact build 8 package and startup verification.

## Stage Purpose
Admit the stable-feed candidate after protected signing approval. Context: root
and host rules, approved plan, Stages 3.2/3.3, task-stage-report procedure and
artifact retention guide. Routine continuation is already authorized.

## Artifacts
| Artifact | Outcome |
|---|---|
| [Signing run 39383912617](https://github.com/postmelee/pear/actions/runs/39383912617) | All required build, candidate macOS 15 and protected signing jobs passed |
| [Signed macOS 15 run 39385304875](https://github.com/postmelee/pear/actions/runs/39385304875) | Exact signed app/CLI security and startup checks passed |
| .build/task62/ci-39383912617 | Signed packages, manifests, notarization/provenance, local admission and execution receipts |
| mydocs/orders/20261020.md | Candidate admission reflected; publication remains pending |

## Body Change Scope / Lossless Preservation
Only task records changed. No production source, runtime, installed application,
public feed, release, Homebrew or homepage was modified. Candidate source is
51fbe6f2dea42c82691d803ef02ae1663c087dd9. Existing signed build 6 -> 7 update and
recovery evidence remains scoped to unchanged application source; build 8 has a
new Info.plist, signatures and packages, checked anew here. No new game test.

## Verification Results
The returned source identity and clean manifest matched the approved revision.
All three archive sizes and SHA-256 values matched. Apple accepted app, CLI and
DMG notarization. Local strict deep app signature/team check, stapled ticket and
Gatekeeper assessment passed; the embedded CLI's notarized requirement and the
DMG's signature/staple also passed.

| Package | Bytes | SHA-256 |
|---|---:|---|
| Pear-0.1.0-macos-arm64.zip | 8364949 | 8adeb255d6b51e6235394be3fcb509ea4a5f37f04aed9c8533df447c436ae991 |
| pear-preview-0.1.0-macos-arm64-cli.zip | 359468 | 94b70c2c3411b0d5a3c10d4816d8af17d86c7d982d94d27e0a4b8326f49729e6 |
| Pear-0.1.0-macos-arm64.dmg | 9652438 | 38239f3ce37de8021c918c548018fdd45c08b9efa72d817cf39bfb0fd83504fb |

The signed Info.plist has version 0.1.0/build 8, minimum macOS 15.0, the committed
Ed25519 public key, and https://postmelee.github.io/pear/updates/appcast.xml.
Signed feed and pre-extraction update validation are required. System profiling,
profile submission, automatic background checks and automatic installation are
false. Pear's explicit launch coordinator retains its own bounded check.

The separate signed verification ran on macOS 15.7.9 arm64. It checked exact
packages, code signatures, ticket/Gatekeeper, CLI version/help/setup-info and
isolated app process startup. This does not qualify Steam UI or games on macOS 15.
The source-matched candidate job retains unchanged runtime startup evidence.

Local macOS 26.5.2: no Pear/Steam/game processes existed before launch. The exact
extracted build 8 opened one primary Steam process and showed Steam window is
open. The requester confirmed existing login/library and normal Steam/Pear exit.
The stable feed currently returns HTTP 404; this execution qualifies unavailable-
feed fallback, not a successful check against the future published stable feed.
Eleven save files and normalized history/consent/shared mappings were unchanged.
No Pear, Steam, Steam web helper, wineserver or Megabonk processes remained.

Commands included:
```sh
codesign --verify --deep --strict '-R=anchor apple generic and certificate leaf[subject.OU] = "XH6JHKYXV8"' <app>
xcrun stapler validate <app-or-dmg>
spctl --assess --type execute <app>
codesign --verify --strict -R=notarized --check-notarization <embedded-cli>
```
Wall and monotonic boundaries are recorded before launch, at process observation
and after manual confirmation. Human response time is included in the final
observation; no exact startup latency or continuous source-to-input benchmark is
claimed. UI is the previously accepted implementation, with no redesign.

## Artifact Disposition
| Artifact/root | State | Owner/consumer | Identity / release condition |
|---|---|---|---|
| Build 8 packages and local app | Retained, verified | Final delivery | Hashes above; retain through publication and download verification |
| Signed builds 6/7 and qualification feed | Retained | #62/recovery | Prior reports; retire only after final handoff |
| Private saves/history/app recovery and diagnostics | Local, ignored | Requester/recovery | Preserve until final data handoff; never publish |
| Runtime and installed Pear | Unchanged | Existing user environment | No copy or rebuild performed |

Signed archives total 18,376,855 logical bytes. Filesystem observation before
extraction showed approximately 13 GiB available. Allocated output size and net
free-space change were not measured; no storage recovery is claimed.

## Residual Risks
- Stable appcast publication and exact release-asset binding remain pending.
- Final signed reporting end-to-end coverage must retain #63's consent and review
  evidence; this startup did not generate or transmit a new game report.
- Legacy apps without Sparkle need one manual installation. Prior injected error
  tests do not qualify every filesystem/power-loss failure.

## Impact on Next Stage
Use these immutable build 8 packages for final delivery. Prepare matching release
notes/appcast, final user documentation, Homebrew and download links; verify the
published signed feed and actual downloaded bytes. Preserve local review gates.

## Approval Request
Existing implementation and release authorization remains applicable. No additional
signing approval or broad continuation approval is requested for this admission.
