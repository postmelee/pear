# Task #7 Stage 5 — Final Reconstruction and Corrected Native Pairing

GitHub Issue: [#7](https://github.com/postmelee/pear/issues/7)
Implementation plan: [task_m1_7_impl.md](../plans/task_m1_7_impl.md)
Stage: 5 — completed October 5, 2026.

## Stage Purpose

Reconstruct the complete final graphics component, explain or reject every raw
output difference, verify its actual Wine/Metal pairing and deliver the #8
integration handoff. All three Issue acceptance criteria are satisfied for this
finite development-component scope. FEX, translated Direct3D, Steam, Megabonk,
performance and ordinary-user distribution remain unqualified.

Context used: the Issue, approved task and implementation plans, Stage 4 report,
root/runtime/DXMT/host/tests/docs rules, architecture/runtime/source contracts,
#4's exact Wine baseline and the dated verification-reuse investigation. Reuse
retains upstream Wine C/Objective-C, DXMT C/C++/Objective-C and native LLVM.
The [stage procedure](../skills/task-stage-report/SKILL.md),
[daily board procedure](../skills/todo/SKILL.md) and central templates govern
reporting. Standing requester instructions authorize continuing through Stage 5
and allow completion without commits or pushes; no publication or Issue closure
was performed. The prior selected Apple `using-metal-validation` guidance at
`4f42344c90be22112f46becc3fb9687f423f2f88` remains applicable to the unchanged
Metal environment and explicit diagnostic review. No profiler, capture expansion,
new signing claim or security-setting change was added.

## Artifacts

| Path | Change summary |
|---|---|
| `tools/dxmt/deterministic_pair.py`, `deterministic_reuse.py`, `metal_stdin.py`, `deterministic_monitor.py` and source pins | Fresh exact-source graphics reconstruction, fixed compilation directories, original shader bytes through stdin, deterministic native small-stub link and bounded cache accounting |
| `tools/dxmt/deterministic_native.py`, `deterministic_reproduce.py` | Preserved predecessor predicates, current per-image admission and full raw comparison; explicit source-bound final loader in both complete payload inventories and native execution |
| `runtime/wine/patches/0004-arm64-native-heap-reservation.patch` | Independent LGPL-2.1-or-later Wine loader correction, outside historical and graphics patch series |
| `tools/dxmt/loader_reservation.py` | Original object/link controls, two small source builds, exact unsigned equality, PIE/null-guard/reservation inspection and replay |
| `tests/dxmt/test_loader_reservation.py`, `test_deterministic_native.py` | Address-layout, complete-payload replacement and source-loading regression coverage |
| [Observations](task_m1_7_stage5_reconstruction_observations.json) | Historical failures preserved alongside final allowlisted source/build/run/review digests |
| [Incident](../troubleshootings/task_m1_7_initial_access_violation.md) | Captured failure, independent Foundation reproduction, loader repair and finite disposition |
| [Contributor guide](../../docs/development/dxmt-build.md), [Wine handoff](../../docs/development/wine-host.md), [research follow-up](../../docs/research/graphics-and-game-integration.md) | Reproducible commands, final scope and #5/#8 integration obligations |

## Body Change Scope / Lossless Preservation

All official changes use the task's approved existing `docs/` locations. Internal
plans, reports, evidence sidecars and the daily board remain in `mydocs/`.
The original source caches, #4's 23-patch series and historical receipts remain
unchanged. No private game files, accounts, profiles, signing material, raw
memory or diagnostics are published. Completed diagnostic prefix file contents were archived
with verified restoration data while the original inodes and metadata remain
in place; restoration is required before prefix-content inspection. Original failures were not erased.

The final graphics source recipe produced two complete fresh builds with 2,878
raw inventory entries equal without normalization. Unchanged LLVM, shader,
compiler and Wine prerequisites were reused only under exact input verification.
The final native loader is an additional source-built dependency: its original
object and link reproduce exactly, and two patched outputs also match exactly.
The complete comparison uses those actual first/second loader bytes, not the
historical loader, while retaining the graphics candidates' identities.

The captured fatal path released a freed low-address Swift array during
Foundation Locale comparison. A Foundation-only control failed below 4GB and
passed with the allocation boundary above 4GB. Wine's existing zero-fill
reservation mechanism is adapted to ARM64, retaining PIE and the 64KiB guard,
using the actual slid range and failing startup if PROT_NONE remapping fails.
The 8GB x86_64 layout collides with the ARM64 shared cache; simply raising
PAGEZERO to 4GB would block guest addresses. The final patch does neither.
The normal runner, PE fixture, ntdll, server and Metal environment were preserved.
The #5 worktree was not edited.

## Verification Results

Execution context: Apple M4 Pro, 24GiB, macOS 26.5.2 (25F84), Xcode 26.6
(17F113), SDK 26.5, Apple Clang 21, Python 3.14.4 for current adapters,
LLVM-MinGW 20260908 / LLVM 23.1.1, native LLVM 15.0.7 and the retained qualified
Metal tools. The observed finite route is ARM64 without Rosetta, with actual
4KiB loader pages on a 16KiB kernel. Signing uses the existing device-bound
cross-architecture/JIT development grant, checked per executable before/after.

Executed commands use the private paths captured in their receipts; equivalent
CLI spellings are documented in the contributor guide:

```sh
python3 -B -m tools.dxmt.loader_reservation --repo "$pear_repo" --constructor-root tools/dxmt --baseline "$pear_wine_native" --output "$pear_loader_output"
python3 -B -m tools.dxmt.deterministic_native --repo "$pear_repo" --constructor-root tools/dxmt --loader-reservation "$pear_loader_output" --prepare --build "$pear_graphics_candidate" --profile "$pear_wine_profile" --output "$pear_final_runtime"
# Two ordinary --run operations, each with a fresh prefix and the same loader selection.
# Root explicitly reviewed every raw stream and wrote immutable diagnostics-review.json records.
python3 -B -m tools.dxmt.deterministic_native --repo "$pear_repo" --constructor-root tools/dxmt --loader-reservation "$pear_loader_output" --evidence --run-root "$pear_second_run"
python3 -B -m tools.dxmt.deterministic_reproduce --repo "$pear_repo" --constructor-root tools/dxmt --loader-reservation "$pear_loader_output" --complete --output "$pear_comparison" --native-evidence "$pear_second_run" --require-complete
python3 -B -m tools.dxmt.deterministic_reproduce --repo "$pear_repo" --constructor-root tools/dxmt --loader-reservation "$pear_loader_output" --verify --output "$pear_comparison" --require-complete
python3 -B -m unittest discover -s tests/dxmt -p 'test_*.py'
python3 tools/check_governance.py
git diff --check
```

| Evidence | SHA-256 | Result |
|---|---|---|
| Loader patch | `8ab5deb0cf144e8c50f02fe2353613ec33123e558525904476dfa9f10264541f` | Source-derived Wine correction |
| Loader build receipt | `ac845ea04a80096be20e2057efa38339d5dd3576a3b78d23d39c949fa29f95e6` | Original controls and two identical source builds |
| Final unsigned loader | `06113536af8b594fe19aa84c33d783b323ba53265d346d438c362f0bc29def79` | ARM64, PIE, contiguous exclusion below native heap |
| Final runtime receipt | `df705e39476503bdab716332c84965c836b3ea4c2d64a0190b9bdec7b5c4bd81` | 39 native images, exact origins and current authorization |
| Complete raw comparison | `4826b4f957187cc51b740fb7652247b2387e3dcab2f08a207840761a808ed4e8` | All 2,878 entries equal; no normalization |
| Final ordinary run 1 | `8f0dde9e0edc97b5732c1359ebdb47c209e8158a3f59268cd11ce2cca6630436` | 39 rows, terminal and exit zero, physical lifetime and cleanup verified |
| Final ordinary run 2 | `c1a19033a79fb95c4f54d9e323b06d91146b5f78bd90f008b5ec1d353081ee21` | 39 rows, terminal and exit zero, physical lifetime and cleanup verified |
| Completed reconstruction | `be94089919d2314e08ae4482db292d150632a40cdb8f8dffebb122ea1ac2c556` | Independent replay requires complete final native evidence |

Each native run observed all original 39 cases, a successful PE terminal,
loader exit zero, three views/three layers/one proxy physically deallocated,
zero final leases/attachments, all 20 streams complete, owned descendants reaped
and the unrelated sentinel surviving. Explicit review classified every captured
nonfixture diagnostic; no Metal API validation error or unknown validation
warning was accepted. Expected Wine working-directory fallback messages remain
visible. No debugger, diagnostic ntdll, hold server or altered locale was used.

The final portable suite ran 530 tests: 522 passed and eight conditional controls
were skipped. Optional actual Metal qualification/FEX-input controls were not
selected; skips are unperformed observations. Existing unchanged Wine modules
were not rebuilt or subjected to an unrelated expanded test matrix. The affected
native bootstrap, low-address mapping, PE publication and window lifetime paths
were exercised by the full original pairing route. Governance/local-document
links and diff checks passed after the final documentation changes.

Earlier failed native runs, private diagnostic successes, rejected linker
layouts and two loader-preparation errors remain historical evidence. One
comparison was stopped before completion to include the new loader in the full
payload view. A new test's import-alias collision was corrected before the final
530-test pass. An initial final-runtime preflight raised POSIX EBADF before any
pairing output or Wine launch; an unchanged structural replay passed and the
replacement batch retained full exception tracebacks. That isolated preflight
error remains unexplained and recorded separately from native results. None of
these earlier attempts is substituted for final evidence.

## Residual Risks

- Two same-host finite runs do not prove arbitrary scheduling or other OS/hardware behavior.
- The captured low-address failure class is corrected; every historical fault is not assigned one cause.
- ARM64X graphics DLLs are built/inspected, not executed by this ordinary ARM64 fixture.
- FEX, translated Direct3D, games, performance, second-machine reproduction and release authorization remain unperformed.
- Reconstruction still depends on retained private source/tool/qualification receipts; this is not a portable end-user installer.

## Impact on Next Stage

#5 inherits the exact Wine baseline, independent loader patch and link flags in
the contributor handoff. Revalidate affected low guest mapping, MAP_JIT arena
and vprot/file_view metadata assumptions on the combined candidate; #7 does not
qualify #5's 256KiB admission or FEX execution. #8 inherits the corrected typed
native pairing and must still verify actual translated D3D11 rendering. #10–#13
retain observation, Steam/game and distribution obligations.

## Completion and Publication Status

Stage 5 and #7's implementation acceptance criteria are satisfied. Completion
is reported under the requester's standing authorization. Commits, pushes, PR
publication, merge and GitHub Issue closure were not performed; they are separate
repository actions. No further Stage or game-support claim is implied.
