"""Bounded data and exact-byte helpers for Wine component preparation."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat

REPO = Path(__file__).resolve().parents[2]
MAX_JSON = 8 * 1024 * 1024
MAX_FILE = 2 * 1024 * 1024 * 1024
MAX_NODES = 250000
MAX_DEPTH = 48
MAX_STRING = 262144
HEX256 = re.compile(r'[0-9a-f]{64}\Z')


class Error(Exception):
    """A stable public error code, without raw paths or subprocess diagnostics."""
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def need(condition, code):
    if not condition:
        raise Error(code)


def relative(value):
    need(isinstance(value, str) and 0 < len(value.encode('utf-8', 'surrogatepass')) <= 4096,
         'unsafe_path')
    need(not value.startswith(('/', '~')) and not any(c in value for c in ('\\', ':', '%'))
         and all(ord(c) >= 32 and ord(c) != 127 and not 0xD800 <= ord(c) <= 0xDFFF for c in value),
         'unsafe_path')
    parts = tuple(value.split('/'))
    need(len(parts) <= 64 and all(p not in ('', '.', '..') and len(p.encode('utf-8')) <= 255 for p in parts),
         'unsafe_path')
    return parts


def _identity(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def open_relative(root, value, directory=False):
    """Read descriptor-relative paths without following any relative component."""
    parts = relative(value)
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for index, part in enumerate(parts):
            is_dir = index < len(parts) - 1 or directory
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
            if is_dir:
                flags |= os.O_DIRECTORY
            new = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = new
            mode = os.fstat(fd).st_mode
            need(stat.S_ISDIR(mode) if is_dir else stat.S_ISREG(mode), 'nonregular_input')
        return fd
    except BaseException:
        os.close(fd)
        raise


def read_relative(root, value, limit=MAX_JSON):
    with os.fdopen(open_relative(root, value), 'rb') as stream:
        before = os.fstat(stream.fileno())
        need(before.st_size <= limit, 'input_size_limit')
        data = stream.read(limit + 1)
        need(len(data) <= limit, 'input_size_limit')
        need(_identity(before) == _identity(os.fstat(stream.fileno())), 'input_changed')
        return data


def sha256(path):
    """Hash an ordinary file, refusing symlink leaves, special files and changes."""
    path = Path(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        need(stat.S_ISREG(before.st_mode), 'nonregular_input')
        need(before.st_size <= MAX_FILE, 'input_size_limit')
        digest, size = hashlib.sha256(), 0
        while block := stream.read(1024 * 1024):
            size += len(block)
            need(size <= MAX_FILE, 'input_size_limit')
            digest.update(block)
        need(_identity(before) == _identity(os.fstat(stream.fileno())) and size == before.st_size,
             'input_changed')
        return digest.hexdigest()


def decode_json(data, max_bytes=MAX_JSON):
    need(isinstance(data, bytes) and len(data) <= max_bytes, 'input_size_limit')
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'duplicate_json_key')
            result[key] = value
        return result
    def forbidden(_):
        raise Error('noninteger_json_number')
    try:
        value = json.loads(data.decode('utf-8'), object_pairs_hook=pairs,
                           parse_constant=forbidden, parse_float=forbidden)
    except (UnicodeError, ValueError, RecursionError):
        raise Error('invalid_json') from None
    pending, count = [(value, 0)], 0
    while pending:
        item, depth = pending.pop()
        count += 1
        need(count <= MAX_NODES and depth <= MAX_DEPTH, 'json_structure_limit')
        if isinstance(item, dict):
            for key, child in item.items():
                need(len(key) <= 256, 'json_key_limit')
                pending.extend(((key, depth + 1), (child, depth + 1)))
        elif isinstance(item, list):
            pending.extend((child, depth + 1) for child in item)
        elif isinstance(item, str):
            need(len(item) <= MAX_STRING and all((ord(c) >= 32 or c in '\n\r\t') and ord(c) != 127
                 and not 0xD800 <= ord(c) <= 0xDFFF for c in item), 'json_string_limit')
        elif type(item) is int:
            need(abs(item) <= 2**53 - 1, 'json_integer_limit')
    need(isinstance(value, dict), 'invalid_document_shape')
    return value


def load_json(path, max_bytes=MAX_JSON):
    path = Path(path)
    return decode_json(read_relative(path.parent, path.name, max_bytes), max_bytes)


def record(value, kind):
    need(isinstance(value, dict), 'invalid_document_shape')
    need(type(value.get('schema_version')) is int and value['schema_version'] == 1,
         'unsupported_record_version')
    need(value.get('record_kind') == kind, 'unexpected_record_kind')
    return value


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')
