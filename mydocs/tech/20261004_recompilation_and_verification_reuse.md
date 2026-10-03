# Recompilation, verification reuse and early CI readiness

Reviewed: October 4, 2026. Task: [#14](https://github.com/postmelee/pear/issues/14).
Status: dated, non-normative research and source inspection. This note is not a second roadmap, a runtime qualification record or proof that proposed Linux commands passed.

## Research Background

The requester asked whether Theo's Melee recompilation and the Agent Engineering Handbook could reduce repeated implementation and accelerate owned Windows Megabonk without Rosetta. Pear already has validators, source pins, task reports and a staged delivery plan. The useful addition is discoverable evidence and bounded reuse, not another translation or verification framework.

## Research Questions

- Which external lessons apply to Pear's existing Wine/FEX/DXMT integration?
- What implementation already exists outside master, and which claims remain unproved?
- Which current tests can be considered for later portable CI without duplicating active work?

## Research Targets

| Target | Reason | Reviewed location/identity |
|---|---|---|
| Handbook investigation | Verification and agent-workflow evidence | [Full investigation](https://agent-engineering-handbook.dev/github-inspection.html), reviewed October 4 |
| Melee4Mac | Separate matching reconstruction from native execution | [Repository](https://github.com/t3dotgg/melee4mac), inspected research snapshot; re-pin code before reuse |
| Initial Melee verifier | Concrete validation design | [Commit 035d9711623a32fbe891cffdcf44a91a550c1947](https://github.com/doldecomp/melee/commit/035d9711623a32fbe891cffdcf44a91a550c1947) |
| Pear master | Existing rules, contracts and validators | d35428f037a91b5db1a22fb0b065d6d13132ccb7 |
| FEX work | Avoid duplicate Darwin/CPU-module implementation | [#5 checkpoint 275681a07353ccfe5676ed2518530795c4994938](https://github.com/postmelee/pear/commit/275681a07353ccfe5676ed2518530795c4994938) |
| DXMT work | Reuse typed bridge and construction work | [#7 checkpoint e6565f6cbffdf5d125a58c6efb0f35328054e13b](https://github.com/postmelee/pear/commit/e6565f6cbffdf5d125a58c6efb0f35328054e13b) |

The supplied Instagram and X posts could not be read directly. Their contents are not independently verified here. The Handbook is a third-party investigation, not Theo's endorsement. Its later completeness fix is reported by that author; the corresponding later code revision was not independently retrieved in this investigation.

## Findings

### What the external examples establish

Melee's path combines matching PowerPC reconstruction, DolRecomp-generated C and ARM64 compilation with a Dolphin-derived hardware runtime. The original executable hash belongs to the matching PowerPC stage, not equality between PowerPC and ARM64 binaries. This is not a general Windows x64/Unity-to-Mac conversion pipeline.

The Handbook's most relevant example checks current command success, expected artifacts and source-completion reports, preventing retained outputs or original-object fallback from supporting a stronger completion claim. Its author ran synthetic verifier tests; they did not reproduce the whole game. Artifact availability to the consuming agent and recoverable checkpoints are useful workflow lessons. These findings justify focused checks for observed false-success modes, not importing an entire architecture.

### Existing Pear implementation and evidence limits

| Area | Reusable work at the recorded checkpoint | Remaining boundary |
|---|---|---|
| #4, merged | Native Wine build/finite ABI, thread, memory, exception and Cocoa fixtures; verifier and negative tests | Does not establish translated x64, Steam or game support |
| #5, Stage 3 | ARM64EC/WoW64 CPU module builds, Darwin services, current JIT owner/accounting work | FEX initialization and first guest dispatch remain unperformed; 262,144-byte added-metadata gate still lacks complete attribution/lifetime evidence |
| #7, Stage 4/5 | Typed Wine–Metal ABI and bounded native adapter execution in Stage 4; later reproducible-link candidate | Stage 4 execution applies to its original candidate. e6565f6's 11 equal diagnostic links do not replace clean rebuilds or native execution on the changed candidate |
| Runtime contracts | Distinct evidence kinds, identities, ownership and reference evaluator | Evaluating submitted records is not observing a real process or game |

The #5/#7 owner confirmed in the existing conversation that this document-only scope does not directly overlap their implementation. Both branches have Wine patch integration obligations despite mostly distinct repository paths. Later integration needs one agreed base, patch order, ABI and candidate identity. Storage/iCloud cleanup retains priority over new native builds; this note does not lift that instruction. Its temporary sidechat could not be read through the thread API, so its completion is unknown here.

The separate native-restoration conversation reported a completed bounded XP/event/UI stage, with remaining test inputs and unreconstructed dependencies. That is useful research evidence, not an alternative qualified M1 runtime. No next restoration stage was started by this task.

### Reuse decisions by upstream

| Source | Reuse judgment | Boundary |
|---|---|---|
| [FEX](https://github.com/FEX-Emu/FEX) and [ARM64EC design](https://wiki.fex-emu.com/index.php/Development:ARM64EC) | Keep existing decoder, IR, ARM64 backend, Windows CPU modules and useful semantics tests; concentrate new code on necessary host boundaries | Retain upstream languages and inspect pinned test harness assumptions; [contribution policy](https://github.com/FEX-Emu/FEX/blob/main/CONTRIBUTING.md) is separate from reuse licensing |
| [DXMT](https://github.com/3Shain/dxmt) | Keep D3D11/Metal implementation, thunks and build paths; reuse #7's adapter work | Pair with the actual Wine ABI and qualify through #8; an upstream README is not Pear execution evidence |
| Melee4Mac/DolRecomp/Dolphin-derived runtime | Reuse verification/navigation ideas and review techniques | PPC/GameCube assumptions do not replace Windows CPU/API/Steam integration |
| [NotProton](https://github.com/NotProtonNot/NotProton) | Future native Steam bridge reference | Version-dependent integration; Windows Steam remains the approved baseline |
| [CrossOver ARM64 announcement](https://www.codeweavers.com/blog/mjohnson/2026/7/31/crossover-preview-the-right-to-bear-arm64-on-mac) and [published source](https://www.codeweavers.com/crossover/source) | Inspect concrete public deltas at named blockers | Product behavior does not establish availability of every matching preview source; no wholesale stack update is selected |

No external source code is copied by this stage. Re-pin mutable upstream links and review the exact version's licenses and contribution rules before implementation. Independent translator research remains conditional R1, outside M1's critical path.

### Portable CI readiness: source inspection only

Current CI is Ubuntu 24.04/Python 3.12 documentation governance. The table classifies candidates, not executed Linux results.

| Existing test area | Readiness assessment | Necessary next evidence |
|---|---|---|
| tests/docs | Already connected in the existing workflow | Retain current workflow behavior |
| tests/sources/test_inventory.py | Promising stdlib/Git candidate using temporary local repositories | Clean Linux run and observed failure detection |
| tests/wine/test_verification.py, test_inputs.py, test_unsigned_compare.py, test_abi_review.py | Promising explicit subset using synthetic records/files/disassembly | Audit imported paths and run the selected list on clean Linux |
| All tests/wine | Not a safe blanket CI selection | Separate macOS/ARM64/Cocoa/clang and private generated-header prerequisites; report skips |
| tests/contracts | Current dependency lock is incompatible with simply copying it to existing CI | Qualify Linux/Python dependency artifacts and hashes, including active markers |
| #5 tests/fex | Inventory candidates now; do not import another active worktree | Some tests need private .build data or sibling task7 sources; wait for a reviewed integrated revision |
| #7 tests/dxmt | A portable label is insufficient | test_deterministic_pair.py:31 fixes temporary storage to /private/tmp; qualify paths and actual Linux execution |

The contract lock explicitly targets CPython 3.14/macOS ARM64; dependencies.json identifies an rpds-py cp314 macosx_11_0_arm64 wheel. The current CI uses Python 3.12, where referencing's typing-extensions marker is also active. Do not remove hashes or use an unlocked installation to conceal this mismatch.

Candidate commands for a later approved Linux experiment, not executed here:

```bash
python3 -B -m unittest discover -s tests/sources -p test_inventory.py -v
python3 -B -m unittest discover -s tests/wine -p test_verification.py -v
python3 -B -m unittest discover -s tests/wine -p test_inputs.py -v
python3 -B -m unittest discover -s tests/wine -p test_unsigned_compare.py -v
python3 -B -m unittest discover -s tests/wine -p test_abi_review.py -v
```

## Decisions

- Preserve this investigation under mydocs/tech and add only minimal discovery/reuse prompts to existing rules/templates.
- Use existing Issue #14 for this preparation. Reuse unittest and current validators; do not build a second runner or verifier framework.
- Keep current #5/#7 ownership and approval gates. Reuse their code and recorded findings rather than restarting either integration.
- Keep evidence scope visible: source inspection, synthetic tests, compilation, host execution, translated execution, game qualification and ordinary-user distribution are separate.
- Convey useful external findings to the existing runtime and native-restoration conversations as advice, without authorizing new stages or builds.

## Non-decisions / Deferred Items

- No workflow activation, Linux success, runtime speedup, game support or #14 completion is claimed.
- No new CPU backend, persistent FEX cache, native Steam bridge or change to #5's metadata gate is selected.
- Full CI/promotion coverage still needs #14's existing acceptance dependencies and separate stage approval.
- Current source and toolchain changes still require approved verification; evidence reuse is not permission to skip required checks.

## Implementation Impact

The next useful sequence remains #5 native/guest boundary, #6 CPU/API qualification, #7 coherent graphics construction, #8 translated D3D11 qualification, and #11/#12 Steam/game behavior, with #9/#10 preparation according to the existing delivery plan. This is a reference to that plan, not a replacement dependency graph. #13/#14/#15/#16 final candidate and qualification work remains required.

Small read-only research and documentation can proceed alongside #5/#7. Heavy build/storage operations remain coordinated by their owner. Reuse unchanged, input-bound evidence; after relevant source/compiler/configuration/ABI changes, revalidate the affected claims and finally the integrated candidate. A successful command receipt or an increased test count is not proof of a new runtime behavior.

## References

- [Canonical delivery plan](../../docs/delivery-plan.md)
- [Runtime evidence contracts](../../docs/runtime-contracts.md)
- [Existing Wine report verifier](../../tools/wine/verify.py)
- [Existing verifier negative tests](../../tests/wine/test_verification.py)
- [Current documentation CI](../../.github/workflows/documentation.yml)
- [Contract dependency lock](../../tests/contracts/requirements.lock) and [artifact metadata](../../tests/contracts/dependencies.json)
- [Task plan](../plans/task_m1_14.md) and [implementation plan](../plans/task_m1_14_impl.md)
