"""Inspect unsigned payload bytes, modes and aliases; completion is a separate gate.
The coordinator independently replays builds, origins and native evidence.
No builder, Apple tool, profile, signer or native/guest execution is called here.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import stat
MAX_FILES=20000
MAX_FILE_BYTES=512*1024**2
MAX_TOTAL_BYTES=2*1024**3
MAX_LINK_DEPTH=32
class Error(ValueError):pass
def need(value,reason):
    if not value:raise Error(reason)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def encode(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode()
def relative(value):
    need(type(value)is str and value and len(value.encode())<=4096 and '\\'not in value
         and not value.startswith('/')and not any(ord(c)<32 or ord(c)==127 for c in value),'relative_path')
    parts=value.split('/');need(all(part not in ('','.','..')for part in parts),'relative_path');return parts
def mode(value):need(type(value)is int and 0<=value<=0o7777,'entry_mode')
def identity(info):
    return (info.st_dev,info.st_ino,info.st_mode,info.st_size,info.st_mtime_ns,info.st_ctime_ns,info.st_nlink)
def resolve_alias_target(mapped,cursor,target):
    # Preserve source filesystem meaning; lexical normpath alone can hide a
    # missing/file/alias component before '..'. No directory alias is selected.
    parts=target.split('/');need(all(part for part in parts),'link_component')
    stack=cursor.split('/')[:-1]
    for index,part in enumerate(parts):
        if part=='.':continue
        if part=='..':need(stack,'link_escape');stack.pop()
        else:stack.append(part)
        path='/'.join(stack)
        if not path and index<len(parts)-1:continue  # The owned root is an implicit directory.
        need(path in mapped,'link_missing_target')
        if index<len(parts)-1:need(mapped[path]['kind']=='directory','link_component')
    path='/'.join(stack);relative(path);return path
def validate_entries(entries):
    need(type(entries)is list and 0<len(entries)<=MAX_FILES,'entry_count');paths=[];total=0
    for row in entries:
        need(type(row)is dict,'entry_shape');relative(row.get('path'));kind=row.get('kind')
        need(kind in ('file','directory','symlink'),'entry_kind');mode(row.get('mode'));expected={'path','kind','mode'}
        if kind=='file':
            expected|={'size_bytes','sha256'};size=row.get('size_bytes')
            need(type(size)is int and 0<=size<=MAX_FILE_BYTES,'file_size');value=row.get('sha256')
            need(type(value)is str and len(value)==64 and all(c in '0123456789abcdef'for c in value),'file_digest');total+=size
        elif kind=='symlink':
            expected.add('target');target=row.get('target')
            need(type(target)is str and target and not target.startswith('/')and '\\'not in target
                 and len(target.encode())<=4096 and not any(ord(c)<32 or ord(c)==127 for c in target),'link_target')
        need(set(row)==expected,'entry_fields');paths.append(row['path'])
    need(total<=MAX_TOTAL_BYTES and paths==sorted(paths)and len(set(paths))==len(paths),'entry_order_or_bound')
    mapped={row['path']:row for row in entries}
    for path,row in mapped.items():
        parts=relative(path)
        for index in range(1,len(parts)):
            parent='/'.join(parts[:index]);need(parent in mapped and mapped[parent]['kind']=='directory','entry_parent')
        if row['kind']!='symlink':continue
        cursor=path;visited=set()
        for _ in range(MAX_LINK_DEPTH):
            need(cursor not in visited,'link_cycle');visited.add(cursor);alias=mapped[cursor]
            target=resolve_alias_target(mapped,cursor,alias['target'])
            relative(target);need(target in mapped,'link_missing_target')
            for index in range(1,len(relative(target))):
                parent='/'.join(relative(target)[:index]);need(mapped.get(parent,{}).get('kind')=='directory','link_parent_alias')
            selected=mapped[target]
            if selected['kind']=='symlink':cursor=target;continue
            need(selected['kind']=='file','link_directory_alias');break
        else:raise Error('link_depth')
    return entries

def scan_tree(root):
    """FD-rooted nonfollowing byte/mode walk; no executable is evaluated."""
    root=Path(root).absolute();need(root.resolve(strict=True)==root,'root_alias');rows=[];total=0
    fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    def visit(parent,prefix):
        nonlocal total
        for name in sorted(os.listdir(parent)):
            relative(name);path=prefix+name;need(len(rows)<MAX_FILES,'entry_count')
            observed=os.stat(name,dir_fd=parent,follow_symlinks=False);item={'path':path,'mode':stat.S_IMODE(observed.st_mode)}
            if stat.S_ISDIR(observed.st_mode):
                item['kind']='directory';rows.append(item)
                child=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent)
                try:
                    opened=os.fstat(child);need(identity(opened)==identity(observed),'directory_changed');visit(child,path+'/')
                    need(identity(os.fstat(child))==identity(opened)
                         and identity(os.stat(name,dir_fd=parent,follow_symlinks=False))==identity(opened),'directory_changed')
                finally:os.close(child)
            elif stat.S_ISLNK(observed.st_mode):
                item.update(kind='symlink',target=os.readlink(name,dir_fd=parent))
                need(identity(os.stat(name,dir_fd=parent,follow_symlinks=False))==identity(observed),'link_changed');rows.append(item)
            else:
                need(stat.S_ISREG(observed.st_mode)and observed.st_nlink==1,'file_kind_or_hardlink')
                need(observed.st_size<=MAX_FILE_BYTES,'file_size');total+=observed.st_size;need(total<=MAX_TOTAL_BYTES,'total_size')
                child=os.open(name,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=parent)
                try:
                    opened=os.fstat(child);need(stat.S_ISREG(opened.st_mode)and opened.st_nlink==1
                        and identity(opened)==identity(observed),'file_changed')
                    value=hashlib.sha256();size=0
                    while block:=os.read(child,1024*1024):
                        size+=len(block);need(size<=MAX_FILE_BYTES,'file_size');value.update(block)
                    after=os.fstat(child)
                    need((after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns,stat.S_IMODE(after.st_mode),after.st_nlink)==
                         (opened.st_dev,opened.st_ino,opened.st_size,opened.st_mtime_ns,opened.st_ctime_ns,stat.S_IMODE(opened.st_mode),1)
                         and size==opened.st_size and opened.st_size==observed.st_size
                         and stat.S_IMODE(opened.st_mode)==item['mode'],'file_changed')
                    current=os.stat(name,dir_fd=parent,follow_symlinks=False)
                    need(identity(current)==identity(opened),'file_replaced')
                    item.update(kind='file',size_bytes=size,sha256=value.hexdigest());rows.append(item)
                finally:os.close(child)
    try:
        initial=os.fstat(fd);visit(fd,'');need(identity(os.fstat(fd))==identity(initial),'root_changed')
    finally:os.close(fd)
    return validate_entries(sorted(rows,key=lambda row:row['path']))

def check_wine_manifest(entries,manifest):
    """Exact file/alias check; caller first admits actual old manifest bytes.
    Original kind/PE metadata is not relabeled. Directory modes are newly
    observed because the historical file manifest does not contain them.
    """
    validate_entries(entries)
    need(type(manifest)is dict and set(manifest)=={'schema_version','record_kind','files','symlinks'}
         and type(manifest['schema_version'])is int and manifest['schema_version']==1
         and manifest['record_kind']=='wine_build_inventory','wine_manifest_shape')
    files=manifest['files'];links=manifest['symlinks'];need(type(files)is list and type(links)is list,'wine_manifest_shape')
    actual={row['path']:{key:row[key]for key in ('path','mode','size_bytes','sha256')}for row in entries if row['kind']=='file'};expected={}
    for row in files:
        need(type(row)is dict and all(key in row for key in ('path','mode','size_bytes','sha256')),'wine_manifest_file')
        relative(row['path']);need(row['path']not in expected,'wine_manifest_duplicate')
        expected[row['path']]={key:row[key]for key in ('path','mode','size_bytes','sha256')}
    need(encode(actual)==encode(expected),'wine_manifest_bytes')
    actual_links=[{'path':row['path'],'target':row['target']}for row in entries if row['kind']=='symlink']
    need(actual_links==links,'wine_manifest_aliases');return entries

def scan_selected(root,paths):
    """Read a closed selected file set and its real parents, never glob objects."""
    root=Path(root);need(root.is_absolute()and root.resolve(strict=True)==root,'root_alias')
    need(type(paths)is list and paths and len(paths)==len(set(paths))<=MAX_FILES,'selected_set')
    for path in paths:relative(path)
    descriptors={};rows={};total=0
    flags=os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW
    rootfd=os.open(root,flags);descriptors['']=(rootfd,os.fstat(rootfd),None,None)
    def directory(path):
        if path in descriptors:return descriptors[path][0]
        parts=relative(path);parent='/'.join(parts[:-1]);parentfd=directory(parent);leaf=parts[-1]
        before=os.stat(leaf,dir_fd=parentfd,follow_symlinks=False)
        need(stat.S_ISDIR(before.st_mode),'selected_parent')
        child=os.open(leaf,flags,dir_fd=parentfd);opened=os.fstat(child)
        if identity(opened)!=identity(before):os.close(child);raise Error('directory_changed')
        descriptors[path]=(child,opened,parentfd,leaf)
        rows[path]={'path':path,'kind':'directory','mode':stat.S_IMODE(opened.st_mode)}
        return child
    try:
        for path in sorted(paths):
            parts=relative(path);parentfd=directory('/'.join(parts[:-1]));leaf=parts[-1]
            before=os.stat(leaf,dir_fd=parentfd,follow_symlinks=False)
            need(stat.S_ISREG(before.st_mode)and before.st_nlink==1,'file_kind_or_hardlink')
            need(before.st_size<=MAX_FILE_BYTES,'file_size');total+=before.st_size;need(total<=MAX_TOTAL_BYTES,'total_size')
            fd=os.open(leaf,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=parentfd)
            try:
                opened=os.fstat(fd);need(identity(opened)==identity(before),'file_changed')
                value=hashlib.sha256();size=0
                while block:=os.read(fd,1024*1024):
                    size+=len(block);need(size<=MAX_FILE_BYTES,'file_size');value.update(block)
                need(identity(os.fstat(fd))==identity(opened)and size==opened.st_size
                     and identity(os.stat(leaf,dir_fd=parentfd,follow_symlinks=False))==identity(opened),'file_changed')
                rows[path]={'path':path,'kind':'file','mode':stat.S_IMODE(opened.st_mode),
                            'size_bytes':size,'sha256':value.hexdigest()}
            finally:os.close(fd)
        for fd,before,parentfd,leaf in descriptors.values():
            need(identity(os.fstat(fd))==identity(before),'directory_changed')
            if parentfd is not None:need(identity(os.stat(leaf,dir_fd=parentfd,follow_symlinks=False))==identity(before),'directory_changed')
        need(root.resolve(strict=True)==root and identity(root.lstat())==identity(descriptors[''][1]),'root_changed')
        return validate_entries(sorted(rows.values(),key=lambda row:row['path']))
    finally:
        for fd,_,_,_ in descriptors.values():os.close(fd)

REPLACEMENTS={'lib/wine/aarch64-unix/winemac.so':'replace','lib/wine/aarch64-windows/winemac.drv':'replace',
 'lib/wine/aarch64-unix/winemetal.so':'add','libexec/pear-dxmt/pairing-arm64.exe':'add'}
def overlay_wine(entries,replacements):
    """Closed conceptual unsigned payload; no copying/signing/execution."""
    validate_entries(entries);need(type(replacements)is list and len(replacements)==4,'overlay_count')
    mapping={row.get('path'):row for row in replacements};need(set(mapping)==set(REPLACEMENTS),'overlay_set')
    out={row['path']:dict(row)for row in entries}
    need('libexec'in out and out['libexec']['kind']=='directory'and 'libexec/pear-dxmt'not in out,'overlay_directory')
    out['libexec/pear-dxmt']={'path':'libexec/pear-dxmt','kind':'directory','mode':0o755}
    for path,action in REPLACEMENTS.items():
        row=mapping[path];need(row.get('kind')=='file','overlay_file')
        need((path in out)==(action=='replace')and(path not in out or out[path]['kind']=='file'),'overlay_origin');out[path]=dict(row)
    return validate_entries(sorted(out.values(),key=lambda row:row['path']))
def namespace(name,entries):
    relative(name);validate_entries(entries)
    return [{'path':name,'kind':'directory','mode':0o755}]+[{**row,'path':name+'/'+row['path']}for row in entries]
def compare_entries(reference,candidate):
    """Every raw name/byte/mode/alias difference refuses; normalization NONE."""
    validate_entries(reference);validate_entries(candidate)
    left={row['path']:row for row in reference};right={row['path']:row for row in candidate};changes=[]
    for path in sorted(set(left)|set(right)):
        before=left.get(path);after=right.get(path)
        if encode(before)==encode(after):continue
        fields=sorted(set(before or {})|set(after or {}))
        changed=[key for key in fields if encode((before or {}).get(key))!=encode((after or {}).get(key))]
        changes.append({'path':path,'changed_fields':changed,'reference':before,'candidate':after})
    return {'schema_version':1,'record_kind':'dxmt_unsigned_comparison','scope':'complete_unsigned_component_payload',
      'normalization_policy':'none','reference_inventory_sha256':digest(encode(reference)),
      'candidate_inventory_sha256':digest(encode(candidate)),'raw_equal':not changes,'differences':changes,
      'reconstruction_complete':False,'native_evidence_binding':'unperformed','native_execution_performed':False,
      'hybrid_execution_performed':False,'translated_guest_execution_performed':False,'game_qualified':False,
      'runtime_eligible':False,'distribution_qualified':False}
