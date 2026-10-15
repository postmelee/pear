// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
//! Isolated Rosetta preview bootstrap. Steam owns authentication and game launch.
use pear_manager::{fs::hex, native::sha256};
use std::sync::atomic::{AtomicBool, Ordering};
use std::{
    error::Error,
    ffi::OsStr,
    fs::{self, File, OpenOptions},
    io::{self, Read},
    os::{
        fd::AsRawFd,
        unix::fs::{DirBuilderExt, OpenOptionsExt, PermissionsExt},
    },
    path::{Path, PathBuf},
    process::{Command, Stdio},
    thread,
    time::{Duration, Instant},
};
static CANCELLED: AtomicBool = AtomicBool::new(false);
extern "C" fn cancel(_: libc::c_int) {
    CANCELLED.store(true, Ordering::Relaxed);
}
pub fn install_cancellation() {
    // SAFETY: handler only writes a lock-free atomic, retains no pointers and never unwinds.
    unsafe {
        libc::signal(libc::SIGINT, cancel as *const () as libc::sighandler_t);
        libc::signal(libc::SIGTERM, cancel as *const () as libc::sighandler_t);
    }
}
fn cancelled() -> Result<()> {
    need(
        !CANCELLED.load(Ordering::Relaxed),
        "Preparation stopped. Downloaded game files and saves were kept.",
    )
}
pub type Result<T> = std::result::Result<T, Box<dyn Error>>;
const OWNER: &str = "pear-rosetta-preview-v1\n";
const GAME: &str = "3405340";
#[derive(Clone, Copy)]
pub struct Artifact {
    pub name: &'static str,
    pub url: &'static str,
    pub sha: &'static str,
    pub size: u64,
}
mod migration;
mod runtime_pin;
pub use runtime_pin::{RUNTIME, RUNTIME_ID};
fn runtime_inputs() -> String {
    format!("{}\n{}\n", RUNTIME_ID, RUNTIME.sha)
}
pub const STEAM: Artifact = Artifact {
    name: "SteamSetup.exe",
    url: "https://cdn.fastly.steamstatic.com/client/installer/SteamSetup.exe",
    sha: "7d3654531c32d941b8cae81c4137fc542172bfa9635f169cb392f245a0a12bcb",
    size: 2380800,
};
fn need(ok: bool, message: &str) -> Result<()> {
    if ok {
        Ok(())
    } else {
        Err(message.into())
    }
}
fn private_dir(path: &Path) -> Result<()> {
    match fs::symlink_metadata(path) {
        Ok(m) => need(
            m.is_dir() && !m.file_type().is_symlink(),
            "Expected a directory, not a link.",
        )?,
        Err(e) if e.kind() == io::ErrorKind::NotFound => {
            fs::DirBuilder::new().mode(0o700).create(path)?
        }
        Err(e) => return Err(e.into()),
    }
    Ok(())
}
fn plain_file(path: &Path) -> Result<File> {
    Ok(OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_NOFOLLOW | libc::O_NONBLOCK)
        .open(path)?)
}
fn text(path: &Path, limit: u64) -> Result<String> {
    let f = plain_file(path)?;
    need(
        f.metadata()?.is_file() && f.metadata()?.len() <= limit,
        "Unexpected file type or size.",
    )?;
    let mut s = String::new();
    f.take(limit + 1).read_to_string(&mut s)?;
    need(s.len() as u64 <= limit, "File exceeds size limit.")?;
    Ok(s)
}
fn artifact_matches(path: &Path, artifact: Artifact) -> Result<bool> {
    let f = plain_file(path)?;
    need(f.metadata()?.is_file(), "Expected a regular artifact file.")?;
    if f.metadata()?.len() != artifact.size {
        return Ok(false);
    }
    let (digest, size) = sha256(&f, artifact.size)?;
    Ok(size == artifact.size && hex(&digest) == artifact.sha)
}
pub fn verify(path: &Path, artifact: Artifact) -> Result<()> {
    need(artifact_matches(path, artifact)?,
         "Download verification failed. No installation was activated; retry with the pinned artifact.")
}
fn write_new(path: &Path, bytes: &[u8]) -> Result<()> {
    use std::io::Write;
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o600)
        .open(path)?;
    file.write_all(bytes)?;
    file.sync_all()?;
    Ok(())
}
pub fn run(cmd: &mut Command, seconds: u64) -> Result<()> {
    run_observed(cmd, seconds, || {})
}
fn run_observed(cmd: &mut Command, seconds: u64, mut observe: impl FnMut()) -> Result<()> {
    cancelled()?;
    // No client output capture: authentication belongs in Steam's window.
    let mut child = cmd
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()?;
    let start = Instant::now();
    loop {
        observe();
        if let Some(status) = child.try_wait()? {
            return need(status.success(), &format!("The current step failed ({status}). Retry after closing this preview's Steam window."));
        }
        if cancelled().is_err() || start.elapsed() >= Duration::from_secs(seconds) {
            let killed = child.kill();
            let reaped = child.wait();
            if killed.is_err() || reaped.is_err() {
                return Err("Step timed out; child cleanup could not be confirmed.".into());
            }
            cancelled()?;
            return Err("Step timed out. Steam or Wine helpers may still be open; close this preview's windows before retrying.".into());
        }
        thread::sleep(Duration::from_millis(50));
    }
}
/// Read-only hints for the initial UI. Normal preparation still verifies every input.
pub fn setup_info(root: &Path) -> Result<String> {
    need(root.is_absolute(), "State path must be absolute.")?;
    let matches = |path: PathBuf, expected: &str| text(&path, 512).is_ok_and(|s| s == expected);
    let owned = matches(root.join(".owner"), OWNER);
    let runtime = owned
        && matches(
            root.join("runtimes").join(RUNTIME_ID).join("inputs"),
            &runtime_inputs(),
        )
        && root
            .join("runtimes")
            .join(RUNTIME_ID)
            .join("Libraries/Wine/bin/wine")
            .is_file();
    let steam = owned
        && [RUNTIME_ID, migration::PREVIOUS]
            .iter()
            .any(|id| matches(root.join("private/prefix.ready"), id))
        && matches(root.join("private/steam.ready"), STEAM.sha)
        && root
            .join("private/prefix/drive_c/Program Files (x86)/Steam/steam.exe")
            .is_file();
    // All strings below are compile-time constants; no private paths or user input are emitted.
    Ok(format!(
        r#"{{"version":"{}","runtime_id":"{}","runtime_bytes":{},"steam_bytes":{},"runtime_present":{},"steam_present":{},"ready":{}}}"#,
        env!("CARGO_PKG_VERSION"),
        RUNTIME_ID,
        RUNTIME.size,
        STEAM.size,
        runtime,
        steam,
        runtime && steam
    ))
}

pub struct Session {
    pub root: PathBuf,
    _lock: File,
}
impl Drop for Session {
    fn drop(&mut self) {
        // A concurrently spawned child can briefly retain the open description
        // until exec even with CLOEXEC. Session owns the lock, not that child.
        // SAFETY: the owned file stays live until after this destructor.
        unsafe { libc::flock(self._lock.as_raw_fd(), libc::LOCK_UN) };
    }
}
impl Session {
    pub fn open(path: &Path) -> Result<Self> {
        need(path.is_absolute(), "State path must be absolute.")?;
        let parent = path.parent().ok_or("Invalid state path.")?.canonicalize()?;
        let root = parent.join(path.file_name().ok_or("Invalid state path.")?);
        private_dir(&root)?;
        if !root.join(".owner").exists() {
            need(
                fs::read_dir(&root)?.all(|e| e.is_ok_and(|e| e.file_name() == ".lock")),
                "This folder contains unrelated files. Select a new empty preview folder.",
            )?;
        }
        // The lock is held across all setup and install-wait steps, including first adoption.
        let lock = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .truncate(false)
            .mode(0o600)
            .custom_flags(libc::O_NOFOLLOW)
            .open(root.join(".lock"))?;
        need(lock.metadata()?.is_file(), "Invalid lock file.")?;
        // SAFETY: a live owned file descriptor; flock retains no userspace pointer.
        need(
            unsafe { libc::flock(lock.as_raw_fd(), libc::LOCK_EX | libc::LOCK_NB) } == 0,
            "Pear is already preparing or waiting for Steam. Use its existing window.",
        )?;
        let owner = root.join(".owner");
        if !owner.exists() {
            need(
                fs::read_dir(&root)?.all(|e| e.is_ok_and(|e| e.file_name() == ".lock")),
                "This folder contains unrelated files. Select a new empty preview folder.",
            )?;
            write_new(&owner, OWNER.as_bytes())?;
        }
        need(
            text(&owner, 100)? == OWNER,
            "This state folder belongs to a different tool.",
        )?;
        fs::set_permissions(&root, fs::Permissions::from_mode(0o700))?;
        for name in ["cache", "runtimes", "private"] {
            private_dir(&root.join(name))?;
        }
        Ok(Self { root, _lock: lock })
    }
    fn archive(
        &self,
        artifact: Artifact,
        supplied: Option<&Path>,
        notify: &dyn Fn(&str),
    ) -> Result<PathBuf> {
        self.archive_with(artifact, supplied, |download| {
            let mut last = None;
            let mut updated = Instant::now() - Duration::from_secs(1);
            notify(&format!(
                "@download\t0\t{}\t{}",
                artifact.size, artifact.name
            ));
            run_observed(
                Command::new("/usr/bin/curl")
                    .args([
                        "--fail",
                        "--location",
                        "--silent",
                        "--show-error",
                        "--proto",
                        "=https",
                        "--proto-redir",
                        "=https",
                        "--retry",
                        "2",
                        "--connect-timeout",
                        "30",
                        "--max-time",
                        "1800",
                        "--output",
                    ])
                    .arg(download)
                    .arg(artifact.url),
                1810,
                || {
                    if updated.elapsed() >= Duration::from_millis(250) {
                        let bytes = fs::metadata(download).map(|m| m.len()).unwrap_or(0);
                        if last != Some(bytes) {
                            notify(&format!(
                                "@download\t{}\t{}\t{}",
                                bytes, artifact.size, artifact.name
                            ));
                            last = Some(bytes);
                        }
                        updated = Instant::now();
                    }
                },
            )?;
            notify("Verifying the download…");
            Ok(())
        })
    }
    // The operation seam keeps failure tests on the real cache/verification transaction.
    // Production always supplies the HTTPS curl operation above.
    fn archive_with(
        &self,
        artifact: Artifact,
        supplied: Option<&Path>,
        download_into: impl FnOnce(&Path) -> Result<()>,
    ) -> Result<PathBuf> {
        if let Some(path) = supplied {
            verify(path, artifact)?;
            return Ok(path.canonicalize()?);
        }
        let cache = self.root.join("cache");
        let final_path = cache.join(artifact.name);
        let cached = match fs::symlink_metadata(&final_path) {
            Ok(_) => true,
            Err(error) if error.kind() == io::ErrorKind::NotFound => false,
            Err(error) => return Err(error.into()),
        };
        if cached {
            if artifact_matches(&final_path, artifact)? {
                return Ok(final_path);
            }
            need(!artifact.url.is_empty(),
                 "Cached download is damaged and no public runtime download is available. Supply its pinned archive with --runtime-archive PATH; private data was kept.")?;
            // Only an owned, regular cache file with a known digest/length mismatch.
            // I/O errors and links return above; installed runtimes/private state are untouched.
            fs::remove_file(&final_path)?;
        }
        need(!artifact.url.is_empty(),
             "This development candidate has no public runtime download yet. Supply its pinned archive with --runtime-archive PATH.")?;
        let scratch = Stage::new(&cache)?;
        let download = scratch.path.join(artifact.name);
        download_into(&download)?;
        verify(&download, artifact)?;
        fs::rename(download, &final_path)?;
        Ok(final_path)
    }
    pub fn runtime(&self, supplied: Option<&Path>, notify: &dyn Fn(&str)) -> Result<PathBuf> {
        let dest = self.root.join("runtimes").join(RUNTIME_ID);
        if dest.exists() {
            private_dir(&dest)?;
            private_dir(&dest.join("Libraries"))?;
            notify("Checking the installed runtime…");
            need(
                text(&dest.join("inputs"), 512)? == runtime_inputs(),
                "Runtime identity changed.",
            )?;
            need(text(&dest.join("inventory"), 2_000_000)? == inventory(&dest.join("Libraries"))?,
                 "Runtime files changed. Keep your private folder; repair the runtime before launching.")?;
            return Ok(dest.join("Libraries"));
        }
        self.space(3 * 1024 * 1024 * 1024)?;
        notify("Checking and installing the Pear runtime…");
        let archive = self.archive(RUNTIME, supplied, notify)?;
        notify("Extracting the runtime…");
        self.install_runtime(&archive, |archive, stage| {
            // Only this exact reviewed archive is passed to tar, after hash verification.
            run(
                Command::new("/usr/bin/tar")
                    .arg("-xf")
                    .arg(archive)
                    .arg("-C")
                    .arg(stage),
                180,
            )
        })
    }
    // Own the staging directory until every check and marker write succeeds.
    fn install_runtime(
        &self,
        archive: &Path,
        extract_into: impl FnOnce(&Path, &Path) -> Result<()>,
    ) -> Result<PathBuf> {
        let dest = self.root.join("runtimes").join(RUNTIME_ID);
        let stage = Stage::new(&self.root.join("runtimes"))?;
        extract_into(archive, &stage.path)?;
        let lib = stage.path.join("Libraries");
        need(
            lib.join("Wine/bin/wine").is_file()
                && lib.join("DXMT/x64/d3d11.dll").is_file()
                && lib
                    .join("Wine/share/pear/licenses/toolchain/provenance.json")
                    .is_file(),
            "Runtime layout or component notices are incomplete.",
        )?;
        write_new(&stage.path.join("inventory"), inventory(&lib)?.as_bytes())?;
        write_new(&stage.path.join("inputs"), runtime_inputs().as_bytes())?;
        fs::rename(&stage.path, &dest)?;
        Ok(dest.join("Libraries"))
    }
    fn compatible_prefix(&self) -> Result<()> {
        let ready = self.root.join("private/prefix.ready");
        if ready.try_exists()? {
            need(
                matches!(text(&ready, 100)?.as_str(), RUNTIME_ID | migration::PREVIOUS),
                "This installation uses a different runtime. Its games and saves were kept. Continue with its original Pear version; automatic migration is not available.",
            )?;
        } else if self.prefix().try_exists()? {
            // A partial prefix belongs to this runtime only if its setup marker matches.
            need(
                text(&self.root.join("private/prefix.runtime"), 100)? == RUNTIME_ID,
                "The unfinished environment belongs to an unknown runtime. Its files were kept.",
            )?;
        }
        Ok(())
    }
    fn space(&self, needed: u64) -> Result<()> {
        let root = File::open(&self.root)?;
        let mut value = std::mem::MaybeUninit::<libc::statvfs>::uninit();
        // SAFETY: live directory FD and correctly sized writable output.
        need(
            unsafe { libc::fstatvfs(root.as_raw_fd(), value.as_mut_ptr()) } == 0,
            "Cannot check available storage.",
        )?;
        let value = unsafe { value.assume_init() };
        need(
            u64::from(value.f_bavail).saturating_mul(value.f_frsize) >= needed,
            "More free storage is needed for setup. Your existing game and saves were kept.",
        )
    }
    fn prefix(&self) -> PathBuf {
        self.root.join("private/prefix")
    }
    fn wine(&self, lib: &Path) -> Command {
        let mut c = Command::new(lib.join("Wine/bin/wine"));
        self.environment(&mut c, lib);
        c
    }
    fn environment(&self, c: &mut Command, lib: &Path) {
        c.env_clear()
            .env("HOME", std::env::var_os("HOME").unwrap_or_default())
            .env("USER", std::env::var_os("USER").unwrap_or_default())
            .env("TMPDIR", std::env::temp_dir())
            .env("PATH", "/usr/bin:/bin:/usr/sbin:/sbin")
            .env("WINEPREFIX", self.prefix())
            .env("WINEARCH", "win64")
            .env("PEAR_STEAM_IN_PROCESS_GPU", "1")
            .env(
                "PEAR_STEAM_WEBHELPER_PATH",
                r"C:\Program Files (x86)\Steam\bin\cef\cef.win64\steamwebhelper.exe",
            )
            .env("WINEDEBUG", "-all")
            .env(
                "WINEDLLOVERRIDES",
                "winemenubuilder.exe=d;mscoree,mshtml=d;dxgi,d3d11,d3d10core=n,b;winemetal=b",
            )
            .env("WINELOADER", lib.join("Wine/bin/wine"));
    }
    pub fn prepare(
        &self,
        runtime: Option<&Path>,
        installer: Option<&Path>,
        notify: &dyn Fn(&str),
    ) -> Result<PathBuf> {
        self.compatible_prefix()?;
        notify("Checking Rosetta…");
        run(
            Command::new("/usr/bin/arch").args(["-x86_64", "/usr/bin/true"]),
            15,
        )
        .map_err(|_| {
            "Rosetta is required. Install it through macOS, then open Pear again."
        })?;
        let lib = self.runtime(runtime, notify)?;
        self.upgrade_prefix(&lib, notify)?;
        let ready = self.root.join("private/prefix.ready");
        if !ready.exists() {
            self.space(2 * 1024 * 1024 * 1024)?;
            notify("Preparing the Windows game environment…");
            let pending = self.root.join("private/prefix.runtime");
            if !pending.try_exists()? {
                write_new(&pending, RUNTIME_ID.as_bytes())?;
            }
            need(
                text(&pending, 100)? == RUNTIME_ID,
                "Runtime setup identity changed.",
            )?;
            private_dir(&self.prefix())?;
            run(self.wine(&lib).args(["wineboot", "-u"]), 180)?;
            run(
                self.wine(&lib).args([
                    "reg",
                    "add",
                    "HKCU\\Software\\Wine",
                    "/v",
                    "Version",
                    "/t",
                    "REG_SZ",
                    "/d",
                    "win10",
                    "/f",
                ]),
                30,
            )?;
            self.install_graphics(&lib, &self.prefix())?;
            write_new(&ready, RUNTIME_ID.as_bytes())?;
        }
        need(
            text(&ready, 100)? == RUNTIME_ID,
            "The prefix needs a reviewed runtime migration.",
        )?;
        let steam = self.steam();
        let steam_ready = self.root.join("private/steam.ready");
        if !steam_ready.exists() {
            notify("Installing official Steam…");
            let installer = self.archive(STEAM, installer, notify)?;
            run(self.wine(&lib).arg(installer).arg("/S"), 180)?;
            need(
                steam.is_file(),
                "Steam installation is incomplete. Open the preview again to retry.",
            )?;
            write_new(&steam_ready, STEAM.sha.as_bytes())?;
        }
        need(
            steam.is_file() && text(&steam_ready, 100)? == STEAM.sha,
            "Steam setup needs repair. Existing account and game state were preserved.",
        )?;
        Ok(lib)
    }
    fn steam(&self) -> PathBuf {
        self.prefix()
            .join("drive_c/Program Files (x86)/Steam/steam.exe")
    }
    fn installed(&self) -> Result<bool> {
        let manifest = self
            .prefix()
            .join("drive_c/Program Files (x86)/Steam/steamapps/appmanifest_3405340.acf");
        if !manifest.exists() {
            return Ok(false);
        }
        Ok(game_installed(&text(&manifest, 262144)?))
    }
    fn open_steam(&self, lib: &Path, arguments: &[&str]) -> Result<()> {
        // Keep the notarized loader at its original runtime path. Copying it into
        // a generated .app creates an unsigned bundle with an invalid resource seal.
        // Wine's start returns after creating Steam; /wait would couple its lifetime
        // to the setup timeout. A successful handoff does not prove a visible window.
        run(
            self.wine(lib)
                .args(["start", "/unix"])
                .arg(self.steam())
                .args(arguments),
            30,
        )
    }
    pub fn steam_library(&self, lib: &Path, notify: &dyn Fn(&str)) -> Result<()> {
        notify("Opening Windows Steam…");
        self.open_steam(lib, &["steam://open/games"])?;
        notify("Steam is opening. Sign in and choose a game from your library. You can close this Pear window; Steam and your games stay open.");
        Ok(())
    }
    pub fn play(&self, lib: &Path, notify: &dyn Fn(&str)) -> Result<()> {
        let mut flow = InstallFlow::default();
        let start = Instant::now();
        let manifest = self
            .prefix()
            .join("drive_c/Program Files (x86)/Steam/steamapps/appmanifest_3405340.acf");
        loop {
            cancelled()?;
            match flow.next(self.installed()?, manifest.exists(), start.elapsed())? {
                InstallAction::Request => {
                    notify("Sign in to official Steam if asked. Megabonk will download and launch automatically. Keep this window open.");
                    // Verified on the pinned preview client. Steam owns the download, install metadata and entitlement check.
                    self.open_steam(lib, &["-console", "+app_install", GAME])?;
                }
                InstallAction::Wait => (),
                InstallAction::Launch => {
                    notify("Requesting Megabonk launch through Steam…");
                    self.open_steam(lib, &["-applaunch", GAME])?;
                    notify("Launch request sent. Continue in Steam if sign-in or an update is required.");
                    return Ok(());
                }
            }
            thread::sleep(Duration::from_secs(2));
        }
    }
}
#[derive(Debug, PartialEq, Eq)]
enum InstallAction {
    Request,
    Wait,
    Launch,
}
#[derive(Default)]
struct InstallFlow {
    last_request: Option<Duration>,
    launched: bool,
}
impl InstallFlow {
    fn next(
        &mut self,
        ready: bool,
        manifest_present: bool,
        elapsed: Duration,
    ) -> Result<InstallAction> {
        if self.launched {
            return Ok(InstallAction::Wait);
        }
        if ready {
            self.launched = true;
            return Ok(InstallAction::Launch);
        }
        need(elapsed < Duration::from_secs(3600),
             "Still waiting for Steam installation. Check the Steam connection or sign-in, then retry. Downloaded files and saves were kept.")?;
        // A pre-login request may be ignored. Retry without opening the installation confirmation dialog.
        // Once Steam creates the target manifest, allow its own download/update machinery to finish.
        if !manifest_present
            && self
                .last_request
                .is_none_or(|last| elapsed.saturating_sub(last) >= Duration::from_secs(15))
        {
            self.last_request = Some(elapsed);
            return Ok(InstallAction::Request);
        }
        Ok(InstallAction::Wait)
    }
}
struct Stage {
    path: PathBuf,
}
impl Stage {
    fn new(parent: &Path) -> Result<Self> {
        let parent_fd = File::open(parent)?;
        let name = pear_manager::native::stage_directory(&parent_fd)?;
        let path = parent.join(OsStr::from_bytes(name.to_bytes()));
        Ok(Self { path })
    }
}
use std::os::unix::ffi::OsStrExt;
impl Drop for Stage {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.path);
    }
}
fn inventory(root: &Path) -> Result<String> {
    fn walk(root: &Path, dir: &Path, rows: &mut Vec<String>) -> Result<()> {
        for e in fs::read_dir(dir)? {
            let e = e?;
            let path = e.path();
            let name = path
                .strip_prefix(root)?
                .to_str()
                .ok_or("Invalid runtime path.")?;
            need(!name.contains(['\t', '\n', '\r']), "Invalid runtime path.")?;
            let m = fs::symlink_metadata(&path)?;
            if m.file_type().is_symlink() {
                let target = fs::read_link(&path)?;
                need(
                    !target.is_absolute() && path.canonicalize()?.starts_with(root.canonicalize()?),
                    "Runtime link escapes its directory.",
                )?;
                rows.push(format!(
                    "L\t{name}\t{}",
                    target.to_str().ok_or("Invalid runtime link.")?
                ));
            } else if m.is_dir() {
                rows.push(format!("D\t{name}"));
                walk(root, &path, rows)?;
            } else if m.is_file() {
                let (digest, _) = sha256(&plain_file(&path)?, 2_000_000_000)?;
                rows.push(format!(
                    "F\t{name}\t{:o}\t{}",
                    m.permissions().mode() & 0o777,
                    hex(&digest)
                ));
            } else {
                return Err("Unexpected runtime file type.".into());
            }
        }
        Ok(())
    }
    let mut rows = Vec::new();
    walk(root, root, &mut rows)?;
    rows.sort();
    Ok(rows.join("\n") + "\n")
}
fn replace_file(source: &Path, target: &Path, scratch_parent: &Path) -> Result<()> {
    let scratch = Stage::new(scratch_parent)?;
    let replacement = scratch.path.join("replacement");
    fs::copy(source, &replacement)?;
    // Rename replaces a prefix symlink rather than modifying its shared runtime target.
    fs::rename(replacement, target)?;
    Ok(())
}
/// Read only a complete top-level Steam AppState, rejecting duplicates and truncation.
pub fn game_installed(s: &str) -> bool {
    fn parse(s: &str) -> Option<bool> {
        let mut chars = s.chars().peekable();
        let mut tokens = Vec::new();
        while let Some(c) = chars.next() {
            if c.is_whitespace() {
                continue;
            }
            match c {
                '{' | '}' => tokens.push(c.to_string()),
                '"' => {
                    let mut token = String::new();
                    let mut closed = false;
                    while let Some(c) = chars.next() {
                        match c {
                            '"' => {
                                closed = true;
                                break;
                            }
                            '\\' => token.push(chars.next()?),
                            _ => token.push(c),
                        }
                    }
                    if !closed {
                        return None;
                    }
                    tokens.push(format!("q{token}"));
                }
                _ => return None,
            }
            if tokens.len() > 32768 {
                return None;
            }
        }
        fn object(
            tokens: &[String],
            at: &mut usize,
            depth: usize,
        ) -> Option<std::collections::BTreeMap<String, String>> {
            if depth > 16 || tokens.get(*at)? != "{" {
                return None;
            }
            *at += 1;
            let mut entries = std::collections::BTreeMap::new();
            while tokens.get(*at)? != "}" {
                let key = tokens.get(*at)?.strip_prefix('q')?.to_owned();
                *at += 1;
                let value = if tokens.get(*at)? == "{" {
                    object(tokens, at, depth + 1)?;
                    String::new()
                } else {
                    let v = tokens.get(*at)?.strip_prefix('q')?.to_owned();
                    *at += 1;
                    v
                };
                if entries.insert(key, value).is_some() {
                    return None;
                }
            }
            *at += 1;
            Some(entries)
        }
        if tokens.first()? != "qAppState" {
            return None;
        }
        let mut at = 1;
        let fields = object(&tokens, &mut at, 0)?;
        Some(at == tokens.len() && fields.get("appid")? == GAME && fields.get("StateFlags")? == "4")
    }
    parse(s) == Some(true)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::os::unix::fs::symlink;
    fn scratch() -> Stage {
        Stage::new(&std::env::temp_dir()).unwrap()
    }
    #[test]
    fn setup_info_is_read_only_and_does_not_trust_partial_markers() {
        let t = scratch();
        let root = t.path.join("absent state");
        let info = setup_info(&root).unwrap();
        assert!(info.contains("\"ready\":false"));
        assert!(!root.exists());
        assert!(setup_info(Path::new("relative")).is_err());
        let session = Session::open(&root).unwrap();
        let runtime = root.join("runtimes").join(RUNTIME_ID);
        fs::create_dir_all(runtime.join("Libraries/Wine/bin")).unwrap();
        fs::write(runtime.join("Libraries/Wine/bin/wine"), b"fixture").unwrap();
        fs::write(runtime.join("inputs"), runtime_inputs()).unwrap();
        fs::create_dir_all(session.steam().parent().unwrap()).unwrap();
        fs::write(session.steam(), b"fixture").unwrap();
        fs::write(root.join("private/prefix.ready"), RUNTIME_ID).unwrap();
        fs::write(root.join("private/steam.ready"), STEAM.sha).unwrap();
        let before = inventory(&root.join("private")).unwrap();
        assert!(setup_info(&root).unwrap().contains("\"ready\":true"));
        assert_eq!(inventory(&root.join("private")).unwrap(), before);
        fs::write(root.join("private/prefix.ready"), migration::PREVIOUS).unwrap();
        assert!(setup_info(&root)
            .unwrap()
            .contains("\"steam_present\":true"));
        fs::write(root.join("private/prefix.ready"), "different-runtime").unwrap();
        assert!(setup_info(&root).unwrap().contains("\"ready\":false"));
    }

    #[test]
    fn progress_observer_runs_before_completion_and_preserves_failure() {
        let mut observations = 0;
        run_observed(Command::new("/bin/sleep").arg("0.2"), 3, || {
            observations += 1
        })
        .unwrap();
        assert!(observations >= 2);
        assert!(run_observed(&mut Command::new("/usr/bin/false"), 3, || {}).is_err());
    }

    #[test]
    fn session_drop_releases_lock_despite_a_duplicated_descriptor() {
        let owner = scratch();
        let root = owner.path.join("state");
        let session = Session::open(&root).unwrap();
        // Model the shared open description retained between another thread's
        // fork and exec, without a timing-dependent real process race.
        let duplicate = session._lock.try_clone().unwrap();
        assert!(Session::open(&root).is_err());
        drop(session);
        let reopened = Session::open(&root).unwrap();
        drop(duplicate);
        assert!(Session::open(&root).is_err());
        drop(reopened);
        assert!(Session::open(&root).is_ok());
    }
    #[test]
    fn owned_state_reopens_and_rejects_concurrent_session() {
        let t = scratch();
        let root = t.path.join("state");
        let s = Session::open(&root).unwrap();
        fs::write(root.join("private/sentinel"), "save").unwrap();
        assert!(Session::open(&root).is_err());
        drop(s);
        let _next = Session::open(&root).unwrap();
        assert_eq!(
            fs::read_to_string(root.join("private/sentinel")).unwrap(),
            "save"
        );
    }
    #[test]
    fn unrelated_state_and_symlinks_are_rejected_without_writes() {
        let t = scratch();
        let root = t.path.join("foreign");
        fs::create_dir(&root).unwrap();
        fs::write(root.join("save"), "keep").unwrap();
        assert!(Session::open(&root).is_err());
        assert_eq!(fs::read_dir(&root).unwrap().count(), 1);
        let link = t.path.join("link");
        symlink(&root, &link).unwrap();
        assert!(Session::open(&link).is_err());
    }
    #[test]
    fn artifact_hash_size_and_symlink_checks() {
        let t = scratch();
        let f = t.path.join("artifact");
        fs::write(&f, b"abc").unwrap();
        let a = Artifact {
            name: "fixture",
            url: "unused",
            size: 3,
            sha: "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        };
        verify(&f, a).unwrap();
        fs::write(&f, b"bad").unwrap();
        assert!(verify(&f, a).is_err());
        fs::write(&f, b"abcd").unwrap();
        assert!(verify(&f, a).is_err());
        let link = t.path.join("link");
        symlink(&f, &link).unwrap();
        assert!(verify(&link, a).is_err());
    }
    #[test]
    fn invalid_runtime_cannot_activate_or_erase_private_data() {
        let t = scratch();
        let s = Session::open(&t.path.join("state")).unwrap();
        fs::write(s.root.join("private/save"), b"keep").unwrap();
        let bad = t.path.join("bad.tar.gz");
        fs::write(&bad, b"bad").unwrap();
        assert!(s.archive(RUNTIME, Some(&bad), &|_| {}).is_err());
        assert_eq!(fs::read_dir(s.root.join("runtimes")).unwrap().count(), 0);
        assert_eq!(fs::read(s.root.join("private/save")).unwrap(), b"keep");
    }
    #[test]
    fn inventory_detects_mutation_and_refuses_escape() {
        let t = scratch();
        let root = t.path.join("runtime");
        fs::create_dir(&root).unwrap();
        fs::write(root.join("file"), "a").unwrap();
        symlink("file", root.join("link")).unwrap();
        let first = inventory(&root).unwrap();
        fs::write(root.join("file"), "b").unwrap();
        assert_ne!(first, inventory(&root).unwrap());
        symlink("..", root.join("escape")).unwrap();
        assert!(inventory(&root).is_err());
    }
    #[test]
    fn dxmt_replacement_does_not_write_through_runtime_link() {
        let t = scratch();
        let original = t.path.join("runtime.dll");
        let source = t.path.join("dxmt.dll");
        let target = t.path.join("prefix.dll");
        fs::write(&original, "original").unwrap();
        fs::write(&source, "dxmt").unwrap();
        symlink(&original, &target).unwrap();
        replace_file(&source, &target, &t.path).unwrap();
        assert_eq!(fs::read_to_string(&original).unwrap(), "original");
        assert_eq!(fs::read_to_string(&target).unwrap(), "dxmt");
        assert!(!fs::symlink_metadata(&target)
            .unwrap()
            .file_type()
            .is_symlink());
    }
    #[test]
    fn different_runtime_is_refused_before_setup_changes_private_state() {
        let t = scratch();
        let session = Session::open(&t.path.join("state")).unwrap();
        fs::write(session.root.join("private/prefix.ready"), "whisky-3.1.1").unwrap();
        fs::write(session.root.join("private/save"), "keep").unwrap();
        let before = inventory(&session.root.join("private")).unwrap();
        assert!(session
            .prepare(None, None, &|_| panic!("must refuse before setup"))
            .is_err());
        assert_eq!(before, inventory(&session.root.join("private")).unwrap());
        assert_eq!(
            fs::read_dir(session.root.join("runtimes")).unwrap().count(),
            0
        );
        fs::remove_file(session.root.join("private/prefix.ready")).unwrap();
        fs::create_dir(session.prefix()).unwrap();
        assert!(session.compatible_prefix().is_err());
        fs::write(session.root.join("private/prefix.runtime"), RUNTIME_ID).unwrap();
        session.compatible_prefix().unwrap();
    }
    #[test]
    fn shared_wine_environment_uses_reviewed_cef_path() {
        let t = scratch();
        let session = Session::open(&t.path.join("state")).unwrap();
        let command = session.wine(Path::new("/candidate/Libraries"));
        let vars: std::collections::BTreeMap<_, _> = command.get_envs().collect();
        assert_eq!(
            vars.get(OsStr::new("PEAR_STEAM_IN_PROCESS_GPU")),
            Some(&Some(OsStr::new("1")))
        );
        assert_eq!(
            vars.get(OsStr::new("PEAR_STEAM_WEBHELPER_PATH")),
            Some(&Some(OsStr::new(
                r"C:\Program Files (x86)\Steam\bin\cef\cef.win64\steamwebhelper.exe"
            )))
        );
        assert!(!vars.contains_key(OsStr::new("WINEMSYNC")));
    }
    #[test]
    fn steam_handoff_preserves_loader_and_existing_private_bundle() {
        let t = scratch();
        let session = Session::open(&t.path.join("state with spaces")).unwrap();
        fs::create_dir_all(session.prefix()).unwrap();
        let lib = t.path.join("signed runtime/Libraries");
        fs::create_dir_all(lib.join("Wine/bin")).unwrap();
        let loader = lib.join("Wine/bin/wine");
        let script = b"#!/bin/sh\nprintf '%s\\n' \"$@\" > \"$WINEPREFIX/request\"\nprintf '%s' \"$WINELOADER\" > \"$WINEPREFIX/loader\"\n";
        fs::write(&loader, script).unwrap();
        fs::set_permissions(&loader, fs::Permissions::from_mode(0o700)).unwrap();
        let old = session.root.join("private/Steam Preview.app");
        fs::create_dir(&old).unwrap();
        fs::write(old.join("retained-evidence"), b"keep").unwrap();
        let before = inventory(&old).unwrap();
        session.open_steam(&lib, &["-applaunch", GAME]).unwrap();
        assert_eq!(fs::read(&loader).unwrap(), script);
        assert_eq!(inventory(&old).unwrap(), before);
        assert_eq!(
            fs::read_to_string(session.prefix().join("loader")).unwrap(),
            loader.to_str().unwrap()
        );
        assert_eq!(
            fs::read_to_string(session.prefix().join("request")).unwrap(),
            format!(
                "start\n/unix\n{}\n-applaunch\n{}\n",
                session.steam().display(),
                GAME
            )
        );
        fs::write(&loader, b"#!/bin/sh\nexit 7\n").unwrap();
        assert!(session.open_steam(&lib, &["steam://open/games"]).is_err());
        assert_eq!(inventory(&old).unwrap(), before);
    }
    #[test]
    fn unpublished_artifact_refuses_network_fallback() {
        let t = scratch();
        let s = Session::open(&t.path.join("state")).unwrap();
        let unpublished = Artifact { url: "", ..RUNTIME };
        let error = s
            .archive_with(unpublished, None, |_| {
                panic!("unpublished input must not download")
            })
            .unwrap_err()
            .to_string();
        assert!(error.contains("no public runtime download"));
        assert_eq!(fs::read_dir(s.root.join("cache")).unwrap().count(), 0);
    }
    #[test]
    fn install_manifest_must_be_complete_and_unambiguous() {
        let installed =
            r#""AppState" { "appid" "3405340" "StateFlags" "4" "nested" { "value" "ok" } }"#;
        assert!(game_installed(installed));
        for bad in [
            installed.replace("3405340", "1"),
            installed.replace("\"4\"", "\"1026\""),
            installed.trim_end_matches('}').to_owned(),
            installed.replace("\"nested\"", "\"appid\""),
            installed.replace("\"appid\" \"3405340\"", ""),
        ] {
            assert!(!game_installed(&bad), "{bad}");
        }
        assert!(!game_installed(
            r#""AppState" { "nested" { "appid" "3405340" "StateFlags" "4" } }"#
        ));
    }
    #[test]
    fn installation_flow_retries_until_accepted_then_launches_once() {
        let mut flow = InstallFlow::default();
        let step = |flow: &mut InstallFlow, ready, present, seconds| {
            flow.next(ready, present, Duration::from_secs(seconds))
                .unwrap()
        };
        assert_eq!(step(&mut flow, false, false, 0), InstallAction::Request);
        assert_eq!(step(&mut flow, false, false, 14), InstallAction::Wait);
        assert_eq!(step(&mut flow, false, false, 16), InstallAction::Request);
        assert_eq!(step(&mut flow, false, true, 32), InstallAction::Wait);
        assert_eq!(step(&mut flow, true, true, 60), InstallAction::Launch);
        assert_eq!(step(&mut flow, true, true, 62), InstallAction::Wait);
        let mut timed_out = InstallFlow::default();
        assert!(timed_out
            .next(false, false, Duration::from_secs(3600))
            .is_err());
    }
    #[test]
    fn command_timeout_reaps_only_owned_child_and_preserves_failure() {
        let mut sentinel = Command::new("/bin/sleep").arg("10").spawn().unwrap();
        let start = Instant::now();
        assert!(run(Command::new("/bin/sleep").arg("10"), 1).is_err());
        assert!(start.elapsed() < Duration::from_secs(4));
        assert!(sentinel.try_wait().unwrap().is_none());
        sentinel.kill().unwrap();
        sentinel.wait().unwrap();
        assert!(run(&mut Command::new("/usr/bin/false"), 1).is_err());
        run(&mut Command::new("/usr/bin/true"), 1).unwrap();
    }
}

#[cfg(test)]
mod recovery_tests;
