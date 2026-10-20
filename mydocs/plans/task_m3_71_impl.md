# Task #71 implementation plan

Implements the explicitly approved repair/release scope in task_m3_71.md.

1. Add a local CLI initialize operation using Session ownership before setup metadata/reporting. Keep setup-info read-only. Recognize only the previous history layout with bounded JSON, same-user regular files, no links, an exclusive observer lock and rechecks before adoption. Never mutate history during admission.
2. Regression checks: `cargo test --manifest-path preview/Cargo.toml --locked --offline`, `python3 -B preview/ci_checks.py`, native suites in `preview/build.sh`, and test_first_install with the actual old bundled CLI. Guard unrelated-file, alias and concurrent-owner rejection.
3. Version 0.1.1 / build 9; retain runtime pin and update public key. Qualified official Sparkle framework reused. Protect signing with existing exact SHA/environment reviewer gates.
4. Final signed empty/failed setup and update tests, public deployment and exact download verification follow the task plan. UI changes are limited to local initialization and actionable initialization errors, so accepted layout stays unchanged.

Artifacts and official documentation locations follow the task plan. Untracked analysis/ and research/ are unrelated and excluded from commits, notices and packages. Use the staged tree/committed SHA for the incremental notice check to avoid sweeping those files. Local iconutil requires normal host access; its sandbox failure is not a source defect.
