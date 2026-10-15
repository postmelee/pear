# Task #48: Artifact Retention Reuse Assessment

Reviewed: October 11, 2026. Issue: [#48](https://github.com/postmelee/pear/issues/48).
Status: dated source/receipt review for the approved [implementation plan](../plans/task_m1_48_impl.md). This is not a new cleanup, recovery test or runtime qualification record. The reusable operating policy is the [retention manual](../manual/artifact_retention_guide.md).

## Existing Work and Reuse Decision

Reuse Pear's existing task documents and Hyper-Waterfall v0.3.0 manuals/templates/skills rather than introduce a storage subsystem, separate reporting framework or automatic cleanup service. The installed framework attribution remains upstream commit `83836828a4da24385d0410515d35ee43946b981f`; the Pear source baseline is `d01f5264cca305649fbf7df488b1dd7badaa5b80`. No upstream subsystem code is imported and no language rewrite is involved.

The [architecture](../../docs/architecture.md) already separates immutable runtime payloads from private mutable state. The [dated verification-reuse investigation](20261004_recompilation_and_verification_reuse.md) requires input-bound reuse and preservation of approved checks. The completed [#5](../report/task_m1_5_report.md), [#6](../report/task_m1_6_report.md), [#7](../report/task_m1_7_report.md), [#8](../report/task_m1_8_report.md) and [#40](../report/task_m1_40_report.md) reports preserve exact reconstruction, failure and downstream input boundaries. A merged producer therefore does not make its ignored artifacts disposable.

The missing reusable piece is explicit ownership, consumer/recovery dependencies, output-space planning and release events. Add those through one internal manual, concise agent obligations and later template/skill hooks. Preserve fresh reconstruction and affected-input revalidation; retention documentation alone does not justify another native matrix.

## Local Source Identities

Existing maintenance records were read from the primary checkout's ignored `.build/storage-maintenance/20261010-completed-tasks/`. Relative names below identify local evidence, not downloadable repository artifacts. SHA-256 values identify the receipt bytes read during this review; hashing a receipt does not freshly verify the files or behavior it describes.

| Local record | SHA-256 |
|---|---|
| `final-verification.json` | `7dcbd53fb1e129a92ef37274409090a21c77c032afac5dfb0226f8c8ab4bcda1` |
| `protected-verification.json` | `8fb94116da2c606fc97fee2cf2da7ddd28ad5c0c4e93ef4665bfa77e718b1ea6` |
| `restore-roundtrip.json` | `2681eb84f4dcc1168c1a8745a5930d02e8beff7719319378e80c606f1f91dead` |
| `followup-survey/survey.md` | `2d98f5a818850d723fc8c936b72126fc4619be624d2a11f4b115ab8deb674d83` |
| `followup-survey/task5-sizes.json` | `14531506e3e9a0b548e6ef5d6d9e2dc2559a3128c8e62092cc67a7458d6ef038` |
| `followup-survey/task8-sizes.json` | `b5a70ab6d116108ade107b3a042e5e6f64a4f2d7062801c01cd0240f3f8ad55b` |
| `followup-survey/residual-references.json` | `2b375f73e50c29290e3f96364571ef0ee88498989bdbfd34d1ad52bf3a2ea9be` |
| `followup-survey/policy-proposal.md` | `8d9d8993d4116ee46e19e0081f0ecc6cbfe711aa21e55e56a062974d2d990593` |

Keep the original receipts, protected inventories, per-root archives, restore tool and `content/` store in place. Original locations expose `COLD-ARCHIVE.json` recovery instructions. #48 does not copy or remove these dependencies. The approved proposal is design input; the repository manual is the normative text once integrated.

## Historical Maintenance Observations

The final receipt completed October 10, 2026 at 14:42:34 UTC (23:42:34 Asia/Seoul). It records:

| Observation | Recorded result | Limit |
|---|---:|---|
| Historical runtime bundles archived | 49 | Required final/active consumer inputs excluded by that operation |
| Terminated synthetic prefixes archived | 25 | Not permission to archive authenticated or active prefixes |
| Archived file metadata verified | 156,287 | Historical check; not all possible metadata or current availability |
| Unique payload digests verified | 5,630 | Recovery-store content is a continuing dependency |
| Protected file digests verified | 31,902 | Matching receipt reports no mismatches; not a new scan |
| Actual in-place restore demonstration | 872 files | One recorded prefix round trip, not all archived roots restored |
| Git temporary files removed | 13 | Reported allocated bytes removed: 3,958,263,808 |
| Filesystem free space before / after | 16,038,531,072 / 22,663,565,312 bytes | Concurrent Pear work continued |
| Observed net free-space increase | 6,625,034,240 bytes, approximately 6.17 GiB | Not exclusive cleanup attribution or a promise based on displayed sizes |

The restore receipt has state `restored` and 872 file entries. It describes an earlier restore demonstration; it does not establish that those original bytes remain restored now. The final receipt distinguishes 74 archived roots and unchanged case records. No archive payload, protected runtime or restore operation was reverified during this stage.

## Residual Inventory and Dependency Limits

The October 10 survey used `du -k -d 1` and pathname groups. Its displayed allocations were:

| Root/category | Displayed size | Interpretation |
|---|---:|---|
| #5 total remaining | 94.39 GiB | Includes the following groups; do not sum again |
| #5 integration prefix templates, 24 directories | 39.41 GiB | Parent/source-case identities require tracing |
| #5 build/tool/component-named directories, 111 | 24.39 GiB | Includes reconstruction inputs and historical objects |
| #5 source/input-named directories, 139 | 3.22 GiB | Names do not prove duplicate contents |
| #8 total remaining | 36.28 GiB | Includes protected graphics and game-related contexts |
| #8 other runs/runtimes/evidence group | 34.69 GiB | A survey category, not a release list |

The survey records #5 `stage6-wine3` and several `stage3-wine-build` directories as mixed source/object/install/provenance inputs. Prefix templates bind runtime identity, source cases, inventory/overlays and sometimes parent-template hashes. The #8 survey finds references to `device15`, `device8`, `rendering5`, `pairing6/10` and `presentation1`; the #40 handoff uses `device15` as a seed. These are reasons to inspect dependency closure, not proof that every textual mention is active. No-reference results also cannot exclude dynamic consumers.

A later cleanup proposal would need a bounded candidate list, current transitive consumers/process state, protected identities and recovery-space checks. This stage performs no new whole-worktree scan or deletion. Existing games, private state, original failures and recovery stores remain protected.

## Integration and Verification Consequences

On October 11, #10/#11/#46/#47 are still open. Their worktree diffs show no overlap with this stage's root policy, manual or research file. #46 also has an October 11 board; preserve its row when integrating the independently edited board. No changes or messages were sent to those tasks. #11's Dock work continues independently; neither this policy nor bridge comparison becomes a new runtime prerequisite.

The existing governance checker is reusable for its limited routing/inventory scope. It does not cover all internal documents by default, so #48's approved supplemental check covers changed Markdown destinations and discovery symlinks, with manual review of parser limitations. Stage 1 validates policy text and historical-source consistency. Stage 2 owns template/skill wiring; Stage 3 owns the complete eight-scenario and acceptance review. No automatic enforcement, new storage savings, bridge implementation or WoW64 implementation is claimed.
