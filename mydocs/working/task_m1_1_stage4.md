# Task #1 Stage 4: Repeat acquisition and source decision

GitHub Issue: [#1](https://github.com/postmelee/pear/issues/1)
Implementation plan: [`task_m1_1_impl.md`](../plans/task_m1_1_impl.md)
Stage: 4
Date: September 28, 2026

## Stage Purpose

Repeat acquisition against the recorded immutable inputs, reconcile every declared audit requirement, and publish a reproducible source decision with explicit downstream obligations. This is the final source-audit stage.

## Artifacts

| File | Change Summary |
|---|---|
| `runtime/sources/manifest.json` | Complete audit with `decision: blocked`, `source_ready: false`; missing implementation, tools and dependency/notice closure remain explicit. |
| `mydocs/working/task_m1_1_stage4_evidence.json` | Fresh remote acquisition commands, matching identities, patch replay and exact final validation results. |
| `docs/source-qualification.md` | Selected inputs, copyable reproduction commands, validator meanings, terms, gap owners and reconsideration conditions. |
| `docs/README.md`, two existing research audits | Narrow dated links to the completed source audit, preserving historical claims and scope. |
| `mydocs/report/task_m1_1_report.md` | All four stages and three Issue acceptance criteria mapped to evidence. |
| Plan, daily task board and this report | Final audit completion and publication approval checkpoint. |

## Body Change Scope / Lossless Preservation

Source pins and original acquired inputs are preserved. All Stage 1–3 evidence remains byte-identical. The second acquisition resides in fresh ignored `.build/task1-sources/reproduction/inputs/`; logs and disposable patch indexes remain under `.build/task1-sources/stage4/`. No source checkout, upstream configuration/build/install, new port patch, opaque preview binary, runtime launch or security-policy change occurred.

The documentation uses the approved locations. Historical research receives only dated follow-up links. No other Issue's acceptance status is changed, and #1 remains open until its approved lifecycle reaches merge or explicit closure authorization.

## Verification Results

```sh
python3 -m unittest discover -s tests/sources -p 'test_*.py' -v
python3 tools/sources/validate_inventory.py --manifest runtime/sources/manifest.json --cache-root .build/task1-sources/reproduction/inputs --require-complete
python3 tools/sources/validate_inventory.py --manifest runtime/sources/manifest.json --cache-root .build/task1-sources/reproduction/inputs --require-source-ready
python3 -m json.tool mydocs/working/task_m1_1_stage4_evidence.json > /dev/null
git diff --check
```

| Check | Result |
|---|---|
| Fresh public Git acquisition | All 22 selected commit/tree/object-format/listing identities match; fresh `fsck` passes. No original repository objects were substituted for remote acquisition. |
| Archive and patch | Exact 149,054,023-byte archive, member metadata and 3,358-byte patch match original SHA-256 pins. |
| Existing patch replay | Original parent check/apply succeeds and reproduces tree `ffb8dd5bf8171ec59c40ee3f5d66f17408206890`; both selected Wine candidates still reject the patch with expected exit 1 and remain unmodified. |
| Owned validator tests | 77 pass; recorded final run 4.426 seconds. |
| Complete-audit gate | Exit 0; `record_valid: true`, `audit_complete: true`, `decision: blocked`, `source_ready: false`. |
| Source-ready gate | Expected exit 3, `requested_gate_not_met`. Source readiness remains refused. |
| Real-cache coverage | 30 components, 22 acquired Git repositories, one archive, 24 content digests, 206 unique source blobs, 16 archive members, 20 gitlinks, one patch, 276 evidence definitions and 359 bounded Git commands. |
| Documentation and preservation | Both contributor Python snippets parse; relative links resolve. Stage 1–3 evidence matches the previous commit. JSON and whitespace checks pass. |

The full [Stage 4 evidence](task_m1_1_stage4_evidence.json) retains the actual commands and observations. Acquisitions used the same Mac and public HTTPS origins; neither publisher signature authentication nor independent-host reproduction was performed.

### Decision and its meaning

The audit is complete because every declared requirement has an evidence-backed disposition. The current assembled candidate is **blocked**: required Darwin ports remain `needs-port`, while missing/conflicting tools and unresolved configured dependency/notice closure prevent a positive build-input gate. The available Wine/FEX/DXMT code is reusable input for further engineering.

The [contributor guide](../../docs/source-qualification.md#gaps-and-downstream-obligations) maps loader/page/x18, FEX UnixLib/thread/JIT/exception and graphics driver/shader obligations to #4, #5 and #7. It records missing Metal/cross/build tools, the Bison 2.3 versus minimum 3.0 conflict, and #13's eventual distribution/source/notice responsibilities. No Preview implementation or unknown hash is silently substituted.

Preparatory work and port implementation may proceed through their own approved plans. Downstream acceptance and all positive runtime/game/distribution claims remain gated until actual implementations, build inputs and matching evidence satisfy them.

## Residual Risks

- This same-host repeat establishes input identity and audit reproducibility, not a working runtime or independently authenticated source supply chain.
- Final build options may activate conditional dependencies or additional notices; the configured dependency and shipped-payload closure remains unresolved.
- Bounded vendor/source inspection does not prove availability of the complete commercial Preview implementation.
- Source inspection, successful historical patch application and finite #2 host tests cannot substitute for Wine/FEX/DXMT integration or gameplay evidence.

## Impact on Next Stage

The #1 investigation has reached its final report. Future approved #4/#5/#7 work must explicitly resolve the blocked inputs and required ports. #3 remains independent and cannot make this source set ready by choosing a manager language. Source-ready status requires a reviewed new manifest decision and its passing gate.

## Approval Request

Review this final stage and the [Issue #1 final report](../report/task_m1_1_report.md), then approve PR publication. No merge or Issue closure is requested implicitly.
