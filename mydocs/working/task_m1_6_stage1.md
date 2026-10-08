# Task #6 Stage 1 — Source-bound CPU Corpus and Reference Contract

GitHub Issue: [#6](https://github.com/postmelee/pear/issues/6)
Implementation plan: [task_m1_6_impl.md](../plans/task_m1_6_impl.md)
Stage: 1 — complete locally on October 8, 2026

## Stage Purpose

Define what the CPU qualification will compare before running the translator.
Inventory the pinned source, select meaningful instruction/boundary cases, freeze
setup and defined-output masks, and keep unavailable reference execution explicit.
The requester approved the task plan and then explicitly continued the detailed
implementation/Stage 1 approval request in this thread.

Context: approved task and implementation plans; root/runtime/FEX/tests/docs rules;
architecture, delivery plan, runtime contracts and #5 final report. Use
Hyper-Waterfall v0.3.0 task-stage-report/todo procedures. No Metal work applies.

## Artifacts

| File | Change Summary |
|---|---|
| `tests/cpu/corpus.json` | 12 original upstream ASM selections, 10 required boundary contracts, setup, feature requirements, defined comparisons and explicit unsupported coverage |
| `tests/cpu/sources.json` | Source revisions and hashes, reviewed FEX/Madeira/Hangover functions, selection IDs and full ASM inventory digest |
| `tests/cpu/LICENSES/FEX-MIT.txt` | Unmodified upstream notice, checked against the reviewed source |
| `tools/cpu/corpus.py` | Bounded inventory/config reader, strict selected-subset validation, complete exclusion census and source-only output |
| `tests/cpu/test_corpus.py` | 14 focused false-success/refusal tests |
| [Sanitized observations](task_m1_6_stage1_observations.json) | Actual input/output hashes, counts, tool availability and no-execution scope |

## Body Change Scope / Lossless Preservation

All paths match the approved location judgment. No product guide, runtime patch,
Wine/FEX binary, signing grant or previous #5 report changed. This is original
Python validation using the existing Wine bounded readers and strict JSON helpers;
no new source downloader, engine or general execution framework was introduced.
No Madeira implementation code was copied in this stage. Its generator/driver
remain Stage 2 adaptation candidates with their applicable GPL notices.

The full 2,270-row census is generated in ignored `.build/task6/`, not inserted
into the active plan or report. The tracked JSON is machine-readable fixture
metadata. Unique source/config findings remain in this report and observations;
#5's absolute-path-bound source/tool/runtime worktree is preserved.

## Verification Results

Execution context: native ARM64 Python 3.14.4 on the existing development Mac.
The earlier plan listed historical Python 3.13 availability; the actual interpreter
used here is recorded explicitly. This stage performed source inspection and
synthetic validator tests only, with no guest, native reference or game execution.

Evidence reuse: #5's final FEX source preparation provides unchanged upstream ASM,
config readers and license; exact current bytes were inventoried. Existing five
Pear boundary fixtures are source-hash references for later comparison, not newly
executed results. The recorded LLVM-MinGW clang hash matched its retained receipt;
Mach-O inspection found an ARM64 slice (also an x64 slice). No compiler was run.

Commands executed:

```sh
python3 -B tools/cpu/corpus.py --source "$PEAR_FEX_SOURCE" --manifest tests/cpu/corpus.json --output .build/task6/stage1-verification
python3 -B -m unittest discover -s tests/cpu -p test_corpus.py -v
python3 -B tools/check_governance.py
git diff --check
```

Results:

- Full source census: 2,270 ASM files; 12 selected, 2,258 explicitly outside the
  initial corpus or rejected by the declared harness subset. Selection covers
  partial registers/carry/flags, packed and scalar floating point, conversion,
  memory setup/addressing, scalar RMW semantics and an AVX upper-lane contract.
- Ten boundary contracts: five source-bound #5 cases (API/callback, TLS worker,
  guest fault/data guard, invalidation, suspend/context); five planned additions
  (ABI state preservation, guest SEH/unwind, locked RMW, message passing and
  store buffering). These contracts are all marked unperformed for #6.
- The AVX case keeps four 64-bit lanes per vector; it is required if exposed by
  the candidate. Actual guest features and native AVX/OSXSAVE remain to observe.
  No feature-gated case silently loses upper-lane expectations.
- Undefined AF after XOR is masked before execution. Shift-zero flag comparisons
  keep defined arithmetic flags and exclude OS-controlled/reserved bits. Other
  selected values retain full-bit comparisons; no failure-driven relaxation.
- Strict parsing found duplicate CONFIG keys in `FEX_bugs/pdep_overlap.asm` and
  `VEX/vpackuswb.asm`. The initial inventory stopped rather than silently taking
  the last value. Final census records both as excluded invalid configurations;
  neither is a selected case or a passing result. Original upstream files remain
  untouched.
- 14 validator tests passed, no skips: altered/extra source, incomplete census,
  missing/duplicate cases, changed expectations, missing/zero masks, unknown
  CONFIG, conflicting TSO/feature overrides, AVX width, memory initialization,
  duplicate JSON keys, unsafe/symlink paths, retained license and false execution
  promotion. No broad historical runtime suite was repeated.
- Governance passed: 25 documents, 231 local targets. `git diff --check` passed.
- Aggregate output is `scope=source_inventory_only`, `inventory_valid=true`,
  `cpu_qualified=false`, `guest_execution=false`, `reference_status=unavailable`.

### Reuse Decisions

FEX's native HostRunner initializes CPU state but depends on Linux
signals/ucontext/modify_ldt and is excluded from MinGW by its CMake recipe. Reuse
its CONFIG/expectation semantics; do not embed those host assumptions into Pear.
The selected harness subset rejects unsupported Match/Ignore and MM/x87 data
explicitly rather than dropping them. The nonselected census is not a statement
that those instructions are unsupported by FEX.

Madeira's per-object generation and capture-table approach is reusable, but its
current driver can finish a resumed incomplete sweep with exit zero. It also
ignores important configuration/feature/upper-lane coverage. Stage 2 must preserve
complete counts, required state and safe Windows ABI boundaries. Upstream golden
values are expectations, not independently validated reference execution.

Hangover's pinned `load_arm64ec_module` selects `libarm64ecfex.dll` with HODLL64
and calls `arm64ec_process_init`; its separate HODLL route selects WoW64. Pear
already checks its actual selected module. Retain Pear's passing selection rather
than copying Linux defaults. Reviewed exact files and revisions are in sources.json.

## Residual Risks

- No native Windows x64 reference, CPU execution or conformance pass yet.
- NASM was not found in PATH or checked retained caches. The official
  [3.02 source listing](https://www.nasm.us/pub/nasm/releasebuilds/3.02/) identifies
  commit `8f1fb545a582c55c69607f457b4d1e71c19b2ecf`. Archive hash, source preparation
  and ARM64 tool execution remain unperformed. Stage 2 should use a task-local
  pinned build; use an initial 256 MiB tool workspace budget and stop if exceeded.
- Full ABI state and SEH/unwind still require fixtures. The original API case
  checks API/callback behavior, not every nonvolatile register; the original TLS
  case uses a coordinator and one worker, not two workers. The manifest preserves
  those distinctions and plans missing tests explicitly.
- Memory mapping, AVX capture, floating-point edge modes, stress and i386 helpers
  are not qualified by source inspection. Required failures cannot be reclassified
  optional after execution.

## Impact on Next Stage

Implement the selected PE harness, observe actual CPUID/reference capabilities,
obtain independent native x64 outcomes and execute matching cases through the
retained #5 pair. Reuse signing/supervision and only rebuild a component when its
inputs change. Frozen expectations/masks and complete case counts are mandatory.

No remote source publication or reference workflow was performed. Stage 2's
planned early task-branch workflow, if needed, still requires the concrete diff
review described in the approved implementation plan before publication. No
credentials, prefixes, profiles or signed runtime payloads belong in that workflow.

## Approval Request

Review Stage 1 and continue to Stage 2 harness/reference implementation. This
approves the next planned local implementation, not an unseen remote workflow
or an unqualified claim that CPU tests have passed.
