//! Purpose-specific evaluation ported from the v1 independent oracle.
//! A passing result is an evaluation, never an execution authorization receipt.
use crate::{
    contract::{self, Bundle, string_set, timestamp},
    fs::{Error, Result, Root, require},
    json::{J, ensure},
};
use std::collections::{BTreeMap, BTreeSet};
/// A filesystem policy is caller-selected outside the submitted bundle. Compare
/// opened directory identities, not textual prefixes or resolved symlink paths.
pub fn load_external(bundle: &Root, path: &str) -> Result<(J, String)> {
    let (parent, name) = path.rsplit_once('/').ok_or(Error::code("invalid_path"))?;
    let root = Root::open_outside(parent, bundle)?;
    let (bytes, hash, _) = root.read_record(name, 262144)?;
    Ok((crate::json::parse(&bytes)?, hash))
}

pub type Codes = BTreeSet<&'static str>;
fn add(c: &mut Codes, condition: bool, code: &'static str) {
    if condition {
        c.insert(code);
    }
}
fn passed(v: &J) -> bool {
    v.s() == Ok("passed")
}
fn nonempty(v: &J) -> bool {
    v.a().is_ok_and(|a| !a.is_empty())
}
fn hash(v: &J) -> Result<&str> {
    Ok(v.get("digest")?.get("value")?.s()?)
}
fn approved(p: &J, h: &str) -> Result<bool> {
    Ok(string_set(p.get("approved_record_digests")?)?.contains(h))
}
pub fn validate(p: &J) -> Result<()> {
    p.keys(&[
        "policy_version",
        "approved_record_digests",
        "trusted_reviewers",
        "required_checks",
        "required_processes",
        "required_host_modules",
        "required_guest_modules",
        "module_expectations",
        "host",
        "allowed_signing_scopes",
        "max_age_days",
    ])?;
    ensure(
        p.get("policy_version")?.i()? == 1 && (0..=3650).contains(&p.get("max_age_days")?.i()?),
    )?;
    for k in [
        "approved_record_digests",
        "trusted_reviewers",
        "required_checks",
        "required_processes",
        "required_host_modules",
        "required_guest_modules",
        "allowed_signing_scopes",
    ] {
        let a = p.get(k)?.a()?;
        ensure(a.len() <= 128 && string_set(p.get(k)?)?.len() == a.len())?;
        for v in a {
            if k == "approved_record_digests" {
                contract::digest_value(v)?;
            } else {
                contract::id(v)?;
            }
        }
    }
    ensure(
        string_set(p.get("allowed_signing_scopes")?)?
            .iter()
            .all(|v| ["development", "distribution"].contains(v)),
    )?;
    let a = p.get("module_expectations")?.a()?;
    ensure(a.len() <= 64)?;
    let mut ids = BTreeSet::new();
    for m in a {
        m.keys(&["module_id", "kind", "source", "observed_sha256"])?;
        contract::id(m.get("module_id")?)?;
        ensure(ids.insert(m.get("module_id")?.s()?))?;
        ensure(
            ["host", "guest"].contains(&m.get("kind")?.s()?)
                && ["artifact", "system", "game"].contains(&m.get("source")?.s()?),
        )?;
        contract::digest_value(m.get("observed_sha256")?)?;
    }
    contract::host(p.get("host")?)?;
    p.get("host")?.get("architecture")?.eqs("arm64")?;
    Ok(())
}
fn complete_lock(l: &J) -> Result<bool> {
    if !l.get("component_coverage")?.get("complete")?.b()? || !nonempty(l.get("toolchains")?) {
        return Ok(false);
    }
    for k in [
        "compatibility_family",
        "host_requirements",
        "signing_requirements",
    ] {
        if l.get(k)?.get("status")?.s()? != "known" {
            return Ok(false);
        }
    }
    for c in l.get("components")?.a()? {
        for k in [
            "source",
            "dependencies",
            "patches",
            "build_context",
            "terms",
        ] {
            if c.get(k)?.get("status")?.s()? != "known" {
                return Ok(false);
            }
        }
        let b = c.get("build_context")?;
        if !nonempty(b.get("targets")?)
            || *b.get("configuration")? == J::Null
            || !nonempty(b.get("toolchain_ids")?)
            || !nonempty(c.get("terms")?.get("references")?)
            || !nonempty(c.get("evidence")?)
        {
            return Ok(false);
        }
        for t in b.get("targets")?.a()? {
            if *t.get("triple")? == J::Null {
                return Ok(false);
            }
        }
    }
    Ok(true)
}
impl Bundle {
    fn request_codes(&self, q: &J, p: Option<&J>, runtime: bool) -> Result<Codes> {
        let mut c = Codes::new();
        if ["lock", "artifact", "profile"]
            .iter()
            .any(|k| q.get(k) == Ok(&J::Null))
        {
            c.insert("incomplete_identity");
            return Ok(c);
        }
        let l = self.target(q.get("lock")?, "runtime_lock")?;
        let a = self.target(q.get("artifact")?, "runtime_artifact")?;
        let profile = self.target(q.get("profile")?, "game_profile")?;
        add(&mut c, !complete_lock(l)?, "incomplete_identity");
        add(
            &mut c,
            !q.get("observer_required")?.b()?,
            "observer_required",
        );
        add(
            &mut c,
            q.get("prefix_family")? != a.get("compatibility_family")?,
            "incompatible_family",
        );
        add(
            &mut c,
            q.get("signing_scope")? != l.get("signing_requirements")?.get("value")?
                || q.get("signing_scope")? != a.get("signing")?.get("scope")?
                || !passed(a.get("signing")?.get("status")?),
            "signing_not_qualified",
        );
        add(
            &mut c,
            !nonempty(a.get("build_evidence")?),
            "missing_build_evidence",
        );
        let h = q.get("configuration")?.get("host")?;
        let e = l.get("host_requirements")?.get("value")?;
        let version = |v: &J| -> Result<Vec<i64>> {
            Ok(v.get("version")?
                .a()?
                .iter()
                .map(J::i)
                .collect::<std::result::Result<_, _>>()?)
        };
        add(
            &mut c,
            *e == J::Null
                || h.get("architecture")?.s()? != "arm64"
                || h.get("os")? != e.get("os")?
                || h.get("architecture")? != e.get("architecture")?
                || version(h)? < version(e)?
                || !string_set(e.get("capabilities")?)?
                    .is_subset(&string_set(h.get("capabilities")?)?),
            "host_requirements_unmet",
        );
        if runtime {
            for component in l.get("components")?.a()? {
                for t in component.get("build_context")?.get("targets")?.a()? {
                    add(
                        &mut c,
                        t.get("format")?.s()? == "fixture",
                        "fixture_not_runtime",
                    );
                }
            }
            add(
                &mut c,
                *l.get("source_inventory_ref")? == J::Null,
                "source_inventory_required",
            );
            add(
                &mut c,
                profile.get("store")?.s()? != "steam"
                    || nonempty(profile.get("environment")?)
                    || profile
                        .get("operations")?
                        .a()?
                        .iter()
                        .any(|o| o.get("key").and_then(J::s) == Ok("fixture_flag")),
                "fixture_not_runtime",
            );
            for f in a.get("files")?.a()? {
                add(
                    &mut c,
                    f.get("format")?.s()? == "fixture",
                    "fixture_not_runtime",
                );
                add(
                    &mut c,
                    f.get("role")?.s()? == "host" && f.get("architecture")?.s()? != "arm64",
                    "host_not_native",
                );
            }
            add(
                &mut c,
                *q.get("configuration")?.get("game_build")? == J::Null
                    || *q.get("configuration")?.get("steam_build")? == J::Null,
                "incomplete_identity",
            );
            if let Some(p) = p {
                for k in ["lock", "artifact", "profile"] {
                    add(
                        &mut c,
                        !approved(p, hash(q.get(k)?)?)?,
                        "identity_not_trusted",
                    );
                }
                add(&mut c, h != p.get("host")?, "policy_host_mismatch");
                add(
                    &mut c,
                    !string_set(p.get("allowed_signing_scopes")?)?
                        .contains(q.get("signing_scope")?.s()?),
                    "policy_signing_mismatch",
                );
            } else {
                c.insert("external_policy_required");
            }
        }
        Ok(c)
    }
    fn run_codes(&self, r: &J, p: &J, qual: &J) -> Result<Codes> {
        let mut c = Codes::new();
        if *r.get("request")? == J::Null {
            c.insert("incomplete_observation");
            return Ok(c);
        }
        let q = self.target(r.get("request")?, "launch")?;
        c.extend(self.request_codes(q, Some(p), true)?);
        add(
            &mut c,
            q.get("purpose")?.s()? != "qualification_run",
            "wrong_run_purpose",
        );
        if *q.get("profile")? == J::Null {
            c.insert("incomplete_identity");
            return Ok(c);
        }
        let profile = self.target(q.get("profile")?, "game_profile")?;
        let mut checks = string_set(profile.get("required_checks")?)?;
        checks.extend(string_set(p.get("required_checks")?)?);
        checks.extend(string_set(qual.get("required_checks")?)?);
        for needed in checks {
            add(
                &mut c,
                !r.get("checks")?.a()?.iter().any(|x| {
                    x.get("check_id").and_then(J::s) == Ok(needed)
                        && x.get("status").is_ok_and(passed)
                        && x.get("evidence").is_ok_and(nonempty)
                }),
                "required_check_not_passed",
            );
        }
        let cov = r.get("coverage")?;
        let mut needed = string_set(profile.get("required_processes")?)?;
        needed.extend(string_set(p.get("required_processes")?)?);
        needed.extend(string_set(cov.get("required_processes")?)?);
        add(
            &mut c,
            !passed(cov.get("status")?)
                || nonempty(cov.get("missing_processes")?)
                || nonempty(cov.get("missing_modules")?)
                || cov.get("dropped_events")?.i()? != 0
                || !needed.is_subset(&string_set(cov.get("required_processes")?)?),
            "incomplete_observation",
        );
        let processes = r.get("processes")?.a()?;
        let mut observed = BTreeSet::new();
        for x in processes {
            if x.get("required")?.b()? && x.get("observed")?.b()? {
                observed.insert(x.get("purpose")?.s()?);
            }
        }
        add(
            &mut c,
            !needed.is_subset(&observed),
            "incomplete_observation",
        );
        let mut files = BTreeMap::new();
        if *q.get("artifact")? != J::Null {
            for f in self
                .target(q.get("artifact")?, "runtime_artifact")?
                .get("files")?
                .a()?
            {
                files.insert(f.get("file_id")?.s()?, f);
            }
        }
        let mut expectations = BTreeMap::new();
        for m in p.get("module_expectations")?.a()? {
            expectations.insert(m.get("module_id")?.s()?, m);
        }
        let mut modules_present: BTreeMap<&str, BTreeSet<&str>> = BTreeMap::new();
        for proc in processes {
            add(
                &mut c,
                !proc.get("observed")?.b()?
                    || *proc.get("translated")? != J::Bool(false)
                    || proc.get("host_architecture")?.s()? != "arm64",
                "host_not_native",
            );
            let modules = proc.get("modules")?.a()?;
            add(&mut c, modules.is_empty(), "incomplete_module_observation");
            for m in modules {
                let kind = m.get("kind")?.s()?;
                if m.get("observed")?.b()? {
                    modules_present
                        .entry(kind)
                        .or_default()
                        .insert(m.get("module_id")?.s()?);
                }
                add(
                    &mut c,
                    !m.get("observed")?.b()?
                        || *m.get("observed_sha256")? == J::Null
                        || !nonempty(m.get("evidence")?)
                        || (kind == "host" && m.get("architecture")?.s()? != "arm64")
                        || (kind == "guest"
                            && !["x86_64", "i386", "arm64ec"]
                                .contains(&m.get("architecture")?.s()?)),
                    "incomplete_module_observation",
                );
                if m.get("source")?.s()? == "artifact" {
                    let matches = if let Some(f) = files.get(m.get("artifact_file_id")?.s()?) {
                        *m.get("content")? != J::Null
                            && m.get("observed_sha256")?
                                == f.get("content")?.get("digest")?.get("value")?
                            && m.get("content")?.get("digest")?
                                == f.get("content")?.get("digest")?
                            && m.get("kind")? == f.get("role")?
                            && m.get("architecture")? == f.get("architecture")?
                    } else {
                        false
                    };
                    add(&mut c, !matches, "module_identity_mismatch");
                }
                if let Some(e) = expectations.get(m.get("module_id")?.s()?) {
                    add(
                        &mut c,
                        ["kind", "source", "observed_sha256"]
                            .iter()
                            .any(|k| m.get(k) != e.get(k)),
                        "module_policy_mismatch",
                    );
                }
            }
        }
        for kind in ["host", "guest"] {
            let required = string_set(p.get(&format!("required_{kind}_modules"))?)?;
            add(
                &mut c,
                !required.is_subset(modules_present.entry(kind).or_default()),
                "incomplete_module_observation",
            );
            for m in required {
                if let Some(e) = expectations.get(m) {
                    add(
                        &mut c,
                        e.get("kind")?.s()? != kind,
                        "module_policy_mismatch",
                    );
                } else {
                    c.insert("module_policy_incomplete");
                }
            }
        }
        let exit = r.get("exit")?;
        add(
            &mut c,
            exit.get("kind")?.s()? != "exited"
                || exit.get("code")?.i().ok() != Some(0)
                || *exit.get("signal")? != J::Null
                || !passed(exit.get("cleanup")?)
                || nonempty(r.get("failures")?),
            "run_not_passed",
        );
        let events: Vec<&J> = r
            .get("events")?
            .a()?
            .iter()
            .map(|x| self.target(x, "launch"))
            .collect::<Result<_>>()?;
        let hashes: BTreeSet<_> = r
            .get("events")?
            .a()?
            .iter()
            .map(hash)
            .collect::<Result<_>>()?;
        let mut seq = BTreeSet::new();
        for e in &events {
            add(
                &mut c,
                (*e.get("previous")? != J::Null && !hashes.contains(hash(e.get("previous")?)?))
                    || !seq.insert((e.get("producer")?.s()?, e.get("sequence")?.i()?)),
                "event_gap",
            );
        }
        let filtered = |kind: &str, pass: bool| -> Vec<&J> {
            events
                .iter()
                .copied()
                .filter(|e| {
                    e.get("event").and_then(J::s) == Ok(kind)
                        && (!pass || e.get("status").is_ok_and(passed))
                })
                .collect()
        };
        let ready = filtered("observer_ready", true);
        let complete = filtered("observer_complete", true);
        let starts = filtered("spawned", false);
        let stops = filtered("exited", false);
        let tokens: BTreeSet<_> = processes
            .iter()
            .map(|x| {
                x.get("identity")
                    .and_then(|x| x.get("token"))
                    .and_then(J::s)
            })
            .collect::<std::result::Result<_, _>>()?;
        let clocks: BTreeSet<_> = events
            .iter()
            .map(|x| x.get("clock_id").and_then(J::s))
            .collect::<std::result::Result<_, _>>()?;
        if ready.len() != 1
            || complete.len() != 1
            || starts.is_empty()
            || stops.is_empty()
            || clocks.len() != 1
            || events.iter().any(|e| {
                e.get("event").and_then(J::s) == Ok("gap") || !e.get("status").is_ok_and(passed)
            })
        {
            c.insert("observer_lifecycle_incomplete");
        } else {
            let first = starts
                .iter()
                .map(|e| e.get("elapsed_ns").and_then(J::i))
                .collect::<std::result::Result<Vec<_>, _>>()?
                .into_iter()
                .min()
                .unwrap();
            let last = stops
                .iter()
                .map(|e| e.get("elapsed_ns").and_then(J::i))
                .collect::<std::result::Result<Vec<_>, _>>()?
                .into_iter()
                .max()
                .unwrap();
            add(
                &mut c,
                ready[0].get("elapsed_ns")?.i()? >= first
                    || complete[0].get("elapsed_ns")?.i()? <= last
                    || string_set(complete[0].get("covers")?)? != tokens,
                "observer_lifecycle_incomplete",
            );
        }
        for e in &starts {
            add(
                &mut c,
                *e.get("ready_ack")? == J::Null
                    || !hashes.contains(hash(e.get("ready_ack")?)?)
                    || ready.len() != 1
                    || self.target(e.get("ready_ack")?, "launch")? != ready[0],
                "readiness_ack_missing",
            );
        }
        if complete.len() == 1 {
            let basis: BTreeSet<_> = complete[0]
                .get("completed_exits")?
                .a()?
                .iter()
                .map(hash)
                .collect::<Result<_>>()?;
            let mut exits = BTreeSet::new();
            for e in r.get("events")?.a()? {
                if self.target(e, "launch")?.get("event")?.s()? == "exited" {
                    exits.insert(hash(e)?);
                }
            }
            add(&mut c, basis != exits, "completion_basis_incomplete");
        }
        for proc in processes {
            let start: Vec<_> = starts
                .iter()
                .filter(|e| e.get("process") == proc.get("identity"))
                .collect();
            let stop: Vec<_> = stops
                .iter()
                .filter(|e| e.get("process") == proc.get("identity"))
                .collect();
            add(
                &mut c,
                start.len() != 1
                    || stop.len() != 1
                    || start[0].get("elapsed_ns")?.i()? >= stop[0].get("elapsed_ns")?.i()?,
                "process_lifecycle_incomplete",
            );
        }
        add(
            &mut c,
            starts.len() != processes.len() || stops.len() != processes.len(),
            "process_lifecycle_incomplete",
        );
        add(
            &mut c,
            timestamp(r.get("started_at")?.s()?)? > timestamp(qual.get("reviewed_at")?.s()?)?,
            "invalid_review_order",
        );
        Ok(c)
    }
    fn qualification_codes(&self, q: &J, p: Option<&J>, now: i64) -> Result<Codes> {
        let mut c = Codes::new();
        let Some(p) = p else {
            c.insert("external_policy_required");
            return Ok(c);
        };
        add(
            &mut c,
            q.get("decision")?.s()? != "supported",
            "qualification_not_supported",
        );
        add(
            &mut c,
            !string_set(p.get("trusted_reviewers")?)?.contains(q.get("reviewer")?.s()?),
            "reviewer_not_trusted",
        );
        add(
            &mut c,
            !string_set(p.get("allowed_signing_scopes")?)?.contains(q.get("scope")?.s()?),
            "policy_signing_mismatch",
        );
        let reviewed = timestamp(q.get("reviewed_at")?.s()?)?;
        let max = p.get("max_age_days")?.i()? * 86400;
        add(
            &mut c,
            reviewed > now || now - reviewed > max,
            "qualification_expired",
        );
        let mut identities = BTreeSet::new();
        for reference in q.get("runs")?.a()? {
            let run = self.target(reference, "run")?;
            add(
                &mut c,
                !approved(p, hash(reference)?)?,
                "identity_not_trusted",
            );
            c.extend(self.run_codes(run, p, q)?);
            if *run.get("request")? != J::Null {
                let r = self.target(run.get("request")?, "launch")?;
                let mut identity = Vec::new();
                for k in ["lock", "artifact", "profile"] {
                    identity.push(if *r.get(k)? == J::Null {
                        ""
                    } else {
                        hash(r.get(k)?)?
                    });
                }
                identity.push(r.get("entry_file_id")?.s()?);
                identities.insert(identity);
                add(
                    &mut c,
                    r.get("signing_scope")? != q.get("scope")?,
                    "policy_signing_mismatch",
                );
            }
            add(
                &mut c,
                now - timestamp(run.get("started_at")?.s()?)? > max,
                "qualification_expired",
            );
        }
        add(&mut c, identities.len() != 1, "qualified_identity_mismatch");
        Ok(c)
    }
    pub fn eligibility(
        &self,
        entry: &str,
        purpose: &str,
        p: Option<&J>,
        now: i64,
    ) -> Result<Codes> {
        require(
            [
                "inspect",
                "fixture_launch",
                "qualification_run",
                "supported_launch",
                "qualify",
            ]
            .contains(&purpose),
            "invalid_purpose",
        )?;
        if let Some(p) = p {
            validate(p)?;
        }
        let mut c = Codes::new();
        if purpose == "inspect" {
            return Ok(c);
        }
        let r = self
            .records
            .get(entry)
            .ok_or(crate::fs::Error::code("missing_record"))?;
        add(
            &mut c,
            self.records.values().any(|r| {
                r.get("disclosure")
                    .and_then(|v| v.get("mode"))
                    .and_then(J::s)
                    != Ok("full")
            }),
            "partial_bundle",
        );
        add(
            &mut c,
            purpose == "fixture_launch" && self.context != "fixture",
            "fixture_context_required",
        );
        add(
            &mut c,
            purpose != "fixture_launch" && self.context != "runtime",
            "runtime_context_required",
        );
        if purpose == "qualify" {
            if r.get("record_kind")?.s()? != "qualification" {
                c.insert("wrong_entry_kind");
                return Ok(c);
            }
            if let Some(p) = p {
                add(
                    &mut c,
                    !approved(p, &self.hashes[entry])?,
                    "identity_not_trusted",
                );
            }
            c.extend(self.qualification_codes(r, p, now)?);
            return Ok(c);
        }
        if r.get("record_kind")?.s()? != "launch" || r.get("variant")?.s()? != "request" {
            c.insert("wrong_entry_kind");
            return Ok(c);
        }
        add(
            &mut c,
            r.get("purpose")?.s()? != purpose,
            "purpose_mismatch",
        );
        c.extend(self.request_codes(r, p, purpose != "fixture_launch")?);
        if purpose == "supported_launch" {
            if *r.get("qualification")? == J::Null {
                c.insert("qualification_required");
                return Ok(c);
            }
            let q = self.target(r.get("qualification")?, "qualification")?;
            c.extend(self.qualification_codes(q, p, now)?);
            if let Some(p) = p {
                add(
                    &mut c,
                    !approved(p, hash(r.get("qualification")?)?)?,
                    "identity_not_trusted",
                );
            }
            add(
                &mut c,
                q.get("configuration")? != r.get("configuration")?
                    || q.get("scope")? != r.get("signing_scope")?,
                "qualified_identity_mismatch",
            );
            for reference in q.get("runs")?.a()? {
                let run = self.target(reference, "run")?;
                if *run.get("request")? == J::Null {
                    c.insert("qualified_identity_mismatch");
                    continue;
                }
                let old = self.target(run.get("request")?, "launch")?;
                add(
                    &mut c,
                    old.get("entry_file_id")? != r.get("entry_file_id")?,
                    "qualified_identity_mismatch",
                );
                for k in ["lock", "artifact", "profile"] {
                    add(
                        &mut c,
                        *old.get(k)? == J::Null
                            || *r.get(k)? == J::Null
                            || old.get(k)?.get("digest")? != r.get(k)?.get("digest")?,
                        "qualified_identity_mismatch",
                    );
                }
            }
        }
        Ok(c)
    }
}
