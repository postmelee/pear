"""Task #9 glue reusing #3 build verification and bounded process capture."""
import hashlib
import importlib.util
import os
import stat
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
experiment_build = load('task9_original_build', REPO / 'experiments/manager/build.py')
experiment_cases = load('task9_original_cases', REPO / 'experiments/manager/run_cases.py')


def fixture_input_identity(root, policy):
    """Record owned test inputs without following links or reading special files."""
    root = Path(root)
    identity = root.stat()
    files = {}
    for path in sorted(root.rglob('*')):
        info = path.lstat()
        item = {'device': info.st_dev, 'inode': info.st_ino,
                'mode': stat.S_IMODE(info.st_mode), 'size': info.st_size}
        if stat.S_ISREG(info.st_mode):
            item.update(kind='regular', sha256=experiment_build.digest(path))
        elif stat.S_ISLNK(info.st_mode):
            item.update(kind='symlink', target_sha256=hashlib.sha256(os.fsencode(os.readlink(path))).hexdigest())
        elif stat.S_ISDIR(info.st_mode):
            item['kind'] = 'directory'
        else:
            item.update(kind='special', file_type=stat.S_IFMT(info.st_mode))
        files[path.relative_to(root).as_posix()] = item
    return {'root_identity': {'device': identity.st_dev, 'inode': identity.st_ino},
            'readonly': bool(os.statvfs(root).f_flag & os.ST_RDONLY),
            'policy_sha256': experiment_build.digest(policy), 'files': files}
