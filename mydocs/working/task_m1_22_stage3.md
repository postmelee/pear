# Task #22 — Stage 3 report

GitHub Issue: [#22](https://github.com/postmelee/pear/issues/22)
Implementation plan: [task_m1_22_impl.md](../plans/task_m1_22_impl.md)
Stage: 3

## Stage Purpose

Verify the complete approved adoption and retain a source/installed identity record for review and future updates.

## Artifacts

| File | Change Summary |
|---|---|
| [task_m1_22_inventory.json](task_m1_22_inventory.json) | Complete 54-target inventory with source and installed hashes, relative paths and symlink targets |
| This report | Integrated installation evidence and limitations |

## Body Change Scope / Lossless Preservation

The 51 source-backed files still match pinned v0.3.0 English sources plus the exact approved substitutions. Version state and discovery links are the only other installed targets. All additional files are explicitly named Issue work artifacts; no product source or documentation changed.

## Verification Results

- Expanded manifest/source comparison: 54 of 54 targets passed, including 51 exact source/substitution matches, real version dates and both links.
- All configured project-specific placeholders are resolved. Generic Issue/stage/commit template variables are intentionally retained.
- Source-backed English text: zero Korean-character matches.
- `git diff --exit-code ddf502c -- README.md docs .gitignore`: passed, confirming existing product materials are unchanged.
- Staged diff whitespace checks passed at each stage; the final publication check repeats them for the final task records.
- Inventory contains only relative paths, hashes and framework identity. No account credentials, game files or experimental prefixes are included.
- Independent review confirmed manifest coverage, substitution parity, English text and license attribution before installation.

The upstream doctor returned exit status 0 while displaying source-root errors. Its status code must not be interpreted as a clean diagnosis. The verified cause and independent installation checks are recorded in [Stage 2](task_m1_22_stage2.md).

## Rechecking recorded installed hashes

From the Pear repository root:

```python
import hashlib, json, os
from pathlib import Path
record = json.loads(Path('mydocs/working/task_m1_22_inventory.json').read_text())
for item in record['files']:
    path = Path(item['target'])
    if item['kind'] == 'symlink':
        assert path.is_symlink() and os.readlink(path) == item['link']
    else:
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item['installedSha256']
print('54 recorded targets verified')
```

Source hashes are checked against the immutable framework commit stated in the inventory. These digests record this adoption; they are not upstream release signatures.

## Residual Risks

The v0.3.0 doctor source-root limitation and inapplicable single-branch release examples remain explicitly documented. No runtime or game test is part of this documentation-only adoption.

## Impact on Next Stage

Complete the final report and publish the reviewable open PR. Framework adoption does not merge itself or start unapproved source stages.

## Approval Record

All three stages remain within the approved concrete adoption scope. PR publication follows the approved tracked workflow; merge remains a separate maintainer decision.
