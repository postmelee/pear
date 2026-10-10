# Artifact Retention and Storage Cleanup

## Purpose and Authority

Use this procedure for Pear tasks that create build, runtime, diagnostic or research artifacts. Plan their reuse, ownership and release before substantial creation, then reconcile actual disposition at stage and merge handoffs. This is the canonical internal procedure; templates capture its outputs and skills link its checkpoints.

Apply [repository rules](../../AGENTS.md), the [task workflow](task_workflow_guide.md) and [rule precedence](agent_code_hyperfall_rule_conflict.md). Existing authorization applies to its approved scope. This procedure neither authorizes another worker's state changes nor adds a confirmation gate to cleanup already authorized by the requester. Unclear ownership, destructive scope or conflicts require resolution before mutation.

Keep the [architecture's](../../docs/architecture.md) immutable runtime inputs separate from private mutable state. Preserve required qualification and fresh-reconstruction checks. Storage optimization does not qualify a runtime, authorize execution or change a game's acceptance criteria. Product documentation belongs in `docs/`; dated investigations and local cleanup outcomes belong in task research/reports.

For small documentation-only work, give a reasoned Not applicable for material output/peak-space planning. A compact record in existing task documents is sufficient; no inventory for every command or new storage service is required.

## Artifact Classes and States

Class describes what must be preserved; state describes current use and availability. Record both when they affect a decision.

| Class | Treatment |
|---|---|
| Source, patches, dependency locks and configuration | Keep authoritative identities and reconstruction instructions; inspect exact reusable inputs before reacquisition |
| Toolchains and immutable runtime inputs | Reuse compatible admitted inputs; retain exact consumer and identity requirements |
| Intermediate objects, caches and staging | Release after the last build/diagnostic consumer, unless unique or required reconstruction evidence depends on them |
| Per-run mutable state and temporary runtime copies | Isolate from immutable inputs; release only after owned processes stop and required evidence/private state is secured |
| Qualification and unique failure evidence | Retain the smallest sufficient input/producer/result set for the declared claim and required replay |
| Games, authentication, saves, signing material and private diagnostics | Keep outside Git/releases and distinct from disposable synthetic state; task completion does not authorize deletion |
| Recovery archives, manifests and tools | Retain while any retired original depends on them; account for restoration space and identity requirements |

| State | Meaning and next decision |
|---|---|
| Active | A producer, process or consumer currently needs the artifact; do not retire it |
| Retained dependency | Needed for a named later consumer or replay; record the event that releases it |
| Historical evidence | Supports a bounded past claim or unique failure; identify what must remain verifiable |
| Cold archive | Original bytes require restoration; record the verified recovery location and procedure, and mark restore-required |
| Disposable | Dependency, evidence, private-state and authorization checks establish that release is permitted |
| Unavailable | Required bytes or a usable recovery path are missing/unverified; report the gap and do not claim present availability |
| Released | Authorized removal completed and its scope/result recorded; do not count its space again |

A historical result can remain recorded when its bytes become unavailable, but it cannot be presented as presently replayable. Reassess state when consumers, inputs or recovery availability change. A filename, directory or saved hash alone proves none of these states.

## Planning Before Substantial Creation

1. Inspect existing tasks, retained artifacts and exact source, patch, toolchain, configuration and component identities. Reuse compatible inputs and evidence only within their recorded claim scope. Relevant source/tool/configuration/signing/artifact changes require revalidation of affected claims; a required fresh reconstruction still runs even when a cache exists.
2. Identify immutable inputs and mutable output roots, owner and consumers, expected peak additional storage and uncertainty. Include overlap between old/new builds and temporary archive or restore space. Measure available filesystem space, naming the method, filesystem and time. If capacity is insufficient or unknown, resolve the storage plan before a substantial operation; no universal quota or arbitrary minimum is imposed.
3. Prefer an admitted immutable base with minimal isolated per-run state. A full runtime copy needs an explicit isolation, signing, loader, consumer or evidence reason and release trigger. Do not introduce shared writable bases or change copy mechanisms merely because bytes match; such implementation changes retain their normal review requirements.
4. Record retention and release conditions in the task plan. Prefer concrete consumer/review/migration events to fixed retention periods. Avoid both unexplained indefinite retention and premature removal based on age or Issue closure.

## Minimum Retention Record

Use a compact table in the task plan and reconcile it in stage/final reports. Reference detailed local manifests where needed rather than copying them into every report.

| Artifact/root | Class and state | Owner/consumer | Identity and recovery needs | Retain reason | Release condition |
|---|---|---|---|---|---|
| Named input or output root | Class; current state | Producing task and consuming task/check | Identity/manifest; relevant bindings; recreation/restore procedure | Exact supported claim or pending use | Event and verification that permit release |

Identify source/tool/configuration versions or their manifest, required content hashes and any path, inode, mode, xattr or signing bindings. Distinguish metadata that a chosen recovery method can preserve from metadata it changes. Byte-identical replacement is insufficient when the evidence also depends on another identity.

For material outputs, include measured sizes, method and expected peak creation/restoration cost with uncertainty. Unknown consumers or unavailable reproduction inputs remain explicit risks. Keep detailed private inventories local; a public report may retain a sanitized summary and reference/digest without exposing payloads or credentials.

## Checkpoints and Handoff

- **After a run:** confirm owned process termination and cleanup outcome; secure necessary observations, original failure inputs/logs and private state before marking mutable output disposable. Failure does not make all outputs disposable.
- **At stage completion:** reconcile newly created, superseded, retained, archived, unavailable and released material. Name remaining consumers, restore-required state, deferred cleanup reasons and release events. Reuse unchanged evidence only within its valid scope; do not rerun a native matrix solely to write this record.
- **At final reporting:** carry forward remaining owners/consumers, recovery locations, required checks and unresolved disposition into the retention handoff. Task completion does not end downstream dependencies.
- **Before worktree removal or archival:** inspect ignored and untracked artifacts as well as Git state. A Git or app snapshot may exclude ignored evidence. Preserve and verify needed material independently before removal; if original-path/inode bindings require the checkout, retain it with an owner and release condition. Record whether the worktree was retained, removed or archived and what remains recoverable.

Do not silently retain everything forever. Record the next resolving event for uncertain dependencies. Do not message another task or change its state without the requester's authorization; read existing plans/reports and raise unresolved conflicts through the current task.

## Bounded Cleanup Procedure

1. Define an explicit candidate list within the authorized scope. Inspect actual producer/checker inputs, transitive dependencies and restoration requirements. A literal reference may be historical; no reference found does not exclude dynamic or relative-path consumers.
2. Recheck current ownership, process/open-handle state and concurrent or planned consumers before mutation. No open handle alone does not establish disposability. Use existing coordination/locks where applicable; do not interrupt another worker or remove its lock to obtain space. Stop if candidates or ownership change unexpectedly.
3. Identify protected authoritative inputs, private state, accepted evidence and unique failures. Record appropriate pre-change identities for the protected set and the fields the operation can affect. Reuse an existing baseline only if its inputs/scope remain valid.
4. Choose retention, deletion of proven disposable material, or recoverable archival. Equal hashes, old age, a merged Issue or a directory named cache are insufficient reasons for deletion or hard-link substitution.
5. Before retiring required original bytes, verify archive completeness/content against the frozen inventory and demonstrate actual restoration with the required identity checks. Record the tested coverage, restore command/tool, expected space and any untested properties. A compression exit code or archive listing alone is insufficient. If recovery fails or cannot preserve a required binding, retain intact originals. If originals are already retired and recovery is missing/corrupt, mark them unavailable, preserve surviving recovery material and record the unresolved loss/recovery path.
6. After mutation, verify protected identities and repository state, record exact affected roots, method, outcome, remaining recovery dependencies and measured filesystem free space. Unexpected differences stop further cleanup and require investigation. Keep receipts until their review/dependency release event; do not erase failed attempts to manufacture a passing result.

For archive publication or copying, private-state and distribution rules still apply. A local recovery archive is not a release artifact. Preserve authentication, saves, game files and signing material unless their specific removal is authorized; never infer that permission from synthetic-prefix cleanup.

## Legacy Cold-Storage Exception

The normal outcome is an intact retained artifact, a conventional verified recovery archive with explicit original availability, or deletion of proven disposable data. In-place retirement of file bytes while preserving required inode/path metadata is a narrow legacy exception where retained evidence binds those identities. It is not the default output layout for future work.

The exception requires explicitly authorized roots, no active consumers, a frozen identity inventory, verified recovery payloads and an actual restore demonstration covering the required properties. Record metadata that cannot be preserved, including change-time effects where relevant; do not claim all metadata is unchanged. Leave a visible restore-required marker discoverable at the original location with recovery references and instructions. Preserve manifests, tools and the content store for as long as any original depends on them, including through worktree cleanup.

Empty placeholders must not be admitted for execution or described as available bytes. If existing consumers cannot reliably distinguish the retired state, retain intact inputs instead. Restore and perform applicable identity/admission checks before reuse; restoration does not renew expired authorization or qualify changed inputs. These are operating requirements, not a claim that automatic runtime enforcement exists or approval to implement it.

## Storage Accounting

Report quantities separately with units, scope, method and observation time:

| Quantity | Interpretation |
|---|---|
| Logical file bytes | Content lengths; not expected physical recovery |
| Allocated/displayed size | Tool-reported allocation for the chosen paths; sharing and traversal can affect totals |
| Compressed archive size | Recovery-store cost; distinguish apparent size from allocation when relevant |
| Filesystem free space before/after | Observed net change on the named filesystem, with concurrent activity and uncertainty |

APFS clones, hard links, snapshots and concurrent writes can make these quantities diverge. Do not sum child sizes with parent totals or promise physical recovery from `du` output. Separate already released material from new candidates. A net free-space increase during concurrent work is not exclusive attribution to cleanup, and a compressed archive's apparent size is not proof of its physical cost.

## Related Procedures

- [Task workflow](task_workflow_guide.md): approval and stage boundaries.
- [Document locations](document_structure_guide.md): internal manuals versus task evidence.
- [Git workflow](git_workflow_guide.md): branch and post-merge operations, subject to retained artifact dependencies.
