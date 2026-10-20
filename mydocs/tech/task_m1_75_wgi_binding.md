# Task #75 — WGI source-to-development-PE binding

Tracking: [#75](https://github.com/postmelee/pear/issues/75).
Review/build scope: the selected `windows.gaming.input.dll` and its bounded
retained-input module recipe. No Wine/guest/game execution, activation, installation
or signing is part of this investigation.

## Established producer and source relationship

Candidate3, runtime12, the historical Task5 Wine installed DLL and its original
object-tree DLL are whole-file equal: SHA-256
`ee23564869279df291d84b80029f196137117870eb65830fe47e8334073332d2`,
1,114,112 bytes. The outer PE machine is ARM64 (`0xaa64`); the original link
constructs ARM64X from AArch64 and ARM64EC objects. A static format is not a
claim about any running host process or library.

The original build receipt records fresh construction with
`source_only_reuse=true`, `previous_objects_reused=false`, and successful
configure/make/install commands. The initial collection failure and later
inventory finalization remain separate records; finalization did not recompile.
The original source manifest SHA-256 is
`fc7c9c9ebb7a4201a67c7be9f5131c7aa6316347b734708b758269d1f18b95a7`;
the installed manifest is
`0f106a74b9f13ad109521f69dd5500cfb4aa102c3d3dac0c2fd0ab7555fc79a5`.
A retained 30-record provenance chain connects the candidate to that build.

All 173 source/header prerequisites in the recorded module closure match the
historical source inventory and these exact Wine Git trees:

| Role | Commit |
|---|---|
| Public upstream base | `4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf` |
| Selected split-runtime build source | `1b76db6902345388c589ba3909b22badf751dfd5` |
| Final Task56 source/documentation tip | `007291b81de386fd8886770c33b5d385c078635d` |

This WGI subset has no Pear delta relative to that upstream pin. It does not
claim equality of whole source trees or reattribute retained lower-layer objects
of other Wine modules to a single current tree.

## Inputs and procedure

The generated top-level Makefile and original compiler log identify 65 actions:
36 header/resource generation steps, 28 compilations (14 C units for each
architecture), and one ARM64X link. The source `Makefile.in`, module spec/IDL,
source and headers are tied to those actions. The forwarding Makefile stub alone
is insufficient. Task56's selected Wine reconstruction recipe did not build WGI.

The static closure comprises 252 existing files and 16,387,120 logical bytes:
173 source/header files, 35 generated headers, one registration resource,
28 objects, 11 libraries, three native helper tools and the final DLL. The
281-file audit/reconstruction pack also retains the exact Makefile/configuration,
logs and original toolchain receipts. Original WIDL and winegcc differ from the
copies in Task56's selected Wine pack; those copies are not interchangeable.

Original compilation uses the recorded `aarch64-windows` / `arm64ec-windows`
targets, definitions, include order and flags, with no optimization flag in the
logged commands. Preserve relative `../source` spellings, object/library order
and exact helper/toolchain inputs. Only the reviewed vanished tool-root alias
mapping and explicit diagnostics may differ. Existing compiled libraries remain
explicit lower-layer inputs; this is not a full clean Wine/toolchain rebuild.

## Fresh module reconstruction result

The common-runtime adapter `pear_runtime/recipes/wgi.py` reuses the existing
build executor, Wine PE/COFF comparison and dependency/trace checks. Existing
`build.py` and `recipes/wine.py` are unchanged. No Wine module source was edited.
The public recipe SHA-256 is
`16b35a33816e5846f3dbd46620e066a0b9a557d3f77aacb839042a975dd9141f`;
the separately recovered private historical action plan is
`64a3fe23165dfae82badcec179771aec743f16bf20806170bd8d8d8c85563fd1`.
The executed adapter SHA-256 is
`6b621c2a16fa113a56d751910710886f194b5507a27723f91fcdfbc602a2df7e`.
These tool identities are separate from the selected runtime tool `6f0202b`.

The first attempt completed its retained-object control link but failed the
strict tool-trace gate: Wine printed its known child executable as
`./tools/winebuild/winebuild`. That failed receipt and all raw output survive.
The WGI-only adapter now binds precisely that executable field against the
recorded command directory into separately hashed derived logs. It rejects
other relative child paths and leaves original logs, executed argv and the
shared parser unchanged. Pure replay of the actual failed trace confirmed all
39 required operands, 41 actual linker reads and three tools before retry.

The fresh second attempt passed all 66 commands: the extra retained-object
control link, the 36 original generation actions, 28 original compilation
actions and final selected link. All 36 generated files are byte-identical.
All 28 fresh raw objects match after deriving only their four-byte COFF
timestamp for the working link operands; raw objects are separately retained.
Twenty-eight compiler depfiles admit 133 unique actual paths. Both strict link
traces admit all 39 required operands, actual reads and child tools. All 9,152
declared inputs are validated, and all 281 original pack-source files and
executed builder sources remain unchanged.

| Artifact | Raw SHA-256 | Comparison to retained DLL |
|---|---|---|
| Retained WGI | `ee23564869279df291d84b80029f196137117870eb65830fe47e8334073332d2` | Original |
| Fresh control link | `eff53cae7e9f688edec2657786dff35e7b5ae4dca6ea2037ae0880bfe5f3fc4e` | Only COFF/debug timestamp fields differ |
| Fresh source reconstruction | `2399c75b0cdc5a4c95249502abea9e9afe5b1003296d1a22172169d79dfcfb0e` | Only COFF/debug timestamp fields differ |

Both PEs remain 1,114,112 bytes. Only the four-byte COFF timestamp at file offset
128 and four-byte debug timestamp at 531,392 are derived in memory; every other
byte, including RSDS, code, imports, unwind and ARM64X data, matches. The derived
whole-file digest equals the retained DLL. Raw hashes do not match and are not
reported as byte-for-byte reproduction. No raw file is rewritten.

The successful result is joined to CLI exit 0, `status=passed`,
`wgi_finalization_complete=true`, the exact released operation and external
post-release accounting. `runtime_eligible=false` and `game_qualified=false`
remain explicit. The unchanged executor's historical `task56_component_build`
envelope does not turn this into a Task56 candidate or qualification result.

### Reproduce or extend

From the Task75 common-runtime source, use the exact recipe, private pack manifest
and bindings; the existing recipe README documents root roles and rejection
rules. A fresh output directory must not exist:

```sh
python3 -B -m pear_runtime.recipes.wgi \
  --recipe recipes/wine/wgi-v1.json \
  --bindings "$PRIVATE_WGI_BINDINGS" --output "$FRESH_WGI_OUTPUT"
```

The pack, attempts and evidence roots must be separate canonical directories and
all retained attempts count against the declared budget. Bind the exact Wine
checkout, LLVM-MinGW installation and host tools; unavailable or mismatched
inputs fail before compilation. Rebinding requires byte/mode-matched inputs,
not a fallback search into old worktrees. The module is not installed, signed or
selected by this procedure. Preserve failed output and choose another fresh
output root after a reviewed correction; do not overwrite receipts.

This sealed recipe reconstructs the unchanged baseline only. A later source
change needs a separately reviewed recipe version/seal, intentional-difference
checks and a new candidate/controls. Do not weaken this baseline equality gate
to admit an instrumentation DLL.

### Validation timing

The second external build interval was 15.576 seconds, from
2026-10-20T15:08:04.121753Z to 15:08:19.698199Z; its child interval was
15.462 seconds. Python was 3.13.5. Records contain both wall and monotonic
boundaries for admission, preparation, lock acquisition, generation, compilation,
linking, comparison and final validation. This is a build-only diagnostic
interval, not frozen-source-to-user-response latency or a performance baseline.
No window, manual input, native fixture, guest or game was executed.

## Static function observations and remaining causal limits

Both architecture variants retain symbols for `wine_provider_get_State`,
`gamepad_GetCurrentReading` and `raw_controller_GetCurrentReading`. The inspected
provider returns success early when `GetDeviceState` fails, before populating the
output; the caller paths require observation of actual HRESULT/output handling.
A source path, a symbol or a reproducible DLL is not evidence that D36 called it.

The historical outcome remains responsive-menu/loading progression followed by
EC-gate status 3 and owner-initiated termination. The reported Down input and WGI
invalid-output path remain hypotheses, not a verified root cause or crash cause.

## Next implementation and observation

The next editable owner is `pear-wine/dlls/windows.gaming.input/`: observe the
existing single `GetDeviceState` invocation in `provider.c`, together with
public reading paths in `gamepad.c` and `controller.c`. Distinguish the existing
initialization call from public readings. Record underlying and returned HRESULT,
whether complete output writes occurred, and whether caller conversion was
reached. Derive write validity from the branch; never read/hash unwritten output
or initialize it as part of observation. Preserve call count, arguments, return
value, error state, output writes and ordering. Add no polling, retry, input
injection or speculative behavior repair.

Use bounded opt-in diagnostic records with operation/PID/TID and per-call
correlation; loss, overflow or unpaired records mean unknown. Reuse Wine's
diagnostic facilities and existing component tests (`tests/input.c`). Verify
exactly one underlying call across success/failure, both public APIs,
initialization and trace loss before any game request.

Common runtime owns the new module recipe, assembly and input/control admission;
Pear owns the isolated selection and human-only game policy. Freeze new source,
new PE and new candidate records. The current game policy requires fifteen
operations for the exact selected runtime/assembly: seven D36, seven
native/bootstrap and presentation frames. Changed bytes do not inherit old
receipts; any narrower reuse needs a separately reviewed admission change.
Recalculate complete build/candidate/control/game storage before that next task.

Only later causal evidence would justify FEX changes in
`Source/Windows/ARM64EC/Module.cpp` or `Source/Windows/Common/PearFEXMemory.cpp`.
Keep lifetime, ownership, capacity and failure guards. Occupied bindings alone
do not establish liveness or safe reclamation.

Game execution needs a separate approved task with current owned-input admission,
lease/authority, manual confirmation and independent release. Follow the
[current developer route](../../docs/development/rosetta-free.md#continue-the-developer-megabonk-investigation).
Selecting a prior prepared record recovers only development selection metadata;
it does not restore payloads, private state or execution authorization.

## Storage and retention

The admitted plan is 128 MiB additional module storage plus a separate 6 GiB
reserve, requiring at least 6,576,668,672 free bytes before compilation. The pack
is 57,220,780 logical / 57,802,752 stat-allocated bytes; the 782,265,656-byte LLVM
tree is reused read-only. No runtime/game/prefix copy is required.

Before retry, the retained first attempt plus a full fresh-output/final-record/
diagnostic allowance forecast 126,810,798 bytes, below the 134,217,728-byte
aggregate ceiling. Actual post-release usage was 108,280,808 logical /
110,501,888 stat-allocated bytes for both attempts, pack and evidence at the
external observation. Final handoff accounting includes later audit records.
Free space was 17,810,632,704 before and 17,779,208,192 after the retry; concurrent
work prevents attributing that filesystem delta solely to this task. No cleanup
or recovered-space claim is made.

Retain original and fresh raw outputs, parsed differences, exact input/action
plans and private bindings. Do not overwrite frozen hashes, rewrite receipts or
release historical source/tool roots under this investigation. The absent
494-byte historical frame request remains restore-required with its exact
retained recovery copy; restoring it for a later game task requires that task's
current admission. This source/PE investigation does not need it.

## Evidence and claim boundary

The successful private build receipt has SHA-256
`8a8f24211bb990e81d881409de870b5ca59d17c0bdc94e61fc1a6b6874c82ff2`
(3,857,433 bytes). The original artifact/tool/source proof is
`d1186ea7ba6572e31064a0334ec27e614bc85b1bf5108d4ccee8f214b8df05ec`,
the runtime provenance chain is
`58356c1284be25e4e188b49d70b9054f2ee1e6506c5c01a055ba887bb82d3647`,
and the input inventory is
`340d1024be29d148243bf51df89fc5d5496dce989265b2e5538051d6ca704077`.
The [Stage3 report](../working/task_m1_75_stage3.md) records independent review,
portable rejection tests, final source/notice/privacy checks and durable evidence
identities. The [final report](../report/task_m1_75_report.md) records exact
component commits and retention handoff.

Private operational paths, raw selectors and game data are not exported here.
Source review, reconstruction, fixtures and game qualification remain distinct.
