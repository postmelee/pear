# Runtime component rules

Read the [root rules](../AGENTS.md), [architecture](../docs/architecture.md), [runtime contracts](../docs/runtime-contracts.md), [source qualification](../docs/source-qualification.md) and the approved Issue plans before changes.

- Keep component input/build records distinct from runtime eligibility and game qualification. A completed audit or validated record does not clear unresolved source, port, execution or distribution gates.
- Preserve the original source-audit snapshot and historical evidence. Record new source and ordered patch identities with attribution and applicable notices. Retain upstream implementation languages.
- Materialize and build in isolated owned directories; do not mutate original input caches or use a commercial runtime as an implicit dependency. Verify actual host and guest targets separately.
- Keep tools and generated results tied to exact inputs, configuration and output hashes. Record failed, unknown and unperformed observations; never invent a passing value or source identity.
- Preserve normal macOS protections and verify real per-executable authorization before restricted operations. No helper inherits an authorization claim by assumption.
- Keep game files, credentials, prefixes, private profiles and raw diagnostics outside Git. Use reviewed sanitized evidence for public results.
- Follow the existing contract ownership boundaries; Wine-scoped build tooling does not replace the manager, observer or versioned product contracts.
