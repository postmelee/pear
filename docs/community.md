# Pear community

Pear welcomes players, testers, developers and documentation contributors. Follow
the [Code of Conduct](CODE_OF_CONDUCT.md). Use the [support guide](SUPPORT.md) to
choose a reporting channel; no paid tool or AI subscription is required.

## Where to participate

| Channel | Purpose |
|---|---|
| [Announcements](https://github.com/postmelee/pear/discussions/categories/announcements) | Maintainer release/status updates with bounded claims |
| [Q&A](https://github.com/postmelee/pear/discussions/categories/q-a) | Setup questions and guidance |
| [Show and tell](https://github.com/postmelee/pear/discussions/categories/show-and-tell) | Structured owned-game observations, including failures |
| [Ideas](https://github.com/postmelee/pear/discussions/categories/ideas) | Proposals and game requests |
| [General](https://github.com/postmelee/pear/discussions/categories/general) | Contribution coordination and broader discussion |
| [Issues](https://github.com/postmelee/pear/issues) | Reproducible defects and accepted, scoped work |
| Pull requests | Reviewable code, documentation and record changes |

Write repository contributions in English; conversation can use your preferred
language. Search before posting and add new evidence to the relevant discussion.
Reactions help show interest but cannot establish compatibility or a deadline.

## Introductory discussions

These posts are already prepared in the current private repository and become
public only with the reviewed visibility change:

- [Welcome to Pear](https://github.com/postmelee/pear/discussions/50).
- [Preview status and remaining release gates](https://github.com/postmelee/pear/discussions/51).
- [How to share a game result](https://github.com/postmelee/pear/discussions/52).
- [Contributing toward the Rosetta-free goal](https://github.com/postmelee/pear/discussions/53).

## From a report to a public record

1. Submit a [game report](compatibility/README.md#submit-a-result).
2. A maintainer checks privacy, exact inputs, missing data and claim scope.
3. A PR updates the [reviewed JSON](compatibility/reports.json) and generated table.
4. CI validates the data and table. Once configured, Pages renders the same data
   from public `master`. An Issue or Discussion alone never changes support status.

Keep the original discussion linked, distinguish reports from reproductions, and
add a new dated record for a changed game/runtime/OS. Preserve regressions and
unknowns. Game Profiles are separate engineering records; this catalog is not an
automatic settings installer or qualified-game registry.

## Public-opening checklist for maintainers

The repository is currently private. These documents and forms are preparation,
not evidence that public services are enabled. After the reviewed visibility
change and integration into `master`:

- Enable GitHub private vulnerability reporting and verify the private form from
  the [security policy](SECURITY.md). Keep exploit details out of Issues.
- Verify the content-reporting options described in the [conduct policy](CODE_OF_CONDUCT.md).
  Reporting to GitHub Support does not guarantee delivery to Pear maintainers.
- Check new Issue/Discussion forms in GitHub and the community profile. A local
  YAML syntax check cannot establish GitHub's rendered form behavior.
- Choose GitHub Actions as the Pages source, configure the `github-pages`
  environment for `master`, then set repository variable `PEAR_PAGES_ENABLED=true`.
  The workflow refuses private repositories and other branches.
- Review the generated site before enabling deployment. It contains only the
  catalog, reviewed JSON, stylesheet and branding; never upload the checkout,
  `mydocs`, private logs, runtime state or game files as a Pages artifact.
- Keep download links unavailable until the [release gates](development/preview-release.md#release-admission)
  pass. Update announcement text when actual availability changes.

Support demand uses one canonical GitHub Discussion per Steam App ID; the
catalog groups separate structured reports beneath that game. Upvotes express
interest and never count as successful play reports. Local draft forms only
prepare text to copy into GitHub; they do not maintain a second report database.

The Wiki may link to these pages, but should not duplicate the roadmap, guides or
records. Keep [docs/README.md](README.md) as the documentation entry point.
