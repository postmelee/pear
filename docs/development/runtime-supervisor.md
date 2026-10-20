# Native runtime supervisor CLI

This developer CLI implements inspection, evaluation, immutable fixture activation, preparation, foreground supervision, status and manual recovery. It currently executes only owned native fixtures with a synthetic observer. It cannot run Wine, Steam or Megabonk. A native manager build and successful fixture run do not qualify the full runtime or an end-user release.

The [runtime contracts](../runtime-contracts.md) define independent eligibility and ownership requirements. The [profile guide](../game-profiles.md) explains fixture inputs and the researched Megabonk profile. Installation/library discovery, a Mac UI, automatic migration and save rollback remain separate work.

## Separate development candidate path

[Task #56](https://github.com/postmelee/pear/issues/56) provides a separate
[runtime-owned development reconstruction and diagnostic path](https://github.com/postmelee/pear-runtime/blob/master/docs/development.md). Its
explicit local candidate/operation records and current artifact authorization
do not change the Rust manager commands documented below. A diagnostic assembly
receipt is not a product `runtime_artifact` record, and a synthetic caller policy
cannot authorize it for supported play.

The separate [Pear development selector](rosetta-free.md#select-an-isolated-development-candidate)
provides the closed local spec and exact prepare/select/inspect/diagnose commands.
It binds a clean committed runtime tool root, preserves Preview/default state and
delegates to the existing runtime owner. Its committed portable/source checkpoint
and seven fresh selector-driven fixture operations passed, followed by independent
release. Game-input inspection and metadata reselection passed without copying
or executing the game. These do not change the manager's admission. The
[Rosetta-free guide](rosetta-free.md#split-native-development-components) lists
component owners and prerequisites. Candidate3's native four, three bootstrap controls, seven D36 cases and visible
presentation-frame check passed with independent release evidence. This document does not
waive required oracles or enable real-runtime admission in the existing manager.

## Build and reproduce

The tested development setup is ARM64 macOS 26.5.2, Xcode 26.6 with SDK 26.5, Rust/Cargo 1.94.1 and CPython 3.14. The build targets macOS 26.0; this does not declare an end-user minimum. Use physical paths without symlink components. Work from the repository root and keep all generated evidence under ignored `.build/task9/`.

The manager retains the reviewed `libc = 0.2.186` lock; Cargo build/test is offline. Populate the exact crate cache using the [existing dependency instructions](../../experiments/manager/README.md#reproduce-the-native-prototypes) if it is unavailable; do not substitute a version or another task's build. For the Python oracle, create a task-owned environment with the existing hash lock:

```sh
python3 -m venv .build/task9/venv
.build/task9/venv/bin/python -m pip download --only-binary=:all: --require-hashes --no-deps -r tests/contracts/requirements.lock --dest .build/task9/wheels
.build/task9/venv/bin/python -m pip install --no-index --find-links .build/task9/wheels --require-hashes --no-deps -r tests/contracts/requirements.lock
python3 -B tests/manager/build.py --output .build/task9/stage4 --locked
PEAR_MANAGER_BUILD=.build/task9/stage4 .build/task9/venv/bin/python -B -m unittest discover -s tests/manager -p test_cli.py
PEAR_MANAGER_BUILD=.build/task9/stage4 .build/task9/venv/bin/python -B -m unittest discover -s tests/profiles -p 'test_*.py'
```

These tests create their own finite native fixtures, policies, read-only images, observer sockets and unrelated sentinel. The CLI test executes the marked command examples below as argument arrays, checks actual settings/save persistence and both cancellation signals, and retains sanitized command outcomes locally. Failures remain failures; a missing mount identity is not retried through writable media. Run image-creating suites sequentially: availability during concurrent image attach/detach activity is not qualified.

Build receipts bind their recorded source and binary inputs. Reuse an existing output only when those identities remain valid; changed inputs require a fresh build and affected checks. Run labels such as `stage4` are output locations, not an authority. Raw media commands/private scratch paths stay in ignored local evidence; do not upload them as public logs.

At the Task #56 checkpoint, the existing fresh builder refuses the current
whole-file mismatch between `manager/Cargo.toml` and
`experiments/manager/rust/Cargo.toml`: the manager manifest now contains its
package license field. The original builder and these command examples remain
unchanged. Existing executable-policy source and command blocks still match the
recorded Task #9 Stage 6.1 evidence, but its exact binary/raw build output is not
available in the checked retained roots. Older retained Task #10 binaries bind a
different policy implementation and cannot replace it. Task #56 therefore makes
no fresh manager/profile test or clean-rebuild claim; the metadata reconciliation
belongs to a separate manager change. Its independent portable contract run
passed 154 tests plus the v1/v2 schema/example validators without a manager build.

## Manual fixture setup

The manager does not download, unpack or mount runtime payloads. The existing fixture producer constructs records and exact-byte references, adds the original redistributable C companion, generates a synthetic caller policy, creates an `hdiutil` UDRO image and attaches it read-only. It never copies game files. To explore the same setup, start the task-owned Python interpreter from the repository root with `PEAR_MANAGER_BUILD=.build/task9/stage4`, then run:

<!-- pear-fixture-setup -->
```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path("tests/manager").resolve()))
from case_adapter import Cases, BINARY
from state_support import cases

entries = cases()[:2]  # The checked-in fixture A and B profiles only.
media = Cases(entries, only=["a", "b"])
state, unused_default = media.state()  # Private mode 0700, outside the image.
manager = str(BINARY)
bundle_a, policy_a = (str(media.entries["a"][key]) for key in ("root", "policy"))
bundle_b, policy_b = (str(media.entries["b"][key]) for key in ("root", "policy"))
```

Keep this Python session alive while using its paths. The `Cases` adapter is test tooling, not a product installer or trusted-policy service. Its generated policy approves only owned synthetic records. A real caller must select independently reviewed policy; a file supplied by an untrusted bundle cannot approve itself. For manual command use, bind `PEAR_MANAGER` to `manager`, `PEAR_STATE` to `str(state)`, and `PEAR_BUNDLE`/`PEAR_POLICY` to A's or B's pair. Bind `PEAR_CONTEXT` to `a` or `b`. Quote these paths. Do not run the generic examples until these bindings exist.

First inspect the selected immutable request, then evaluate its declared fixture use:

<!-- pear-cli: inspect -->
```sh
"$PEAR_MANAGER" inspect --bundle-root "$PEAR_BUNDLE" --entry records/request.json --context fixture
```

<!-- pear-cli: evaluate -->
```sh
"$PEAR_MANAGER" evaluate --bundle-root "$PEAR_BUNDLE" --entry records/request.json --context fixture --purpose fixture_launch --policy "$PEAR_POLICY"
```

`record_valid: true` means parsing, structure and reachable-byte checks passed. `eligible: true` is relative to the requested purpose. Native `evaluate` may exit zero with `eligible: false`; always inspect the JSON fields. Neither command executes a child or grants real-runtime authority.

## Activate and prepare A and B

For each pair in turn, activate the read-only bundle and prepare its distinct context:

<!-- pear-cli: activate -->
```sh
"$PEAR_MANAGER" activate --bundle-root "$PEAR_BUNDLE" --entry records/request.json --context fixture --state-root "$PEAR_STATE" --policy "$PEAR_POLICY"
```

<!-- pear-cli: prepare -->
```sh
"$PEAR_MANAGER" prepare --state-root "$PEAR_STATE" --profile records/profile.json --context-id "$PEAR_CONTEXT" --policy "$PEAR_POLICY"
```

Activation commits a selection descriptor and retains prior version metadata. It verifies actual read-only media and admitted bytes; permission bits on a writable directory are insufficient. Preparation snapshots that selection, creates the five private mutable roots, binds exact family/profile/request/cache identities and applies only the permitted fixture setting. The context ID is a lower-case declared game/library instance. The A/B adapters use App IDs 101/102, `alpha`/`beta` arguments, opposite boolean settings, and distinct prefix/save/cache roots. Both use the same manager.

Activating B does not redirect A: launch uses A's prepared snapshot and A's original policy. Keep each old read-only volume at its recorded identity/location for reuse; remounting or replacement can invalidate its binding. Prefix/context lease descriptors remain held through mutation or run cleanup. Busy, aliased, replaced, incompatible and incomplete contexts refuse. `prepare` is not a way to clear a dirty journal.

## Foreground launch and observation

Launch requires an already connected socket descriptor inherited into the new manager process. `PEAR_OBSERVER_FD` below denotes that descriptor; a shell integer alone does not create or inherit a peer. The test launcher uses `socketpair`, the bounded synthetic [Peer](../../tests/manager/synthetic_peer.py) and `subprocess.Popen(..., pass_fds=(fd,))`.

<!-- pear-cli: launch -->
```sh
"$PEAR_MANAGER" launch --state-root "$PEAR_STATE" --request records/request.json --policy "$PEAR_POLICY" --context-id "$PEAR_CONTEXT" --observer-fd "$PEAR_OBSERVER_FD" --timeout-ms 5000 --output-limit 4096
```

For a manual A run in the Python session above, use this complete descriptor handoff:

<!-- pear-fixture-launch -->
```python
import json
import subprocess
from synthetic_peer import Peer
from support import experiment_cases

peer = Peer()
peer.work = state / "contexts/a"
peer.start()
process = None
try:
    fd = peer.client.fileno()
    process = subprocess.Popen(
        [manager, "launch", "--state-root", str(state), "--request", "records/request.json",
         "--policy", policy_a, "--context-id", "a", "--observer-fd", str(fd),
         "--timeout-ms", "5000", "--output-limit", "4096"],
        pass_fds=(fd,), stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    peer.client.close()
    output, errors, capture_failure = experiment_cases.capture_bounded(process, 10)
    assert capture_failure is None and not errors
    result = json.loads(output)
    assert process.returncode == 0 and result["classification"] == "success", result
    assert result["reaped"] and result["cleanup"] == "passed" and result["observation_complete"]
    assert peer.error is None
    print(result)
finally:
    if process is not None and process.poll() is None:
        process.kill()  # Only this directly owned manager, never a name or saved PID.
        process.communicate(timeout=5)
    peer.close()
```

The finite fixture reads the setting, writes its own absent save marker, and reads it on the next run. A mismatching preexisting marker exits without replacing the save. The CLI consumes bounded stdout/stderr and exports counts, not raw streams or inherited credentials. `fixture_only: true`, `runtime_eligible: false` remain explicit even on success. Its `translated` field concerns the manager; the fixture supplies its own native identity trace. Neither establishes every real host library's architecture.

SIGINT or SIGTERM sent to the foreground manager requests cancellation. The manager owns signaling/reaping and checks bounded cleanup; inspect `classification`, `reaped`, `cleanup` and `observation_complete`, not just the exit status. The CLI test signals only the freshly created process handle after its actual child trace appears. It does not use `killall`, process-name matching or PIDs recovered from a journal.

The present transport has a four-byte big-endian frame length, 1–256 KiB JSON frames, a 512 KiB allocated outbound queue and raw adapter buffers bounded to 1 MiB. Readiness, partial frames and queued sends have absolute 1,500 ms deadlines; progress does not reset them. Launch timeout is restricted to 100–5,000 ms and output limit to 256–65,536 bytes per stream. These fixture bounds are not a real-game duration interface.

The envelope is closed: `protocol_version`, `scope: synthetic`, `capture_id`, `request_sha256`, `record`. It binds request/capture/run identity, producer sequences, previous events, readiness and completed exits. It covers one synthetic owned-main lifecycle, not arbitrary Steam/Wine descendants or modules. Event references identify canonical in-session bytes; a complete persisted public evidence bundle is not produced. The synthetic elapsed-time convention does not establish a shared OS clock origin for a real collector.

[#9](https://github.com/postmelee/pear/issues/9) owns creation, cancellation, signals, reap, context mutation and cleanup. [#10](https://github.com/postmelee/pear/issues/10) must establish actual process/module attribution, backend permissions, shared timebase, coverage and gaps. Readiness is not an execution grant or complete-coverage proof; current fixture framing cannot silently be relabeled as a real observer. Real-runtime admission still refuses independently of synthetic policy success.

## Status and preservation-first recovery

<!-- pear-cli: status -->
```sh
"$PEAR_MANAGER" status --state-root "$PEAR_STATE" --context-id "$PEAR_CONTEXT"
```

`context_prepared` means prepared with no completed run journal. `context_clean` means the required last-run bookkeeping completed. `context_incomplete` means a nonclean journal remains; status can exit zero while reporting it. A busy context can refuse status. A free lease or missing live PID does not prove cleanup. Actual SIGKILL/abort crash tests leave incomplete state, and no custodian promises to clean descendants after the manager dies.

Preserve the previous context and saves. Keep the desired read-only selection activated, set a new lower-case `PEAR_NEW_CONTEXT` value, then create fresh state:

<!-- pear-cli: recover-new -->
```sh
"$PEAR_MANAGER" recover --state-root "$PEAR_STATE" --profile records/profile.json --new-context "$PEAR_NEW_CONTEXT" --policy "$PEAR_POLICY"
```

The new ID must not exist. This does not copy or restore saves, remove old state, mutate another profile or claim that crashed processes were cleaned. Unselected interrupted staging may remain for inspection. Do not clear journals, replace lease files or delete the only existing save copy to force a launch.

Alternatively, explicitly validate a previously clean compatible context with its original policy:

<!-- pear-cli: recover-existing -->
```sh
"$PEAR_MANAGER" recover --state-root "$PEAR_STATE" --profile records/profile.json --context-id "$PEAR_CONTEXT" --policy "$PEAR_POLICY"
```

`compatible_context_selected` verifies that explicit context; it does not change a global active-context pointer. Launch it using the same `--context-id`. Exact profile/request/cache identity and the preserved runtime snapshot must still match. Launch rechecks settings and identities at use. No upgrade, migration or automatic save rollback is performed.

When all owned runs have finished, `media.close()` detaches this test image and removes only its disposable scratch state, including fixture saves. Do this only for the `Cases` session above, whose data are disposable. The manager's recovery commands never perform that teardown. Test receipts and retained failures remain under `.build/task9/runs/` for review.

## Diagnostics and return status

| Command | Result handling |
|---|---|
| `inspect`, `evaluate` | Read `record_valid`, `eligible`, `outcome_codes`, `evaluation_only`. Native `evaluate` returns 0 for completed evaluation even if ineligible; the Python oracle instead returns 3 for valid ineligible input. |
| `activate` | Success: `selection_committed`. Ineligible, unavailable runtime authorization or non-read-only payload: refusal. Existing selected data are preserved. |
| `prepare`, `status`, `recover` | Read `phase`, `reason`, `runtime_eligible: false`, `native_error`. Return 0 for completed operation/status, 2 for command misuse, 3 for semantic refusal, 4 for native errors or uncertain publication. |
| `launch` | Return 0 for success, 1 for invalid contract, 3 for ineligibility/readiness/busy/incomplete refusal, 4 for cancellation, child failure or cleanup/observation failure. Return values do not copy the child's code; read `exit_code` and `signal`. |

Global command syntax errors return 2, but launch-specific option errors currently map to `invalid_contract`/1. Native inspection/activation invalid input returns 1; do not assume one universal error shape across commands. Native numeric errors can remain present after a narrowly verified cleanup exception. Do not discard such diagnostics or turn failed/unknown operations into support evidence.
