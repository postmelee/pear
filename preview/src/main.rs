// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
use pear_preview::{Result, Session};
use std::{io::Write, path::PathBuf};
fn main() {
    if let Err(error) = execute() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
fn execute() -> Result<()> {
    pear_preview::install_cancellation();
    let mut args = std::env::args_os().skip(1);
    let command = args.next().unwrap_or_else(|| "steam".into());
    if command == "--version" {
        println!(
            "Pear {} (Wine 11.0, DXMT 0.80; Rosetta required)",
            env!("CARGO_PKG_VERSION")
        );
        return Ok(());
    }
    if command == "--help" || command == "help" {
        println!("Pear (Rosetta required)\n\npear-preview [steam|setup|setup-info|megabonk|check-runtime] [--root PATH] [--runtime-archive PATH] [--steam-installer PATH]\n\nsetup-info: read-only setup and download information; no network or state changes.\n--version: show Pear and component versions.\nDefault: prepare and open Windows Steam. Sign in and choose games in your library.\nmegabonk: automatically install and launch the first validation game (legacy alias: play).\nSubsequent runs reuse private state. Other games have not been qualified.\nNo account credentials are accepted by this tool.");
        return Ok(());
    }
    if command != "setup-info"
        && command != "initialize"
        && command != "steam"
        && command != "megabonk"
        && command != "play"
        && command != "setup"
        && command != "check-runtime"
    {
        return Err("Unknown command. Use --help.".into());
    }
    let home = std::env::var_os("HOME").ok_or("HOME is unavailable.")?;
    let mut root = PathBuf::from(home).join("Library/Application Support/Pear Preview");
    let mut runtime = std::env::var_os("PEAR_PREVIEW_RUNTIME_ARCHIVE").map(PathBuf::from);
    let mut steam = None;
    let mut events = false;
    let mut seen = std::collections::BTreeSet::new();
    while let Some(key) = args.next() {
        if !seen.insert(key.clone()) {
            return Err("Duplicate option. Use --help.".into());
        }
        let value = args.next().ok_or("Missing option value. Use --help.")?;
        match key.to_str() {
            Some("--root") => root = value.into(),
            Some("--runtime-archive") => runtime = Some(PathBuf::from(value)),
            Some("--output") if value == "events" => events = true,
            Some("--steam-installer") => steam = Some(PathBuf::from(value)),
            _ => return Err("Unknown option. Use --help.".into()),
        }
    }
    if command == "setup-info" {
        println!("{}", pear_preview::setup_info(&root)?);
        return Ok(());
    }
    let session = Session::open(&root)?;
    if command == "initialize" {
        // Local ownership only: no downloads, runtime execution or reporting.
        println!("{}", pear_preview::setup_info(&root)?);
        return Ok(());
    }
    let notify = |s: &str| {
        if !events && s.starts_with("@download\t") {
            let fields: Vec<_> = s.split('\t').collect();
            println!(
                "Downloading {}: {} / {} bytes",
                fields[3], fields[1], fields[2]
            );
        } else {
            println!("{s}");
        }
        let _ = std::io::stdout().flush();
    };
    if command == "check-runtime" {
        session.runtime(runtime.as_deref(), &notify)?;
        notify("Runtime verified. Steam and game state were not started.");
        return Ok(());
    }
    let lib = session.prepare(runtime.as_deref(), steam.as_deref(), &notify)?;
    if command == "steam" {
        session.steam_library(&lib, &notify)?;
    } else if command == "megabonk" || command == "play" {
        session.play(&lib, &notify)?;
    } else {
        notify("Setup complete. Run pear-preview or open Pear.app to continue in Steam.");
    }
    Ok(())
}
