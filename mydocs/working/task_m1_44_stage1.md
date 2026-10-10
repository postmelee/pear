# Task #44 Stage 1: Route requirements and retained evidence

GitHub Issue: [#44](https://github.com/postmelee/pear/issues/44)
Implementation plan: [task_m1_44_impl.md](../plans/task_m1_44_impl.md)
Stage: 1 — Establish route requirements and evidence inputs
Date: October 10, 2026 (Asia/Seoul)

## Stage Purpose

Separate actual required Dock i386 helpers from full Windows Steam bootstrap/desktop requirements, bind reused inputs to exact identities and establish the limited native-bridge comparison criteria. The requester's continuation after `1aaf86e` approved this research stage only. Stage 1 does not select or implement WoW64 or a bridge.

Context used: the [approved plan context and locations](../plans/task_m1_44.md), root/scoped rules and official documents listed there; latest merged #40 reports; retained #11 Stage 1/October 10 priority and diagnostic/reuse records; newly shared #11 step2a/component/no-account assessment. The [task-stage-report skill](../skills/task-stage-report/SKILL.md) and central technical-note/stage-report templates govern reporting. The repository's `codex/task44` rule overrides the framework's example branch prefix. Metal technical guidance is not applicable to source-only PE/Steam research.

## Artifacts

| File | Change Summary |
|---|---|
| [Research note](../tech/task_m1_44_reuse.md) | Two-route/phase matrix, conditional services/ownership findings, original installer and parser limits, native-bridge criteria and unknowns |
| [Stage 1 observations](task_m1_44_stage1_observations.json) | Exact source/artifact/reader hashes, actual comparison counts, first inspection correction, static headers and allowlisted new peer evidence |
| [Task plan](../plans/task_m1_44.md), [implementation plan](../plans/task_m1_44_impl.md) | Approval/status and dated peer evidence/integration-order update |
| [Daily board](../orders/20261010.md) | Only #44 row advanced to Stage 1 complete / Stage 2 continuation pending |
| This report | Actual verification, limitations and Stage 2 approval boundary |

Task-owned ignored evidence: `.build/task44/stage1-intake1/` contains both reader versions, initial/corrected inspection results and logs, the peer-update reader/result and verification logs. `source-review/stage1-retained1/` and `stage1-retained2/` each preserve 115 public files; total 3,818,620 bytes. No proprietary payload, authenticated state or peer cache was copied or edited.

## Body Change Scope / Lossless Preservation

All six tracked files match the approved `mydocs/tech`, `mydocs/working`, `mydocs/plans` and board locations. Existing plans retain their research scope and stage ordering; the dated update names newer evidence without replacing old input identities. The #40 board row and all other task artifacts are unchanged. No official `docs/`, runtime/host/test/tool source, workflow procedure, source lock, private input or another worktree is edited.

The new #11 evidence changes selected-file classification, not its dynamic necessity. The selected original `bin/SteamService.exe` is i386, while actual required execution for Megabonk remains unknown. The no-account Dock failure reached genuine client interfaces and then reported an x64 FEX stale-identity guard; it does not demonstrate that i386 caused the failure. #11's independent direct-game timeout diagnosis stays with its owner. No message or implementation is sent back to another task by this stage.

## Verification Results

Execution context: Darwin/arm64, Python 3.14.4, Git 2.53.0, worktree branch `codex/task44`, starting HEAD `1aaf86e9c7f8223bd5f1e4f250b1112d12e31b6d`. This is read-only source/hash/header inspection and document verification. Compiler/signing/runtime authority was not tested or used. No native lock was taken.

Evidence reuse: 131 actual expected-digest comparisons passed after correcting one reader field mapping; 115 cover retained public source files. Parser binary, harness, experiment and fixture producers, observations, fixtures, exact installer, baseline parser sources/build/config and #40 receipt still match. Four parser stdout files match their historical diagnostic strings. This permits reuse of the original parser claims only; it is not current parser execution, complete toolchain validation or PE32/game qualification. The first reader incorrectly mapped the experiment copy to the fixture-producer hash, raised an assertion and was corrected using the retained producer's field definitions. Both attempts and hashes remain visible; no source mismatch was hidden.

The supplementary reader checked three newly shared #11 receipt hashes, all 59 static inventory rows across the two receipts, and equality of all bootstrap assessment fields. Selected payload architectures/imports and execution outcomes are reused #11 observations, not newly measured by #44. The original SteamSetup headers were independently decoded from their unchanged bytes, with bounds checks and no execution. The observations identify both reader hashes and the explicit source inputs.

Read-only inspection commands (owner aliases below replace local worktree-root arguments only; all switches and task-local paths are shown):

```sh
python3 -B .build/task44/stage1-intake1/inspect_stage1_v2.py --task11 '<task11-worktree>' --task8 '<task8-worktree>' --task40 '<task40-worktree>' --output .build/task44/stage1-intake1/checks2
python3 -B .build/task44/stage1-intake1/inspect_peer_update.py --task11 '<task11-worktree>' --output .build/task44/stage1-intake1/peer-update.json
```

Each owner alias means its existing named `pear-task{N}/New project` worktree, with artifact-relative paths and exact expected hashes in the observation ledger. Both corrected commands returned zero. Their stdout is preserved as `inspection-v2.log` and `peer-update.log`; the initial `checks1/inspection.json` preserves the rejected mapping. No retained parser/producer was executed or imported.

Common commands run exactly as planned from #44:

```sh
git status --short --branch
git log -1 --oneline
python3 -B -m json.tool mydocs/working/task_m1_44_stage1_observations.json > /dev/null
python3 -B tools/check_governance.py
git diff --check
git diff --name-only
```

Results before writing this report: every command exited zero; governance reported `PASS: 27 documents, 268 local targets; skill routing and source inventory consistent (offline)`. The initial status showed only the intended plans/board modifications and two new Stage 1 artifacts. `git diff --name-only` omits untracked files, so status and the later explicit staged-file review are both required. The exact command output is retained in `verification-before-report.json`.

Additional review passed: all 23 local links then present in the note/plans resolve; all eight technical-note template headings exist; 115 task-owned public snapshots rehash correctly; the observation JSON contains no user-home paths, selection files, token values or private material. Manual review rejects installer-to-all-routes, x64-to-all-helpers, installed-to-required, parser-to-guest, old-to-current-inventory, exit-zero-to-SCM-ready and macOS-Steam-to-working-bridge inferences. The actual compiler hash is retained historical metadata only. These checks verify the research artifacts and claim boundaries, not runtime compatibility.

After writing the report, JSON/governance/whitespace checks passed again; all 34 final local links and seven stage-template sections passed. Explicit staging contained exactly the six approved files, and `git diff --cached --check` passed. Outputs and the staged-file list are retained in `verification-after-report.json`.

Unperformed: new native compilation, parser/guest/Steam/game execution, low-address experiments, authentication/session access, complete process/module architecture qualification, signing and all bridge implementation/tests. The source/function-contract comparison belongs to Stage 2. No CPU/graphics suite is rerun for unchanged runtime code. Failed #11 bootstrap and historical #40 timeout remain failures, even though their receipt-consistency checks pass here.

## Residual Risks

- Static i386 service identity does not settle actual CEG/prerequisite use. The selected Wine service-manager image and complete required helper closure remain unknown.
- #11's stale-identity result has multiple possible source predicates and no demonstrated connection to the separate direct-game timeout. This stage establishes no cause and implements no fix.
- Peer working documents can change; later work must use these exact receipts or separately inspect updated inputs. Receipt agreement is not a replay of the original build/execution.
- Existing native bridge source availability, ABI/callback/session coverage, full Rosetta-free host closure, per-component terms and maintenance cost remain unresolved until the bounded Stage 2 comparison.

## Impact on Next Stage

Stage 2 can use the stable source ledger and explicit helper/source conditions to compare complete Wine/FEX WoW64 and existing macOS Steam bridge contracts. It must preserve all five bridge criteria and distinguish source declarations from actual Windows-game evidence. A substantial shared loader/memory/ABI proposal waits for this comparison; #11 does not.

If later implementation overlaps LookupCache/OvercommitTracker/owner/ntdll, record concrete files and preimages and consume the accepted #40 baseline before any separately reviewed #11 correction and subsequently approved #44 correction. This is a conditional integration order, not adoption of a pending patch or an implementation grant.

## Approval Request

Review these Stage 1 artifacts and approve **Stage 2 only**: read-only function/dependency and existing native-bridge contract comparison. The [stage-report procedure](../skills/task-stage-report/SKILL.md) says, “Enter the next stage without task requester approval” under Never Do; the approved plan and root rules require explicit continuation after this verified report/commit. No runtime/bridge implementation, native experiment, publication or Issue closure is requested.
