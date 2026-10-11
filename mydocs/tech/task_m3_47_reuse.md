# Task #47 Reuse Investigation: Rosetta preview entry point

Date: October 10, 2026 (Asia/Seoul)
Status: Stage 1 in progress; no game or distribution qualification.
Plan: [task plan](../plans/task_m3_47.md), [implementation plan](../plans/task_m3_47_impl.md).
Observed inputs: [Stage 1 observations](../working/task_m3_47_stage1_observations.json).

## Actual GUI Baseline

Whisky app-v3.7.0 DMG matched the published SHA-256. DMG verification and deep
strict app signature verification passed; Gatekeeper accepted Notarized Developer
ID, team Z7JS58F8U3. The unmodified app was installed at its previously absent
standard path. No existing fork runtime or active Wine process was found at the
initial check. This does not establish a clean second machine or browser delivery.

The first-run GUI reported Rosetta installed; optional usage sharing stayed off.
It downloaded/installed Libraries 3.1.1. All 4,787 regular archive files matched
the resulting installed runtime byte-for-byte. Archive regular bytes total
866,066,635; symlink inventory remains separate. The live version feed matched
3.1.1/DXMT 0.80 at this observation; it is still mutable.

A new task-owned Windows 10 bottle uses MSync and explicit DXMT. No existing
experimental prefix, credentials or saves were imported. The official Steam
installer hash matched 7d3654531c32d941b8cae81c4137fc542172bfa9635f169cb392f245a0a12bcb.
Whisky started its PE32 installer process. The Wine UI did not appear in the
computer-use app inventory, so installer completion and login were not observed.
Do not classify the automation limitation as proof that the installer failed.

## Exact Source and Reuse

Release tag app-v3.7.0 resolves to
`305da2143bf6f73ac5b261303c7e7e957c23a227`, distinct from the previously inspected
main pin. Source files and hashes are recorded in the observation artifact.

- `DistributionConfig` uses a mutable remote version plist.
- `WhiskyWineDownloadView` resumes downloads, verifies an advertised digest,
  but skips digest verification when metadata has no hash.
- `WhiskyWineInstaller.install` removes the old Libraries directory before
  extracting the replacement. It does not implement atomic retained rollback.
- `BottleOperations` supplies existing export/duplicate/move operations. Their
  source availability does not establish safe live-game backup/restore.
- `SteamLauncher.launch` delegates `-applaunch <AppID>` to the actual Windows
  Steam client. This is a reusable normal-launch design, not observed game success.
- Examined Whisky source retains GPL-3.0-or-later headers; the actual DXMT 0.80
  archive carries its MIT notice. Review each other selected component separately.
  No source import or whole-bundle licensing conclusion has been made.

## Requester Question: One Command and QR

During Stage 1 the requester asked whether Whisky GUI is necessary and whether a
single command, potentially distributed through npx, could handle preparation,
QR sign-in and Megabonk play. This is an entry-point comparison within the
reuse-first task, not authorization for a new Steam authentication implementation.
The requester subsequently approved the small shared tool; do not require manual setup
merely because the current experiment used a GUI.

Read-only inspection of the original private `analysis/scripts/acquire.py` confirms
it invokes existing DepotDownloader with `-qr` to obtain owned content and verify
manifests/files. It explicitly says it does not execute game files. The separate
`run_wine_experiment.py` starts an official Steam client and launches the game
executable with `steam_appid.txt`. That history does not prove a single fresh QR
session supplies both acquisition and normal runtime Steamworks.

#11's current reuse notes describe an existing QR-result adapter and genuine
client integration, with synthetic checks but real account/normal-launch gates
still pending in the inspected record. Do not import its private adapter or make
its Rosetta-free runtime a preview prerequisite. No cross-chat message was sent.

| Candidate | What can be reused | Unresolved behavior |
|---|---|---|
| One entry command with ordinary Windows Steam | Pinned Wine/DXMT, isolated prefix/setup, Steam's own login and normal launch | Automatic install orchestration, owner-visible QR login, session persistence and actual normal game launch |
| Terminal QR through DepotDownloader plus genuine runtime client | Existing owned-content QR/download tools | Valid runtime credential handoff, client-recognized installation and actual Steamworks; downloader success alone is insufficient |
| Existing Whisky GUI | Already demonstrated app/runtime setup and bottle configuration | Steam installer/login/Play, preservation/recovery; automation cannot currently address its Wine window |

A one-command entry point does not require the Whisky management UI. It also
does not eliminate Wine, Steam or the authentication/ownership requirements.
Packaging with npx does not solve runtime credential handoff. Prefer one coherent
existing Steam session where feasible before adding two separate auth flows.
The exact product command and package do not yet exist; no package publication
or guarantee of QR-only interaction is claimed.

## Remaining Stage 1 Work

Compare the smallest command-driven normal-Steam route with GUI delivery and
record a concrete implementation design before any source correction. Preserve
current task-owned install state. Complete official Steam install/login/owned
install/normal Play and actual Steamworks before completing Stage 1. All Stage 2
recovery, 20-minute gameplay and clean-distribution gates remain unperformed.

### Existing CLI inspection

At the same app-v3.7.0 tag, `WhiskyCmd/Main.swift` already exposes `run`, `games`
and `launch <AppID> --bottle <name>`; launch delegates to genuine Windows Steam.
Its `create` only registers a bottle and explicitly tells the user to open Whisky
to bootstrap the prefix. `Install` is an empty, unregistered command. Therefore
wrapping the current CLI alone does not provide fresh-machine one-command setup.
Also, the `launch` command prints a launched status after scheduling the async
launch task; that text is not a readiness/menu/Steamworks success check. Reuse
existing functions where appropriate, but verify actual lifecycle and outcomes.

## Selected implementation after requester revision

Whisky management UI is no longer the selected user entry. Its CLI lacks complete
bootstrap, and copying its GUI would add unnecessary UI and licensing integration.
Reuse unchanged Libraries 3.1.1, official Steam and the normal Steam launch model.
Use the existing Pear Rust direction for the shared preparation/launch binary,
reusing the manager library's public hashing/path helpers without weakening its
fixture-only real-runtime gate. A small Swift shell adds native status presentation
and double-click entry; it contains no separate installation logic. No upstream
GPL source is copied. Pin current dependencies and preserve runtime notices.

The requester asked for storage cleanup. The newly installed Whisky app, duplicate
expanded runtime, unfinished bottle (no Steam executable/account/game/save state)
and unmounted DMG were removed. Observed free-space increase was 1,228,140,544
bytes; concurrent host activity/APFS accounting means this is an observation,
not exact uniquely reclaimed allocation. Runtime archive and installer remain.

## October 11 implementation progress

The shared Rust core and Swift window build locally. Eight functional checks
pass. The locked libc archive and all 360 extracted regular files match. The
existing manager's unused-symbol warning is unchanged; its source and real-runtime
admission remain untouched. No native runtime qualification is inherited.

A fresh private setup with the retained verified archives completed Wine/DXMT
preparation and official Steam installation. Repeated setup verified the runtime
and reused the prefix/Steam without downloading or reinstalling. The app window
was observed through accessibility. The requester confirmed the Steam login
screen and subsequently reported successful login. No account data was captured.

The official installation URI sent before login did not establish an installed
game. An explicit continue action (Enter in CLI or button in the app) can resend
the same request after login without authenticating elsewhere. Automatic login
detection and QR-only interaction are not claimed. The app now waits for the
default Steam library's complete AppState before requesting normal Steam launch.
Game installation, menu and original Steamworks success remain pending.

The initial wrapper resource-signature assessment failed before local sealing.
The build now applies a local ad-hoc signature without extra entitlements. A
separate copied bundle passed deep/strict verification; this is not Developer ID,
notarization or browser-delivery qualification. Prior failures remain in the
observations. Stage 1 is incomplete; no Stage 1 completion report is issued.

## Requester feedback: manual Steam installation is not the intended automation

The requester supplied a Steam install-confirmation screenshot and recalled the
previous terminal QR/download flow. The screenshot confirms the install URI
reached the real Megabonk install dialog; it does not prove installation or play.
Do not retain the image or its account identifier in repository evidence.

The previous acquire.py invokes DepotDownloader with -qr, a distinct login ID,
explicit Windows depots/manifests, an owned output directory and validation. The
[upstream 3.4.0 README](https://github.com/SteamRE/DepotDownloader/blob/DepotDownloader_3.4.0/README.md)
confirms QR and automated download support. That can be reused without writing
a downloader or authentication protocol. Its login is not established as the
official Windows client's running game session. Earlier direct launch plus
steam_appid.txt does not prove a single-authentication normal Steam route.

Current manual installation confirmation is an implementation choice, not merely
a development display. The requester has not accepted it as the final experience.
Treat the current tool as a baseline and the minimized-interaction acquisition
flow as unresolved; do not claim the requested end-to-end automation is complete.
Further design should evaluate existing acquisition/client integration and avoid
duplicating #11's private adapter or changing #46's comparison. The current #46
plan still leaves actual authentication/game comparison to its later stages.

The app packaging failure was traced to an unterminated shell heredoc that put
sealing commands into Info.plist. The boundary is corrected, the plist parses,
and the full packaging pipeline is rechecked in a separate output directory
while preserving the user's running authenticated Steam session.


## October 11 fresh-login automation verification

The historical install-URI/Continue design above is superseded. The current Rust
core sends official Steam `-console +app_install 3405340`, retries at a bounded
interval until the target manifest exists, waits for complete installation, and
sends `-applaunch 3405340` once. No DepotDownloader, token transfer, synthetic
manifest or direct game launch is used. Nine functional checks pass.

The existing authenticated baseline first completed automatic installation and
normal launch. The requester confirmed responsive menus and normal exit. A new
private prefix, without copied authentication or game files, then exercised the
final app candidate. Only the verified runtime was APFS-cloned. The requester
completed official Steam login and confirmed automatic game launch and responsive
menus without an install click. The target manifest reached StateFlags 4, build
21750826, depot 3405342, manifest 446680890915713051. The original Player.log
reported Steam initialized and Direct3D 11 on Apple M4 Pro. The process used the
selected Wine winemetal library, DXMT shader cache and Rosetta mappings. Client
and game executable hashes matched the baseline; no steam_appid.txt was present.
See the sanitized observation JSON for exact candidate hashes and scope.

The requester accepts Steam windows. This flow retains the official client for
login, download and game services. DepotDownloader 3.4.0 separately supports QR
or account authentication and downloads without the desktop Steam client, but
it does not itself provide the game's Steamworks runtime. The earlier acquisition
script used DepotDownloader; the separate runtime script started Steam before
direct game launch. That history does not prove Steam-client-free Megabonk play.

The final app passed deep/strict local signature verification. Its signature is
ad hoc, without a Developer ID. The sandboxed Gatekeeper query returned an
internal error; a host query returned rejected (exit 3). Local execution success
must not be promoted to ordinary-user distribution. Stage 1 security remains
unresolved and no completion report or stage transition is recorded. The old
Whisky GUI's notarization evidence applies only to that removed upstream app.
The same-host fresh prefix is not the Stage 3 second-clean-setup qualification.


## October 11 distribution-focused requester revision

The requester prioritized general Windows Steam entry, public-document alignment
and real app/CLI delivery, with performance and language rewrites deferred. The
app now opens the library; the requester confirmed it. The signed CLI reused the
same private state without download or installation, preserving ready markers
and the game manifest. Megabonk automation remains an explicit command.

The owner authorized their Developer ID Application certificate. The app and
nested CLI were signed with Hardened Runtime and timestamps, without additional
entitlements, then verified. Candidate ZIP sizes are 344,605 and 314,357 bytes;
these exclude the external Wine runtime, Steam installer and all private data.
Nine Rust, four packaging-boundary and 35 documentation tests passed, plus four
CLI argument/help checks and real reused-prefix launch. The notary profile check
failed because pear-notary was not present in Keychain. No notary submission,
stapling, public release, visibility change or Stage completion is claimed.

The concrete license boundary is recorded in preview/THIRD_PARTY_NOTICES.md.
Linked libc and Rust library notices were copied unchanged into the package.
The selected DXMT 0.80 archive carries MIT; Wine is LGPL with additional component
terms. Whisky's GPL app code is not incorporated. External-runtime source/patch
correspondence and aggregate dependencies remain a review gap. Selecting a Pear
license does not cure a missing upstream source/notice obligation. The requester
has not yet selected the product license. No root license has been invented.

A publication pattern audit covered 1,877 locally available origin-history blobs
(52,228,983 logical bytes) plus current task files. No configured high-confidence
key/token pattern matched. Seven historical file paths contain personal-home-path
patterns, largely fixture/example data; this is not a complete secret review.
GitHub surfaces, current refs and final publication inventory require review.
Private prefixes, saves and prior experiments remain retained. Build outputs reuse
the existing Cargo cache; no runtime clone or game download was added in this
revision. Signed candidate and package receipts remain needed for notarization
and release review, so they are retained under the task's ignored output roots.


The follow-up GitHub text review covered 49 Issue/PR bodies, two Issue comments
and no review comments. No configured secret patterns or GitHub attachment links
matched. Six historical personal-path files use synthetic placeholders; one old
plan contains a real local home path. These bounded checks inform the final
visibility review and do not authorize publication or certify absence of secrets.


## October 11 Apple notarization and package verification

The owner completed pear-notary Keychain registration after accepting Apple's
updated agreement and waiting for the service to accept the request. No account
password or key was exported. The authorized Developer ID app and CLI ZIPs were
submitted separately and accepted with no issues. Submission identities and
archive hashes are in the sanitized observation record; Apple logs are retained
only under the ignored task output. The app ticket was stapled and validated.
Deep/strict signature verification, spctl (Notarized Developer ID) and
syspolicy_check distribution passed.

The raw CLI spctl execute probe returned exit 3 because it is not an app. The
[Apple product-type guidance](https://developer.apple.com/forums/thread/130560)
(revised December 5, 2024; reviewed October 11, 2026) instead uses codesign with
an explicit notarized requirement for other code. That check passed. The package
release checks and existing maintainer guide now enforce the correct CLI probe
and add the newer app distribution check. No launcher/runtime bytes changed.

Repacked candidates were extracted separately, and their signatures, app ticket,
app assessment, CLI notarization and CLI help execution all passed. All regular
CLI ZIP entries are byte-identical to the submitted archive; its ZIP metadata
changed. App/CLI candidate sizes are 346,274 and 314,357 bytes. These tests ran on
the build host, so clean browser delivery is still unperformed. The previous
ad-hoc Gatekeeper failure remains historical evidence and is superseded only for
the exact Developer ID candidate. Source licensing, runtime provenance, recovery,
sustained play and clean setup remain release gates. No public upload, repository
visibility change, Stage 1 completion or next-stage transition occurred.

The additional source review found Gcenx macOS_Wine_builds documents MacPorts and
its macports-wine overlay as dependency sources. The 11.0_1 release identifies
wine-gecko 2.47.4 and wine-mono 10.4.1. These identify upstream leads, not exact
source/patch correspondence for every file in Whisky Libraries 3.1.1. The existing
aggregate provenance gap remains explicit; no new runtime payload was downloaded.


## October 11 License Review and Proposed Decision

The requester asked whether GPL would be safer. Recommend **GPL-3.0-or-later for
original Pear code without an existing separate license**, if the desired
policy is that redistributed modified versions also provide their covered
source. This is a proposal, not an adopted root license. It does not replace
third-party terms or establish distribution qualification.

| Boundary | Observed terms | Required treatment / review result |
|---|---|---|
| Pear launcher, bootstrap and reused Pear manager helpers | Product choice pending | Apply the selected license only where the copyright holder has authority; preserve already marked files |
| Linked libc 0.2.186 | MIT OR Apache-2.0 | Original license texts are already packaged; preserve attribution |
| Rust 1.94.1 linked libraries | MIT/Apache with separately licensed dependencies | Complete toolchain library notices are retained; their all-target inventory is broader than this macOS binary |
| System frameworks/libraries | Apple/system terms | Referenced on the host; not bundled in Pear ZIPs |
| Whisky GUI/WhiskyKit | GPL-3.0-or-later | Inspected, not incorporated into Pear; do not describe the runtime aggregate as uniformly GPL |
| Wine 11.0 | LGPL-2.1-or-later and separate component terms | Notice and corresponding-source closure still incomplete for the selected repack |
| DXMT 0.80 | MIT | Exact archive notice matches upstream; later LGPL DXMT pins in native work retain their own terms |
| Other runtime libraries, Mono and Gecko | Component-specific, not fully mapped | Resolve versions, notices, source/patch/build provenance for actual distributed files |
| Existing Madeira-derived CPU driver | GPL-3.0-or-later | Preserve its existing license and provenance; not part of the preview binary |
| Steam, Rosetta and owned games | Proprietary, separate terms | No Pear relicensing; not included in Pear app/CLI archives |

### Artifact findings

The cached Libraries 3.1.1 archive was rehashed to
01f3a1b43b98065fe20c529c1023b61dd79a6d2ad93bba6040865f646481ccf3.
It has 4,787 regular files. A case-insensitive basename scan for license/licence,
copying, copyright, notice or authors found only Libraries/DXMT/LICENSE.
Its SHA-256, 6b928413c6308c106f3e0080bd94b6427b56d587d400fd40e6cbfbab7d9c4ae1,
equals the upstream v0.80 MIT file. This bounded filename scan does not prove
absence of embedded attribution and is not a finding of upstream infringement.

The archive also contains 39 regular dylib files and 55 dylib symlinks,
including GnuTLS, GMP, Nettle, libidn2, libunistring, gettext, SDL2, ICU,
FreeType, libpng, MoltenVK, compression and MacPorts support libraries.
The observation JSON records every filename. ABI filenames do not establish
source versions. Embedded strings identify GnuTLS 3.8.7 and libpng 1.6.45;
MoltenVK's project version remains unresolved. Mono, Gecko, shared objects,
PE and managed modules require additional inventory beyond this dylib list.

Whisky's pinned assembly script starts from a prebuilt v3.0.0 runtime, replaces
DXMT payloads, changes Wine builtin markers and repacks. A Whisky source ZIP
therefore does not itself supply all corresponding Wine/helper source.
Gcenx's 11.0_1 README points to MacPorts and its overlay. The inspected overlay
Portfile pins Wine 11.0 and lists patches/dependencies and notice installation,
but its relationship to the release's actual build is unproven. These are
useful source leads, not completed source correspondence or permission to mirror
the aggregate. No additional large runtime or game download was performed.

A bounded scan found SPDX marker text in 191 tracked files, including
documentation and patches; this is not a count of independently licensed
components. Existing MIT fixtures and LGPL integration material keep their terms.
The CPU driver at tests/cpu/runner.c already declares GPL-3.0-or-later and
attribution to Madeira revision 48f976429c189f8396e23d251d8a82f43c705922.
The upstream GPL text and additional-permission file were fetched and matched
the hashes in tests/cpu/sources.json. The permission records adoption on
September 24, 2026, covers specified Apple-library combinations for
Madeira-author-owned code and does not grant rights over Apple libraries or
unrelated Wine code. Keep the provenance and any relied-on permission with
that adapted material. There is currently no root license or tracked GPL text
in the license-filename inventory; include the required text in the
public-source preparation.

### Concrete recommendation and obligations

GPL-3.0-or-later is a better fit than MIT if Pear wants redistributed derivative
versions to remain available under copyleft. GPLv3 is compatible with Apache-2.0
material; GPL-2.0-only is not, and does not accommodate the existing GPLv3
driver as one combined work. Separate independent works keep their terms.
LGPL is aimed at allowing broader library linking, while the desktop wrapper
does not currently need AGPL's network-use condition. The later-version option
permits recipients to choose a future FSF GPL version; GPL-3.0-only would fix
the choice to version 3.

GPL allows paid redistribution; Pear can offer its own official builds for free,
but cannot use GPL to prohibit someone else charging for copies. Distribution
of covered binaries requires the applicable source and notices. Private
modifications do not by themselves require public release. A private GitHub
repository URL is insufficient for an ordinary recipient's source access.

For the selected release, provide corresponding Pear source, lockfile, build and
packaging scripts and required dependency source access beside the binary.
Preserve copyright notices, license texts and any applicable NOTICE material.
For a redistributed Wine library, LGPL-2.1 section 4 requires complete
corresponding source, including relevant build/install scripts and changes;
linked combinations have additional section 6 conditions. Pear currently runs
Wine separately rather than linking its code. That observed boundary is not a
blanket exemption for every future integration or download arrangement.

A complete source/build-input record is needed; hash-identical reproduction of
a signed binary is not the GPL test. Standard macOS system libraries and the
owner's private signing keys are not ordinary source-release contents. Keep
official signing private, and document how contributors build their own copy.

### Release decisions still open

1. Owner adoption of the scoped GPL-3.0-or-later proposal and addition of the
   root text/appropriate first-party metadata, preserving existing exceptions.
2. Public-source notice closure, including the GPL CPU fixture and existing
   framework/third-party attributions.
3. Full runtime source/notice mapping. The current direct-upstream download
   boundary is recorded separately from Pear rehosting; it does not certify
   the aggregate. Do not bundle/mirror it while the mapping is unresolved.
   If exact inputs cannot be recovered, qualify a build with complete sources
   and notices rather than relabeling the existing archive.
4. Rebuild, re-sign and re-notarize the final packaged app after license/notice
   additions. The already notarized candidate remains sealed and unchanged.
5. Retain the separate public-visibility, recovery, sustained-play and clean
   delivery gates. This review is not Stage 1 completion or publication approval.

### Primary references reviewed October 11, 2026

- [GPLv3 text, particularly sections 1, 4-7 and 10](https://opensource.org/license/gpl-3.0)
- [GNU compatibility notes](https://www.gnu.org/licenses/license-list.html.en)
- [GNU GPL questions: private changes, aggregation and source access](https://www.gnu.org/licenses/gpl-faq.html)
- [GNU guidance on selling free software](https://www.gnu.org/philosophy/selling.en.html)
- [Wine 11.0 license](https://github.com/wine-mirror/wine/blob/wine-11.0/LICENSE)
  and [LGPL text](https://github.com/wine-mirror/wine/blob/wine-11.0/COPYING.LIB)
- [DXMT 0.80 MIT notice](https://github.com/3Shain/dxmt/blob/v0.80/LICENSE)
- [Pinned Whisky assembly](https://github.com/frankea/Whisky/blob/305da2143bf6f73ac5b261303c7e7e957c23a227/scripts/assemble-runtime.sh)
- [Gcenx release README](https://github.com/Gcenx/macOS_Wine_builds/blob/11.0_1/README.md)
  and [inspected overlay recipe](https://github.com/Gcenx/macports-wine/blob/092031f7b987a1f1047f263ff3bfd4e1c9c850ee/emulators/wine-stable/Portfile)
- [Madeira license](https://github.com/willfaust/Madeira/blob/48f976429c189f8396e23d251d8a82f43c705922/LICENSE)
  and [additional permission](https://github.com/willfaust/Madeira/blob/48f976429c189f8396e23d251d8a82f43c705922/LICENSE-EXCEPTION.md)

Source-text hashes and bounded observations are in the existing Stage 1 JSON.
This review changed no executable, runtime, authenticated state or signed bundle.


## October 11 License Adoption

After reviewing the proposal, the requester explicitly selected
GPL-3.0-or-later. The earlier proposal/pending statements above are historical.
The root GPLv3 text is identical to the reviewed canonical upstream text
(SHA-256 e6037104443f9a7829b2aa7c5370d0789a7bda3ca65a0b904cdc0c2e285d9195).
README and packaged notices specify the later-version option, warranty and
original-code scope; both Pear Rust crate manifests now declare that SPDX
expression. Existing file/directory licenses remain intact.

The exact Madeira additional-permission text is retained beside its CPU fixture;
its hash matches the existing source manifest. This preserves that upstream
record without extending its author-specific permission to all of Pear.
Existing license source bytes and third-party notices were not rewritten.

The review's 35 documentation tests, offline governance check (29 documents,
283 local targets), inventory/hash checks and whitespace checks passed before
adoption. Revalidate affected document/package evidence after these additions.
A separate licensed package candidate will supersede the prior candidate only
after successful build/sign/notary checks. Runtime provenance, recovery, play,
clean delivery and visibility decisions remain unresolved.


### Licensed candidate verification

The separate GPL candidate passed nine Rust tests, four package tests and
35 documentation tests. Offline governance passed for 29 documents and 288
local targets; license hashes, both Cargo license fields and whitespace passed.
The existing unused-function compiler warning remains; there was no build error.

Both app and CLI notarization submissions were Accepted with status code 0 and
no issues. The app was stapled, repacked and extracted. Deep/strict signatures,
app Gatekeeper, app syspolicy distribution, CLI's explicit notarized requirement
and extracted CLI help all passed. Both ZIPs contain the exact root GPL text and
current component notices. The app's core and standalone CLI are byte-identical.

The current local candidates are 359,749 bytes (app) and 327,659 bytes (CLI);
their hashes, notary identities and source-input hashes are recorded under
license_review.licensed_candidate in the Stage 1 observations. The prior
candidate's receipts remain historical, not interchangeable with these artifacts.
Source is still uncommitted pending the required stage gates. These checks are
on the build host; no public upload, visibility change or clean-delivery
qualification occurred.

## October 11 Exact Runtime Provenance Follow-up

The requester approved this review after website approval. The existing approved
component notice and this investigation are the documentation destinations.
No executable, installed runtime, authenticated prefix or sealed candidate changed.

### Results and scope

- Libraries v3.1.1 resolves to 58b3ce120bcc7a86ff6e6b4a4e921dfce57fe115.
  Its assembly script matches the later inspected script exactly and pins the
  January v3.0.0 base. The tag's dependency table still says v3.1.0; use actual
  archive identities and release metadata rather than that heading as evidence.
- All 11 DXMT v0.80 payload files match after applying the documented marker
  replacement to six DLLs in memory. Other bytes are unchanged. Exact source:
  589adb780354b461645b29999cefaf533594ee99. The top-level license is MIT;
  src/util/dxvk.LICENSE separately retains zlib terms. Submodule pins are NVAPI
  d08488fcc82eef313b0464db37d2955709691e94 and DirectX headers
  9df86f2341616ef1888ae59919feaa6d4fad693d. NVIDIA License.txt explicitly scopes
  its MIT text to nvapi.lib/nvapi64.lib; do not infer every header's terms from it.
- DXVK's four DLLs and dxvk.conf match the native
  v1.10.3-20230507-repack archive, not its builtin sibling. Exact source:
  8f1e28deed3ad30802f7e1bdff428ec14e6e7817, zlib/libpng license.
- All 39 regular helper dylibs, 2,921 Mono regular files and 60 Gecko regular
  files match the Gcenx 11.0_1 package by same-path hash. Mono is 10.4.1; both
  Gecko VERSION files identify 2.47.4. Mapping binary origin does not complete
  the transitive corresponding-source and notice inventory.
- Of 4,770 regular files under Libraries/Wine, 3,200 match some regular file in
  Gcenx 11.0_1 and 1,570 do not. The Libraries base release was published on
  January 18; Gcenx 11.0_1 on April 16. Representative cmd.exe sizes are 986,624
  and 1,007,616 bytes, and ntdll.so sizes 581,696 and 577,552 bytes. Differences
  are not limited to timestamps. Later documentation's 11.0_1 label is therefore
  insufficient to identify the selected Wine binary's origin. No legal violation
  is inferred, and byte-for-byte builds are not asserted as a license requirement.
- Gcenx overlay's initial available recipe snapshot is April 16 commit
  5c5bf5771ab8110d538aa25faee1b81578111840. It differs from the later recipe
  previously reviewed; neither is proven to be the January build recipe.
- No D3DMetal/GPTK-named member exists in the inspected archive. The old tag's
  table lists D3DMetal; later upstream discussion #163 describes its absence.
  Filename inspection alone is not proof that no proprietary bytes exist.

### Decision and remaining inputs

Keep the successful current runtime for development. Do not replace it with the
April build just to make a version label agree. DXMT/DXVK binary transformation
and origin are now mapped; Wine core source/build identity and complete auxiliary
notice/source records remain the release admission gap. Ask upstream for concrete
source inputs before deciding whether a source-recorded replacement is necessary.
A correspondence request is prepared below, not posted. No outside person has
been messaged. This review does not complete Stage 1 or authorize Stage 2.

### Prepared upstream inquiry (not sent)

Destination: https://github.com/frankea/Whisky/issues

Title: Source/build provenance for Wine in Libraries v3.1.1

Hello, we are reviewing the unchanged Libraries v3.1.1 download for Pear, a free
open-source Windows Steam launcher. Could you point us to the source revisions,
patches and build/packaging scripts for the Wine build inherited from v3.0.0, and
the dependency source/notice inventory?

The v3.1.1 assembly script at 58b3ce120bcc7a86ff6e6b4a4e921dfce57fe115
pins the January 18 v3.0.0 archive (SHA-256 9c3d2a7d9bb682ae8398d8bae458e3cb52bb9f5a3345fb0830a64d9b6a1025f8).
The dependency table later names Gcenx 11.0_1, published April 16. Comparing the
v3.1.1 Wine subtree against that archive gives 3,200 regular-file hash matches
and 1,570 unmatched files. All 39 helper dylibs and the Mono/Gecko trees match,
but cmd.exe and ntdll.so differ in size and substantial contents.

We have matched the DXMT v0.80 files with the documented six marker replacements
and the native DXVK v1.10.3-20230507-repack files. The remaining questions are the
original Wine build inputs and exact MacPorts/helper, Mono and Gecko source/notice
records. We are not assuming a reproducible binary hash is a license requirement
or alleging noncompliance; we want to avoid attaching the wrong build sources.
Thank you for any archived manifest, recipe revision or source links.

### Evidence retention

Read-only comparison archives and per-file maps are under ignored
.build/task47/license-review, owned by #47. Four additional archives total
209,563,977 bytes (about 200 MiB); no unpacked runtime copy was created. Keep these
inputs and sanitized maps through provenance resolution/review, then retain the
small manifests and remove redundant public archives only when no longer needed.
Existing signed candidate packages remain sealed; changed notice source must be
included in a separately rebuilt/signed/notarized candidate before any release.


## October 11 Authorized Replacement Candidate

The requester chose candidate validation without contacting upstream. The prepared
inquiry above remains unsent. Gcenx Wine 11.0_1 plus DXMT 0.80 is now implemented
in the development bootstrap as two independently pinned downloads. Existing
sealed packages remain historical baseline builds. No existing prefix is migrated.
The new bootstrap refuses a different runtime marker before downloading/executing
Wine; partial setup also has a versioned runtime marker.

Reused the already verified release inputs (203,984,701 combined bytes) and the
reviewed DXMT builtin pairing/16-byte native marker transformation. Steam setup
needs only eight DXMT DLLs and the Unix bridge; no DXVK or optional NVAPI DLL is
selected. The Wine subtree retains all 4,768 original regular files byte-for-byte;
bridge files and supplemental notices are added. Installed inventory remained
unchanged after setup and Steam startup. The release-pinned Gcenx README identifies
configure options and MacPorts/overlay sources. This is a more direct binary origin
than the prior repacked base, not a claim that every auxiliary source/patch record
is already complete. The historical April recipe remains a source lead.

Wine --version, wineboot -u and cmd /c ver passed in a disposable prefix. The actual
shared bootstrap then completed isolated Wine/DXMT setup and official Steam silent
installation. Eleven Rust checks and four package checks passed; governance found
37 documents and 352 local targets. A separate ad-hoc Mac app built and verified;
no new Developer ID signing or notarization occurred.

The first Steam startup failed visibly: the updater disappeared and the owner saw
no login window, although Steam/CEF processes stayed alive. Bounded CEF diagnostics
identify SwapChain11 reset failure (0x80004005) and EGL_BAD_ALLOC creating the login
surface, client build 1788652215. Steam's -cef-disable-gpu flag is present in the
installed official executables. Test that UI-only flag without changing game DXMT,
CEF sandbox settings or macOS protections. A normal -shutdown request returned 0
but left processes alive; only the newly created, unauthenticated candidate prefix
was stopped with its own wineserver -k/-w and restarted. Result remains pending.

The Gcenx release declares GStreamer.framework, which is absent on this host. Basic
Wine/Steam preparation is therefore not evidence of media or broad game support.
No non-system absolute load dependency appeared in inspected Unix modules after
excluding their own install names; dynamic dlopen dependencies remain separate.
No source from #10/#11/#46 was imported. Read the latest #46 Stage 2 and #11 Stage 1
reports; they remain separate native-runtime work and do not qualify this Preview.

Candidate inputs, probe results and pair/inventory checks are retained under
.build/task47/runtime-candidate. Private test state stays ignored and must not enter
release assets. Keep relevant evidence through review, then remove duplicate probe
material when no longer needed. This does not complete Stage 1 or release admission.


### Replacement startup failures and next source candidate

The requester confirmed a solid black window with -cef-disable-gpu, including a
screenshot. A separate diagnostic assembly then selected DXVK native d3d11/Wine
dxgi for Steam helpers through AppDefaults, leaving DXMT as game builtins. Module
loads confirmed the intended split, but the requester observed no window. Both
experiments failed Steam UI qualification; the probe prefix was stopped and the
original candidate/private environments remain preserved. Do not adopt the split
in the production bootstrap or convert absent swapchain errors into a UI pass.

Reviewed DXMT #141 and Gcenx macOS_Wine_builds #159/#170: maintainers describe
upstream Wine presentation/Steam limitations. Community reports include corrections
to initial root-cause claims; do not assume crypto errors cause this UI failure.
No Steam helper replacement, archived Steam downgrade or disabled updater is used.

Sikarugir engines were inspected read-only as another distributor option. Its
wrapper includes separately restricted components; the public Wine mirror HEAD
does not by itself identify source/patch inputs for each engine asset. No engine
was downloaded, executed or selected. This would not yet resolve the original
provenance goal. CodeWeavers publishes official FOSS source archives, including
Wine; a source-built Wine subset is the next candidate to assess. This is not
permission to copy the proprietary CrossOver app or D3DMetal. Inspect exact source,
build dependencies, notices and storage before attempting a reproducible build.

Primary references:
- https://github.com/3Shain/dxmt/issues/141
- https://github.com/Gcenx/macOS_Wine_builds/issues/159
- https://github.com/Gcenx/macOS_Wine_builds/issues/170
- https://github.com/frankea/Whisky/blob/3abfbae945e3400caaa13cf2e78fe5a187a1405b/WhiskyKit/Sources/WhiskyKit/Wine/Wine.swift
- https://github.com/Sikarugir-App/Sikarugir
- https://www.codeweavers.com/crossover/source

The official FOSS Wine subset built and installed successfully using Apple clang
and task-local Bison. Its winemac exports macdrv_functions, which the selected
DXMT bridge can consume. A fresh prefix and D3D11 device probe passed
(hr=0, feature level 11_0), followed by official Steam installation and update
to 1788652215. The requester confirmed a black login window. Device creation
is therefore insufficient to qualify presentation. Steam loaded native DXVK
d3d11 and source-built Wine dxgi as intended. The diagnostic build still has
absolute helper-library dependencies and is not portable or release-admitted.
The next bounded test disables CEF GPU rendering and GPU compositing together;
no product bootstrap default has been changed to this experiment.

The requester confirmed black UI with both CEF GPU flags and explicitly requested
cleanup of abandoned methods. Stop the source-test wineserver and retire the failed
Gcenx, cloned renderer-split and source-built configurations. This is not a claim
that every possible source-built Wine configuration fails. All three were
unauthenticated: no Steam userdata/steamapps, loginusers or game manifests were
present. The broad-root deletion was rejected by automatic review; subsequent
cleanup used separately inspected paths and retained input/build/result metadata.
Remove build trees, downloaded source archives, failed runtime/prefix payloads and
obsolete raw logs. Keep notices, hashes and concise metadata under
.build/task47/retired-runtime-evidence. Preserve the previously working runtime,
authenticated state, game/saves and sealed app/packages. Stage 1 remains incomplete;
no replacement is admitted and no new release is published.

## October 11 Baseline Steam Argument Difference

Read-only inspection of both successful private prefixes found webhelper options
--no-sandbox --in-process-gpu --disable-gpu. The baseline kernelbase DLL in both
architectures contains this option string and the Steam helper-name/exception
strings. An original no-network argv-printing PE in a disposable prefix confirmed
three controls: an ordinary filename preserves sentinel only; steamwebhelper.exe
adds all three options; --type=crashpad-handler prevents injection. No Valve
executable was replaced and real Steam was not started.

The exact official crossover-sources-26.3.0.tar.gz was checksum-verified again,
with only sources/wine/dlls/kernelbase/process.c retained. That selected source
contains neither steamwebhelper nor in-process-gpu. Thus the earlier source build
did not reproduce this baseline process-launch behavior. The source archive was
not retained. A Wine 9.0 mirror contains the same three-option table entry:
https://github.com/Ryu-ga/winecx/blob/1b7e19170021fa95a170f0312358dd408e906317/dlls/kernelbase/process.c#L686
This identifies a public behavior pattern, not the baseline's complete source.
WineAndAqua at 479d46a96a325caff09e6143cb0636fcbe565ff9 uses in-process-gpu
without an explicit no-sandbox option for Steam; source inspection alone does not
qualify that alternative. No third-party code was imported into the product.

Security correction: earlier statements that protections were unchanged describe
macOS and Pear's directly supplied switches, not the resulting CEF process. The
baseline itself disables CEF sandboxing through Wine. Do not treat successful
notarization or default launcher arguments as proof of CEF sandboxing. This
behavior is not silently accepted into a release. No new security setting was
weakened in this comparison: the named dummy only prints argv and exits.

This is a concrete behavioral difference and a strong explanation consistent with
CEF cross-process presentation limits, not proof that it is the only cause of
all failed candidates. Next isolate the in-process presentation workaround from
explicit sandbox disabling in source-controlled tests, before another full Steam
setup. Full Wine source/build and auxiliary correspondence remain unresolved.
The disposable probe prefix is removed after execution; small source/results stay
in ignored .build/task47/baseline-argument-probe.


## October 11 Opt-in In-process GPU Candidate Result

The pinned official FOSS Wine source built with the single opt-in process patch
(configure 23.96 s, build 493.86 s, install 4.07 s; all exit 0). Eight original
argv controls passed: disabled opt-in, ordinary name, near-match name, exact
name, case variation, crashpad subprocess, renderer subprocess and an existing
option. Only the selected main helper receives --in-process-gpu; there is no
Valve executable substitution. The patch hash and resulting Wine/kernelbase
hashes are in the existing Stage 1 observations JSON.

In a fresh prefix with DXMT 0.80, official Steam updated, showed a normal login
screen, and the requester completed QR authentication. The actual webhelper log
contains --in-process-gpu without the baseline's --no-sandbox or --disable-gpu.
This checks the observed arguments, not effective CEF sandbox enforcement.
Official Steam then installed owned Megabonk (App ID 3405340, build 21750826,
StateFlags 4) and launched it through -applaunch. The requester confirmed a
visible, interactive menu. Unity identified Direct3D on Apple M4 Pro and input
initialization. Active gameplay duration, audio, saves, recovery and clean-Mac
qualification were not tested in this experiment.

This reproduces the minimum route without copying the baseline's explicit
sandbox-disable switch and provides stronger evidence for the process-launch
workaround than the earlier device-only probes. It does not identify the full
baseline source, prove this was the sole cause of every failed configuration,
or qualify ordinary-user distribution. The candidate still references the
preserved baseline's helper dylibs through absolute paths. Helpers need their
own source/build/license review and a portable package before release admission.
Do not select this diagnostic tree as a product download.

Keep the new authenticated prefix and installed game private; do not delete it
as though it were an unauthenticated failed candidate. The original baseline
prefixes remain untouched. Remove only the completed no-network argv probe
prefix; this reclaimed approximately 1.40 GiB. Source, patch, build recipes,
results and installed candidate remain under the ignored diagnostic directory.
Stage 1 remains in progress. No stage commit, PR, repository visibility change,
upstream message or release publication occurred.


## October 11 Independent Runtime Assembly and Relocation

The requester subsequently reported extended gameplay and audio without problems
on the minimal-patch candidate. Exact minutes and save/reload were not measured.
Those observations apply to that candidate, not automatically to rebuilt helpers.

The same Wine 11.0 FOSS archive and one opt-in patch were reconfigured and built
against pinned upstream GnuTLS 3.8.13, FreeType 2.14.3 and their local source-built
shared dependency closure. The official public MoltenVK 1.4.2 macOS dylib and
DXMT 0.80 are retained with source revisions and notices. No installed Homebrew
runtime or old baseline helper is a dynamic dependency of the assembled tree.
All 45 Mach-O load-command audits passed. After moving the package to a path
containing spaces, Wine, native initialization, AES known-answer, font metrics,
two valid-host HTTPS controls and wrong-host certificate rejection passed.
Nine private helper dylibs were observed loading from the relocated package.
Wine returns API error 12157 for the negative TLS case; the diagnostic trace
explicitly identifies hostname mismatch 12038. A generic network failure alone
was not accepted as a successful certificate check.

Source archives, per-component commands/results, source-lock.json, notices and
relocation results are retained under ignored .build/task47/portable-runtime.
Build recipes are diagnostic and still need clean source-kit generalization.
The linked helper license combination is not described as LGPL-2.1-only: Nettle,
GMP and libunistring introduce LGPL-3.0-or-later/GPL alternatives. FreeType FTL
attribution and bundled third-party notices are retained. Public corresponding
source delivery and final release admission remain pending.

After the requester normally exited the game, the original Wine server stopped.
An APFS clone preserves the authenticated prefix, game and saves privately.
The cloned prefix update returned zero and ten core/DXMT file comparisons passed.
Steam auto-started during wineboot; wineserver wait timed out without force-kill.
A same-prefix official -applaunch request loaded Megabonk build 21750826, DXMT
D3D11/DXGI and builtin winemetal. Unity 2023.2.22f1 reports Apple M4 Pro Direct3D
and input initialization. The requester subsequently confirmed normal menu, gameplay and audio for this
independent package. Exact duration and save/reload remain unmeasured. No explicit SteamAPI_Init success is inferred from Player.log.
Sanitized module/initialization evidence is steam-test/sanitized-launch-evidence.json.
The original successful prefix is preserved. This is a Rosetta experiment, not
ARM64 Wine/FEX or M1 qualification. No public release or stage transition occurred.

Only completed Wine objects, the unused aggregate dependency extraction and the
unauthenticated smoke prefix were removed. The object/smoke cleanup reclaimed
4.50 GiB; source archives, installed runtimes, recipes and private state remain.

The tested runtime file set is now recorded in runtime-content-manifest.json
with SHA-256 hashes and internal symlink targets; candidate-input-manifest.json
records retained source archives, configuration, patch and diagnostic recipes.
These manifests exclude authenticated prefixes and proprietary content. They
freeze the observed local inputs, not clean-build reproducibility or distribution
qualification. With approximately 4.1 GiB available, no further full clone, large
archive or rebuild was started; the tested candidate is retained for reuse.


## October 11 Fresh Reconstruction Checkpoint

The old portable runtime and dependency trees were subsequently released by
coordinated storage cleanup; their historical observations are not current
availability. The approved Stage 1 continuation adds an allowlisted source/input
kit under preview/, exact input/notice verification, absent-output enforcement
and a shared host lock. Existing successful receipts cannot skip missing outputs.

A full fresh v2 build completed after a v1 configure failure exposed the upstream
Bison whitespace-path requirement. The corrected recipe uses a local tool-prefix
alias. v1 failure records remain in portable-runtime/rebuild-v1-failure.
The actual v2 executing recipe and toolchain records are retained beside its
runtime; later source-kit packaging/toolchain metadata additions are not silently
attributed to that already-running build. MinGW GCC 15.2.0 identities are recorded
separately for v2 and automatically by the current recipe.

The v2 runtime was renamed into a path containing spaces without making another
full copy. All 45 Mach-O audits passed. A fresh unauthenticated prefix passed AES,
font metrics, valid-host HTTPS and a wrong-host rejection with the explicit
12038 certificate trace. Ten packaged helper dylibs were observed; no old helper
or Homebrew runtime dylib was loaded. The synthetic services stopped and their
prefix was removed. This does not establish game or distribution qualification.

Exact replay inputs are preview/runtime-inputs.json, preview/runtime_build.py,
preview/patches/steam-inprocess.patch and preview/runtime-notices/. The local kit
is portable-runtime/pear-runtime-input-kit.tar.gz (11 inputs, 61 notice files);
its independent extraction/verification result is source-kit-result.json.
Current output, manifest, load-audit.json, validation/result.json, configuration,
executing build-recipe.py and toolchain records are under
/private/tmp/pear47-rebuild-v2. DXMT/MoltenVK remain identified upstream binary
inputs with source references; full corresponding-source/release admission is
still pending. No ARM64 consumer claim or source/toolchain migration is implied.

After successful synthetic checks, completed objects, extracted sources, build
helper prefix and binary staging were released under the shared lock after a
handle check. Logical removed bytes were 3,986,138,048; stat-block allocation was
4,106,924,032 bytes. Filesystem free bytes increased by 4,116,430,848 during the
operation, a net observation rather than exclusive physical attribution. The
runtime manifest remained identical; private prefixes were not traversed by
cleanup. Inputs, runtime and small evidence remain required by Stage 1 admission.
Official Steam/game observation on this rebuilt runtime remains pending.


The rebuilt runtime then updated the existing private test prefix after a small
save/config backup. Save/config hashes were unchanged by prefix update. Official
Steam launched Megabonk. Current-run Player.log reports Unity 2023.2.22f1,
Direct3D 11 and Apple M4 Pro; module tracing was unavailable because Steam had
already started during prefix update. Do not reuse the previous runtime's
module trace as a new observation or infer SteamAPI_Init success.

The requester confirmed normal menu/input, persisted sniper-rifle enablement,
shop purchase state and currency 296, then normal game exit. This is a same-host
relaunch/save observation, not restore/recovery or independent clean-Mac
qualification. Official Steam shutdown completed; no owned runtime/prefix/app
handles remained, and the shared compilation lock was released. The runtime
content manifest remained unchanged after execution. Coordinated result and
small source/recipe/audit paths are in task47-heavy-result.json for the next
heavy consumer (#46, then #11); their code/state is untouched.


## October 11 Source-delivery Notice Review

The same-runtime manifest remains unchanged after a read-only comparison.
The next package's notice set expands from 61 to 103 files: exact Wine bundled
license/copyright files, authors, font embedded fields and XML2 attribution
exceptions; DXMT LLVM 15.0.7 (CI pin plus shipped binary version strings),
Microsoft DXBCParser, NVIDIA NVAPI and pinned MinGW DirectX header attribution.
The top-level Wine LGPL and DXMT MIT texts alone were insufficient inventories.
This is a conservative retained notice set, not an exhaustive static-code audit.

No executable was rebuilt or relabeled as tested. Current runtime_build.py merges
pinned Wine notices and rejects differing source notices; source kits now include
the component record. The updated local kit, independent extraction receipt and
review result are in .build/task47/source-delivery-review. Its 11 archives and
103 notice hashes verified; 16 focused tests passed from the extracted kit and
the installed notice tree matched the lock exactly. Retain the earlier 61-notice
kit separately as the historical reconstruction input. Neither kit is published.

Remaining source/delivery work is concrete: upstream static compiler/runtime
notice correspondence; the shared app/CLI still targets the rejected Gcenx
candidate and must be connected to the admitted runtime; normal Steamworks
initialization still lacks explicit same-run evidence; exact committed sources,
signing/notarization, recovery and independent clean-Mac qualification remain.
No blanket license violation or final legal clearance is inferred. Upstream
reference: GNU LGPL 2.1 section 4 and LGPL 3 section 4/GPL 3 section 6; the intended
release will carry the corresponding source kit alongside binary downloads,
not rely only on a third-party source homepage.

Review cache is below the approved 300 MiB additional bound (about 204 MB revised
kit plus small notices/source). Original runtime, login, games and saves remain
protected; extracted kit/test scaffolding was removed after verification. The
shared heavy slot stays released for #46/#11.


## October 11 Rebuilt Runtime App/CLI Integration

Requester approval covers the remaining notice comparison and integration of the
successful runtime into both entry points. The conservative static toolchain set
now includes the DXMT CI-selected LLVM-MinGW 20251216 (LLVM 21.1.8 and pinned
MinGW), separate LLVM 15.0.7 shader-translator notices, and local Wine PE compiler
GCC 15.2.0 with its Runtime Library Exception. MinGW runtime/pthread/SEH/profile
notices and authors are preserved for the DXMT pin and Wine toolchain v14.0.0.
All 127 notice files and 11 source/binary inputs verify. This closes the identified
notice comparison, not an independent byte reproduction of upstream DXMT or final
public distribution admission.

The rejected Gcenx fetch/assembly was removed from the shared Rust bootstrap.
Both entry points select pear-wine11-cw26.3-dxmt0.80-v2 and the same pinned archive.
Before publication there is intentionally no fallback download URL. Developers
provide --runtime-archive or PEAR_PREVIEW_RUNTIME_ARCHIVE. The app inherits this
selector; PEAR_PREVIEW_ROOT selects an isolated app state directory. Existing
prefixes of another runtime are refused without modifying saves or credentials.
The reviewed PEAR_STEAM_IN_PROCESS_GPU=1 opt-in is shared by app/CLI launches;
WINEMSYNC is not introduced into the independently tested runtime configuration.

runtime_package.py streams only files matching the reviewed immutable baseline,
injects the new notices and adds the six reviewed 16-byte DXMT native overrides.
All eight installed DXMT DLLs match the successful private test prefix exactly.
The baseline runtime remains unchanged. The archive is separately pinned and
verified; it contains neither an authenticated prefix nor Steam/game payloads.

The app/CLI build and 12 Rust tests passed. The bundled and standalone CLI hashes
match. Actual CLI extraction, repeat use, altered-file rejection and incompatible
prefix refusal passed; synthetic save sentinels were preserved. Nineteen runtime
Python checks and four app-package checks passed. The independently extracted
source kit verifies 11 inputs/127 notices and passes all 19 checks.

The installed runtime also passed fresh synthetic native/Windows AES, fonts and
positive/negative HTTPS checks. Ten packaged helpers were observed, no external
helper loads occurred, and wrong-host TLS rejection was explicit. Its unauthenticated
prefix was stopped and removed. This is distinct from the preceding successful
user gameplay/save test: the new app has not yet opened Steam or a game. #11's
ongoing Rosetta-free work retains live-run priority; no game session was started
or interrupted here. Final GUI/Steamworks/recovery/clean-Mac and signed delivery
checks remain. The new app is ad hoc signed, not a new notarized release.

Detailed receipts: .build/task47/integrated-runtime-v1/result.json and
source-delivery-review/source-kit-integration-v3-result.json. The superseded first
533 MB archive was removed after the final replacement passed; its small receipt
remains. The immutable baseline, current installed runtime, final archive, source
kits and all private state are retained for their recorded consumers.


## October 11 Developer ID and Notarization Checkpoint

The integrated app and its shared CLI were signed using the requester-authorized
Developer ID, then separately Accepted by Apple's notary service. App submission
479bdeb4-eb69-484f-b4e7-7170b29823f1 and CLI submission
498a6a5e-bc19-4950-9a38-2418602309de are retained with logs. The app ticket was
stapled and validated; syspolicy_check and Gatekeeper accepted it. Both entry points
still pin the previously tested unsigned runtime archive. This does not qualify
the separately installed runtime or establish a new Steam/game execution result.

An isolated runtime copy had all 45 Mach-O objects signed and independently
verified; executable text and all non-Mach-O content stayed unchanged. Only its
two Wine loaders received allow-unsigned-executable-memory. Runtime submission
06546735-84a0-4e90-a108-106d34945c06 was Accepted; all 45 notarized signature-policy
checks passed. The submitted ZIP SHA-256 is
0045d92717668eece7633627e3f954266176d470f3ba8bc80d081f47c8462c81.

Fresh synthetic execution nevertheless FAILED. Native helper initialization passed,
but Wine could not set executable protection on wineboot/ntdll PE sections and
entered a repeated exec-fault loop. Its own synthetic wineserver was stopped;
zero runtime/prefix handles were verified and the unauthenticated prefix removed.
No Steam, game, login or save state was used. The immutable failed result hash is
29b6a029331e6f90fe8d5e9ef15511255761e4164a867b138ad1d8073f1cc882.
The repetitive log was compressed from 192,135,830 to 1,282,042 bytes, with its
restored SHA checked. Do not promote this signed archive to the app/CLI runtime pin.
The earlier user-confirmed gameplay/save evidence remains scoped to unsigned v2.

Source reuse review: Apple's library-validation documentation explains the default
same-team/Apple code requirement and the exception for third-party loaded code.
osxEQL's public packaging reports the same PE noexec failure and uses four Wine
exceptions. That implementation motivates a narrow loader-only library-validation
probe; it does not prove Pear requires all four. No upstream signing code was
copied, and no broader exceptions or system-wide security changes were applied.
References reviewed October 11, 2026:
- https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.cs.disable-library-validation
- https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.cs.allow-unsigned-executable-memory
- https://github.com/sowoky/osxEQL/blob/main/packaging/entitlements.plist
- https://github.com/sowoky/osxEQL/blob/main/packaging/sign-and-notarize.sh

The validator now bounds retained output to 16 MiB and terminates/reaps its owned
child on timeout or log overflow; existing prefix-specific server cleanup remains.
The flood and timeout regression checks pass. Independently extracting source kit
v5 verified all 11 inputs/127 notices and 24 runtime tests. Kit SHA-256:
a58be53271ec48d0acb26d21e73aaf01ced5c26f7cf78116392bb71b9bdfab06.
It contains the current bounded validator; that change was not used retroactively
for the failed run. Same-turn v4 was removed after verification; historical source
kits and private state remain. Receipts live under integrated-signing-v1,
signed-runtime-v1 and source-delivery-review in .build/task47.

The shared slot is released for the prepared #11 observation and subsequent #46
work. Stage 1 remains open. Runtime execution, new app Steam/game, Steamworks,
recovery, clean-Mac qualification and public release admission are still distinct
unfinished checks; notary acceptance does not replace them.


## October 11 Narrow Signed Loader Retry Prepared

Explicit requester continuation authorized resolving the signed-runtime failure
and validating the new app, while respecting other experiments. Only two small
loader copies were prepared with allow-unsigned-executable-memory plus the
third-party library-validation exception. Signatures verify and executable text
matches v1; app/CLI/wineserver/library policies and the original runtime remain
unchanged. The prepared copies total 66,240 bytes after signing. This is neither
an execution result nor a new notarization result.

The synthetic validation now observes mapped images from its exact owned Wine
PID with macOS lsof at a flushed fixture marker, requires GnuTLS/FreeType mappings,
and refuses missing or external native-image evidence. It uses no DYLD entitlement.
Twenty-six focused source-only tests pass, including marker ownership, missing
mapping evidence and external path refusal. The prepared one-shot executor refuses
before runtime copying when a current Task47 handoff is absent. Receipts and exact
source hashes are in .build/task47/signed-runtime-v2-preparation/preflight.json.
No Steam/game/private prefix was opened during preparation. Stage 1 remains open.


Signed-runtime v2 bounded host observation (2026-10-11): the two prepared
loader changes passed native initialization, Windows AES/font, positive HTTPS,
wrong-host rejection and actual Wine-PID packaged-helper mapping (20 native
images, no external helper). The previous noexec failure did not recur. Original
validation result SHA256 84234c37ef03a91951a3b704a64e1b25f637733436befef22cef2d4f15fcbf3e.
The wrapper failed because synthetic wineserver -k returned 1 without output.
Wine server/main.c uses exit(!kill_lock_owner(...)); server/request.c also returns
0 when no server remains, so this exit alone cannot establish a live failure or
successful cleanup. Independent lsof returned 0 with no owned handles; the new
unauthenticated prefix was removed (1,494,935,009 logical bytes; 1,498,808,320
stat-allocated bytes; measured net free increase 1,500,831,744 bytes). Private
sessions remained unchanged. See signed-runtime-v2/validation/cleanup-verification.json.
The slot was returned to #11 without a retry or Steam/game run.

The validator now accepts stop exit1 only provisionally: it still requires the
prefix-specific wait and successful independent empty-handle inspection. Other
exit codes, failed inspection and remaining handles fail cleanup. 29 focused
runtime tests pass; this revised validator has not been re-executed on Wine.
Automatic approval review rejected persistently adding disable-library-validation
to the production loader recipe pending explicit approval of that security change.
The requester was asked; production signing policy and app/CLI pin stay unchanged.
This checkpoint is neither notarization of the changed loaders nor app/game or
public-distribution qualification. Stage1 remains in progress.


## Stage 1 disposition — October 11

Later owner authorization applied the narrow two-loader policy. The signed-v2
runtime and corrected original-loader app/CLI passed notarization and actual
official Steam install/login/owned-game launch with Steamworks, normal menu/input
and normal exit. This supersedes pending conclusions in the chronological
checkpoints above, without altering their failures. The [Stage 1 report](../working/task_m3_47_stage1.md)
binds the exact artifacts, 127-notice/source-kit comparison, evidence and remaining
recovery/final-delivery gates. No public release or Rosetta-free result is claimed.
