# Pear documentation

`docs/` is Pear's official root for product, technical and contributor documentation. The [delivery plan](delivery-plan.md) is the single roadmap and completion-criteria reference; the root [README](../README.md) provides a short project overview. The [architecture](architecture.md) defines the intended runtime. These requirements do not establish completed implementation or qualified support.

## Start with your goal

This index uses [Diataxis](https://diataxis.fr/) to separate learning, practical
steps, reference and explanation. Existing technical guides stay in place; a
planned feature is not a usable release.

| Need | Start here |
|---|---|
| Learn by doing | [First Steam session](rosetta-preview.md#app-experience); [first local check/build](development/getting-started.md) today |
| Complete a task | [Report a game result](compatibility/README.md#submit-a-result), [get help](SUPPORT.md), [submit a change](contributing.md#propose-and-submit-a-change), [build/sign a candidate](development/preview-release.md) |
| Look up details | [System requirements](rosetta-preview.md#before-using-a-release), [CLI](rosetta-preview.md#optional-cli), [data location](rosetta-preview.md#data-and-recovery), [record meanings](compatibility/README.md#read-the-records), technical references below |
| Understand the design | [One delivery plan](delivery-plan.md), [architecture](architecture.md), [Rosetta-free contribution path](development/rosetta-free.md), [evidence and community boundaries](community.md) |

## Technical references and engineering guides

- [Website design and content components](development/catalog.md): reusable design tokens, page components, blog sources and local catalog preview checks.

- [Split native development components](development/rosetta-free.md#split-native-development-components): private source repositories, selected reconstruction/fixture/recovery interfaces and isolated Pear development selection; source and execution gates remain explicit.
- [Common runtime developer guide](https://github.com/postmelee/pear-runtime/blob/codex/task56/docs/development.md): collaborator-access build/input locks, isolated assembly and bounded recovery. Historical Wine/FEX/DXMT guides below retain their original evidence scope.

- [App release procedure](development/preview-release.md): maintainer signing and distribution gates.
- [Contributor guide](contributing.md): scope, verification, upstream policies and licensing.
- [Runtime contracts](runtime-contracts.md): seven experimental record kinds, reference validation, source handoff, and supervisor/observer ownership.
- [Native supervisor CLI](development/runtime-supervisor.md): read-only fixture setup, activation, prepared contexts, cancellation and preservation-first recovery; real-runtime execution remains unavailable.
- [Game profiles](game-profiles.md): v2 profile knowledge, two fixture profiles and researched Megabonk facts with explicit unknowns.
- [Manager language decision](decisions/manager-language.md): Rust/Swift fixture evidence, the Rust supervisor choice, reproduction scope, and remaining production gates.
- [Source qualification](source-qualification.md): reproduced public-source pins, the complete blocked audit, contributor verification commands and remaining Wine/FEX/DXMT port/build gates.
- [Host capability diagnostics](host-capabilities.md): reproduce native host probes and understand their declared development-configuration evidence and limits.
- [Wine host development](development/wine-host.md): exact component build, development authorization and finite native fixture reproduction; later translator integration has separate evidence.
- [FEX CPU integration](development/fex-host.md): fresh Wine/FEX reconstruction, finite x64 lifecycle fixtures, native refusal controls and development-only limits.
- [DXMT build and Wine Metal pairing](development/dxmt-build.md): pinned graphics construction, deterministic reconstruction commands and finite native evidence boundaries.
- [Build diagnostics](development/build-diagnostics.md): attribute build time, investigate selected Ninja targets and preserve final verification requirements.
- [Apple technical guidance](development/apple-tooling.md): select relevant pinned Metal expertise, check tool availability and preserve evidence boundaries.

## Research and observations

These existing research documents remain dated evidence and analysis within the official documentation root. Their experiments and alternatives are not automatically accepted contracts or support claims.

- [Local evidence](research/local-evidence.md): completed game experiments and their limits.
- [macOS runtime audit](research/macos-runtime-audit.md): Wine/FEX source availability, host APIs and porting work.
- [Graphics and game integration](research/graphics-and-game-integration.md): DXMT, alternatives, Steam dependencies and validation.
- [Engine and language options](research/engine-and-language-options.md): Rust, Cranelift and the path to a Pear-owned engine.
- [Platform reuse](research/platform-reuse.md): runtime, launcher, profile and Steam reuse with revision-specific boundaries.

## Where information is authoritative

| Information | Source of truth | Boundary |
|---|---|---|
| Product requirements, roadmap and completion criteria | This documentation root, with the delivery plan as the roadmap | A planned capability is not a completed capability |
| Current work state and ownership | [GitHub Issues](https://github.com/postmelee/pear/issues) and linked PRs | A dated document or issue closure alone is not execution evidence |
| Observed behavior and support qualification | Referenced verification records tied to exact inputs and tested configurations | Build, fixture, host, game and ordinary-user results have separate scopes; gaps stay explicit |
| A specific task's plan, approvals and reports | [mydocs](../mydocs/) task artifacts | These preserve work history; they do not duplicate the current product specification |
| Repeated task-management procedures | [Workflow manuals](../mydocs/manual/) and shared skills | Detailed product requirements belong in `docs/`, not `mydocs/manual/` |

For example, [host capability evidence](host-capabilities.md) establishes a bounded native host result; it does not establish an integrated Rosetta-free Megabonk runtime. Published claims must point to the actual qualification record, not infer support from the roadmap or CI alone.

## Community surfaces

The recommended role of Discussions is requests, votes, questions and proposals. Adopted decisions should be linked into the appropriate official document and tracked Issue before implementation. A vote does not by itself change support status or promise a delivery date.

The Wiki, if used, links to these documents. Reviewed game observations live in
[versioned records](compatibility/README.md); generated Markdown and the optional
GitHub Pages catalog use the same source. See the [community guide](community.md)
for reporting, moderation and publication boundaries.
