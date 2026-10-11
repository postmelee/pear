# Task #47 — Stage 2 evidence review

Date: October 12, 2026. Status: interim review; Stage 2 remains in progress.

This review implements the request to reconcile existing results without
interfering with other host experiments. It does not start Stage 3, waive required
checks or declare a public download ready. No Wine, Steam, game, build, signing or
notarization process was started for this review.

## Candidate and evidence boundaries

The current signed candidate is source
`0f712b93bbd239a1defd959da4dbf1cd0ad9a7a1`, from
[CI run 38171422915](https://github.com/postmelee/pear/actions/runs/38171422915).
The run and all three jobs were rechecked as successful. Its recorded fixture
results are 22 Rust and 59 Python tests, with no skipped/ignored cases. The app
and CLI have accepted notarizations and recorded local policy checks. These are
candidate checks, not public browser-delivery qualification.

The current `lib.rs`, `recovery_tests.rs`, `runtime_pin.rs`, `main.rs` and
`Launcher.swift` were compared byte-for-byte with that CI revision and match.
Historical 21-test Rust results have a different `lib.rs` hash; they remain
historical evidence. Between checkpoint `d9e2223` and the CI revision, the relevant
library change is explicit session-lock release in `Drop` plus its regression
test (24 added lines). The signed CI's 22 tests supersede the old fixture count
for this candidate; old host runs are not relabeled as runs of the new app.

The later supervisor-only fix `b1ac5c6` tolerates disappearing updater child files
without suppressing missing-root or access failures. Its recorded 64 Python
checks include 22 supervisor cases. It changes the observation harness, not the
signed app or runtime. The reinstall interval used this fixed supervisor.

Detailed identities, hashes, private receipt locations and chronological records
are in [Stage 2 observations](task_m3_47_stage2_observations.json). Early
“not yet executed” entries describe their original checkpoints; the later
`ci_reinstall_observation` is the current execution result.

## Reconciled matrix

| Case | Established result | Boundary / remaining qualification |
| --- | --- | --- |
| Download interruption and GUI retry | Pinned Steam installer partial download interrupted; cache cleaned; GUI retry installed Steam. After full network recovery, the owner selected Open Steam again and normal login pixels appeared. | Initial Steam update ended with `Failed to load steamui.dll`. Preserve that failure and manual recovery; the owner's network interruption is associated evidence, not a proven root cause. No hosted runtime-download or uninterrupted first-attempt claim. |
| Installation interruption/reuse | Frozen signed Stage 1 CLI and source fixtures verified interrupted extraction, retry/reuse and no partial activation. | Historical CLI scope; not every current GUI failure path. |
| Invalid/missing inputs | Source fixtures reject malformed, wrong-hash, missing and unsafe-link inputs and preserve unrelated state. | Synthetic validation, not a game test. Current candidate fixtures passed in CI. |
| Insufficient space | Real `statvfs` admission rejects an impossible requirement without changing private state. | No physically full filesystem, quota exhaustion or mid-write ENOSPC observation. |
| Failed replacement | Same-runtime transaction fixtures preserve previous runtime and private sentinel after failed replacement. | No different-runtime migration or general updater rollback qualification. |
| Repeat launch | Notarized app-v4 opened Steam/game twice; current CI candidate also opened the Steam library and game after reinstall. | Same host and retained account/runtime; no independent clean installation claim. |
| Local save restoration | App-v4 restored eight baseline files with Cloud off; owner confirmed sniper enabled state and normal input after changing it to disabled. Changed state retained; Cloud setting restored. | Actual historical same-host restoration. Latest candidate preserved progression after reinstall; that is not a second restore test. Cloud synchronization/cross-device recovery not qualified. |
| App removal/reinstall | Exact CI candidate app copy removed/reinstalled; signatures/runtime checks passed; owner confirmed library, game menu/input/prior progression and normal game exit. | Whole-session normal shutdown did not pass: an orphan helper required scoped termination. Game/reinstall success remains valid within its recorded scope. |

The first GUI observer's disappearing-file error remains a failed interval; the
subsequent supervisor fix does not retroactively pass it. A post-close
accessibility inspection unexpectedly relaunched the earlier trial app and is
excluded from recovery evidence. The reinstall interval avoided that inspection.

## Steam helper exit: release decision

The reinstall harness requested Steam shutdown with `steam.exe -shutdown`.
Steam main, the game and Pear exited, but one owned `steamwebhelper` and Wine
services remained beyond one minute. A single process snapshot showed 86.1%
CPU for the helper and 54.1% for wineserver. This is evidence of a potentially
user-visible resource problem, not a sustained performance measurement.

One coordinator-authorized, identity/prefix/no-live-game-checked SIGTERM to that
helper released the remaining services. No game was forcibly terminated. This
was operator cleanup, not a supported ordinary-user recovery feature. The guard
used `abort-release`; its failed status must not be represented as a passing
normal shutdown test merely because resources were eventually returned.

Closing Pear while Steam and games remain open is intentional: the launcher
hands the session to Steam and explicitly tells users they may close Pear.
Automatically killing Wine when Pear closes would contradict that behavior and
could interrupt a game. It is not the proposed fix.

The evidence does **not** yet establish that Steam's normal UI Exit leaves the
same helper, or that the Wine runtime requires an upstream patch. The observed
failure is in the harness-requested shutdown path. Its cause and frequency are
unknown; older successful exits do not prove this candidate's path is reliable.

**Before public ordinary-user distribution, resolve the exit-risk disposition.**
That means validating normal user exit/reopen and providing a safe usable recovery
if the problem also occurs there. It does not automatically require rewriting
Wine, replacing the runtime, or rerunning all passed tests. A Terminal kill recipe
or a disclaimer alone is insufficient to close a reproduced normal-user exit
failure under the existing release criteria. Bounded developer testing and
non-conflicting documentation work can continue.

### Smallest next host check

At the next available coordinated host interval, keep the exact signed candidate,
runtime and preserved state. With no active game, use Steam's normal UI Exit,
then inspect owned process lifetimes and prefix handles without reopening a quit
app through an accessibility query. Reopen through Pear and confirm the library
and preserved state. Record the observation window and any remaining CPU-active
helpers; one successful run does not establish a general frequency claim.

- If UI exit and reopening succeed but the harness path leaves a helper, record
  the distinction and correct or constrain the harness cleanup procedure. Close
  the interval through verified normal user exit; no product change follows solely
  from this failure.
- If normal UI exit also leaves active helpers, investigate the smallest scoped
  fix or a supported safe exit/recovery action. Preserve data and active games;
  no broad process killing. Obtain the applicable implementation/stage approval
  if the solution exceeds the existing approved scope, then retest affected paths.
- If results are inconclusive, retain the unresolved status rather than counting
  forced cleanup as normal exit.

The passed reinstall/game check need not be repeated wholesale solely for this
question. Any app/runtime change would require affected evidence to be
revalidated; candidate identity is part of every claim.

## Resource return and remaining work

The owner receipt verifies 49 tracked lifetimes plus the guard owner absent,
no owned handles, and independent lock acquisition/release. SHA-256:
`eb80d8aa8b08fd7b558cb9728f3e1f81746640ce8113795bcc6f5018714066c9`.
The coordinator independently retired the interval, with receipt SHA-256:
`fa12e66beace1a715658662ce1f73d38a6c6fbf49a56d45be5cce8ccde52df67`.
This proves resource return, not normal full-session exit.

Stage 2 remains open for the exit-risk disposition and formal completion review
against the approved plan. Actual disk exhaustion and general updater migration
remain unperformed and must not be silently promoted from narrower fixtures.
Measured 20-minute play, defined clean-environment reproduction and final
browser-delivered artifact qualification remain Stage 3/release work. Earlier
reported long play and audio success do not supply a measured-duration record.

This review changes internal records only. Preserve signed inputs, failure
receipts, private recovery archives and authenticated state under existing
retention conditions. No artifact deletion or storage-reclamation claim is made.
