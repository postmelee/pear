# DXMT component rules

Read the root/runtime rules, approved Task #7 plans, graphics audit and Wine host handoff before changes.

- Retain upstream C/C++/Objective-C, source notices and contribution-policy boundaries. Do not modify original source caches, #1 audit bytes or #4 historical patch series.
- Keep exact source inventory, developer-tool availability, compilation, native bridge behavior, hybrid execution and game qualification separate. An accounted unavailable prerequisite is never a ready toolchain.
- Stage 1 is bounded source/tool/layout accounting only: no installation/bootstrap, shader/LLVM/DXMT build, signing, GPU or guest execution.
- #7 owns graphics-only supplemental Wine/DXMT patches. #5 owns translator/CHPE/loader/memory/x18 integration. Root serializes shared changes and native/resource operations.
- Never expose Wine private structure offsets as a stable ABI or change PE headers to satisfy a native-view inspector.
- Keep output under isolated owned task roots, preserve failures and exact input/output/producers. Publish allowlisted observations only; private paths, raw diagnostics and signing material stay outside Git.
