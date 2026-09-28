# Task #1 final report: Source qualification and toolchain inventory

GitHub Issue: [#1](https://github.com/postmelee/pear/issues/1)
Milestone: M1

## Work Summary

- Target Issue: #1 — Qualify source availability and pin the runtime toolchain.
- Milestone: M1 — Megabonk on Apple Silicon without Rosetta.
- Stage count: four, completed with recorded verification.
- Work purpose: identify reproducible source inputs and remaining implementation/build gates before assembling Pear's Wine/FEX/DXMT runtime.

**Result: the investigation is complete; the current source/build candidate is blocked and not source-ready.** Public source identities reproduce. Required Darwin integration remains `needs-port`; unavailable/conflicting build tools and configured dependency/notice closure remain blockers. This result does not establish a runtime, game, performance or distribution claim.

## Changed Files and Impact Area

| Path | Change Summary | Impact Area |
|---|---|---|
| `runtime/sources/manifest.json` | Immutable source and scoped digest records, dependencies, patch provenance, terms, tool metadata, gap accounting and explicit no-go decision | Source/build prerequisite handoff |
| `tools/sources/validate_inventory.py`, `tests/sources/test_inventory.py` | Bounded read-only consistency/content validator and 77 positive/negative fixtures | Reproducibility and false-readiness rejection |
| `docs/source-qualification.md` | Source selections, concrete acquisition/replay/validation instructions, gaps and reconsideration conditions | Contributors and downstream implementation |
| `docs/README.md`, existing macOS/graphics research audits | Narrow dated links; historical content preserved | Documentation navigation and scope |
| Plans, four stage reports/evidence records, this report and daily board | Approval trail, actual results, acceptance mapping and residual risks | Review and long-term work record |

## Document Location Verification

| File | Planned Location | Actual Location | Result | Evidence |
|---|---|---|---|---|
| Contributor source guide | `docs/source-qualification.md` | Same | OK | Approved task-plan document-location judgment and implementation-plan Stage 4 |
| Historical follow-ups/index | Existing `docs/research/` files and `docs/README.md` | Same | OK | Narrow dated paragraphs/links only |
| Source data and validation | `runtime/sources/`, `tools/sources/`, `tests/sources/` | Same | OK | Approved factual inventory/validator ownership |
| Stage and final work records | `mydocs/working/`, `mydocs/report/` | Same | OK | Milestone-bearing filenames and central templates |

## Quantitative Before/After Comparison

| Metric | Before this Issue | After |
|---|---|---|
| Committed factual source inventory | Historical leads without this verified inventory | 30 component records; 22 Git inputs, one archive, seven explicitly conditional exclusions |
| Existing patch provenance/replay | Historical candidate without this scoped replay | One exact patch; original-base success, two selected-base rejections |
| Source implementation evidence | Architecture research | 206 unique Git source blobs and 16 selected archive members validated at final pins |
| Candidate tool records | No configuration-specific inventory in this Issue | 17 records: ten metadata-observed, six not found, one unavailable; conflicts explicit |
| Source validator tests | None | 77 passing owned fixtures |
| Acquisition verification | Not established by this Issue | Initial and fresh remote acquisition identities match |
| Source readiness | Unassessed | Complete `blocked` audit; source-ready gate deliberately refuses with exit 3 |

## Verification Results

| Acceptance Criterion | Result |
|---|---|
| Manifest identifies immutable revisions, archive/patch hashes and build-tool versions, with evidence for required components | **OK as an audit deliverable.** Exact acquired identities and observed tool versions are recorded; missing inputs, conditional dependencies and unavailable provenance have explicit dispositions. Unknowns are not promoted to ready inputs. Fresh acquisition and complete-audit validation pass. |
| Gap table separates reusable code, patches to implement, unavailable inputs and external prerequisites | **OK.** Guide and manifest map ten source requirement areas to Wine/FEX/DXMT reuse and #4/#5/#7/#13 obligations. New Darwin ports were not authored in this investigation. |
| No opaque Preview binary or placeholder hash is classified as reproducible; no-go and downstream gates remain explicit | **OK.** No Preview binary accepted; unknowns remain unknown. `decision: blocked`, `source_ready: false`, runtime/game/distribution unassessed. Readiness validation returns the expected refusal. |

### Stage Verification Results

- [Stage 1](../working/task_m1_1_stage1.md): selected immutable public inputs, acquired exact objects/bytes, recorded source/dependency coverage and explicit unknowns.
- [Stage 2](../working/task_m1_1_stage2.md): bound reusable-code, patch and terms findings to inspected bytes; historical patch applies only to its original parent, while selected Wine bases reject it.
- [Stage 3](../working/task_m1_1_stage3.md): implemented the validator and tool inventory; 77 tests pass, default actual-cache validation passes and incomplete/readiness gates refuse as designed.
- [Stage 4](../working/task_m1_1_stage4.md): fresh remote acquisition reproduces all selected identities; 77 tests pass, complete-audit validation exits 0 and source-ready validation returns expected exit 3. Historical patch outcomes reproduce; all prior evidence remains unchanged.

Stage 4's final cache check covers 30 components, 24 content digests, 206 source blobs, 16 archive members, 20 gitlinks, one patch and 276 evidence definitions. The linked stage evidence contains actual commands and bounded results. Guide snippets parse, relative links resolve and diff checks pass. No upstream source was executed.

## Residual Risks and Follow-up Work

### Residual Risks

- The assembled source/build candidate remains blocked despite completing the investigation. Final dependency configuration, missing tools and required ports need implementation evidence.
- Same-Mac reacquisition is not independent-host reproduction, publisher signature authentication, a successful component build or gameplay qualification.
- Vendor and upstream searches are bounded; the full ARM64 Preview implementation and a complete applicable port series were not established.
- Future shipped files need their own source/notice/replacement obligations reviewed. This inventory is not blanket legal clearance or ordinary-user distribution approval.
- Installed compiler/SDK metadata and #2's host results cannot establish a coherent Wine/FEX/DXMT ABI, signing and runtime combination.

### Follow-up Candidates

Existing Issues own the necessary work; no duplicate Issue is proposed:

- [#4](https://github.com/postmelee/pear/issues/4): native Wine loader, memory/page layout, x18/ABI, processes and tool/configuration selection.
- [#5](https://github.com/postmelee/pear/issues/5): FEX Darwin host services, thread ordering, JIT and exception integration.
- [#7](https://github.com/postmelee/pear/issues/7): Wine/DXMT driver ABI and paired ARM64EC/native shader/Metal builds.
- [#13](https://github.com/postmelee/pear/issues/13): complete source-built artifact, signing, dependency and notice closure.

These tasks may perform separately approved preparation and implementation. Their acceptance gates remain tied to actual passing evidence. Retain upstream implementation languages, normal macOS protections, official ownership/authentication flows and exclusion of private/proprietary payloads.

## Approval Request to Task Requester

Approve the completed investigation, final negative source decision and acceptance mapping, then authorize publication of the prepared Issue #1 PR to `master`. Publication does not merge the changes or close the Issue automatically. A future source-ready decision requires a reviewed evidence update and a passing gate.
