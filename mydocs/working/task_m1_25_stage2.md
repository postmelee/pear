# Task #25 - Stage 2 Report

GitHub Issue: [#25](https://github.com/postmelee/pear/issues/25)
Implementation plan: [task_m1_25_impl.md](../plans/task_m1_25_impl.md)
Stage: 2 - Scoped rules and pinned Apple technical guidance
Date: September 28, 2026
Work branch: `codex/task25`

## Stage Purpose

Connect approved tasks to relevant repository rules and Apple technical expertise without changing runtime contracts or adding another project workflow. The maintainer explicitly approved the Stage 1 report and continuation to Stage 2 in this thread. This stage implements the approved document-location judgment and preserves later approval gates.

## Artifacts

| File | Change Summary |
|---|---|
| `AGENTS.md` | 78 lines; explicit context discovery, concise persistent rules and relevant-area routing; full framework attribution preserved |
| `host/AGENTS.md` | 11 lines; native evidence, authorization, owned-process diagnostics and upstream boundaries |
| `tests/AGENTS.md` | 10 lines; redistributable fixtures, meaningful rejection cases and truthful execution/skip limits |
| `docs/AGENTS.md` | 11 lines; approved locations, single roadmap, source provenance and evidence authority |
| `docs/development/apple-tooling.md` | 67 lines; public task selection, pinned source reading, availability, alternatives, lifecycle and API-contract boundaries |
| `docs/README.md` | One link to the new development guide |
| `mydocs/skills/pear-apple-tooling/SKILL.md` | 32 lines; narrow task trigger and technical-reference routing |
| `mydocs/skills/pear-apple-tooling/references/upstream.json` | 84 lines; revision/version, six expert paths, five relative references and two sourced CLI requirements |
| Task/implementation plans and `mydocs/orders/20260928.md` | Stage 1 approval and Stage 2 completion; only #25 board row updated |
| `mydocs/working/task_m1_25_stage2.md` | This report and the next-stage approval request |

## Body Change Scope / Lossless Preservation

The root rules are deliberately reorganized, not a lossless prose copy. They retain explicit same-thread stage approval, source-change authorization, Issue ownership, document-location approval, English repository output, preservation of other workers, requester-controlled work duration, Codex naming, master integration/release policy and existing M1/R1 identities. The obsolete automatic-loading claim and deferred documentation-root choice are replaced by context lookup and the Stage 1 selection of `docs/`.

The framework release/commit attribution and entire MIT notice match the prior version exactly. Both skill discovery symlinks retain their original targets and Git mode `120000`. The framework version record, historical #22 inventory, runtime source, tests, contracts, other workers' checkouts and untracked `analysis/` and `research/` are untouched. No empty `runtime/`, `profiles/`, `manager/` or `.porting` directory was created.

Reviewed the shared-skill folder rules, relevant template/manual references and workflow call-display guidance. The Pear entrypoint includes the required trigger, preconditions, procedure, verification, prohibitions and invocation information. Existing README has no framework “Core SKILL Details” table to extend. Root routing and the docs index supply the new entrypoints; no framework manual/index correction was necessary. This is a Pear customization, not a framework version upgrade.

## Verification Results

### Planned commands

Ran the Stage 2 command block from the implementation plan verbatim under `bash -e`:

```sh
PEAR_TASK25_VALIDATION_ENV=$(mktemp -d /private/tmp/pear-task25-validation.XXXXXX)
python3 -m venv "$PEAR_TASK25_VALIDATION_ENV"
"$PEAR_TASK25_VALIDATION_ENV/bin/python" -m pip install --disable-pip-version-check --only-binary=:all: 'PyYAML==6.0.3'
"$PEAR_TASK25_VALIDATION_ENV/bin/python" "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" mydocs/skills/pear-apple-tooling
python3 -m json.tool mydocs/skills/pear-apple-tooling/references/upstream.json
python3 - <<'PY'
from pathlib import Path
root = Path.cwd()
for name in ['.agents/skills', '.claude/skills']:
    link = root / name
    assert link.is_symlink() and link.resolve() == root / 'mydocs/skills', name
print('PASS: both skill discovery links preserved')
PY
git ls-files -s .agents/skills .claude/skills
sw_vers -productVersion
xcodebuild -version
python3 - <<'PY'
import shutil
for name in ['gpucapture', 'gpudebug']:
    print(name + ': ' + (shutil.which(name) or 'unavailable on PATH; not executed'))
PY
git diff --check
```

| Check | Actual result |
|---|---|
| Isolated authoring dependency | Created `/private/tmp/pear-task25-validation.N60riY`; installed and rechecked PyYAML `6.0.3` using its CPython 3.14 ARM64 wheel; no global/project dependency added |
| skill-creator validator | `Skill is valid!` |
| JSON formatting/parsing | Passed |
| Discovery links | Both resolved to this worktree's `mydocs/skills`; both tracked as mode `120000`, blob `d1fe2f5ad8f296c8dd1932d69a837a1bc5032415` |
| Local environment | macOS `26.5.2`; Xcode `26.6`, build `17F113` |
| GPU CLI discovery | Both `gpucapture` and `gpudebug`: `unavailable on PATH; not executed` |
| Whitespace | Initial block exited 2 at `git diff --check` because `AGENTS.md` had an extra blank line at EOF. Removed that line and reran the same check: exit 0. Earlier checks in the block had passed. |

The full initial output is retained locally in `/private/tmp/pear-task25-stage2/verification.log`; the table records its results and the resolved failure. The temporary environment remains available for the next stage if useful. The authoring validator does not become a prerequisite for human contributions.

### Source verification

Read the following 13 files from Apple's official repository at revision `4f42344c90be22112f46becc3fb9687f423f2f88`. The manifest reports `game-porting-skills` version `1.0.0-beta.1`. A live `git ls-remote https://github.com/apple/game-porting-toolkit.git refs/heads/main` recheck returned the same revision. No moving source reference was substituted for the reviewed pin.

| Original file at reviewed revision | Git blob SHA | Result |
|---|---|---|
| [README.md](https://github.com/apple/game-porting-toolkit/blob/4f42344c90be22112f46becc3fb9687f423f2f88/README.md) | `e7d73d9dce149001fcb1a8de0999bd85d478d026` | Read and checked |
| [game-porting-skills/.codex-plugin/plugin.json](https://github.com/apple/game-porting-toolkit/blob/4f42344c90be22112f46becc3fb9687f423f2f88/game-porting-skills/.codex-plugin/plugin.json) | `beedf5c929a3b21740f08e749326b6256a7d05a4` | Read and checked |
| [game-porting-skills/skills/using-metal-validation/SKILL.md](https://github.com/apple/game-porting-toolkit/blob/4f42344c90be22112f46becc3fb9687f423f2f88/game-porting-skills/skills/using-metal-validation/SKILL.md) | `7815a2039790cba346b9d8f206ac55fb619b6f15` | Read and checked |
| [game-porting-skills/skills/using-gpucapture/SKILL.md](https://github.com/apple/game-porting-toolkit/blob/4f42344c90be22112f46becc3fb9687f423f2f88/game-porting-skills/skills/using-gpucapture/SKILL.md) | `7d3e008ea131b6db83bd095ecc7115429263f13e` | Read and checked |
| [game-porting-skills/skills/using-gpudebug/SKILL.md](https://github.com/apple/game-porting-toolkit/blob/4f42344c90be22112f46becc3fb9687f423f2f88/game-porting-skills/skills/using-gpudebug/SKILL.md) | `fecec6751f56050a401be89143a204a479a937a0` | Read and checked |
| [game-porting-skills/skills/debugging-rendering-issues/SKILL.md](https://github.com/apple/game-porting-toolkit/blob/4f42344c90be22112f46becc3fb9687f423f2f88/game-porting-skills/skills/debugging-rendering-issues/SKILL.md) | `85f6c54cbfc9ac2bd3bc18c7784664b297bf44d2` | Read and checked |
| [game-porting-skills/skills/presenting-metal-drawables/SKILL.md](https://github.com/apple/game-porting-toolkit/blob/4f42344c90be22112f46becc3fb9687f423f2f88/game-porting-skills/skills/presenting-metal-drawables/SKILL.md) | `744819c8870fba5d0209f01815ac75edf9d6c3a4` | Read and checked |
| [game-porting-skills/skills/managing-metal-cpp-lifetimes/SKILL.md](https://github.com/apple/game-porting-toolkit/blob/4f42344c90be22112f46becc3fb9687f423f2f88/game-porting-skills/skills/managing-metal-cpp-lifetimes/SKILL.md) | `7b7198fa5a4e26eec9b76a0b782bced3ae9fb96e` | Read and checked |
| [game-porting-skills/skills/debugging-rendering-issues/references/tier-1-instant-checks.md](https://github.com/apple/game-porting-toolkit/blob/4f42344c90be22112f46becc3fb9687f423f2f88/game-porting-skills/skills/debugging-rendering-issues/references/tier-1-instant-checks.md) | `5506f95c52b50e2022aaab18cb36ab25d13e50a7` | Read and checked |
| [game-porting-skills/skills/debugging-rendering-issues/references/tier-2-state-inspection.md](https://github.com/apple/game-porting-toolkit/blob/4f42344c90be22112f46becc3fb9687f423f2f88/game-porting-skills/skills/debugging-rendering-issues/references/tier-2-state-inspection.md) | `f38805eeccde829bc41a1c27a2bcc52dfba4122e` | Read and checked |
| [game-porting-skills/skills/debugging-rendering-issues/references/tier-3-data-inspection.md](https://github.com/apple/game-porting-toolkit/blob/4f42344c90be22112f46becc3fb9687f423f2f88/game-porting-skills/skills/debugging-rendering-issues/references/tier-3-data-inspection.md) | `331c0d9ef801ebeb8546982c8b2f0e4731c3d90c` | Read and checked |
| [game-porting-skills/skills/presenting-metal-drawables/references/frame-pacing.md](https://github.com/apple/game-porting-toolkit/blob/4f42344c90be22112f46becc3fb9687f423f2f88/game-porting-skills/skills/presenting-metal-drawables/references/frame-pacing.md) | `aef78d075488be7f98f97b7de8e411d8711bf80d` | Read and checked |
| [game-porting-skills/skills/presenting-metal-drawables/references/hdr-colorspace.md](https://github.com/apple/game-porting-toolkit/blob/4f42344c90be22112f46becc3fb9687f423f2f88/game-porting-skills/skills/presenting-metal-drawables/references/hdr-colorspace.md) | `2bcd061a301cd1c1715b83ed7d555d02636c47c2` | Read and checked |

The six routes match the original skill purposes. Capture/debug minimum macOS 27 comes from each corresponding skill's requirements; README's Xcode 27 requirement concerns its agent/MCP workflow. Neither establishes Pear's user minimum OS. Reference paths resolve from the skill directory; nested relative links resolve from the containing reference at the same revision. The five listed references are the selected direct inventory, not a claim to list every transitive upstream file.

The guide's optional installation commands match Apple's pinned README. They were not executed. No Apple expert skill was exposed in the session or found in the inspected Codex skill/cache directories. The source files were inspected directly; a plugin installation or execution result is not claimed. Read-only `xcrun --find metal` and `xcrun --find xctrace` located Xcode tools; capture/debug alternatives are documented candidates, not successful capture evidence.

Additional primary-source review confirmed the `.porting` lifecycle in [porting-methodology](https://github.com/apple/game-porting-toolkit/blob/4f42344c90be22112f46becc3fb9687f423f2f88/game-porting-skills/skills/porting-methodology/SKILL.md). The lifetime skill's reusable-pool example conflicts with [Foundation drain semantics](https://developer.apple.com/documentation/foundation/nsautoreleasepool/drain) and the [metal-cpp forwarding header](https://github.com/apple/metal-cpp/blob/27c4382b7151d55a51692cdcb27aaa98752240de/Foundation/NSAutoreleasePool.hpp). Apple's pinned tree records that exact metal-cpp submodule commit. The guide records the conflict and directs implementation to the actual SDK/header/API contract instead of copying the example.

### Local and independent review

A temporary read-only check passed for 47 simple inline local link targets in the seven Stage 2 Markdown guidance files. It also checked unchanged attribution/discovery/version records, absent future implementation and `.porting` directories, and agreement between the six-skill/five-reference metadata URLs and the 13 fetched source records. These new links introduce no heading fragments. An independent reviewer confirmed rule preservation, approved scope and internal source URL/path consistency with no actionable findings.

A separate read-only behavioral evaluation used a black-frame diagnosis request and an unrelated board-wording request. It selected rendering diagnosis/Tier 1, validation and capture guidance, with trace inspection conditional on a captured trace; retrieved the pinned originals; checked the actual host and local MetalValidation manual; and selected Xcode alternatives without claiming successful attachment or capture. It identified the missing target process/reproduction input and excluded the router from the board-only task. Initial web-cache/DNS lookup failures were resolved by authorized read-only network access. This observed routing result supports usability, not a general proof of agent behavior.

### Verification limitations

No GPU capture, validation execution, trace replay, rendering test, performance run, game launch, Steam flow, signing change or runtime qualification occurred. Missing CLI tools remain unavailable; their absence is not a failed Stage 2 requirement because this stage requires source and availability verification only. No plugin, marketplace, OS or toolchain configuration changed.

Skill-format and static link/source checks do not prove an agent will follow the rules or that remote guidance is technically correct. The temporary link check covers simple inline local targets, not all Markdown forms or anchors. Maintained offline checks and rejection fixtures belong to Stage 3; no new CI result is claimed here.

## Residual Risks

- Tool/platform availability and upstream guidance may change; recheck actual task prerequisites and record deliberate pin changes.
- Apple's lifetime guidance contains a reviewed conflict. Future implementation must reconcile its actual API contract rather than assume every pinned example is safe.
- GPU evidence collection remains unperformed on this host; documented alternatives need task-specific authorization and successful execution before any result claim.
- #3 may later edit the documentation index and architecture. Preserve its work and recheck the integration base before publication.

## Impact on Next Stage

Stage 3 should add the approved five template extensions, offline governance checker, meaningful fixture tests and documentation CI. The checker must validate routing/metadata relationships while preserving its stated Markdown and remote-content limitations. It must not execute GPU tools, invent a runtime contract or impose agent tooling on human contributors.

## Approval Request

Review the Stage 2 artifacts and verification results, then explicitly approve proceeding to Stage 3. This report does not authorize Stage 3, PR publication or merge by itself.
