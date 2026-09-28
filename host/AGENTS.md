# Host engineering rules

Read the [root rules](../AGENTS.md), [architecture](../docs/architecture.md) and [host capability diagnostics](../docs/host-capabilities.md), plus the approved Issue and plans for the change.

- Preserve existing upstream languages and reuse decisions. The current C, assembly and Python host tools do not decide the future manager language or runtime/profile contracts.
- Collect native architecture and translation evidence for the actual required processes and libraries. A resolved symbol, built ARM64 executable or successful launcher is not evidence that a restricted operation or integrated game runtime works.
- Run diagnostics only within their authorized process/configuration scope. Preserve owned-child isolation, bounded execution/output, descriptor handling, reaping and cleanup-failure reporting. These controls are not a hostile-code sandbox.
- Check the actual signing/provisioning grant before restricted operations. Preserve normal security protections; do not infer authorization from an entitlement claim or a parent's signature.
- Keep unavailable queries, OS error domains/codes, rejected configurations and unperformed steps in the evidence. Never convert a denied translation query into `false` or CLI exit zero into qualification.
- Bind results to source, input and binary identities, OS/SDK/toolchain and relevant settings. Share sanitized evidence; keep private profiles, signing material and raw diagnostics outside Git.
- Separate correctness diagnostics from performance runs. Use the [Pear Apple-tooling skill](../mydocs/skills/pear-apple-tooling/SKILL.md) only when the approved work needs its Metal expertise.
