#!/usr/bin/env python3
"""Check Pear's local documentation routing and Apple source inventory offline.

Supports simple inline links/images and reference definitions, including angle
brackets and optional titles. Skips fenced/inline code, comments and external
URLs. This is not a full Markdown parser: reference-use resolution, heading
anchors, nested/escaped Markdown and raw HTML links require manual review.
No remote content, agent behavior or runtime qualification is verified.
"""

import argparse
from datetime import date
import json
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import unquote, urlsplit


ROUTER = "mydocs/skills/pear-apple-tooling/SKILL.md"
INVENTORY = "mydocs/skills/pear-apple-tooling/references/upstream.json"
GUIDE = "docs/development/apple-tooling.md"
REQUIRED_DOCS = (
    "README.md", "AGENTS.md", "CLAUDE.md", "host/AGENTS.md",
    "tests/AGENTS.md", "docs/AGENTS.md", ROUTER, GUIDE,
)
REPOSITORY = "https://github.com/apple/game-porting-toolkit"
MANIFEST = "game-porting-skills/.codex-plugin/plugin.json"
EXPERTS = {
    "using-metal-validation": (),
    "using-gpucapture": (),
    "using-gpudebug": (),
    "debugging-rendering-issues": (
        "references/tier-1-instant-checks.md",
        "references/tier-2-state-inspection.md",
        "references/tier-3-data-inspection.md",
    ),
    "presenting-metal-drawables": (
        "references/frame-pacing.md", "references/hdr-colorspace.md",
    ),
    "managing-metal-cpp-lifetimes": (),
}
# Mask ignored regions before finding links; preserve offsets for diagnostics.
IGNORED_START = re.compile(
    r"^ {0,3}(?:(?P<ticks>`{3,})[^`\n]*|(?P<tildes>~{3,})[^\n]*)$|<!--|(?P<code>`+)",
    re.M,
)
DESTINATION = r"(?:<(?P<angle>[^<>\n]+)>|(?P<plain>[^\s()<>]+))"
INLINE_LINK = re.compile(
    r"!?\[[^\]\n]*\]\([ \t]*" + DESTINATION
    + r"(?:[ \t]+(?:\"[^\"\n]*\"|'[^'\n]*'|\([^()\n]*\)))?[ \t]*\)"
)
REFERENCE = re.compile(r"^ {0,3}\[[^\]\n]+\]:[ \t]*" + DESTINATION, re.M)


def visible_markdown(text):
    """Mask complete code spans/blocks and comments, in source order."""
    chars = list(text)
    cursor = 0
    while match := IGNORED_START.search(text, cursor):
        end = match.end()
        if fence := (match.group("ticks") or match.group("tildes")):
            closing = re.compile(r"^ {0,3}" + re.escape(fence[0])
                                 + "{" + str(len(fence)) + r",}[ \t]*(?:\n|$)", re.M)
            close = closing.search(text, end)
            end = close.end() if close else len(text)
        elif match.group("code"):
            close = re.search(r"(?<!`)" + re.escape(match.group("code")) + r"(?!`)", text[end:])
            if close is None:
                cursor = end
                continue
            end += close.end()
        else:
            close = text.find("-->", end)
            end = close + 3 if close >= 0 else len(text)
        for i in range(match.start(), end):
            if chars[i] != "\n":
                chars[i] = " "
        cursor = end
    return "".join(chars)


def link_targets(text):
    visible = visible_markdown(text)
    for pattern in (INLINE_LINK, REFERENCE):
        for match in pattern.finditer(visible):
            yield match.group("angle") or match.group("plain"), text.count("\n", 0, match.start()) + 1


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field {key!r}")
        result[key] = value
    return result


class GovernanceCheck:
    def __init__(self, root):
        self.root = root
        self.errors = []
        self.local_links = 0

    def error(self, source, detail):
        self.errors.append(f"{source}: {detail}")

    def contained(self, path, source):
        try:
            resolved = path.resolve()
            if not resolved.is_relative_to(self.root):
                self.error(source, "resolved path escapes repository")
                return None
            return resolved
        except (OSError, RuntimeError, ValueError) as exc:
            self.error(source, f"cannot resolve path ({exc})")
            return None

    def read(self, name):
        path = self.contained(self.root / name, name)
        if path is None:
            return None
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            self.error(name, f"cannot read required file ({exc})")
            return None

    def local_target(self, source, target, line):
        location = f"{source}:{line}: {target!r}"
        try:
            if re.match(r"^[A-Za-z]:[/\\]", target):
                self.error(location, "absolute local drive path is not allowed")
                return None
            url = urlsplit(target)
            if url.scheme or url.netloc:
                return None
            path = unquote(url.path)
            if not path:
                return None  # Same-file fragments and queries have no file target.
            if Path(path).is_absolute():
                self.error(location, "absolute local path is not allowed")
                return None
            resolved = self.contained(self.root / source.parent / path, location)
            if resolved is None:
                return None
            if not resolved.exists():
                self.error(location, "missing local target")
                return None
            self.local_links += 1
            return resolved
        except (OSError, ValueError) as exc:
            self.error(location, f"invalid local target ({exc})")
            return None

    def check_documents(self):
        names = {Path(name) for name in REQUIRED_DOCS}
        # Follow contained directory aliases, but never escape or loop through
        # them. rglob skips directory symlinks and could silently omit documents.
        pending = [(Path("docs"), frozenset())]
        while pending:
            directory, ancestors = pending.pop()
            resolved = self.contained(self.root / directory, directory)
            if resolved is None:
                continue
            if resolved in ancestors:
                self.error(directory, "document directory symlink cycle")
                continue
            try:
                for path in sorted((self.root / directory).iterdir()):
                    name = path.relative_to(self.root)
                    if path.is_symlink() and self.contained(path, name) is None:
                        continue
                    if path.is_dir():
                        pending.append((name, ancestors | {resolved}))
                    elif path.suffix == ".md":
                        names.add(name)
            except OSError as exc:
                self.error(directory, f"cannot scan documents ({exc})")
        for source in sorted(names):
            text = self.read(source)
            if text is None:
                continue
            targets = {self.local_target(source, target, line) for target, line in link_targets(text)}
            if source.as_posix() == ROUTER:
                for required in (GUIDE, INVENTORY):
                    if self.root / required not in targets:
                        self.error(source, f"missing routing link to {required}")
        return len(names)

    def check_discovery(self):
        expected = self.root / "mydocs/skills"
        for name in (".agents/skills", ".claude/skills"):
            link = self.root / name
            resolved = self.contained(link, name)
            if not link.is_symlink() or resolved != expected or not expected.is_dir():
                self.error(name, "expected discovery symlink to mydocs/skills")

    def field(self, condition, name, expected):
        if not condition:
            self.error(INVENTORY, f"{name}: expected {expected}")
        return condition

    def entries(self, value, field, key):
        if not self.field(isinstance(value, list), field, "a list"):
            return {}
        result = {}
        for i, entry in enumerate(value):
            label = f"{field}[{i}]"
            if not self.field(isinstance(entry, dict), label, "an object"):
                continue
            identity = entry.get(key)
            if not self.field(isinstance(identity, str) and bool(identity.strip()), f"{label}.{key}", "a nonempty string"):
                continue
            if identity in result:
                self.error(INVENTORY, f"{field}: duplicate {key} {identity!r}")
            result[identity] = entry
        return result

    def check_inventory(self):
        raw = self.read(INVENTORY)
        if raw is None:
            return
        try:
            data = json.loads(raw, object_pairs_hook=unique_object)
        except ValueError as exc:
            self.error(INVENTORY, f"invalid JSON ({exc})")
            return
        if not self.field(isinstance(data, dict), "root", "an object"):
            return
        self.field(type(data.get("schema_version")) is int and data["schema_version"] == 1, "schema_version", "1")
        self.field(data.get("repository") == REPOSITORY, "repository", REPOSITORY)
        revision = data.get("revision")
        valid_pin = isinstance(revision, str) and re.fullmatch(r"[0-9a-fA-F]{40}", revision)
        self.field(bool(valid_pin), "revision", "a full immutable 40-hex Git revision")
        reviewed = data.get("reviewed_on")
        try:
            valid_date = isinstance(reviewed, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", reviewed) and date.fromisoformat(reviewed)
        except ValueError:
            valid_date = False
        self.field(bool(valid_date), "reviewed_on", "an ISO calendar date (YYYY-MM-DD)")

        def pinned_url(value, path, field):
            if valid_pin:
                expected = f"{REPOSITORY}/blob/{revision}/{path}"
                self.field(value == expected, field, expected)

        plugin = data.get("plugin")
        if self.field(isinstance(plugin, dict), "plugin", "an object"):
            self.field(plugin.get("name") == "game-porting-skills", "plugin.name", "game-porting-skills")
            version = plugin.get("version")
            self.field(isinstance(version, str) and bool(version.strip()), "plugin.version", "a nonempty version")
            self.field(plugin.get("manifest_path") == MANIFEST, "plugin.manifest_path", MANIFEST)
            pinned_url(plugin.get("url"), MANIFEST, "plugin.url")
        skills = self.entries(data.get("skills"), "skills", "name")
        self.field(set(skills) == set(EXPERTS), "skills", "exactly the six selected expert identities: " + ", ".join(EXPERTS))
        for name, entry in skills.items():
            field = f"skills.{name}"
            path = f"game-porting-skills/skills/{name}/SKILL.md"
            self.field(entry.get("path") == path, field + ".path", path)
            pinned_url(entry.get("url"), path, field + ".url")
            refs = self.entries(entry.get("references"), field + ".references", "path")
            for required in EXPERTS.get(name, ()):
                self.field(required in refs, field + ".references", required)
            for relative, ref in refs.items():
                parts = PurePosixPath(relative).parts
                self.field(bool(parts) and not relative.startswith("/") and ".." not in parts and "\\" not in relative and str(PurePosixPath(relative)) == relative,
                           field + ".references.path", f"a canonical relative path inside this skill, got {relative!r}")
                pinned_url(ref.get("url"), str(PurePosixPath(path).parent / relative), field + f".references[{relative}].url")
        tools = self.entries(data.get("tools"), "tools", "name")
        self.field(set(tools) == {"gpucapture", "gpudebug"}, "tools", "gpucapture and gpudebug")
        for name, entry in tools.items():
            self.field(entry.get("minimum_macos") == "27.0", f"tools.{name}.minimum_macos", "27.0 from the reviewed source")
            self.field(entry.get("requirement_skill") == f"using-{name}", f"tools.{name}.requirement_skill", f"using-{name}")

    def run(self):
        documents = self.check_documents()
        self.check_discovery()
        self.check_inventory()
        if self.errors:
            for error in self.errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print(f"PASS: {documents} documents, {self.local_links} local targets; skill routing and source inventory consistent (offline)")
        return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="repository root (default: parent of this script's tools directory)")
    args = parser.parse_args()
    try:
        root = args.root.resolve()
        if not root.is_dir():
            parser.error(f"repository root is not a directory: {args.root}")
    except (OSError, RuntimeError, ValueError) as exc:
        parser.error(f"cannot resolve repository root: {exc}")
    return GovernanceCheck(root).run()


if __name__ == "__main__":
    sys.exit(main())
