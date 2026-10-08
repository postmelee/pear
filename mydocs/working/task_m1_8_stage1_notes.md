# Task #8 Stage 1 — Integration Investigation Notes

Status: historical investigation; see the [completed Stage 1 report](task_m1_8_stage1.md).
Approved scope: [implementation plan](../plans/task_m1_8_impl.md).

## Construction and observed boundaries

- The 14 Wine graphics preimages match the admitted CPU source. The affected
  ARM64EC Wine driver and original x64 device fixture build successfully; the
  native `winemac.so` is byte-identical to the retained #7 artifact.
- Combined development payload signing verifies 41 ARM64 native images.
- Initial candidate omitted #7's independent native-heap reservation loader.
  Its device run recorded the same Swift release function offset as #7's
  historical fault. Native pairing stopped after 33 rows. These failures remain
  retained; a zero OS exit did not establish completion.
- The corrected #7 loader was independently re-admitted, with exact shared
  source/header matching, and included in subsequent candidates. The next native
  pairing produced all 39 required rows, balanced physical lifetime and its PE
  terminal/exit zero. Formal assessment remains incomplete: the legacy reader
  needs #5's extended arena size and the cold prefix attempted an unavailable
  32-bit `rundll32`. Do not label the entire run passed or erase that child failure.
- The earlier x64 device initialization timed out. A 30-second synchronization
  diagnostic observes a cycle between the process heap and loader critical
  sections: the guest main thread and a newly initialized worker block each other.
- A provisional cached-diagnostic-output FEX supplement builds successfully but
  does not resolve the cycle. It is not a proven repair. Retain original and
  modified execution records separately; no core-change acceptance is claimed.
- A separate, nonqualifying ntdll diagnostic records at most 12 bounded frame
  return addresses on the first critical-section timeout, without calling an
  unwinder or changing signing permissions. It identified the actual cycle:
  FEX's memory write guard enters the PE owner thunk, whose caller validation
  invokes `RtlPcToFileHeader` under the process heap lock. That lookup takes the
  loader lock while a new worker holds the loader lock and waits for the heap.
- Replace only that lookup with Wine's existing `NtQueryVirtualMemory` image
  allocation identity check. The same bound/pinned translator remains mandatory;
  committed image type, allocation base and complete query output must match.
  There is no new ABI, caller authorization or permission. Rebuild only PE ntdll.
- Normal candidate `runtime4` with the original qualified #6 FEX DLL completed
  the x64 D3D11 device fixture, exit 42. Independent assessment passed: intended
  loaded DXMT module paths, addresses and bytes, FEX dispatch, native winemac,
  winemetal and Metal, and API/GPU validation banners in the loader process.
  Owned cleanup, unrelated sentinel and current signing admission passed.
  Every observed native process/image was ARM64. Complete late-load coverage and
  game qualification remain unclaimed.
- Candidate `runtime5` adds only the unchanged #6 ordering PE to the fixture
  inventory and repeats the device success. It is the final Stage 1 candidate
  for required native bridge and full affected CPU/ordering revalidation; the
  following regressions superseded its selection as the final candidate.
- Native pairing uses an independently cloned, hash-inventoried completed
  synthetic prefix from this candidate. This exercises the unchanged 39-case
  oracle without repeating the known unsupported 32-bit cold installer attempt.
  Cold-prefix failure remains preserved; it does not establish a working 32-bit
  initialization path. No native bridge or descendant failure is waived.

## Verification and retention

Nine portable tests pass for artifact replacement/symlink/duplicate refusal and
incomplete/failed/substituted device terminals. These do not qualify graphics.
Owned execution cleanup and the unrelated sentinel pass in the completed device
attempts. No Megabonk or Steam execution was performed.

Raw inputs, signatures, build receipts, logs, prefixes and diagnostic records are
private under `.build/task8/`. Existing #5/#6/#7 inputs are unchanged. Final Stage 1
still requires translated device/backend success, admitted native pairing and the
CPU corpus/ordering checks affected by the loader or any retained FEX correction.

## Subsequent regression findings

- Initialized-prefix native pairing again completed all 39 cases, but strict
  descendant assessment found exit 1 in a Wine helper. This run remains failed;
  the original stdout/stderr and full owned process record are preserved.
- The first exact #6 CPU PE (`zero-extension`) exited 91 before instruction
  comparison: fixed scratch data at `0xe0000000` could not be reserved. A bounded
  virtual-memory trace proves an earlier translator-owned 512 MiB slab occupied
  `0xe0000000`–`0x100000000`. This is a changed address-space integration conflict,
  not evidence of a wrong instruction result. The first cold trace exceeded the
  existing output bound; its observation-gap failure remains explicit. A cloned
  initialized synthetic prefix provided the bounded deciding trace.
- Reuse FEX's existing Windows address-requirement API pattern for its private
  data allocator: require translator data at or above 4 GiB. Guest allocation
  requests, the original CPU fixture/expected values, executable arena, owner
  ABI, software TSO and permissions remain unchanged. This downstream supplement
  is built over the qualified #6 source, without the failed logging hypothesis.
  Full affected CPU/ordering and graphics checks remain required.

- Limiting only the lookup-cache allocator did not change the failing CPU result.
  The 512 MiB reservation is made by rpmalloc during FEX CRT initialization.
  The final supplement therefore uses the existing address-requirement path for
  FEX-private anonymous `VirtualAlloc`/`VirtualAlloc2` requests; explicit-address
  commits and the original WOW64 policy remain unchanged. This matches the
  upstream allocator comment about preserving guest low VA, including LuaJIT.
- Candidate `runtime7` with this supplement passed the device/backend check and
  the complete native 39-case assessment, including descendant exits, current
  authorization, sentinel survival and physically balanced views/layers/proxy.
  CPU regression now passes the formerly failing fixed-address case; remaining
  declared CPU/ordering checks are running.
- Diagnostic process tracing identified Wine's optional `winemenubuilder -a -r`
  startup. Its source returns failure when no XDG desktop is present. The native
  fixture clone removes only that exact RunServices value, with before/after
  hashes and the original seed preserved. All child-exit oracles remain intact.
  This setup does not qualify desktop-menu integration or cold 32-bit startup.
- Superseded logging/cache-only patch bytes are retained privately with their
  identities. They are not part of the production patch selection. Completed
  earlier synthetic prefixes are replaced by retained registry/configuration
  files and full hashed inventories; their raw execution logs and runtime/build
  records remain preserved. The active candidate, seed and required results stay
  available. No other task's files were removed.

Final replay passed for candidate `runtime7`: device, native 39 cases, CPU 18
matched plus one explicitly unsupported AVX case, and ordering 32,768 pairs with
eight checked worker retirements. The separate Stage 1 report records acceptance.
