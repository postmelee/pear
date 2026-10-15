// SPDX-FileCopyrightText: 2026 Pear contributors
// SPDX-License-Identifier: GPL-3.0-or-later
//! Disposable source-seam checks; these do not qualify GUI or actual save recovery.
use super::*;

const FIXTURE: Artifact = Artifact {
    name: "fixture.tar",
    url: "https://example.invalid/pinned-fixture",
    size: 3,
    sha: "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
};

fn state() -> (Stage, Session, String) {
    let owner = Stage::new(&std::env::temp_dir()).unwrap();
    let session = Session::open(&owner.path.join("state with spaces")).unwrap();
    fs::write(
        session.root.join("private/save-sentinel"),
        b"existing progress",
    )
    .unwrap();
    let before = inventory(&session.root.join("private")).unwrap();
    (owner, session, before)
}
fn preserved(session: &Session, before: &str) {
    assert_eq!(inventory(&session.root.join("private")).unwrap(), before);
}
fn fixture_layout(stage: &Path) -> Result<()> {
    for name in [
        "Wine/bin/wine",
        "DXMT/x64/d3d11.dll",
        "Wine/share/pear/licenses/toolchain/provenance.json",
    ] {
        let p = stage.join("Libraries").join(name);
        fs::create_dir_all(p.parent().unwrap())?;
        fs::write(p, b"synthetic, not executable")?;
    }
    Ok(())
}

#[test]
fn partial_download_failure_reopens_and_retries_without_activating_partial_bytes() {
    let (_owner, session, before) = state();
    let root = session.root.clone();
    let error = session
        .archive_with(FIXTURE, None, |p| {
            fs::write(p, b"ab")?;
            Err("injected download interruption".into())
        })
        .unwrap_err()
        .to_string();
    assert_eq!(error, "injected download interruption");
    assert_eq!(fs::read_dir(root.join("cache")).unwrap().count(), 0);
    preserved(&session, &before);
    drop(session);
    let reopened = Session::open(&root).unwrap();
    let archive = reopened
        .archive_with(FIXTURE, None, |p| {
            fs::write(p, b"abc")?;
            Ok(())
        })
        .unwrap();
    assert_eq!(archive, root.join("cache/fixture.tar"));
    assert_eq!(
        reopened
            .archive_with(FIXTURE, None, |_| panic!("verified cache must be reused"))
            .unwrap(),
        archive
    );
    preserved(&reopened, &before);
}

#[test]
fn truncated_and_wrong_downloads_never_activate_and_missing_input_does_not_fallback() {
    let (_owner, session, before) = state();
    for bytes in [b"ab".as_slice(), b"bad".as_slice()] {
        assert!(session
            .archive_with(FIXTURE, None, |p| {
                fs::write(p, bytes)?;
                Ok(())
            })
            .is_err());
        assert_eq!(fs::read_dir(session.root.join("cache")).unwrap().count(), 0);
        preserved(&session, &before);
    }
    assert!(session
        .archive_with(FIXTURE, Some(&session.root.join("missing")), |_| panic!(
            "must not replace missing input by network"
        ))
        .is_err());
    preserved(&session, &before);
}

#[test]
fn corrupt_cache_redownloads_but_supplied_and_unpublished_inputs_remain_safe() {
    let (owner, session, before) = state();
    let cached = session.root.join("cache/fixture.tar");
    let unrelated = session.root.join("cache/unrelated");
    fs::write(&unrelated, b"keep").unwrap();
    fs::write(&cached, b"bad").unwrap();
    let supplied = owner.path.join("verified.tar");
    fs::write(&supplied, b"abc").unwrap();
    assert_eq!(
        session
            .archive_with(FIXTURE, Some(&supplied), |_| panic!("no download"))
            .unwrap(),
        supplied.canonicalize().unwrap()
    );
    assert_eq!(fs::read(&cached).unwrap(), b"bad");
    let offline = Artifact { url: "", ..FIXTURE };
    assert!(session
        .archive_with(offline, None, |_| panic!("no public endpoint"))
        .is_err());
    assert_eq!(fs::read(&cached).unwrap(), b"bad");
    assert!(session
        .archive_with(FIXTURE, None, |p| {
            fs::write(p, b"a")?;
            Err("network interrupted".into())
        })
        .is_err());
    assert!(!cached.exists());
    assert_eq!(fs::read_dir(session.root.join("cache")).unwrap().count(), 1);
    assert_eq!(
        session
            .archive_with(FIXTURE, None, |p| {
                fs::write(p, b"abc")?;
                Ok(())
            })
            .unwrap(),
        cached
    );
    assert_eq!(fs::read(&cached).unwrap(), b"abc");
    assert_eq!(fs::read(unrelated).unwrap(), b"keep");
    preserved(&session, &before);
}

#[test]
fn cache_link_is_not_replaced_or_followed_by_retry() {
    let (owner, session, before) = state();
    let outside = owner.path.join("outside");
    fs::write(&outside, b"bad").unwrap();
    let cached = session.root.join("cache/fixture.tar");
    std::os::unix::fs::symlink(&outside, &cached).unwrap();
    assert!(session
        .archive_with(FIXTURE, None, |_| panic!("must refuse link"))
        .is_err());
    assert!(cached.is_symlink());
    assert_eq!(fs::read(&outside).unwrap(), b"bad");
    fs::remove_file(outside).unwrap();
    assert!(session
        .archive_with(FIXTURE, None, |_| panic!("must refuse dangling link"))
        .is_err());
    assert!(cached.is_symlink());
    preserved(&session, &before);
}

#[test]
fn partial_extraction_failure_retries_and_reuses_only_complete_inventory() {
    let (owner, session, before) = state();
    let root = session.root.clone();
    let archive = owner.path.join("fixture.tar");
    fs::write(&archive, b"abc").unwrap();
    let error = session
        .install_runtime(&archive, |_, stage| {
            fixture_layout(stage)?;
            Err("injected extraction interruption".into())
        })
        .unwrap_err()
        .to_string();
    assert_eq!(error, "injected extraction interruption");
    assert_eq!(fs::read_dir(root.join("runtimes")).unwrap().count(), 0);
    preserved(&session, &before);
    drop(session);
    let reopened = Session::open(&root).unwrap();
    let library = reopened
        .install_runtime(&archive, |_, stage| fixture_layout(stage))
        .unwrap();
    let before_runtime = inventory(&root.join("runtimes")).unwrap();
    assert_eq!(
        reopened
            .runtime(Some(&owner.path.join("missing")), &|_| {})
            .unwrap(),
        library
    );
    assert_eq!(before_runtime, inventory(&root.join("runtimes")).unwrap());
    preserved(&reopened, &before);
}

#[test]
fn invalid_layout_and_failed_replacement_keep_previous_runtime_and_private_state() {
    let (owner, session, before) = state();
    let archive = owner.path.join("fixture.tar");
    assert!(session
        .install_runtime(&archive, |_, stage| {
            fs::create_dir(stage.join("Libraries"))?;
            Ok(())
        })
        .is_err());
    assert_eq!(
        fs::read_dir(session.root.join("runtimes")).unwrap().count(),
        0
    );
    session
        .install_runtime(&archive, |_, stage| fixture_layout(stage))
        .unwrap();
    let runtime_before = inventory(&session.root.join("runtimes")).unwrap();
    assert!(session
        .install_runtime(&archive, |_, stage| {
            fixture_layout(stage)?;
            Err("injected update failure".into())
        })
        .is_err());
    assert_eq!(
        inventory(&session.root.join("runtimes")).unwrap(),
        runtime_before
    );
    assert!(session
        .install_runtime(&archive, |_, stage| fixture_layout(stage))
        .is_err());
    assert_eq!(
        inventory(&session.root.join("runtimes")).unwrap(),
        runtime_before
    );
    preserved(&session, &before);
}

#[test]
fn insufficient_space_check_is_actionable_and_does_not_modify_state() {
    let (_owner, session, before) = state();
    let error = session.space(u64::MAX).unwrap_err().to_string();
    assert!(error.contains("More free storage"));
    assert!(error.contains("saves were kept"));
    assert_eq!(
        fs::read_dir(session.root.join("runtimes")).unwrap().count(),
        0
    );
    preserved(&session, &before);
}

#[test]
fn partial_prefix_requires_matching_runtime_and_never_becomes_ready_by_inspection() {
    let (_owner, session, _) = state();
    fs::create_dir(session.prefix()).unwrap();
    fs::write(
        session.root.join("private/prefix.runtime"),
        "foreign-runtime",
    )
    .unwrap();
    let foreign = inventory(&session.root.join("private")).unwrap();
    assert!(session.compatible_prefix().is_err());
    preserved(&session, &foreign);
    fs::write(session.root.join("private/prefix.runtime"), RUNTIME_ID).unwrap();
    let matching = inventory(&session.root.join("private")).unwrap();
    session.compatible_prefix().unwrap();
    assert!(!session.root.join("private/prefix.ready").exists());
    preserved(&session, &matching);
}
