# Task #1 — Source qualification implementation plan

Task plan: [task_m1_1.md](task_m1_1.md)
GitHub Issue: [#1](https://github.com/postmelee/pear/issues/1)
Milestone: M1

Status: the task requester approved this implementation plan and Stage 1 on September 28, 2026 by explicitly instructing work to proceed. Stage 1 is complete; its actual verification and limits are recorded in ../working/task_m1_1_stage1.md. Stage 2 awaits approval. Later stages retain separate report approval checkpoints; planned commands for unstarted stages are not passing results.

## Stage Overview

| Stage | Title | Main Output | Verification |
|---|---|---|---|
| 1 | Identify and acquire source inputs | Initial source inventory and acquisition evidence | Resolved immutable objects, measured input hashes, dependency coverage |
| 2 | Audit source coverage, patches and terms | Requirement/gap and license/provenance records | Claims bound to inspected sources; existing patch applicability |
| 3 | Pin tool inputs and validate inventory | Candidate toolchain inventory, bounded validator and tests | Reference/checksum failures, valid incomplete records, readiness distinction |
| 4 | Repeat acquisition and decide | Reproduction evidence, contributor guide, final decision | Fresh input verification; three acceptance criteria mapped |

## Document Location Check

| Artifact | Task-plan location | Stage artifact path | Match | Notes |
|---|---|---|---|---|
| Factual source inventory | `runtime/sources/manifest.json` | Same | OK | #1 audit data; not #3's runtime lock |
| Inventory validator/tests | `tools/sources/`, `tests/sources/` | `tools/sources/validate_inventory.py`, `tests/sources/test_inventory.py` | OK | Provenance, references and local content verification only |
| Contributor guide | `docs/source-qualification.md` | Same | OK | Instructions, inspected scope, source decision and limits |
| Historical audits/index | Existing `docs/research/` audits and `docs/README.md` | Same | OK | Coordinator applies narrow dated links; preserve original findings |
| Stage evidence/reports | `mydocs/working/` | `task_m1_1_stage{N}.md` and `task_m1_1_stage{N}_evidence.json` | OK | Sanitized work records, not product qualification |
| Final report | `mydocs/report/` | `task_m1_1_report.md` | OK | Audit acceptance and downstream obligations |

All acquisition caches, Git repositories, archive bytes, scratch indexes and raw logs stay under `.build/task1-sources/` in the #1 worktree. Stages 1–3 share a stable `inputs/` root containing all acquired source, submodule, archive and patch bytes; manifest content paths are relative to that root. Stage-specific logs and scratch indexes stay in separate `stage{N}/` directories. Repeat acquisition uses `reproduction/inputs/` with the same relative content layout, preserving the original inputs. No shared cache with #3 is assumed. Existing `/.build/` exclusion is sufficient. The coordinator owns shared board/index/audit edits.

## Data, Ownership and Decision Rules

The inventory has a local `schema_version`, `record_kind: source_audit`, audit date/scope, component records, requirement/gap records, evidence references, `audit_complete`, and a decision. Stage 1 uses `audit_complete: false` and `decision: unassessed`; final outcomes are `go`, `needs-port` or `blocked`. This is a bounded inventory format, not another runtime-lock schema.

The agreed logical handoff to #3 is component ID/role/dependencies; source URL and immutable ref; typed content digest and scope; ordered patch/base/provenance; toolchain/SDK/host-versus-guest targets; license/notice/contribution references; evidence/date/inspection scope/status. #3 owns mapping these facts into product contracts. Its fixture work does not depend on #1 completion; #1 does not wait for product schemas to record verified facts.

Required identity rules:

- A Git source records its canonical URL, full commit object ID, Git object format, root tree object ID and required gitlink/submodule records. Record the candidate-selection reason separately from identity. Historical commits and moving refs remain leads until newly resolved, acquired and inspected.
- Git object IDs are typed Git identities, not SHA-256 file digests. Capture `git ls-tree -r -z --full-tree <commit>` bytes and their SHA-256 with scope `git_tree_listing_bytes`; this hashes the listing of modes/paths/object IDs, not concatenated source contents. `git fsck` and object checks verify available objects separately.
- Downloaded archives retain SHA-256 of exact downloaded bytes, archive format, retrieval URL/date and any independently published verification evidence. An extracted-tree or generated-archive hash is a different scope and must not replace that hash silently. Submodules and external inputs are separate records.
- Existing patch digests cover exact patch-file bytes. Record origin, base commit, order, applicable terms and applicability result. Missing implementation is a gap with no invented patch file or digest.
- Unknown identities use explicit null/unknown status and a reason. `record_valid` means structurally and internally consistent; `audit_complete` means every declared requirement is accounted for, including substantiated blockers. Neither means source readiness or runtime qualification.
- A valid completed `needs-port` or `blocked` audit can satisfy the investigation/report deliverable. `go` requires verified required inputs and no unresolved source/patch prerequisite for the proposed build work. `needs-port` retains named implementation gates; `blocked` is a no-go. Neither is promoted to runtime readiness because #1 closes.

Only public sources and read-only installed-tool metadata are used. Use isolated Git configuration with hooks, automatic submodule recursion and external diff/filter execution disabled; do not run upstream configure, build, install, package-manager or executable files. Inspect archives by listing or streaming reviewed members; extraction, if necessary, rejects absolute/traversing paths and links outside its fresh cache root. New upstream sources/archives are selected from verified public references during the approved stage, not hardcoded as guessed versions in this plan.

## Stage 1 — Identify and acquire source inputs

### Artifacts

- New `runtime/sources/manifest.json` with acquired/unknown input records and an unassessed overall decision.
- New `mydocs/working/task_m1_1_stage1_evidence.json` and `task_m1_1_stage1.md`.
- Local-only `.build/task1-sources/inputs/` with per-component repositories, downloaded bytes and listing files; acquisition logs under `.build/task1-sources/stage1/`.

### Ordered Steps

1. Revisit the historical Wine/FEX/DXMT references and official CrossOver source offerings. Record current inspected URLs/dates and candidate-selection reasons; do not treat a preview announcement as source availability.
2. Resolve the chosen candidates to immutable IDs, then acquire those exact objects or source archive bytes. Record inaccessible or unavailable inputs honestly; do not substitute preview binaries.
3. Inspect tracked build definitions and submodule metadata without executing them. Add the dependencies required by the selected Wine/FEX Windows-module and DXMT/Metal/shader paths, separating build tools, runtime code, guest PE components and platform prerequisites.
4. For each acquired Git input, save the resolved commit, tree, object format, recursive listing and listing hash. For each archive, save its exact byte hash and listing. Keep retrieval/authenticity observations separate from content identity.
5. Populate reviewed evidence and the initial inventory. Every unresolved required input has a reason and follow-up; incomplete dependency discovery keeps `audit_complete` false.

### Verification

These commands are executed only after acquisition. `PEAR_SOURCE_REPO`, `PEAR_SOURCE_COMMIT`, `PEAR_SOURCE_LISTING` and `PEAR_SOURCE_ARCHIVE` are set to one actual acquired record at a time; no placeholder commit or digest is accepted. The stage report saves the literal public commands and resolved identities, with private absolute paths replaced by cache-relative paths.

```sh
git -C "$PEAR_SOURCE_REPO" rev-parse --show-object-format
git -C "$PEAR_SOURCE_REPO" rev-parse --verify "$PEAR_SOURCE_COMMIT^{commit}"
git -C "$PEAR_SOURCE_REPO" rev-parse --verify "$PEAR_SOURCE_COMMIT^{tree}"
git -C "$PEAR_SOURCE_REPO" fsck --full --no-reflogs
git -C "$PEAR_SOURCE_REPO" ls-tree -r -z --full-tree "$PEAR_SOURCE_COMMIT" > "$PEAR_SOURCE_LISTING"
shasum -a 256 "$PEAR_SOURCE_LISTING"
shasum -a 256 "$PEAR_SOURCE_ARCHIVE"
python3 -m json.tool runtime/sources/manifest.json > /dev/null
python3 -m json.tool mydocs/working/task_m1_1_stage1_evidence.json > /dev/null
git diff --check
```

Git commands apply to Git records; the archive command applies to acquired archive records. Expected: the recorded identities/hashes match actual output and acquired Git object checks succeed. A failed acquisition is an explicit unavailable input, not a successful hash check. JSON parsing alone establishes no provenance or readiness. Reconcile every selected component and required submodule with the inventory before the report.

### Commit

`Task #1 Stage 1: inventory immutable source inputs`

## Stage 2 — Audit source coverage, patches and terms

### Artifacts

- Update `runtime/sources/manifest.json` with inspected requirements, terms, existing patches and gaps.
- New `mydocs/working/task_m1_1_stage2_evidence.json` and `task_m1_1_stage2.md`; the report includes the human-readable gap table.
- Add downloaded public patch bytes under the existing `.build/task1-sources/inputs/` root; keep temporary source extracts, logs and disposable patch indexes under `.build/task1-sources/stage2/`.

### Ordered Steps

1. Map #2's measured host boundary and the graphics audit's Wine/DXMT interface requirements to the chosen source paths: loader/layout, x18 transitions, thread/signal/exception/JIT services, FEX Windows/UnixLib integration, driver exports and Metal/shader dependencies.
2. Inspect actual implementation and relevant upstream changes. Cite immutable file locations and distinguish present code, unverified behavior, missing port work, unavailable source and external prerequisites. A bounded unsuccessful search is not a repository-wide absence proof.
3. Inventory existing public patches by exact base/order/content. Check and, when needed, apply them only to a disposable index/source copy to validate the series; do not author or integrate a new port. Failed applicability remains a recorded gap.
4. Inspect license, notice, vendored-dependency and contribution-policy files at each selected revision. Record evidence references and exceptions; distinguish downstream reuse rights from upstream submission policy. Treat unavailable or ambiguous required terms as unresolved, not a legal clearance.
5. Associate each remaining implementation gap with #4, #5 or #7 and its future test obligation. Do not change those Issues or claim their completion.

### Verification

The file variables identify actual reviewed files or bytes. For ordered patches, the temporary index is initialized once and advanced only after each check succeeds; `PEAR_SOURCE_INDEX` is a fresh absolute path inside the task cache. No worktree checkout or upstream hook/script is required for this check.

```sh
git -C "$PEAR_SOURCE_REPO" show "$PEAR_SOURCE_COMMIT:$PEAR_SOURCE_FILE"
shasum -a 256 "$PEAR_PATCH_FILE"
GIT_INDEX_FILE="$PEAR_SOURCE_INDEX" git -C "$PEAR_SOURCE_REPO" read-tree "$PEAR_SOURCE_COMMIT"
GIT_INDEX_FILE="$PEAR_SOURCE_INDEX" git -C "$PEAR_SOURCE_REPO" apply --cached --check "$PEAR_PATCH_FILE"
GIT_INDEX_FILE="$PEAR_SOURCE_INDEX" git -C "$PEAR_SOURCE_REPO" apply --cached "$PEAR_PATCH_FILE"
python3 -m json.tool mydocs/working/task_m1_1_stage2_evidence.json > /dev/null
git diff --check
```

Expected: evidence references resolve to the inspected bytes; applicable patches pass in declared order. A patch rejection, missing behavior or unresolved term is preserved and prevents an unsupported positive decision; it does not invalidate an honestly completed audit stage. No full runtime behavior or build is inferred from source inspection or patch application.

### Commit

`Task #1 Stage 2: audit source coverage patches and terms`

## Stage 3 — Pin candidate tool inputs and validate inventory

### Artifacts and Ordered Steps

1. Update `runtime/sources/manifest.json` with exact candidate tool/SDK versions, target roles and source-required settings. Reconcile source build definitions with read-only installed-tool metadata; record conflicts and compatibility still awaiting #4/#5/#7 builds.
2. Add `tools/sources/validate_inventory.py` using Python's standard library and narrow local Git inspection where needed. It reads inventory/evidence/cache inputs, checks references and acquired bytes, and emits one structured report. It performs no acquisition, upstream-script execution, launch or signing.
3. Add `tests/sources/test_inventory.py`. Create tiny owned Git/archive/patch fixtures in temporary storage; their computed hashes remain fixture data. Cover duplicate/missing IDs, mutable-only refs, invalid digest scopes, mismatched object/tree/archive bytes, missing required submodule/patch provenance, broken references, cache path escape, and contradictory readiness claims.
4. Test valid incomplete and complete-negative records separately from eligible source decisions. Record the agreed logical #3 handoff in `task_m1_1_stage3_evidence.json`; write `task_m1_1_stage3.md`. Do not modify `runtime/contracts/` or require #3 completion.

### Validator Contract and Verification

CLI: `--manifest PATH --cache-root PATH`, optionally `--require-complete` or `--require-source-ready`. Required acquired inputs are checked against local content; missing/corrupt bytes cannot pass as verified. Output includes `record_valid`, `audit_complete`, `decision`, `source_ready` and bounded error codes/component references. It omits raw private paths and never reports a qualified runtime.

Exit 0 means the requested audit check passed; default validation can accept an honest incomplete/blocked record. Exit 1 means invalid/inconsistent evidence or a content mismatch; exit 2 is CLI misuse; exit 3 means a valid record fails the requested completeness/readiness gate. `--require-complete` accepts fully accounted `go`, `needs-port` and `blocked` audits. `--require-source-ready` succeeds only for complete `go`; its deliberate refusal is expected for other valid decisions and must not be described as a passed source gate.

```sh
xcrun clang --version
xcrun --show-sdk-version
git --version
python3 --version
python3 -m unittest discover -s tests/sources -p 'test_*.py' -v
python3 tools/sources/validate_inventory.py --manifest runtime/sources/manifest.json --cache-root .build/task1-sources/inputs
git diff --check
```

Inspect additional selected tools using their actual version/architecture commands; absence is recorded without installing or building them automatically. Expected: all validator tests pass, inventory validation exits 0, and unresolved tool/port facts remain explicit. Real-source verification and synthetic tests are reported separately.

### Commit

`Task #1 Stage 3: validate source provenance and toolchain inputs`

## Stage 4 — Repeat acquisition and issue the decision

### Artifacts and Ordered Steps

1. Reacquire/materialize all available selected inputs into fresh `.build/task1-sources/reproduction/inputs/` using the literal Stage 1–2 acquisition commands resolved to the recorded immutable refs and patch identities. Reproduce the original input root's relative layout, preserve previous inputs, and keep logs/indexes under `.build/task1-sources/stage4/`. Repeat submodule and existing patch verification without running upstream code.
2. Compare Git object/tree identities and scoped listing digests; compare exact archive/patch bytes. Record changed archive representations or retrieval failures explicitly. Do not rewrite a pin to conceal a mismatch; any representation change needs an explained evidence update before a positive decision.
3. Complete the manifest's requirement accounting and `go`/`needs-port`/`blocked` decision. A complete negative audit names affected candidate inputs, downstream gates and reconsideration conditions. No-go remains blocking even if the investigation is accepted and #1 later closes.
4. Add `docs/source-qualification.md` with actual reproducible acquisition commands, the inventory format, inspected terms/gaps and decision limits. Through the coordinator, add narrow dated links to the two historical audits and `docs/README.md` without rewriting historical findings.
5. Write `task_m1_1_stage4_evidence.json`, `task_m1_1_stage4.md` and `mydocs/report/task_m1_1_report.md`; map all three Issue criteria to evidence. Root coordinates the daily board and final-report/PR procedure.

### Verification

```sh
python3 -m unittest discover -s tests/sources -p 'test_*.py' -v
python3 tools/sources/validate_inventory.py --manifest runtime/sources/manifest.json --cache-root .build/task1-sources/reproduction/inputs --require-complete
python3 tools/sources/validate_inventory.py --manifest runtime/sources/manifest.json --cache-root .build/task1-sources/reproduction/inputs --require-source-ready
python3 -m json.tool mydocs/working/task_m1_1_stage4_evidence.json > /dev/null
git diff --check
```

Expected: tests and complete-audit verification exit 0. Readiness exits 0 only for `go`, or the documented 3 for `needs-port`/`blocked`; inspect structured output and compare it to the declared decision. Any unexpected exit, invalid record, checksum mismatch or falsely claimed verification must be resolved. Review relative links, privacy and shared-document diffs. Reproduction covers source acquisition on the declared environment, not component builds, a clean runtime installation or independent gameplay.

### Commit

`Task #1 Stage 4 + final report: record source qualification decision`

## Verification, Dependencies and Reporting

- Each stage bundles its reviewed artifacts, evidence and stage report in the named commit. Unexpected verification failures prevent completion; an explicitly expected unavailable input or negative gate is retained as evidence, never recast as success.
- Stage 1 requires this implementation-plan and Stage 1 approval. Each later stage requires the preceding report's approval. Scope or document-location changes require review before implementation.
- Acceptance 1 maps to immutable source/tool records and repeat verification; acceptance 2 to the requirement/gap/terms table; acceptance 3 to negative validator fixtures and the final no-go/readiness decision.
- #1 and #3 remain independent. The source inventory cannot launch a runtime; #3's valid product schema cannot make incomplete source or port evidence ready. #4/#5/#7/#13 own builds, implementation and later qualification.
- Preserve #2 source/evidence and its bounded host conclusion. No #2 probe, Steam/game process, signing operation, system-policy change, commercial preview dependency or upstream submission is part of this task.

## Risks and Responses

- Moving upstream refs or generated archive differences: resolve once to immutable objects, retain byte/digest scope and compare provenance; never silently update selected inputs.
- Hidden downloads, submodules or terms: inspect selected build definitions recursively and keep unmet dependencies explicit. An audit can conclude no-go without inventing unavailable inputs.
- Parallel drift: #1 owns factual inventory/validator, #3 owns product contracts; coordinate handoff meanings and shared-document edits without adding completion dependencies.
- Overstated readiness: content verification and patch applicability are source evidence only. Needed ports, actual build compatibility and runtime acceptance remain separate obligations.

## Approval Request

Approve this four-stage implementation sequence, exact artifact locations, validation/exit semantics and stage commits, and authorize Stage 1 source identification/acquisition. Actual immutable revisions and hashes will be selected and measured during Stage 1. Later stages retain their report checkpoints; this request does not authorize port implementation, runtime builds or game execution.

## Approval Record

The task requester approved both #1 and #3 implementation plans and authorized parallel Stage 1 execution on September 28, 2026. This approval preserves the task-plan scope and document locations. Stage 2 has not been authorized.
