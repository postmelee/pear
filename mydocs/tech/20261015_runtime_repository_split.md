# Runtime repository separation and development reconstruction

Date: October 15, 2026. Task: [#56](https://github.com/postmelee/pear/issues/56). This dated investigation updates the earlier temporary separation proposal. It is not gameplay, distribution or complete Rosetta-independence qualification.

## Research Background

The native candidate's editable source and build inputs span accepted component layers and selected generated diagnostics. The requester approved separating source ownership and preparing a usable development/reconstruction path while preserving the Rosetta Preview and existing execution environment. Actual Megabonk correction remains follow-up work.

## Research Questions

- Which exact source and generator inputs can be transferred without losing their provenance or private boundary?
- Which retained build dependencies can become explicit immutable inputs, and which must be rebuilt?
- How can the new candidate be selected and diagnosed without replacing Preview or existing private state?

## Research Targets

| Target | Reason | Location |
|---|---|---|
| Selected source checkpoint | Defines exact delta and private exclusions | [Sanitized checkpoint](task_m1_56_source_checkpoint.json) |
| Existing native owner | Source continuity, failure and cutover review | [#11](https://github.com/postmelee/pear/issues/11) |
| Game/input and observation owners | Next diagnostics and required evidence | [#12](https://github.com/postmelee/pear/issues/12), [#10](https://github.com/postmelee/pear/issues/10) |
| Reconstruction acceptance | Broader clean setup/packaging boundary | [#13](https://github.com/postmelee/pear/issues/13) |
| Preserved product | Separate Rosetta Preview lineage | [#47](https://github.com/postmelee/pear/issues/47) |

## Findings

### Source continuity and original-producer recovery

The source owner rechecked and accepted isolated import of the selected Stage 1 range: 58 Wine and 83 FEX changed files, 17 generic diagnostic payloads and five DXMT patches. All 141 selected Wine/FEX units were independently rehashed for this task with no differences. The owner requested no new component changes. This is acceptance of exact isolated import, not source authority cutover, licensing clearance or runtime qualification.

Wine retains 46 accepted baseline patches and seven selected owner changes. Keep query patch `0004b`; exclude superseded `0004` and the N1-only NX-pool experiment. Preserve D27 native-owner and string-build3 PE compilation separately; unchanged string source compiled with `-O2` is a build overlay rather than another patch.

The original D25 `phase_build.py` was recovered at exactly 9,057 bytes and SHA-256 `3e83e11f7806b639d091052e140a103c2d3dd0eda6187cacc9117f9aae8ab84c`. Ninety-seven retained producer snapshots did not contain it; a narrowly selected original source declaration and three literal edits reconstructed the recorded bytes. No historical command or recovered program was executed. The recovered file remains local because its historical coordination paths are not a portable/public interface. Its digest and recovery method are permanent evidence.

The overall old D25 build3 failed after its successful control object commands. Admit only the individually identified outputs later selected by D26/D36; do not relabel the entire failed build. Original-byte recovery closes the missing producer issue. Portable execution and new output validation are still required.

### Responsibility and shared inputs

The requester selected four private repositories: `postmelee/pear-wine`, `pear-fex`, `pear-dxmt` and `pear-runtime`. Names/visibility are approved; repository and commit links become active only when creation/import is verified. Pear remains the application and actual game/Steam/profile policy owner.

Wine owns the memory/lifecycle ABI header at SHA-256 `a089b475fe6d6f2401977319eb4f0702e85c0753063f5748093131088f9f8b55` (wire v3, 128-byte records, Unix index 10, eight services). FEX consumes a pinned export. Wine/DXMT provider/consumer interfaces remain paired. Wine owns the Pear v1/v2 provider headers; DXMT retains ownership of its upstream winemetal headers consumed by Wine. Exported copies are pinned and are not independently editable. The common runtime owns the shared abort diagnostic schema/generator, yielding `PearAbortObservation.h` at digest `da52c81da2051d3c255dc953f1c49758d76920f065de076de2adfa53c6f324a5`; both components consume identical bytes. This consolidates the earlier FEX-local destination label without rewriting its historical manifest. Other 16 generic payloads remain FEX candidates.

Wine owns its native API/ABI tests; FEX its CPU/repair/lifetime tests; DXMT its rendering/presentation tests. Common runtime owns paired integration and seven-fixture orchestration, and Pear owns original-game/account/user policy. Preserve one editable implementation/test source per contract. Directory names such as `tools/steam` are not sufficient ownership criteria.

Game-derived selectors and owned image/spec/roles stay private and outside Git. A synthetic selector can exercise generic controls but is not the same private diagnostic artifact. Preserve upstream histories and file-specific notices; moving a tool does not change its license to the destination project's default.

### Explicit-input reconstruction

The smallest FEX route has 63 COFF objects, 15 archives and one DEF input totaling 69,463,668 bytes. Pin a complete baseline link-input set, rebuild the final Core/Module/memory units from the fork, replace only the selected archive member and relink. Four unique generated configuration payloads total 912,793 bytes and can initially be declared immutable inputs with their generator provenance. Compiler wrappers, implicit libraries, VFS/header precedence and source identity remain part of the contract.

Wine's selected native link has 28 explicit objects. Its PE link's earlier 85-input list omitted resource/config/tool details; the new inventory covers all 2,309 files and one matching symlink in the retained PE objects tree, including `version.res`, winebuild and generated configuration. This closure is approximately 62 MB logical and 68.6 MB displayed allocation. Selected source/graphics correspondence remains unchanged; large Apple tooling references retain their stated verification limits.

These preserved inputs enable bounded developer reconstruction. They are not proof that every lower-layer dependency was freshly built from source. Each needs content identity, a named input role, recorded recipe/source provenance and a recovery/retention contract. The portable builder must reject an undeclared fallback to an old worktree.

### Current failure and next implementation

D36/runtime12 is the latest tested private combination. Menu/CONFIRM and progressing loading were observed, followed by owner refusal and supervised termination; gameplay remains unqualified. The 64 retained binding rows map to distinct native thread IDs, but their failure-time liveness is unknown. There is no evidence-based permission to reclaim slots, increase capacity or change the ABI.

D37 thread-liveness observation is a pending integration diagnostic, not part of the selected Wine/FEX delta. Its portable controls and primitive native controls have evidence, while transport joint controls and game execution remain unperformed. Old grants/boot/time state do not authorize another run. The Down/WGI invalid-output hypothesis remains separate and unproven; preserve original API behavior and do not add a neutral-success stub.

All seven required D36 fixture oracles remain: TLS/thread, SEH/unwind, suspend/context, code invalidation, guest-fault guard, configured memory and original rendering. Reconstructed artifacts require affected validation. Preserve #6 CPU/order, #8 graphics, #40 loader, #10 observation and #11/#12 game evidence boundaries.

## Decisions

- Continue through the six stages in the [implementation plan](../plans/task_m1_56_impl.md), with verification/report/commit gates and the requester's continuous authorization.
- Use private component repositories and retain upstream ancestry; existing shallow caches are acquisition inputs, not complete-history evidence.
- Preserve the recovered D25 original as provenance and validate new portable execution explicitly.
- Allow declared immutable lower-layer inputs for this bounded development candidate; complete clean reconstruction remains a separate claim.
- Preserve Preview resources, original runtime selection, authenticated prefixes, saves and normal macOS protections.

## Non-decisions / Deferred Items

Authoritative cutover requires exact imported commits, source-owner acceptance and verified development reconstruction. No gameplay correction, public repository transition, player release, original runtime change or additional deletion is implied. #13 and other existing issues stay open under their original acceptance criteria.

## Implementation Impact

Source checkout payloads are approximately 449 MB before history and build inputs. Wine's upstream repository API size is approximately 1.21 GiB; the clone/fetch/index overlap and source checkout must be budgeted separately. Measure actual consumption before subsequent material work. Existing full Wine build storage thresholds do not describe the proposed partial reconstruction, whose new budget requires explicit measured justification.

A separate proposal identifies 3,030 old Task4 PE/archive products at 3.826 GiB displayed allocation. The source owner has no current D36/D37 payload consumer; historical source/install/config/log readers remain preserved. This is a proposed retirement of historical relink products, not verified duplicate cleanup. The requester separately approved exactly those 3,030 paths. Preflight and execution completed with protected metadata/hashes/Git state unchanged; the stage report records the measured result. This new consent does not release any other artifact. Physical attribution remains bounded by APFS sharing and concurrent activity.

## References

- [Task plan](../plans/task_m1_56.md) and [implementation plan](../plans/task_m1_56_impl.md)
- [Architecture](../../docs/architecture.md), [runtime contracts](../../docs/runtime-contracts.md), [delivery plan](../../docs/delivery-plan.md)
- [Artifact retention](../manual/artifact_retention_guide.md)

## Owner review update — October 16

The #12 review found no newer source edits; its selected Wine WGI files match the pinned upstream and must arrive with the whole tree rather than a fabricated downstream patch. The actual WGI call/failure-source binding remains unproved. #10 confirms the existing D24/D32 reader cannot admit D36 by relabeling; an explicit current-candidate adapter and refreshed path/signing/authority checks are required. Reuse the current APISession and manual handoff seam; do not replace it with an older observer fork or require full N1 production closure before bounded debugging. Both reviews were read directly from their completed chat records after outbound reply approval was rejected; no implementation change or new execution was requested.
