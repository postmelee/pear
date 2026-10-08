# Task #5 Stage 6 — Fresh Reconstruction and CPU Integration Handoff

GitHub Issue: [#5](https://github.com/postmelee/pear/issues/5)
Implementation plan: [task_m1_5_impl.md](../plans/task_m1_5_impl.md)
Stage: 6 — completed locally on October 8, 2026

## Stage Purpose

Reconstruct the final Wine/FEX candidate in fresh object directories and verify
its required finite CPU behavior. The requester's explicit continuation of the
reviewed next-work plan supplied Stage 6 authority. Documentation coordination
is preserved in local commit `e3f6b0a`; no runtime code was pushed to GitHub.

Context used: root/runtime/FEX/host/tests/docs rules; approved task and current
implementation/design; Stage 5 report; official architecture, runtime contracts,
source qualification and delivery plan; task-stage-report and todo procedures.
The October 8 upstream reuse review retains the selected engine and languages.

## Artifacts

| File | Change Summary |
|---|---|
| `tools/fex/reconstruct.py`, `reconstruct_fex.py` | Fresh component compilation from checked source/tool preparations, existing patch readers, recipes and storage/child-process monitor |
| `reconstruct_wine_result.py`, `reconstruction_check.py` | Current integrated arena collection and admission of actual source, completed commands/logs and output bytes |
| `integration_fixture.py`, `reconstruction_cases.py`, `reconstruction_services.py` | Reproducible original fixture construction, empty-prefix case sequence and current native-service checks |
| Existing `integration_runtime.py`, `integration_run.py`, `integration_assess.py` | Admit the reconstructed pair, preserve installed PE modes, and distinguish native caller refusal from x64 execution |
| Native service fixture/reader and two targeted test files | Current 12-setting policy profile, explicit historical/default profile, and failed/altered build-evidence rejection |
| `docs/development/fex-host.md` and existing index/audit/source/Wine cross-references | Approved official guide, exact scope and remaining integration requirements |
| [Sanitized observations](task_m1_5_stage6_observations.json) | Exact receipts, six actual case results, native checks and retention outcome |

## Body Change Scope / Lossless Preservation

No Wine/FEX engine source or integration patch changed from the passing Stage 5
candidate. Preserve all original MIT FEX and Wine language/license boundaries.
Reuse existing constructors/readers, signing, provisioning, supervision and
cleanup rather than replacing them. No Rust rewrite, new owner ABI, executable
alias, entitlement or permission bypass was introduced.

The only C++ test adjustment removes its obsolete hardcoded 20-control total.
The actual current policy has twelve settings, including three additional code
cache restrictions, hence 26 positive/conflicting/unknown-setting checks. The
reader still requires 20 by default for the historical Stage 2 scope and requires
an explicit 26-control profile for this regression. Guest/runtime bytes are
unchanged by rebuilding that test executable.

Historical stage reports, source audit and failures remain unchanged. New public
guidance uses the approved existing documentation root and one FEX guide. Private
profiles, prefixes, raw observations and signed runtime payloads remain outside
Git. Completed synthetic prefixes were inventoried and removed only after owned
cleanup and current process checks; no other project or authenticated state was
removed.

## Verification Results

Execution context: Apple Silicon, native ARM64, macOS 26.5.2 (25F84), pinned
macOS 26.5 SDK and recorded native/cross compiler caches. Wine
`4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf`; FEX
`59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa`. Retain software TSO, disabled
persistent code caches and normal development signing/provisioning.

Actual command sequence (input variables denote recorded local preparations):

```sh
python3 tools/fex/reconstruct.py --component wine --base "$PEAR_WINE_OWNER" --baseline "$PEAR_WINE_BASE" --output .build/task5/stage6-wine3
python3 tools/fex/reconstruct_fex.py --base "$PEAR_FEX_OWNER" --wine .build/task5/stage6-wine3 --output .build/task5/stage6-fex1
# First API fixture, signed runtime and empty-prefix execution were run separately:
python3 tools/fex/integration_assess.py --run .build/task5/stage6-run-api1 --runtime .build/task5/stage6-runtime-api2 --output .build/task5/stage6-assess-api1
# Remaining cases used the same recorded compiler/helper/profile/reuse inputs:
python3 tools/fex/reconstruction_cases.py --wine .build/task5/stage6-wine3 --fex .build/task5/stage6-fex1 --compiler "$PEAR_CROSS_CLANG" --helper "$PEAR_OWNER_LAUNCH" --profile "$PEAR_WINE_PROFILE" --reuse "$PEAR_REUSE_SOURCE" --output .build/task5/stage6-final-cases1 --cases thread invalidation exception context native-owner
python3 tools/fex/reconstruction_services.py --build .build/task5/stage6-fex1 --output .build/task5/stage6-native-services3
python3 -m unittest discover -s tests/fex -p test_stage2_services.py -v
python3 -m unittest discover -s tests/fex -p test_reconstruction.py -v
python3 -m py_compile tools/fex/reconstruct*.py tools/fex/integration*.py tools/fex/services.py
git diff --check
```

- Wine: all 21 configure/build/install/fixture/inspection commands passed. Fresh
  source and objects, no prior object reuse. Final receipt
  `f590ffab548efbc06a9f53486e93212431fb1c7f6fd32dd6f17e9962171e56e1`.
- FEX: ten commands passed, including both complete module targets, native
  UnixLibs, inspection and deployment stripping. Existing object/dependency/link
  readers admitted 32 artifacts. Receipt
  `a91d836a6a9c915be98ff4a3a7ad759f0a928d9018a98fee726b2191891048cd`.
- Five original x64 cases all exited42: API/callback, worker/TLS/self-return,
  two-thread invalidation with failed-removal preservation, guest exceptions/data
  guard/nested call, and running-loop suspend/context editing. All use the same
  fresh pair and independent empty synthetic prefixes, not historical templates.
- Each x64 case passed current authorization before/after, complete owned cleanup,
  unrelated-sentinel survival, 41 native ARM64 translation observations and
  16,437–16,439 ARM64 image events. No observed Rosetta path. These snapshots do
  not establish a complete module timeline.
- The ordinary ARM64 caller was refused with `PEAR_FEX_UNAVAILABLE` and expected
  exit68. Its exact refusal record, authorization and cleanup passed. This is a
  negative control, not a native-owner/JIT execution success.
- Both native UnixLib service checks passed: eight services, seven mapping
  controls, 26 policy controls and two joined workers per role. These execute
  ordinary host services, not i386 guests or a restricted JIT operation.
- Eleven targeted portable checks passed: seven service-reader cases and four
  fresh-build admission cases. No broad historical suite or game benchmark was
  repeated. Source/patch algorithms unchanged from Stage 5 retain their scoped
  evidence; the old instrumented 62-check run is not relabeled a new-byte run.

Required failures were retained and resolved, not converted silently:

1. Initial CLI import/admission setup failed before compilation; the missing
   historical Bison path alias was restored to its exact recorded target.
2. All Wine commands passed, but the old collector rejected the expanded FEX
   mapping formula. Collection was corrected without recompilation; original
   failed receipt, failure record, producer and identical command list are
   preserved and checked by the finalization admission path.
3. Initial runtime copying rejected installed `ntdll.dll` mode0644 because the
   incremental overlay assumed0755. Preserve the actual installed mode; no
   executable code or protection policy changed.
4. The native service test initially expected the older policy count. Only that
   fixture was recompiled, with the explicit current profile. Final runtime bytes
   were unchanged, so the five passing x64 cases were not repeated.

Six completed cold synthetic prefixes were removed after recorded and live
process checks. Inventories account for 4,992,257,066 logical bytes; APFS physical
recovery was not measured. Builds, sources, signatures, runtime bundles, original
logs and unique failures remain available for #6/#8 and review.

## Residual Risks

- Same development Mac and verified tool caches; clean-machine, independent Mac,
  independent compiler and ordinary-user distribution remain unqualified.
- The reproduction commands require admitted prepared sources and receipts.
  They are not a one-command build from a clean checkout or a player installer.
- No Steam or Megabonk execution, GPU pairing, full host-module timeline, general
  CPU conformance or performance/power qualification is claimed.
- i386/WoW64 module construction is distinct from i386 execution. Inspect and
  qualify actual required Steam helpers before supporting that user flow.
- One Context/up-to-three-thread fixture profile; broad concurrency, forced
  foreign termination, arbitrary unwind, inline SMC/unaligned repair and compiler
  JIT-guard recovery remain unqualified. Finite capacity refusals remain active.

## Impact on Next Stage

Task #5's technical completion contract is met in the declared component scope:
actual x64 PE execution, required representative host/lifetime paths, and fresh
paired construction from recorded source/tools. No further implementation stage
is added to #5. Use its exact source set for #6 CPU-boundary tests and #8 translated
D3D11 pairing with #7; review existing Madeira ASM-to-PE and DXMT fixtures first.
Keep #1's historical blocked aggregate decision and #4's baseline unchanged.

## Approval Request

Stage 6 is complete locally. Final publication/review, PR/merge and Issue closure
remain separate requester decisions; none was performed by this continuation.
