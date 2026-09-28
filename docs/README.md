# Pear documentation

`docs/` is Pear's official root for product, technical and contributor documentation. The [delivery plan](delivery-plan.md) is the single roadmap and completion-criteria reference; the root [README](../README.md) provides a short project overview. The [architecture](architecture.md) defines the intended runtime. These requirements do not establish completed implementation or qualified support.

## Start here

- [Delivery plan](delivery-plan.md): Phase 1-5, technical M1, proposed ordinary-user M2, independent R1 and acceptance dependencies.
- [Contributor guide](contributing.md): requests, reports, testing, documentation, profiles and code contributions; no AI subscription required.
- [Runtime architecture](architecture.md): requirements, subsystem boundaries, interfaces, language decisions and qualification gates.
- [Host capability diagnostics](host-capabilities.md): reproduce native host probes and understand their declared development-configuration evidence and limits.

## Research and observations

These existing research documents remain dated evidence and analysis within the official documentation root. Their experiments and alternatives are not automatically accepted contracts or support claims.

- [Local evidence](research/local-evidence.md): completed game experiments and their limits.
- [macOS runtime audit](research/macos-runtime-audit.md): Wine/FEX source availability, host APIs and porting work.
- [Graphics and game integration](research/graphics-and-game-integration.md): DXMT, alternatives, Steam dependencies and validation.
- [Engine and language options](research/engine-and-language-options.md): Rust, Cranelift and the path to a Pear-owned engine.
- [Platform reuse](research/platform-reuse.md): launcher, profile and Steam integration projects.

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

The initial recommended Wiki role is navigation and links to these documents. It should not maintain a second copy of roadmap, contribution or engineering rules. These roles do not require either surface to be activated or populated now; use available GitHub Issues for current tracked work.
