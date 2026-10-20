# Pear Preview component and license record

Reviewed October 11, 2026. This is a candidate distribution inventory, not a claim
that all release obligations are resolved.

## Pear license

Copyright (C) 2026 Pear contributors.

Except where a file or directory specifies separate terms, original Pear code
is free software: you may redistribute it and/or modify it under the GNU General
Public License as published by the Free Software Foundation, either version 3
of the License, or (at your option) any later version.

Pear is distributed without any warranty, including implied warranties of
merchantability or fitness for a particular purpose. See the included LICENSE
for the full terms. This choice preserves existing upstream/file/directory
licenses and does not apply to Steam, Rosetta or games.

## Included in the Pear app and CLI

- Pear's Rust bootstrap, thin Swift/AppKit window, reused Pear manager hashing/path
  helpers and Pear C bridge: original Pear code under GPL-3.0-or-later.
- Rust libc 0.2.186: MIT OR Apache-2.0. Both original license texts are included in
  `licenses/`. Locked archive SHA-256:
  `68ab91017fe16c622486840e4c83c9a37afeff978bd239b5293d61ece587de66`.
  Source: https://github.com/rust-lang/libc/tree/0.2.186 .
- Rust standard-library code linked by Rust 1.94.1: toolchain-supplied library
  copyright and license notices are included in `licenses/`, unchanged. The
  library attribution file also covers its separately licensed dependencies.
- System AppKit/Foundation/Swift and system C libraries are referenced from macOS;
  Pear does not package copies of these system libraries.

The original MIT attribution on Hyper-Waterfall operating documents applies to
those documents, not to a new product-license choice for Pear. Other repository
fixtures retain their original notices; they are not copied into these binaries.

## Historical rejected Gcenx candidate

The earlier bootstrap evaluated Gcenx Wine 11.0_1 with DXMT 0.80.
The current app and CLI instead select the pinned source-built Pear runtime.
This candidate failed Steam login-window rendering on the test host and is not
admitted for release. A separate DXVK/native versus DXMT/builtin diagnostic split
also failed to display a window. Existing notarized packages
still contain the earlier bootstrap; do not reuse their receipts for this code.

| Input | Fixed identity | Origin and source boundary |
|---|---|---|
| Wine stable 11.0_1 | 185,303,032 bytes; SHA-256 b50dc50ec7f41d58b115a6b685d4d1315ba3c797bd3aa0f49213f2703cb82388 | Direct Gcenx release archive. Release documentation at 362fe0e69deeced7ac4db06e1ff69652569313b2 identifies Wine 11.0, configure options and MacPorts/overlay dependency origins. Exact dependency source/patch coverage is still under review. |
| DXMT 0.80 builtin | 18,681,669 bytes; SHA-256 8f260e36b5739e68f3bad613381441385c4dc7b85b78ba8de653d5a6a264529d | Direct 3Shain release; source 589adb780354b461645b29999cefaf533594ee99. The MIT and separate DXVK zlib notices are preserved in licenses/ and installed with the runtime. |

That earlier bootstrap assembled these in isolated staging, retaining Wine's own helper, Mono and
Gecko files. It pairs DXMT's winemetal.dll and winemetal.so, preserves their builtin
identity and changes only the checked 16-byte builtin marker of d3d11, dxgi and
d3d10core in each Windows architecture for native per-prefix loading. Pear records
both archive digests, the assembly version and the installed inventory. No DXVK
payload is selected by this D3D11 candidate. Wine's LICENSE and COPYING.LIB are
also preserved in licenses/ and installed as supplemental notices; these texts
alone do not complete the dependency inventory. Existing private environments
require a reviewed migration and are refused by this candidate without mutation.

The release declares GStreamer.framework as a dependency. This host has no such
framework; successful basic Wine execution does not qualify media playback or
all games. Resolve the tested delivery scope before public distribution.

Candidate references:
- https://github.com/Gcenx/macOS_Wine_builds/releases/tag/11.0_1
- https://github.com/Gcenx/macOS_Wine_builds/blob/362fe0e69deeced7ac4db06e1ff69652569313b2/README.md
- https://github.com/3Shain/dxmt/releases/tag/v0.80

## Historical baseline downloaded from its distributor

Pear packages contain none of the following runtime or installer payloads. A
separate download is not a blanket license exemption. Preserve upstream notices
and resolve exact source/provenance before changing delivery or mirroring binaries.

The historical baseline also injects `--no-sandbox --in-process-gpu --disable-gpu`
when launching Steam webhelper. This was confirmed by command-line records and a
no-network dummy probe. CEF sandboxing is therefore not established by the app
signing checks, and this workaround is not approved as a release default.

| Component | Exact selected input | Review and obligations |
|---|---|---|
| Whisky Libraries | v3.1.1, SHA-256 01f3a1b43b98065fe20c529c1023b61dd79a6d2ad93bba6040865f646481ccf3 | Downloaded unchanged from frankea/Whisky. The archive is an aggregate, not wholly licensed under the Whisky app's GPL. |
| Wine | 11.0, carried from the January 18 Libraries v3.0.0 release | LGPL-2.1-or-later with separately licensed files/dependencies. The later upstream table names Gcenx 11.0_1, but that April release is not the same Wine build. Exact source, patch and build-script correspondence remains unresolved. |
| DXMT | 0.80 in the above runtime | The actual archive includes the MIT copyright/permission notice for Feifan He. Preserve it. Later DXMT versions have different licensing; never infer their terms from 0.80. All 11 DXMT payload files match the v0.80 release after the documented six 16-byte marker changes. Preserve separate dependency terms, including the source tree's DXVK zlib notice; the top-level MIT notice is not an inventory of every dependency. Pear retains the distributed bytes. |
| DXVK | Gcenx v1.10.3-20230507-repack, native archive | Four DLLs and dxvk.conf match the upstream archive exactly. The source tag has the zlib/libpng license; retain its attribution and mark altered source versions. |
| MoltenVK / Wine helpers | 39 regular dylibs match Gcenx 11.0_1 byte-for-byte | Binary origin is mapped; exact dependency source versions, build inputs and complete notice coverage remain unresolved. An ABI filename is not a source version. |
| Wine Mono / Gecko | Mono 10.4.1; Gecko 2.47.4 | 2,921 Mono and 60 Gecko regular files match Gcenx 11.0_1. Their component-specific source/license inventories remain necessary; Wine's LGPL alone does not describe this aggregate. |
| Official Steam installer/client | Valve HTTPS installer pinned in preview/src/lib.rs; client self-updates | Proprietary Valve software, not relicensed by Pear. Downloaded from Valve, not included in Pear archives. Users authenticate directly with Steam and supply their own licensed games. |
| Rosetta | Installed through macOS | Apple component; not included, modified or relicensed by Pear. |

Whisky GUI source is GPL-3.0-or-later. It was inspected for reuse, but no Whisky
GUI/WhiskyKit source or app binary is incorporated into Pear's app/CLI. The
core invokes a separately installed Wine executable; it does not link Wine into
the Rust program. If code is imported or that boundary changes, revisit the
license analysis before adopting the change. Choosing GPL for Pear alone would
not resolve missing corresponding source or other components' notice obligations.

D3DMetal/GPTK is not selected. DepotDownloader and FEX are not used by this preview.
No game binary, authenticated prefix, save or private signing material belongs in
any Pear release archive.

## Bounded runtime and repository findings

The historical Whisky runtime has 4,787 regular files. A case-insensitive basename scan
for license/licence, copying, copyright, notice or authors found only
Libraries/DXMT/LICENSE; its digest matches the upstream 0.80 notice. This
filename scan does not establish absence of embedded attribution or a license
violation. Wine's complete notices and all auxiliary component source/build
correspondence are not yet resolved. Notice text may also exist in resources or
source headers; the filename scan does not inspect every embedded notice.

The 39 regular dylibs include GnuTLS, GMP, Nettle, libidn2, libunistring, gettext,
SDL2, ICU, FreeType, libpng, MoltenVK, compression and MacPorts support libraries.
Mono/Gecko and other PE/managed modules require their own license/source review,
even where binary identity is mapped. An ABI filename
is not a verified source version. Whisky's assembly script repacks prior binaries;
its source repository alone is not the complete corresponding runtime source.

Pear's source tree also includes a GPL-3.0-or-later Madeira-derived CPU test driver
and separately licensed MIT/LGPL fixtures. These are not in this preview binary.
The root license preserves their existing terms and attribution.
The owner adopted GPL-3.0-or-later for original Pear code without a separate
existing license on October 11, 2026. It does not relicense the external aggregate.

## October 11 binary provenance comparison

The historical Whisky archive's Wine subtree has 4,770 regular files. Of those, 3,200
have a SHA-256 match somewhere in Gcenx's current 11.0_1 archive; 1,570 do not.
The same-path comparison establishes the helper/Mono/Gecko matches listed above.
A representative cmd.exe differs in both size and extensive contents, not only
its timestamp, and ntdll.so also differs. This is not proof of a source-license
violation: binary equality is a provenance aid, not the test for corresponding
source. It does mean the April 11.0_1 package cannot be treated as the unchanged
source of the January Wine build.

The exact Libraries v3.1.1 tag is
58b3ce120bcc7a86ff6e6b4a4e921dfce57fe115. Its assembly script pins the January
v3.0.0 archive and transforms DXMT; it does not build Wine or enumerate all helper
sources. The April 16 MacPorts overlay snapshot
5c5bf5771ab8110d538aa25faee1b81578111840 differs from the previously inspected
later recipe and is only a source lead, not an established January build input.

The requester selected replacement-candidate validation without an upstream
inquiry. Resolve source/patch/recipe and dependency notice records for whichever
candidate is admitted for release; the historical baseline gap remains recorded. Do not silently replace
working installations. The unchanged direct-upstream download boundary remains;
Pear does not bundle or mirror the runtime. No infringement conclusion is made.

## Primary references

- Exact assembly: https://github.com/frankea/Whisky/blob/58b3ce120bcc7a86ff6e6b4a4e921dfce57fe115/scripts/assemble-runtime.sh
- Original base release: https://github.com/frankea/Whisky/releases/tag/v3.0.0
- Comparison Wine release: https://github.com/Gcenx/macOS_Wine_builds/releases/tag/11.0_1
- DXVK source/license: https://github.com/Gcenx/DXVK-macOS/tree/8f1e28deed3ad30802f7e1bdff428ec14e6e7817
- DXMT exact source: https://github.com/3Shain/dxmt/tree/589adb780354b461645b29999cefaf533594ee99
- Runtime release: https://github.com/frankea/Whisky/releases/tag/v3.1.1
- Pinned assembly record: https://github.com/frankea/Whisky/blob/305da2143bf6f73ac5b261303c7e7e957c23a227/docs/DEPENDENCIES.md
- Wine 11.0 license: https://github.com/wine-mirror/wine/blob/wine-11.0/LICENSE
- Wine LGPL text: https://github.com/wine-mirror/wine/blob/wine-11.0/COPYING.LIB
- DXMT 0.80 license: https://github.com/3Shain/dxmt/blob/v0.80/LICENSE

The product license is selected. Release remains pending component provenance/
obligation review and the other qualification gates. This record must match the
shipped bytes.


## Source-built Rosetta candidate (local reconstruction verified)

The independent runtime candidate is separate from both the failed Gcenx setup
and previously notarized launcher packages. Its first installed tree was released
during storage maintenance. Historical gameplay observations remain recorded, but
that deleted tree cannot be used or treated as current qualification.

`runtime-inputs.json` pins the original CodeWeavers 26.3.0 FOSS Wine archive,
GMP 6.3.0, Nettle 4.0, libtasn1 4.21.0, libunistring 1.4.2, libidn2 2.3.8,
GnuTLS 3.8.13, libpng 1.6.59 and FreeType 2.14.3 source archives. The recipe builds
the shared libraries and Wine locally using their upstream build systems. The
Wine derivative patch retains Wine's LGPL terms. It opts into --in-process-gpu
for the main Steam webhelper, without adding an explicit sandbox-disable switch.
This statement does not establish effective CEF sandbox enforcement.

The original component notices are retained in `runtime-notices/`. FreeType is
used under FTL with its attribution and separate contribution notices. GnuTLS's
main library terms must be considered together with the LGPL-3.0-or-later/GPL
alternatives of linked GMP, Nettle and libunistring; this closure is not described
as LGPL-2.1-only. The source archives preserve per-file licensing detail.

DXMT 0.80 and public-API MoltenVK 1.4.2 remain unmodified upstream release inputs
apart from recorded install-name/ad-hoc-signature adjustments where applicable.
The lock records exact binary hashes and source revisions; this recipe does not
claim to rebuild those two upstream releases. DXMT MIT and DXVK-derived zlib
notices, MoltenVK Apache-2.0 and pinned external notices remain included. macOS
system libraries and Rosetta are not redistributed in the candidate.

The source/input kit uses an explicit allowlist of pinned archives, build recipe,
patch, lock and notices. It excludes Steam, games, private prefixes, credentials,
saves and signing material. The kit and a successful build do not alone close
source-delivery review, final signing/notarization, gameplay/recovery or independent
clean-Mac delivery requirements. No new download is admitted by this record.


### Source-delivery preparation after reconstruction

The replacement runtime has now passed a fresh build, relocated synthetic
crypto/font/TLS checks and a same-host Steam/game relaunch with requester-reported
save persistence. Those results refer to the immutable v2 runtime manifest; they
are not final package signing, clean-Mac or public release qualification.

The reviewed next-package notice set adds Wine's bundled-library license files,
original authors and font attribution. This software is based in part on the
work of the Independent JPEG Group. Wine's source archive retains the complete
per-file terms; the bundled-library licenses do not become Pear's GPL license.

DXMT 0.80's shader translator statically links LLVM. Its pinned CI declares
LLVM 15.0.7, consistent with the shipped winemetal.so version strings; the LLVM
license and exceptions are now retained alongside the existing DXMT/DXVK notices.
Original Microsoft DXBCParser files preserve their MIT attribution, and pinned
NVIDIA NVAPI and MinGW DirectX header notices are included. Their origins and
hashes are recorded in runtime-notices/dxmt/provenance.json. This does not claim
byte-reproduction or a complete static toolchain-runtime audit of that release.

These additions are prepared for the next package, not retroactively installed
into the already-tested runtime. The source kit includes this component record,
complete pinned copyleft source archives, the Wine patch, build/install recipe
and original notices. At release, provide the matching source kit next to the
binary download with clear links, preserved license texts and all modifications;
an upstream project URL alone is not the chosen source-delivery mechanism.
The current kit is a local development artifact, not a public source offer.

Remaining admission work: verify the final integrated package and normal
app/CLI execution against its new inventory;
provide the exact committed Pear/app sources, runtime source kit and final
packaging/signing recipe together; and perform the approved signing, normal-open,
recovery and clean-Mac checks. Do not publish a candidate based on the earlier
launcher notarization or the historical 61-notice package.

Source-delivery references: GNU LGPL 2.1 section 4; GNU LGPL 3 section 4 and
GNU GPL 3 section 6. These upstream terms govern the respective components;
this inventory is an engineering record, not a substitute for their full texts.


### App/CLI integration notice closure

The conservative static compiler-runtime notice set is now retained under
runtime-notices/toolchain: LLVM 21.1.8 LLVM/libc++/libc++abi/libunwind/compiler-rt,
llvm-mingw 20251216, its pinned MinGW-w64 COPYING, and GCC 15.2.0 GPL text with
the GCC Runtime Library Exception. DXMT's pinned CI selects llvm-mingw 20251216;
that toolchain's scripts select the recorded LLVM/MinGW revisions. These notices
supplement, rather than replace, the separate LLVM 15.0.7 shader-translator terms.
The locally built Wine PE toolchain records GCC 15.2.0. Build tools themselves
are not included. Original per-file exceptions continue to apply.

This completes the identified notice comparison for the candidate integration.
Conservative inclusion does not claim byte-identical reproduction of the upstream
DXMT release or prove that every collected library contributes linked code.
Packaging must bind the final notice inventory, baseline executable hashes and
source kit. Public distribution admission remains separate.


## Sparkle app updater (2.10.0)

The app embeds the unmodified Sparkle 2.10.0 framework from the upstream release
archive, SHA256 `c2bf58aa8387266ac179357b1415d6f2635f044da8be41042af32425dae6da0c`.
Origin: https://github.com/sparkle-project/Sparkle/releases/tag/2.10.0.
The framework retains Sparkle's MIT terms and the bundled BSD/Ed25519 notices;
the complete upstream license is copied to `licenses/Sparkle.txt` in the app.
Its signatures are replaced by Pear's approved Developer ID during distribution
signing, without changing the upstream source or its license. Sparkle updates
only the Pear app; the Wine/DXMT runtime remains a separately verified input.
The upstream file/link inventory is recorded in `sparkle-files.json` (JSON does
not carry comment headers). Framework headers and binaries retain their original
notices rather than Pear's source header. Build/signing admission is not a claim
that signed old-to-new update qualification has completed.

`update-public.json` contains only public update configuration and a public Ed25519 key; JSON cannot carry source comment headers. Private signing keys remain outside the repository.

## First-install recovery JSON recognition (0.1.1)

The Rust launcher reuses serde_json 1.0.151 (https://github.com/serde-rs/json,
MIT OR Apache-2.0) to recognize a preserved 0.1.0 reporting snapshot. Its bounded
input is not rewritten and recognition does not grant sharing consent. Swift
continues to decode the complete reporting schema. The existing manager JSON
parser only accepts integers and cannot read Swift Date values, so it is not
extended for this unrelated contract. Cargo.lock pins serde/serde_core, itoa,
memchr and zmij; upstream license files, including conservatively retained
locked proc-macro dependencies, are included under licenses/. The existing
crate sources are unmodified.
