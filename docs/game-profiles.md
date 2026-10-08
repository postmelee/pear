# Game profiles and evidence

The manager reads versioned profiles independently of game identity. [Fixture A](../profiles/fixtures/a.json) and [fixture B](../profiles/fixtures/b.json) exercise the same native consumer with different arguments, settings and save roots. The [Megabonk profile](../profiles/megabonk/profile.json) is a **research record**, not a supported game configuration. See the [CLI guide](development/runtime-supervisor.md) for the implemented fixture workflow and [runtime contracts](runtime-contracts.md) for qualification policy.

## Profile fields and writable state

Use the existing `game_profile` schema, with explicit `schema_version` and `record_context`. Both versions retain store/App ID, a `guest_relative` executable, bounded argument/environment arrays, typed operations, required checks/processes and relative save declarations. The native host entry is separately selected by the artifact and launch request; the profile's guest executable is not a host path to execute directly.

Version 2 adds nullable unselected runtime family/renderer, save-inventory knowledge, path observations, provenance and feature observations. Its [schema](../runtime/contracts/v2/game-profile.schema.json) is closed; arbitrary scripts, downloads or new executable fields are rejected. Mixing versions in a reachable record graph is rejected. V1 records retain their original meaning.

| Field | Consumer meaning |
|---|---|
| `game_build`, `compatibility_family`, `renderer` | `null` means not established; it cannot authorize an eligible runtime launch. Historical versions belong in provenance when they do not identify the current candidate. |
| `save_inventory_status` | `unknown` requires a reason and empty `save_paths`. Empty inventory in this state does not mean the game has no saves. |
| `save_paths` | Explicit relative paths beneath an independently resolved saves root. An observation or guessed Wine user directory does not create a writable mapping. |
| `path_observations` | An unknown observation has `path: null`; an observed path requires typed relative location and matching evidence. Historical candidate strings in explanatory text grant no file access. |
| `provenance` | Credential-free HTTPS source, review date and bounded scope/detail. A citation records where a claim came from; it is not an execution grant. |
| `features` | Preserve `untested`, `unknown`, `unsupported`, `failed` and `passed`. Results needing evidence cannot be asserted with empty references; even a valid feature result is not a qualification overlay. |
| `required_checks`, `required_processes` | Declared requirements, supplemented by independent policy and actual run scope. A research list is not a complete discovery of Steam helpers or loaded modules. |

The implemented v2 setting subset is one boolean `fixture_flag` at `prefix/config/options.json`. Preparation changes only that JSON key and preserves other keys and all save bytes. V1 nonempty operations, `dxmt_log_level`, other paths and duplicate operations are currently refused. A name appearing in the schema does not mean an executor supports it. Manager-owned `WINEPREFIX` and fixture descriptors cannot be overridden by submitted environment entries.

A prepared context binds exact profile/request/cache identities, runtime family and declared roots to a caller-selected lower-case game/library context ID. Profile edits change byte identity and invalidate the old binding; sharing a family name does not authorize in-place migration. Use fresh state or explicitly select a previously clean compatible context as described in the CLI guide.

## Megabonk: recorded facts and open evidence

Review date: October 9, 2026. The official [Steam listing](https://store.steampowered.com/app/3405340/Megabonk/) identifies App ID `3405340`. The checked-in profile names `Megabonk.exe` from the [September 27 read-only file inventory](research/graphics-and-game-integration.md#local-file-architecture-inventory). Neither source establishes the currently installed game bytes on a user's machine.

| Item | Profile treatment and evidence boundary |
|---|---|
| Historical game identity | [Local evidence](research/local-evidence.md) records game 1.0.69, Windows depot 3405342 and manifest 446680890915713051 on September 27, 2026. These remain dated provenance. Current App BuildID is unknown and `game_build` is null. |
| Runtime and Steam | The earlier Wine 11.0 / DXMT 0.80 / Whisky Libraries 3.1.1 experiment used Rosetta. Current selected runtime family, renderer, Steam client build and complete helper coverage are unestablished. No runtime lock/artifact or current Steam identity is invented by the profile. |
| Experimental arguments | Prior script inspection recorded `-force-d3d11`, window/size and a local Unity log argument. They are hints only; `arguments` and `environment` remain empty instead of becoming unverified native defaults. |
| Configuration hint | `AppData/LocalLow/Ved/Megabonk/Saves/LocalDir/config.json` was a candidate under an experimentally chosen Wine user. Current existence, actual user mapping, write semantics and native applicability are unverified. The structured settings path remains unknown/null and `operations` is empty. |
| Saves | Complete save inventory, persistence and save/relaunch remain unverified. `save_paths` is empty with an explicit unknown status. No personal save data or authenticated prefix is inspected by this profile. |
| Features | Rosetta independence, Steam initialization on the candidate, 20-minute gameplay, input, audio, save/relaunch, overlay, cloud, achievements, controller and Discord integration remain untested for this profile. Store labels or old Rosetta observations do not mark them passed. |

The profile's revision-pinned provenance links preserve the exact repository sources used, including the sanitized planning note for script hints. The underlying private experiment is not redistributed or represented as independently reproduced public evidence.

Normal official Steam launch and legitimate ownership remain required downstream. Valve's [Steamworks initialization documentation](https://partner.steamgames.com/doc/sdk/api#initialization_and_shutdown), reviewed October 9, 2026, describes `steam_appid.txt` as a development mechanism and says not to ship it. The researched profile supplies no such shortcut or ownership bypass.

## Inspect without executing

After the CLI guide's build/setup, from the repository's physical root:

```sh
PEAR_REPO="$(pwd -P)"
PEAR_MANAGER="$PEAR_REPO/.build/task9/stage4/bin/pear-manager"
```

<!-- pear-profile-inspect -->
```sh
.build/task9/venv/bin/python -B tests/contracts/validate_v2.py --bundle-root "$PEAR_REPO" --entry profiles/megabonk/profile.json --context research --purpose inspect
"$PEAR_MANAGER" inspect --bundle-root "$PEAR_REPO" --entry profiles/megabonk/profile.json --context research
```

Both consumers should report a valid, inspectable research record with `evaluation_only: true`. Inspection does not make the record eligible for `qualification_run` or `supported_launch`. New runtime use needs reviewed current game/Steam identities, a selected source-built artifact, exact independent policy, actual host/signing authorization, complete save/user mappings and owned process/module observation. Supported launch additionally needs matching game qualification. The current native manager refuses real-runtime activation even for complete synthetic candidate declarations.

Profile changes should be checked through both the v2 oracle and native consumer. The executable profile tests also exercise missing prerequisites, invalid knowledge/evidence and actual activation refusal without spawning Steam or a game:

```sh
PEAR_MANAGER_BUILD=.build/task9/stage4 .build/task9/venv/bin/python -B -m unittest discover -s tests/profiles -p 'test_*.py'
```
