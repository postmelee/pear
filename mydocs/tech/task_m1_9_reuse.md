# Task #9 reuse implementation record

Date: October 8, 2026. Scope: approved Stage 1 native foundation and v2 contract/oracle structure. See the [implementation plan](../plans/task_m1_9_impl.md) for the approved choices and remaining stage gates.

## Existing Pear implementation reused

Source baseline: #3 integration `1f229dab08e30afb01080e7664240e317e5df2ef`, still present without source changes in the #9 base. The selected language remains Rust; no new language comparison was performed.

| Original input | Actual Stage 1 use | Preservation / new verification |
|---|---|---|
| `experiments/manager/rust/src/json.rs` | Byte-identical copy at `manager/src/json.rs` | Build adapter checks equality; native positive Unicode/integer and malformed/depth/node/size/duplicate/private-input cases execute against the copied parser |
| Original Rust `Cargo.toml` and `Cargo.lock` | Byte-identical manager manifests | Same build profile and sole dependency `libc = 0.2.186`; adapter verifies complete equality and calls the original dependency verifier |
| `fixtures/native_bridge.c/.h` process identity function | Same implementation and signature in `manager/native/bridge.c/.h`; header name adapted | Native self/invalid-PID tests; added staging/hash functions have caller-owned buffers and errno results |
| `experiments/manager/build.py` | Imported `verify_lock`, controlled environment and digest helper | Exact archive checksum and all 360 regular extracted libc files rechecked; native builder retains bounded command capture, compiler/SDK/target identities and system dependency/signature inspection |
| `experiments/manager/run_cases.py` | Imported bounded command capture | Same process-group reservation/capture/watchdog behavior for compiler/test invocations; no separate generic runner |
| `tests/contracts/validate.py` | Imported strict parser, SafeRoot, graph loading, semantic/purpose/policy methods and closed diagnostics | v1 file and behavior preserved; v2 subclasses the bundle/root and narrowly adapts local registration, profile metadata and blob budgets |
| `tests/contracts/fixture_factory.py` | Original producer and digest-repair routine, with a small v2 conversion helper | Existing synthetic non-executable payloads and record graph; no authority granted by converting version/context |
| Seven v1 schemas/shared definitions | Explicit versioned copies in `runtime/contracts/v2/` | v1 files/registry/examples preserved. Only v2 version/reference IDs, profile metadata/nullability and registry limits change |

The v2 schema registrar, blob verification loop and CLI are narrow adaptations of corresponding #3 functions. The v2 root additionally constrains each actual blob read to the remaining aggregate budget. Purpose evaluation itself remains the original implementation, so the first `qualification_run` does not depend on a previous game qualification. V2 tests cover both positive and negative admission semantics and report `evaluation_only: true`.

New native code is limited to closed diagnostic mapping, safe Rust wrappers, two header-checked C primitives and a foundation test probe. The probe is not the product CLI. Native v2 contract/policy admission, payload activation, leases as ownership proof, supervisor lifecycle and observer framing remain later stages.

## Standard/system implementation choices

| Boundary | Implementation used | Why no additional package was adopted |
|---|---|---|
| Cooperative file locking | Installed Rust 1.94.1 `File::try_lock`, `try_lock_shared`, `unlock` | Actual contention, shared/exclusive behavior, release and arbitrary writer controls pass. A crate cannot turn advisory locks into ownership/generation proof |
| Disposable test roots | Python `tempfile.TemporaryDirectory` | Existing platform API; no custom random naming/cleanup framework |
| Retained staging directory | Darwin `mkdtempat_np` beneath a borrowed parent descriptor, fixed template | Native mode 0700/uniqueness/parent refusal tests pass; caller retains the returned name and owns later publication/cleanup |
| Streaming digest | System CommonCrypto `CC_SHA256_Init/Update/Final`, fixed 1 MiB buffer, `pread` | No new hash algorithm/library or handwritten SHA context ABI. Native empty/abc/multichunk, bounds/error and preserved-offset controls pass |
| Descriptor lifetime | Rust borrowed `AsFd` and standard `File`; existing pinned libc | No parallel FD or syscall abstraction. Actual at-use/immutable admission remains Stage 2 |

CommonCrypto deprecation declarations in the current SDK are locally suppressed for this existing system API boundary; ordinary C warnings remain errors. This does not make an SDK/OS deployment claim beyond the recorded host. Rust and Apple system libraries remain external tool/host inputs, not bundled copies.

## Small Whisky portions reviewed

Review pin: `frankea/Whisky` commit `3abfbae945e3400caaa13cf2e78fe5a187a1405b`; archive SHA-256 `033eb22f95464b68042bbf053ae71855f18123119e862c49fb54f9b3a078b3ec`. The earlier source-only inspection remains the review input. No additional broad source acquisition, compilation or upstream test execution occurred in Stage 1.

- `EnvironmentBuilder`: its deterministic merge logic would require a Swift boundary and layers not needed by the flat approved profile environment. Reuse #3 collections instead of implementing another layered engine.
- Installer streaming hash: system incremental CommonCrypto already supplies the operation behind a small existing C boundary; a copied Swift/CryptoKit helper would add a second tool/language boundary without removing policy work.
- Process trailing-output/EOF tests: retain useful scenario references for Stage 3 while preserving #3's actual bounded drain/reap implementation. Direct Swift tests would exercise another process path.
- ProcessRegistry/per-bottle scenarios: use isolation/registration triggers as design references; stored PID cleanup does not replace generation/reservation proof.
- BottleOperations failed-copy/rollback scenarios: selecting atomic activation metadata and preserving old contexts removes the need for general move/export/copy features.

Direct Whisky source/test adoption is **none**. This is a decision about these concrete portions and required layers, not a language prohibition. Its reviewed GPL-3.0-or-later headers/terms remain relevant if direct code is later selected; preserve Swift, headers, origin and combination terms then. No translation to evade licensing, Pear license selection or upstream submission occurred.

## Dependencies and evidence boundaries

The existing libc archive checksum is `68ab91017fe16c622486840e4c83c9a37afeff978bd239b5293d61ece587de66` (MIT OR Apache-2.0). The exact archive was acquired through locked Cargo fetch and checked again together with its 360 extracted regular members. The manager retains #3's reviewed license/build-script hashes in `manager/dependencies.json` and identifies their source review. No new Rust dependency was selected.

The existing five hash-locked CPython 3.14/macOS ARM64 wheels were downloaded and installed offline into `.build/task9/venv`; this is a task-owned test environment, not a rebuilt-from-source Python dependency claim. All native Cargo build/test commands use locked/offline mode and controlled compiler/linker inputs. Build products are confined to one task9 leaf, symlink outputs are rejected, and new attempts retain unique logs/metadata. Other task caches/builds/prefixes were not used or modified.

Original #3 sources, 55-case corpus, two pipe-fault source cases and ten history records remain unchanged. The current reproduction checker now detects the three added contract Python files and expanded suite inventory; the old result is historical evidence rather than a new full-current-tree pass. All its 58 original source hashes still match, and the original comparison consistency check passes. Existing experiment regression tests were rerun (60 pass). The current manager's 55-case adaptation and actual pipe faults belong to Stage 3 and were not run in Stage 1.
