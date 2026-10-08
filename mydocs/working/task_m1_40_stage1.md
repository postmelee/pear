# Task #40 Stage 1 — Attributed GameAssembly Image-Size Refusal

GitHub Issue: [#40](https://github.com/postmelee/pear/issues/40)
Implementation plan: [task_m1_40_impl.md](../plans/task_m1_40_impl.md)
Stage: 1 — complete, October 9, 2026.

## Stage Purpose

Identify the first actual loader refusal for the owner's unchanged GameAssembly
and propose a bounded correction. The diagnostic confirms the size gate; no
admission limit has been changed and DLL initialization remains blocked.

Context: approved task/implementation plans and explicit Stage 1 continuation;
root/runtime/host/tests rules, architecture, delivery plan and #8 Stage 4 evidence.
Applied stage-report and repository todo procedures. Metal-specific guidance is
not applicable because no graphics behavior is changed. #10/#11 have independent
worktrees; their sources and outputs were not modified.

## Artifacts

| File | Change Summary |
|---|---|
| `runtime/wine/patches/gameassembly/0001-admission-diagnostics.*` | Ordered opt-in caller/parser diagnostics with exact pre/post images; original statuses and limits preserved |
| `tools/wine/image_admission_inputs.py` | Original failure, source/runtime, snapshot and 69 original file bindings |
| `tools/wine/image_admission_build.py` | Source-bound ntdll control relink and two diagnostic objects |
| `tools/wine/image_admission_runtime.py` | Existing signing reuse; only ntdll code changes in a separate immutable candidate |
| `tools/wine/image_admission_run.py` | #8 owned-game runner adapted for exact candidate and file identity |
| `tools/wine/image_admission_check.py` | Raw-log attribution, before/after authorization, native observations and cleanup checks |
| `tools/wine/image_admission_budget.py` | Actual relocation inspection and proposal accounting |
| `tests/wine/test_image_admission*.py` | Six reader controls and three actual composed-parser checks |
| [Stage observations](task_m1_40_stage1_observations.json) | Allowlisted results and hashes; no private paths or logs |

## Body Change Scope / Lossless Preservation

Wine C and existing Pear ownership are retained. Inspected pinned Wine
`virtual.c` mapping and the final composed `pear_pe_arena.c` parser,
`parse_relocations`, staging and slot publication. Wine's LGPL-2.1-or-later notice
and the original Pear MIT owner attribution remain intact; no upstream submission
was made. No new FEX code, owner ABI, allocator, Metal bridge or manager contract.

The diagnostic records PID, descriptor, device/inode/file size, phase and original
NTSTATUS. It preserves errno and emits a bounded line only when explicitly enabled.
The independently admitted game clone binds those file identifiers to the original
GameAssembly SHA-256. Truncated/missing/misattributed observations fail assessment.

The first control relink used #8 build3 objects and reproduced that build, but its
code did not match the final runtime ntdll; the strict origin gate rejected it
before diagnostic compilation/execution. Following the runtime source ledger
identified the actual origin in retained #5 `stage6-wine3`. The three affected
source preimages are identical to the planned composed source. Reusing that
origin's recorded recipes reproduced its ntdll and matched the signed baseline.
The failed control and logs remain retained; the comparison was not weakened.

Final `diagnostic-build2` rebuilds only `pear_pe_arena.o` and `virtual.o`, retaining
and checking compiler dependencies and all other native link inputs. Existing
signing, authorization, APISession, restricted bootstrap, output limits, sentinel
and owned cleanup are reused. #8's original candidate, producers and failure
records remain untouched. Official documentation is unchanged at this stage.

## Verification Results

Environment: ARM64 M4 Pro, macOS 26.5.2, Xcode 26.6 (17F113), existing development
profile, normal security protections. Private records bind the exact tools and
payloads. This is an instrumented startup diagnostic, not performance testing.

Commands executed successfully after the attributable origin correction:

```sh
python3 -B -m tools.wine.image_admission_inputs --baseline-repo "$PEAR_TASK8" --output .build/task40/inputs2
python3 -B -m tools.wine.image_admission_build --inputs .build/task40/inputs2 --mode diagnostic --output .build/task40/diagnostic-build2
python3 -B -m tools.wine.image_admission_runtime --inputs .build/task40/inputs2 --build .build/task40/diagnostic-build2 --output .build/task40/diagnostic-runtime1
python3 -B -m tools.wine.image_admission_run --inputs .build/task40/inputs2 --runtime .build/task40/diagnostic-runtime1 --case game-start --output .build/task40/diagnostic-run1
python3 -B -m tools.wine.image_admission_check --run .build/task40/diagnostic-run1 --require refusal
python3 -B -m tools.wine.image_admission_budget --inputs .build/task40/inputs2 --run .build/task40/diagnostic-run1
PEAR_IMAGE_ADMISSION_BUILD="$PWD/.build/task40/diagnostic-build2" python3 -B -m unittest discover -s tests/wine -p 'test_image_admission*.py'
python3 -B tools/check_governance.py
git diff --check
```

- Actual owned game run: first nonzero parser result is `parser.return08`,
  `STATUS_NOT_SUPPORTED` (`0xc00000bb`), followed by the same caller result on the
  same mapping attempt and exact cloned file. This is the `SizeOfImage` gate.
  Its nonzero size and 4 KiB alignment are valid; only the maximum is exceeded.
- Required image: **57,647,104 bytes**; current maximum: **38,993,920 bytes**.
  Earlier parser target/header/flags/alignment checks did not reject this attempt.
  Later checks remain unexecuted for the game and may reveal more constraints.
- One new game run completed diagnosis and owned cleanup in **10,581 ms**, within
  the 120-second maximum. The diagnostic stopped on an attributable refusal;
  it did not count this as a successful game exit.
- Authorization checks before/after, original 69-file integrity, unchanged runtime,
  reaped owned children and unrelated sentinel survival all passed. Forty-one
  native images have ARM64 closure/signature evidence; observed process/module
  events were native. Complete late-load coverage remains #10.
- **Nine tests passed, zero skipped:** six evidence tests plus three real C parser
  tests under UBSan. The same large synthetic PE returns the same status before
  and after instrumentation; an earlier flag refusal is distinguished; opt-out
  emits no diagnostic. The real `pear_pe_plan` size is compile-checked at 88 bytes.
- Documentation governance and whitespace checks passed. No full CPU/graphics
  qualification was repeated for this diagnostic-only candidate.

Private inputs, diagnostics, clone/prefix and signatures remain in ignored
`.build/task40/`; summarized hashes are in the linked observations. Original
failure and the first rejected control build remain preserved. No GitHub push,
PR, proprietary binary edit, authenticated Steam copy or signing-policy change.

## Residual Risks

- Size acceptance alone does not prove role validation, relocation, publication,
  imports, TLS/DllMain or Unity initialization. Those gates remain required.
- The observed loaded set is bounded startup evidence; it is not the game's final
  memory footprint, concurrency limit or complete process/module qualification.
- A 64 MiB cap bounds parser payload allocations, not process RSS. Allocation
  bookkeeping, source buffers, FEX and other runtime memory remain additional.
- Existing development authorization is not ordinary-user distribution approval.

## Impact on Next Stage — Concrete Budget Proposal

| Item | Measured / proposed bytes |
|---|---:|
| GameAssembly rounded slot | 57,671,680 |
| Staging bytes | 57,647,104 |
| Per-image page metadata | 14,074 |
| Current relocation-array allocation for this file | 1,738,640 |
| Plan structure | 88 |
| Total temporary parser payload for this file | 59,399,906 |
| Observed PE high-water by diagnostic cleanup (44 publications) | 111,083,520 |
| Conservative append of this DLL to that high-water | 168,755,200 |
| Existing PE interior | 1,050,345,472 |
| Remaining interior after that append | 881,590,272 |
| Proposed per-image maximum | 67,108,864 (64 MiB) |
| Proposed worst-case single-plan payload bound | 100,679,768 |

The game has 1,207 relocation blocks, 429,566 DIR64 destinations and 266 padding
entries, with no overlapping eight-byte destinations in this read-only inspection.
The parser allocates from directory size, not only nonpadding count; the proposal
retains that real accounting and all malformed/overlap/overflow checks.

**Propose raising only the per-image limit to 64 MiB**, preserving the current PE
interior, 756 slots, dynamic region, FEX geometry and single-MAP_JIT mapping. The
existing formula permits up to 32 MiB relocation-array storage at that ceiling,
plus 64 MiB staging, 16 KiB page metadata and the 88-byte plan. This is a payload
bound excluding allocator overhead; plans are freed before subsequent guest
initialization. Do not claim the whole game's future demand fits from this run.

Stage 2 must verify the required size and new aligned boundary, rejection beyond
it, invalid section/relocation cases, relocation to a different base, failure
rollback and unload/reuse under the unchanged ownership/publication model. Use
fresh #40 correction outputs and the proven #5 native origin; preserve #8's final
FEX/surface overlays. Additional refusal inside this loader remains part of #40;
a new owner/ABI or mapping redesign requires a reviewed amendment.

## Approval Request

Approve the Stage 1 evidence and this 64 MiB per-image budget, then proceed to
Stage 2 correction and loader-fixture verification. Game DLL initialization and
the mandatory changed-candidate CPU/graphics regressions remain later gates.
