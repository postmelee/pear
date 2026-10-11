# Task #47 cloud handoff

Scope: approved Stage 2 preparation, not Stage 2 completion or public release.
Use the existing [implementation plan](../plans/task_m3_47_impl.md) and
[Stage 1 report](task_m3_47_stage1.md). The requester approved cloud development
and hosted macOS candidate building while retaining every local qualification
requirement. M3 remains a Rosetta Preview; this work does not change M1 or #11.

## Source and ownership

Repository: https://github.com/postmelee/pear (private at handoff).
Continue from the recorded checkpoint on `codex/publish-task47`, not the older
`master` Preview source. Resolve and record its exact commit before changes.
Use a separate cloud workspace; do not edit or launch the local working tree.
The checkpoint is incomplete Stage 2 work, not a completed-stage report or PR.
Do not merge moving #11/#12 source, create duplicate Issues or change master.

No private runtime output, Steam account/prefix, game, save, Keychain or raw
local diagnostics is included. Paths in observation records describe retained
local evidence; those bytes are unavailable in cloud unless explicitly supplied.
Never infer that a local verification command ran in cloud. Keep the existing
signed runtime and local supervisor readiness untouched.

## Codex Cloud environment

Select the existing Pear GitHub repository and this checkpoint branch when
preparing a Codex Cloud environment. Repository skills are under mydocs/skills;
local personal skills and local Apple credentials are not assumed available.
No secrets or Wine runtime are needed for the first environment verification.
Python 3.12+, Node.js 22+ and Git are sufficient for portable checks. Permit
GitHub access only as needed for source and CI; runner-side dependency downloads
are handled by Actions, not a request to upload local caches.

Run in the repository root:

```sh
python3 -B preview/ci_checks.py
python3 -B tools/check_governance.py
python3 -B tools/compatibility.py --check
python3 -B -m unittest discover -s tests/docs -p 'test_*.py' -v
node --test tests/docs/test_steam_search.cjs
git diff --check
```

These are synthetic, source and website checks. preview/build.rs invokes Apple
native tools: do not claim a Linux cargo build qualifies the app. Native app
building is delegated to the candidate workflow on a GitHub-hosted macOS runner.
The cloud environment itself still needs actual creation/setup validation; a
committed handoff document is not evidence that it exists or was published.

## Hosted Mac candidate job

The workflow .github/workflows/preview-candidate.yml runs portable fixtures,
then uses macos-26 ARM64, Xcode 26.5 and Rust 1.94.1 to reuse preview/build.sh and
preview/package.py. Existing repository actions are pinned by commit. The source
must remain clean. The job records compiler/SDK/image and archive identities.
It runs on source pushes to codex/publish-task47 and can be manually dispatched
once available through GitHub's workflow registration rules.

The artifact contains only app/CLI ZIPs, checksums, a manifest, provenance and a
candidate notice. It expires after 14 days; download selected immutable outputs
before expiration if later review needs them. Per-job outputs are fresh and
hosted scratch is disposable. No runtime build, real Steam or game is launched.

**This first candidate is ad-hoc signed, not Developer ID signed or notarized.**
It is build evidence, not the installable candidate for normal-security user
acceptance. No signing secrets are referenced and contents permission is read-only.
There is no release upload or Pages deployment step. Do not bypass Gatekeeper.

## Remaining signing and local acceptance

Before hosted signing, obtain explicit authorization to provision the necessary
Developer ID private key and notarization credentials into a protected CI
signing environment. The existing local signing authorization and pear-notary
Keychain profile do not authorize/export cloud credentials. Keep secrets outside
chat, source, PR jobs and artifacts; review exact provisioning steps first.
Reuse immutable approved runtime bytes with verified hashes and matching sources;
do not rebuild/re-sign that runtime merely to move app builds to CI.

A later signed candidate must pass Apple acceptance, applicable stapling and
package-policy checks, then be downloaded and tested locally. Record exact
package/app/CLI/runtime/source identities. Require actual interrupted download
and GUI retry, post-reinstall GUI/Steam/game reuse and save preservation. Preserve
all other Stage 2 cases and explicit source-seam boundaries. CI success cannot
supply these observations. Final runtime URL wiring and actual hosted runtime
acquisition remain distinct from the existing pinned SteamSetup retry test.

After Stage 2 completion and explicit Stage 3 continuation, perform measured
20-minute active play, audio/input/save/relaunch and the recorded clean-user or
clean-OS delivery flow, including browser/Finder entry under normal protections.
A new bottle or hosted CI machine does not substitute for that user flow.
Publish only the same tested final package bytes after all required evidence,
source/license/privacy checks and final publication authorization. Any changed
candidate revalidates affected evidence; unaffected exact-input evidence is reused.

The local coordinator retains execution-slot ownership for real local GUI/game
runs. No cloud source edit or hosted build needs a local Wine/GPU slot. Do not
resume stopped automations or recreate Goals. Existing local preparation is
ready but is not authorization to launch it from cloud.


## First hosted execution

Source checkpoint: d9e222327efda07fe24a39c6d8841251c94d1ba3.
[Actions run 38163826676](https://github.com/postmelee/pear/actions/runs/38163826676)
passed. Ubuntu and macOS each passed 51 Python fixtures with zero skips; the Mac
passed 21 Rust tests, app/CLI build and candidate package checks. Downloaded
archive bytes matched the package manifest. Actual host: macOS 26.6.2 ARM64,
Xcode 26.5 (17F42), SDK 26.5, Swift 6.3.2 and Rust 1.94.1. This differs from the
local candidate toolchain and is a new unsigned-for-distribution candidate,
not inherited local game qualification. No runtime was fetched or executed.
