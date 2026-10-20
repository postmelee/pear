# Task #75 — Component source-publication readiness

Initial review: 2026-10-20; notice and PR successor review: 2026-10-21. Tracking: [#75](https://github.com/postmelee/pear/issues/75).
This is a review of exact private source refs and observed GitHub surfaces. No
repository visibility, default branch, inherited history or runtime was changed.

## Decision

| Repository | Decision | Required interpretation/action |
|---|---|---|
| Wine | READY WITH LIMITS | Bounded downstream history and metadata review; retain upstream/license caveats and experimental-source status |
| FEX | READY WITH LIMITS | Stage4 PR successor includes reviewed adjacent notices; missing original holder information remains disclosed, and the default branch still requires integration |
| DXMT | READY WITH LIMITS | Bounded downstream history review, unchanged submodule pins and upstream contribution policy; no full inherited-history rescan |
| Common runtime | READY WITH LIMITS | Reviewed own history, documentation successor and final Task75 WGI delta below |

These are publication-review dispositions, not authorization to make repositories
public, exhaustive legal clearance, clean-clone build support or game qualification.
The requester must see these findings before a visibility decision. All four remain
private. A later visibility operation needs a fresh ref and remote-surface check.

## Initial Stage2 reviewed scope (dated snapshot)

| Repository | Published private ref (`codex/task56`) | Inherited upstream boundary | Downstream commits / new blob versions / logical bytes |
|---|---|---|---|
| Wine | `007291b81de386fd8886770c33b5d385c078635d` | `4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf` | 7 / 133 / 4,457,084 |
| FEX | `4ae26ddf9a21b52cd50d096504c4d0ea5ab49204` | `59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa` | 9 / 183 / 3,491,896 |
| DXMT | `d0ad50946ab64bbe4dc3584a5d91f8e99a6e492c` | `7c8dee1c2d73415301ceb7d1fa810861cef4cd67` | 6 / 29 / 501,125 |
| Common runtime | `9be1545f5a0845d3b14d4b845bf6bd413a224df3` | No history exemption | 9 / 372 / 18,974,948 |

The scanners enumerate reachable downstream commit text, paths and every new
blob version, including intermediate versions. No object-size skip is treated
as inspected. Known public upstream ancestry is identified by exact commit and
is not freshly content-scanned. Wine/DXMT head histories contain 185,810 / 1,366
commits respectively, including downstream work; those totals are not fresh
content coverage counts. Existing Git objects and authorship are preserved.

Local Stage1 successors were separately reviewed: Wine
`6684cba19474dabbf6bdb5de4019427e0c958938`, DXMT
`28fe386342ae849e746564eae3ca94e9612bd912`, runtime
`17516d76d02d5ddd15d477bf5604cf7fda6be5b1`. Their changes are documentation and
bundled stage reports only; source and frozen inputs are unchanged. At the Stage2 snapshot they had not been pushed. Stage4 PR publication is
recorded below; none replaces default/build/tool refs. Wine/DXMT add four
Markdown blob versions (31,400 bytes), all scanned without findings. Runtime's
four-Markdown successor likewise passed its incremental content/path review.

## Privacy and remote exposure

No high-confidence private key/token, personal home path, tracked private-selector
payload, game binary, signing material or runtime payload was found in the bounded
downstream scans. Pattern findings were manually disposed: public source concepts,
exclusion rules, synthetic fixtures and deliberately invalid path tests are not
private operational records. Pattern absence is not a guarantee against every
encoded or novel secret. Raw matches/private operational records remain local.

At the Stage2 snapshot each repository had one private `codex/task56` branch and no tags. Final live
branch/privacy reads matched the initial pins. All four then had zero observed Issues,
comments, PRs, workflows, runs, Actions artifacts and releases, so there were no
listed logs/release payloads to inspect. FEX/runtime also reported zero Actions
caches. Wine/DXMT additionally reported zero deployments/environments. Wiki and
discussions are disabled in Wine/DXMT metadata; the Pages endpoint is unreadable
(404). FEX/runtime metadata report Pages/wiki disabled. Unreadable endpoints and
previously deleted/hidden objects are not asserted to be fully inspected.
Actions is enabled with read-default workflow token permissions.

No new workflow/settings were created. New runs, comments, artifacts or source
refs after the snapshot invalidate the corresponding exposure scope. GitHub's
visibility documentation is the operational reference for the eventual conversion:
[repository visibility](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility).

## Licenses, provenance and contribution boundaries

Wine upstream AUTHORS/LICENSE/COPYING.LIB and DXMT upstream LICENSE/LICENSE.OLD/
COPYING.LIB/CONTRIBUTING/AGENTS remain exact. Original README bodies remain intact
beneath the Pear prefaces. The 58 Wine and six DXMT selected manifest entries
match their declared bytes/modes. Mixed original MIT/LGPL/GPL terms remain
file-specific; no blanket downstream relicensing was performed. Historical
notice-check warnings remain recorded warnings, not a new automatic clearance.

DXMT's two inherited gitlinks are unchanged; their contents were not recursively
rescanned. FEX and DXMT upstream contribution restrictions remain intact. This
review makes no upstream submission or claim of acceptance. Public downstream
hosting is a separate decision from an upstream contribution.

### FEX generated-header notice finding

The exact affected files are `Pear/Diagnostics/include/PearMismatchObservation.h`,
`PearTargetObservation.h` and `PearWriterObservation.h`. Each matches the retained
MIT-marked source template/schema and the historical capture-to-import chain.
The first Git import is `52fd8a95955ad33cc589bcd8c5837b84cb21705e`; the original
Pear generator sources were untracked and have no demonstrated introducing Git
commit. Do not invent an original committed revision from a neighboring checkout.

Their template files carry `SPDX-License-Identifier: MIT`, but omit a copyright
holder line and the full permission text. The emitted headers omit inline terms;
the current adjacent import notice describes them as unmarked legacy bytes.
FEX's upstream LICENSE cannot silently supply the Pear template's copyright
holder. The same applies to a sibling runtime file's collective attribution.

The Stage2 prerequisite was to add reviewed adjacent provenance/notice documentation
that binds these exact output/template hashes, preserves all known notices,
records the absent original holder notice and reproduces the MIT permission and
warranty text without inventing ownership. Keep frozen header/import-manifest
bytes intact. This audit establishes MIT-marked template provenance; it does not
resolve absent attribution by assumption or claim blanket legal clearance.

## Conditions for a later public source release

1. Integrate the reviewed Task75 PRs, including the FEX notice successor below,
   then recheck the exact integrated refs. The old FEX default alone does not
   contain the correction.
2. Preserve the completed Stage3 delta review below; review any later successor separately.
3. Recheck all branch/tag heads and GitHub exposure surfaces immediately before
   an authorized visibility change; preserve component default branches until
   a separate branch-policy decision.
4. Update private/collaborator-only wording only when the actual switch occurs.
   Keep experimental support and retained-input requirements explicit.
5. Keep installed app/game/private state and existing candidate bytes separate.
   Source availability does not qualify the Rosetta-free player experience.

## Stage3 successor addendum — 2026-10-21

Runtime `db95ed3278d9d20233fbd395665f3d39c3a4b13d` adds the WGI adapter, sealed data recipe, synthetic tests,
existing recipe README update and bundled Stage3 report. The final five-file
delta passed notice, privacy-pattern/manual and whitespace review. The final
test-only change adds license comments to synthetic source fixtures; 43 guarded
tests passed again. Executed adapter/recipe bytes are unchanged from the successful
reconstruction. This local commit is READY WITH LIMITS under the same retained-input,
inherited-history and experimental-support boundaries. It was unpushed at the Stage3 snapshot; Stage4 publishes its
review PR without replacing selected runtime tools or candidate pins.

Final delta-review SHA-256: `990b954d3c333fff63624312b013921eefc0c9f53933ec3b8976cb10744b9251`.
The [WGI note](task_m1_75_wgi_binding.md) separates source reconstruction from
natural-call observation and gameplay. The new JSON is identity/action data
with separately reviewed provenance, not an inline SPDX-compatible source format.

A final read at 2026-10-20T15:14:07Z confirms all four private remote branch heads,
default branches and absent tags still match the table above. This does not
relabel the earlier dated exposure-surface inventory as newly rescanned.
Downstream author/committer identities were separately compared with public
Pear history at `2c151f1d074fab5a55bc2d77e25b5fb81aedc257`; no newly exposed
identity was found. No raw personal identity is exported in this note.
FEX's adjacent-notice prerequisite was still open at this Stage3 snapshot;
the following Stage4 addendum supersedes that current disposition.

## Stage4 notice and PR successor review — 2026-10-21

All four reviewed successors are READY WITH LIMITS for a later source-visibility
decision. They are published as private, open review PRs. The existing default
branches remain `codex/task56`; each PR uses `codex/publish-task75`. No merge or
visibility conversion has occurred.

| Repository | Reviewed PR head | Review |
|---|---|---|
| Wine | `6684cba19474dabbf6bdb5de4019427e0c958938` | [PR #1](https://github.com/postmelee/pear-wine/pull/1) |
| FEX | `97a52dd11128ffc866a127dc43fdca9e8a1c5dd9` | [PR #1](https://github.com/postmelee/pear-fex/pull/1) |
| DXMT | `28fe386342ae849e746564eae3ca94e9612bd912` | [PR #1](https://github.com/postmelee/pear-dxmt/pull/1) |
| Runtime | `db95ed3278d9d20233fbd395665f3d39c3a4b13d` | [PR #1](https://github.com/postmelee/pear-runtime/pull/1) |

FEX `97a52dd11128ffc866a127dc43fdca9e8a1c5dd9` changes three Markdown files only:
`Pear/Diagnostics/include/NOTICE.md`, its existing README link and the bundled
Stage4 report. The notice binds three exact header outputs to six retained
MIT-marked sources, discloses the missing original holder/introducing-commit
information and reproduces the MIT clauses without inventing attribution.
It includes the later 56-byte target-header addition. All 99 imported source
identities/modes, 42 retained origin references and 17 protected metadata/source
paths were verified; the frozen headers and manifests remain unchanged.

Independent final notice review:
`becf12c57ca66f35cb8c8b4aa40670e0b87e61c47bba9fb0eb4a87c4831f66d1`.
This resolves the specific documentation prerequisite on the reviewed successor;
it does not manufacture missing authorship or provide exhaustive legal clearance.
The dated detail JSON and Stage1–3 reports remain unchanged.

A fresh prepublication inventory at 2026-10-20T15:28:54Z verified all four private
defaults and zero listed workflows/runs/artifacts/caches/releases/Issues/PRs/
comments/deployments/environments. Its receipt is
`1c2d834c99af81f3858a10aeaa3bbc214a08afce4a30197897060a787c2a35c1`.
The [Stage4 report](../working/task_m1_75_stage4.md) records the separate
post-publication check, new branch/PR surfaces and CI availability. A new PR is
new reviewed remote content, not evidence that the earlier zero-count snapshot
still describes the repository.

The unchanged runtime adapter, recipe, tests and Stage3 receipt were rejoined
before reusing the 43-test/build evidence. No runtime result was rerun or
broadened by this documentation-only extension. Public source access still
requires a separate requester decision after reviewing these findings, plus a
fresh check of the actual refs and surfaces immediately before conversion.

## Evidence and limits

The [sanitized FEX/runtime detail](task_m1_75_publication_details.json) retains
exact source/output hashes, manual dispositions and coverage limits. The JSON is
investigation data, not executable source or a notice replacement. Exact raw
local records remain private; their identities are:

| Evidence role | SHA-256 | Bytes |
|---|---|---|
| `wine-dxmt-public-readiness.md` | `2310df72ab7848fc02c0ddb606abe3a70f5acbbf6c116e69735884be8c092e3d` | 8481 |
| `task75-stage1-readiness-addendum.json` | `2c40e5feacca7310eacf1f37a49dae4166a062e1dd704d90a06cdcaf210cf962` | 5492 |
| `findings-public.md` | `3fd74e68c2f01809a22eb9b3697ea28f026cd64fdac54299a2f86aa09e78f8cc` | 4156 |
| `readiness-public.json` | `16b58a29f3d2e9e71a186ed7b65d91203d16ac48fd84e42b7a7b090e699c91d7` | 10763 |
| `legacy-header-origin-private.json` | `e9bc1efef2b586704e0506ce0ff7c7c18a259372eebd6bf7e00c61368740caee` | 29245 |

Evidence is content-addressed locally. Public summaries omit personal absolute
paths, private selectors, game data and raw diagnostics. Source inspection,
synthetic tests, historical controls and actual gameplay retain separate claims.
