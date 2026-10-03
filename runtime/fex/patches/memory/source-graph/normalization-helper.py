"""Private pure proposal: reversible Git metadata for closed new-file paths.

This module performs no filesystem writes, subprocess calls, source compilation
or module initialization. Callers pass their pinned historical strict parser.
The historical strict bytes remain the authority for all source hunk contents.
"""
from __future__ import annotations

import re


class CanonicalizationError(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise CanonicalizationError(code)


def closed_rows(rows):
    require(isinstance(rows, list) and rows, "changes_shape")
    by_path = {}
    for row in rows:
        require(isinstance(row, dict) and set(row) == {
            "path", "preimage_sha256", "postimage_sha256", "postimage_bytes"
        }, "change_fields")
        path = row["path"]
        require(isinstance(path, str) and re.fullmatch(r"[A-Za-z0-9_.+/-]+", path)
                and not path.startswith("/") and all(p not in ("", ".", "..") for p in path.split("/")),
                "change_path")
        require(path not in by_path, "duplicate_change")
        require(row["preimage_sha256"] is None or isinstance(row["preimage_sha256"], str)
                and re.fullmatch(r"[0-9a-f]{64}", row["preimage_sha256"]), "preimage_digest")
        require(isinstance(row["postimage_sha256"], str)
                and re.fullmatch(r"[0-9a-f]{64}", row["postimage_sha256"]), "postimage_digest")
        require(type(row["postimage_bytes"]) is int and 0 < row["postimage_bytes"] <= 8 * 1024**2,
                "postimage_size")
        by_path[path] = row
    return by_path


def render_git_derivative(strict_raw, rows, patch_sections):
    """Add only one exact mode line for each manifest-declared new regular file.

    `patch_sections` is the unchanged historical pure parser supplied by caller.
    The caller separately replays every source preimage/postimage and supplies
    exact pinned strict_raw bytes; existing files never acquire mode metadata.
    """
    require(type(strict_raw) is bytes and len(strict_raw) <= 2 * 1024**2, "strict_size")
    by_path = closed_rows(rows)
    sections = patch_sections(strict_raw)
    require(set(sections) == set(by_path), "changed_path_closure")
    result = bytearray()
    for path, lines in sections.items():
        row = by_path[path]
        require(lines[:2] == ["--- " + ("/dev/null" if row["preimage_sha256"] is None else "a/" + path) + "\n",
                             "+++ b/" + path + "\n"], "strict_file_header")
        result.extend(("diff --git a/" + path + " b/" + path + "\n").encode())
        if row["preimage_sha256"] is None:
            result.extend(b"new file mode 100644\n")
        result.extend("".join(lines).encode())
    require(len(result) <= 2 * 1024**2, "derivative_size")
    # This parser reconstructs exact section order; do not normalize formatting.
    restored = bytearray()
    for path, lines in sections.items():
        restored.extend(("diff --git a/" + path + " b/" + path + "\n").encode())
        restored.extend("".join(lines).encode())
    require(bytes(restored) == strict_raw, "strict_format_changed")
    return bytes(result)


def normalize_git_derivative(git_raw, strict_raw, rows, patch_sections):
    """Refuse every derivative other than the exact inverse of selected bytes.

    No arbitrary Git metadata is stripped. Exact reproduction permits only a
    declared-null-preimage `new file mode 100644` line directly after its matching
    diff header. Old/new/deleted modes, executable new files, index/rename/copy
    headers, duplicate/missing creation metadata and changed hunks all refuse.
    """
    require(type(git_raw) is bytes and len(git_raw) <= 2 * 1024**2, "derivative_size")
    require(git_raw == render_git_derivative(strict_raw, rows, patch_sections),
            "unreviewed_git_derivative")
    # Equality is stronger than a permissive metadata filter. Source hunk replay
    # still uses the unchanged historical parser on the exact selected bytes.
    return strict_raw


def portable_controls(patch_sections):
    """Original finite metadata controls; no git/source process is run."""
    existing = b"diff --git a/existing.cpp b/existing.cpp\n--- a/existing.cpp\n+++ b/existing.cpp\n@@ -1 +1 @@\n-old\n+new\n"
    new = b"diff --git a/new.h b/new.h\n--- /dev/null\n+++ b/new.h\n@@ -0,0 +1 @@\n+new\n"
    rows = [dict(path="existing.cpp", preimage_sha256="a"*64, postimage_sha256="b"*64, postimage_bytes=4),
            dict(path="new.h", preimage_sha256=None, postimage_sha256="c"*64, postimage_bytes=4)]
    strict = existing + new
    rendered = render_git_derivative(strict, rows, patch_sections)
    assert rendered == existing + new.replace(b"\n--- /dev/null", b"\nnew file mode 100644\n--- /dev/null")
    assert normalize_git_derivative(rendered, strict, rows, patch_sections) == strict
    rejected = 0
    mutations = [rendered.replace(b"100644", b"100755"),
                 rendered.replace(b"new file mode 100644\n", b"new file mode 100644\nnew file mode 100644\n"),
                 rendered.replace(b"new file mode 100644\n", b""),
                 rendered.replace(b"--- a/existing.cpp", b"new file mode 100644\n--- a/existing.cpp"),
                 rendered.replace(b"--- /dev/null", b"index 0000000..abcdef0\n--- /dev/null"),
                 rendered.replace(b"--- a/existing.cpp", b"old mode 100644\nnew mode 100755\n--- a/existing.cpp"),
                 rendered.replace(b"+new\n", b"+changed\n", 1),
                 rendered.replace(b"new file mode 100644", b"deleted file mode 100644")]
    for raw in mutations:
        try:
            normalize_git_derivative(raw, strict, rows, patch_sections)
        except CanonicalizationError:
            rejected += 1
    assert rejected == len(mutations)
    for changed in [rows + rows[:1], [{**rows[0], "path": "../outside"}, rows[1]],
                    [{**rows[0], "postimage_bytes": True}, rows[1]],
                    [{**rows[0], "unselected": True}, rows[1]]]:
        try:
            render_git_derivative(strict, changed, patch_sections)
        except CanonicalizationError:
            rejected += 1
    assert rejected == len(mutations) + 4
    return {"roundtrip_controls": 2, "refusal_controls": rejected,
            "git_execution_performed": False, "source_build_performed": False}
