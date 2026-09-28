# Task #1 Stage 1: Identify and acquire source inputs

GitHub Issue: [#1](https://github.com/postmelee/pear/issues/1)
Implementation plan: [`task_m1_1_impl.md`](../plans/task_m1_1_impl.md)
Stage: 1
Date: September 28, 2026

## Stage Purpose

Establish an identifiable, locally acquired source baseline for the proposed Wine/FEX/DXMT investigation. Resolve actual input objects, inspect source-declared dependencies without running upstream code, and record incomplete coverage before the implementation/patch/terms audit.

Stage 1 is complete as an acquisition and inventory stage. The overall audit remains `audit_complete: false`, `decision: unassessed`, and `source_ready: false`. No source-feasibility, runtime-build or game-support gate has passed.

## Artifacts

| File | Change Summary |
|---|---|
| `runtime/sources/manifest.json` | New factual inventory: 29 component records, 25 dependency edges, 42 tracked vendored paths, observed build requirements and seven unresolved input questions. It is not a product runtime lock. |
| `mydocs/working/task_m1_1_stage1_evidence.json` | New sanitized acquisition and inspection record: actual commands/exit codes, immutable identities, scoped digests, 20 gitlinks and 31 selected build-metadata inspections. |
| `mydocs/working/task_m1_1_stage1.md` | This verification and handoff report. |
| `mydocs/plans/task_m1_1.md`, `task_m1_1_impl.md`, `mydocs/orders/20260928.md` | Approval/progress records updated by the coordinator; approved scope and stage boundaries preserved. |

Downloaded repositories, archive bytes, member listings and raw logs stay under the ignored `.build/task1-sources/` directory. They are not committed. The stable `inputs/` layout preserves source and later patch paths for the next stages.

## Body Change Scope / Lossless Preservation

The stage adds factual metadata and task evidence. Existing architecture, research, product indexes, operating manuals, Issue #2 evidence and Issue #3 contracts are unchanged in this branch. No upstream source is edited or checked out, and no configure/build/install script, toolchain binary, game or Steam client is executed.

### Acquired inputs

The 29 components contain **21 acquired Git source trees, one acquired source archive and seven explicitly unacquired gitlink targets**. Source candidates are not asserted to form a compatible runtime kit.

| Candidate | Acquired immutable commit or archive identity | Role and limit |
|---|---|---|
| Wine upstream | `4e819f054dd2d9ee855ee3f1e30d8c1bb8f80fcf` | Freshly resolved reference for the host/API source audit. |
| FEX upstream | `59f85d6b7df4eb053d2cc1b9d33411b4f31bfbaa` | Windows ARM64EC/WoW64 module and host-integration source candidate. |
| DXMT upstream | `7c8dee1c2d73415301ceb7d1fa810861cef4cd67` | ARM64EC graphics and native shader/Metal source candidate. |
| Wine source associated with DXMT's CI label | `87ba10bb3aa8ea636dff5c2030b376da1627910a` | Source tag `wine-11.2`; matching a binary label does not prove release-binary correspondence. |
| DXMT shader LLVM | `8dfdcc7b7bf66834a761bd8de445840ef68e4d1a` | Acquired `llvmorg-15.0.7` source selected by DXMT CI. |
| LLVM-MinGW source | `030097eeee87fcfd0f3bfe536b21cbd6e5d3b324` | Source tag `20260908`; release-binary build parameters remain unverified. |
| LLVM-MinGW's default LLVM source | `6dfe1677ab8dffbc6ec13d53a1e0215d75147689` | Acquired `llvmorg-23.1.1` source default; separate from DXMT's shader LLVM role. |
| MinGW-w64 source | `9f55f4a2d3b9783dab76d9808be3d6279b99ec2a` | Exact default declared by the selected LLVM-MinGW build source. |
| CrossOver 26.3.0 public source archive | SHA-256 `ac99c8ca4b3848f3e81784135f023df266b61c2345726ea55a50b3e030dd6872` | 149,054,023 downloaded bytes from the [official source page](https://www.codeweavers.com/crossover/source); source-coverage/terms audit is pending. |

All 20 discovered gitlinks in the selected acquired trees are accounted for: 13 targets were acquired and seven were explicitly excluded from this source subset. Exclusions are conditional on the initial MinGW Windows-module path with `BUILD_THUNKS=OFF` and documentation builds disabled. They cover Linux-specific inputs/prebuilt test repositories and range-v3 documentation; they are not permanent declarations about every future Darwin configuration. The required MinGW-path `rpmalloc` source is acquired.

The CrossOver archive was streamed as metadata without extraction. Its 50,394 entries include 16 immediate directories under `sources/`, including Wine. No immediately named FEX/DXMT directory was found. This limited naming observation neither proves absence of relevant code nor establishes ARM64 Preview implementation coverage.

## Verification Results

The planned Git checks were run against each acquired Git input. The evidence file contains the resolved literal paths, commit arguments and exit codes; the following is the implementation plan's per-input command sequence:

```sh
git -C "$PEAR_SOURCE_REPO" rev-parse --show-object-format
git -C "$PEAR_SOURCE_REPO" rev-parse --verify "$PEAR_SOURCE_COMMIT^{commit}"
git -C "$PEAR_SOURCE_REPO" rev-parse --verify "$PEAR_SOURCE_COMMIT^{tree}"
git -C "$PEAR_SOURCE_REPO" fsck --full --no-reflogs
git -C "$PEAR_SOURCE_REPO" ls-tree -r -z --full-tree "$PEAR_SOURCE_COMMIT" > "$PEAR_SOURCE_LISTING"
shasum -a 256 "$PEAR_SOURCE_LISTING"
shasum -a 256 "$PEAR_SOURCE_ARCHIVE"
python3 -m json.tool runtime/sources/manifest.json > /dev/null
python3 -m json.tool mydocs/working/task_m1_1_stage1_evidence.json > /dev/null
git diff --check
```

The archive hash command applies only to the acquired archive. Unacquired inputs have no invented hash, tree verification or successful acquisition result.

| Check | Actual result | Scope |
|---|---|---|
| Git acquisition and integrity | 21/21 acquired inputs; every `git fsck --full --no-reflogs` exited 0 | Available depth-one objects, not complete repository history or authenticated authorship. |
| Git object and listing verification | 21/21 exact commit/tree/object-format and saved listing comparisons passed | SHA-256 covers raw NUL-delimited tree-listing bytes, not concatenated source contents. |
| Archive verification | Download/hash checks passed; exact archive and separate member-listing hashes rechecked | Archive bytes and outer member metadata, not extracted implementation behavior. |
| Dependency accounting | 20 gitlinks: 13 acquired, seven explicit exclusions | Each target remains separate from its parent; conditional omissions are visible. |
| Build-metadata inspection | 31 source blobs recorded with object IDs and byte hashes | Read as text only; requirements and candidate identities are not build results. |
| JSON parsing and internal references | Both planned JSON commands and reference checks passed | Syntax and inventory consistency; the Stage 3 inventory validator does not exist yet. |
| Whitespace, privacy and Git exclusions | Passed | No private absolute user paths or raw acquisition stdout/stderr in tracked records; source caches remain ignored. |
| Independent review | Passed after clarifications | Main source/archive identities, conditional FEX exclusions, factual #1/#3 handoff and explicit incomplete readiness reviewed. |

Source acquisition output, Git object/tree IDs and typed content digests have distinct meanings. No independent publisher signature or published archive checksum was verified. A successful integrity command is not a license determination, compatible toolchain result, native runtime build or Rosetta-independence observation.

## Residual Risks

- Wine's final feature set and native font/TLS/multimedia/graphics packages are unselected. Source/toolchain dependency closure remains incomplete.
- The DXMT-related Wine and LLVM-MinGW source labels do not authenticate their CI binary bundles. Those binaries were not downloaded or executed.
- The two LLVM roles use different declared revisions. Compiler/SDK/Metal versions, build flags and compatibility must be reconciled in Stage 3 and later actual builds.
- CrossOver ARM64 Preview source coverage, existing patch provenance/applicability and required Darwin integration remain unassessed. No missing patch is fabricated or treated as available.
- License, notice and upstream contribution-policy content has not been audited. Candidate filenames are leads only; public availability is not a reuse/distribution clearance.
- Source-acquisition reproduction is Stage 4 work. This first acquisition and local recheck do not count as a second clean acquisition or runtime build.

## Impact on Next Stage

- Stage 2 starts from the recorded immutable inputs. Map Issue #2's bounded host requirements and graphics interfaces to actual source, existing patches, missing behavior and external prerequisites.
- Audit the relevant vendor/fork sources and actual terms; record patch bases/order/hashes and test existing patch applicability only in isolated disposable storage.
- Keep the seven unresolved input questions and conditional dependency exclusions explicit. New input choices must retain provenance; do not silently replace a pin or treat a closed investigation Issue as a passed runtime gate.
- Preserve #3's separate contract ownership. This inventory supplies facts and scope; it cannot authorize a launch or promote an incomplete record into a qualified runtime.

## Approval Request

Review the Stage 1 inventory, evidence and remaining gaps. Approval to proceed authorizes Stage 2's source-coverage, existing-patch and terms audit within the approved plan. It does not authorize new port implementation, runtime builds or game execution. Stage 2 has not started.
