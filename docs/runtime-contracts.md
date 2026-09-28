# Runtime contracts

Status: **proposed design**, September 28, 2026, Issue [#3](https://github.com/postmelee/pear/issues/3), Stage 1. The [registry](../runtime/contracts/contract-index.json) lists planned version 1 schemas; those schemas and their validators do not exist yet. The [research example](../runtime/contracts/examples/research-lock.json) is an incomplete design example, not a runtime lock that can be executed. No runtime, manager language, game support, or distribution capability is qualified here.

This specification develops the boundaries in the [architecture](architecture.md) and [delivery plan](delivery-plan.md). Its audience is contributors implementing source/build tools, the manager, profiles, and observation/qualification tooling. The current stage fixes responsibilities and identity semantics; Stage 2 supplies executable structure and semantic checks. JSON parsing alone does not establish compliance with this proposed contract.

## Record kinds and consumers

Every product record has a `record_kind`, integer `schema_version`, `record_context`, and a human-readable `record_id`. Version 1 is planned, not currently supported by an implementation. A record ID is a label; it does not replace a content digest. IDs must be unambiguous within an input bundle. The registry is design metadata, not an eighth product-record kind.

| Kind | Producer and primary consumers | Meaning and identity links |
|---|---|---|
| `runtime_lock` | Runtime/build maintainers; build, packaging and manager tools | Selected source/component/patch identities; dependency relationships; toolchain, SDK, flags and host/guest targets; compatibility family; host/signing prerequisites and terms references. Links to source evidence, not to an artifact built from itself. |
| `runtime_artifact` | Build/packaging tooling; manager and qualification tooling | Exact lock reference, produced payload paths/hashes, native/PE inventory, build provenance, packaging/signing observations and requirements. Describes produced bytes; later qualification is an external record. |
| `game_profile` | Profile contributors; manager and test tooling | Store/App ID, explicitly selected guest executable and bounded arguments/settings, runtime compatibility requirements, known game/build identity, expected save roots and declared feature requirements. Compatibility claims are derived from qualification, not asserted by a recipe. |
| `launch` | Supervisor produces requests; supervisor/observer produce events; observer and run aggregator consume them | Discriminated `request` and `event` variants. The request freezes selected lock/artifact/profile identities, run purpose and local root handles; events describe readiness, execution and termination against that request. |
| `failure` | Validator, supervisor or observer; diagnostics and run aggregator | Stable phase/category/reason, affected component/process token where known, bounded numeric details and evidence references. May reference the launch request, but never the later run report that includes this failure. |
| `run` | Supervisor and evidence aggregator; qualification tooling | Final lock/artifact/profile/game/Steam identities, scoped Mac/OS/configuration, process/module timeline, selected translator/renderer, exit and feature outcomes, failures, timing and observation gaps. References the launch request and completed event/failure evidence. |
| `qualification` | Test/review workflow; manager support selection and compatibility presentation | Test revision, required checks, applicable configuration, exact input and run/evidence references, reproduction scope, date, reviewer attribution and known limitations. Derives a bounded support decision; does not rewrite its inputs. |

The seven schemas will live under `runtime/contracts/v1/`, with shared types in `common.schema.json`. A launch event is not another top-level kind: its variant determines its fields and allowed references. Raw streams and private operational storage are outside the public contract.

## Validity, state and eligibility

These questions are independent:

1. **Can the record be read?** Strict, bounded UTF-8 JSON parsing must reject duplicate keys before a decoder loses them, malformed encoding, unexpected types and unsupported numeric forms.
2. **Does its structure have defined meaning?** A locally registered kind/version and schema determine required fields and allowed extensions. Unknown versions, mandatory semantics, operations or unrecognized fields fail explicitly. Remote references are not fetched during validation.
3. **Are its relationships and bytes consistent?** Resolve permitted local references, check actual content digests, expected kinds and versions, compatible component/ABI families, path rules and the absence of identity cycles. Matching bytes alone do not establish publisher authenticity or correct runtime behavior.
4. **Is the requested use eligible?** Evaluate missing prerequisites, record context, host/signing state, operation ownership and the matching evidence required for that purpose. A producer-supplied `supported` or `launch_allowed` assertion is not authorization.

| Context or derived state | Meaning | What it does not authorize |
|---|---|---|
| `research` context | Partial investigation, candidate selection or an explicit unknown/failed observation | Runtime execution or game qualification, even when structurally valid |
| `fixture` context | Redistributable, self-owned inputs and tests scoped to the declared experiment | Promotion to real upstream source pins, runtime/game support, or ordinary-user distribution |
| `runtime` context | Actual source/build/profile/run records intended for the production integration path | Execution or support based solely on the context label |
| Proposed | A candidate lock/profile or design exists | A claim that matching artifacts were built |
| Built | A verified artifact identifies its exact lock and payload | Passing required execution or game tests |
| Tested | Matching run evidence records actual outcomes and its bounded scope | Passing every required qualification gate or support for untested configurations |
| Supported | A matching qualification record passes all required checks for its named configuration and purpose | All-Mac support, later changed inputs, or a broader distribution route |

Proposed/built/tested/supported are evidence-derived views of a record set, not a mutable progression field inside the lock. A failed run remains a tested failure. `unknown`, `unsupported`, `failed` and `passed` observations retain their distinct meanings; absence is never a passing result. Unknown collections carry a reason and an explicit unknown state: an empty patch list with unknown status does not mean that no patches are required.

Runtime launch and supported launch need different gates to avoid a qualification deadlock. A future explicitly scoped **qualification run** may use a complete built candidate whose required host, signing, compatibility and ownership checks pass, before game qualification exists. A **supported launch** additionally needs current qualification for the requested configuration. Neither purpose permits an incomplete research record, an unresolved required identity, a required unsafe operation, or an unavailable execution permission. These gates are to be implemented and tested in later stages/tasks.

Developer execution and ordinary-user distribution are separate scopes. [#2's host evidence](host-capabilities.md) describes its own tested binaries, Mac, OS and authorization; it is not automatic authorization or proof for a future Wine build. Reuse it by a scoped evidence reference, preserving the original record unchanged.

## Exact-byte identity and acyclic references

A product-record content reference identifies its expected kind/version, a permitted bundle-relative location and a typed digest. The proposed digest type is SHA-256 over the **exact stored UTF-8 bytes**, including whitespace and the final newline. References are written by a different record after the referenced bytes are final. No record contains its own content digest. Editing even formatting changes its identity and requires updating/rechecking dependents.

Raw bytes, source trees, archives, patch files, produced payloads and signing observations have explicitly different digest scopes. A Git commit or tree object ID includes its Git object format and is not a SHA-256 file digest. A hash of a Git tree listing is identified as a listing hash; it is not described as a hash of concatenated source contents. Repositories, source authenticity evidence and acquisition methods come from the source audit; changing a digest label cannot establish trust.

References point from later records toward already finalized inputs:

```text
qualification -> completed run -> launch request -> artifact -> runtime lock
       |              |                |
       +--------------+----------------+-> game profile
                      +-> completed launch events / failures
                                      +-> launch request
```

An event may reference its earlier request and preceding event; it cannot reference a later event or completed run. A failure may carry a logical `run_id` for correlation, but not the digest of the run that will include it. Correlation labels do not certify bytes. A bundle must reject reused labels with inconsistent meanings, conflicting input digests, unresolved required references and cycles.

Architecture section 7 describes artifact qualification status and evidence references. This design refines their representation to avoid a cycle: the immutable artifact/profile supplies identity, while a later **qualification overlay** references those exact inputs and runs. It is an ordinary `qualification` record, not a new kind. An interface can display derived status by locating matching qualification records; it must not insert that qualification's digest into the very artifact/profile it qualifies. Historical links cannot qualify changed bytes, and a status cache is not authoritative evidence. The architecture file is unchanged in Stage 1.

Signature/provisioning observations identify the exact payload/context tested, with private keys, profiles and personal identity data excluded. A detached signature or external observation has its own identity; it does not substitute for the payload digest. A byte-identical signature is not the definition of a reproducible source build. Any relevant payload, lock, profile, game, Steam, signing or configuration change requires re-evaluating affected evidence.

## Source handoff with Issue #1

[#1](https://github.com/postmelee/pear/issues/1) owns facts in `runtime/sources/manifest.json` and its local `source_audit` format. #3 owns the product-record representation and references under `runtime/contracts/`. The source audit is an input, not a product lock or an eighth product-record kind. Neither task depends on the other finishing its implementation.

| Source-audit fact | Product-contract meaning and rejection boundary |
|---|---|
| Stable component ID, role and dependency IDs | Logical component relationships; reject duplicate/conflicting identities and missing required dependency references. Role does not establish native or guest architecture. |
| Canonical source URL and immutable ref | Identifiable acquisition input. A moving branch, display version or guessed commit is insufficient for executable runtime selection. |
| Typed acquired-content digest and scope | Verification of the declared bytes/representation; unknown digest remains unknown. Preserve Git object format, archive bytes and tree-listing scopes rather than coercing them into one file hash. |
| Ordered patches, bases, origin and applicability | The build input sequence and its evidence. Unknown/missing port work is a gap, not an invented empty series or patch hash. |
| Toolchain/SDK identities, build constraints and host/guest targets | Candidate build context; source-declared, locally observed and actually build-tested versions remain distinct. Native Mach-O ARM64 and guest PE x64/i386 are separate roles. |
| License/notice locations, exceptions and contribution-policy references | Version-specific terms/provenance evidence; public availability is not a license conclusion, and reuse rights do not imply upstream submission permission. |
| Inspection date/scope, evidence, availability and decision | The inspected source-readiness claim and gaps, not behavioral validation. `record_valid` and `audit_complete` are audit results rather than runtime launch permission. |

An audit's `go` permits its named build/implementation work, not game execution. `needs-port` requires the named gaps to be implemented and verified by their owning tasks. `blocked` remains a no-go for that input path even if the completed investigation's Issue closes. A future build record may demonstrate that earlier named port gaps were resolved with attributable new inputs; it may not silently reinterpret the old audit decision.

The research example uses the intended Wine/FEX/DXMT component labels but selects no upstream URL, commit, hash, toolchain, license or build target as verified. Its component coverage is explicitly incomplete. Later fixtures may use computed identities from owned content, labeled `fixture`; none becomes a substitute for #1's real findings. Final integration must verify the mapping against actual source and build records.

## Launch and mutable-state ownership

[#9](https://github.com/postmelee/pear/issues/9) owns the production manager/supervisor. A launch request selects explicit identities and local root handles; it does not carry a shell program. Executables are selected by declared profile/artifact entries, never by largest-file or filename heuristics. The host supervisor uses argument arrays and an allowlisted scoped environment; no shell interpolation, global environment changes, arbitrary downloaded script, or ambient environment dump is part of the contract.

| Storage / operation | Owner and boundary |
|---|---|
| Runtime artifact | Immutable verified content; users' profiles, logs and generated caches cannot write into it. A future installer stages content before activation. |
| Prefix | Supervisor-owned local data scoped to runtime compatibility family and game/library context. Incompatible upgrades cannot mutate the only usable copy. Migration/recovery implementation remains outside #3. |
| Saves | User-owned data with explicit local location/consent boundaries; no upload, overwrite, deletion or automatic backup is implied by a profile. |
| Caches | Disposable local data keyed by guest identity, translator/version/configuration, CPU features, ABI and relevant runtime identity. Unknown/incompatible identities forbid reuse. |
| Logs and raw observation data | Local bounded operational storage; public records are allowlisted/redacted derivatives with explicit omissions. |
| Process creation/reaping/termination | Supervisor only; target verified owned processes/groups, preserve identity across PID reuse and report cleanup failures. Never terminate unrelated Wine sessions by a global name. |

The initial profile-operation vocabulary is limited to declarative argument lists, explicitly approved environment keys, renderer selection from the selected runtime's supported set, and typed setting values within declared prefix-relative locations. Operation names do not authorize their implementation: unsupported operations or unknown values must be rejected. Arbitrary commands, registry scripts, downloads, deletion/migration actions and writes outside owned roots are not profile escape hatches. Actual per-setting allowlists and executor support are later implementation gates.

Host artifact paths are normalized relative entries, not ambient absolute paths. Local root handles are resolved by the manager outside the public record; Windows guest paths have a separate type and are not normalized with host filesystem rules. Reject traversal, NULs, ambiguous path interpretation, unapproved absolute locations, symlink escapes and writes to immutable content. #9 must enforce ownership again at use time; validating a path string once cannot remove filesystem races. Private absolute roots and argument values that may contain secrets are not emitted into public evidence.

## Supervisor and observer handshake

[#10](https://github.com/postmelee/pear/issues/10) observes required process/module execution. It consumes the #9 lifecycle interface; it does not reap, signal, restart or modify the supervisor's children/prefixes. The interface sequence is:

1. The supervisor finalizes the launch request and assigns a run/capture-session identity before execution.
2. The observer acknowledges readiness for that exact request and declares what it can observe, including short-lived or detached required helpers. Readiness is a prerequisite for covered execution, not proof that later coverage will be complete.
3. The supervisor starts the owned process and publishes a process-instance identity; the observer associates observations with it and any required descendants/helpers.
4. Both parties publish monotonic sequence numbers within their producer stream, producer IDs and elapsed-time bases. Sequence gaps, dropped observations, late attachment, ambiguous ancestry and inaccessible modules are explicit gaps; timestamps alone do not establish a total cross-producer order.
5. The supervisor reports termination and owned cleanup. The observer reports its final covered interval, unresolved required processes and gaps. A run can be finalized as incomplete, but cannot qualify as completely observed.

Required-readiness refusal or timeout prevents starting the covered launch; a failure record explains why. If readiness is lost after start, retain the gap and keep qualification failed/unknown for that requirement. #9's later cleanup/cancellation policy owns any termination decision. An experimental run deliberately lacking coverage must be labeled as such and cannot be a supported launch or Rosetta-independence proof.

A PID alone is insufficient. Local attribution combines the run/capture session, OS process-generation or creation observation and PID; the observer records the observation method and time base. If that identity cannot be established, the association is unknown. Public records can use per-run process tokens with the needed non-personal generation evidence; they must not publish hardware provisioning identifiers or credentials. Required detached helpers need an evidence-backed association, not an assumption from a matching executable name.

Record host images' actual running Mach-O slices/translation state separately from guest PE architecture and selected FEX modules. A parent's `sysctl.proc_translated` observation applies only to that parent. Guest x64 execution through the selected translator is expected; an unobserved or Rosetta-translated required host process blocks Rosetta-independent qualification. A static ARM64 file, a ready observer, or the absence of a visible Rosetta service is insufficient.

## Failures, privacy and support decisions

Failure categories distinguish contract validation, source/build, host capability, signing, supervision, observation, CPU translation, Windows API, graphics, Steam integration and game behavior. Each failure carries the failing phase, a stable reason code, bounded typed details and known component/process references. Unknown cause stays unknown; do not invent a CPU or graphics diagnosis from a generic crash. Raw parser input, stdout/stderr, command lines and whole environments are not public error messages.

Public run/qualification records use allowlisted fields and bounded evidence references. Credentials, tokens, personal paths, Apple signing/profile material, authenticated prefixes, proprietary files and saves stay local. Redaction never converts omitted required observations into passing evidence. Host/chip/OS and configuration observations describe their actual scope; they are not unique-device identifiers. Public reviewer attribution must be intentionally supplied, not scraped from local accounts.

Exporting a redacted record creates a **new immutable derivative with its own byte identity**; never overwrite an original record or retain its digest for different exported bytes. A private launch request can contain arguments or local details that must not be exported. Its public derivative uses only privacy-safe correlation to the local original and explicitly declares withheld references and reduced disclosure. A publicly inspectable partial bundle is not a self-contained, fully validated run: missing private references cannot be treated as publicly verified. Full local validation and the exported view retain distinct scope, and Stage 2 must represent and test that distinction.

The consuming application or review workflow supplies its trusted reviewer, evidence-origin and qualification policy **outside the submitted JSON**. Matching digests, a named reviewer, a `passed` result or a self-declared qualification do not grant their producer trust. The consumer must apply its independently configured policy before accepting a support claim, including any reliance on a local review that public redaction prevents others from reproducing. Stage 1 defines this boundary; it implements no signature authority, trust service or PKI.

Qualification names the exact test revision, configuration, required feature set, dates and remaining gaps. Required unknown/unsupported/failed results prevent the relevant support claim. Known limitations and optional untested features remain visible. Votes, a proposed recipe, successful schema validation or a game menu are not qualification. The first M1 game record still needs the [delivery plan's complete gates](delivery-plan.md#first-milestone-completion), including required-process coverage and sustained gameplay.

## Research example: explicit refusal to launch

`examples/research-lock.json` has `record_context: research`, an unknown compatibility family, no source audit identity and incomplete component coverage. For each intended component, its source, patch, build and terms facts are unknown, with null values and explanatory reasons. The root's host/signing requirements and dependency coverage are also unestablished. Empty evidence means none is supplied; it is not a passing result.

The design review therefore yields: JSON syntax may be readable; schema validity is **not yet tested**; semantic completeness is absent; runtime launch and qualification must be refused. Changing the context string would not supply the missing identities or evidence. Stage 2 must test that refusal and separately accept this as an honest incomplete research record. No computed eligibility field is embedded in the example for a consumer to trust blindly.

## Remaining implementation work

Stage 2 must define exact field schemas, parse/collection bounds, stable rejection codes, local reference resolution, eligibility checks and adversarial fixtures. Supported version transitions require explicit consumer support; published schemas are not silently reinterpreted. Any semantic change that would make an old consumer accept a different operation requires a new supported contract version. Unknown extensions remain non-executable unless a later version explicitly defines them.

Stages 3–5 then implement equal bounded Rust/Swift experiments, make a measured manager-language decision and reproduce the final results. Until those checks exist, this document and registry remain proposed design; no schema validation, safe execution, source readiness, runtime support or end-user release is asserted.
