#!/usr/bin/env python3
"""Package only the reviewed Pear app and CLI; never walk a runtime/state root."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

REPO = Path(__file__).resolve().parent.parent
VERSION = "0.1.0-preview.1"
REQUIRED = {
    "Contents/Info.plist", "Contents/MacOS/PearPreview", "Contents/Resources/Pear.icns",
    "Contents/Resources/pear-preview", "Contents/Resources/THIRD_PARTY_NOTICES.md",
    "Contents/_CodeSignature/CodeResources",
}
OPTIONAL = {"Contents/Resources/LICENSE", "Contents/CodeResources"}


def audit_app(app):
    if app.is_symlink() or not app.is_dir() or app.name != "Pear Preview.app":
        raise ValueError("Expected the built Pear Preview.app directory, not a link.")
    found = set()
    for p in app.rglob("*"):
        relative = p.relative_to(app).as_posix()
        if p.is_symlink():
            raise ValueError(f"Unexpected package symlink: {relative}")
        if not p.is_file():
            continue
        notice = relative.startswith("Contents/Resources/licenses/") and p.suffix in {".txt", ".html", ".md"}
        if relative not in REQUIRED | OPTIONAL and not notice:
            raise ValueError(f"Unexpected package file: {relative}")
        found.add(relative)
    if missing := REQUIRED - found:
        raise ValueError(f"Incomplete app: {sorted(missing)}")
    if not any(p.startswith("Contents/Resources/licenses/") for p in found):
        raise ValueError("Linked-library license notices are missing.")
    return sorted(found)


def run(*args):
    subprocess.run([str(a) for a in args], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--release", action="store_true", help="Require clean licensed source, app distribution checks and CLI notarization; other release gates still apply.")
    args = parser.parse_args()
    # Check the caller's original path before resolve would erase a symlink.
    files = audit_app(args.app)
    app = args.app.resolve()
    out = args.output.resolve()
    if app == out or app in out.parents or out == REPO:
        raise ValueError("Select a separate, empty package output directory.")
    if out.exists() and any(out.iterdir()):
        raise ValueError("Package output must be empty; preserve previous candidates.")
    run("/usr/bin/codesign", "--verify", "--deep", "--strict", app)
    cli = app / "Contents/Resources/pear-preview"
    run("/usr/bin/codesign", "--verify", "--strict", cli)
    if args.release:
        if not (REPO / "LICENSE").is_file() or not (app / "Contents/Resources/LICENSE").is_file():
            raise ValueError("The approved product license must be present in source and app.")
        if subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO):
            raise ValueError("Release source must be committed and clean.")
        run("/usr/bin/xcrun", "stapler", "validate", app)
        run("/usr/sbin/spctl", "--assess", "--type", "execute", app)
        run("/usr/bin/syspolicy_check", "distribution", app)
        run("/usr/bin/codesign", "--verify", "--strict", "-R=notarized", "--check-notarization", cli)
    out.mkdir(parents=True, exist_ok=True)
    app_zip = out / f"Pear-{VERSION}-macos-arm64.zip"
    cli_zip = out / f"pear-preview-{VERSION}-macos-arm64-cli.zip"
    run("/usr/bin/ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", app, app_zip)
    with tempfile.TemporaryDirectory(prefix="pear-package-") as scratch:
        bundle = Path(scratch) / "pear-preview"
        bundle.mkdir()
        shutil.copy2(cli, bundle / "pear-preview")
        for name in ["THIRD_PARTY_NOTICES.md", "LICENSE"]:
            p = app / "Contents/Resources" / name
            if p.exists():
                shutil.copy2(p, bundle / name)
        shutil.copytree(app / "Contents/Resources/licenses", bundle / "licenses")
        (bundle / "README.txt").write_text(
            "Pear Preview (Apple Silicon, macOS 26+, Rosetta required)\n"
            "Run ./pear-preview to prepare and open Windows Steam.\n"
            "Sign in directly in Steam and choose games from your library.\n"
            "Run ./pear-preview --help for optional commands.\n"
            "Data: ~/Library/Application Support/Pear Preview\n"
            "Keep this folder to preserve Steam, games and saves.\n"
            "Source and status: https://github.com/postmelee/pear\n"
            + ("" if args.release else "DEVELOPMENT CANDIDATE: NOT FOR PUBLIC DISTRIBUTION.\n"), encoding="utf-8")
        run("/usr/bin/ditto", "-c", "-k", "--keepParent", bundle, cli_zip)
    artifacts = {}
    for p in [app_zip, cli_zip]:
        artifacts[p.name] = {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "size": p.stat().st_size}
    (out / "SHA256SUMS").write_text("".join(f"{v['sha256']}  {n}\n" for n, v in artifacts.items()))
    (out / "package-manifest.json").write_text(json.dumps({
        "version": VERSION,
        "candidate": not args.release,
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "source_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO)),
        "app_files": files,
        "artifacts": artifacts,
        "qualification": "Package checks alone do not establish game, recovery, license or clean-distribution qualification.",
    }, indent=2) + "\n")
    print(out)


if __name__ == "__main__":
    main()
