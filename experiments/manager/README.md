# Native manager experiments

These are bounded Issue #3 research fixtures for comparing a Rust and a Swift manager implementation. Both implement validation and process supervision natively. Python constructs the common corpus and independently evaluates the version 1 contracts; it is never called by either candidate. Passing these fixtures does not qualify Wine, Steam, Megabonk, signing, distribution, or an entire Rosetta-free runtime.

## Reproduce Stage 3

Run from the repository root on native Apple Silicon with the toolchains in [`dependencies.json`](dependencies.json). The existing Stage 2 oracle environment must be installed using its [hashed requirements](../../tests/contracts/requirements.lock). Prefetch the exact reviewed `libc` release with `cargo fetch --manifest-path experiments/manager/rust/Cargo.toml --locked` if absent. `build.py` checks its archive and extracted source bytes before the locked offline build. This currently uses Cargo's default crates.io cache location; custom Cargo homes and ambient Cargo configuration files are not supported by this experiment. Swift has no external package dependency.

```bash
python3 experiments/manager/build.py --output .build/task3/prototypes --locked
python3 experiments/manager/run_cases.py --build-root .build/task3/prototypes --all --oracle .build/task3/venv/bin/python
python3 -m unittest discover -s experiments/manager -p 'test_*.py'
```

Build commands, tool versions, input hashes, Mach-O slices, dependencies and binary hashes are recorded in the ignored output directory. Each corpus run retains its own results and owned bundle directory; `case-results.json` points to the latest result by containing a copy. Rebuild after changing native sources. The harness checks native source and binary identities before execution. Never use a game installation or authenticated prefix as a fixture bundle.

## Shared contract subset

Each candidate accepts exactly four reachable version 1 record kinds: `runtime_lock`, `runtime_artifact`, `game_profile`, and a launch request. The controlled fixture component, family, ABI, host requirements, store, game identities, operations and executable identity are fixed by [`run_cases.py`](run_cases.py). The source blob is a deterministic tar containing the actual owned C child and bridge. The build-configuration blob and actual native executable are hashed. Signing and observation references retain explicit synthetic evidence; their fields do not attest to a signature or a production runtime build.

Both candidates reject unknown keys, kinds, versions, duplicate keys, invalid UTF-8/scalars, BOM, floats, nonfinite values, oversized integers, incompatible identities, unsafe references and untrusted executable digests. They traverse descriptor-relative paths without following symlinks and reject nonregular inputs. They require existing owned state directories and empty profile operations. The only environment value allowed for the environment fixture is `PEAR_FIXTURE_VALUE=allowed`; the child never inherits the parent's environment. Guest path `fixture.exe` is a declaration, not a Mac path to execute. The host fixture's digest must also equal an independent command-line trust pin.

Limits are 256 KiB per JSON record, 4 MiB aggregate JSON, nesting depth 32, 8,192 JSON nodes including object keys, 2,048 Unicode scalars per string, 96 per key, 128 records and 64 references per record. Prototype blob limits are stricter than the reference validator: 16 MiB per blob and 64 MiB aggregate. Path limits are at most 512 UTF-8 bytes and 32 segments; relative paths containing `%` or starting with `~` are rejected. Some field text also has a stricter 4,096-byte limit. Different-path inode aliases are rejected by both prototypes, including identical hardlinked blob bytes; the reference validator permits that specific blob case. Valid profile setting operations and unknown source provenance can be inspected by the general reference contract but are outside this executable subset. The research-context case asks the oracle to validate records in their declared research context, then confirms that fixture execution is ineligible. These are declared scope differences, not claims of implementing every version 1 contract.

## Execution and observations

The command-line interface is identical:

```text
pear-manager --bundle-root ABSOLUTE_PATH --entry records/request.json \
  --fixture-sha256 HEX --timeout-ms 1500 --output-limit 4096 \
  --observer-ready yes --observer-gap no
```

The managers launch only the owned C fixture with argument arrays, `/dev/null` standard input, a scoped environment and a new process group. They use bounded nonblocking output and deadlines; no child output, private paths, PIDs or environment values appear in their JSON result. Ordinary functional cases allow 1,500 ms, while deliberate delay and descendant-pipe cases allow 300 ms. This avoids treating a cold copied executable's initial launch latency as the intended delayed-child test. No durations from Stage 3 are used for a language performance claim.

Each manager confirms its running ARM64 slice and `sysctl.proc_translated` state. The child does the same, writes its creation identity to the owned prefix, and independently records a pipe-holding descendant. The harness checks that those identities disappear and that an unrelated sentinel remains alive. Missing observer readiness prevents launch; the controlled gap flag yields `observer_gap`. These flags and child traces are fixtures, not a module observer or complete host-process coverage evidence.

The direct child remains unreaped until owned-group cleanup, preventing PID/group reuse during signaling. On the tested Darwin version, signaling a zombie-only group can return `EPERM`. The managers accept that case only after `waitid(WNOWAIT)` confirms their exact leader has exited and a bounded `proc_listpids(PROC_PGRP_ONLY)` query finds no other group member. Errors, truncation and other members do not establish cleanup. A leader that exits while its descendant keeps a pipe open reaches the execution deadline; cleanup kills the owned group before reaping the leader. The harness verifies creation-identity disappearance, while only the manager reaps its direct child. Grandchildren are reaped by the OS.

The outer harness also bounds output and time. An outer watchdog intervention always fails the case and does not claim cleanup of a fixture's separate process group. Trace disappearance is checked independently; unresolved identities remain failed observations. Fixture delays are finite, but the harness is not a production recovery supervisor. Local failed bundles/logs are retained for diagnosis.

## C ABI and dependencies

`pear_process_identity(int32_t pid, uint64_t *seconds, uint64_t *microseconds)` returns zero on success, otherwise a bounded native error. Output storage is caller-owned and valid only on success. The bridge performs one `proc_pidinfo` query; it does not allocate, retain pointers, spawn, signal, wait, reap or unwind. Both candidates directly implement the rest of their lifecycle logic, including bounded group enumeration.

Rust uses the exact locked `libc` crate, standard library and explicit C ABI declarations. Swift uses Foundation/Darwin and explicit CommonCrypto/libproc declarations. Both use system `CC_SHA256`. Apple SDK/system library availability is a host dependency; this is not a portable standalone hashing library or a finalized license/release decision for Pear. The [dependency inventory](dependencies.json) records the source/license/build-script review and observed compiler versions.

## Limits and next stage

Concurrent mutation of a bundle is unsupported. Descriptor validation and immediate executable identity checks reduce exposure but do not eliminate the pathname-execution race in `Command`/`posix_spawn`; #9 must establish immutable runtime and mutable-state ownership for production use. Successful fixtures cannot validate arbitrary imported executable bytes, a real observer handshake, macOS distribution entitlements or full game-process coverage.

[`comparison-plan.json`](comparison-plan.json) freezes functional gates, builds, sampling and qualitative review before Stage 4. Its inert comment edits are predetermined native-source incremental build inputs. Stage 3 does not select a manager language, measure power/game performance, or implement the production manager. The custom parsers and native FFI surface are maintenance costs to evaluate, not reasons to assume either language will win.
