# Task #56: split source ownership and restore a usable native development path

GitHub Issue: [#56](https://github.com/postmelee/pear/issues/56)
Milestone: M1 — Megabonk on Apple Silicon without Rosetta

## Purpose

Move the selected native Wine/FEX/DXMT implementation into independently owned component repositories and assemble it through one common runtime repository. Completion requires an actually reconstructable, verifiable development candidate and a Pear development/diagnostic entrypoint, so the existing Megabonk failure can be investigated in the new structure.

Resolving that failure, completing M1, general player support and distribution qualification are excluded. #11/#12 retain game implementation/qualification, #10 retains architecture observation, and #13 retains broader clean reconstruction acceptance.

## Background

The October 15 initial separation proposal and source audit established 53 selected Wine patches/58 changed units, 83 selected FEX changed units, 17 generic diagnostic payloads and five DXMT patches. Full component trees and dependencies remain necessary. The selected checkpoint is Task11 commit `951264bf5be4b9d2afb87320f5fac74778b2dd58` plus individually identified dirty/ignored D36/runtime12 inputs. Source correspondence is not a clean build or authority transfer.

The D25 producer gap has now been narrowed: the original 9,057-byte `phase_build.py` was reconstructed from source-edit history and matches recorded SHA-256 `3e83e11f7806b639d091052e140a103c2d3dd0eda6187cacc9117f9aae8ab84c`. Original-byte recovery and validation of a portable successor are distinct evidence. The old producer still contains historical path/coordination assumptions and must not run unchanged against existing state.

Pear base: `bcd27806da5c9885cfcf40e639ae02b2c400e3c1`. Existing Preview delivery advanced after the first investigation; preserve its resources and active work. Existing source owners are being asked to review current differences and cutover requirements. Root/scoped AGENTS, architecture, delivery plan, runtime contracts, source qualification and artifact retention rules apply.

## Scope

### Included

- Reconcile owner changes, freeze source/provenance/input identities and retain exact private inputs separately.
- Create PRIVATE `postmelee/pear-wine`, `pear-fex`, `pear-dxmt` and `pear-runtime`, as explicitly selected by the requester; preserve upstream commit ancestry and attribution.
- Import accepted and selected candidate layers separately, establish one editable source authority and digest-pinned shared-header/test ownership.
- Preserve the original D25 helper as historical evidence; implement portable compilation/assembly with explicit immutable inputs, fixed commits and affected validation.
- Provide isolated development candidate selection/diagnostics from Pear with preservation-first rollback. Keep manager in Pear where Preview depends on it.
- Component READMEs, related repository links, developer build/verification/recovery guidance and sanitized permanent investigation records.
- Additional storage investigation and exact pre-deletion proposals; no new deletion without approval.

### Excluded

- Fixing Megabonk Loading/Down/WGI/Steamworks, gameplay qualification or full host-path Rosetta-independence proof.
- Closing #10–#16, rebasing upstream, changing ABI/capacity/guards, rewriting implementation languages or unrelated refactors.
- Preview resource/activation changes, existing runtime/prefix/save changes, public component release or visibility transition.
- Committing game-derived selector contents, owned image/spec/role inputs, account state, raw private evidence, personal paths or signing secrets.
- Deletion under the earlier Task4 object approval; that exact operation is complete and grants no new scope.

## Design Direction

Wine owns its C/Objective-C port, native owner and wire ABI provider. FEX owns its C++/assembly translator/frontend and generic diagnostics. DXMT owns its C++/Objective-C renderer/consumer changes. The common runtime owns exact compatible commit/toolchain/input locks, assembly/build/verification orchestration, generic contract package and shared diagnostic schema generation. Pear retains app/Steam/game policy and its existing manager dependency.

Keep pinned upstreams: Wine `4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf`, FEX `59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa`, DXMT `7c8dee1c2d73415301ceb7d1fa810861cef4cd67`. Preserve file-specific licenses and upstream history. Reuse existing build/verification logic; do not replace subsystems. Upstream contribution policies apply to any future submission; private downstream development does not imply upstream acceptance.

Wine exports `pear_fex_memory.h` unchanged at digest `a089b475fe6d6f2401977319eb4f0702e85c0753063f5748093131088f9f8b55`. Wine/DXMT provider and consumer interfaces remain exactly paired. One common runtime schema/generator owns shared `PearAbortObservation.h`; both components consume the same identified output. Keep other generic diagnostic payloads with FEX and private phase selection outside all Git repositories.

Historical receipts remain immutable. A new build receipt binds portable source roots, preserved immutable input identities, tools, argv/environment, outputs and verification. An explicit prebuilt input is acceptable for this bounded development reconstruction; it must not masquerade as a full clean source rebuild and must have a retention/recovery contract. No unspecified old-worktree lookup is acceptable.

Use the existing contract/manager/observer seams. Development qualification must remain distinct from supported Preview admission; a fixture record cannot authorize actual runtime execution. Host signing/permission checks use current artifact-specific evidence and normal macOS protections.

Technical skills: task-register/start/stage-report and todo govern workflow. Apple-tooling guidance is selected before any affected Metal execution/validation; no new rendering design is introduced by planning. The selected platform/toolchain versions are taken from exact build receipts, not current defaults.

## Document Location Judgment

The requester explicitly included README, Pear/runtime documentation and permanent sanitized records in this task. This table defines that authorized location scope; it does not establish a second roadmap.

| File | Classification | Audience | Selected Location | Alternative Location | Reason |
|---|---|---|---|---|---|
| Component READMEs | Official component entrypoints | Maintainers/developers | Each repository `README.md` or existing upstream README with a Pear section | Pear-only guide | Roles, upstream and local commands must be discoverable at source |
| Runtime build/input/recovery guide | Official integration guide | Runtime developers | `pear-runtime/docs/development.md` and linked input reference | `mydocs/manual/` | Reusable developer contract, not workflow procedure |
| Pear native development guide | Official contributor guide | Pear/runtime developers | Existing `docs/development/rosetta-free.md`, linked `docs/development/runtime-supervisor.md` | New parallel roadmap | Extend existing entrypoints and preserve qualification status |
| Architecture/runtime link references | Official reference | Integrators | `docs/architecture.md`, `docs/runtime-contracts.md`, `docs/README.md`, root README | New roadmap | Narrow ownership/link updates; delivery plan remains canonical |
| Reviewed source investigation | Dated technical evidence | Maintainers | `mydocs/tech/20261015_runtime_repository_split.md` plus sanitized data | Raw temporary packet | Preserve decisions/provenance without personal/private contents |
| Task plans/reports | Workflow artifacts | Reviewers | `mydocs/plans`, `mydocs/working`, `mydocs/report`, `mydocs/orders` | Official guides | Keep task evidence separate from reusable instructions |

## Expected Changed Files

New: component-owned source commits and provenance/README/test metadata; `pear-runtime` lock/build/verification/contract/docs; Pear source-handoff data and narrow development candidate adapter/tests as the existing interface requires.

Modified: the existing Pear native developer documentation and related reference links; legacy selected source entries receive frozen ownership references only at accepted cutover. Preview resources, code paths and manager dependency remain intact.

Task artifacts: `mydocs/plans/task_m1_56.md`, `task_m1_56_impl.md`, `mydocs/orders/20261015.md`, `mydocs/working/task_m1_56_stage{N}.md`, `mydocs/report/task_m1_56_report.md` and the dated technical note. Detailed private path maps remain in ignored task-owned evidence.

## Artifact Lifecycle

| Artifact/root | Class and state | Owner/consumer | Identity and recovery needs | Retain reason | Release condition |
|---|---|---|---|---|---|
| Original source/cache/patch trees | Authoritative/retained input | #11 and component owners; #56 import | Exact commit/tree/patch/content/mode identities; no mutation | Import comparison and rollback | Accepted imported history, agreed cutover and all consumers release |
| Selected current runtime/prefix and unique evidence | Active or retained private input | #10/#11/#12 and existing owner | Original identity/private recovery rules | Existing execution/review | Separate explicit owner/user decision; excluded here |
| Toolchains, generated config, retained object/archive inputs | Retained immutable build input | Component builders/#13/#56 | Digest, role, source/recipe provenance, named roots/recovery | Bounded reconstruction | Valid successor and last consumer release, then separate deletion approval |
| New component repositories | New source authority after cutover | Component maintainers | Upstream ancestry, selected commits, provenance, private remotes | Continued development | Normal source retention; not disposable |
| New candidate/build outputs | Task-owned isolated output | #56 verification and next #11 debug | Lock/argv/hash/signing/verification record | Rebuild/diagnostic handoff | Successful successor and explicit retention handoff |
| Scratch investigation packet | Local review evidence | #56/owners | Hash-indexed inputs, no public personal paths | Source/consumer comparison | Sanitized committed record plus last consumer release |

Reuse/copy decision: reuse exact admitted toolchains and declare every retained binary input. Do not duplicate complete old build roots. A separate candidate bundle may need an isolated copy for changed payload/signature safety; record that specific reason, allocation and release event before creating it. Never share writable runtime files with the original.

Peak-space plan: initial planning observed approximately 8.9 GiB available on `/System/Volumes/Data`; this is not a build budget. Planning/source metadata is small. Measure actual source checkout/history cost and changed-object/link/package peak before each material operation. The recovered D25 helper's historical 6 GiB guard is only a prior estimate. Account for simultaneous old/new outputs, archive restore and APFS uncertainty; serialize heavy operations under the existing host ownership seam. If insufficient, continue small independent work and resolve capacity with exact cleanup proposals before building.

## Tentative Stages

1. Reconcile and freeze the source/input checkpoint; recover D25 source; commit updated plan and sanitized investigation with owner review and space gates.
2. Import component histories/source/test/provenance into isolated private repositories; verify exact deltas and shared inputs. Legacy source authority remains until final accepted cutover.
3. Implement portable explicit-input build/assembly and reconstruct the selected development combination with new receipts.
4. Run affected required component/integration checks, compare artifacts and record qualified/unperformed limits; verify recovery and reconstruction commands.
5. Connect Pear's separate development candidate selection/diagnosis; finalize component READMEs and developer links without Preview changes.
6. Verify cross-repository locks/links and accepted ownership cutover, record Megabonk failure/next implementation/reproduction handoff, retention and final report/PR.

## Verification Plan

Stage 1: exact current source hash comparison, recovered D25 hash, owner differences/holds, upstream/provenance/privacy and storage inventories. Read-only checks do not imply execution success.

Stage 2: upstream ancestry, exact source bytes/modes/symlinks, accepted/candidate attribution, no private payloads, single shared-header/test provider, actual remote privacy/refs.

Stage 3: fixed commit resolution, strict input hashes, all file dependency roles explicit, replay/compile/link/assembly commands in isolated roots; unchanged original inputs verified. Compare unsigned payload/text differences and explain known timestamp/path effects.

Stage 4: execute affected existing required CPU/ABI/graphics fixtures and policy controls on exact selected candidate using valid current host authorization. Preserve failures and report unavailable checks honestly. Historical unchanged component checks support only their original scope.

Stage 5: candidate selection rejects mismatch/missing inputs, keeps existing defaults/state, records actual selected runtime/diagnostic paths and supports recovery. Validate portable tests and relevant host scenarios; actual game success is excluded.

Stage 6: check all locked source/remote artifact identities, READMEs/links, source owner acknowledgments, next debug recipe and retained/recovery inputs. `git diff --check`; source-only staged changes; no private inputs in Git; clean task trees before PR.

## Risks

- Old graph/path/config dependencies can exceed the source delta: name every retained input, rebuild affected objects and do not equate source correspondence with binary parity.
- Storage pressure: exact peak calculation and separately approved cleanup, no blanket deletion or giant duplicate runtime copies.
- Private selectors: preserve exact local diagnostic replay separately; public/generic test selection is a different configuration.
- Concurrent ownership: compare again before cutover and preserve all owner edits and #47 state.
- Upstream provenance/licenses: maintain existing terms and upstream history; unresolved attribution stays an import gate.

## Approval Record

The requester authorized the specified implementation/preparation scope and continuous stage progression, including verification, reports and commits. They subsequently selected PRIVATE creation of all four named repositories and necessary read-only coordination messages/replies with #11/#12/#10. These instructions supersede repeated per-stage approval prompts for this task only. Scope expansion, public visibility, additional deletion and #47/existing environment changes remain unapproved.
