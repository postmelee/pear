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


### Hosted recovery fix and publication preparation receipt

Source e27e002e4745cd1dbd7ac1b7245ac154e589711a passed hosted run
[38167091034](https://github.com/postmelee/pear/actions/runs/38167091034):
58 Python tests on each Ubuntu/macOS job and 22 Rust tests, with zero skips or
ignored tests. App and CLI packaging succeeded; both downloaded archive sizes
and SHA-256 values match the package manifest. Signing correctly remained skipped.
These are ad hoc candidates, not Developer ID/notarized distribution evidence.
The explicit Session unlock changes app/CLI source identity. The old local frozen
readiness record describes only its old bytes; a newly signed candidate needs
fresh readiness and local execution/recovery qualification. No local GUI started.

Publication preparation scanned 2,100 historical blobs from the three remote refs
at the recorded snapshot (before e27e002), plus 49 Issues/PRs, two issue comments
and four Discussions. Selected credential patterns had no matches; this is not a
complete security/privacy review. Nineteen historical blobs contain personal
absolute paths. Current-ref, Actions log/artifact content and disclosure review
remain. master lacks the approved GPL license and Preview entry/release documents
that exist on this task branch. Align the public default-branch entry separately
without merging unfinished Stage 2 solely to unlock CI. The owner has asked about
public feasibility, not authorized visibility conversion. Keep secrets absent and
the approved signing SHA unset until effective reviewer protection is verified.


### Public-source review ready for owner decision (October 12)

The requester approved the preparation sequence. The exact-base public-entry
patch is retained privately at .build/task47/publication-audit/master-entry.patch.
Base master: 4340f2059ae187a0322fec564a700721e57a88f8. Pinned Preview guide
source: 4e1be9114fc76802e21b075e143cfc2f86c66c0a. Patch SHA-256:
4f697e6c290dc6eb01f06860e5a32a769d1f5e33c9f7740b2b1fb4820e6429d2.

Fourteen files provide GPL text/package metadata, short README, documentation
and contribution entry points, security/conduct/support/community policies and
Issue/Discussion forms. Existing approved community files are reused; their
Preview links pin the reviewed task source instead of importing unfinished code.
No workflow, runtime source or implementation change is included. master already
preserves the exact Madeira exception under tests/cpu/LICENSES; no duplicate is
added. Its SHA-256 matches the task copy. This is a proposed narrow integration,
not the final #47 PR, stage completion or permission to close #47.

Verification passed: exact-base cached patch application; pinned file targets;
31 governed documents and 284 local targets; 35 existing documentation tests;
five intake YAML parses; whitespace checks. GitHub-rendered intake and private
reporting still need verification after integration/visibility change. Full site
publication and runtime/game qualification remain separate.

Refreshed remote review covered three branch heads, 37 Actions runs (5,647,479
log bytes), 17 artifacts (646 members including nested app/CLI ZIPs), 49 Issues/PRs,
two issue comments, zero review comments and four Discussions. Selected credential
patterns produced no matches; no history paths ending in the reviewed executable,
archive, credential or save suffixes were found. GitHub body attachment URL scan
found none. Artifact entries contain the expected public Steam identities,
redistributable CPU fixtures/results and ad hoc Pear candidates. Review is bounded,
not a guarantee against every possible secret or a general license clearance.

Historical author names/email and personal absolute paths remain visible if
published. Actions development binaries are not player releases. Zero tags or
releases exist. Wiki is enabled in metadata but its authenticated Git endpoint
returns Repository not found; no readable Wiki contents were available. This
limitation is recorded rather than treating a failed read as an empty-content audit.

No visibility, master, secret or runtime-state change occurred. The exact signing
branch policy and zero environment secrets were read back. After final owner
approval, integrate only the reviewed public-entry change, recheck changed remote
inputs, then make the existing repository public. Verify required reviewer
postmelee, disable administrator bypass and preserve the exact branch rule before
provisioning credentials. A single owner must be able to approve their own run;
this is a manual approval gate, not independent peer review. Enable private
vulnerability reporting, verify intake availability and apply prepared Discussion
50/51 updates. Keep Pages and player downloads gated.

Private review receipts, the prepared tree/patch and after-public draft messages
remain retained for this decision. No raw log/archive downloads were retained,
and no binary was executed. Inspect the latest remote delta again after approval;
prior public-source snapshot hashes are not an unbounded future approval.


### Public source and CI credential registration completed (October 12)

The owner approved the exact public-source change and visibility conversion.
PR #54 merged as 3a15ddd2539ca5c0578834ff644548e58b7a6a39 after eight hosted
checks passed. The repository is public; #47 and Stage 2 remain in progress.
Private vulnerability reporting is enabled. Bug and Show and tell forms rendered
in the browser; the Wiki displayed its empty first-page creation state. Prepared
Discussion 50/51 updates now distinguish public source from a player release.
No Pages deployment or player release was performed.

The owner completed the local credential helper. Its non-secret receipt and
GitHub metadata confirm four expected environment secret names and the approved
public certificate fingerprint. Secret contents were not read back. Protection
was rechecked: required reviewer postmelee, exact codex/publish-task47 branch,
administrator bypass disabled. Single-owner self-review is permitted; this is
manual owner approval, not independent peer review. The original Keychain
identity and owner-exported encrypted certificate remain preserved.

Set PEAR_SIGNING_APPROVED_SHA to e27e002e4745cd1dbd7ac1b7245ac154e589711a and
rerun existing hosted run 38167091034, attempt 2, without debug logging. The
preview/, manager/ and signing workflow trees match current task HEAD 39c5001.
Rerunning preserves the reviewed original commit/ref and avoids changing source
or merging unfinished Stage 2 merely to trigger signing. The protected sign job
must wait for the owner's GitHub approval; do not approve it through automation.
Remove the approved-SHA variable after the selected run finishes. Credential
registration alone does not establish successful import/signing/notarization.

Reuse the existing hosted storage plan and workflow-owned fresh roots: builds
admit at least 6 GiB free; credentials are transient in the job-owned keychain;
only allowlisted candidate packages and sanitized receipts are retained for 14
days. No local substantial build, runtime copy, Steam or game execution occurs.
Local receipts are small task evidence; retain signed candidate bytes through
local qualification and preserve all earlier private state/recovery dependencies.
A fresh signed app needs new readiness and a non-conflicting GUI validation slot.

Attempt 2 passed both portable fixtures and the hosted macOS app/CLI build.
GitHub now reports Approved Developer ID candidate as waiting, with pending
environment pear-preview-signing and owner approval available. No signing job
has started; the owner was directed to Review deployments on the run page.


### Hosted attempt 2 failure and repair

Owner approved the protected job. Credential import and notary credential
validation passed, but codesign reported no identity found before submitting
anything to Apple notarization. Always-cleanup passed; no signed artifact uploaded.
Removed PEAR_SIGNING_APPROVED_SHA after the failed run. Add the missing temporary
user keychain search-list setup from GitHub's official hosted certificate recipe
and require the exact valid signing identity before signing. No local identity,
private export, app runtime code or entitlements changed. Portable tests: 59
passed, zero skipped; actionlint, governance and whitespace passed. The repair
requires another hosted run with owner approval before claiming success.


### Hosted signed candidate accepted and locally assessed (October 12)

Owner-approved run [38171422915](https://github.com/postmelee/pear/actions/runs/38171422915)
passed on exact source 0f712b93bbd239a1defd959da4dbf1cd0ad9a7a1. The corrected
keychain search-list setup resolved the earlier identity lookup failure. All
three jobs passed: 59 Python fixtures per test job and 22 Rust tests per Mac
build, zero skips/ignored. App and CLI notarization both returned Accepted:
12fff2ca-f4f3-4fa4-aa7d-4e3683e8c2f6 and
04de6001-cf22-4a9d-8b9c-170ae6bd232f, respectively. Job-owned credential cleanup
passed. Removed PEAR_SIGNING_APPROVED_SHA and read back its absence.

Downloaded only the signed artifact to .build/task47/stage2/ci-signed-0f712b9.
Both ZIP sizes/hashes match the manifest; source/provenance/notary receipts agree.
Archive paths/types were checked before separate app/CLI extraction. This Mac
passed deep strict team-bound app signature, staple validation, Gatekeeper,
distribution assessment, CLI notarization and help. The CLI matches the app's
embedded CLI. The app package allowlist excludes runtime/private payloads.
No quarantine/security attribute was removed and no Steam/game/GUI was started.
This is local package assessment, not clean-user or game qualification.

Reuse the existing Stage 2 supervisor with a new immutable candidate inventory,
16 exact inputs and fresh output root final-gui-ci-0f712b9. Readiness SHA-256:
debbf025dde9f319ef596adf4305f7828210618feb3c80faa972612437f7f049.
Readiness is at .build/task47/stage2/supervisor-preparation-ci-0f712b9/ready.json.
Requested a conflict-free fresh coordinator grant for actual download interruption
and GUI retry, then post-reinstall Steam/game launch. The old app/runtime/private
state and old readiness remain preserved. Host free space was about 13 GiB;
small candidate download/extraction stayed within 100 MiB. Exact logical,
stat-allocated and observed free bytes are in the observations record; no cleanup
or free-space attribution is claimed. Retain these packages and receipts through
local qualification. The inherited 8 GiB entry/6 GiB output GUI budget still applies.

Stage 2 remains in progress. Measured gameplay/clean-user qualification is Stage 3;
public runtime URL, final DMG and player release remain separate pending gates.
