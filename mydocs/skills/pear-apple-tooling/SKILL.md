---
name: pear-apple-tooling
description: Select pinned Apple technical guidance for approved Pear Metal validation, GPU capture/debugging, rendering defects, drawable presentation or metal-cpp lifetime work. Use for those engineering tasks, not general roadmap or host-only work.
---

# Pear Apple technical guidance

## Trigger and preconditions

Use when the approved task needs the expertise above. Follow Pear's Issue, context, approval and report rules; this skill supplies technical references, not a second project workflow.

## Procedure

1. Read the [public tooling guide](../../../docs/development/apple-tooling.md) and [pinned source inventory](references/upstream.json). Select only the expert relevant to the concrete task and state its name and purpose.
2. Read that original `SKILL.md` at the recorded revision and any references needed by the task. Resolve relative links against their containing file at the same revision. The guide describes reading raw sources when the plugin is absent. Record a deliberate source update instead of silently substituting `main` or a different installed version.
3. Check actual tool/platform prerequisites before invoking a command. Record unavailable tools and choose a documented, applicable alternative when possible. If essential source or execution access is missing, retain the limitation; do not claim the expert was applied or the check passed.
4. Reconcile examples with the actual SDK/header/API contract before implementation, especially metal-cpp ownership and autorelease-pool lifetime. Record conflicts and the chosen evidence.

## Verification

Record the selected source revision/plugin version, what was read, installed/tool availability, actual commands and settings, input identity, result and sanitized evidence. Separate correctness diagnostics from performance measurements and source inspection from execution. Mark unperformed or unsupported checks explicitly.

## Never do

- Do not start Apple's `porting-assistant`, `porting-discover`, `porting-validate` or `.porting` lifecycle through this router.
- Do not infer approval for global plugin installation, OS/toolchain changes, security changes, optional shader experiments or raw capture publication. Follow the existing task authorization.
- Do not treat a source pin, a native launcher or a tool's availability as a qualified Rosetta-free game result.

## Invocation

- Codex: `$pear-apple-tooling` or the skills menu.
- Claude Code: `/pear-apple-tooling`.
