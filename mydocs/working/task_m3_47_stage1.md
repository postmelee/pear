# Task #47 Stage 1: Pinned Rosetta Steam entry point

GitHub Issue: [#47](https://github.com/postmelee/pear/issues/47)
Implementation plan: [task_m3_47_impl.md](../plans/task_m3_47_impl.md)
Stage: 1 — complete; Stage 2 awaiting requester continuation.
Date: October 11, 2026 (Asia/Seoul)

## Stage Purpose

Select and reproduce a small app/CLI that prepares official Windows Steam and
launches owned Megabonk normally on the declared Rosetta configuration. The
requester's later approvals also included public onboarding, branding, a reviewed
catalog, replacement-runtime provenance and signing/notarization preparation.
This stage establishes a working local candidate, not a public release or M1.

Context used: [task plan](../plans/task_m3_47.md), its approved location judgments
and extensions, root/docs/tests rules, task/Git/document-location procedures,
`task-stage-report` and `todo` skills, the primary checkout's artifact-retention
procedure, and the [reuse record](../tech/task_m3_47_reuse.md). The task worktree
predates the retention manual, so the current primary copy was read without
importing unrelated framework changes. Issue #47 remains open. #11 and #46 were
inspected read-only; no native-runtime completion is a dependency of this preview.
Only conflicting resource-intensive runs on the same Mac need sequencing.

## Artifacts

| File or group | Change summary |
|---|---|
| `preview/src/`, `Cargo.toml`, `Cargo.lock`, `build.rs` | Shared Rust setup/verification/Steam entry; versioned runtime pin, isolated private state and bounded commands |
| `preview/Launcher.swift`, `build*.sh`, `package.py` | Thin AppKit window, supplied icon, signed app/CLI packaging and explicit allowlist |
| `preview/runtime_{build,package,sign,validate}.py`, input lock, patch and fixtures | Reconstructible Wine/helper candidate, dependency inventory, narrow signing policy and synthetic execution checks |
| `preview/THIRD_PARTY_NOTICES.md`, `runtime-notices/`, `licenses/`, root `LICENSE` | GPL-3.0-or-later for original Pear code; preserved component terms, pinned source and 127 runtime notice files |
| `manager/Cargo.toml`, `tests/cpu/LICENSE-MADEIRA-EXCEPTION.md` | Pear package license metadata and preserved existing fixture permission; no manager runtime-admission implementation change |
| `.gitattributes` | Exact-path whitespace exceptions for 26 verbatim notices and one pinned unified patch; all other source keeps whitespace checks |
| README and official `docs/` entry points | Preview/native contribution paths, Diataxis navigation, release/help/security/community guidance and bounded current status |
| `.github/` templates/workflows | Player and contributor intake, preserved internal PR template, gated catalog publication and server-side Steam metadata snapshot |
| `tools/compatibility.py`, `tools/steam_catalog.py`, `tools/catalog/`, `docs/compatibility/` | Reviewed App-ID-based records, local catalog/report/download UI, searchable public Steam identities; GitHub remains request/vote authority |
| [Observations](task_m3_47_stage1_observations.json), plans, reuse record and daily board | Sanitized chronological outcomes, current completion summary and retained failure boundaries |

## Body Change Scope / Lossless Preservation

All product-document locations were approved in the plan or explicit onboarding
extensions. `docs/` remains the official root and delivery-plan.md the single
roadmap. Earlier private experiments and other tasks' checkouts are unchanged.
Historical failures remain in observations; later success does not rewrite them.
The original task criteria are retained despite the expanded Steam-library entry.

The final launch correction removes the generated private `Steam Preview.app`.
Putting a signed standalone Wine executable inside that new unsigned bundle caused
macOS to reject its resource seal. Reuse of pinned Wine `start /unix` starts the
exact official Steam executable through the original notarized loader; no `/wait`
is used for the client lifetime. No runtime bytes, permissions, game executable,
Steam API or ownership checks were changed by this correction. The failed helper
and private state were preserved. Pear's default opens the library; `megabonk`
explicitly requests owned installation and normal Steam `-applaunch`.

The current app resources and runtime source kit remain frozen. Public documents
now distinguish the accepted local candidate from unavailable public downloads;
archival component notices inside the frozen packages were not edited in place.

## Verification Results

Execution context: M4 Pro, 24 GB, macOS 26.5.2 (25F84), ARM64 Pear launcher/CLI,
Rosetta Wine 11.0 from the CodeWeavers 26.3 source input, DXMT 0.80. Build evidence
uses Rust 1.94.1 and Swift 6.3.3. Original upstream languages/build systems are
retained. Source/fixture/host/game/distribution results are distinguished below.

### Required Stage 1 cases

| Case | Result and evidence boundary |
|---|---|
| S1-identity | Passed. Runtime archive and source-kit pins below; all 33 recorded corrected-GUI inputs still match. Source kit has 11 pinned inputs, 127 notices, 15 recipe/license files and two generated instructions/maps, all compared with current inputs. DXMT/MoltenVK are pinned upstream binaries with source references, not claimed independently rebuilt. |
| S1-isolation | Passed. Task-owned state; existing authenticated environments preserved. CLI rejects a foreign runtime prefix before Wine starts and preserves its save sentinel. No private state is in the staged files. |
| S1-security | Passed for local candidate. Runtime's 45 Mach-O notarization requirements and corrected app/CLI policy checks passed. Only the two explicitly approved Wine loaders have unsigned-executable-memory and disable-library-validation exceptions. App/CLI and the other 43 images receive no such exception. No Gatekeeper/quarantine bypass. |
| S1-steam | Passed. Corrected notarized app displayed official login, owner authenticated, and signed app-bundled CLI installed App 3405340, build 21750826, StateFlags 4. Download 179,240,512 bytes; staged 522,734,781 bytes. |
| S1-play | Passed. Normal Steam launch; current game log recorded `Steam initialized`, Direct3D 11.0/feature 11.1 and Apple M4 Pro. Owner confirmed normal menu/input and normal exit. Selected DXMT pairing/inventory is retained. No direct-executable fallback or shipped steam_appid.txt. |
| S1-cleanup | Passed. Normal Steam shutdown and Pear window close; 19 pre-cleanup owned identities plus game/guard absent, no state/app handles, guard exit 0 and shared interval released. Older private server preserved. |

Steam self-updated in the owned environment. Its exact client build number was
not captured in the sanitized current-run evidence and remains unknown; the
Megabonk build is recorded. This limits later reuse after Steam updates.

### Frozen candidate identities

All paths below are relative to ignored `.build/task47/`; no binaries are committed.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `integrated-signing-v2/pear-runtime-signed-v2.tar.gz` | 534424618 | `bf660c1ddf0a40cd2c7e345343b32f6515bf34c1fe6566aae337302f221a4127` |
| `integrated-signing-v2/pear-runtime-source-kit-signing-v6.tar.gz` | 204187222 | `61e7f41f4644c49061e485e3149cc0cc0ee33b4e58aaf417dd6380630b930fbe` |
| `loader-handoff-v3/submission/Pear-0.1.0-preview.1-macos-arm64.zip` | 5308934 | `bb2fa78cade589dcdfb7a20845413675fd80e916873dbf1a8c4fbde649e3e006` |
| `loader-handoff-v3/submission/pear-preview-0.1.0-preview.1-macos-arm64-cli.zip` | 343245 | `1a5c85d9ef791d6d87209d36c2936543c67c658d79e6b34c6cbe4005e984c003` |

The submission app ZIP predates stapling and is not the final downloadable ZIP.
The tested app at `loader-handoff-v3/Pear Preview.app` is stapled. Runtime ID:
`pear-wine11-cw26.3-dxmt0.80-signed-v2`. Apple Accepted submission IDs:

- Runtime: `0835e086-ae8c-4524-a509-5c56073681fb`.
- Corrected app: `d85a8ee3-13dc-4dfa-99e1-389c2436414d`.
- Corrected CLI: `18c4759c-5f60-4e3b-b27f-25754a31e975`.

Final GUI receipt `loader-handoff-v3/gui-validation/whole-release.json` SHA-256:
`32926f3a366d76c022fe8be29e758741c3a52c4dab1e00c4ffbd751783f33f1d`.
Its nine referenced receipt/readiness/policy files were rechecked. Raw initial
attempt metadata remains unchanged; the final receipt is authoritative for the
completed sequence. Sanitized outcomes are in the tracked observations.

### Automated closure checks

Commands run from `codex/task47`:

```sh
sw_vers
uname -m
df -h .
python3 -B tools/check_governance.py
python3 -B tools/compatibility.py --check
python3 -B -m unittest discover -s tests/docs -p 'test_*.py' -v
node --test tests/docs/test_steam_search.cjs
python3 -B -m unittest discover -s preview -p 'test_*.py' -v
git diff --check
```

Final checks passed: governance 37 documents/354 local targets, one reviewed catalog
record, 72 documentation/catalog tests, six JavaScript identity/search tests and
34 preview packaging/build/signing/validator tests. GitHub YAML syntax passed. Initial staged whitespace validation flagged 26
verbatim notice files and the unified patch context. Exact-path Git attributes
preserve these hash-checked inputs without changing their bytes; the final staged
check passes and Pear-authored source retains normal whitespace checks.
An additional changed-document check passed 25 Markdown files/180 local file
targets and parsed nine JSON files. Two preserved internal PR placeholders
(`stage-url`, `commit-url`) were excluded after the generic scan initially treated
them as paths; actual file links passed. This does not check remote URLs or anchors.
App deep/strict signature and CLI explicit notarization requirement passed again
without execution. Logs and hash manifests: `.build/task47/stage1-closure/`.

Evidence reuse: the exact unchanged v3 Rust source passed 13 tests and its release
build before signing; `loader-handoff-v3/step-0.log` retains output, including the
existing unused `pear_process_identity` warning. The original-loader argument,
spaced-path, preservation and failure regression passed. No fresh Rust/Wine build
or game run was needed to write this report. Signed-v2 synthetic AES/font/TLS,
wrong-host rejection and actual owned-Wine-PID helper mapping were previously
verified; modified-runtime/corrupt-archive/foreign-prefix CLI checks also passed.
The source-kit contents were compared again; this is not another reconstruction.

Earlier actual replacement-runtime trials received owner confirmation of extended
play/audio and save/relaunch (sniper enabled, purchases retained, balance 296).
Their precise active duration was unmeasured and their app/signature inputs differ;
they are historical observations, not final-package gameplay qualification.
Website desktop/mobile review and subsequent requester approval remain valid for
unchanged catalog UI. No public deployment or new visual approval is claimed.

The old Whisky DMG commands apply to the superseded GUI candidate and were not
rerun: the authorized replacement selection and closure command mapping are in
the implementation plan. Required security/Steam/menu cases were preserved and
passed on the selected artifacts. Remote CI has not run for this entire stage.

## Artifact Disposition

| Artifact/root | State, consumer and release condition |
|---|---|
| Source, locks, patches, notices and task records | Retained authoritative Stage 1 inputs; commit with this report. Later source/package assembly consumes this revision. |
| `loader-handoff-v3` | Retained candidate/evidence for Stage 2 and final packaging. 11,921,699 logical bytes / 12,054,528 stat-allocated bytes. Release superseded packages only after replacement and evidence review. |
| `signed-runtime-v2/Libraries` | Retained immutable runtime: 1,558,908,079 logical / 1,562,882,048 stat-allocated bytes. Required signing/recovery reference until final accepted replacement. |
| Signed runtime archive and source kit v6 | Retained pins above; allocation respectively 534,425,600 and 204,189,696 bytes. Keep together through release/source correspondence review. |
| `integrated-signing-v2/state` and earlier authenticated prefixes | Retained private login/game/save dependencies for recovery and qualification; not traversed in this closure, not copied or staged. No automatic deletion at stage completion. |
| Failed signed-v1 and generated-helper evidence | Historical unique failures. Retain small receipts and required reproduction inputs until next-stage/final failure review; no success inferred from failed runs. |
| `integrated-runtime-v1` old installed unsigned copy | Previously released, restore-required from its preserved 533,646,314-byte verified archive. Restore and revalidate before reuse; not an available installed runtime. |
| Earlier build intermediates and synthetic prefixes | Previously released after their owned-process and preservation checks; no reclaimed bytes counted again. |
| Closure logs | Small text evidence, retained through stage review/final report. No full runtime copy or substantial build created. |

Current measured filesystem available space: 8,395,681,792 bytes; no cleanup was
performed in this closure, and concurrent activity prevents attributing changes.
Logical and stat-allocated amounts are separate, not promises of APFS recovery.
Private-state size was not newly measured. The worktree remains required for
ignored evidence and subsequent work; a Git commit alone would not preserve it.

## Residual Risks

- Stage 2 interruption/retry, insufficient-storage, failed-update, repeat app
  launch, backup restoration and removal/reinstall cases remain required.
- Measured 20-minute play/input/audio/save on final artifacts, second clean setup
  and real downloaded-artifact execution under normal protections remain pending.
- Runtime URL is intentionally unset. Final DMG/app/CLI and corresponding sources
  are not published; final packaging must occur after stapling and bind a commit.
- Identified notice comparison is complete for this candidate; release matching
  and accessible source delivery remain. Upstream DXMT/MoltenVK binary source
  references do not claim byte-identical independent reproduction.
- Steam updates may invalidate observations. CEF sandbox enforcement, other
  games/Macs, controllers, overlay, achievements and Steam Cloud are unqualified.
- Public visibility, Pages, default-branch forms and private reporting activation
  remain separate publication steps. Existing catalog records remain dated results.

## Impact on Next Stage

Use the frozen candidate above for the approved Stage 2 scenario matrix. Reuse
valid rejection evidence, but do not treat a synthetic sentinel as actual save
restoration. Keep original and pre-restore progress recoverable. Start with
lightweight source/seam inspection; coordinate only actual conflicting host runs.
Neither #11 nor #46 must finish before #47 can proceed. No runtime/security policy
change or public-release admission follows from this stage report.

## Approval Request

Review these Stage 1 artifacts and results. Explicit continuation authorizes
Stage 2 setup/recovery/save-preservation work; Stage 3 and public publication
remain subsequent gates.
