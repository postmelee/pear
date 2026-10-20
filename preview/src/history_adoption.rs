// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
//! Preservation-only admission for the history-only layout produced by 0.1.0.
use super::{need, plain_file, Result};
use std::{
    fs::{self, File},
    io::Read,
    os::{fd::AsRawFd, unix::fs::MetadataExt},
    path::Path,
};

const FOREIGN: &str = "This folder contains unrelated files. Select a new empty preview folder.";
const INVALID: &str = "Pear could not safely recover its previous setup. Existing files were kept.";

fn identity(path: &Path, directory: bool) -> Result<(u64, u64)> {
    let m = fs::symlink_metadata(path)?;
    // SAFETY: geteuid has no pointer arguments or side effects.
    need(
        m.uid() == unsafe { libc::geteuid() }
            && !m.file_type().is_symlink()
            && if directory {
                m.is_dir()
            } else {
                m.is_file() && m.nlink() == 1
            },
        INVALID,
    )?;
    Ok((m.dev(), m.ino()))
}

fn root_entries(root: &Path, history: bool) -> Result<()> {
    for entry in fs::read_dir(root)? {
        let entry = entry?;
        need(
            entry.file_name() == ".lock" || (history && entry.file_name() == "history"),
            FOREIGN,
        )?;
        if entry.file_name() == ".lock" {
            identity(&entry.path(), false)?;
        }
    }
    Ok(())
}

pub(super) struct Admission {
    root: (u64, u64),
    history: Option<(u64, u64)>,
    files: Vec<(String, (u64, u64), Vec<u8>)>,
    // Closing the descriptor releases the exclusive observer lock.
    _observer: Option<File>,
}

impl Admission {
    pub(super) fn recheck(&self, root: &Path) -> Result<()> {
        need(identity(root, true)? == self.root, INVALID)?;
        root_entries(root, self.history.is_some())?;
        if let Some(expected) = self.history {
            let history = root.join("history");
            need(identity(&history, true)? == expected, INVALID)?;
            need(fs::read_dir(&history)?.count() == self.files.len(), INVALID)?;
            for (name, id, bytes) in &self.files {
                need(identity(&history.join(name), false)? == *id, INVALID)?;
                need(read(&history.join(name))? == *bytes, INVALID)?;
            }
        }
        Ok(())
    }
}

fn read(path: &Path) -> Result<Vec<u8>> {
    let f = plain_file(path)?;
    need(
        f.metadata()?.is_file() && f.metadata()?.len() <= 32 * 1024 * 1024,
        INVALID,
    )?;
    let mut bytes = Vec::new();
    f.take(32 * 1024 * 1024 + 1).read_to_end(&mut bytes)?;
    need(bytes.len() <= 32 * 1024 * 1024, INVALID)?;
    Ok(bytes)
}

fn recognizable(bytes: &[u8]) -> bool {
    // Recognition is not consent or schema migration. Swift still decodes the
    // complete typed snapshot before any report can be queued or transmitted.
    let Ok(v) = serde_json::from_slice::<serde_json::Value>(bytes) else {
        return false;
    };
    let Some(o) = v.as_object() else { return false };
    v["schemaVersion"] == 1
        && v["runs"].is_array()
        && (v["shared"].is_object() || v["shared"].is_array())
        && v["policy"]["pending"].is_array()
        && (v["policy"]["revisions"].is_object() || v["policy"]["revisions"].is_array())
        && matches!(
            v["policy"]["consent"]["mode"].as_str(),
            Some("localOnly" | "askAfterExit" | "automatic")
        )
        && v["policy"]["consent"]["fields"].is_array()
        && v["policy"]["consent"]["generation"].is_u64()
        && o.keys().all(|k| {
            [
                "schemaVersion",
                "policy",
                "runs",
                "shared",
                "delivery",
                "serverDeletions",
            ]
            .contains(&k.as_str())
        })
}

pub(super) fn admit(root: &Path) -> Result<Admission> {
    let root_id = identity(root, true)?;
    let history = root.join("history");
    let present = fs::symlink_metadata(&history).is_ok();
    root_entries(root, present)?;
    let mut admission = Admission {
        root: root_id,
        history: None,
        files: vec![],
        _observer: None,
    };
    if !present {
        return Ok(admission);
    }
    admission.history = Some(identity(&history, true)?);
    // An empty arbitrary directory is not evidence of a Pear history store.
    let lock = history.join("observer.lock");
    let lock_id = identity(&lock, false)?;
    let observer = plain_file(&lock)?;
    let opened = observer.metadata()?;
    need((opened.dev(), opened.ino()) == lock_id, INVALID)?;
    // SAFETY: live owned descriptor; retained until root adoption is complete.
    need(
        unsafe { libc::flock(observer.as_raw_fd(), libc::LOCK_EX | libc::LOCK_NB) } == 0,
        "Another Pear window is using this history. Quit that Pear app and retry.",
    )?;
    admission._observer = Some(observer);
    for entry in fs::read_dir(&history)? {
        let entry = entry?;
        let name = entry.file_name().to_string_lossy().into_owned();
        need(name == "observer.lock" || name == "history.json", FOREIGN)?;
        let id = identity(&entry.path(), false)?;
        let bytes = read(&entry.path())?;
        need(
            if name == "observer.lock" {
                bytes.is_empty()
            } else {
                recognizable(&bytes)
            },
            INVALID,
        )?;
        admission.files.push((name, id, bytes));
    }
    admission.recheck(root)?;
    Ok(admission)
}
