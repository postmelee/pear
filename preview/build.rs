// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
use std::{env, path::PathBuf, process::Command};
fn main() {
    let out = PathBuf::from(env::var_os("OUT_DIR").unwrap());
    let object = out.join("bridge.o");
    assert!(Command::new("/usr/bin/xcrun")
        .args([
            "clang",
            "-arch",
            "arm64",
            "-mmacosx-version-min=26.0",
            "-O2",
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-Wno-deprecated-declarations",
            "-c",
            "../manager/native/bridge.c",
            "-o",
        ])
        .arg(&object)
        .status()
        .unwrap()
        .success());
    assert!(Command::new("/usr/bin/ar")
        .arg("rcs")
        .arg(out.join("libpreview_bridge.a"))
        .arg(object)
        .status()
        .unwrap()
        .success());
    println!("cargo:rustc-link-search=native={}", out.display());
    println!("cargo:rustc-link-lib=static=preview_bridge");
    println!("cargo:rustc-link-lib=proc");
    println!("cargo:rerun-if-changed=../manager/native/bridge.c");
    println!("cargo:rerun-if-changed=../manager/native/bridge.h");
}
