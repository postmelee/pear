# Test and fixture rules

Read the [root rules](../AGENTS.md), affected implementation rules and the task's approved verification plan. Host tests also follow the [host evidence boundaries](../docs/host-capabilities.md).

- Use redistributable fixtures with clear provenance. Keep proprietary game data, account state, authenticated prefixes, saves, private signing material and raw captures out of tests and release artifacts.
- Cover meaningful behavior and failure cases: rejected inputs, unavailable prerequisites, incomplete evidence and cleanup failures where relevant. Do not assert exact documentation prose or mirror implementation details without testing an observable contract.
- Record what actually ran. Distinguish synthetic fixture success, real host execution, platform/tool skips and game qualification. A skip or unavailable prerequisite cannot become a passing qualification claim.
- Preserve process ownership, unrelated-process survival, bounded output/execution and cleanup assertions when changing host tests. Retain original operation errors even when a paired negative-control assessment passes.
- Keep correctness diagnostics and performance measurements separate; record instrumentation/settings and input identity. Do not infer performance from an instrumented correctness run.
- Run the approved checks appropriate to the changed area. Report commands, results, limitations and evidence without imposing game or GPU dependencies on unrelated documentation checks.

## Temporary files and retained evidence

- Portable tests use the platform temporary-directory API, respecting an explicitly selected test root; do not hardcode an OS-specific temporary root. Isolate each test's files and automatically clean only its owned scratch data. Synthetic path literals used to test validation are not output locations.
- Keep retained build/run evidence separate from disposable scratch. Use an ignored task/run-owned directory such as `.build/task{issue}/runs/{run_id}/`, or an explicitly recorded external/CI artifact location. Record the owning task, input/revision identity, command, result, location and retention/cleanup conditions in the task evidence. A path alone does not prove that evidence remains available.
- Preserve required failure evidence before scratch cleanup; retain only relevant diagnostics and apply the root privacy rules. Do not commit raw private data or preserve every temporary file by default. Document platform-specific path requirements and their scope instead of silently applying them to portable tests.
