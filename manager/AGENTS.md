# Native manager rules

Read the root rules, `docs/runtime-contracts.md`, `docs/architecture.md`, the approved task plans and `host/AGENTS.md`. Tests here also follow `tests/AGENTS.md`.

- Preserve purpose-specific admission: candidate qualification runs do not require a prior game qualification; supported launches do. Synthetic policy tests never authorize real execution.
- Reuse the #3 strict parser and lifecycle boundaries. Native ABI outputs belong to callers; retain native errors, descriptor ownership and bounded byte/time limits.
- Keep payload admission, declared dependencies and actual #10 module observation distinct. Never infer immutable execution or complete observation from a native build.
- Stage 1 is a library/foundation probe only. Activation, supervision, mutable profile operations and transport require their separately approved stages.
- Keep dependency versions/checksums/notices and task-owned evidence explicit. No game files, personal state or raw private diagnostics enter Git.
