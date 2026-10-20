# Task #70 Stage 1 — Locale presentation and routes

GitHub Issue: [#70](https://github.com/postmelee/pear/issues/70)
Implementation plan: [task_m3_70_impl.md](../plans/task_m3_70_impl.md)
Stage: 1

## Stage Purpose
Establish static English/Korean page mapping without changing application or report
semantics. Context and reuse decisions follow the approved task/implementation
plans, root/scoped rules and task-stage-report skill. The latest requester
continuation authorizes both implementation stages through local preview.

## Artifacts
- tools/catalog_locale.py: reviewed presentation lookup, protected text boundaries,
  Korean page destinations and shared assets.
- tools/catalog_site.py, compatibility.py: language links, metadata, search output
  and explicit allowlists.
- tools/catalog/locales/ko.json: initial navigation messages; expanded in Stage 2.
- catalog JS/CSS: same-page language navigation and responsive controls.
- community_reports.py: preserve submitted field values.
- tests/docs: locale contract tests and expanded bilingual publication expectations.

## Body Change Scope / Lossless Preservation
No article prose changed in this stage. Report enums, submitted values, commands,
media, English URLs and signed update bytes are preserved. Korean is a reviewed
presentation projection, not an automatic translation service. Option values remain
English; translate="no" protects evidence even when text matches a UI message.

## Verification Results
Source/fixture checks on the current Mac using Python 3.14.4. No runtime/game test
is warranted by these display-only changes. No prior pass was reused.

`python3 -m unittest discover -s tests/docs -p 'test_*.py'`: 118 tests passed in
12.511 seconds. Includes generated nested URLs/assets/fragments under /pear/,
rebuild determinism, protected text, metadata, shared media and form option values.
`git diff --check`: passed. Full translation and browser interaction are Stage 2
work, not claimed here. Temporary command output: /tmp/pear70-stage1-tests.log.

## Artifact Disposition
Source and tests retained in Git for Stage 2. Unit-test temporary sites removed by
TemporaryDirectory cleanup. No application/runtime copies or dependency installs.
Other .build roots and recovery evidence untouched. Storage/free-space deltas not
measured; this stage creates only small tracked text and disposable test fixtures.

## Residual Risks
Korean message coverage and article translation incomplete until Stage 2. Browser
layout/interaction not yet checked. Future unmarked dynamic fields need provenance
review before extending templates.

## Impact on Next Stage
Complete translations, date/correction notice and current-release wording; preserve
all stable identifiers. Review dynamic JS messages and local visual behavior.

## Approval Request
No new permission needed: the requester explicitly authorized continuing through
local preview. Public deployment remains pending that review.
