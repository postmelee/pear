# Contributing to the Rosetta-free goal

Pear's final goal is an owned Windows Steam game experience on Apple Silicon
without Rosetta in any required host process or library. There is **no player-ready
Rosetta-free preview**. The [Rosetta Preview](../rosetta-preview.md) is a separate
interim path; improving it does not automatically qualify native execution.

## Start with a bounded task

Run the [portable first checks](getting-started.md) and read the [architecture](../architecture.md).
Inspect open Issues and their latest evidence before proposing overlapping work.
Examples of current engineering areas (Issue state remains authoritative):

| Area | Read first | Work tracking |
|---|---|---|
| Native host observations | [Host capability evidence](../host-capabilities.md) | [#10](https://github.com/postmelee/pear/issues/10) |
| Steam and game startup | [FEX integration](fex-host.md) | [#11](https://github.com/postmelee/pear/issues/11), [#46](https://github.com/postmelee/pear/issues/46) |
| Owned-game qualification | [Delivery criteria](../delivery-plan.md) | [#12](https://github.com/postmelee/pear/issues/12), [#16](https://github.com/postmelee/pear/issues/16) |
| Reproducible runtime assembly | [Source qualification](../source-qualification.md), [Wine](wine-host.md), [DXMT](dxmt-build.md) | [#13](https://github.com/postmelee/pear/issues/13) |
| Portable regression evidence | Existing test fixtures and [contracts](../runtime-contracts.md) | [#14](https://github.com/postmelee/pear/issues/14) |

Documentation, deterministic fixture checks and source inventory improvements can
help without a provisioned runtime or game. Agree scope before implementation;
an Issue on this list is not necessarily unassigned or a beginner task.

## Split native development components

[Task #56](https://github.com/postmelee/pear/issues/56) establishes separate source repositories. The component
repositories are private and require collaborator access. Upstream history,
source languages, file-specific notices and contribution policies remain intact.

| Component | Source and responsibility |
| --- | --- |
| [Wine](https://github.com/postmelee/pear-wine) | Native/PE Windows implementation, memory owner and wire/graphics ABI providers |
| [FEX](https://github.com/postmelee/pear-fex) | Translator/frontend and canonical CPU source corpus |
| [DXMT](https://github.com/postmelee/pear-dxmt) | Renderer and typed graphics consumers; reverse Metal header providers |
| [Common runtime](https://github.com/postmelee/pear-runtime) | Compatible locks, explicit-input reconstruction, assembly, shared diagnostics and integration verification |
| [Pear](https://github.com/postmelee/pear) | App, manager, game/account policy and development selection |

The [runtime development guide](https://github.com/postmelee/pear-runtime/blob/codex/task56/docs/development.md) supplies the selected source/build lock,
exact retained-input prerequisites, exercised assembly/fixture commands and
bounded recovery procedure. The Stage 3 reconstruction (local report; publication pending) and
seven-fixture checkpoint (local report; publication pending) have bounded passing evidence. Candidate3 assembly and all fifteen fresh controls passed with independent
release: four native controls, three bootstrap controls, seven D36 cases and
an eighteen-frame presentation check. Accepted reuse keeps candidate2 CPU/ordering and graphics operations
under their original identities and reviewed limits; it does not relabel them as
new runs. Earlier failed captures remain retained; the unlocked candidate2 frame
observation is separate passing evidence. A clean Git clone alone does not recover the
preserved object/config/toolchain packs or private local inputs.

The Pear-side prepare/select/inspect interface below binds an exact reviewed
candidate and final operation, separate development state and complete producer
inputs. Stage 5 separates its portable/source checkpoint from real selected-
fixture execution. Neither changes Preview selection or the existing manager's
fixture-only admission; see the [native manager guide](runtime-supervisor.md#separate-development-candidate-path).

The selected source/test exports and accepted 196-method reconciliation are
recorded in the [local Stage 4 report](../../mydocs/working/task_m1_56_stage4.md).
The exact Stage 4 component tool/test checkpoints are published privately;
collaborator access is required. Stage 5 publication and final source-owner
cutover still require their named review gates. Preserve old source
and private candidate recovery inputs until their owners release them; this source
split does not solve or qualify the current game/runtime limitations.

## Select an isolated development candidate

This Pear selector is separate from Preview and the Rust manager's supported-play
admission. Run it from the reviewed Pear checkout with an explicitly admitted
ARM64 Python interpreter. Its spec uses scope `pear_development_selection` and
purpose `development_diagnostics`, an exact clean runtime checkout commit, a
separate development lock, exact fixture descriptor, optional exact game
descriptor, isolated state root and explicit protected roots. Use the exact clean Stage 5.1 source checkpoint and reviewed descriptor/producer
identities; the historical reconstruction lock remains unchanged. Keep that
selected source-only checkout at `.worktrees/runtime-development-v1`, separate
from later report/documentation edits on `runtime-task56`. Its creation requires
a fresh 128 MiB allowance plus the separate 6 GiB reserve; it copies no runtime
bundle, prefix, input pack or game. Retain it until all consumers accept a successor.

### Prepare the explicit local selection

Use a clean checkout of the exact runtime tool commit in Pear's separate
`tools/development/locks/task56-development-v1.json`. This development lock
binds the selected candidate's runtime and final assembly identities, its three
component build identities and source pins, and current tool source pins.
Its `reconstruction` field references the unchanged historical reconstruction
lock; `assembly_tool_checkpoint` identifies the earlier assembly producer. A
current tool commit does not reattribute those earlier builds or signatures.

Keep the following local inputs outside Git:

| Input | Required contents |
| --- | --- |
| `FIXTURE_DESCRIPTOR` | The closed `FixtureContext` descriptor: exact runtime/final-operation/profile/capability refs; current complete producer manifest; preserved provider root; immutable account-free seed ref and inventory; two selected module bindings; declared seven fixture refs; isolated existing output root. |
| `GAME_DESCRIPTOR` (optional) | The closed Pear `GameContext` descriptor for the same runtime/final-operation pair, all 69 owned Windows files and snapshot refs, manual-only policy, exact helper refs, separate current game producer manifest, fifteen selected control pairs and their three independent-release groups. |
| `DEVELOPMENT_LOCK` | The reviewed Pear development lock. Use its exact runtime tool pin, not the branch tip or an inspection result. |
| `RUNTIME_REPO` | Canonical, clean runtime checkout at that exact tool pin. |
| `FEX_TOOL_ROOT` | When the producer manifest consumes FEX modules, the canonical clean checkout at `lock.tool_sources.fex`. The selected tool root is the CPU checkpoint `9c9b602c07b57a08500862abfdf62e1bac351640`, distinct from the Stage 4 developer/export checkpoint and historical artifact-build commit. |
| `DEVELOPMENT_STATE` | New or selector-owned state directory outside source, candidate, seed, output, signing and game roots. Its parent must already exist. |
| `PROTECTED_ROOTS_JSON` | JSON array of existing canonical Preview/installed-runtime/user-state roots that this selection must preserve. |
| `SELECTION_SPEC` | Fresh local JSON filename whose existing parent is outside all source repositories. |

Descriptors bind retained inputs; a Git clone does not recreate them. Recreate
producer manifests from the exact new checkout after source changes, then review
and pin the descriptor again. The canonical closure functions are
`pear_runtime.fixtures.producers.manifest_for_roots` for fixtures and the same
function with `game_operation.GAME_ENTRY_MODULES`,
`game_operation.GAME_DYNAMIC_PATHS` and `game_operation.GAME_SCOPE` for the game
route. The game root map additionally contains `pear` and the consumed `fex`
root; the selected seven-fixture map needs only `runtime`. The selector checks
clean runtime/FEX state and every consumed file against its independent tool
commit before importing it. FEX generated/private inputs are separate from its
Python tool-source checkout.
Do not copy old producer hashes or reuse a saved current-authority result.

From the reviewed Pear checkout, this metadata-only recipe writes the complete
closed selection spec. Supply the named variables as environment variables;
leave `GAME_DESCRIPTOR` unset for the initial fixture-only selection.

```sh
"$ARM64_PYTHON" -B - <<'PY'
import json
import os
from pathlib import Path
from tools.development import runtime_candidate as selector

def existing(name):
    return Path(os.environ[name]).resolve(strict=True)

lock_ref = selector.fact(existing('DEVELOPMENT_LOCK'))
lock = selector.read_ref(lock_ref)
runtime = existing('RUNTIME_REPO')
state = Path(os.environ['DEVELOPMENT_STATE'])
protected = json.loads(os.environ['PROTECTED_ROOTS_JSON'])
game_path = os.environ.get('GAME_DESCRIPTOR')
spec = {
    'schema_version': 1,
    'scope': 'pear_development_selection',
    'purpose': 'development_diagnostics',
    'runtime_checkout': {'path': str(runtime), 'commit': lock['tool_sources']['runtime']},
    'lock_ref': lock_ref,
    'fixture_descriptor_ref': selector.fact(existing('FIXTURE_DESCRIPTOR')),
    'game_descriptor_ref': selector.fact(Path(game_path).resolve(strict=True)) if game_path else None,
    'state_root': str(state),
    'protected_roots': protected,
}
destination = Path(os.environ['SELECTION_SPEC'])
with destination.open('x') as stream:
    os.fchmod(stream.fileno(), 0o600)
    json.dump(spec, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps(selector.fact(destination), sort_keys=True))
PY
```

This creates data, not admission or execution authority. Run `prepare` next: it
checks the exact clean checkout, lock and selected context before creating its
owned metadata. Run the seven fixture cases and their independent release checks
first. Only then prepare the game descriptor/control packet and a new selection
spec with that descriptor. Its inspect/select operations still do not copy or run
the game. Requests and output names must be fresh for a later explicitly admitted
diagnostic operation.

Set `SELECTION_SPEC`, `PREPARED_SELECTION`, `DEVELOPMENT_STATE`,
`FIXTURE_REQUEST` and, only for a separately prepared owned-game diagnosis,
`GAME_REQUEST` from the reviewed local input inventory. The paths and game,
signing and authenticated input identities stay outside Git. Missing, changed,
purpose-incompatible or overlapping inputs refuse. Do not substitute a label or
an inspection result for a current execution grant.

```sh
"$ARM64_PYTHON" -B -m tools.development.runtime_candidate prepare --spec "$SELECTION_SPEC"
# Set PREPARED_SELECTION to the returned prepared_ref.path.
"$ARM64_PYTHON" -B -m tools.development.runtime_candidate inspect --prepared "$PREPARED_SELECTION" --kind fixture
"$ARM64_PYTHON" -B -m tools.development.runtime_candidate select --prepared "$PREPARED_SELECTION"
"$ARM64_PYTHON" -B -m tools.development.runtime_candidate inspect --state "$DEVELOPMENT_STATE" --kind fixture
```

Preparation creates only new local selection metadata. Selection updates only its
isolated development state and retains a transaction record; it does not activate
a Preview runtime. Inspection verifies the exact candidate, final assembly
operation, component builds/pins and producer inputs without copying or running
a game. The default `--kind auto` inspects the game context when a game descriptor
is present, otherwise the fixture context. Use `--kind fixture` for fixture-only
inspection; the other descriptor receives metadata/candidate checks, not game
ownership or execution admission. Diagnosis selects its corresponding context.
Reinspect before diagnosis. A fresh fixture request selects one of the
existing seven categories and a fresh output:

```sh
/usr/bin/arch -arm64 "$ARM64_PYTHON" -B -m tools.development.runtime_candidate diagnose-fixture \
  --state "$DEVELOPMENT_STATE" --request "$FIXTURE_REQUEST"
```

The selector delegates to the canonical runtime operation. It adds no second
launcher or observer; the runtime owns its live lease, deadline, current authority,
original result/cleanup oracles and final receipt. A fresh game diagnostic uses
Pear's explicit owned-game policy context and the same runtime lifecycle:

```sh
/usr/bin/arch -arm64 "$ARM64_PYTHON" -B -m tools.development.runtime_candidate diagnose-game \
  --prepared "$PREPARED_SELECTION" --request "$GAME_REQUEST"
```

The game command is a later, separately admitted operation, not an execution
performed by Task #56. It requires the complete exact owned-game and predecessor
control/release inputs, reviewed capacity, current authority and an isolated
output. Task #56 does not copy or execute Megabonk or qualify gameplay. A refusal
or unsupported result remains such. Preserve the exact prior spec, prepared
record and transaction for diagnosis; select a separately reviewed prior prepared
record to change development selection, without editing old receipts or Preview
state.

The Stage 5.1 portable/source checkpoint supplies these interfaces. Real
selection, fresh seven-case execution through the selector and independent
release are the separate Stage 5.2 gate; they are not claimed by the portable
checkpoint. Game copying and execution remain unperformed in Task #56.

### Finish a future game diagnostic with independent release

The future game request is a closed local JSON object with integer
`schema_version: 1`, scope `development_game_observation`, the exact
`descriptor_ref`, a fresh lowercase `output_name`, manual policy
`manual_feedback_v1` and `limits` containing `whole_timeout_seconds: 5400` and
`worker_log_bytes` between 1,024 and 16,777,216. The game branch retains the
selected D36 settings and manual input policy. An admitted diagnostic observation
may record a guest refusal or nonzero exit; operation completion is not gameplay
qualification. Its harness, current authority and owned cleanup must still pass.

After the worker exits, preserve its exact final `operation_ref`. Create a fresh
release request with exactly `schema_version: 1`, scope
`development_game_release`, and `operations` containing that ref. Run the
read-only resource checker from the same pinned runtime source. It also accepts
failed-operation evidence; missing identities or unavailable inspection remain
unknown, never implicitly released:

```sh
PYTHONPATH="$RUNTIME_REPO" "$ARM64_PYTHON" -B -m pear_runtime.fixtures.game_release \
  --request "$GAME_RELEASE_REQUEST" --output "$FRESH_GAME_RELEASE_RECORD"
```

The checker inspects the original loader/server/sentinel groups, retained game
observation companions and open handles, and transiently probes the existing
operation lock without truncating it. It does not signal processes or launch the
game. Preserve both diagnostic and independent-release outcomes.

## Understand the prerequisites

Existing Wine/FEX reconstruction guides use exact source pins, patches, build
receipts and development-authorized host execution. Some inputs currently depend
on prepared local artifacts. A clean clone does not yet supply a complete,
reproducible player runtime. Follow each guide's declared prerequisites; record
missing inputs as blockers, and do not copy private signing data or authenticated
Steam prefixes into a PR to make it reproducible.

Retain upstream languages and review reuse before writing replacements. Rust
rewrites and performance tuning are not prerequisites for delivering the Preview.
FEX has its own contribution restrictions; follow the
[upstream policy section](../contributing.md#respect-upstream-projects).

## Produce evidence for your claim

A successful native build or fixture is useful evidence for that bounded result.
A Rosetta-free game claim also needs observed process and library architecture
through Steam startup, gameplay, exit and resume; see the
[architecture requirements](../architecture.md#rosetta-independence-evidence).
Preserve failed and unperformed checks. Gameplay, saves, audio and ordinary-user
distribution have separate gates in the [single delivery plan](../delivery-plan.md).

M1 is the technical milestone. The proposed M2 covers ordinary-user delivery;
independent R1 research is not a replacement prerequisite. Report progress against
the actual Issue rather than marking the entire native experience supported.
