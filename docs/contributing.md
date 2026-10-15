# Contributing to Pear

Players, testers, developers and documentation contributors can help build Pear. You do not need Codex, a paid AI service or programming experience to submit a useful request, reproduction report, test result or documentation improvement. Use the tools you choose and understand the work you submit.

Pear is under development. The [delivery plan](delivery-plan.md) defines the intended capabilities and completion criteria; [GitHub Issues](https://github.com/postmelee/pear/issues) track current ownership and progress. No general end-user release or Rosetta-free Megabonk support is established yet.

## Choose a development track

| Track | Useful work | Start here |
|---|---|---|
| Rosetta Preview | Setup, Steam launch, clear errors, recovery, packaging and accessibility | [First local build](development/getting-started.md#build-the-rosetta-preview) |
| Rosetta-free runtime | Source reconstruction, Wine/FEX host integration, DXMT and process/library evidence | [Native contribution path](development/rosetta-free.md) |
| Shared | Documentation, portable tests, reports and reviewed compatibility records | [First local checks](development/getting-started.md#run-your-first-check), [game reporting](compatibility/README.md) |

The native track is engineering work, not a second downloadable preview. Check
current Issue ownership before choosing work. Read the [Code of Conduct](CODE_OF_CONDUCT.md)
and use the [support/security routes](SUPPORT.md) for the appropriate kind of report.

## Choose a contribution

| Contribution | Useful information |
|---|---|
| Game request or usability feedback | Game/store identity, the user goal, current obstacle and relevant existing request |
| Problem report | Expected and observed behavior, reproducible steps, versions, settings and a sanitized failure summary |
| Owned-game testing | Exact configuration, test procedure, observed pass/fail/unavailable outcomes and known gaps |
| Documentation | The confusing or missing guidance, intended audience and relevant existing document |
| Profile or compatibility change | Related Issue, reusable upstream work, bounded settings/patches and evidence from the affected configuration |

Search existing Issues and PRs first. Add relevant evidence to an existing report when possible. Requests and future votes express demand; they do not guarantee support, priority or a delivery date. Use [Discussions](https://github.com/postmelee/pear/discussions) for questions, game observations and ideas; adopted work is linked to Issues. The [documentation index](README.md) explains these information boundaries.

## Propose and submit a change

1. Find or register the relevant Issue and agree the scope with the maintainer before implementation. State the intended behavior, acceptance criteria, affected areas and exclusions. Read the applicable specification and existing code before designing a replacement.
2. Review reusable upstream implementations and retain their languages unless a measured, reviewed reason supports a change. Record source revisions, license/notice obligations, contribution restrictions and the reason for reuse or new code. Keep changes focused on the agreed Issue.
3. Work on a separate branch from current `master`; use a fork when appropriate. Preserve other contributors' changes. Internal tasks follow the approved plan and stage gates; an external contribution follows the agreed scope and the external PR review path below.
4. Verify the relevant behavior. Include actual method, configuration, result and sanitized evidence, plus untested cases and failures. Use redistributable fixtures for automation. Do not mark a skipped hardware/game test as passed or infer game compatibility from a build or schema check.
5. Open a PR to `master` using the [PR template](../.github/pull_request_template.md). Explain the problem and resulting behavior, link the Issue, summarize verification and document effects, and respond to review. Merge and Issue closure remain maintainer decisions under the repository workflow.

Repository documents, Issues, PR descriptions, code comments and default user-facing text are written in English. Contributors may discuss the work in their preferred language.

### Maintainer workflow

Internal Issue work uses the [Hyper-Waterfall task workflow](../mydocs/manual/task_workflow_guide.md): Issue, branch, daily board, approved task and implementation plans, implementation, verification, stage/final reports and PR. Stages need explicit approval to continue. Codex work uses `codex/task{issue_number}` and publishes through `codex/publish-task{issue_number}`, as defined in the [repository rules](../AGENTS.md).

The [internal PR template](../.github/PULL_REQUEST_TEMPLATE/internal.md) preserves detailed stage/report fields for these tasks.

External contributors are not required to produce the internal task-plan/report bundle or run agent skills. Maintainers record that review separately, as explained in the [PR process guide](../mydocs/manual/pr_process_guide.md). The review still needs clear scope, attributable changes and reproducible verification. These procedures do not require an AI subscription.

## Record what was tested

A useful verification record identifies the game/build and Steam version where relevant, Pear/runtime artifact and component versions, profile revision, Mac chip/model, macOS version, date, resolution/settings, procedure, observed outcomes and known limitations. Record unknown values as unknown rather than inventing identities or hashes. Link a source/build manifest when it is available.

For a Rosetta-independence claim, follow the [architecture evidence requirements](architecture.md#rosetta-independence-evidence): observe every required host process and loaded native library throughout Steam startup, game startup, play, exit and resume. A native parent, a filename or a small native probe cannot establish the entire launch path. Keep guest Windows x86/x64 execution through the chosen translator distinct from an Intel macOS process using Rosetta.

Technical M1 can use an authorized development-profile configuration. Ordinary-user installation and distribution require separate evidence. The [host capability guide](host-capabilities.md) documents the currently bounded probe result and its limits. Run only tests for which you have the required host, authorization and game ownership; leave unavailable tests explicitly unverified. Preserve normal macOS protections.

Keep correctness diagnostics and performance runs separate. Comparative performance/power claims need comparable hardware, game/runtime versions, scenes, resolution, settings and measurement conditions; diagnostic overhead must be recorded. A short successful gameplay run is not long-term stability or all-Mac certification.

## Protect private inputs

Use your own licensed game copy and authenticate directly through official Steam. Keep proprietary game files, account credentials/tokens, authenticated prefixes, personal saves, private signing material and private diagnostics out of Git, PR attachments and release artifacts. Review exported logs before sharing. Raw GPU captures can contain game resources and must remain private; provide an appropriate sanitized description or redistributable fixture instead.

Back up current data before any approved recovery test and record which copy was restored. Never use another contributor's working state as a disposable test fixture. Only sanitized evidence necessary to reproduce the finding belongs in the review.

## Respect upstream projects

Reuse existing projects with attribution, identifiable revisions and their license/notice requirements. An open-source license and an upstream project's contribution policy are separate obligations. Check the target project's current policy before offering a patch; Pear cannot promise that another project will accept it.

FEX's [contribution policy reviewed on September 28, 2026](https://github.com/FEX-Emu/FEX/blob/59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa/CONTRIBUTING.md) prohibits AI/ML/LLM code contributions. Do not submit AI-generated Pear code upstream to FEX or obscure its origin to evade that rule. Choosing optional AI assistance for other Pear work does not override this restriction, ownership rights, technical review or any other upstream policy.

Original Pear code is licensed under [GPL-3.0-or-later](../LICENSE), except where
a file or directory specifies separate terms. Contributions to that code must be
available under those terms, with copyright and upstream attribution preserved.
Existing MIT/LGPL/GPL notices and additional permissions remain in force; the
Hyper-Waterfall framework retains its MIT attribution. Do not replace upstream
terms with Pear's root license. The [preview component record](../preview/THIRD_PARTY_NOTICES.md)
records the separate runtime source and notice obligations for each release.

### Source notices

Add copyright and license comments to new or modified original source files.
Use the actual publication year and holder; existing Pear original code uses
`Pear contributors`. For example, Python and shell comments use:

```python
# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
```

Use `//` for Rust/Swift or a C comment for C/C++. Keep a script's shebang first
and Python encoding declarations in the first two lines. Preserve existing
copyright lines, license expressions, permission text and upstream attribution;
append new attribution when needed. Never assume a file is Pear-owned merely
because it is in this repository. Update generators alongside generated source.

Run the incremental check before committing (Python 3 and Git, offline):

```sh
python3 -B tools/check_source_notices.py --base <comparison-commit>
python3 -B tools/check_source_notices.py --base <base-commit> --head <head-commit>
python3 -B -m unittest discover -s tests/docs -p 'test_source_notices.py' -v
```

Use the agreed branch point as the comparison commit, or an explicit PR base/head
pair. Without `--head`, tracked working changes and non-ignored untracked files
are checked. The separate **Changed source notices** PR job uses exact GitHub
base/head SHAs. It runs on ordinary pull requests with read-only permissions and
no signing secrets. It becomes active after this workflow is integrated; making
it a branch-protection requirement is a separate repository setting.

The checker covers source/script extensions, TOML/YAML build configuration,
Makefile/CMakeLists.txt/Dockerfile and extensionless shebang scripts. The exact
suffix list is in [the checker](../tools/check_source_notices.py). It requires
leading-comment copyright/year and SPDX metadata, defaults new files to
GPL-3.0-or-later and preserves existing header copyright/SPDX entries on modified
or renamed files. It reports imported copies under `preview/licenses/` and
`preview/runtime-notices/` for manual review instead of relabeling them.

New separately licensed files or older files without SPDX can use an exact-path
entry in [the reviewed exceptions file](../.github/source-notice-exceptions.json):
`{"path/to/file.c": {"license": "MIT", "reason": "Reviewed source and revision",
"notice": "path/to/existing-license.txt"}}`. This selects the correct existing
license, not a waiver of attribution; the referenced notice must exist. Existing
SPDX expressions cannot be overridden by an exception. Changes to this policy or
to the checker itself need maintainer review.

Documents, JSON/data, patches, binary assets and unrecognized source formats
remain manual-review items; use associated notices or sidecars when inline
comments would corrupt them. This incremental gate does not parse every SPDX
expression, detect unmarked copied code, verify ownership or audit every license
obligation. It is not full [REUSE compliance](https://reuse.software/tutorial/).
Unchanged legacy files are not silently declared compliant. Keep frozen signed
candidates unchanged; notice-only edits belong to the next source/package revision.

## Documentation changes

Read the existing document first and update only the necessary parts. Official product, architecture, roadmap and contributor guidance belongs in `docs/`; retain `docs/delivery-plan.md` as the single roadmap. Dated research is evidence, not automatically an accepted specification.

For an internal task, record and approve audience, officialness, selected location, alternatives and rationale in its plan before editing these documents. External proposals should identify the intended audience and location so the maintainer can review the decision. Task plans, approvals and reports stay in `mydocs/`; detailed product specifications do not belong in `mydocs/manual/`. See the [document structure guide](../mydocs/manual/document_structure_guide.md).

### Local documentation checks

Run from the repository root with Python 3. The checker and its fixture tests use only the standard library and run offline:

```sh
python3 tools/check_governance.py
python3 -m unittest discover -s tests/docs -p 'test_*.py' -v
```

The checker covers the root README/agent rules, required host/tests/docs rules, Markdown under `docs/`, and the Pear Apple-tooling router. It checks local file/directory destinations in supported inline links/images and reference definitions, the two skill discovery symlinks, guide/router links and the pinned Apple source inventory's internal consistency. Historical `mydocs/` work artifacts/templates and unrelated root `analysis/` and `research/` are outside the scanned document set.

It ignores external URLs, fenced/inline code and HTML comments. It does not resolve reference uses, validate heading fragments, parse raw HTML links or cover nested/escaped Markdown edge cases. Check new anchors and unsupported link forms manually. The source inventory checks do not contact upstream or establish remote availability or technical accuracy; source revisions and tool requirements still need primary-source review.

A passing check does not prove that an agent understood guidance, that a GPU tool works, or that a runtime/game is qualified. Report these checks with their actual outcomes and coverage; perform the separate tests required by the changed behavior.
