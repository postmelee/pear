# Task #2 — Stage 1 report

GitHub Issue: [#2](https://github.com/postmelee/pear/issues/2)
Implementation plan: [task_m1_2_impl.md](../plans/task_m1_2_impl.md)
Stage: 1 — Native host diagnostics and result contract

## Stage Purpose

Build a small ARM64 observation tool before executing foreign ABI, memory/JIT or signing-dependent capability tests. Distinguish directly observed process facts, unavailable information and future qualification work.

## Artifacts

| File | Change Summary |
|---|---|
| `host/probe/main.c`, `observations.c`, `observations.h`, `Makefile` | System-only ARM64 C diagnostic; injectable observation boundary; bounded JSON output |
| `tests/host/test_diagnostics.py`, `diagnostic_fixture.c` | Separate fixture linked to production collector/serializer; 14 diagnostic tests |
| [Host capability guide](../../docs/host-capabilities.md) | Contributor build/run instructions, output meaning, initial observations and limits |
| [Observation evidence](task_m1_2_stage1_observations.json) | Two execution contexts, source/test and binary hashes, SDK/compiler identity |
| `.gitignore`, documentation index and historical audit link | Ignore build outputs and connect implementation evidence without rewriting prior research |

## Body Change Scope / Lossless Preservation

New diagnostic code does not alter the experimental game prefix or run Steam, Wine, FEX, DXMT or Megabonk. It does not call the dynamically resolved ABI/page/thread functions or execute generated code. Existing architecture requirements and historical research remain intact. New repository prose and code comments are English.

The production CLI has no fixture controls. Tests inject observations through a C callback table in a separate executable. JSON text is bounded and escaped; invalid UTF-8, oversized values and invalid typed observations fail explicitly rather than silently changing evidence.

## Verification Results

| Check | Method | Result |
|---|---|---|
| Native build | `make -C host/probe` | Passed with Apple clang 21, SDK 26.5, `-Wall -Wextra -Werror` and ARM64 target |
| Diagnostic behavior | `python3 -m unittest discover -s tests/host -p 'test_*.py' -v` | All 14 tests passed; no failures/errors |
| Actual binary architecture | `file` and `lipo -archs` on the built diagnostic | Mach-O 64-bit ARM64; only ARM64 slice |
| Tool-sandbox observation | Execute and parse the JSON report | Own translation query unavailable with errno 1; not converted to false |
| Ordinary host observation | Reviewed read-only execution outside the tool sandbox | ARM64 process, own translation query observed false |
| Host values | Two saved JSON reports | macOS 26.5.2/build 25F84; 16,384-byte process pages |
| Dynamic APIs | Resolve four named symbols without invoking them | All four resolved; execution remains not run |
| Signature boundary | Read generic metadata without identity output | Ad-hoc category; validation/authorization remain not assessed |
| Source review | Independent production/test work plus primary-worker review | No fixture mode in shipped CLI; no restricted execution path |
| Staged diff and evidence integrity | Diff hygiene, hashes, English text, JSON and link validation | Verified before this stage commit |

Meaningful error cases include EPERM/ENOENT translation queries, a non-boolean translation value, absent API symbols, unavailable signature information, unsupported and Intel architecture fixtures, JSON injection/control characters, invalid UTF-8, overflow and invalid CLI options. Real-host tests and synthetic observations are distinguished; fixtures never qualify the host.

The exit status reports whether a diagnostic document was produced. It is not an aggregate capability pass. Every capability field is `not_run` and every runtime/game/distribution qualification field is `not_assessed`.

## Residual Risks

- This is a working native diagnostic, **not a Rosetta-free Megabonk runtime**. Issue #2 remains open.
- A 16 KiB default process and present 4 KiB API do not demonstrate Windows page/protection/decommit semantics.
- Ad-hoc signing and symbol resolution do not authorize restricted macOS capabilities or ordinary-user distribution.
- The diagnostic's macOS 13 build target is only an observation-tool deployment choice; the proposed runtime floor remains independently qualified.
- The finite diagnostic test suite does not cover the upcoming child containment, JIT, x18, callback, signal or thread behavior.

## Impact on Next Stage

Stage 2 adds a disposable child runner with timeouts, signal/exit reporting and output limits before baseline low-mapping and JIT leaf tests. Its verification must preserve this stage's status distinctions and terminate only its own test children. Restricted signed ABI work remains in later stages.

## Approval Request

Review the completed Stage 1 artifacts and evidence, then approve starting Stage 2 under the existing implementation plan. No Stage 2 source has been implemented in this stage.
