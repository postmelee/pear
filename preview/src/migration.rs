// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
//! One reviewed upgrade, with a preserved prefix and atomic directory exchange.
use super::*;
use std::os::unix::fs::{symlink, MetadataExt};

pub(super) const PREVIOUS: &str = "pear-wine11-cw26.3-dxmt0.80-signed-v2";
const PREVIOUS_SHA: &str = "bf660c1ddf0a40cd2c7e345343b32f6515bf34c1fe6566aae337302f221a4127";
const TRANSITION: &str = "runtime-upgrade-signed-v3";
const OWNER: &str = "pear-signed-v2-to-v3\n";

fn directory(path: &Path) -> Result<()> {
    let m = fs::symlink_metadata(path)?;
    need(
        m.is_dir() && !m.file_type().is_symlink(),
        "Unexpected upgrade directory.",
    )
}
fn layout(prefix: &Path) -> Result<()> {
    for part in [
        "",
        "drive_c",
        "drive_c/windows",
        "drive_c/windows/system32",
        "drive_c/windows/syswow64",
    ] {
        directory(&prefix.join(part))?;
    }
    for name in ["system.reg", "user.reg", "userdef.reg"] {
        need(
            plain_file(&prefix.join(name))?.metadata()?.is_file(),
            "Unexpected prefix registry.",
        )?;
    }
    Ok(())
}

// Do not follow Wine's standard dosdevices or user-directory symlinks. APFS
// cloning preserves regular-file data/xattrs without duplicating installed games.
pub(super) fn clone_tree(source: &Path, dest: &Path) -> Result<()> {
    cancelled()?;
    let m = fs::symlink_metadata(source)?;
    if m.file_type().is_symlink() {
        symlink(fs::read_link(source)?, dest)?;
    } else if m.is_dir() {
        fs::DirBuilder::new().mode(0o700).create(dest)?;
        for entry in fs::read_dir(source)? {
            let entry = entry?;
            clone_tree(&entry.path(), &dest.join(entry.file_name()))?;
        }
    } else if m.is_file() {
        clone_file(source, dest)?;
    } else {
        return Err("The prefix contains a special file; automatic upgrade stopped.".into());
    }
    Ok(())
}
#[cfg(target_os = "macos")]
fn clone_file(source: &Path, dest: &Path) -> Result<()> {
    let source = std::ffi::CString::new(source.as_os_str().as_bytes())?;
    let dest = std::ffi::CString::new(dest.as_os_str().as_bytes())?;
    // SAFETY: live NUL-terminated paths; no pointers are retained.
    if unsafe {
        libc::clonefile(
            source.as_ptr(),
            dest.as_ptr(),
            0x0001, /* CLONE_NOFOLLOW from sys/clonefile.h */
        )
    } != 0
    {
        return Err(format!(
            "A storage-efficient upgrade copy could not be made: {}. Existing files were kept.",
            io::Error::last_os_error()
        )
        .into());
    }
    Ok(())
}
#[cfg(not(target_os = "macos"))]
fn clone_file(_: &Path, _: &Path) -> Result<()> {
    Err("Runtime upgrades require macOS clonefile support.".into())
}
#[cfg(target_os = "macos")]
fn exchange(first: &Path, second: &Path) -> Result<()> {
    let first = std::ffi::CString::new(first.as_os_str().as_bytes())?;
    let second = std::ffi::CString::new(second.as_os_str().as_bytes())?;
    // SAFETY: live NUL-terminated paths. RENAME_SWAP never leaves prefix absent.
    if unsafe {
        libc::renameatx_np(
            libc::AT_FDCWD,
            first.as_ptr(),
            libc::AT_FDCWD,
            second.as_ptr(),
            libc::RENAME_SWAP,
        )
    } != 0
    {
        return Err(io::Error::last_os_error().into());
    }
    Ok(())
}
#[cfg(not(target_os = "macos"))]
fn exchange(_: &Path, _: &Path) -> Result<()> {
    Err("Atomic runtime activation requires macOS.".into())
}
fn atomic_text(path: &Path, value: &str) -> Result<()> {
    let parent = path.parent().ok_or("Missing marker directory.")?;
    let stage = Stage::new(parent)?;
    let tmp = stage.path.join("marker");
    write_new(&tmp, value.as_bytes())?;
    fs::rename(tmp, path)?;
    File::open(parent)?.sync_all()?;
    Ok(())
}
fn same_bytes(a: &Path, b: &Path) -> Result<bool> {
    let a = plain_file(a)?;
    let b = plain_file(b)?;
    need(
        a.metadata()?.is_file() && b.metadata()?.is_file(),
        "Expected ordinary runtime files.",
    )?;
    Ok(sha256(&a, 200_000_000)? == sha256(&b, 200_000_000)?)
}
pub(super) fn verify_prefix(prefix: &Path, lib: &Path) -> Result<()> {
    layout(prefix)?;
    for (arch, system, dxmt) in [("x86_64", "system32", "x64"), ("i386", "syswow64", "x32")] {
        let runtime = lib.join("Wine/lib/wine").join(format!("{arch}-windows"));
        let installed = prefix.join("drive_c/windows").join(system);
        for name in ["ntdll.dll", "kernel32.dll", "kernelbase.dll"] {
            need(
                same_bytes(&runtime.join(name), &installed.join(name))?,
                "Core Windows files did not update. The previous environment was kept.",
            )?;
        }
        for item in fs::read_dir(&runtime)? {
            let item = item?;
            if ["d3d11.dll", "dxgi.dll", "d3d10core.dll", "winemetal.dll"]
                .iter()
                .any(|name| item.file_name() == *name)
            {
                continue;
            }
            let target = installed.join(item.file_name());
            if !target.try_exists()? {
                continue;
            }
            // Keep game-installed native DLLs; validate every installed Wine builtin.
            let mut file = plain_file(&target)?;
            let mut header = [0u8; 96];
            let n = file.read(&mut header)?;
            if n >= 85 && header[64..].starts_with(b"Wine builtin DLL\0") {
                need(same_bytes(&item.path(), &target)?, "A Windows builtin remains from the previous runtime. Upgrade was not activated.")?;
            }
        }
        for name in ["d3d11.dll", "dxgi.dll", "d3d10core.dll", "winemetal.dll"] {
            need(
                same_bytes(
                    &lib.join("DXMT").join(dxmt).join(name),
                    &installed.join(name),
                )?,
                "Graphics files did not update. Upgrade was not activated.",
            )?;
        }
    }
    Ok(())
}

// Detect changes made through another launcher while the copy was being prepared.
fn tree_stamp(root: &Path) -> Result<String> {
    fn walk(root: &Path, p: &Path, rows: &mut Vec<String>) -> Result<()> {
        let m = fs::symlink_metadata(p)?;
        rows.push(format!(
            "{:?}\t{}\t{}\t{}\t{}\t{}\t{}",
            p.strip_prefix(root)?,
            m.ino(),
            m.len(),
            m.mtime(),
            m.mtime_nsec(),
            m.ctime(),
            m.ctime_nsec()
        ));
        if m.is_dir() {
            for entry in fs::read_dir(p)? {
                walk(root, &entry?.path(), rows)?;
            }
        }
        Ok(())
    }
    let mut rows = Vec::new();
    walk(root, root, &mut rows)?;
    rows.sort();
    Ok(rows.join("\n"))
}
impl Session {
    fn wait_prefix(&self, lib: &Path, prefix: &Path) -> Result<()> {
        let mut command = Command::new(lib.join("Wine/bin/wineserver"));
        self.environment(&mut command, lib);
        command.env("WINEPREFIX", prefix).arg("-w");
        // This only waits. A timeout terminates the waiter, never the server/game.
        run(&mut command, 15).map_err(|_| "Close this installation's Steam and games, then retry. No running game was stopped.".into())
    }
    fn wine_at(&self, lib: &Path, prefix: &Path, args: &[&str]) -> Result<()> {
        run(self.wine(lib).env("WINEPREFIX", prefix).args(args), 180)
    }
    fn finish_upgrade(
        &self,
        lib: &Path,
        transition: &Path,
        original: u64,
        candidate: u64,
    ) -> Result<()> {
        let prefix = self.prefix();
        let backup = transition.join("prefix");
        need(
            fs::symlink_metadata(&prefix)?.ino() == candidate
                && fs::symlink_metadata(&backup)?.ino() == original,
            "Upgrade journal does not match the preserved environments.",
        )?;
        self.wait_prefix(lib, &prefix)?;
        verify_prefix(&prefix, lib)?;
        atomic_text(&self.root.join("private/prefix.runtime"), RUNTIME_ID)?;
        atomic_text(&self.root.join("private/prefix.ready"), RUNTIME_ID)?;
        Ok(())
    }
    pub(super) fn upgrade_prefix(&self, lib: &Path, notify: &dyn Fn(&str)) -> Result<()> {
        let ready = self.root.join("private/prefix.ready");
        if !ready.try_exists()? || text(&ready, 100)? == RUNTIME_ID {
            return Ok(());
        }
        need(
            RUNTIME_ID == "pear-wine11-cw26.3-dxmt0.80-signed-v3",
            "This target has no reviewed upgrade path.",
        )?;
        need(
            text(&ready, 100)? == PREVIOUS,
            "This runtime has no reviewed upgrade path.",
        )?;
        let old = self.root.join("runtimes").join(PREVIOUS);
        need(
            text(&old.join("inputs"), 512)? == format!("{PREVIOUS}\n{PREVIOUS_SHA}\n"),
            "Previous runtime identity changed.",
        )?;
        let old_lib = old.join("Libraries");
        let transition = self.root.join("private").join(TRANSITION);
        let prefix = self.prefix();
        layout(&prefix)?;
        self.wait_prefix(&old_lib, &prefix)?;
        need(
            text(&old.join("inventory"), 2_000_000)? == inventory(&old_lib)?,
            "Previous runtime files changed; upgrade stopped.",
        )?;
        if transition.try_exists()? {
            directory(&transition)?;
            need(
                text(&transition.join("owner"), 100)? == OWNER,
                "Unknown upgrade state was preserved.",
            )?;
            let journal = transition.join("exchange");
            if journal.try_exists()? {
                let s = text(&journal, 100)?;
                let ids: Vec<_> = s
                    .split_whitespace()
                    .map(str::parse::<u64>)
                    .collect::<std::result::Result<_, _>>()?;
                need(ids.len() == 2, "Invalid upgrade journal.")?;
                if fs::symlink_metadata(&prefix)?.ino() == ids[1] {
                    return self.finish_upgrade(lib, &transition, ids[0], ids[1]);
                }
                need(
                    fs::symlink_metadata(&prefix)?.ino() == ids[0],
                    "Original environment changed during upgrade.",
                )?;
            }
            for entry in fs::read_dir(&transition)? {
                let name = entry?.file_name();
                need(
                    ["owner", "prefix", "exchange"]
                        .iter()
                        .any(|allowed| name == *allowed),
                    "Unknown files in the upgrade folder were preserved.",
                )?;
            }
            // Only an unactivated, owned scratch copy can be retried/removed.
            if transition.join("prefix").try_exists()? {
                directory(&transition.join("prefix"))?;
                self.wait_prefix(lib, &transition.join("prefix"))?;
            }
            fs::remove_dir_all(&transition)?;
        }
        self.space(2 * 1024 * 1024 * 1024)?;
        notify("Updating the Windows environment. Your previous environment will be kept…");
        let before = tree_stamp(&prefix)?;
        fs::DirBuilder::new().mode(0o700).create(&transition)?;
        write_new(&transition.join("owner"), OWNER.as_bytes())?;
        let candidate = transition.join("prefix");
        clone_tree(&prefix, &candidate)?;
        self.wine_at(lib, &candidate, &["wineboot", "-u", "-r"])?;
        self.wait_prefix(lib, &candidate)?;
        // setupapi schedules in-use builtin replacements for this next boot.
        // -r processes those renames, without force/kill or startup applications.
        self.wine_at(lib, &candidate, &["wineboot", "-r"])?;
        self.wait_prefix(lib, &candidate)?;
        self.install_graphics(lib, &candidate)?;
        verify_prefix(&candidate, lib)?;
        self.wait_prefix(&old_lib, &prefix)?;
        need(
            tree_stamp(&prefix)? == before,
            "The original environment changed during upgrade. Close its applications and retry.",
        )?;
        let original = fs::symlink_metadata(&prefix)?.ino();
        let updated = fs::symlink_metadata(&candidate)?.ino();
        write_new(
            &transition.join("exchange"),
            format!("{original} {updated}\n").as_bytes(),
        )?;
        File::open(&transition)?.sync_all()?;
        cancelled()?;
        exchange(&prefix, &candidate)?;
        File::open(&transition)?.sync_all()?;
        File::open(self.root.join("private"))?.sync_all()?;
        self.finish_upgrade(lib, &transition, original, updated)
    }
    pub(super) fn install_graphics(&self, lib: &Path, prefix: &Path) -> Result<()> {
        for (arch, system) in [("x64", "system32"), ("x32", "syswow64")] {
            for name in ["d3d11.dll", "dxgi.dll", "d3d10core.dll", "winemetal.dll"] {
                replace_file(
                    &lib.join("DXMT").join(arch).join(name),
                    &prefix.join("drive_c/windows").join(system).join(name),
                    &self.root.join("private"),
                )?;
            }
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn scratch() -> Stage {
        Stage::new(&std::env::temp_dir()).unwrap()
    }
    fn fixture(prefix: &Path, lib: &Path) {
        fs::create_dir_all(prefix).unwrap();
        for name in ["system.reg", "user.reg", "userdef.reg"] {
            fs::write(prefix.join(name), "fixture registry").unwrap();
        }
        for (arch, system, dxmt) in [("x86_64", "system32", "x64"), ("i386", "syswow64", "x32")] {
            let runtime = lib.join("Wine/lib/wine").join(format!("{arch}-windows"));
            let installed = prefix.join("drive_c/windows").join(system);
            fs::create_dir_all(&runtime).unwrap();
            fs::create_dir_all(&installed).unwrap();
            for name in ["kernelbase.dll", "ntdll.dll", "kernel32.dll", "extra.dll"] {
                let mut bytes = vec![0; 64];
                bytes.extend_from_slice(b"Wine builtin DLL\0");
                bytes.extend_from_slice(b"synthetic fixture");
                fs::write(runtime.join(name), &bytes).unwrap();
                fs::write(installed.join(name), &bytes).unwrap();
            }
            let graphics = lib.join("DXMT").join(dxmt);
            fs::create_dir_all(&graphics).unwrap();
            for name in ["d3d11.dll", "dxgi.dll", "d3d10core.dll", "winemetal.dll"] {
                fs::write(graphics.join(name), b"graphics fixture").unwrap();
                fs::write(installed.join(name), b"graphics fixture").unwrap();
            }
        }
        fs::create_dir_all(lib.join("Wine/bin")).unwrap();
        fs::write(lib.join("Wine/bin/wineserver"), "#!/bin/sh\nexit 0\n").unwrap();
        fs::set_permissions(
            lib.join("Wine/bin/wineserver"),
            fs::Permissions::from_mode(0o700),
        )
        .unwrap();
    }
    #[test]
    fn stale_core_and_other_builtin_cannot_qualify() {
        let t = scratch();
        let p = t.path.join("prefix");
        let lib = t.path.join("Libraries");
        fixture(&p, &lib);
        verify_prefix(&p, &lib).unwrap();
        let f = p.join("drive_c/windows/syswow64/extra.dll");
        let mut data = fs::read(&f).unwrap();
        data.push(1);
        fs::write(&f, data).unwrap();
        assert!(verify_prefix(&p, &lib).is_err());
        fs::remove_file(f).unwrap();
        fs::write(
            p.join("drive_c/windows/system32/kernelbase.dll"),
            b"old core",
        )
        .unwrap();
        assert!(verify_prefix(&p, &lib).is_err());
    }
    #[test]
    fn graphics_mismatch_and_external_system_directory_are_rejected() {
        let t = scratch();
        let p = t.path.join("prefix");
        let lib = t.path.join("Libraries");
        fixture(&p, &lib);
        fs::write(p.join("drive_c/windows/syswow64/dxgi.dll"), b"old graphics").unwrap();
        assert!(verify_prefix(&p, &lib).is_err());
        let system = p.join("drive_c/windows/system32");
        let moved = t.path.join("outside");
        fs::rename(&system, &moved).unwrap();
        symlink(&moved, &system).unwrap();
        assert!(layout(&p).is_err());
    }
    #[test]
    fn stamp_detects_external_save_edits() {
        let t = scratch();
        fs::write(t.path.join("save"), b"old").unwrap();
        let before = tree_stamp(&t.path).unwrap();
        fs::write(t.path.join("save"), b"new progress").unwrap();
        assert_ne!(before, tree_stamp(&t.path).unwrap());
    }
    #[test]
    #[cfg(target_os = "macos")]
    fn clone_isolated_writes_preserve_original_and_symlinks() {
        let t = scratch();
        let original = t.path.join("original");
        fs::create_dir(&original).unwrap();
        fs::write(original.join("save"), b"retained").unwrap();
        symlink("save", original.join("alias")).unwrap();
        let before = tree_stamp(&original).unwrap();
        let copy = t.path.join("copy");
        clone_tree(&original, &copy).unwrap();
        fs::write(copy.join("save"), b"changed").unwrap();
        assert_eq!(fs::read(original.join("save")).unwrap(), b"retained");
        assert_eq!(
            fs::read_link(copy.join("alias")).unwrap(),
            Path::new("save")
        );
        assert_eq!(before, tree_stamp(&original).unwrap());
    }
    #[test]
    #[cfg(target_os = "macos")]
    fn interrupted_exchange_can_finish_without_losing_previous_state() {
        let t = scratch();
        let s = Session::open(&t.path.join("state")).unwrap();
        let transition = s.root.join("private").join(TRANSITION);
        fs::create_dir(&transition).unwrap();
        let lib = t.path.join("Libraries");
        fixture(&s.prefix(), &lib);
        fs::write(s.prefix().join("save"), b"original progress").unwrap();
        let candidate = transition.join("prefix");
        clone_tree(&s.prefix(), &candidate).unwrap();
        fs::write(candidate.join("save"), b"candidate").unwrap();
        fs::write(s.root.join("private/prefix.ready"), PREVIOUS).unwrap();
        let original = fs::metadata(s.prefix()).unwrap().ino();
        let updated = fs::metadata(&candidate).unwrap().ino();
        // Before exchange, a completion attempt must not relabel the original.
        assert!(s
            .finish_upgrade(&lib, &transition, original, updated)
            .is_err());
        assert_eq!(
            text(&s.root.join("private/prefix.ready"), 100).unwrap(),
            PREVIOUS
        );
        exchange(&s.prefix(), &candidate).unwrap();
        // Model a process interruption after atomic exchange but before readiness.
        s.finish_upgrade(&lib, &transition, original, updated)
            .unwrap();
        assert_eq!(
            text(&s.root.join("private/prefix.ready"), 100).unwrap(),
            RUNTIME_ID
        );
        assert_eq!(
            fs::read(candidate.join("save")).unwrap(),
            b"original progress"
        );
        assert_eq!(fs::read(s.prefix().join("save")).unwrap(), b"candidate");
        s.finish_upgrade(&lib, &transition, original, updated)
            .unwrap();
    }
    #[test]
    #[cfg(target_os = "macos")]
    fn failed_post_exchange_verification_keeps_backup_and_old_marker() {
        let t = scratch();
        let s = Session::open(&t.path.join("state")).unwrap();
        let transition = s.root.join("private").join(TRANSITION);
        fs::create_dir(&transition).unwrap();
        let lib = t.path.join("Libraries");
        fixture(&s.prefix(), &lib);
        let candidate = transition.join("prefix");
        clone_tree(&s.prefix(), &candidate).unwrap();
        fs::write(s.prefix().join("save"), b"original").unwrap();
        fs::write(
            candidate.join("drive_c/windows/system32/kernelbase.dll"),
            b"bad",
        )
        .unwrap();
        let original = fs::metadata(s.prefix()).unwrap().ino();
        let updated = fs::metadata(&candidate).unwrap().ino();
        fs::write(s.root.join("private/prefix.ready"), PREVIOUS).unwrap();
        exchange(&s.prefix(), &candidate).unwrap();
        assert!(s
            .finish_upgrade(&lib, &transition, original, updated)
            .is_err());
        assert_eq!(fs::read(candidate.join("save")).unwrap(), b"original");
        assert_eq!(
            text(&s.root.join("private/prefix.ready"), 100).unwrap(),
            PREVIOUS
        );
    }
}
