# Task #2 — Stage 3 report

GitHub Issue: [#2](https://github.com/postmelee/pear/issues/2)
Implementation plan: [task_m1_2_impl.md](../plans/task_m1_2_impl.md)
Stage: 3 — Authorized signing and process capability tests
Date: September 28, 2026

## Stage Purpose

Establish an actual authorized development signing route and test native 4 KiB process pages, independent protection/recommit, low-address mapping and Hardened Runtime JIT behavior. The maintainer explicitly approved Stage 3 and supplied the requested development profile. Passing these tests establishes bounded host prerequisites; it does not establish Rosetta-free Megabonk execution.

## Artifacts

| File | Change Summary |
|---|---|
| `host/probe/hardened_baseline.py` | Independent signed positive/negative JIT controls; strict signature checks, paired assessment and sanitized results |
| `host/probe/provisioned_probe.py` | Local profile/device/certificate validation, fresh signed app copies, exact claim checks and actual process-mode trials |
| `host/probe/process_child.c`, `process_evaluate.c`, `process_main.c` | Self-spawned geometry, middle-page protection/recommit and armed fault probes with independent semantic assessment |
| `host/probe/baseline.h`, `child_runner.c` | Explicit default/4 KiB spawn mode and attribute evidence; existing containment preserved |
| `host/probe/baseline_child.c`, `baseline_child_entry.c`, `Makefile` | Reusable baseline entry and separate standard/emulation-layout ARM64 executables |
| `tests/host/test_hardened_baseline.py`, `test_provisioned_probe.py` | 39 pure signing, authorization, assessment and privacy tests |
| `tests/host/test_process_capabilities.py`, `process_runner_driver.c`, `process_runner_fixture.c` | 18 tests of setter failures, mode evidence, packet semantics and fault interpretation |
| [Contributor guide](../../docs/host-capabilities.md) | Developer setup, commands, actual results and qualification limits |
| [Stage 3 evidence](task_m1_2_stage3_observations.json) | Source/test/binary hashes, signature/profile checks, full sanitized trial records and test output |
| Implementation plan and [daily board](../orders/20260928.md) | Concrete approved-stage boundaries and Stage 4 checkpoint |

## Body Change Scope / Lossless Preservation

Stage 1 observations, Stage 2 default behavior and historical reports remain intact. The baseline child entry is reusable without changing the four original trials. The private packet remains 160 bytes; the expanded IDs are a same-build internal interface. The original runner API retains default spawning. Only the new explicit mode requests 4 KiB pages; missing APIs and setter errors fail without falling back to ordinary pages. Existing deadlines, process ownership, bounded output and reaping rules remain active.

The development tool validates a CMS-decoded, unexpired macOS profile for the explicit App ID, the current Mac's Provisioning UDID and a matching valid Apple Development certificate. It embeds that actual profile and signs a single self-spawning app executable with the granted `com.apple.developer.cross-architecture-support` plus public allow-jit. Both app and executable undergo strict signature and exact effective-claim verification before launch. The successful OS launches and memory behavior supplement these preflight checks; signature validation alone is not treated as authorization proof.

The independent Developer ID controls have no restricted entitlement or profile. Their supervisor has no entitlement exception; only the positive child receives allow-jit. Local signatures use Hardened Runtime and no timestamp. Signed bundles, profiles and raw personal metadata remain in ignored local storage, outside Git and release artifacts.

The standard process executable retains its 4 GiB protected `__PAGEZERO`. The separate layout build adds `-Wl,-x86_64_layout_emulation,-pagezero_size,0x10000` and retains 64 KiB of null protection. The emulation flag alone did not reduce PAGEZERO; explicit sizing is part of the tested configuration. No arbitrary address is overwritten: the low-address trial is non-overwriting, and MAP_FIXED is restricted to the already-owned middle page of the new memory trial.

No Steam, Wine, FEX, DXMT or game process is launched. No x18 mode transition or per-thread ordering policy is executed. SIP and Gatekeeper remain enabled. Repository documentation, comments and test fixtures are English.

## Verification Results

The implementation plan's commands were run, retaining output under ignored `.build/` before reviewing the evidence:

```sh
make -C host/probe
python3 -m unittest discover -s tests/host -p 'test_*.py' -v
python3 host/probe/hardened_baseline.py
python3 host/probe/provisioned_probe.py --profile "$PEAR_PROVISIONING_PROFILE"
git diff --check
```

The environment variable identifies a local profile and is not committed. Supplemental `lipo -archs`, `otool -l`, `codesign --verify --strict`, `csrutil status` and `spctl --status` checks establish binary layout and protection context.

| Check | Result |
|---|---|
| Build | Passed with Apple clang 21.0.0, SDK 26.5, ARM64 and warnings treated as errors |
| Complete test suite | `Ran 94 tests in 10.098s` / `OK`: 37 retained tests plus 18 process, 22 hardened-control and 17 provisioned-control tests |
| Architecture | All five built tools contain only ARM64 slices; every signed supervisor observed its own translation query as false |
| Profile binding | CMS decoding, expiration/platform, explicit App ID, team/prefix, actual cross-architecture grant, registered Mac and certificate checks passed |
| Effective signed claims | Strict verification passed; Hardened Runtime present, ad-hoc flag absent; profile-bound claims and public allow-jit matched exactly |
| Ordinary signed controls | Positive JIT returned 42; paired negative allocation rejected with errno 22; both control assessments passed |
| Restricted process trials | Both layout variants passed in default and 4 KiB modes; every requested 4 KiB setter call returned zero |
| Lifecycle | All 28 provisioned trial children and eight ordinary control children were reaped; retained lifecycle/cleanup regressions passed |
| Platform protections | SIP enabled; Gatekeeper assessments enabled before and after testing |
| Evidence and diff | Source/binary bindings, privacy filtering, local links and diff hygiene checked; no private profile or identity content committed |

Actual signed process results on M4 Pro/macOS 26.5.2 (25F84):

| Layout / mode | User / Mach user page bytes | Kernel page bytes | Low address `0x20000000` | JIT |
|---|---|---|---|---|
| Standard / default | 16,384 / 16,384 | 16,384 | Unavailable, Mach code 3 | Passed, returned 42 |
| Standard / 4 KiB | 4,096 / 4,096 | 16,384 | Unavailable, Mach code 3 | Passed, returned 42 |
| Emulation / default | 16,384 / 16,384 | 16,384 | Passed; readback and release | Passed, returned 42 |
| Emulation / 4 KiB | 4,096 / 4,096 | 16,384 | Passed; readback and release | Passed, returned 42 |

The standard-layout unavailability is retained as a comparison result, not converted to success. The selected emulation layout independently supplies positive low-address evidence. The ordinary page-size supervisor does not imply an ordinary page size in its explicitly configured child.

Both 4 KiB configurations passed these additional behaviors:

- A three-page, 12,288-byte allocation retained distinct sentinels on all pages. Protecting only the middle page read-only allowed neighbor writes without corruption; restoring middle-page write access returned 84 and preserved both neighbors.
- Replacing only the owned middle 4 KiB with anonymous PROT_NONE memory preserved the neighbors. Restoring RW found all 4,096 middle bytes zero, then wrote/read 42 and checked the neighbors again before release.
- Separate armed trials attempted a protected write and an access to the replaced PROT_NONE page. Each produced SIGBUS (10) after valid setup evidence; subsequent steps remained `not_run` rather than inventing successful cleanup in a terminated child.
- The 4 KiB JIT allocation published and synchronized an eight-byte ARM64 leaf, returned 42 and released its allocation. This is generated native test code, not translated x64 code.

The negative ordinary JIT control requires precise interpretation. Without allow-jit, MAP_JIT allocation produced `failed` with `EINVAL` (22), and the baseline CLI exited one. The control assessment passes only because the positive control already passed from identical pre-signing inputs and the negative result contains exactly the expected allocation rejection. The original failure, errno and exit code remain recorded. EINVAL is not globally classified as authorization denial; other causes remain possible without this paired evidence. A historical [Chromium change](https://chromium.googlesource.com/chromium/src.git/+/dec31e17bcaf07cade7cacf04468299f7c6564b6%5E%21/) also documents this MAP_JIT/hardened-entitlement result, but the current result is supported by the actual local comparison.

New regression coverage includes missing/rejected spawn setters, no silent mode fallback, malformed process packets, incorrect geometry, absent attribute evidence, unarmed or unrelated faults, wrong memory values, unreaped children, required low-mapping failure, expired/mismatched profiles, ambiguous certificates, unexpected entitlement claims, misleading executable-segment flags, unpaired EINVAL and private-output filtering. Profile/signature unit tests use synthetic inputs; restricted behavior is established by the separate signed native runs.

## Residual Risks

- Rosetta-free Megabonk execution is not achieved. These results do not qualify Wine/FEX integration, x86 instruction translation or performance.
- The development profile covers the registered Mac. No general-user distribution, notarization, different hardware/OS or profile-renewal path is qualified.
- Four-KiB protection/recommit tests cover finite operations in owned memory. They do not prove the complete Windows virtual-memory contract, physical reclamation or arbitrary mixed mappings.
- Low mapping is demonstrated at one address in the explicit test layout. The eventual Wine address-space reservation policy still needs integration evidence.
- Fault trials validate armed setup and SIGBUS/SIGSEGV termination, not a captured fault address or instruction pointer. The cooperative-child containment limits from Stage 2 still apply.
- Foreign x18 transitions, host callbacks, asynchronous signals and per-thread memory ordering remain untested. Kernel pages remaining 16 KiB must not be confused with failed user 4 KiB mode.

## Impact on Next Stage

Stage 4 can reuse the actual profile validation, strict signing checks, self-spawning executable and bounded runner. It must add narrow assembly transitions and deterministic state fixtures without allowing ordinary C/POSIX/framework calls in foreign mode. Required cases include nested transitions, guest x18 preservation, callbacks, asynchronous signal/error entry and per-thread policy initialization. API return values and finite ordering stress observations must remain distinct.

Stage 5 must still reproduce the approved tests from a clean build and map every Issue #2 criterion to evidence. Issue #2 remains open; this stage is published on the existing review branch rather than opening the task's final PR.

## Approval Request

Review the Stage 3 artifacts and evidence, then approve Stage 4 under the existing implementation plan. No Stage 4 ABI or thread-policy execution has been performed in this stage.
