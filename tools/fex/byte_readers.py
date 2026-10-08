"""Bounded byte readers reused from Wine without its component entrypoints.

Bodies come from tools/wine/toolchain.py. Keep the historical owner unchanged;
FEX wrappers supply component-specific input/output and qualification policy.
"""
import posixpath
from pathlib import Path, PurePosixPath
import struct
if __package__:
    from .common import need, relative, sha256
else:
    from common import need, relative, sha256
MACH_ARM64 = 0x100000C
MAX_ARCHIVE_MTIME = (2**63 - 1) // 1_000_000_000

def inspect_macho(path):
    """Read the ARM64 slice and its load commands without executing the file."""
    path = Path(path)
    need(path.stat().st_size <= 1024**3, "macho_size_limit")
    data = path.read_bytes()
    need(len(data) >= 8, "truncated_macho")
    offset = 0
    size = len(data)
    architectures = []
    magic = data[:4]
    if magic in (b"\xca\xfe\xba\xbe", b"\xca\xfe\xba\xbf"):
        count = struct.unpack_from(">I", data, 4)[0]
        stride = 32 if magic[-1] == 0xBF else 20
        need(0 < count <= 32 and 8 + count * stride <= len(data), "invalid_fat_header")
        selected = None
        for index in range(count):
            at = 8 + index * stride
            cpu = struct.unpack_from(">I", data, at)[0]
            if stride == 32:
                start, length = struct.unpack_from(">QQ", data, at + 8)
            else:
                start, length = struct.unpack_from(">II", data, at + 8)
            need(start >= 8 + count * stride and start + length <= len(data), "invalid_fat_slice")
            architectures.append(cpu)
            if cpu == MACH_ARM64:
                need(selected is None, "ambiguous_arm64_slice")
                selected = (start, length)
        need(selected is not None, "missing_arm64_slice")
        offset, size = selected
    else:
        need(magic == b"\xcf\xfa\xed\xfe", "not_macho64")
        architectures.append(struct.unpack_from("<I", data, 4)[0])
    need(size >= 32 and data[offset:offset + 4] == b"\xcf\xfa\xed\xfe", "not_arm64_macho64")
    cpu, subtype, filetype, count, command_bytes = struct.unpack_from("<IIIII", data, offset + 4)
    need(cpu == MACH_ARM64 and count <= 65536 and 32 + command_bytes <= size, "invalid_arm64_commands")
    dependencies, rpaths = [], []
    at = offset + 32
    end = at + command_bytes
    for _ in range(count):
        need(at + 8 <= end, "truncated_load_command")
        cmd, length = struct.unpack_from("<II", data, at)
        need(length >= 8 and at + length <= end, "invalid_load_command")
        if cmd in (0xC, 0x18, 0x80000018, 0x1F, 0x8000001F, 0x20, 0x23, 0x80000023, 0x8000001C):
            need(length >= 12, "invalid_load_string")
            start = struct.unpack_from("<I", data, at + 8)[0]
            need(12 <= start < length, "invalid_load_string")
            raw = data[at + start:at + length]
            need(b"\0" in raw, "unterminated_load_string")
            text = raw.split(b"\0", 1)[0].decode("utf-8", errors="strict")
            (rpaths if cmd == 0x8000001C else dependencies).append(text)
        at += length
    need(at == end, "load_command_size_mismatch")
    return {"architectures": architectures, "selected_cpu": cpu, "subtype": subtype,
            "filetype": filetype, "dependencies": dependencies, "rpaths": rpaths}

def inspect_closure(path, root):
    """Resolve bundled libraries; OS shared-cache dependencies are explicit inputs."""
    root, executable = Path(root).resolve(), Path(path).resolve()
    need(executable.is_relative_to(root), "tool_outside_bundle")
    found, pending = {}, [(executable, [])]
    while pending:
        current, inherited_rpaths = pending.pop()
        if str(current) in found:
            continue
        need(current.is_relative_to(root), "dependency_outside_bundle")
        info = inspect_macho(current)
        expanded = []
        for item in info["rpaths"]:
            expanded.append(item.replace("@loader_path", str(current.parent)).replace(
                "@executable_path", str(executable.parent)))
        paths = expanded + inherited_rpaths
        resolved = []
        for dep in info["dependencies"]:
            if dep.startswith(("/usr/lib/", "/System/Library/")):
                resolved.append({"name": dep, "kind": "macos_system_dependency"})
                continue
            name = dep.replace("@loader_path", str(current.parent)).replace(
                "@executable_path", str(executable.parent))
            candidates = [Path(name)]
            if name.startswith("@rpath/"):
                candidates = [Path(base) / name[7:] for base in paths]
            hits = {p.resolve() for p in candidates if p.is_file()}
            need(len(hits) == 1, "unresolved_or_ambiguous_dependency")
            target = hits.pop()
            need(target.is_relative_to(root), "dependency_outside_bundle")
            resolved.append({"name": dep, "kind": "bundled", "path": str(target)})
            pending.append((target, paths))
        found[str(current)] = {"path": str(current), "sha256": sha256(current),
                               **info, "resolved_dependencies": resolved}
    return list(found.values())

def archive_members(archive, expected_root, max_bytes):
    """Validate the complete member graph before writing any extracted member."""
    need(isinstance(max_bytes, int) and 0 < max_bytes <= 4 * 1024**3, "invalid_archive_budget")
    result, names, links, total = [], set(), {}, 0
    for member in archive.getmembers():
        name = member.name.rstrip("/")
        parts = relative(name)
        need(parts[0] == expected_root, "archive_root_mismatch")
        if len(parts) == 1:
            need(member.isdir(), "invalid_archive_root")
            continue
        rel = "/".join(parts[1:])
        need(rel not in names, "duplicate_archive_member")
        names.add(rel)
        need(member.isfile() or member.isdir() or member.issym() or member.islnk(), "special_archive_member")
        if member.isfile():
            # The locked releases use whole seconds; bound signed-64-bit nanoseconds.
            need(type(member.mtime) is int and 0 <= member.mtime <= MAX_ARCHIVE_MTIME,
                 "invalid_archive_mtime")
            total += member.size
            need(member.size >= 0 and total <= max_bytes, "archive_expansion_limit")
        if member.issym():
            target = member.linkname
            need(target and not target.startswith("/") and "\\" not in target, "unsafe_archive_link")
            dest = posixpath.normpath(posixpath.join(posixpath.dirname(rel), target))
            relative(dest)
            links[rel] = dest
        elif member.islnk():
            target_parts = relative(member.linkname)
            need(target_parts[0] == expected_root and len(target_parts) > 1, "unsafe_archive_hardlink")
            links[rel] = "/".join(target_parts[1:])
        result.append((member, rel))
    for _, rel in result:
        for parent in PurePosixPath(rel).parents:
            need(str(parent) not in links, "archive_link_parent")
    for origin, target in links.items():
        visited = {origin}
        while target in links:
            need(target not in visited, "archive_link_cycle")
            visited.add(target)
            target = links[target]
        need(target in names, "archive_dangling_link")
    return result, total

def coff_machine(path):
    data = Path(path).read_bytes()
    need(len(data) >= 20, "truncated_coff")
    at = 0
    if data[:2] == b"MZ":
        need(len(data) >= 64, "truncated_dos_header")
        at = struct.unpack_from("<I", data, 60)[0]
        need(at + 24 <= len(data) and data[at:at + 4] == b"PE\0\0", "invalid_pe_header")
        at += 4
    return struct.unpack_from("<H", data, at)[0]
