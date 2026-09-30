# Task #4 — Stage 3: ARM64 Windows PE/API and nested Wine callbacks

GitHub Issue: [#4](https://github.com/postmelee/pear/issues/4)
Implementation plan: [`task_m1_4_impl.md`](../plans/task_m1_4_impl.md)
Stage: 3
Status: complete; Stage 4 requires requester approval.
Date: September 30, 2026

## Stage Purpose

Original ARM64 Windows programs now pass the declared API, child-process, relocation, PE security-cookie and nested callback checks through the actual development-authorized Wine host. The required instrumented native processes reported ARM64 and untranslated execution. API/ABI and all three bootstrap controls passed independent verification on the same final signed runtime. This completes the approved Stage 3 and its native PE publication amendment; it does not qualify x64 translation, Megabonk or ordinary-user distribution.

Context used: the approved [task plan](../plans/task_m1_4.md), [implementation plan and amendment](../plans/task_m1_4_impl.md#approved-stage-3-amendment-native-pe-code-publication), [Stage 2 report](task_m1_4_stage2.md), root/runtime/host/test/documentation rules, and the [architecture](../../docs/architecture.md), [runtime contracts](../../docs/runtime-contracts.md) and [source qualification](../../docs/source-qualification.md). Reporting follows Hyper-Waterfall v0.3.0 [stage-report](../skills/task-stage-report/SKILL.md) and [daily-board](../skills/todo/SKILL.md) procedures. Pear Apple-tooling is **Not applicable** to this host-only work. Wine's existing C/assembly, loader, dispatcher, callback and module-reference implementations are reused; no Rust rewrite or substitute Windows API engine was introduced.

## Artifacts

| File | Change Summary |
|---|---|
| `runtime/wine/patches/0003*.patch`, `series.json` | Attributable x18 transitions, fixture dispatch, owned-process diagnostics, native PE publication and import/lifetime handling; startup, spawn, architecture, capacity and cookie corrections. Seventeen total ordered patches include the two retained Stage 2 patches. |
| `tests/wine/fixtures/api_pe.c`, `api_launch.c` | Original ARM64 Windows API/child fixture and native launch/ownership bridge. |
| `tests/wine/fixtures/abi_pe.c`, `abi_native.c`, `abi_gateway.S`, `lifetime_pe.c/h`, missing-import fixtures | Actual Wine ABI entry/callback checks, two simultaneous relocated DLL copies, real PE load-config cookie initialization, and held-module load/unload checks. |
| `tests/wine/fixtures/pe_arena_native.c`, `tools/wine/pe_arena_probe.py`, `arena_evidence.py` | Separate native 4 KiB publication/lifecycle prerequisite, fault controls, and bounded interpretation of retained evidence. |
| `tools/wine/build.py`, `signing.py`, `run_fixtures.py`, `api_runner.py`, `common.py` | Exact source/build/signing identities, finite capacity, actual fixture execution, owned cleanup, strict bounded evidence decoding and scoped OS-image origin handling. |
| `tools/wine/abi_review.py`, `verify.py`, `evidence.py`; `tests/wine/` regressions | Byte-bound finite assembly review, independent fixture/run checks, negative controls and allowlisted public export. |
| [Stage observations](task_m1_4_stage3_observations.json) | Final build/sign/run identities, source hashes, fixed public results, six retained ordinary API failures and three native prerequisite attempts. |
| [Wine development guide](../../docs/development/wine-host.md), plans, daily boards | Verified behavior, reproduction procedure, preserved failed/partial histories and the next-stage checkpoint. |

## Body Change Scope / Lossless Preservation

The requester approved the native PE publication amendment on September 29 and continued Stage 3 on September 30. Code and documentation remain in the approved paths. The original source audit and its blocked aggregate decision are unchanged. Existing upstream licenses are retained; original Pear owner/fixture notices remain distinct from Wine's LGPL integration. Patch bytes, exact before/after source hashes and ordering are recorded.

The selected publisher uses one bounded process-owned `MAP_JIT` region, fixed code/ordinary-data classes and page W^X. It prepares relocations before publishing immutable code, updates the guest image base to prevent a second code relocation, validates loader-data destinations, and retires owned slots to nonexecutable storage. Wine's existing loader references and the exercised callback completion determine safe retirement. Missing imports return explicit typed failures instead of requiring executable failure stubs. Mixed writable/executable sections, unsupported relocation types and incompatible backing reuse remain rejected.

A source review found that load-config lengths 89–95 exposed a partial SecurityCookie pointer to Wine while bypassing the publisher's destination check. `0003n` rejects those inputs before publication. The fixture has a real 96-byte load-config with a DIR64 pointer to ordinary cookie storage; callback sentinel counters are not substituted for this check.

All failed builds, signed artifacts, prefixes and diagnostic records remain local and ignored. The requester's storage-recovery authorization was fulfilled without deleting evidence: strict APFS cloning of 9,702 byte-identical ordinary installation files reclaimed approximately **10.2 GiB**. Destination content and recorded metadata were verified; inode/ctime changes were recorded. Independent checks matched nine installation inventories, nine signed inventories and 38 unchanged evidence-record hashes. The private verification receipt is `e5a335c1f156acb39f54c76496e9bf991f6ff6279ec13795d449f531ff7b095a`. No game, authentication or signing inputs were removed or published.

## Verification Results

Execution context: native Apple M4 Pro, macOS 26.5.2 (25F84), Xcode 26.6 (17F113), SDK 26.5, pinned LLVM-MinGW 20260908/clang 23.1.1, and locally built Bison 3.8.2. Wine source is commit `4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf`. Builds used four jobs and fresh owned outputs. These are same-host correctness checks, not performance or power measurements.

### Final commands and identities

The original destinations and earlier attempts remain occupied evidence. The final combined run uses the approved fresh-output substitution `attempt12`:

```sh
python3 -B tools/wine/build.py --variant arm64 --inputs .build/task4/inputs --tools .build/task4/tools --output .build/task4/build-stage3-attempt12 --jobs 4
python3 -B tools/wine/abi_review.py --build .build/task4/build-stage3-attempt12 --output .build/task4/build-stage3-attempt12/abi-review.json
python3 -B tools/wine/signing.py prepare --build .build/task4/build-stage3-attempt12 --local-input .build/task4/private/signing.json --output .build/task4/signed-stage3-attempt12 --require-empty
python3 -B tools/wine/run_fixtures.py --suite api-abi --runtime .build/task4/signed-stage3-attempt12 --output .build/task4/runs-stage3-attempt12 --require-empty
python3 -B tools/wine/verify.py runs --root .build/task4/runs-stage3-attempt12 --suite api-abi --require-complete
python3 -B tools/wine/run_fixtures.py --suite bootstrap --runtime .build/task4/signed-stage3-attempt12 --output .build/task4/runs-stage3-attempt12-bootstrap --require-empty
python3 -B tools/wine/verify.py runs --root .build/task4/runs-stage3-attempt12-bootstrap --suite bootstrap --require-complete
python3 -B -m unittest discover -s tests/wine -p 'test_*.py'
python3 -B -m unittest discover -s tests/wine -p 'test_evidence_stage3.py'
python3 -B tools/check_governance.py
git diff --check
```

The full suite ran before the final build: **558 tests passed in 19.933 seconds, with no skips**. A subsequent reporting-only scope clarification passed all 30 affected exporter tests; these overlap the 558 and are not an additional unique total. Full compilation, assembly inspection, real execution and independent verification then passed with the fixed runtime producers. Final governance passed for 22 documents and 157 local targets; working and staged whitespace checks passed. Independent source/provenance and public-evidence reviews found no privacy or runtime-gate defect. Final report review verified the record hashes and counts; its historical-reconstruction and diagnostic-attribution wording corrections were applied.

| Record | SHA-256 |
|---|---|
| Final build | `2fe882533d9cfaeda4cde8f9b1c7c2db75c6faaf34d143c857a7a471468aaff4` |
| Signed runtime | `a70c292479c52907ed518d3eb557ea5f33cbc21de56eea48364a691f4dfea2a9` |
| ABI assembly review | `267b9b31efb2f47f24b14fa46de8d0c677f676671c9ce11b60a1e97324768108` |
| API/ABI run | `ef2c1537a33a560abd71272ab94aadd9130413ce7aba92031b380f851c2cd195` |
| Bootstrap run | `53c2fb5c74e58bbbdef153623c8be860f3d85c2e092f8f1f297aa9d275fa04be` |
| Public observations | `9afc1486d44c8b1bbd3dca2986f0b77bf10fc4cfb230cbb5a9400a0a9a2a5b78` |

All 34 build commands exited zero. The final inventory contains 38 ARM64-only native images and 753 PE images: 751 ARM64 and two unexecuted x64/i386 controls. Capacity was recomputed from installed bytes: 1,011,023,872 aligned image bytes, a 38,993,920-byte largest-image margin and two 65,536-byte copied-fixture slots require 1,050,148,864 interior bytes and 754 slots. These are finite address-space budgets, not measured resident memory consumption.

The actual final DLL, SHA-256 `d986b27424c678d1b3acd9bd895f7a54265e7ef3a552a74f1410f6d91625240a`, passed an additional compiled-instruction review using the pinned ARM64 LLVM reader and `inspect_relocation_indirection` from `test_relocation_fixture.py`. It binds displayed instruction words to DLL bytes, exports, caller cell arguments, one cell-derived indirect call and two reads/one write through the data pointer. The actual load-config/default/DIR64 destination also passed independent parsing. The private receipt SHA-256 is `675fdc6b60651d7a467fc2a48a48e4beb770404cc8c1e9c7ff4ad4dddca1db8d`; disassembly SHA-256 is `b3163b5b269b5e293ad64906804d06d03888544097d1bdf96af0671033ae3787`. This finite fixture checker is separate from the automatic exporter and is not a general ARM64 control-flow proof.

### Actual acceptance results

| Gate | Observed result and boundary |
|---|---|
| Signing and platform protections | The loader passed actual development-profile authorization; all 38 native images passed signature/source-origin checks. The loader has the matched cross-architecture grant, public `allow-jit` and 4 KiB signature pages. Ordinary helpers receive no restricted claims. Hardened Runtime and library validation remain enabled. |
| Windows API and child execution | Unicode/space arguments, fixed environment, memory/TLS, owned-file write/read/hash/delete and missing-file errors passed. A real Windows child returned 37. Native class 181 architecture/flags/terminator checks passed. |
| Real Wine ABI | 64 round trips, 32 callbacks and nested calls, 16 injected errors, 128 gateway/native/TEB checks, 32 frame checks and 256 host-mode checks passed. Register failure mask was zero; inactive callback return was `STATUS_NO_CALLBACK_ACTIVE`. |
| Two PE placements | Two byte-identical but independently owned DLL copies were live at different nonpreferred bases and slots. Four real pointer-call/data probes and two matched retirements passed, with independent original-byte/export/DIR64 and native-generation binding. |
| PE SecurityCookie | Two images and four observations passed: nonzero, nondefault, below 2^48 and stable within each image. Actual destination, load-config pointer and its relocation were verified. Values and addresses remain private; no randomness-quality claim is made. |
| Import failure and lifetime | Two actual named/ordinal import rejections retained typed statuses, null handles and provider-absence checks. Thirty-two callback-held unload attempts, paired holds/releases and retirements passed, with 31 compatible reuses. The return continuation is the already pinned main executable. |
| Native-process evidence and cleanup | API and ABI cases recorded 17 and 15 native processes respectively; required ARM64/untranslated, role-specific page geometry, image observations, owned cleanup and unrelated-sentinel survival checks passed. Snapshots are finite. |
| Same-byte bootstrap regression | Normal stop, intentional timeout and wrong-prefix-server refusal all passed, including ownership and cleanup, on the exact final signed runtime. Both suites were independently revalidated. |
| Unsupported guest targets | Built x64/i386 fixture bytes were checked and explicitly rejected before execution because no translator is qualified. No fallback Intel host was used. |
| Native publication prerequisite | Retained page-W^X tests passed two positive cases and four matched protection faults, with 4 KiB separation, rollback, exhaustion, retirement and reuse checks. These are standalone native observations, separate from integrated Wine execution. |
| Malformed inputs and test controls | Actual-source UBSan tests reject malformed PE layouts and partial cookie fields; 14 partial-field inputs reproduce old acceptance and corrected rejection. Binary mutation controls reject optimized direct operations and wrong operands. Synthetic controls do not claim execution of hostile PE files through Wine. |

The fixture-only `native-api-abi-no-mono-v1` environment preserves Wineboot/INF initialization but disables CLR loading and registration with `mscoree=`. This avoids the observed optional Mono installer wait and is not a game/default-runtime setting. The image snapshot budget is 2,048; API-case decoding has an explicit 16 MiB/1,000,000-node limit, while other record and stream bounds remain distinct.

### Preserved failures and partial successes

| Earlier evidence | Meaning |
|---|---|
| Initial API timeout; attempt2 execution failure | An upstream pre-guard ARM64EC bitmap access and then denied executable PE file mappings prevented fixture entry. Neither became a passing run. |
| Native thread-JIT prerequisite attempts 1 and 2 | Both retained `EACCES` failures: initial protection setup, then retirement after partial success. The selected page-W^X prerequisite passed separately. |
| Attempt3 failed build | Publication-policy build correction required another fresh build; compilation failure is retained. |
| Attempt4 and diagnostic attempt5 | Relocated-main informational status handling and a high-address exec environment required corrections. Attempt5 diagnostic execution did not qualify ordinary API/ABI. |
| Attempts6 and 7 | Native image observations exceeded the original 1,024-image bound. Attempt7 retained the actual count, 1,041. |
| Attempt8 | The ordinary run timed out during prefix initialization; a subsequent separately retained diagnostic identified the optional Mono installer wait. Private diagnostic adapters remain unqualified. |
| Attempt9 | API/ABI and same-byte bootstrap passed, but actual two-placement relocation binding was missing. |
| Attempt10 | All build commands completed, but measured capacity rejected one extra 64 KiB slot caused by a debug-path length boundary. Its original build and patch inputs remain retained. |
| Attempt11 | Actual two-placement/API/ABI and independent verification passed; the required PE SecurityCookie initialization gate was still absent. Bootstrap was not repeated for this partial candidate. |
| Final attempt12 | All combined required gates passed on the corrected final bytes. |

The public export was produced successfully with:

```sh
python3 -B tools/wine/evidence.py --stage 3 \
  --build .build/task4/build-stage3-attempt12 \
  --runs .build/task4/runs-stage3-attempt12 \
  --bootstrap-runs .build/task4/runs-stage3-attempt12-bootstrap \
  --failed-api-run .build/task4/runs-stage3 \
  --failed-api-run .build/task4/runs-stage3-attempt2 \
  --failed-api-run .build/task4/runs-stage3-attempt4 \
  --failed-api-run .build/task4/runs-stage3-attempt6 \
  --failed-api-run .build/task4/runs-stage3-attempt7 \
  --failed-api-run .build/task4/runs-stage3-attempt8 \
  --native-arena-run .build/task4/pe-arena-prerequisite-attempt1 \
  --native-arena-run .build/task4/pe-arena-prerequisite-attempt2 \
  --native-arena-run .build/task4/pe-arena-prerequisite-attempt3 \
  --output mydocs/working/task_m1_4_stage3_observations.json
```

Current pure validators matched retained native receipts and preserved failed API records. Historical native-profile and bundle-metadata byte hashes were not retained and are explicitly **unavailable**; those receipts do not renew signing authorization. Final Wine authorization was independently checked against the actual current inputs. No profiles, identifiers, credentials, game bytes or raw memory addresses are included in public observations.

## Residual Risks

- Results apply to one development-authorized host/configuration and original ARM64 fixtures. FEX, ARM64EC execution, x64/i386 translation, DXMT, Steam, Megabonk, gameplay, input/audio, performance and distribution remain unqualified.
- The arena supports the exercised immutable PE lifecycle. Dynamic Windows executable memory, generated stubs, concurrent patching/unloading, broader address constraints and FEX's JIT ownership are not established. Standalone fault/exhaustion tests do not establish integrated Wine fault injection or indefinite allocator liveness.
- Callback lifetime evidence uses one stable single-thread table, a held callback DLL and an already pinned main-executable continuation. Unloadable continuations, arbitrary dangling callbacks and concurrent table mutation are unqualified.
- Instrumented process registration has a pre-registration interval; finite native-image snapshots are not a complete load/unload timeline. OS/Cryptex path acceptance is not an independent cryptographic attestation of all Apple images.
- The baseline native positive control also passed without the extra `allow-jit` claim, so its empirical necessity was not established. The selected final loader policy and actual profile checks are recorded separately.
- Thread/signal/exception and dynamic-memory behavior require Stage 4; Mac-driver callbacks require Stage 5. The Stage 2 companion was not rebuilt with Stage 3 patches. Final native/companion reconstruction and handoff remain Stage 6. Optional EGL and excluded component features remain unqualified.

## Impact on Next Stage

Stage 4 can start from these exact passing native PE/API and callback foundations after requester approval. Preserve the W^X policy, real per-executable authorization, original fixture counts, process ownership, bounded observation/cleanup and all historical evidence. Test actual Wine threads, fault/exception contexts, 4 KiB virtual-memory changes and dynamic executable-code publication without equating immutable PE success with a JIT solution. The Issue and M1 remain open.

## Approval Request

Review the Stage 3 artifacts and verification, then approve Stage 4: threads, faults, exception contexts and dynamic-memory behavior. This report does not authorize that transition or PR publication.
