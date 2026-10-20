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
repositories are public as of October 21, 2026 under
[Task #77](https://github.com/postmelee/pear/issues/77). Upstream history,
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
bounded recovery procedure. The Stage 3 reconstruction and seven-fixture
checkpoint have bounded passing evidence recorded in the [final report](../../mydocs/report/task_m1_56_report.md). Candidate3 assembly and all fifteen fresh controls passed with independent
release: four native controls, three bootstrap controls, seven D36 cases and
an eighteen-frame presentation check. Accepted reuse keeps candidate2 CPU/ordering and graphics operations
under their original identities and reviewed limits; it does not relabel them as
new runs. Earlier failed captures remain retained; the unlocked candidate2 frame
observation is separate passing evidence. A clean Git clone alone does not recover the
preserved object/config/toolchain packs or private local inputs.

The Pear-side prepare/select/inspect interface below binds an exact reviewed
candidate and final operation, separate development state and complete producer
inputs. The committed Stage 5.1 source checkpoint and fresh Stage 5.2 selector
checks have distinct records. Seven fresh candidate3 fixture operations passed;
the game prerequisite packet retains eight Stage 4 candidate3 native/bootstrap/
frame operations under their original identities. Fresh independent release
observations cover all fifteen selected operations. Exact game-input inspection
admitted 69 files and 92 producer files, followed by successful game-to-fixture-to-
game metadata reselection. No game was copied or executed. None changes Preview
selection or the existing manager's fixture-only admission; see the [native manager guide](runtime-supervisor.md#separate-development-candidate-path).

The selected source/test exports and accepted 196-method reconciliation are
recorded in the [local Stage 4 report](../../mydocs/working/task_m1_56_stage4.md).
The #11, #10 and #12 owners accepted the exact selected implementation, tests
and development boundary. The [canonical source-cutover record](https://github.com/postmelee/pear-runtime/blob/codex/task56/provenance/source-cutover-task56.json)
and [final repository references](../../mydocs/tech/task_m1_56_source_cutover.json)
separate accepted source revisions, published documentation tips, compiled source
pins and executed tool pins. The four component source repositories are publicly
readable. Historical pending-cutover records remain dated
evidence; future edits to the accepted range belong to the mapped new owners.
Preserve legacy consumer copies and private recovery inputs until their owners
release them. This does not activate a runtime or qualify the game.

### Current source and execution baseline

PR [#58](https://github.com/postmelee/pear/pull/58) merged the Task #56 handoff,
including the runtime-selection and manual-confirmation corrections, at Pear
`26927fa2cc4e5d606ac02f2c1c1eceb54e83f60e`. Use the corrected selector source
`400da1145b20ff787ad30b251ea5c810ed291c29` with its reviewed descriptors.
A later source or documentation tip does not change any retained build or tool
identity. The historical final Task #56 component documentation tips are:

| Repository | Historical Task56 source/documentation tip | Candidate build or executed-tool pin |
| --- | --- | --- |
| Wine | `007291b81de386fd8886770c33b5d385c078635d` | Task56 selected bounded build `1b76db6902345388c589ba3909b22badf751dfd5`; retained WGI producer is identified separately below |
| FEX | `4ae26ddf9a21b52cd50d096504c4d0ea5ab49204` | Build `c62ed75aa6a33809ddb76c7f40aabbe4f4fbdda6`; diagnostic tool `9c9b602c07b57a08500862abfdf62e1bac351640` |
| DXMT | `d0ad50946ab64bbe4dc3584a5d91f8e99a6e492c` | Build `e800e770006fc7c37831ab857000a4781c85f6fd` |
| Common runtime | `9be1545f5a0845d3b14d4b845bf6bd413a224df3` | Executed tool `6f0202b457f0e585c5c7621a63d203e77d07386d` |

[Task #75](https://github.com/postmelee/pear/issues/75) completed documentation
reconciliation, source-publication review and bounded WGI source-to-PE evidence.
Pear [PR #76](https://github.com/postmelee/pear/pull/76) and the four component
PR #1s are merged. Their integrated source/tooling baselines are:

| Component | Task75 integrated baseline |
| --- | --- |
| Wine | [`921039a`](https://github.com/postmelee/pear-wine/commit/921039a56a45544990895910d2a4dca801af4007) |
| FEX | [`b210b27`](https://github.com/postmelee/pear-fex/commit/b210b272fb2784a1a1d04b4d16415c9edefa3519) |
| DXMT | [`e02987b`](https://github.com/postmelee/pear-dxmt/commit/e02987bbe1bfee6b56759f6d1a35090e3404568a) |
| Common runtime | [`d49869e`](https://github.com/postmelee/pear-runtime/commit/d49869e94ab6c2f7e40d4370aa623a9e99541527) |

The component integration/default branch remains `codex/task56`; later
publication-documentation commits do not replace these source/tooling baselines
or the selected build and executed-tool pins above. Task #77 rechecked the
[integrated audit](https://github.com/postmelee/pear/issues/75#issuecomment-6295812832)
and made all four repositories public. Existing builds, private prerequisites
and selected tool roots remain retained. Public source access does not recover
missing inputs, activate a runtime, authorize a game run or qualify gameplay.

## Select an isolated development candidate

This Pear selector is separate from Preview and the Rust manager's supported-play
admission. Run it from the reviewed Pear checkout with an explicitly admitted
ARM64 Python interpreter. Its spec uses scope `pear_development_selection` and
purpose `development_diagnostics`, an exact clean runtime checkout commit, a
separate development lock, exact fixture descriptor, optional exact game
descriptor, isolated state root and explicit protected roots. Use Pear source
`400da1145b20ff787ad30b251ea5c810ed291c29` for the corrected selector and manual
confirmation policy, with its newly reviewed descriptor/producer identities.
The historical reconstruction lock and runtime tool pin remain unchanged. Keep
the selected runtime source-only checkout at `.worktrees/runtime-task56`, detached at runtime
`6f0202b457f0e585c5c7621a63d203e77d07386d`. Later report/documentation edits use
`.worktrees/runtime-development-v1` on `codex/task56`. Creating another source
worktree needs fresh capacity review: the exercised allowance was 128 MiB plus
a separate 6 GiB reserve, with no runtime bundle, prefix, input pack or game copy.
Retain the selected root until all consumers accept a successor.

Candidate3 binds ten assembly-producer files by exact bytes and absolute paths.
An initial attempt from the other source checkout refused
`assembly_builder_changed` before loader execution despite identical source
bytes. That failed operation remains retained. The no-code worktree role swap
restored the recorded builder paths; fresh v5 requests then passed without
changing an authority gate. A retained candidate is not freely relocatable:
commit equality alone cannot replace its recorded builder root. A new root needs
a separately reviewed assembly and new records.

### Prepare the explicit local selection

Use a clean checkout of the exact runtime tool commit in Pear's separate
[development lock](../../tools/development/locks/task56-development-v1.json). This lock
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
| `DEVELOPMENT_STATE` | New or selector-owned state directory disjoint from source, candidate, seed, output, signing, game and descriptor/input-metadata roots. Its parent must already exist. Use a sibling of the metadata root, not a child inside it. |
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
Python tool-source checkout. The selector promotes the admitted runtime root
even if it already appears later in `sys.path`, validates bootstrap source/package
resolution before import, and rejects incompatible loaded modules. Start a fresh
process when changing tool roots.
Do not copy old producer hashes or reuse a saved current-authority result. Keep
source worktrees at their recorded paths while any producer manifest consumes
them; report-only commits do not replace the source commit recorded at capture.

Keep selection state separate from the existing private metadata directory.
For example, set these exported variables under a canonical existing local
parent; the input directory must already exist:

```sh
export DEVELOPMENT_INPUT_ROOT="$LOCAL_PARENT/task56"
export DEVELOPMENT_STATE="$LOCAL_PARENT/pear-development-state-task56-v1"
export SELECTION_SPEC="$DEVELOPMENT_INPUT_ROOT/selection-v5.json"
```

The exercised initial spec placed state inside the metadata root and refused
`state_input_overlap` without creating that state. The accepted spec used a
sibling directory; no input or isolation check was weakened.

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
owned metadata. Initial integration requires the seven fixture cases and their
independent release checks before preparing the game descriptor/control packet.
For a later admission-only rebind, an explicitly reviewed reuse decision may
retain those exact operations and release records when their runtime, payloads
and oracles are unchanged. Re-admit their complete input references; do not
relabel them as new executions. Prepare a new selection spec with that descriptor. Its inspect/select operations still do not copy or run
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

The Stage 5.1 portable/source checkpoint supplies these interfaces. Stage 5.2
separately exercised preparation, selection, inspection, seven fresh fixture
operations and independent release. The selected game context's 69-file input
admission passed; no game copy or execution followed.

Metadata recovery was exercised with the previously returned exact fixture and
game prepared records. The same state retained a transaction for each selection:

```sh
"$ARM64_PYTHON" -B -m tools.development.runtime_candidate select --prepared "$GAME_PREPARED_SELECTION"
"$ARM64_PYTHON" -B -m tools.development.runtime_candidate inspect --state "$DEVELOPMENT_STATE" --kind game
"$ARM64_PYTHON" -B -m tools.development.runtime_candidate select --prepared "$FIXTURE_PREPARED_SELECTION"
"$ARM64_PYTHON" -B -m tools.development.runtime_candidate inspect --state "$DEVELOPMENT_STATE" --kind fixture
"$ARM64_PYTHON" -B -m tools.development.runtime_candidate select --prepared "$GAME_PREPARED_SELECTION"
"$ARM64_PYTHON" -B -m tools.development.runtime_candidate inspect --state "$DEVELOPMENT_STATE" --kind game
```

This restores a development selection only. It does not restore a runtime,
object/toolchain pack, prefix, save, credential or private state, and it does not
reuse an earlier execution grant. The separate input-recovery exercise restored
only exact binding metadata and one 3,634-byte common header; see the
[runtime recovery limits](https://github.com/postmelee/pear-runtime/blob/codex/task56/docs/development.md#bounded-exact-input-recovery).

### Finish a future game diagnostic with independent release

The future game request is a closed local JSON object with integer
`schema_version: 1`, scope `development_game_observation`, the exact
`descriptor_ref`, a fresh lowercase `output_name`, manual policy
`manual_feedback_v1` and `limits` containing `whole_timeout_seconds: 5400` and
`worker_log_bytes` between 1,024 and 16,777,216. The game branch retains the
selected D36 settings and manual input policy. An admitted diagnostic observation
may record a guest refusal or nonzero exit; operation completion is not gameplay
qualification. Its harness, current authority and owned cleanup must still pass.
The corrected manual policy verifies a copy of the confirmation, applies the
verifier-derived expiry, and retains the original control identity for repeated
ticks and the matching finish request. Altered identity, expiry and terminal
states still refuse or end the hold; no automatic game input is introduced.

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

### Continue the developer Megabonk investigation

The [accepted source-cutover record](https://github.com/postmelee/pear-runtime/blob/codex/task56/provenance/source-cutover-task56.json)
identifies the single editable owners and exact reviewed checkpoints. It does not
activate the candidate or replace the historical compilation and executed-tool
pins. Task #56 inspected all 69 owned inputs and exercised metadata selection and
recovery; game copying, execution and gameplay remain unperformed.

The original D36 diagnostic still ended `owner_refused` during loading with
EC-gate status 3, followed by owner-initiated termination. The Down-input report
and WGI invalid-output path remain hypotheses about the cause. Task #75 now
binds candidate3's WGI module to its original producer and the exact Wine source
subset; the [WGI investigation](../../mydocs/tech/task_m1_75_wgi_binding.md) records
the reconstruction result and its retained-input limits. This establishes module
correspondence, not a natural call or the cause of the D36 refusal.

Continue in `pear-wine/dlls/windows.gaming.input/{provider,gamepad,controller}.c`
with bounded observation of the existing call. Preserve its call count, HRESULT,
return value and output writes; determine output validity from the executed
branch without reading or initializing an unwritten structure. Distinguish
initialization from public readings and record lost/unpaired observations as
unknown. Freeze the new source and module, then assemble a new development
candidate and satisfy its affected admission/controls before a separately
authorized game run. Never replace the original candidate or reuse its receipts
as results for changed bytes.

EC gate/lifecycle changes belong in
`pear-fex/Source/Windows/ARM64EC/Module.cpp` and
`Source/Windows/Common/PearFEXMemory.cpp` only when the observed evidence supports
them. Keep existing capacity, ownership and failure guards; an occupied-slot
count is not a reclamation proof.

The historical selected-candidate game run plan was 2,440,587,694 additional
bytes (about 2.44 GB) plus a 6 GiB reserve: 8,883,038,638 free bytes in total,
without assumed clone savings. This is not the budget for a new source build,
candidate or its required controls. Remeasure that complete next-task peak,
then re-admit all inputs, predecessor resources, the live lease/deadline and
current authority immediately before execution. Inspection is not a grant.
Retain human-only input, terminal/expiry priority and the independent release
request above after either success or failure.

Keep the exact retained packs, builder paths, original D36 and candidate2 reuse
evidence, candidate3 and private state. Recover the development pointer by
selecting and inspecting a previously valid prepared record; do not import the
old selection schema or rewrite its receipts. Git checkout and the separate
3,634-byte header restore do not prove full runtime/toolchain/prefix recovery.

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
