use crate::json::{ensure, parse, J, R};
use std::collections::{BTreeMap, BTreeSet};
use std::ffi::CString;
use std::fs::File;
use std::io::Read;
use std::os::fd::{AsRawFd, FromRawFd};
use std::os::unix::fs::MetadataExt;
use std::path::PathBuf;

unsafe extern "C" {
    fn CC_SHA256(data: *const libc::c_void, len: libc::c_uint, digest: *mut u8) -> *mut u8;
}
pub fn sha(data: &[u8]) -> String {
    let mut out = [0u8; 32];
    unsafe {
        CC_SHA256(data.as_ptr().cast(), data.len() as u32, out.as_mut_ptr());
    }
    out.iter().map(|b| format!("{b:02x}")).collect()
}
fn c(s: &str) -> R<CString> {
    CString::new(s).map_err(|_| ())
}
fn relative(s: &str) -> R<()> {
    ensure(
        !s.is_empty()
            && s.len() <= 512
            && !s.starts_with('/')
            && !s.starts_with('~')
            && !s.contains('%')
            && !s.contains('\\')
            && !s.contains(':')
            && !s.chars().any(|c| c <= '\u{1f}' || c == '\u{7f}'),
    )?;
    ensure(
        s.split('/').count() <= 32 && s.split('/').all(|p| !p.is_empty() && p != "." && p != ".."),
    )
}
fn text(v: &J) -> R<()> {
    v.text()
}
fn empty(v: &J) -> R<()> {
    ensure(v.a()?.is_empty())
}
fn null(v: &J) -> R<()> {
    ensure(*v == J::Null)
}
fn strings(v: &J) -> R<()> {
    ensure(v.a()?.len() <= 64)?;
    for x in v.a()? {
        text(x)?;
    }
    Ok(())
}
fn eq(v: &J, s: &str) -> R<()> {
    v.eqs(s)
}
fn digest(v: &J, scope: &str) -> R<()> {
    v.keys(&["algorithm", "scope", "value"])?;
    eq(v.get("algorithm")?, "sha256")?;
    eq(v.get("scope")?, scope)?;
    let s = v.get("value")?.s()?;
    ensure(
        s.len() == 64
            && s.bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b)),
    )
}
fn blob(v: &J, scope: &str) -> R<()> {
    v.keys(&["ref_type", "path", "digest"])?;
    eq(v.get("ref_type")?, "blob")?;
    relative(v.get("path")?.s()?)?;
    digest(v.get("digest")?, scope)
}
fn blobs(v: &J, scope: &str) -> R<()> {
    ensure(!v.a()?.is_empty() && v.a()?.len() <= 64)?;
    for x in v.a()? {
        blob(x, scope)?;
    }
    Ok(())
}
fn reference(v: &J, kind: &str) -> R<()> {
    v.keys(&[
        "ref_type",
        "path",
        "record_kind",
        "schema_version",
        "digest",
    ])?;
    eq(v.get("ref_type")?, "record")?;
    eq(v.get("record_kind")?, kind)?;
    ensure(v.get("schema_version")?.i()? == 1)?;
    relative(v.get("path")?.s()?)?;
    digest(v.get("digest")?, "exact_utf8_file_bytes")
}
fn host(v: &J) -> R<()> {
    v.keys(&["os", "architecture", "version", "capabilities"])?;
    eq(v.get("os")?, "macos")?;
    eq(v.get("architecture")?, "arm64")?;
    ensure(v.get("version")?.a()? == [J::Int(26), J::Int(0), J::Int(0)])?;
    ensure(v.get("capabilities")?.a()? == [J::Str("fixture-capability".into())])
}
fn state(v: &J, fields: &[&str]) -> R<()> {
    let mut k = vec!["status", "reason"];
    k.extend(fields);
    v.keys(&k)?;
    eq(v.get("status")?, "known")?;
    text(v.get("reason")?)
}
fn shape(v: &J) -> R<()> {
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
        "launch" => vec![
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
        _ => return Err(()),
    });
    v.keys(&keys)?;
    ensure(v.get("schema_version")?.i()? == 1)?;
    eq(
        v.get("record_id")?,
        match kind {
            "runtime_lock" => "fixture.lock",
            "runtime_artifact" => "fixture.artifact",
            "game_profile" => "fixture.profile",
            "launch" => "fixture.request",
            _ => return Err(()),
        },
    )?;
    let d = v.get("disclosure")?;
    d.keys(&["mode", "withheld", "origin_token"])?;
    strings(d.get("withheld")?)?;
    match d.get("mode")?.s()? {
        "full" => {
            empty(d.get("withheld")?)?;
            null(d.get("origin_token")?)?;
        }
        "public_partial" => {
            ensure(!d.get("withheld")?.a()?.is_empty())?;
            let token = d.get("origin_token")?.s()?;
            ensure(
                !token.is_empty()
                    && token.len() <= 96
                    && token
                        .bytes()
                        .next()
                        .is_some_and(|c| c.is_ascii_alphanumeric())
                    && token
                        .bytes()
                        .all(|c| c.is_ascii_alphanumeric() || b"_.-".contains(&c)),
            )?;
            for x in d.get("withheld")?.a()? {
                ensure(
                    [
                        "private_launch",
                        "private_evidence",
                        "private_configuration",
                    ]
                    .contains(&x.s()?),
                )?;
            }
        }
        _ => return Err(()),
    }
    ensure(["fixture", "runtime", "research"].contains(&v.get("record_context")?.s()?))?;
    match kind {
        "runtime_lock" => {
            null(v.get("source_inventory_ref")?)?;
            let f = v.get("compatibility_family")?;
            state(f, &["value"])?;
            eq(f.get("value")?, "fixture-family")?;
            let cv = v.get("component_coverage")?;
            state(cv, &["complete"])?;
            ensure(cv.get("complete")?.b()?)?;
            let cs = v.get("components")?.a()?;
            ensure(cs.len() == 1)?;
            let x = &cs[0];
            x.keys(&[
                "component_id",
                "role",
                "source",
                "dependencies",
                "patches",
                "build_context",
                "terms",
                "evidence",
            ])?;
            eq(x.get("component_id")?, "fixture-translator")?;
            eq(x.get("role")?, "fixture")?;
            let s = x.get("source")?;
            state(s, &["url", "immutable_ref", "content"])?;
            eq(s.get("url")?, "https://pear.invalid/self-owned-fixture")?;
            let r = s.get("immutable_ref")?;
            r.keys(&["kind", "object_format", "value"])?;
            eq(r.get("kind")?, "archive")?;
            null(r.get("object_format")?)?;
            null(r.get("value")?)?;
            blob(s.get("content")?, "source_archive_bytes")?;
            let dp = x.get("dependencies")?;
            state(dp, &["component_ids"])?;
            empty(dp.get("component_ids")?)?;
            let p = x.get("patches")?;
            state(p, &["items"])?;
            empty(p.get("items")?)?;
            let b = x.get("build_context")?;
            state(b, &["toolchain_ids", "targets", "configuration"])?;
            ensure(b.get("toolchain_ids")?.a()? == [J::Str("fixture-toolchain".into())])?;
            let ts = b.get("targets")?.a()?;
            ensure(ts.len() == 1)?;
            ts[0].keys(&["role", "format", "architecture", "triple"])?;
            eq(ts[0].get("role")?, "host")?;
            eq(ts[0].get("format")?, "mach_o")?;
            eq(ts[0].get("architecture")?, "arm64")?;
            eq(ts[0].get("triple")?, "arm64-apple-macosx26.0")?;
            blob(b.get("configuration")?, "build_configuration_bytes")?;
            let t = x.get("terms")?;
            state(t, &["references"])?;
            blobs(t.get("references")?, "file_bytes")?;
            blobs(x.get("evidence")?, "evidence_json_bytes")?;
            let ts = v.get("toolchains")?.a()?;
            ensure(ts.len() == 1)?;
            ts[0].keys(&["toolchain_id", "version", "sdk"])?;
            eq(ts[0].get("toolchain_id")?, "fixture-toolchain")?;
            text(ts[0].get("version")?)?;
            text(ts[0].get("sdk")?)?;
            let h = v.get("host_requirements")?;
            state(h, &["value"])?;
            host(h.get("value")?)?;
            let s = v.get("signing_requirements")?;
            state(s, &["value"])?;
            eq(s.get("value")?, "development")?;
            blobs(v.get("evidence")?, "evidence_json_bytes")?;
        }
        "runtime_artifact" => {
            reference(v.get("lock")?, "runtime_lock")?;
            eq(v.get("compatibility_family")?, "fixture-family")?;
            eq(v.get("abi")?, "fixture-abi")?;
            eq(v.get("translator_component")?, "fixture-translator")?;
            let fs = v.get("files")?.a()?;
            ensure(fs.len() == 1)?;
            let f = &fs[0];
            f.keys(&["file_id", "content", "role", "format", "architecture"])?;
            eq(f.get("file_id")?, "fixture-main")?;
            blob(f.get("content")?, "file_bytes")?;
            eq(f.get("content")?.get("path")?, "blobs/fixture-child")?;
            eq(f.get("role")?, "host")?;
            eq(f.get("format")?, "mach_o")?;
            eq(f.get("architecture")?, "arm64")?;
            let s = v.get("signing")?;
            s.keys(&["status", "scope", "payload_digests", "evidence"])?;
            eq(s.get("status")?, "passed")?;
            eq(s.get("scope")?, "development")?;
            ensure(
                s.get("payload_digests")?.a()?
                    == [f.get("content")?.get("digest")?.get("value")?.clone()],
            )?;
            blob(s.get("evidence")?, "evidence_json_bytes")?;
            blobs(v.get("build_evidence")?, "evidence_json_bytes")?;
        }
        "game_profile" => {
            eq(v.get("store")?, "fixture")?;
            ensure(v.get("app_id")?.i()? == 1)?;
            eq(v.get("game_build")?, "fixture-game")?;
            eq(v.get("compatibility_family")?, "fixture-family")?;
            eq(v.get("renderer")?, "fixture-renderer")?;
            let x = v.get("executable")?;
            x.keys(&["path_type", "path"])?;
            eq(x.get("path_type")?, "guest_relative")?;
            eq(x.get("path")?, "fixture.exe")?;
            let a = v.get("arguments")?.a()?;
            ensure(!a.is_empty())?;
            let mode = a[0].s()?;
            ensure(
                [
                    "success",
                    "args",
                    "environment",
                    "stdin",
                    "nonzero",
                    "signal",
                    "delay",
                    "excess_stdout",
                    "excess_stderr",
                    "malformed",
                    "secret",
                    "descendant_pipe",
                ]
                .contains(&mode),
            )?;
            if mode == "args" {
                ensure(
                    a == [
                        J::Str("args".into()),
                        J::Str("value with spaces".into()),
                        J::Str("Unicode-λ-🍐".into()),
                    ],
                )?;
            } else {
                ensure(a.len() == 1)?;
            }
            let e = v.get("environment")?.a()?;
            ensure(e.len() == if mode == "environment" { 1 } else { 0 })?;
            if let Some(e) = e.first() {
                e.keys(&["key", "value"])?;
                eq(e.get("key")?, "PEAR_FIXTURE_VALUE")?;
                eq(e.get("value")?, "allowed")?;
            }
            empty(v.get("operations")?)?;
            ensure(v.get("required_checks")?.a()? == [J::Str("fixture-check".into())])?;
            ensure(v.get("required_processes")?.a()? == [J::Str("game".into())])?;
            let saves = v.get("save_paths")?.a()?;
            ensure(saves.len() == 1)?;
            saves[0].keys(&["root", "path"])?;
            eq(saves[0].get("root")?, "saves")?;
            eq(saves[0].get("path")?, "game/save.dat")?;
        }
        "launch" => {
            eq(v.get("variant")?, "request")?;
            eq(v.get("run_id")?, "fixture-run")?;
            ensure(
                ["fixture_launch", "qualification_run", "supported_launch"]
                    .contains(&v.get("purpose")?.s()?),
            )?;
            reference(v.get("lock")?, "runtime_lock")?;
            reference(v.get("artifact")?, "runtime_artifact")?;
            reference(v.get("profile")?, "game_profile")?;
            null(v.get("qualification")?)?;
            let roots = v.get("roots")?;
            roots.keys(&["runtime", "prefix", "saves", "cache", "logs"])?;
            for k in ["runtime", "prefix", "saves", "cache", "logs"] {
                eq(roots.get(k)?, &format!("state/{k}"))?;
            }
            eq(v.get("prefix_family")?, "fixture-family")?;
            let cache = v.get("cache_identity")?;
            cache.keys(&[
                "lock_digest",
                "artifact_digest",
                "profile_digest",
                "cpu_features",
                "translator_component",
                "abi",
            ])?;
            for k in ["lock", "artifact", "profile"] {
                ensure(
                    cache.get(&format!("{k}_digest"))? == v.get(k)?.get("digest")?.get("value")?,
                )?;
            }
            ensure(cache.get("cpu_features")?.a()? == [J::Str("fixture-capability".into())])?;
            eq(cache.get("translator_component")?, "fixture-translator")?;
            eq(cache.get("abi")?, "fixture-abi")?;
            eq(v.get("entry_file_id")?, "fixture-main")?;
            ensure(v.get("observer_required")?.b()?)?;
            let cfg = v.get("configuration")?;
            cfg.keys(&[
                "host",
                "chip",
                "game_build",
                "steam_build",
                "renderer",
                "translator",
            ])?;
            host(cfg.get("host")?)?;
            eq(cfg.get("chip")?, "synthetic-arm64")?;
            eq(cfg.get("game_build")?, "fixture-game")?;
            eq(cfg.get("steam_build")?, "fixture-steam")?;
            eq(cfg.get("renderer")?, "fixture-renderer")?;
            eq(cfg.get("translator")?, "fixture-translator")?;
            eq(v.get("signing_scope")?, "development")?;
        }
        _ => return Err(()),
    }
    Ok(())
}

pub struct Bundle {
    root: File,
    pub path: PathBuf,
    records: BTreeMap<String, J>,
    bytes: BTreeMap<String, Vec<u8>>,
    active: BTreeSet<String>,
    aliases: BTreeMap<(u64, u64), String>,
    ids: BTreeSet<String>,
    record_bytes: usize,
    blob_bytes: usize,
    pub eligible: bool,
}
impl Bundle {
    pub fn new(path: &str) -> R<Self> {
        ensure(path.starts_with('/') && !path.ends_with('/') && path.len() <= 4096)?;
        let fd = unsafe {
            libc::open(
                c("/")?.as_ptr(),
                libc::O_RDONLY | libc::O_DIRECTORY | libc::O_CLOEXEC,
            )
        };
        ensure(fd >= 0)?;
        let mut f = unsafe { File::from_raw_fd(fd) };
        for part in path[1..].split('/') {
            relative(part)?;
            let fd = unsafe {
                libc::openat(
                    f.as_raw_fd(),
                    c(part)?.as_ptr(),
                    libc::O_RDONLY | libc::O_DIRECTORY | libc::O_NOFOLLOW | libc::O_CLOEXEC,
                )
            };
            ensure(fd >= 0)?;
            f = unsafe { File::from_raw_fd(fd) };
        }
        Ok(Self {
            root: f,
            path: PathBuf::from(path),
            records: BTreeMap::new(),
            bytes: BTreeMap::new(),
            active: BTreeSet::new(),
            aliases: BTreeMap::new(),
            ids: BTreeSet::new(),
            record_bytes: 0,
            blob_bytes: 0,
            eligible: true,
        })
    }
    pub fn directory(&self, path: &str) -> R<File> {
        relative(path)?;
        let mut f = self.root.try_clone().map_err(|_| ())?;
        for p in path.split('/') {
            let fd = unsafe {
                libc::openat(
                    f.as_raw_fd(),
                    c(p)?.as_ptr(),
                    libc::O_RDONLY | libc::O_NOFOLLOW | libc::O_DIRECTORY | libc::O_CLOEXEC,
                )
            };
            ensure(fd >= 0)?;
            f = unsafe { File::from_raw_fd(fd) };
        }
        Ok(f)
    }
    pub fn open(&self, path: &str) -> R<File> {
        relative(path)?;
        let mut f = self.root.try_clone().map_err(|_| ())?;
        let parts: Vec<_> = path.split('/').collect();
        for (i, p) in parts.iter().enumerate() {
            let flags = libc::O_RDONLY
                | libc::O_NOFOLLOW
                | libc::O_CLOEXEC
                | libc::O_NONBLOCK
                | if i + 1 < parts.len() {
                    libc::O_DIRECTORY
                } else {
                    0
                };
            let fd = unsafe { libc::openat(f.as_raw_fd(), c(p)?.as_ptr(), flags) };
            ensure(fd >= 0)?;
            f = unsafe { File::from_raw_fd(fd) };
        }
        ensure(f.metadata().map_err(|_| ())?.is_file())?;
        Ok(f)
    }
    fn read(&mut self, path: &str, record: bool) -> R<Vec<u8>> {
        if let Some(b) = self.bytes.get(path) {
            return Ok(b.clone());
        }
        let mut f = self.open(path)?;
        let meta = f.metadata().map_err(|_| ())?;
        let key = (meta.dev(), meta.ino());
        if let Some(old) = self.aliases.get(&key) {
            ensure(old == path)?;
        }
        self.aliases.insert(key, path.into());
        let max = if record { 262144 } else { 16 * 1024 * 1024 };
        ensure(meta.len() <= max)?;
        let mut b = Vec::new();
        (&mut f).take(max + 1).read_to_end(&mut b).map_err(|_| ())?;
        let after = f.metadata().map_err(|_| ())?;
        ensure(
            b.len() <= max as usize
                && b.len() as u64 == meta.len()
                && meta.dev() == after.dev()
                && meta.ino() == after.ino()
                && meta.len() == after.len()
                && meta.mtime() == after.mtime()
                && meta.mtime_nsec() == after.mtime_nsec()
                && meta.ctime() == after.ctime()
                && meta.ctime_nsec() == after.ctime_nsec(),
        )?;
        if record {
            self.record_bytes += b.len();
            ensure(self.record_bytes <= 4 * 1024 * 1024)?;
        } else {
            self.blob_bytes += b.len();
            ensure(self.blob_bytes <= 64 * 1024 * 1024)?;
        }
        self.bytes.insert(path.into(), b.clone());
        Ok(b)
    }
    fn walk(&mut self, v: &J, refs: &mut usize) -> R<()> {
        match v {
            J::Obj(o) if o.contains_key("ref_type") => {
                *refs += 1;
                ensure(*refs <= 64)?;
                let p = v.get("path")?.s()?;
                let r = v.get("ref_type")?.s()? == "record";
                let b = self.read(p, r)?;
                ensure(sha(&b) == v.get("digest")?.get("value")?.s()?)?;
                if r {
                    self.load(p)?;
                    let rec = self.records.get(p).ok_or(())?;
                    ensure(rec.get("record_kind")? == v.get("record_kind")?)?;
                    ensure(rec.get("schema_version")? == v.get("schema_version")?)?;
                }
            }
            J::Obj(o) => {
                for x in o.values() {
                    self.walk(x, refs)?;
                }
            }
            J::Arr(a) => {
                for x in a {
                    self.walk(x, refs)?;
                }
            }
            _ => (),
        }
        Ok(())
    }
    fn load(&mut self, path: &str) -> R<()> {
        if self.records.contains_key(path) {
            return Ok(());
        }
        ensure(self.active.insert(path.into()))?;
        ensure(self.records.len() + self.active.len() <= 128)?;
        let data = self.read(path, true)?;
        let rec = parse(&data)?;
        shape(&rec)?;
        ensure(self.ids.insert(rec.get("record_id")?.s()?.into()))?;
        let d = rec.get("disclosure")?;
        self.eligible &= rec.get("record_context")?.s()? == "fixture"
            && d.get("mode")?.s()? == "full"
            && d.get("withheld")?.a()?.is_empty()
            && *d.get("origin_token")? == J::Null;
        if rec.get("record_kind")?.s()? == "launch" {
            self.eligible &= rec.get("purpose")?.s()? == "fixture_launch";
        }
        self.walk(&rec, &mut 0)?;
        self.active.remove(path);
        self.records.insert(path.into(), rec);
        Ok(())
    }
    pub fn validate(
        &mut self,
        entry: &str,
        trusted_sha: &str,
    ) -> R<(Vec<String>, Vec<(String, String)>, File)> {
        for k in ["runtime", "prefix", "saves", "cache", "logs"] {
            self.directory(&format!("state/{k}"))?;
        }
        self.load(entry)?;
        ensure(self.records.len() == 4)?;
        let q = self.records.get(entry).ok_or(())?;
        eq(q.get("record_kind")?, "launch")?;
        let lock = q.get("lock")?;
        let art = self
            .records
            .get(q.get("artifact")?.get("path")?.s()?)
            .ok_or(())?;
        ensure(art.get("lock")? == lock)?;
        let profile = self
            .records
            .get(q.get("profile")?.get("path")?.s()?)
            .ok_or(())?;
        let content = art.get("files")?.a()?[0].get("content")?;
        ensure(content.get("digest")?.get("value")?.s()? == trusted_sha)?;
        let args = profile
            .get("arguments")?
            .a()?
            .iter()
            .map(|v| v.s().map(str::to_owned))
            .collect::<R<Vec<_>>>()?;
        let env = profile
            .get("environment")?
            .a()?
            .iter()
            .map(|e| {
                Ok((
                    e.get("key")?.s()?.to_owned(),
                    e.get("value")?.s()?.to_owned(),
                ))
            })
            .collect::<R<Vec<_>>>()?;
        let f = self.open("blobs/fixture-child")?;
        let meta = f.metadata().map_err(|_| ())?;
        let key = (meta.dev(), meta.ino());
        ensure(
            self.aliases
                .get(&key)
                .is_some_and(|p| p == "blobs/fixture-child"),
        )?;
        let mut actual = Vec::new();
        f.try_clone()
            .map_err(|_| ())?
            .take(16 * 1024 * 1024 + 1)
            .read_to_end(&mut actual)
            .map_err(|_| ())?;
        ensure(actual.len() <= 16 * 1024 * 1024 && sha(&actual) == trusted_sha)?;
        Ok((args, env, f))
    }
}
