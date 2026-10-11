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
The private environment was created, checked and published as recorded below.
Fresh-task restoration and subsequent implementation remain separate checks.

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
acceptance. The ordinary build jobs reference no signing secrets; contents
permission is read-only. The separately gated signing job is described below.
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


## Published cloud environment

On October 12 the browser showed **Published** for **Pear Preview · Issue 47**
with availability **Only me**, repository postmelee/pear and checkpoint
c8c7e25739f59c22c9fce5f66b90dcb84f3edd99 on codex/publish-task47. The start skill
pins that checkpoint, reads this handoff and preserves the Stage 2 boundaries.
No network secrets or environment variables were configured; the package-manager
network preset was retained. No signing key or Steam state was uploaded.

The setup instance reported Python 3.12.14 and Node 24.19.0; 51 Preview Python,
72 documentation Python and 6 Node tests passed with zero skips. Governance,
catalog and diff checks passed. Setup made no source changes or pushes and did
not rerun hosted CI. These are setup-instance results, not fresh-task restoration
or native/game qualification. Earlier master-based onboarding results are outside
this checkpoint's claim. Task-owned setup logs remain in the cloud workspace at
.build/task47/cloud-onboarding/check-1.log through check-6.log until setup review;
they are regenerable. No background service is required.

This subsequent local documentation receipt does not change the pinned cloud
source or the app/CLI candidate. Refresh the environment checkpoint only when a
later authorized source change requires it. Stage 2 remains incomplete: hosted
signing credential provisioning, candidate acceptance and the recorded actual
local GUI tests remain outstanding. No public repository/release change occurred.


## Prepared CI signing path (not provisioned or executed)

The optional `sign` job requires the repository to be postmelee/pear, branch
codex/publish-task47, event push or workflow_dispatch, and repository configuration
variable PEAR_SIGNING_APPROVED_SHA equal to that run's exact commit. An unset
variable refuses entry. PRs never enter signing. The environment name is
pear-preview-signing. The existing build jobs retain no signing credentials.

Before enabling, the owner must authorize sending the selected Developer ID
Application private key and a dedicated Apple app-specific password to GitHub
Actions for postmelee/pear. Local certificate permission is not that authorization.
No credentials are requested in chat. None were exported, read or uploaded while
preparing this job. Use only this environment's secrets, never repository-wide
secrets, Codex Cloud variables, committed files or pull-request workflows.

Provisioning after authorization:

1. Create pear-preview-signing with selected deployment branch
   codex/publish-task47 only. Enable required review by the owner if the account
   plan supports it; if unavailable, report that limitation before storing keys
   and obtain an explicit decision on the alternative. Do not silently replace
   protected approval with an unrestricted environment. Disable admin bypass if
   available. Confirm effective settings before importing credentials.
2. In Keychain Access, the owner exports only the authorized Developer ID
   Application identity and its private key as an encrypted .p12 file. Set a
   strong export password using the local UI. Keep its temporary location private
   and outside Git/cloud sync. Do not export an entire keychain or use a blank
   password. Obtain the certificate's SHA-1 fingerprint for exact selection.
3. Add four environment secrets through GitHub's secret-entry UI or stdin to
   `gh secret set --env pear-preview-signing`: PEAR_CERTIFICATE_BASE64 (Base64 of
   that encrypted .p12), PEAR_CERTIFICATE_PASSWORD, PEAR_NOTARY_APPLE_ID and
   PEAR_NOTARY_PASSWORD (a dedicated Apple app-specific password, not the account
   login password). Never paste values in chat, command literals or logs. The
   owner should perform credential-entry prompts directly. The local pear-notary
   profile is not extracted. Add environment variable PEAR_CERTIFICATE_SHA1 with
   the matching fingerprint. Team is pinned to XH6JHKYXV8.
4. Review the exact source commit and workflow, set repository variable
   PEAR_SIGNING_APPROVED_SHA to that full SHA, and push that reviewed commit to
   codex/publish-task47. This allows pre-merge validation without modifying master.
   A previously pushed commit is not automatically a new push event: use a later
   reviewed candidate checkpoint, or manual dispatch only when GitHub accepts
   workflow_dispatch registration. Official guidance requires its presence on
   the default branch; this is not permission to merge unfinished #47.
5. Review/approve the protected job. It rebuilds and checks source without secrets,
   imports credentials only afterward into its own temporary Keychain, signs a
   disposable app copy with Hardened Runtime/timestamps and no added exceptions,
   notarizes app and CLI separately, requires Accepted, staples and runs existing
   distribution/package checks. Only final archives and sanitized receipts upload.
   Notary submissions use Apple; no runtime, login, game or save is uploaded.
6. Remove PEAR_SIGNING_APPROVED_SHA after the selected run to avoid unintended
   re-signing on a rerun. On every outcome delete the job-owned keychain and .p12;
   GitHub also destroys the hosted runner. If cleanup fails, the job fails and
   does not upload a candidate. Remove the owner's temporary exported .p12 only
   after confirming provisioning and its retention decision. Never delete the
   original Keychain identity. Retain downloaded candidate hashes/receipts through
   local qualification. Revoke dedicated credentials when this CI path is retired.

The build owner trusts reviewed repository/workflow changes; environment secrets
are accessible to admitted jobs, so encryption at rest does not remove this trust
boundary. Store no credentials until effective deployment restrictions/review
protection and the owner approval above are confirmed. No hosted signing or actual
Apple acceptance is claimed by portable mocks.

Sources reviewed October 12:
- [GitHub certificate/keychain recipe](https://docs.github.com/en/actions/how-tos/deploy/deploy-to-third-party-platforms/sign-xcode-applications)
- [Manual workflow requirements](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)


### Protection provisioning outcome

The owner explicitly approved GitHub CI credential provisioning after protection
verification. GitHub rejected required_reviewers for the current private-repository
plan but left an empty environment behind. Follow-up hardening set custom branch
policies and verified exactly codex/publish-task47 with type branch. Environment
secrets total is zero; PEAR_SIGNING_APPROVED_SHA is unset. No credential has been
exported, entered or uploaded and no signing job has been admitted.

The owner did not select the proposed weaker alternative and instead asked about
making the repository public. GitHub documentation confirms required reviewers
are available on public repositories on Free/Pro/Team. Keep credential provisioning
on hold until the public-conversion decision and actual reviewer protection are
resolved. Asking about public feasibility is not final visibility authorization.
Repository publication remains separate from app release and all game/recovery gates.

Portable preparation passed 58 tests with zero skips, actionlint and governance.
This validates synthetic boundaries, not real Keychain import, notary acceptance
or hosted cleanup. The existing runtime and local supervisor inputs are unchanged.
