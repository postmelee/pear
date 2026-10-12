# Task #47 Stage 2: Recoverable setup, relaunch and preserved state

GitHub Issue: [#47](https://github.com/postmelee/pear/issues/47)
Implementation plan: [task_m3_47_impl.md](../plans/task_m3_47_impl.md)
Stage: 2 — complete; Stage 3 awaiting explicit continuation.

## Stage Purpose

Verify recoverable setup, app/client/game relaunch and preservation of the
owner's installation and saves for the Rosetta Preview. This is not final public
delivery or Rosetta-free qualification. The requester's latest direction makes
Preview distribution the priority; no other chat was asked to start other work
while completing this focused check.

Context used: root instructions, the approved task/implementation plans and
Stage 1 report, tests rules, retention procedure, existing candidate/source and
CI receipts, the central stage-report template, and `task-stage-report` / `todo`
skills. Reuse decisions and document locations remain in the implementation
plan. No public product-document location changed during this closure.

## Artifacts

| File / group | Change summary |
| --- | --- |
| `preview/src/lib.rs`, `recovery_tests.rs` | Recovery seams/fixtures and explicit session-lock release with regression coverage |
| `preview/validation/stage2_supervisor.py`, its tests | Operator-only exact-input supervision, state isolation, bounded operations, disappearing updater-child tolerance and retained failure evidence |
| `.github/workflows/preview-candidate.yml`, candidate signing support | Portable/macOS candidate verification and protected owner-approved signing/notarization; no public release admission implied |
| [Observations](task_m3_47_stage2_observations.json) | Candidate-specific fixture, recovery, save, reinstall and normal UI-exit outcomes |
| [Interim review](task_m3_47_stage2_review.md) | Preserved failure analysis and smallest follow-up test rationale |
| Task plans and daily board | Stage completion, retained risks and next-stage prerequisites |

The separately prepared source-attribution branch is not silently included in
the frozen signed candidate. Its integration remains final-candidate work.

## Body Change Scope / Lossless Preservation

Recovery uses the existing shared Rust core and thin native launcher. Pear still
opens official Windows Steam and lets the user select games. Closing Pear leaves
Steam/games open intentionally. No broad process kill, Steam credential handling,
security bypass, game modification or general manager/updater was added.

Preserve historical failures and exact source/runtime identities. Authenticated
state, game files and baseline/changed-save archives remain private and outside
Git. Existing private state was reused in place, without a full runtime copy.
Only small app copies were used for reinstall and exit checks. No deletion of
required recovery evidence or space-reclamation claim accompanies this report.

## Verification Results

Host: Apple M4 Pro, 24 GB, macOS 26.5.2 (25F84). This uses Rosetta Wine 11.0 from
the pinned CodeWeavers 26.3 inputs and DXMT 0.80. It does not qualify the native
runtime tracked by other Issues.

Latest candidate source: `0f712b93bbd239a1defd959da4dbf1cd0ad9a7a1`.
[CI run 38171422915](https://github.com/postmelee/pear/actions/runs/38171422915)
and all three jobs were rechecked successful. Recorded exact-candidate results:
22 Rust and 59 Python tests, no skipped/ignored cases. App and CLI notarizations
were Accepted; local signatures, app staple/Gatekeeper/distribution and CLI
notarization checks passed. Runtime pin:
`bf660c1ddf0a40cd2c7e345343b32f6515bf34c1fe6566aae337302f221a4127`.

Evidence reuse: current launcher/core/test/pin source matches the signed CI
revision. Historical 21-test and app-v4 records keep their own source hashes.
Actual local save restoration and frozen Stage 1 CLI extraction trials were not
renamed as executions of the final CI candidate. CI covered the subsequent lock
release correction; actual CI-candidate reinstall and UI-exit checks cover the
changed launch/reopen path. Supervisor-only changes passed 64 Python checks
including 22 supervisor cases; they did not change signed app/runtime bytes.

| Case | Outcome and scope |
| --- | --- |
| S2-download | Passed bounded recovery: partial pinned Steam installer interruption, cache cleanup, GUI retry and verified complete bytes. Steam's later self-update first failed; after full network recovery, owner clicked Open Steam again and normal login pixels appeared. No hosted runtime-download claim. |
| S2-install | Passed exact-source and frozen signed CLI interrupted extraction/retry/reuse, with no partial activation and preserved existing state. |
| S2-invalid | Passed exact-source corrupt/missing/hash/link refusal and state-preservation cases, included in candidate CI fixtures. |
| S2-space | Passed approved installer seam: real `statvfs` admission with impossible requirement, no previous-state loss. No host volume filling or actual quota exhaustion. |
| S2-update | Passed failed same-runtime transaction/replacement preservation of previous runtime and private sentinel. This satisfies the implemented replacement path; no different-runtime migration/general updater claim. |
| S2-repeat | App-v4 repeated Steam/game launch passed; latest candidate library/game launch after reinstall passed. Latest candidate normal Steam UI exit passed twice with one preserved-login library reopen. |
| S2-save | Actual local restoration passed with Cloud temporarily off: sniper enabled state restored after owner changed it to disabled; input normal and changed state retained separately. Owner restored Cloud setting. |
| S2-removal | Exact signed app copy removal/reinstall, library/game/menu/input/progression and normal game exit passed. Follow-up normal Steam UI exit/reopen passed without forced cleanup. |

Focused operation: `task47-stage2-steam-ui-exit-ci-0f712b9-r1`. The owner
confirmed normal library, Steam-menu Exit and Pear close, then preserved login
and normal library after reopening, followed by a second normal Exit/close.
The guard passed and exited with code 0. An independent process/handle check
found all 69 tracked lifetimes and the guard owner absent, no owned handles, and
successfully acquired/released the shared lock. No kill signal or `-shutdown`
command was used in this follow-up. Receipt SHA-256:
`ee7fa7db0c42d48d47030051a6b555110007610db138f39b80c1d406c23c4155`.

Closure commands:

```sh
python3 -B tools/check_governance.py
git diff --check
```

Result: governance passed for 37 documents and 354 local targets; diff whitespace
checks passed. Report-relative links and observations JSON were also checked.
No build, game, signing or full recovery-suite replay was necessary for this
document-only closure. No private payload is included in staged files.

## Residual Risks

- The earlier automated `steam.exe -shutdown` left a CPU-active orphan helper;
  one scoped termination was needed then. This remains a failed harness shutdown
  observation. Normal UI Exit now passed on the same candidate, so an upstream
  runtime patch is not required solely by that earlier result. Future automated
  cleanup must not count a zero command exit as proof that all helpers exited.
- The earlier GUI observer interval failed on a disappearing updater file. The
  fix and subsequent successful interval do not rewrite the original failure.
- Initial `steamui.dll` failure recovered after network restoration and owner
  retry; root cause is not proven. No guarantee of first-attempt success on every
  network/client update is made.
- Two normal exits are bounded evidence, not a reliability-frequency claim.
- Cloud synchronization, actual full-disk failure, different-runtime migration,
  measured 20-minute gameplay and independent clean delivery are not passing
  claims in this stage. Approved source-seam cases remain explicitly scoped.

## Impact on Next Stage

Preserve the exact runtime/source kit and private recovery state. Select the
final candidate once: integrate prepared notices, set the real runtime download
address (currently empty), build/sign/notarize through approved CI, package DMG
and CLI plus matching source/checksums, and test the affected final delivery flow.
Do not distribute the current development app as a working fresh-install download.

Stage 3 retains measured gameplay, input/audio, save/exit/relaunch and a defined
second clean setup under normal protections. A new local macOS user may help
isolate user-level state but must not be described as a second physical Mac or
fresh machine. Revalidate only evidence affected by final candidate changes.
Publish catalog download links only when the actual approved assets exist.

## Approval Request

Stage 2 is complete within its declared recovery scope. Approve Stage 3 to
continue final candidate integration, packaging and ordinary-user qualification.
