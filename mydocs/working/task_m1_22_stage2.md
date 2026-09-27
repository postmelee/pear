# Task #22 — Stage 2 report

GitHub Issue: [#22](https://github.com/postmelee/pear/issues/22)
Implementation plan: [task_m1_22_impl.md](../plans/task_m1_22_impl.md)
Stage: 2

## Stage Purpose

Install shared agent skills, relative discovery links and actual framework version provenance.

## Artifacts

| File | Change Summary |
|---|---|
| `mydocs/skills/**` | Eight English skill files from the pinned release |
| `.agents/skills`, `.claude/skills` | Relative links to `../mydocs/skills`, staged with Git mode 120000 |
| `.hyper-waterfall/version.json` | Framework/tag/locale/source commit and actual UTC timestamps |

## Body Change Scope / Lossless Preservation

All 51 source-backed files match the approved source/substitution output byte for byte. No framework procedure body was rewritten. The generated state and relative links match the approved contract.

## Verification Results

- Full expanded manifest check: 54 targets present, comprising 51 exact source-file matches, one generated version record and two valid relative links.
- Version-state JSON and real ISO-8601 UTC timestamps parsed successfully.
- `git ls-files -s .agents/skills .claude/skills`: both report mode 120000.
- `git diff --cached --check`: passed.
- Pinned CLI `doctor --repo .`: target paths, locale sources, version and links report OK; the overall command reports source-location errors and is **not a passing overall check**.

### Upstream doctor limitation and resolution of installation uncertainty

Inspection of [getTargetStatuses](https://github.com/postmelee/hyper-waterfall/blob/83836828a4da24385d0410515d35ee43946b981f/src/lib/manifest.js#L131) shows it resolves both source and target paths against the target repository. An adopted repository intentionally has installed targets, not a second copy of the framework's `templates/` sources. The command therefore counts 23 absent default source paths and displays the first eight as errors. Its placeholder check also reads `templates/` rather than installed documents.

The independent validation uses the pinned framework checkout for source paths and Pear for target paths, including the selected English sources. It passes all installation checks. No missing framework source or installed target remains unresolved. Do not add unmanifested source folders merely to silence this upstream diagnostic. A CLI correction is a separate upstream task candidate.

## Residual Risks

The unmodified v0.3.0 doctor is not a standalone adoption acceptance gate because of the demonstrated source-root behavior. Future updates must repeat direct selected-source and target validation until that behavior is corrected.

## Impact on Next Stage

Record source/installed hashes and complete the integrated product-preservation and PR checks. Keep the doctor limitation visible in final evidence.

## Approval Record

Proceeding within the explicitly approved three-stage adoption scope; no product or upstream CLI code was changed.
