# Native manager experiments

These are bounded Issue #3 research fixtures for comparing a Rust and a Swift manager implementation. Both implement validation and process supervision natively. Python constructs the common corpus and independently evaluates the version 1 contracts; it is never called by either candidate. Passing these fixtures does not qualify Wine, Steam, Megabonk, signing, distribution, or an entire Rosetta-free runtime.

## Reproduce the native prototypes

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

The managers launch only the owned C fixture with argument arrays, `/dev/null` standard input, a scoped environment and a new process group. They use bounded nonblocking output and deadlines; no child output, private paths, PIDs or environment values appear in their JSON result. Ordinary functional cases allow 5,000 ms within the existing CLI range and ten-second outer watchdog. Deliberate timeout cases retain 1,500 ms; scored successful launches also retain the frozen 1,500 ms limit. The intentional delay lasts 5,000 ms and the pipe-holding descendant has a 10-second bounded lifetime, so both negative cases still require timeout and owned cleanup. Stage 4 corrected the original 300 ms negative-case limits after mandatory traces were sometimes absent when fresh copied children reached the deadline; both languages exhibited the failure. The original attempts remain failed evidence. A later 1,500 ms ordinary-case timeout led to separating the wider functional budget from the unchanged scored-launch budget. Each revision records its input identities and requires the relevant rebuild/checks plus complete comparison reruns; none retroactively passes an earlier failure. No durations from Stage 3 are used for a language performance claim.

Each manager confirms its running ARM64 slice and `sysctl.proc_translated` state. The child does the same, writes its creation identity to the owned prefix, and independently records a pipe-holding descendant. The harness checks that those identities disappear and that an unrelated sentinel remains alive. Missing observer readiness prevents launch; the controlled gap flag yields `observer_gap`. These flags and child traces are fixtures, not a module observer or complete host-process coverage evidence.

The direct child remains unreaped until owned-group cleanup, preventing PID/group reuse during signaling. On the tested Darwin version, signaling a zombie-only group can return `EPERM`. The managers accept that case only after `waitid(WNOWAIT)` confirms their exact leader has exited and a bounded `proc_listpids(PROC_PGRP_ONLY)` query finds no other group member. Errors, truncation and other members do not establish cleanup. A leader that exits while its descendant keeps a pipe open reaches the execution deadline; cleanup kills the owned group before reaping the leader. The harness verifies creation-identity disappearance, while only the manager reaps its direct child. Grandchildren are reaped by the OS.

The outer harness also bounds output and time. An outer watchdog intervention always fails the case and does not claim cleanup of a fixture's separate process group. Trace disappearance is checked independently; unresolved identities remain failed observations. Fixture delays are finite, but the harness is not a production recovery supervisor. Local failed bundles/logs are retained for diagnosis.

## C ABI and dependencies

`pear_process_identity(int32_t pid, uint64_t *seconds, uint64_t *microseconds)` returns zero on success, otherwise a bounded native error. Output storage is caller-owned and valid only on success. The bridge performs one `proc_pidinfo` query; it does not allocate, retain pointers, spawn, signal, wait, reap or unwind. Both candidates directly implement the rest of their lifecycle logic, including bounded group enumeration.

Rust uses the exact locked `libc` crate, standard library and explicit C ABI declarations. Swift uses Foundation/Darwin and explicit CommonCrypto/libproc declarations. Both use system `CC_SHA256`. Apple SDK/system library availability is a host dependency; this is not a portable standalone hashing library or a finalized license/release decision for Pear. The [dependency inventory](dependencies.json) records the source/license/build-script review and observed compiler versions.

## Prototype limits

Concurrent mutation of a bundle is unsupported. Descriptor validation and immediate executable identity checks reduce exposure but do not eliminate the pathname-execution race in `Command`/`posix_spawn`; #9 must establish immutable runtime and mutable-state ownership for production use. Successful fixtures cannot validate arbitrary imported executable bytes, a real observer handshake, macOS distribution entitlements or full game-process coverage.

[`comparison-plan.json`](comparison-plan.json) freezes functional gates, builds, sampling and qualitative review before Stage 4. Its inert comment edits are predetermined native-source incremental build inputs. The custom parsers and native FFI surface are maintenance costs to evaluate, not reasons to assume either language will win. The experiments do not measure game power/performance or implement the production manager.


## Reproduce the controlled comparison

After rebuilding the current native sources and confirming no other heavy work is running on the host, run:

```bash
python3 experiments/manager/compare.py --plan experiments/manager/comparison-plan.json --build-root .build/task3/prototypes --output .build/task3/comparison-raw.json
python3 experiments/manager/compare.py --check-report experiments/manager/results/comparison.json
python3 experiments/manager/run_cases.py --build-root .build/task3/prototypes --all --oracle .build/task3/venv/bin/python
```

The first command runs the complete functional corpus before and after the comparison. It retains three clean builds, three predetermined incremental builds, five unscored warmups and 30 recorded launches per candidate. Each attempt has a separate ignored directory; a failed gate stops the attempt. Preserve failed attempts and review/redact results before copying a completed report into `results/`. The report checker verifies the committed record against current source identities; a locally rerun report can be checked by supplying its own path instead. Passing the checker establishes record consistency, not independent authenticity.

The [manager-language decision](../../docs/decisions/manager-language.md) weighs these measurements and qualitative evidence. Durations include the declared native build command or the whole manager invocation, including validation and child cleanup. Darwin `wait4` RSS is OS accounting for the waited command, not an independently sampled process-tree peak. Dependency caches, OS caches, 1 ms wait polling and fixed Rust-then-Swift launch pairing limit interpretation. No cache flushing, temperature/power measurement or distribution qualification is performed.

## Rust pipe-setup failure regression

Stage 4 found that a failed nonblocking-pipe setup could leave a blocking descriptor in cleanup. The Rust implementation now evaluates both setup calls and closes both read ends if either fails, then performs bounded owned-process cleanup. Two test-only fault cases exercise each failure position with a real child and pipe-holding descendant; they check descriptor closure, reaping, identity disappearance and unrelated sentinel survival. The production command line and environment provide no fault-injection option.

After the prototype build above, reproduce the tests with the same controlled environment and C bridge:

```bash
python3 - <<'PYTEST'
from pathlib import Path
import subprocess
import sys
sys.path.insert(0, 'experiments/manager')
import build
root = Path.cwd()
base = root / '.build/task3/prototypes'
env = build.controlled_environment()
env.update(CARGO_TARGET_DIR=str(root / '.build/task3/rust-pipe-tests'),
           CARGO_ENCODED_RUSTFLAGS='\x1f'.join(['-C', 'link-arg=' + str(base / 'native_bridge.o'), '-C', 'link-arg=-lproc']),
           PEAR_MANAGER_TEST_FIXTURE=str(base / 'bin/fixture-child'))
raise SystemExit(subprocess.run(['cargo', 'test', '--manifest-path', 'experiments/manager/rust/Cargo.toml', '--locked', '--offline', '--target', 'aarch64-apple-darwin', '--', '--test-threads=1'], env=env).returncode)
PYTEST
```


## Recorded Stage 4 outcome

The [manager decision](../../docs/decisions/manager-language.md) selects Rust for the new supervisor, with Swift's tradeoffs and remaining production gates explicit. The [current comparison](results/comparison.json), [final corpus](results/final-corpus.json) and [second input revision](results/fixture-input-revision2.json) bind the final declared functional limits and the preserved historical records. Four full corpus runs passed (110 invocations each), all 82 comparison rows were retained, and 40 Python regression tests passed. No failed historical run was erased or relabeled; in particular, a prior 1,500 ms startup failure remains unexplained. The [Stage 4 report](../../mydocs/working/task_m1_3_stage4.md) records the full sequence and two Rust fault tests. The separate [Stage 5 reproduction](results/reproduction.json) now records functional agreement from empty outputs; it does not rerun these timing measurements.


## Reproduce from empty outputs

Stage 5 uses a fresh output directory, a new validator virtual environment and new native build products. Prefetch the five exact wheels into `.build/task3/wheels` using the [reference-validator setup](../../docs/runtime-contracts.md#reference-validator-and-reproducible-setup), and the locked Rust crate as described above. The reproduction command uses the cached reviewed bytes and performs no dependency download. Missing or altered inputs fail; obtain the pinned inputs explicitly rather than substituting versions.

```bash
python3 experiments/manager/reproduce.py --output .build/task3/reproduction --require-empty
python3 experiments/manager/reproduce.py --check-report experiments/manager/results/reproduction.json
```

Keep prior outputs. For another attempt, select a new empty `.build/task3/reproduction-<label>` directory (lowercase letters, digits, underscores or hyphens in the label); do not delete a failed attempt to reuse its path. The first command recreates the environment, runs contract and native fixture verification, and retains local evidence. The second checks the committed sanitized record; it does not execute its claims or establish independent authenticity. Public evidence must exclude local paths, process identities, raw streams and environment values.

This procedure reuses the installed Python, Rust, Apple toolchain, SDK and hash-verified default Cargo source cache. It does not reconstruct those toolchains, flush machine caches, or reproduce third-party wheels from source. Owned temporary fixture directories used by existing tests may be outside the build directory and are cleaned by those tests. The comparison's 82 timing rows are preserved, not remeasured by this functional reproduction. Same-Mac functional agreement does not establish independent-host, minimum-OS, signature-byte, distribution or game qualification.


The committed [reproduction record](results/reproduction.json) passed 119 contract tests, 60 experiment tests (40 existing and 20 reproduction checks), two Rust fault tests and 110 native corpus invocations. All three rebuilt executables are ARM64 and passed read-only strict ad-hoc signature inspection. Both manager payload hashes differ from the Stage 4 measured build; their exact hashes/sizes and matching semantic outcomes are retained. No source- or signature-byte reproducibility is claimed. See the [Stage 5 report](../../mydocs/working/task_m1_3_stage5.md) for acceptance and preservation details.
