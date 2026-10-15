# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: MIT
"""Original stable input reads and finite owned-game copy guards.

Historical D24 selectors, paths, builders and grants are deliberately absent.
Current candidate authority is supplied by the explicit game context.
"""
from pathlib import Path
import hashlib
import json
import os
import stat
from pear_runtime.errors import need
from pear_runtime.assembly._common import decode_json
from pear_runtime.fixtures.inputs import read, save, fact
from pear_runtime.fixtures.admission import prefix_inventory

def identity(s):
    return (s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns)

def regular(path):
    p=Path(path)
    need(p.is_absolute() and '..' not in p.parts and p.resolve(strict=True)==p,
         'd24_input_alias')
    s=p.lstat();need(stat.S_ISREG(s.st_mode),'d24_input_regular')
    return p,s

class Ledger:
    """Read through no-follow descriptors and recheck every admitted byte at end."""
    def __init__(self):self.rows={};self.closed=False

    def check(self,row,keep=False,sha1=None):
        need(not self.closed,'d24_ledger_closed')
        need(type(row) is dict and set(row)=={'path','sha256','size_bytes'},'d24_reference_shape')
        need(type(row['path']) is str and type(row['size_bytes']) is int and
             0<=row['size_bytes']<=8*1024**3 and type(row['sha256']) is str and
             len(row['sha256'])==64 and all(c in '0123456789abcdef' for c in row['sha256']),
             'game_ledger_reference_identity')
        p,s=regular(row['path']);h=hashlib.sha256();one=hashlib.sha1();chunks=[]
        need(s.st_size==row['size_bytes'],'d24_input_changed')
        need(not keep or s.st_size<=64*1024**2,'d24_record_limit')
        # A regular-to-FIFO swap must not block an inspection before fstat refuses it.
        fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        try:
            need(identity(os.fstat(fd))==identity(s),'d24_open_race')
            consumed=0
            while True:
                b=os.read(fd,min(1024*1024,row['size_bytes']-consumed+1))
                if not b:break
                consumed+=len(b)
                need(consumed<=row['size_bytes'],'game_ledger_read_bound')
                h.update(b)
                if sha1 is not None:one.update(b)
                if keep:chunks.append(b)
            need(identity(os.fstat(fd))==identity(s)==identity(p.lstat()),'d24_read_race')
        finally:os.close(fd)
        need(h.hexdigest()==row['sha256'] and s.st_size==row['size_bytes'],'d24_input_changed')
        need(sha1 is None or one.hexdigest()==sha1,'d24_game_manifest')
        previous=self.rows.get(str(p))
        need(previous is None or previous==(row,identity(s)),'d24_input_changed_during_check')
        self.rows[str(p)]=(dict(row),identity(s))
        return b''.join(chunks) if keep else None

    def record(self,row):
        return decode_json(self.check(row,True),64*1024**2,max_nodes=1000000)

    def finish(self):
        need(not self.closed,'d24_ledger_closed')
        for row,before in list(self.rows.values()):
            need(identity(Path(row['path']).lstat())==before,'d24_input_changed_during_check')
            self.check(row)
        self.closed=True

def validate_game(ledger,m):
    snapshot=ledger.record(m['snapshot_ref'])
    need(str(snapshot['app_id'])=='3405340','d24_game_app')
    rows=[r for d in snapshot['platforms']['windows'] for r in d['files'] if not r['flags']&64]
    need(len(rows)==69 and len(m['game_files'])==69,'d24_game_count')
    declared={r['relative']:r for r in m['game_files']}
    need(len(declared)==69 and set(declared)=={r['path'] for r in rows},'d24_game_paths')
    game=Path(m['game_root']);need(game.resolve(strict=True)==game,'d24_game_root')
    for row in rows:
        rel=Path(row['path']);need(not rel.is_absolute() and '..' not in rel.parts,'d24_game_path')
        current=declared[row['path']]['ref']
        need(current['path']==str(game/rel) and current['size_bytes']==row['size'],'d24_game_binding')
        ledger.check(current,sha1=row['sha1'])

def validate_seed(m):
    seed=Path(m['seed_root'])
    need(seed.resolve(strict=True)==seed,'d24_seed_alias')
    need(prefix_inventory(seed/'run/prefix')==m['seed_inventory'],'d24_seed_changed')
    return seed

def game_copy(source,snapshot,destination):
    import subprocess
    value=read(snapshot)
    need(value['app_id']==3405340 or str(value['app_id'])=='3405340','game_app_identity')
    rows=[r for d in value['platforms']['windows'] for r in d['files'] if not r['flags'] & 64]
    need(len(rows)==69,'game_manifest_file_count')
    destination.mkdir(mode=0o700);facts=[]
    for row in rows:
        rel=Path(row['path'])
        need(not rel.is_absolute() and '..' not in rel.parts,'game_manifest_path')
        path=source/rel
        need(path.resolve().is_relative_to(source) and not path.is_symlink(),'game_source_alias')
        raw=path.read_bytes()
        need(len(raw)==row['size'] and hashlib.sha1(raw).hexdigest()==row['sha1'],'game_manifest_changed')
        target=destination/rel;target.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run(['/bin/cp','-c',str(path),str(target)],check=True,timeout=30)
        need(target.read_bytes()==raw,'game_clone_changed');facts.append(fact(path))
    return facts

def coordination_read(path):
    # Coordinator timestamps may be fractional; executable/input schemas remain strict.
    raw=Path(path).read_bytes();need(len(raw)<=4*1024**2,'menu_coordination_bound')
    def pairs(items):
        result={}
        for key,value in items:
            need(key not in result,'menu_coordination_duplicate');result[key]=value
        return result
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:need(False,'menu_coordination_number'))
