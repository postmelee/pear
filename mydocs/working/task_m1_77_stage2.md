# Task #77 Stage 2: public source conversion and current guidance

Issue: [#77](https://github.com/postmelee/pear/issues/77)
Plan: [task_m1_77_impl.md](../plans/task_m1_77_impl.md)

## Stage Purpose and Artifacts

Convert the four approved repositories after fresh guards, confirm anonymous
source access, and update current access guidance at the planned locations.
Pear changes README.md, docs/README.md, docs/architecture.md and
docs/development/rosetta-free.md. Component document commits are:

| Component | Document commit | Paths |
|---|---|---|
| wine | [`561c61f`](https://github.com/postmelee/pear-wine/commit/561c61f0494640499e80c2f54243f17f9215ea7f) | `README.md`, `pear/README.md` |
| fex | [`16c7a05`](https://github.com/postmelee/pear-fex/commit/16c7a057ae3129bd3dede410bd1755b6e3a93c6e) | `Readme.md`, `Pear/README.md` |
| dxmt | [`322d5f6`](https://github.com/postmelee/pear-dxmt/commit/322d5f62d08b48b4e3fead53c46aab4bd867c531) | `README.md`, `pear/README.md` |
| runtime | [`dfae760`](https://github.com/postmelee/pear-runtime/commit/dfae760b05a10cfef20a3078fe6217c09efe1672) | `README.md`, `docs/development.md` |

## Body Change Scope / Lossless Preservation

Only current Markdown guidance changes. Historical reports/provenance, upstream
README bodies, notices, generated headers, code, recipes, command fences and
existing build/executed-tool pins are unchanged. Task75's completed WGI
correspondence replaces a stale unresolved statement in the runtime guide;
raw/timestamp-derived PE distinctions and unobserved natural-call limits remain.
Only private=false was sent to each repository; default codex/task56 and feature
settings remain. No runtime activation or #47 resource update occurred.

## Verification Results

Each immediate guard confirmed the exact integrated default, sole branch/no
tags and prior configuration. All four transitions report PUBLIC. DXMT's first
post-PATCH commit GET briefly returned 404: processing stopped, current metadata
and ref were re-read, and the successful conversion was not repeated.

Independent post-transition inspection confirmed unchanged integrated commits,
trees, parents and surfaces except visibility/expected metadata timestamps.
Eight anonymous repository/commit requests and fourteen exact-SHA raw README,
license/provenance samples returned HTTP 200 and matched Git objects. Requests
contained no Authorization or Cookie headers. No unexpected findings remain.

- Visibility receipt SHA-256: 09b5c7d8da20f5b4cea616906c5f18328a6e5fc429e51726598f6f026d3f9df3.
- Independent post-public receipt: a41effe792c60b47c50b1fb7e41222cd7b1b60b01d3175667519491f7345dce0.
- FEX/Wine edit checks: 2bc4051fba3a261d3fa819d39fa1948260170abaf6990fd2e552eb68f4dc61f3.
- Runtime/DXMT edit checks: e221d91b1feb2eb38cb5b3250269007804af4f015bd5409470e0d32dd2d4a0b9.

All component git diff --check and incremental notice checks pass; no source
files changed. Forty-nine component relative-link occurrences resolve through
complete Git trees. All prior command fences/pins and FEX protected notice/header
identities remain. New commit author identities already occur in public Pear.
Pear governance passes (40 documents, 386 local targets); 121 document tests pass
on Python 3.13.5 / Git 2.53.0. Incremental source-notice check against cc23a3c
passes with Markdown-only changes; exclusions/provenance were reviewed manually.

## Artifact Disposition

All twelve original protected roots still match their pre-transition HEAD,
branch, status and applicable ignored-file inventories. Original Task56/75
inputs/outputs, installs, game/save/authenticated state remain retained. Only new
text checkouts and audit records exist; no builds, runtime/game execution,
signing, installation, copying of private runtime state or deletion occurred.
No full private-state rehash is claimed. Evidence remains outside public Git.

## Residual Risks and Next Stage

Source publication does not supply retained lower-layer/toolchain/private inputs
or qualify gameplay/distribution. FEX original template holder/introducing-commit
information remains unavailable; the existing notice documents that limit.
Inherited-history/hidden-object coverage remains bounded. The next stage reviews
and publishes these exact document successors and verifies their integration.
The requester's current public-conversion/document-update scope remains active.
