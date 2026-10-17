# Task #63: reporting infrastructure activation checkpoint

Requester authorized hosted transmission, administrator review, GitHub linking and
daily catalog activation on 2026-10-18. This narrow publication is based on master
6b7e1a1, excluding held v0.1.0 release and app changes from codex/task63. Official
service/privacy guidance belongs in docs/reporting-and-privacy.md, within the
approved task documentation scope. Task #63 and its current stage remain open.

Hosted evidence: real GitHub administrator login; synthetic HTTPS report receipt;
exact retry accepted; wrong owner rejected (403); stale request rejected (409);
UI approval moved the report into Queued; GitHub Issue #63 metadata imported and
linked in UI; approved snapshot omitted its private note; capability deletion
succeeded and subsequent replay rejected (410). Synthetic report and its exact
unpublished snapshot/source link were removed before public deployment. These are
transport/review tests, not gameplay or released-app integration evidence.

The prepared workflow imports selected public GitHub metadata, exports approved
records, deploys Pages and acknowledges only after successful deployment. Secret
values are stored independently in Worker/GitHub and never committed. Daily schedule
is 00:17 UTC. Existing public download/version content remains unchanged.

Validation: Worker seven tests passed; incremental notices and diff whitespace
checks passed. Catalog rendered against the live empty approved snapshot. Native
app consent/transport integration, Sparkle and final v0.1.0 remain separate work.

Artifact disposition: small source/static preview only; no runtime copy or game
launch. Test capability/CI probe files are temporary private files, to be removed
after hosted verification. Signed artifacts and user game data are unchanged.
