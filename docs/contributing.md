# Contributing to Pear

Players, testers, developers and documentation contributors can help build Pear. You do not need Codex, a paid AI service or programming experience to submit a useful request, reproduction report, test result or documentation improvement. Use the tools you choose and understand the work you submit.

Pear is under development. The [delivery plan](delivery-plan.md) defines the intended capabilities and completion criteria; [GitHub Issues](https://github.com/postmelee/pear/issues) track current ownership and progress. No general end-user release or Rosetta-free Megabonk support is established yet.

## Choose a contribution

| Contribution | Useful information |
|---|---|
| Game request or usability feedback | Game/store identity, the user goal, current obstacle and relevant existing request |
| Problem report | Expected and observed behavior, reproducible steps, versions, settings and a sanitized failure summary |
| Owned-game testing | Exact configuration, test procedure, observed pass/fail/unavailable outcomes and known gaps |
| Documentation | The confusing or missing guidance, intended audience and relevant existing document |
| Profile or compatibility change | Related Issue, reusable upstream work, bounded settings/patches and evidence from the affected configuration |

Search existing Issues and PRs first. Add relevant evidence to an existing report when possible. Requests and future votes express demand; they do not guarantee support, priority or a delivery date. If Discussions is available, it can hold questions and proposals, with adopted work linked to docs and Issues. The [documentation index](README.md) explains these information boundaries.

## Propose and submit a change

1. Find or register the relevant Issue and agree the scope with the maintainer before implementation. State the intended behavior, acceptance criteria, affected areas and exclusions. Read the applicable specification and existing code before designing a replacement.
2. Review reusable upstream implementations and retain their languages unless a measured, reviewed reason supports a change. Record source revisions, license/notice obligations, contribution restrictions and the reason for reuse or new code. Keep changes focused on the agreed Issue.
3. Work on a separate branch from current `master`; use a fork when appropriate. Preserve other contributors' changes. Internal tasks follow the approved plan and stage gates; an external contribution follows the agreed scope and the external PR review path below.
4. Verify the relevant behavior. Include actual method, configuration, result and sanitized evidence, plus untested cases and failures. Use redistributable fixtures for automation. Do not mark a skipped hardware/game test as passed or infer game compatibility from a build or schema check.
5. Open a PR to `master` using the [PR template](../.github/pull_request_template.md). Explain the problem and resulting behavior, link the Issue, summarize verification and document effects, and respond to review. Merge and Issue closure remain maintainer decisions under the repository workflow.

Repository documents, Issues, PR descriptions, code comments and default user-facing text are written in English. Contributors may discuss the work in their preferred language.

Internal Issue work uses the [Hyper-Waterfall task workflow](../mydocs/manual/task_workflow_guide.md): Issue, branch, daily board, approved task and implementation plans, implementation, verification, stage/final reports and PR. Stages need explicit approval to continue. Codex work uses `codex/task{issue_number}` and publishes through `codex/publish-task{issue_number}`, as defined in the [repository rules](../AGENTS.md).

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

Pear's own product-license choice remains unresolved before public release. The MIT attribution for the installed Hyper-Waterfall framework does not choose a license for Pear or relicense reused components.

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
