# Engineering documentation

Pear's first milestone is Megabonk on macOS/Apple Silicon without Rosetta. These documents define the intended implementation and distinguish it from current evidence.

- [Runtime architecture](architecture.md): requirements, subsystem boundaries, interfaces, language decisions, and qualification gates.
- [Delivery plan](delivery-plan.md): milestone scope, issue dependencies, and acceptance criteria.
- [Host capability diagnostics](host-capabilities.md): build and reproduce the native host tests, inspect the declared development configuration, and distinguish host evidence from runtime or distribution support.
- [Local evidence](research/local-evidence.md): completed experiments and their limits.
- [macOS runtime audit](research/macos-runtime-audit.md): Wine/FEX source availability, host APIs, and porting work.
- [Graphics and game integration](research/graphics-and-game-integration.md): DXMT, alternatives, Steam dependencies, and validation.
- [Engine and language options](research/engine-and-language-options.md): Rust, Cranelift, and the path to a Pear-owned engine.
- [Platform reuse](research/platform-reuse.md): launcher, profile, and Steam integration projects.

The architecture and plan describe work to be done. They do not certify a Rosetta-free runtime or establish performance advantages.
