# Apple technical references for Pear

Use selected Apple Game Porting Toolkit expert guidance for an approved graphics or diagnostics task. Pear's [Phase 1](../delivery-plan.md) retains the Wine/FEX/DXMT direction and complete required-host Rosetta-independence gate. Reading skills or installing their plugin does not supply that runtime. Standalone Metal Shader Converter (MSC) and D3DMetal experiments remain deferred unless a concrete blocker or separately approved implementation needs them.

Contributors can read these references without an AI tool or paid service. Follow the [contribution guide](../contributing.md) and the approved Issue and plan.

## Reviewed sources and task selection

Reviewed on September 28, 2026: Apple [README](https://github.com/apple/game-porting-toolkit/blob/4f42344c90be22112f46becc3fb9687f423f2f88/README.md), revision `4f42344c90be22112f46becc3fb9687f423f2f88`, and [plugin manifest](https://github.com/apple/game-porting-toolkit/blob/4f42344c90be22112f46becc3fb9687f423f2f88/game-porting-skills/.codex-plugin/plugin.json), version `1.0.0-beta.1`. This is the skills-plugin version, not an evaluation-environment or compiler version. The [source inventory](../../mydocs/skills/pear-apple-tooling/references/upstream.json) records the six expert files, five selected relative references and source-backed CLI requirements. The [Pear routing skill](../../mydocs/skills/pear-apple-tooling/SKILL.md) connects agent work to this guide.

| Approved work | Expert reference | Read additionally when needed |
|---|---|---|
| Metal API or shader validation | [using-metal-validation](https://github.com/apple/game-porting-toolkit/blob/4f42344c90be22112f46becc3fb9687f423f2f88/game-porting-skills/skills/using-metal-validation/SKILL.md) | Local `man MetalValidation`; verify settings reach the process that creates the Metal device |
| Create a GPU trace | [using-gpucapture](https://github.com/apple/game-porting-toolkit/blob/4f42344c90be22112f46becc3fb9687f423f2f88/game-porting-skills/skills/using-gpucapture/SKILL.md) | Availability and local `man gpucapture`; capture must be enabled when the target starts |
| Inspect an existing trace | [using-gpudebug](https://github.com/apple/game-porting-toolkit/blob/4f42344c90be22112f46becc3fb9687f423f2f88/game-porting-skills/skills/using-gpudebug/SKILL.md) | Availability and local `man gpudebug`; record replay or resource-fetch failures separately |
| Diagnose incorrect rendering | [debugging-rendering-issues](https://github.com/apple/game-porting-toolkit/blob/4f42344c90be22112f46becc3fb9687f423f2f88/game-porting-skills/skills/debugging-rendering-issues/SKILL.md) | Its three `references/tier-*.md` files, one tier at a time if symptom diagnosis remains unresolved |
| Drawable presentation, frame pacing or HDR | [presenting-metal-drawables](https://github.com/apple/game-porting-toolkit/blob/4f42344c90be22112f46becc3fb9687f423f2f88/game-porting-skills/skills/presenting-metal-drawables/SKILL.md) | `references/frame-pacing.md`, `references/hdr-colorspace.md` and actual SDK headers |
| metal-cpp ownership and lifetime | [managing-metal-cpp-lifetimes](https://github.com/apple/game-porting-toolkit/blob/4f42344c90be22112f46becc3fb9687f423f2f88/game-porting-skills/skills/managing-metal-cpp-lifetimes/SKILL.md) | Actual `NSSharedPtr.hpp` and `NSAutoreleasePool.hpp`; the conflict below |

Choose the relevant expert explicitly and record why it applies; use reasoned `Not applicable` for unrelated work. Apply Metal 4 or Shader Converter advice only to code using the corresponding APIs. Metal 4 presentation examples do not require replacing DXMT's existing API path, and the validation skill's application-launch example is not a verified Wine launch recipe.

## Read pinned guidance without installing a plugin

At review, no Apple expert skill was exposed in this session or found in the inspected Codex skill/cache directories. The original files were read directly. No plugin or marketplace was installed.

Open the inventory's immutable URLs, or read selected raw files without changing global configuration. For example:

```sh
pear_apple_revision=4f42344c90be22112f46becc3fb9687f423f2f88
pear_apple_raw="https://raw.githubusercontent.com/apple/game-porting-toolkit/$pear_apple_revision"
pear_apple_skill_dir=game-porting-skills/skills/debugging-rendering-issues
curl --fail --silent --show-error "$pear_apple_raw/$pear_apple_skill_dir/SKILL.md"
curl --fail --silent --show-error "$pear_apple_raw/$pear_apple_skill_dir/references/tier-1-instant-checks.md"
```

Select the file needed by the task. Inventory reference paths are relative to each skill directory; a relative link inside another reference resolves from that containing file's directory. Keep the same revision when following it, and record any additional file read. If a source cannot be retrieved, report it as unavailable; do not treat the file name as applied guidance.

Apple's pinned README documents the following optional installation commands. They affect user-wide Codex marketplace/plugin state, require separate authorization and are informational here:

```sh
codex plugin marketplace add https://github.com/apple/game-porting-toolkit
codex plugin add game-porting-skills@game-porting-toolkit
```

These commands do not pin a revision or install the missing GPU CLI tools. If installation is later approved, inspect the actual installed revision and exposed skills before claiming availability.

## Tool availability and alternatives

The September 28, 2026 inspection used macOS 26.5.2 (25F84) and Xcode 26.6 (17F113). `gpucapture` and `gpudebug` were absent from PATH; `xcrun --find metal` and `xcrun --find xctrace` resolved Xcode tools. No GPU capture, validation run or game execution was performed for this guidance.

Both selected CLI skills require macOS 27 or later. Apple's README lists Xcode 27 for its latest agent/MCP workflow. These developer-tool requirements do not determine Pear's eventual end-user minimum OS. Recheck the actual task host and local manual pages before execution.

On an older host, assess [Xcode GPU Frame Capture](https://developer.apple.com/documentation/xcode/capturing-a-metal-workload-in-xcode), [programmatic capture](https://developer.apple.com/documentation/xcode/capturing-a-metal-workload-programmatically) when source modification is authorized, and [Xcode Metal Debugger](https://developer.apple.com/documentation/xcode/analyzing-your-metal-workload) for an existing trace. Xcode Instruments/Metal System Trace can also be considered for timing analysis. These are candidates; locating a tool or reading a guide does not establish attachment permission, successful capture or rendering correctness. Keep normal macOS protections enabled.

## Evidence and technical authority

Record the selected source revision, tool/SDK versions, actual commands and settings, target process, redistributable input or private input identity, result, sanitized evidence and unverified cases. Verify validation/capture environment settings reach the intended process before Metal-device creation. Distinguish source review, tool discovery, capture, resource inspection, correct output and whole-runtime qualification.

Run correctness diagnostics separately from performance measurement. Validation and capture can change timing; comparable performance runs need matched workload, versions, settings and measurement conditions. Keep raw GPU captures and any embedded proprietary game resources private, as required by the contribution guide.

A fixed revision provides provenance, not proof that every example is correct. The reviewed lifetime skill says an autorelease pool can be reused after `drain()`. However, the [metal-cpp header pinned by that repository](https://github.com/apple/metal-cpp/blob/27c4382b7151d55a51692cdcb27aaa98752240de/Foundation/NSAutoreleasePool.hpp) forwards to Objective-C `drain`, and [Apple Foundation documentation](https://developer.apple.com/documentation/foundation/nsautoreleasepool/drain) specifies receiver deallocation under reference counting. Do not copy the reusable-pool example; resolve lifetime code against the actual headers and API contract and record the disagreement.

## Workflow and component boundaries

Pear retains its Issue, approved plan, stage approval and report workflow. Apple's [porting-methodology](https://github.com/apple/game-porting-toolkit/blob/4f42344c90be22112f46becc3fb9687f423f2f88/game-porting-skills/skills/porting-methodology/SKILL.md) introduces separate `.porting/` state, invocation gates and session transitions. Do not start that lifecycle, `porting-assistant`, `porting-discover` or `porting-validate` merely to use the expert references. A useful technical checklist can be incorporated into the approved Pear verification plan.

Review reusable upstream implementation and its existing language before adding a subsystem. Treat the Apple source repository, evaluation environment, MSC binaries and other dependencies as distinct components with their own terms and contribution policies. This guidance authorizes no binary distribution and adds no Apple runtime dependency. Retain the upstream-policy restrictions in the contribution guide, including FEX's AI-generated-code contribution restriction.
