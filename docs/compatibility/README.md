# Game observations and reporting

Start with the [reviewed records](records.md). They describe exact configurations,
including incomplete and failed tests. They are not a universal supported-games
list. The current Rosetta Preview has no qualified public download; no player-ready
Rosetta-free preview exists. See the [Preview guide](../rosetta-preview.md).

## Read the records

Two fields answer different questions:

| Field | Meaning |
|---|---|
| Result | Furthest observed behavior: launch failure, unusable launch, interactive menu, active gameplay or regression |
| Evidence | Reported observation; independently reproduced with separate linked evidence; or Pear qualified with a reviewed acceptance record |

A reported result can come from a user or a maintainer. Reviewing its wording does
not make it independently reproduced. Qualification applies only to the recorded
configuration and acceptance scope, not all versions or Macs. The renderer checks
record structure and minimum qualification fields; reviewers must assess whether
the linked evidence actually proves the claim. CI cannot certify gameplay.

Play minutes, input, audio, save/reload and recovery are recorded separately.
`not-tested`, `unknown` and a null play duration remain visible. Rosetta Preview
and Rosetta-free development are separate tracks. Selecting the native track is
not proof that every process/library avoided Rosetta; native qualification needs
the [architecture evidence](../architecture.md#rosetta-independence-evidence).

The initial Megabonk row records a same-host official-Steam menu observation.
It does not claim 20-minute play, audio, save/reload, recovery, independent
reproduction or ordinary-user distribution.

## Browse the catalog

The local/public catalog groups games by Steam App ID, with an official Steam
link, upstream store artwork when available, and a detail page containing dated
reports. A missing image falls back to the game name. The supplied Pear artwork
is separate from Steam/game artwork and does not change its ownership or terms.

Search by name/App ID, filter by runtime and result, and sort by last test, report
count, request votes or name. Pass/Partial/Failed counts are reports, not unique
players or a universal success percentage. Partial includes menu-only and
incomplete tests. Pass requires recorded 20-minute play plus input, audio and
save/reload with no failed checks; it remains distinct from Pear qualification.
A failed check or regression is shown as Failed with its specific limits.
Each report uses the same result, duration, check-state and evidence fields.
Version details retain game-specific notes, reproduction and qualification
status; shared result definitions apply to all games.

[games.json](games.json) holds reviewed Steam metadata and the canonical support
Discussion for each game. Vote counts are optional dated GitHub snapshots;
missing votes are unavailable, never inferred as zero. Report and request forms
search a separate snapshot of Steam game names and App IDs. Suggestions update
as you type; the displayed date identifies the list's freshness. This is not an
upstream request on every keystroke. A Steam search match does not create a Pear
compatibility record. Games omitted by Steam or without a name can still be
entered by Steam store link/App ID. If the list cannot load, reviewed Pear names
and direct ID entry remain available. Introductory-post votes
must not be reused as game demand. A game without a request opens a draft for
Ideas. An existing request links directly to its GitHub upvote. No separate
Pear vote database, automatic support promotion or browser API token is used.

## Submit a result

1. Use the catalog's **Share a result** entry, or open [Show and tell → new discussion](https://github.com/postmelee/pear/discussions/new?category=show-and-tell).
2. Search for a Steam game and choose a result, or paste its store link/App ID.
   Names are filled from Steam metadata (reviewed Pear names are the fallback);
   unlisted IDs can be submitted for name review.
   Reports group by App ID, never by a typed name. Include Pear/runtime/game builds, Mac chip/memory,
   macOS version, test date, settings, exact steps and observed behavior.
3. Record active play duration and choose Observed, Failed or Not tested for
   each input/audio/save/recovery check. Use the same fields for every game;
   leave unmeasured time blank. Failed launches and regressions are useful.
4. Remove account data, passwords, QR codes, tokens, whole prefixes, game files,
   saves and raw logs. Include only sanitized evidence you may share publicly.

The structured form appears after integration into the default branch. Until
then, the catalog can prepare a copyable draft for a normal discussion. It does
not submit the draft, store form data or create a vote. After integration, set
`github_forms_live` in `games.json` only when the live form has been verified. Use a legitimately owned copy;
Pear does not provide games or bypass Steam authentication. Private vulnerabilities
belong in the [security route](../SECURITY.md), not a game report.

## Review and publish a record

A maintainer checks privacy, inputs, claim scope and links, then proposes a PR to
[reports.json](reports.json). Keep stable record IDs; add a new dated record for
new inputs rather than overwriting an earlier success or regression. Do not infer
support from votes or automatically ingest untrusted discussion text.

Each record has game/App ID, date, track, evidence, result, versions, host/settings,
minutes, individual checks, summary, limits and evidence links. Links point to
reviewed Pear GitHub Issues, Discussions, PRs or committed evidence; no local paths,
credentials or externally supplied scripts. Preserve original attribution through
the source discussion link. Independently reproduced and qualified records need
additional evidence URLs; qualified records require reviewed acceptance evidence,
at least 20 gameplay minutes and observed input/audio/save/recovery. These minimum
fields do not replace the full milestone or distribution requirements.

From the repository root:

```sh
python3 tools/compatibility.py
python3 tools/compatibility.py --check
python3 -m unittest discover -s tests/docs -p 'test_*.py' -v
python3 tools/compatibility.py --check --site .build/compatibility-site
```

Commit JSON and generated `records.md` together. The optional site contains only
allowlisted public HTML, CSS, JavaScript, reviewed JSON and Pear branding.
Game detail filenames are derived only from validated numeric App IDs. No private diagnostics or full checkout is copied.
The [community checklist](../community.md#public-opening-checklist-for-maintainers)
controls Pages activation after the approved public transition. Pages is not live
yet; Wiki entries should link here rather than maintain a second data set.

## Refresh Steam search metadata

The [Steam snapshot workflow](../../.github/workflows/steam-catalog.yml) reads the
repository Actions secret `STEAM_WEB_API_KEY`. A maintainer stores a standard
Steam Web API key there; never paste it into source, an Issue, browser code or a
command argument. Only the fetch step receives the secret. The workflow retains
one sanitized `steam-games.json` artifact for seven days, containing a source,
fetch timestamp, and game App IDs/names. It does not deploy the site or edit
compatibility records. It has no recurring schedule.

After workflow integration, run **Steam game search snapshot** from Actions and
download its `steam-game-identities` artifact. Use the extracted file for local
review:

```sh
python3 tools/compatibility.py --check --site .build/compatibility-site \
  --steam-catalog .build/steam-catalog/steam-games.json
node --test tests/docs/test_steam_search.cjs
```

The guarded Pages build fetches a new snapshot when building an approved public
site. Failed or incomplete fetches stop that build, leaving the previous deployed
site in place. No API key appears in the site output. A build without the optional
snapshot provides reviewed-name search and direct Steam link/ID entry instead.
The temporary private Task #47 verification ref only tests this fetch/artifact
path; it does not enable Pages, release downloads or public repository access.

Implementation references (reviewed October 11, 2026): Valve's
[IStoreService/GetAppList](https://partner.steamgames.com/doc/webapi/IStoreService),
[public API host](https://partner.steamgames.com/doc/webapi_overview), and
[header authentication](https://partner.steamgames.com/doc/webapi_overview/auth).
The synchronizer requests games only, continues by the last App ID until an empty
page, normalizes store whitespace, omits unnamed entries and discards every
upstream field except App ID/name. Searches and form drafts stay in the browser.
