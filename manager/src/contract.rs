//! Closed contract consumers adapted from #3 shape/Bundle traversal and the v1 oracle.
use crate::{
    fs::{self, Error, Result, Root, require},
    json::{J, R, ensure, parse},
    native,
};
use std::collections::{BTreeMap, BTreeSet};
use std::os::unix::fs::MetadataExt;

pub fn id(v: &J) -> R<()> {
    let s = v.s()?;
    ensure(
        !s.is_empty()
            && s.len() <= 96
            && s.as_bytes()[0].is_ascii_alphanumeric()
            && s.bytes()
                .all(|c| c.is_ascii_alphanumeric() || b"_.-".contains(&c)),
    )
}
fn text(v: &J, max: usize) -> R<()> {
    ensure(!v.s()?.is_empty() && v.s()?.chars().count() <= max)
}
fn url(v: &J) -> R<()> {
    let s = v.s()?;
    ensure(
        s.starts_with("https://")
            && s.len() > 8
            && s.chars().count() <= 2048
            && !s.chars().any(char::is_whitespace),
    )
}
fn one(v: &J, choices: &[&str]) -> R<()> {
    ensure(choices.contains(&v.s()?))
}
fn array(v: &J, min: usize, max: usize) -> R<&[J]> {
    let a = v.a()?;
    ensure((min..=max).contains(&a.len()))?;
    Ok(a)
}
fn optional(v: &J, f: impl FnOnce(&J) -> R<()>) -> R<()> {
    if *v == J::Null { Ok(()) } else { f(v) }
}
fn ids(v: &J, min: usize) -> R<()> {
    let a = array(v, min, 64)?;
    let mut seen = BTreeSet::new();
    for x in a {
        id(x)?;
        ensure(seen.insert(x.s()?))?;
    }
    Ok(())
}
pub fn digest_value(v: &J) -> R<&str> {
    let s = v.s()?;
    ensure(
        s.len() == 64
            && s.bytes()
                .all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c)),
    )?;
    Ok(s)
}
fn digest(v: &J, scopes: &[&str]) -> R<()> {
    v.keys(&["algorithm", "scope", "value"])?;
    v.get("algorithm")?.eqs("sha256")?;
    one(v.get("scope")?, scopes)?;
    digest_value(v.get("value")?)?;
    Ok(())
}
fn path(v: &J) -> R<()> {
    fs::relative(v.s()?).map_err(|_| ())
}
fn blob(v: &J, scopes: &[&str]) -> R<()> {
    v.keys(&["ref_type", "path", "digest"])?;
    v.get("ref_type")?.eqs("blob")?;
    path(v.get("path")?)?;
    digest(v.get("digest")?, scopes)
}
fn blobs(v: &J, scope: &str) -> R<()> {
    for x in array(v, 0, 64)? {
        blob(x, &[scope])?;
    }
    Ok(())
}
fn reference(v: &J, kind: &str, version: i64) -> R<()> {
    v.keys(&[
        "ref_type",
        "path",
        "record_kind",
        "schema_version",
        "digest",
    ])?;
    v.get("ref_type")?.eqs("record")?;
    v.get("record_kind")?.eqs(kind)?;
    ensure(v.get("schema_version")?.i()? == version)?;
    path(v.get("path")?)?;
    digest(v.get("digest")?, &["exact_utf8_file_bytes"])
}
fn refs(v: &J, kind: &str, version: i64, min: usize) -> R<()> {
    for x in array(v, min, 64)? {
        reference(x, kind, version)?;
    }
    Ok(())
}
fn knowledge(v: &J, fields: &[&str]) -> R<()> {
    let mut keys = vec!["status", "reason"];
    keys.extend(fields);
    v.keys(&keys)?;
    one(v.get("status")?, &["known", "unknown"])?;
    ensure(v.get("reason")?.s()?.chars().count() <= 2048)
}
fn state_value(v: &J, f: impl FnOnce(&J) -> R<()>) -> R<()> {
    knowledge(v, &["value"])?;
    ensure(v.get("status")?.s()?.eq("known") == (*v.get("value")? != J::Null))?;
    optional(v.get("value")?, f)
}
fn immutable(v: &J) -> R<()> {
    v.keys(&["kind", "object_format", "value"])?;
    match v.get("kind")?.s()? {
        "archive" => ensure(*v.get("object_format")? == J::Null && *v.get("value")? == J::Null),
        "git_commit" => {
            let n = match v.get("object_format")?.s()? {
                "sha1" => 40,
                "sha256" => 64,
                _ => return Err(()),
            };
            let s = v.get("value")?.s()?;
            ensure(
                s.len() == n
                    && s.bytes()
                        .all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c)),
            )
        }
        _ => Err(()),
    }
}
pub fn host(v: &J) -> R<()> {
    v.keys(&["os", "architecture", "version", "capabilities"])?;
    v.get("os")?.eqs("macos")?;
    one(v.get("architecture")?, &["arm64", "x86_64", "unknown"])?;
    for n in array(v.get("version")?, 3, 3)? {
        ensure((0..=999).contains(&n.i()?))?;
    }
    ids(v.get("capabilities")?, 0)
}
fn configuration(v: &J) -> R<()> {
    v.keys(&[
        "host",
        "chip",
        "game_build",
        "steam_build",
        "renderer",
        "translator",
    ])?;
    host(v.get("host")?)?;
    for key in ["chip", "renderer", "translator"] {
        id(v.get(key)?)?;
    }
    for key in ["game_build", "steam_build"] {
        optional(v.get(key)?, id)?;
    }
    Ok(())
}
fn status(v: &J) -> R<()> {
    one(v, &["passed", "failed", "unknown", "unsupported"])
}
fn process(v: &J) -> R<()> {
    v.keys(&["token", "pid", "generation"])?;
    id(v.get("token")?)?;
    id(v.get("generation")?)?;
    ensure((1..=2147483647).contains(&v.get("pid")?.i()?))
}
fn unique_field(values: &[J], field: &str) -> R<()> {
    let mut seen = BTreeSet::new();
    for v in values {
        ensure(seen.insert(v.get(field)?.s()?))?;
    }
    Ok(())
}
fn target(v: &J) -> R<()> {
    v.keys(&["role", "format", "architecture", "triple"])?;
    one(v.get("role")?, &["host", "guest", "build"])?;
    one(v.get("format")?, &["mach_o", "pe", "fixture"])?;
    one(
        v.get("architecture")?,
        &["arm64", "arm64ec", "x86_64", "i386"],
    )?;
    optional(v.get("triple")?, id)?;
    let role = v.get("role")?.s()?;
    let format = v.get("format")?.s()?;
    let arch = v.get("architecture")?.s()?;
    ensure(if role == "guest" {
        ["pe", "fixture"].contains(&format) && ["x86_64", "i386", "arm64ec"].contains(&arch)
    } else {
        ["mach_o", "fixture"].contains(&format) && ["arm64", "x86_64"].contains(&arch)
    })
}
fn component(v: &J) -> R<()> {
    v.keys(&[
        "component_id",
        "role",
        "source",
        "dependencies",
        "patches",
        "build_context",
        "terms",
        "evidence",
    ])?;
    id(v.get("component_id")?)?;
    id(v.get("role")?)?;
    let s = v.get("source")?;
    knowledge(s, &["url", "immutable_ref", "content"])?;
    optional(s.get("url")?, url)?;
    optional(s.get("immutable_ref")?, immutable)?;
    optional(s.get("content")?, |v| {
        blob(v, &["source_archive_bytes", "git_tree_listing_bytes"])
    })?;
    if s.get("status")?.s()? == "known" {
        for k in ["url", "immutable_ref", "content"] {
            ensure(*s.get(k)? != J::Null)?;
        }
    }
    if *s.get("content")? != J::Null {
        let scope = if *s.get("immutable_ref")? != J::Null
            && s.get("immutable_ref")?.get("kind")?.s()? == "git_commit"
        {
            "git_tree_listing_bytes"
        } else {
            "source_archive_bytes"
        };
        blob(s.get("content")?, &[scope])?;
    }
    for k in [
        "source",
        "dependencies",
        "patches",
        "build_context",
        "terms",
    ] {
        let section = v.get(k)?;
        if section.get("status")?.s()? == "unknown" {
            ensure(!section.get("reason")?.s()?.is_empty())?;
        }
    }
    let d = v.get("dependencies")?;
    knowledge(d, &["component_ids"])?;
    ids(d.get("component_ids")?, 0)?;
    let patches = v.get("patches")?;
    knowledge(patches, &["items"])?;
    for p in array(patches.get("items")?, 0, 64)? {
        p.keys(&["base_ref", "origin", "content"])?;
        immutable(p.get("base_ref")?)?;
        url(p.get("origin")?)?;
        blob(p.get("content")?, &["patch_file_bytes"])?;
    }
    let b = v.get("build_context")?;
    knowledge(b, &["toolchain_ids", "targets", "configuration"])?;
    ids(b.get("toolchain_ids")?, 0)?;
    for t in array(b.get("targets")?, 0, 64)? {
        target(t)?;
    }
    optional(b.get("configuration")?, |v| {
        blob(v, &["build_configuration_bytes"])
    })?;
    let terms = v.get("terms")?;
    knowledge(terms, &["references"])?;
    blobs(terms.get("references")?, "file_bytes")?;
    blobs(v.get("evidence")?, "evidence_json_bytes")
}
fn profile(v: &J, version: i64) -> R<()> {
    one(v.get("store")?, &["fixture", "steam"])?;
    ensure((1..=2147483647).contains(&v.get("app_id")?.i()?))?;
    optional(v.get("game_build")?, id)?;
    for k in ["renderer", "compatibility_family"] {
        if version == 2 {
            optional(v.get(k)?, id)?;
        } else {
            id(v.get(k)?)?;
        }
    }
    let e = v.get("executable")?;
    e.keys(&["path_type", "path"])?;
    e.get("path_type")?.eqs("guest_relative")?;
    path(e.get("path")?)?;
    for a in array(v.get("arguments")?, 0, 32)? {
        ensure(a.s()?.chars().count() <= 256)?;
    }
    let env = array(v.get("environment")?, 0, 8)?;
    unique_field(env, "key")?;
    for x in env {
        x.keys(&["key", "value"])?;
        one(x.get("key")?, &["PEAR_FIXTURE_MODE", "PEAR_FIXTURE_VALUE"])?;
        ensure(x.get("value")?.s()?.chars().count() <= 256)?;
    }
    for o in array(v.get("operations")?, 0, 16)? {
        o.keys(&["operation", "root", "path", "key", "value"])?;
        o.get("operation")?.eqs("set_setting")?;
        o.get("root")?.eqs("prefix")?;
        path(o.get("path")?)?;
        match o.get("key")?.s()? {
            "fixture_flag" => {
                o.get("value")?.b()?;
            }
            "dxmt_log_level" => ensure((0..=5).contains(&o.get("value")?.i()?))?,
            _ => return Err(()),
        }
    }
    for k in ["required_checks", "required_processes"] {
        ids(v.get(k)?, 1)?;
    }
    for s in array(v.get("save_paths")?, 0, 16)? {
        s.keys(&["root", "path"])?;
        s.get("root")?.eqs("saves")?;
        path(s.get("path")?)?;
    }
    if version == 2 {
        let i = v.get("save_inventory_status")?;
        knowledge(i, &[])?;
        text(i.get("reason")?, 512)?;
        ensure(i.get("status")?.s()? == "known" || v.get("save_paths")?.a()?.is_empty())?;
        for o in array(v.get("path_observations")?, 0, 16)? {
            o.keys(&["kind", "status", "path", "reason", "evidence"])?;
            one(o.get("kind")?, &["settings", "saves"])?;
            one(o.get("status")?, &["observed", "unknown"])?;
            text(o.get("reason")?, 512)?;
            ensure(array(o.get("evidence")?, 0, 8)?.len() <= 8)?;
            blobs(o.get("evidence")?, "evidence_json_bytes")?;
            ensure((o.get("status")?.s()? == "observed") == (*o.get("path")? != J::Null))?;
            if *o.get("path")? != J::Null {
                let p = o.get("path")?;
                p.keys(&["path_type", "path"])?;
                p.get("path_type")?.eqs("windows_user_relative")?;
                path(p.get("path")?)?;
                ensure(!p.get("path")?.s()?.contains('~'))?;
                ensure(!o.get("evidence")?.a()?.is_empty())?;
            }
        }
        for p in array(v.get("provenance")?, 0, 16)? {
            p.keys(&["url", "review_date", "scope", "detail"])?;
            let url = p.get("url")?.s()?;
            ensure(
                url.starts_with("https://")
                    && url.len() <= 512
                    && !url[8..].is_empty()
                    && !url.chars().any(char::is_whitespace)
                    && !url.contains(['@', '?', '#'])
                    && !url[8..].starts_with('/'),
            )?;
            date(p.get("review_date")?.s()?)?;
            id(p.get("scope")?)?;
            text(p.get("detail")?, 512)?;
        }
        let features = array(v.get("features")?, 0, 32)?;
        unique_field(features, "feature_id")?;
        for f in features {
            f.keys(&["feature_id", "status", "evidence"])?;
            id(f.get("feature_id")?)?;
            one(
                f.get("status")?,
                &["passed", "failed", "unknown", "unsupported", "untested"],
            )?;
            array(f.get("evidence")?, 0, 8)?;
            blobs(f.get("evidence")?, "evidence_json_bytes")?;
            if ["passed", "failed"].contains(&f.get("status")?.s()?) {
                ensure(!f.get("evidence")?.a()?.is_empty())?;
            }
        }
    }
    Ok(())
}
pub fn date(s: &str) -> R<(i32, u32, u32)> {
    ensure(
        s.len() == 10
            && s.as_bytes()[4] == b'-'
            && s.as_bytes()[7] == b'-'
            && s.bytes()
                .enumerate()
                .all(|(i, c)| [4, 7].contains(&i) || c.is_ascii_digit()),
    )?;
    let y = s[..4].parse::<i32>().map_err(|_| ())?;
    let m = s[5..7].parse::<u32>().map_err(|_| ())?;
    let d = s[8..].parse::<u32>().map_err(|_| ())?;
    ensure(y > 0 && (1..=12).contains(&m))?;
    let days = [
        31,
        if y % 4 == 0 && (y % 100 != 0 || y % 400 == 0) {
            29
        } else {
            28
        },
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ];
    ensure(d > 0 && d <= days[(m - 1) as usize])?;
    Ok((y, m, d))
}
pub fn timestamp(s: &str) -> R<i64> {
    ensure(
        s.len() == 20
            && s.is_ascii()
            && s.as_bytes()[10] == b'T'
            && s.as_bytes()[13] == b':'
            && s.as_bytes()[16] == b':'
            && s.ends_with('Z'),
    )?;
    let (y, m, d) = date(&s[..10])?;
    let h = s[11..13].parse::<i32>().map_err(|_| ())?;
    let min = s[14..16].parse::<i32>().map_err(|_| ())?;
    let sec = s[17..19].parse::<i32>().map_err(|_| ())?;
    ensure((0..24).contains(&h) && (0..60).contains(&min) && (0..60).contains(&sec))?;
    let mut t: libc::tm = unsafe { std::mem::zeroed() };
    t.tm_year = y - 1900;
    t.tm_mon = m as i32 - 1;
    t.tm_mday = d as i32;
    t.tm_hour = h;
    t.tm_min = min;
    t.tm_sec = sec;
    Ok(unsafe { libc::timegm(&mut t) } as i64)
}
pub(crate) fn shape(v: &J, version: i64) -> R<()> {
    let kind = v.get("record_kind")?.s()?;
    let mut keys = vec![
        "record_kind",
        "schema_version",
        "record_context",
        "record_id",
        "disclosure",
    ];
    keys.extend(match kind {
        "runtime_lock" => vec![
            "source_inventory_ref",
            "compatibility_family",
            "component_coverage",
            "components",
            "toolchains",
            "host_requirements",
            "signing_requirements",
            "evidence",
        ],
        "runtime_artifact" => vec![
            "lock",
            "compatibility_family",
            "abi",
            "translator_component",
            "files",
            "signing",
            "build_evidence",
        ],
        "game_profile" => vec![
            "store",
            "app_id",
            "game_build",
            "executable",
            "compatibility_family",
            "renderer",
            "arguments",
            "environment",
            "operations",
            "required_checks",
            "required_processes",
            "save_paths",
        ],
        "launch" if v.get("variant")?.s()? == "request" => vec![
            "variant",
            "run_id",
            "purpose",
            "lock",
            "artifact",
            "profile",
            "qualification",
            "roots",
            "prefix_family",
            "cache_identity",
            "entry_file_id",
            "observer_required",
            "configuration",
            "signing_scope",
        ],
        "launch" => vec![
            "variant",
            "request",
            "run_id",
            "producer",
            "sequence",
            "previous",
            "event",
            "clock_id",
            "elapsed_ns",
            "process",
            "status",
            "covers",
            "ready_ack",
            "completed_exits",
        ],
        "run" => vec![
            "request",
            "run_id",
            "events",
            "failures",
            "configuration",
            "started_at",
            "processes",
            "coverage",
            "checks",
            "exit",
        ],
        "qualification" => vec![
            "runs",
            "decision",
            "reviewer",
            "required_checks",
            "configuration",
            "scope",
            "reviewed_at",
            "test_revision",
            "limitations",
        ],
        "failure" => vec![
            "request",
            "run_id",
            "category",
            "phase",
            "reason_code",
            "component_id",
            "process_token",
            "error_code",
            "evidence",
        ],
        _ => return Err(()),
    });
    if kind == "game_profile" && version == 2 {
        keys.extend([
            "save_inventory_status",
            "path_observations",
            "provenance",
            "features",
        ]);
    }
    v.keys(&keys)?;
    ensure(v.get("schema_version")?.i()? == version && [1, 2].contains(&version))?;
    id(v.get("record_id")?)?;
    one(
        v.get("record_context")?,
        &["fixture", "research", "runtime"],
    )?;
    let d = v.get("disclosure")?;
    d.keys(&["mode", "withheld", "origin_token"])?;
    one(d.get("mode")?, &["full", "public_partial"])?;
    ids(d.get("withheld")?, 0)?;
    for x in d.get("withheld")?.a()? {
        one(
            x,
            &[
                "private_launch",
                "private_evidence",
                "private_configuration",
            ],
        )?;
    }
    optional(d.get("origin_token")?, id)?;
    if d.get("mode")?.s()? == "full" {
        ensure(d.get("withheld")?.a()?.is_empty())?;
    } else {
        ensure(!d.get("withheld")?.a()?.is_empty() && *d.get("origin_token")? != J::Null)?;
    }
    match kind {
        "runtime_lock" => {
            optional(v.get("source_inventory_ref")?, |v| {
                blob(v, &["source_inventory_json_bytes"])
            })?;
            state_value(v.get("compatibility_family")?, id)?;
            state_value(v.get("host_requirements")?, host)?;
            state_value(v.get("signing_requirements")?, |v| {
                one(v, &["development", "distribution"])
            })?;
            let cv = v.get("component_coverage")?;
            knowledge(cv, &["complete"])?;
            ensure(!cv.get("complete")?.b()? || cv.get("status")?.s()? == "known")?;
            let cs = array(v.get("components")?, 1, 64)?;
            unique_field(cs, "component_id")?;
            for c in cs {
                component(c)?;
            }
            let ts = array(v.get("toolchains")?, 0, 64)?;
            unique_field(ts, "toolchain_id")?;
            for t in ts {
                t.keys(&["toolchain_id", "version", "sdk"])?;
                id(t.get("toolchain_id")?)?;
                id(t.get("version")?)?;
                id(t.get("sdk")?)?;
            }
            let names: BTreeSet<_> = cs
                .iter()
                .map(|c| c.get("component_id").unwrap().s().unwrap())
                .collect();
            let tools: BTreeSet<_> = ts
                .iter()
                .map(|t| t.get("toolchain_id").unwrap().s().unwrap())
                .collect();
            for c in cs {
                for x in c.get("dependencies")?.get("component_ids")?.a()? {
                    ensure(names.contains(x.s()?))?;
                }
                for t in c.get("build_context")?.get("toolchain_ids")?.a()? {
                    ensure(tools.contains(t.s()?))?;
                }
            }
            fn visit<'a>(
                name: &'a str,
                cs: &'a [J],
                active: &mut BTreeSet<&'a str>,
                done: &mut BTreeSet<&'a str>,
            ) -> R<()> {
                ensure(!active.contains(name))?;
                if done.contains(name) {
                    return Ok(());
                }
                active.insert(name);
                let c = cs
                    .iter()
                    .find(|c| c.get("component_id").and_then(J::s) == Ok(name))
                    .ok_or(())?;
                for d in c.get("dependencies")?.get("component_ids")?.a()? {
                    visit(d.s()?, cs, active, done)?;
                }
                active.remove(name);
                done.insert(name);
                Ok(())
            }
            for name in names {
                visit(name, cs, &mut BTreeSet::new(), &mut BTreeSet::new())?;
            }
            blobs(v.get("evidence")?, "evidence_json_bytes")?;
        }
        "runtime_artifact" => {
            reference(v.get("lock")?, "runtime_lock", version)?;
            for k in ["compatibility_family", "abi", "translator_component"] {
                id(v.get(k)?)?;
            }
            let files = array(v.get("files")?, 1, 64)?;
            unique_field(files, "file_id")?;
            let mut paths = BTreeSet::new();
            let mut hashes = BTreeSet::new();
            for f in files {
                f.keys(&["file_id", "content", "role", "format", "architecture"])?;
                id(f.get("file_id")?)?;
                blob(f.get("content")?, &["file_bytes"])?;
                ensure(paths.insert(f.get("content")?.get("path")?.s()?))?;
                hashes.insert(f.get("content")?.get("digest")?.get("value")?.s()?);
                let role = f.get("role")?.s()?;
                let fmt = f.get("format")?.s()?;
                let arch = f.get("architecture")?.s()?;
                ensure(match role {
                    "host" => {
                        ["mach_o", "fixture"].contains(&fmt)
                            && ["arm64", "x86_64", "unknown"].contains(&arch)
                    }
                    "guest" => {
                        ["pe", "fixture"].contains(&fmt)
                            && ["x86_64", "i386", "arm64ec"].contains(&arch)
                    }
                    "data" => fmt == "data" && arch == "none",
                    _ => false,
                })?;
            }
            let sign = v.get("signing")?;
            sign.keys(&["status", "scope", "payload_digests", "evidence"])?;
            status(sign.get("status")?)?;
            one(
                sign.get("scope")?,
                &["development", "distribution", "unknown"],
            )?;
            optional(sign.get("evidence")?, |v| blob(v, &["evidence_json_bytes"]))?;
            let mut signed = BTreeSet::new();
            for h in array(sign.get("payload_digests")?, 0, 64)? {
                ensure(signed.insert(digest_value(h)?))?;
            }
            if sign.get("status")?.s()? == "passed" {
                ensure(signed == hashes && *sign.get("evidence")? != J::Null)?;
            }
            blobs(v.get("build_evidence")?, "evidence_json_bytes")?;
        }
        "game_profile" => {
            profile(v, version)?;
            if d.get("mode")?.s()? == "public_partial" {
                for key in ["arguments", "environment", "save_paths"] {
                    ensure(v.get(key)?.a()?.is_empty())?;
                }
            }
        }
        "launch" if v.get("variant")?.s()? == "request" => {
            id(v.get("run_id")?)?;
            one(
                v.get("purpose")?,
                &["fixture_launch", "qualification_run", "supported_launch"],
            )?;
            for (k, kind) in [
                ("lock", "runtime_lock"),
                ("artifact", "runtime_artifact"),
                ("profile", "game_profile"),
                ("qualification", "qualification"),
            ] {
                optional(v.get(k)?, |v| reference(v, kind, version))?;
            }
            let roots = v.get("roots")?;
            roots.keys(&["runtime", "prefix", "saves", "cache", "logs"])?;
            let mut paths: Vec<String> = Vec::new();
            for k in ["runtime", "prefix", "saves", "cache", "logs"] {
                path(roots.get(k)?)?;
                let p = roots.get(k)?.s()?;
                ensure(p.is_ascii())?;
                let folded = p.to_ascii_lowercase();
                for other in &paths {
                    ensure(!overlaps(&folded, other))?;
                }
                paths.push(folded);
            }
            optional(v.get("prefix_family")?, id)?;
            id(v.get("entry_file_id")?)?;
            v.get("observer_required")?.b()?;
            one(v.get("signing_scope")?, &["development", "distribution"])?;
            configuration(v.get("configuration")?)?;
            let cache = v.get("cache_identity")?;
            cache.keys(&[
                "lock_digest",
                "artifact_digest",
                "profile_digest",
                "cpu_features",
                "translator_component",
                "abi",
            ])?;
            for k in ["lock_digest", "artifact_digest", "profile_digest"] {
                digest_value(cache.get(k)?)?;
            }
            ids(cache.get("cpu_features")?, 0)?;
            id(cache.get("translator_component")?)?;
            id(cache.get("abi")?)?;
        }
        "launch" => {
            v.get("variant")?.eqs("event")?;
            reference(v.get("request")?, "launch", version)?;
            for k in ["run_id", "clock_id"] {
                id(v.get(k)?)?;
            }
            one(v.get("producer")?, &["supervisor", "observer"])?;
            for k in ["sequence", "elapsed_ns"] {
                ensure(v.get(k)?.i()? >= 0)?;
            }
            optional(v.get("previous")?, |v| reference(v, "launch", version))?;
            one(
                v.get("event")?,
                &[
                    "observer_ready",
                    "spawned",
                    "exited",
                    "observer_complete",
                    "gap",
                ],
            )?;
            optional(v.get("process")?, process)?;
            status(v.get("status")?)?;
            ids(v.get("covers")?, 0)?;
            optional(v.get("ready_ack")?, |v| reference(v, "launch", version))?;
            refs(v.get("completed_exits")?, "launch", version, 0)?;
        }
        "run" => {
            optional(v.get("request")?, |v| reference(v, "launch", version))?;
            id(v.get("run_id")?)?;
            refs(v.get("events")?, "launch", version, 0)?;
            refs(v.get("failures")?, "failure", version, 0)?;
            configuration(v.get("configuration")?)?;
            timestamp(v.get("started_at")?.s()?)?;
            let mut tokens = BTreeSet::new();
            let mut generations = BTreeSet::new();
            for p in array(v.get("processes")?, 0, 64)? {
                p.keys(&[
                    "identity",
                    "purpose",
                    "required",
                    "observed",
                    "host_architecture",
                    "translated",
                    "modules",
                ])?;
                process(p.get("identity")?)?;
                let pi = p.get("identity")?;
                ensure(
                    tokens.insert(pi.get("token")?.s()?)
                        && generations.insert((pi.get("pid")?.i()?, pi.get("generation")?.s()?)),
                )?;
                id(p.get("purpose")?)?;
                p.get("required")?.b()?;
                p.get("observed")?.b()?;
                one(p.get("host_architecture")?, &["arm64", "x86_64", "unknown"])?;
                optional(p.get("translated")?, |v| v.b().map(|_| ()))?;
                let modules = array(p.get("modules")?, 0, 64)?;
                unique_field(modules, "module_id")?;
                for m in modules {
                    m.keys(&[
                        "module_id",
                        "kind",
                        "architecture",
                        "observed",
                        "source",
                        "artifact_file_id",
                        "observed_sha256",
                        "evidence",
                        "content",
                    ])?;
                    id(m.get("module_id")?)?;
                    one(m.get("kind")?, &["host", "guest"])?;
                    one(
                        m.get("architecture")?,
                        &["arm64", "arm64ec", "x86_64", "i386", "unknown"],
                    )?;
                    m.get("observed")?.b()?;
                    one(m.get("source")?, &["artifact", "system", "game"])?;
                    optional(m.get("artifact_file_id")?, id)?;
                    optional(m.get("observed_sha256")?, |v| digest_value(v).map(|_| ()))?;
                    blobs(m.get("evidence")?, "evidence_json_bytes")?;
                    optional(m.get("content")?, |v| {
                        blob(
                            v,
                            &[
                                "file_bytes",
                                "evidence_json_bytes",
                                "source_archive_bytes",
                                "git_tree_listing_bytes",
                                "patch_file_bytes",
                                "build_configuration_bytes",
                                "source_inventory_json_bytes",
                            ],
                        )
                    })?;
                    if m.get("source")?.s()? == "artifact" {
                        ensure(*m.get("artifact_file_id")? != J::Null)?;
                    } else {
                        ensure(
                            *m.get("artifact_file_id")? == J::Null
                                && *m.get("content")? == J::Null
                                && ((m.get("source")?.s()? == "system"
                                    && m.get("kind")?.s()? == "host")
                                    || (m.get("source")?.s()? == "game"
                                        && m.get("kind")?.s()? == "guest")),
                        )?;
                    }
                }
            }
            let cov = v.get("coverage")?;
            cov.keys(&[
                "status",
                "required_processes",
                "missing_processes",
                "missing_modules",
                "dropped_events",
            ])?;
            status(cov.get("status")?)?;
            for k in ["required_processes", "missing_processes", "missing_modules"] {
                ids(cov.get(k)?, 0)?;
            }
            ensure(cov.get("dropped_events")?.i()? >= 0)?;
            let checks = array(v.get("checks")?, 0, 64)?;
            unique_field(checks, "check_id")?;
            for c in checks {
                c.keys(&["check_id", "status", "evidence"])?;
                id(c.get("check_id")?)?;
                status(c.get("status")?)?;
                blobs(c.get("evidence")?, "evidence_json_bytes")?;
            }
            let e = v.get("exit")?;
            e.keys(&["kind", "code", "signal", "cleanup"])?;
            status(e.get("cleanup")?)?;
            optional(e.get("code")?, |v| ensure((0..=255).contains(&v.i()?)))?;
            optional(e.get("signal")?, |v| ensure((1..=127).contains(&v.i()?)))?;
            ensure(match e.get("kind")?.s()? {
                "exited" => *e.get("code")? != J::Null && *e.get("signal")? == J::Null,
                "signaled" => *e.get("code")? == J::Null && *e.get("signal")? != J::Null,
                "timeout" | "unknown" => *e.get("code")? == J::Null && *e.get("signal")? == J::Null,
                _ => false,
            })?;
        }
        "qualification" => {
            refs(v.get("runs")?, "run", version, 1)?;
            one(v.get("decision")?, &["supported", "failed", "unknown"])?;
            for k in ["reviewer", "test_revision"] {
                id(v.get(k)?)?;
            }
            ids(v.get("required_checks")?, 1)?;
            configuration(v.get("configuration")?)?;
            one(v.get("scope")?, &["development", "distribution"])?;
            timestamp(v.get("reviewed_at")?.s()?)?;
            for l in array(v.get("limitations")?, 0, 64)? {
                id(l)?;
            }
        }
        "failure" => {
            optional(v.get("request")?, |v| reference(v, "launch", version))?;
            optional(v.get("run_id")?, id)?;
            one(
                v.get("category")?,
                &[
                    "contract_validation",
                    "source_build",
                    "host_capability",
                    "signing",
                    "supervision",
                    "observation",
                    "cpu_translation",
                    "windows_api",
                    "graphics",
                    "steam_integration",
                    "game_behavior",
                    "unknown",
                ],
            )?;
            for k in ["phase", "reason_code"] {
                id(v.get(k)?)?;
            }
            for k in ["component_id", "process_token"] {
                optional(v.get(k)?, id)?;
            }
            optional(v.get("error_code")?, |v| {
                ensure((-2147483648..=2147483647).contains(&v.i()?))
            })?;
            blobs(v.get("evidence")?, "evidence_json_bytes")?;
        }
        _ => return Err(()),
    }
    Ok(())
}
pub fn overlaps(a: &str, b: &str) -> bool {
    a == b
        || a.strip_prefix(b).is_some_and(|x| x.starts_with('/'))
        || b.strip_prefix(a).is_some_and(|x| x.starts_with('/'))
}

pub struct Bundle {
    pub root: Root,
    pub version: i64,
    pub context: String,
    pub records: BTreeMap<String, J>,
    pub hashes: BTreeMap<String, String>,
    pub blobs: BTreeMap<String, String>,
    active: BTreeSet<String>,
    ids: BTreeSet<String>,
    aliases: BTreeMap<(u64, u64), (String, bool)>,
    record_bytes: u64,
    blob_bytes: u64,
}
impl Bundle {
    pub fn inspect(root: Root, entry: &str, context: &str) -> Result<Self> {
        require(
            ["research", "fixture", "runtime"].contains(&context),
            "invalid_context",
        )?;
        let mut b = Self {
            root,
            version: 0,
            context: context.into(),
            records: BTreeMap::new(),
            hashes: BTreeMap::new(),
            blobs: BTreeMap::new(),
            active: BTreeSet::new(),
            ids: BTreeSet::new(),
            aliases: BTreeMap::new(),
            record_bytes: 0,
            blob_bytes: 0,
        };
        b.load(entry)?;
        b.semantics()?;
        Ok(b)
    }
    fn alias(&mut self, path: &str, device: u64, inode: u64, record: bool) -> Result<()> {
        if let Some(old) = self.aliases.get(&(device, inode)) {
            require(old == &(path.into(), record), "file_alias")?;
        } else {
            self.aliases.insert((device, inode), (path.into(), record));
        }
        Ok(())
    }
    fn load(&mut self, path: &str) -> Result<()> {
        require(!self.active.contains(path), "reference_cycle")?;
        if self.records.contains_key(path) {
            return Ok(());
        }
        require(
            self.records.len() + self.active.len() < 128,
            "record_count_limit",
        )?;
        self.active.insert(path.into());
        let (data, hash, identity) = self
            .root
            .read_record(path, 4 * 1024 * 1024 - self.record_bytes)?;
        self.record_bytes += data.len() as u64;
        self.alias(path, identity.device, identity.inode, true)?;
        let v = parse(&data)?;
        let version = v.get("schema_version")?.i()?;
        require([1, 2].contains(&version), "unsupported_schema_version")?;
        if self.version == 0 {
            self.version = version;
        }
        require(version == self.version, "mixed_versions")?;
        shape(&v, version)?;
        require(
            v.get("record_context")?.s()? == self.context,
            "context_mismatch",
        )?;
        require(
            self.ids.insert(v.get("record_id")?.s()?.into()),
            "duplicate_identity",
        )?;
        self.walk(&v, &mut 0)?;
        self.active.remove(path);
        self.hashes.insert(path.into(), hash);
        self.records.insert(path.into(), v);
        Ok(())
    }
    fn walk(&mut self, v: &J, count: &mut usize) -> Result<()> {
        match v {
            J::Obj(o) if o.contains_key("ref_type") => {
                *count += 1;
                require(*count <= 64, "reference_count_limit")?;
                let path = v.get("path")?.s()?;
                let record = v.get("ref_type")?.s()? == "record";
                if record {
                    self.load(path)?;
                    let target = &self.records[path];
                    require(
                        target.get("record_kind")? == v.get("record_kind")?
                            && target.get("schema_version")? == v.get("schema_version")?,
                        "reference_kind_mismatch",
                    )?;
                    require(
                        self.hashes[path] == v.get("digest")?.get("value")?.s()?,
                        "digest_mismatch",
                    )?;
                } else {
                    if !self.blobs.contains_key(path) {
                        let file = self.root.open_file(path)?;
                        let m = file.metadata()?;
                        self.alias(path, m.dev(), m.ino(), false)?;
                        let (limit, total) = if self.version == 1 {
                            (64 * 1024 * 1024, 256 * 1024 * 1024)
                        } else {
                            (8 * 1024 * 1024 * 1024, 64 * 1024 * 1024 * 1024)
                        };
                        require(
                            m.len() <= limit && m.len() <= total - self.blob_bytes,
                            "blob_size_limit",
                        )?;
                        let (hash, bytes) =
                            native::sha256(&file, limit.min(total - self.blob_bytes))?;
                        self.blob_bytes += bytes;
                        self.blobs.insert(path.into(), fs::hex(&hash));
                    }
                    require(
                        self.blobs[path] == v.get("digest")?.get("value")?.s()?,
                        "digest_mismatch",
                    )?;
                }
            }
            J::Obj(o) => {
                for x in o.values() {
                    self.walk(x, count)?;
                }
            }
            J::Arr(a) => {
                for x in a {
                    self.walk(x, count)?;
                }
            }
            _ => (),
        }
        Ok(())
    }
    pub fn target<'a>(&'a self, r: &J, kind: &str) -> Result<&'a J> {
        require(
            r.get("record_kind")?.s()? == kind,
            "reference_kind_mismatch",
        )?;
        self.records
            .get(r.get("path")?.s()?)
            .ok_or_else(|| Error::code("missing_reference"))
    }
    pub fn request(&self, entry: &str) -> Result<&J> {
        let q = self
            .records
            .get(entry)
            .ok_or_else(|| Error::code("missing_request"))?;
        require(
            q.get("record_kind")?.s()? == "launch" && q.get("variant")?.s()? == "request",
            "wrong_entry_kind",
        )?;
        Ok(q)
    }
    fn semantics(&self) -> Result<()> {
        for v in self.records.values() {
            match v.get("record_kind")?.s()? {
                "runtime_artifact" => {
                    let l = self.target(v.get("lock")?, "runtime_lock")?;
                    let family = l.get("compatibility_family")?.get("value")?;
                    require(
                        *family == J::Null || family == v.get("compatibility_family")?,
                        "incompatible_family",
                    )?;
                    require(
                        l.get("components")?
                            .a()?
                            .iter()
                            .any(|c| c.get("component_id") == v.get("translator_component")),
                        "unknown_component",
                    )?;
                }
                "launch" if v.get("variant")?.s()? == "request" => {
                    match self.root.directory(v.get("roots")?.get("runtime")?.s()?) {
                        Ok(_) => (),
                        Err(e) if e.errno == Some(libc::ENOENT) => (),
                        Err(e) => return Err(e),
                    }
                    for root in ["prefix", "saves", "cache", "logs"] {
                        let p = v.get("roots")?.get(root)?.s()?.to_ascii_lowercase();
                        for imm in self.hashes.keys().chain(self.blobs.keys()) {
                            require(
                                !overlaps(&p, &imm.to_ascii_lowercase()),
                                "immutable_path_overlap",
                            )?;
                        }
                        match self.root.directory(v.get("roots")?.get(root)?.s()?) {
                            Ok(f) => {
                                let m = f.metadata()?;
                                require(
                                    !self.aliases.contains_key(&(m.dev(), m.ino())),
                                    "immutable_path_overlap",
                                )?;
                                fs::check_mutable(f, &self.aliases.keys().copied().collect())?;
                            }
                            Err(e) if e.errno == Some(libc::ENOENT) => (),
                            Err(e) => return Err(e),
                        }
                    }
                    if ["lock", "artifact", "profile"]
                        .iter()
                        .all(|k| v.get(k).is_ok_and(|x| *x != J::Null))
                    {
                        let a = self.target(v.get("artifact")?, "runtime_artifact")?;
                        let p = self.target(v.get("profile")?, "game_profile")?;
                        require(
                            a.get("lock")?.get("digest")? == v.get("lock")?.get("digest")?,
                            "lock_mismatch",
                        )?;
                        require(
                            p.get("compatibility_family")? == a.get("compatibility_family")?
                                && (*v.get("prefix_family")? == J::Null
                                    || v.get("prefix_family")? == a.get("compatibility_family")?),
                            "incompatible_family",
                        )?;
                        let c = v.get("cache_identity")?;
                        for k in ["lock", "artifact", "profile"] {
                            require(
                                c.get(&format!("{k}_digest"))?
                                    == v.get(k)?.get("digest")?.get("value")?,
                                "cache_identity_mismatch",
                            )?;
                        }
                        for k in ["abi", "translator_component"] {
                            require(c.get(k)? == a.get(k)?, "cache_identity_mismatch")?;
                        }
                        require(
                            string_set(c.get("cpu_features")?)?
                                == string_set(
                                    v.get("configuration")?.get("host")?.get("capabilities")?,
                                )?,
                            "cache_identity_mismatch",
                        )?;
                        require(
                            a.get("files")?.a()?.iter().any(|f| {
                                f.get("file_id") == v.get("entry_file_id")
                                    && f.get("role").and_then(J::s) == Ok("host")
                            }),
                            "invalid_entry_file",
                        )?;
                        let cfg = v.get("configuration")?;
                        require(
                            cfg.get("renderer")? == p.get("renderer")?
                                && cfg.get("game_build")? == p.get("game_build")?
                                && cfg.get("translator")? == a.get("translator_component")?,
                            "configuration_mismatch",
                        )?;
                    }
                }
                "launch" => self.event_semantics(v)?,
                "run" => {
                    if *v.get("request")? != J::Null {
                        let q = self.target(v.get("request")?, "launch")?;
                        require(
                            q.get("variant")?.s()? == "request"
                                && q.get("run_id")? == v.get("run_id")?
                                && q.get("configuration")? == v.get("configuration")?,
                            "run_identity_mismatch",
                        )?;
                    } else {
                        require(
                            v.get("disclosure")?.get("mode")?.s()? == "public_partial"
                                && string_set(v.get("disclosure")?.get("withheld")?)?
                                    .contains("private_launch"),
                            "missing_request",
                        )?;
                    }
                    let mut paths = BTreeSet::new();
                    for e in v.get("events")?.a()? {
                        require(paths.insert(e.get("path")?.s()?), "duplicate_identity")?;
                        let event = self.target(e, "launch")?;
                        require(
                            event.get("variant")?.s()? == "event"
                                && *v.get("request")? != J::Null
                                && event.get("request")?.get("digest")?
                                    == v.get("request")?.get("digest")?,
                            "run_identity_mismatch",
                        )?;
                    }
                    for f in v.get("failures")?.a()? {
                        let f = self.target(f, "failure")?;
                        require(
                            f.get("run_id")? == v.get("run_id")?
                                && f.get("request")? == v.get("request")?,
                            "run_identity_mismatch",
                        )?;
                    }
                }
                "qualification" => {
                    let mut paths = BTreeSet::new();
                    for r in v.get("runs")?.a()? {
                        require(paths.insert(r.get("path")?.s()?), "duplicate_identity")?;
                        require(
                            self.target(r, "run")?.get("configuration")?
                                == v.get("configuration")?,
                            "configuration_mismatch",
                        )?;
                    }
                }
                "failure" => {
                    if *v.get("request")? != J::Null {
                        require(
                            self.target(v.get("request")?, "launch")?.get("run_id")?
                                == v.get("run_id")?,
                            "run_identity_mismatch",
                        )?;
                    }
                }
                _ => (),
            }
        }
        Ok(())
    }
    fn event_semantics(&self, v: &J) -> Result<()> {
        let q = self.target(v.get("request")?, "launch")?;
        require(
            q.get("variant")?.s()? == "request" && v.get("run_id")? == q.get("run_id")?,
            "run_identity_mismatch",
        )?;
        let observer = v.get("producer")?.s()? == "observer";
        let event = v.get("event")?.s()?;
        require(
            if observer {
                ["observer_ready", "observer_complete", "gap"].contains(&event)
                    && *v.get("process")? == J::Null
            } else {
                ["spawned", "exited", "gap"].contains(&event)
                    && (event == "gap" || *v.get("process")? != J::Null)
            },
            "event_ownership",
        )?;
        if *v.get("ready_ack")? != J::Null {
            let r = self.target(v.get("ready_ack")?, "launch")?;
            require(
                event == "spawned"
                    && r.get("event")?.s()? == "observer_ready"
                    && r.get("request")?.get("digest")? == v.get("request")?.get("digest")?,
                "invalid_ready_ack",
            )?;
        }
        let mut exits = BTreeSet::new();
        for r in v.get("completed_exits")?.a()? {
            require(exits.insert(r.get("path")?.s()?), "duplicate_identity")?;
            let e = self.target(r, "launch")?;
            require(
                event == "observer_complete"
                    && e.get("event")?.s()? == "exited"
                    && e.get("request")?.get("digest")? == v.get("request")?.get("digest")?,
                "invalid_completion_basis",
            )?;
        }
        if *v.get("previous")? == J::Null {
            require(v.get("sequence")?.i()? == 0, "event_sequence")?;
        } else {
            let p = self.target(v.get("previous")?, "launch")?;
            require(
                p.get("producer")? == v.get("producer")?
                    && p.get("request")?.get("digest")? == v.get("request")?.get("digest")?
                    && p.get("sequence")?.i()? + 1 == v.get("sequence")?.i()?
                    && p.get("clock_id")? == v.get("clock_id")?
                    && p.get("elapsed_ns")?.i()? <= v.get("elapsed_ns")?.i()?,
                "event_sequence",
            )?;
        }
        Ok(())
    }
}
pub fn string_set(v: &J) -> R<BTreeSet<&str>> {
    v.a()?.iter().map(J::s).collect()
}
