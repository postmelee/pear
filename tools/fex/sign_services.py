#!/usr/bin/env python3
"""Sign the exact ordinary-native FEX service fixture; no engine or JIT runs.

Reuse: Pear's Wine Mach-O signing-origin reader and Host Probe's pure profile
validator. Task4 signing entrypoints/loader identities are not reused.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
from pathlib import Path
import plistlib
import re
import shutil
import struct
import sys
import time
if __package__:
    from .common import REPO, Error, need, load_json, record, sha256, read_relative, decode_json, relative, operation_output, bounded_command, write_json
else:
    from common import REPO, Error, need, load_json, record, sha256, read_relative, decode_json, relative, operation_output, bounded_command, write_json

BUNDLE_ID = 'io.github.postmelee.pear.host-probe'
BUNDLE = 'PearFEXServices.app'
MAIN = BUNDLE+'/Contents/MacOS/pear-fex-services'
LIBRARIES = ('libarm64ecfex.so', 'libwow64fex.so')
APP_ID, TEAM_ID = 'com.apple.application-identifier', 'com.apple.developer.team-identifier'
ENV = {'PATH':'/usr/bin:/bin:/usr/sbin:/sbin','LC_ALL':'C'}


def profile_reader():
    spec=importlib.util.spec_from_file_location('_pear_fex_service_profile',REPO/'host/probe/provisioned_probe.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def producers():
    names=['tools/fex/sign_services.py','tools/fex/common.py','tools/fex/build.py',
           'host/probe/provisioned_probe.py','host/probe/hardened_baseline.py','tools/wine/common.py']
    return {name:sha256(REPO/name) for name in names}


def native(argv,root,ident,commands):
    need(argv and argv[0] in ('/usr/bin/security','/usr/bin/codesign','/usr/sbin/system_profiler'), 'service_signing_command')
    log=root/'logs'/ident;log.mkdir(parents=True)
    command=['/usr/bin/arch','-arm64',*argv];started=time.monotonic()
    row={'argv':command,'returncode':None,'elapsed_ms':0,'status':'unperformed',
         'id':ident,'environment':dict(ENV),'logs':{}}
    try:
        result=bounded_command(command,cwd=root,output_dir=log,timeout=60,max_output=1024*1024,env=ENV)
        row.update({k:result[k] for k in ('returncode','elapsed_ms','status')})
    except (Error,OSError) as error:
        row.update(elapsed_ms=int((time.monotonic()-started)*1000),status='failed',
                   error=getattr(error,'code',type(error).__name__))
        raise
    finally:
        for stream in ('stdout','stderr'):
            path=log/(stream+'.bin')
            if path.is_file():
                row['logs'][stream]={'path':path.relative_to(root).as_posix(),
                                    'sha256':sha256(path),'size_bytes':path.stat().st_size}
        commands.append(row)
    need(result['returncode']==0,'service_signing_command_failed:'+ident)
    return result['stdout'],result['stderr']


def authorize(profile_path,root,commands):
    profile_path=Path(profile_path).absolute()
    need(profile_path.is_file() and not profile_path.is_symlink() and '..' not in profile_path.parts,'service_profile_path')
    raw=read_relative(profile_path.parent,profile_path.name,1024*1024);digest=hashlib.sha256(raw).hexdigest()
    need(sha256(profile_path)==digest,'service_profile_changed')
    captured=root/'captured-profile.provisionprofile'
    with captured.open('xb') as stream:stream.write(raw)
    captured.chmod(0o600)
    decoded,_=native(['/usr/bin/security','cms','-D','-i',str(captured)],root,'profile.decode',commands)
    need(sha256(captured)==digest and sha256(profile_path)==digest,'service_profile_changed')
    identities,_=native(['/usr/bin/security','find-identity','-v','-p','codesigning'],root,'profile.identities',commands)
    hardware,_=native(['/usr/sbin/system_profiler','-json','SPHardwareDataType'],root,'profile.device',commands)
    info=decode_json(hardware)['SPHardwareDataType']
    need(isinstance(info,list) and len(info)==1 and isinstance(info[0],dict),'service_profile_device')
    devices=[v for k,v in info[0].items() if 'provision' in k.casefold()]
    need(len(devices)==1 and isinstance(devices[0],str),'service_profile_device')
    reader=profile_reader()
    try:
        authorization=reader.validate_profile(plistlib.loads(decoded),identities.decode(),devices[0],BUNDLE_ID)
    except reader.ControlError as error:
        raise Error(error.code) from None
    need(sha256(profile_path)==digest,'service_profile_changed')
    # The genuine profile is rechecked, but these tests request no restricted
    # entitlement, JIT exception or library-validation exception.
    authorization['claims']={key:authorization['claims'][key] for key in (APP_ID,TEAM_ID)}
    authorization.update(profile_sha256=digest,profile_bytes=raw)
    return authorization


def signature_facts(metadata,entitlements,claims,team):
    flags=re.findall(r'^CodeDirectory\b[^\r\n]*?\bflags=0x([0-9a-fA-F]+)(?:\(|\s|$)',metadata,re.M)
    need(len(flags)==1 and int(flags[0],16)&0x10000 and not int(flags[0],16)&2,'service_signature_hardened')
    need(re.search(r'^Authority=Apple Development: [^\r\n]+$',metadata,re.M) is not None,'service_signature_category')
    need(re.findall(r'^TeamIdentifier=([^\r\n]+)$',metadata,re.M)==[team],'service_signature_team')
    actual=plistlib.loads(entitlements) if entitlements.strip() else {}
    need(isinstance(actual,dict) and actual==claims and all(type(actual[key]) is type(value) for key,value in claims.items()),'service_signature_claims')
    need(set(claims)<=set((APP_ID,TEAM_ID)),'service_restricted_claim')
    return {'hardened_runtime':True,'ad_hoc':False,'category':'apple_development','same_team':True,
            'claim_keys':sorted(claims),'strict_verification':True,'restricted_operations':False}


def inspect_signature(path,claims,team,root,ident,commands):
    native(['/usr/bin/codesign','--verify','--strict',str(path)],root,ident+'.verify',commands)
    _,metadata=native(['/usr/bin/codesign','--display','--verbose=4',str(path)],root,ident+'.metadata',commands)
    entitlements,_=native(['/usr/bin/codesign','--display','--entitlements',':-',str(path)],root,ident+'.claims',commands)
    return signature_facts(metadata.decode(),entitlements,claims,team)



def signing_recipe(root,identity,profile_path):
    sources={'fixtures/pear-fex-services':MAIN,**{'install/'+name:BUNDLE+'/Contents/Resources/native/'+name for name in LIBRARIES}}
    recipe=[('profile.decode',['/usr/bin/security','cms','-D','-i',str(root/'captured-profile.provisionprofile')]),
            ('profile.identities',['/usr/bin/security','find-identity','-v','-p','codesigning']),
            ('profile.device',['/usr/sbin/system_profiler','-json','SPHardwareDataType'])]
    for _,dst in sources.items():
        path=root/dst;argv=['/usr/bin/codesign','--force','--sign',identity,'--options','runtime']
        if dst==MAIN:argv+=['--entitlements',str(root/'claims.plist')]
        recipe.append(('sign.'+path.name,[*argv,str(path)]))
    recipe.append(('sign.bundle',['/usr/bin/codesign','--force','--sign',identity,'--options','runtime','--entitlements',str(root/'claims.plist'),str(root/BUNDLE)]))
    for _,dst in sources.items():
        path=root/dst;ident='signature.'+path.name
        recipe.extend([(ident+'.verify',['/usr/bin/codesign','--verify','--strict',str(path)]),
                       (ident+'.metadata',['/usr/bin/codesign','--display','--verbose=4',str(path)]),
                       (ident+'.claims',['/usr/bin/codesign','--display','--entitlements',':-',str(path)])])
    recipe.append(('signature.bundle',['/usr/bin/codesign','--verify','--strict',str(root/BUNDLE)]))
    return [(ident,['/usr/bin/arch','-arm64',*argv]) for ident,argv in recipe]


def verify_command_receipts(root,rows,recipe):
    need(isinstance(rows,list) and len(rows)==len(recipe),'service_signing_command_set')
    for row,(ident,argv) in zip(rows,recipe):
        need(isinstance(row,dict) and set(row)=={'id','argv','returncode','elapsed_ms','status','environment','logs'},'service_signing_command_fields')
        need(row['id']==ident and row['argv']==argv and type(row['returncode']) is int and row['returncode']==0
             and row['status']=='completed' and row['environment']==ENV and type(row['elapsed_ms']) is int and row['elapsed_ms']>=0,'service_signing_command_recipe')
        need(isinstance(row['logs'],dict) and set(row['logs'])=={'stdout','stderr'},'service_signing_logs')
        for stream,ref in row['logs'].items():
            need(isinstance(ref,dict) and set(ref)=={'path','sha256','size_bytes'}
                 and ref['path']=='logs/'+ident+'/'+stream+'.bin','service_signing_log_path')
            data=read_relative(root,ref['path'],1024*1024)
            need(type(ref['size_bytes']) is int and len(data)==ref['size_bytes'] and sha256(root/ref['path'])==ref['sha256'],'service_signing_log_changed')


def code_parts(path):
    """Preserve executable/data bytes; allow only documented signing fields."""
    path=Path(path);data=read_relative(path.parent,path.name,512*1024*1024)
    need(len(data)>=32,'service_code_truncated');header=struct.unpack_from('<8I',data)
    need(header[0]==0xfeedfacf and header[1]==0x100000c and header[3] in (2,6,8),'service_code_not_arm64')
    count,end=header[4],32+header[5]
    need(count<=65536 and end<=len(data),'service_code_commands')
    commands,signature,linkedit=[],None,None;at=32
    for _ in range(count):
        need(at+8<=end,'service_code_commands');command,size=struct.unpack_from('<II',data,at)
        need(size>=8 and size%4==0 and at+size<=end,'service_code_commands');chunk=bytearray(data[at:at+size])
        if command==0x1d:
            need(signature is None and size==16,'service_signature_command')
            offset,length=struct.unpack_from('<II',data,at+8)
            need(offset>=end and length>0 and offset+length==len(data),'service_signature_range')
            signature=(offset,length)
        else:
            if command==0x19 and chunk[8:24].rstrip(b'\0')==b'__LINKEDIT':
                need(size>=72 and linkedit is None,'service_code_linkedit')
                vmaddr,vmsize,fileoff,filesize=struct.unpack_from('<4Q',chunk,24)
                need(fileoff+filesize<=len(data),'service_code_linkedit')
                linkedit=(vmsize,fileoff,filesize);struct.pack_into('<Q',chunk,32,0);struct.pack_into('<Q',chunk,48,0)
            commands.append(bytes(chunk))
        at+=size
    need(at==end,'service_code_commands')
    return {'data':data,'header':header[:4]+header[6:],'commands':commands,'command_end':end,'signature':signature,'linkedit':linkedit}


def verify_origin(unsigned,signed):
    before,after=code_parts(unsigned),code_parts(signed)
    need(before['header']==after['header'] and before['commands']==after['commands'],'service_signed_origin')
    start=max(before['command_end'],after['command_end'])
    for part in (before,after):
        need(not any(part['data'][part['command_end']:start]),'service_signing_padding')
    old_end=before['signature'][0] if before['signature'] else len(before['data'])
    new_end=after['signature'][0] if after['signature'] else len(after['data'])
    old,new=before['data'][start:old_end],after['data'][start:new_end]
    need(new.startswith(old) and 0<=len(new)-len(old)<16 and not any(new[len(old):])
         and (before['signature'] is None or old_end==new_end),'service_signed_origin')
    if before['linkedit'] or after['linkedit']:
        need(before['linkedit'] is not None and after['linkedit'] is not None,'service_signed_linkedit')
        old_vm,old_off,old_size=before['linkedit'];new_vm,new_off,new_size=after['linkedit']
        need(old_off==new_off and new_size-old_size==len(after['data'])-len(before['data'])
             and new_vm in {old_vm,new_size,(new_size+4095)&~4095,(new_size+16383)&~16383} and new_vm>=new_size,'service_signed_linkedit')


def verify_build(root):
    if __package__:
        from .build import verify_build as implementation
    else:
        from build import verify_build as implementation
    return implementation(root)


def inventory(root):
    rows=[]
    for path in sorted((root/BUNDLE).rglob('*')):
        need(not path.is_symlink(),'service_bundle_symlink')
        if path.is_file():
            rows.append({'path':path.relative_to(root).as_posix(),'sha256':sha256(path),'size_bytes':path.stat().st_size,'mode':path.stat().st_mode&0o777})
    need(len(rows)<=32,'service_bundle_size')
    return rows


def prepare(build_root,profile_path,output):
    build_root=operation_output(build_root,require_empty=False,create=False)
    built=verify_build(build_root);need(built.get('native_built') is True,'service_native_not_built')
    root=operation_output(output)
    value={'schema_version':1,'record_kind':'fex_service_authorization','scope':'fex_component',
           'build_ref':{'path':str(build_root),'sha256':sha256(build_root/'build.json')},'profile_path':str(Path(profile_path).absolute()),'producers':producers(),
           'bundle_identifier':BUNDLE_ID,'bundle':BUNDLE,'executable':MAIN,'profile_sha256':None,'profile_checks':{},
           'restricted_operations':False,'restricted_claims_requested':False,'commands':[],'native_images':[],
           'bundle_inventory':[],'service_execution':False,'fex_initialization':False,'guest_execution':False}
    try:
        auth=authorize(profile_path,root,value['commands'])
        contents=root/BUNDLE/'Contents';(contents/'MacOS').mkdir(parents=True);(contents/'Resources/native').mkdir(parents=True)
        (contents/'embedded.provisionprofile').write_bytes(auth['profile_bytes'])
        (contents/'Info.plist').write_bytes(plistlib.dumps({'CFBundleIdentifier':BUNDLE_ID,'CFBundleExecutable':'pear-fex-services','CFBundleName':'Pear FEX Service Probe','CFBundlePackageType':'APPL','CFBundleVersion':'1'}))
        claims_path=root/'claims.plist';claims_path.write_bytes(plistlib.dumps(auth['claims']))
        sources={'fixtures/pear-fex-services':MAIN,**{'install/'+name:BUNDLE+'/Contents/Resources/native/'+name for name in LIBRARIES}}
        for src,dst in sources.items():
            source=build_root/src;target=root/dst;code_parts(source);shutil.copy2(source,target)
            arguments=['/usr/bin/codesign','--force','--sign',auth['identity'],'--options','runtime']
            if dst==MAIN:arguments+=['--entitlements',str(claims_path)]
            native([*arguments,str(target)],root,'sign.'+target.name,value['commands'])
            verify_origin(source,target)
        native(['/usr/bin/codesign','--force','--sign',auth['identity'],'--options','runtime','--entitlements',str(claims_path),str(root/BUNDLE)],root,'sign.bundle',value['commands'])
        for src,dst in sources.items():
            target=root/dst;verify_origin(build_root/src,target)
            fact=inspect_signature(target,auth['claims'] if dst==MAIN else {},auth['claims'][TEAM_ID],root,'signature.'+target.name,value['commands'])
            value['native_images'].append({'source':src,'path':dst,'unsigned_sha256':sha256(build_root/src),'sha256':sha256(target),'signature':fact})
        native(['/usr/bin/codesign','--verify','--strict',str(root/BUNDLE)],root,'signature.bundle',value['commands'])
        value.update(profile_sha256=auth['profile_sha256'],profile_checks=auth['checks'],bundle_inventory=inventory(root))
        verify_command_receipts(root,value['commands'],signing_recipe(root,auth['identity'],Path(value['profile_path'])))
        write_json(root/'authorization.json',value)
        validate_authorization_record(root)
        return value
    except (Error,OSError,ValueError,KeyError) as error:
        write_json(root/'failure.json',{'schema_version':1,'record_kind':'fex_service_signing_failure','scope':'fex_component','commands':value['commands'],'error':error.code if isinstance(error,Error) else 'service_signing_failed','restricted_operations':False})
        raise


def cms_plist_content(raw):
    """Extract a bounded DER CMS data eContent; no signature trust is asserted.

    Only the envelope used by the provided development profile is supported.
    macOS remains the live CMS decoder and code-signature verifier. Structural
    extraction independently binds that decoder's complete plist to input bytes.
    """
    need(isinstance(raw,bytes) and 0<len(raw)<=1024*1024,'service_cms_size')
    def tlv(data,offset):
        need(offset+2<=len(data),'service_cms_truncated')
        tag=data[offset];first=data[offset+1];start=offset+2
        need(tag&31!=31,'service_cms_tag')
        if first&128:
            width=first&127
            need(1<=width<=4 and start+width<=len(data) and data[start]!=0,'service_cms_length')
            length=int.from_bytes(data[start:start+width],'big');start+=width
            need(length>=128 and length.bit_length()>(width-1)*8,'service_cms_length')
        else:length=first
        end=start+length;need(end<=len(data),'service_cms_truncated')
        return tag,data[start:end],end
    def children(data):
        result=[];offset=0
        while offset<len(data):
            need(len(result)<16,'service_cms_node_limit')
            tag,content,offset=tlv(data,offset);result.append((tag,content))
        return result
    tag,content,end=tlv(raw,0)
    need(tag==0x30 and end==len(raw),'service_cms_envelope')
    outer=children(content)
    need(len(outer)==2 and outer[0]==(6,bytes.fromhex('2a864886f70d010702')) and outer[1][0]==0xa0,'service_cms_signed_data')
    explicit=children(outer[1][1]);need(len(explicit)==1 and explicit[0][0]==0x30,'service_cms_signed_data')
    signed=children(explicit[0][1])
    need(4<=len(signed)<=6 and [tag for tag,_ in signed[:3]]==[2,0x31,0x30] and signed[-1][0]==0x31
         and [tag for tag,_ in signed[3:-1]] in [[],[0xa0],[0xa1],[0xa0,0xa1]],'service_cms_signed_fields')
    encapsulated=children(signed[2][1])
    need(len(encapsulated)==2 and encapsulated[0]==(6,bytes.fromhex('2a864886f70d010701')) and encapsulated[1][0]==0xa0,'service_cms_data_content')
    payload=children(encapsulated[1][1]);need(len(payload)==1 and payload[0][0]==4,'service_cms_data_content')
    need(payload[0][1],'service_cms_empty_content')
    return payload[0][1]


def profile_from_receipts(root):
    """Replay private captured authorization inputs without another native call."""
    decoded=read_relative(root,'logs/profile.decode/stdout.bin',1024*1024)
    captured=read_relative(root,'captured-profile.provisionprofile',1024*1024)
    profile=plistlib.loads(decoded)
    original=plistlib.loads(cms_plist_content(captured))
    need(plistlib.dumps(profile,fmt=plistlib.FMT_BINARY,sort_keys=True)==plistlib.dumps(original,fmt=plistlib.FMT_BINARY,sort_keys=True),'service_profile_decoded_content_changed')
    identities=read_relative(root,'logs/profile.identities/stdout.bin',1024*1024)
    hardware=decode_json(read_relative(root,'logs/profile.device/stdout.bin',1024*1024))
    info=hardware.get('SPHardwareDataType')
    need(isinstance(info,list) and len(info)==1 and isinstance(info[0],dict),'service_profile_device')
    devices=[v for k,v in info[0].items() if 'provision' in k.casefold()]
    need(len(devices)==1 and isinstance(devices[0],str),'service_profile_device')
    reader=profile_reader()
    try:
        auth=reader.validate_profile(profile,identities.decode(),devices[0],BUNDLE_ID)
    except reader.ControlError as error:
        raise Error(error.code) from None
    auth['claims']={key:auth['claims'][key] for key in (APP_ID,TEAM_ID)}
    return auth


def captured_signature(root,ident,claims,team):
    metadata=read_relative(root,'logs/'+ident+'.metadata/stderr.bin',1024*1024).decode()
    entitlements=read_relative(root,'logs/'+ident+'.claims/stdout.bin',1024*1024)
    return signature_facts(metadata,entitlements,claims,team)


def validate_authorization_record(root):
    """Pure replay of original signing evidence, code bytes and private grant."""
    root=operation_output(root,require_empty=False,create=False)
    need(not (root/'failure.json').exists(),'failed_service_authorization')
    value=record(load_json(root/'authorization.json'),'fex_service_authorization')
    need(set(value)=={'schema_version','record_kind','scope','build_ref','profile_path','producers','bundle_identifier','bundle','executable','profile_sha256','profile_checks','restricted_operations','restricted_claims_requested','commands','native_images','bundle_inventory','service_execution','fex_initialization','guest_execution'},'service_authorization_fields')
    need(value['scope']=='fex_component' and value['bundle_identifier']==BUNDLE_ID and value['bundle']==BUNDLE and value['executable']==MAIN,'service_bundle_identity')
    need(all(value[key] is False for key in ('restricted_operations','restricted_claims_requested','service_execution','fex_initialization','guest_execution')),'service_authorization_scope')
    need(value['producers']==producers() and value['bundle_inventory']==inventory(root),'service_authorization_changed')
    need(isinstance(value['build_ref'],dict) and set(value['build_ref'])=={'path','sha256'},'service_build_reference')
    build=operation_output(value['build_ref']['path'],require_empty=False,create=False)
    need(sha256(build/'build.json')==value['build_ref']['sha256'],'service_build_changed');verify_build(build)
    auth=profile_from_receipts(root)
    need(auth['checks']==value['profile_checks'],'service_profile_checks_changed')
    profile=Path(value['profile_path'])
    need(profile.is_absolute() and '..' not in profile.parts and profile.is_file() and not profile.is_symlink(),'service_profile_path')
    original=read_relative(profile.parent,profile.name,1024*1024)
    embedded=read_relative(root,BUNDLE+'/Contents/embedded.provisionprofile',1024*1024)
    captured=read_relative(root,'captured-profile.provisionprofile',1024*1024)
    need(original==embedded==captured and hashlib.sha256(captured).hexdigest()==value['profile_sha256'],'service_original_profile_changed')
    need(plistlib.loads(read_relative(root,'claims.plist',1024*1024))==auth['claims'],'service_claims_input_changed')
    expected_info={'CFBundleIdentifier':BUNDLE_ID,'CFBundleExecutable':'pear-fex-services','CFBundleName':'Pear FEX Service Probe','CFBundlePackageType':'APPL','CFBundleVersion':'1'}
    need(plistlib.loads(read_relative(root,BUNDLE+'/Contents/Info.plist',1024*1024))==expected_info,'service_bundle_info_changed')
    verify_command_receipts(root,value['commands'],signing_recipe(root,auth['identity'],profile))
    expected_sources={'fixtures/pear-fex-services':MAIN,**{'install/'+name:BUNDLE+'/Contents/Resources/native/'+name for name in LIBRARIES}}
    need(isinstance(value['native_images'],list) and len(value['native_images'])==3
         and {r['source']:r['path'] for r in value['native_images']}==expected_sources,'service_signed_images')
    for row in value['native_images']:
        need(set(row)=={'source','path','unsigned_sha256','sha256','signature'},'service_signed_image_fields')
        source=build.joinpath(*relative(row['source']));path=root.joinpath(*relative(row['path']))
        need(sha256(source)==row['unsigned_sha256'] and sha256(path)==row['sha256'],'service_image_changed');verify_origin(source,path)
        fact=captured_signature(root,'signature.'+path.name,auth['claims'] if row['path']==MAIN else {},auth['claims'][TEAM_ID])
        need(row['signature']==fact,'service_signature_record_changed')
    return value


def preflight_recipe(output,authorization):
    recipe=[('profile.decode',['/usr/bin/security','cms','-D','-i',str(output/'captured-profile.provisionprofile')]),
            ('profile.identities',['/usr/bin/security','find-identity','-v','-p','codesigning']),
            ('profile.device',['/usr/sbin/system_profiler','-json','SPHardwareDataType'])]
    for relative_path in [MAIN,*[BUNDLE+'/Contents/Resources/native/'+name for name in LIBRARIES]]:
        path=authorization/relative_path;ident='current.'+path.name
        recipe.extend([(ident+'.verify',['/usr/bin/codesign','--verify','--strict',str(path)]),
                       (ident+'.metadata',['/usr/bin/codesign','--display','--verbose=4',str(path)]),
                       (ident+'.claims',['/usr/bin/codesign','--display','--entitlements',':-',str(path)])])
    recipe.append(('current.bundle',['/usr/bin/codesign','--verify','--strict',str(authorization/BUNDLE)]))
    return [(ident,['/usr/bin/arch','-arm64',*argv]) for ident,argv in recipe]


def validate_preflight_record(output,authorization):
    """Pure replay of the live checks captured immediately before service runs."""
    output=operation_output(output,require_empty=False,create=False)
    need(not (output/'failure.json').exists(),'service_preflight_failed_record')
    authorization=operation_output(authorization,require_empty=False,create=False)
    value=validate_authorization_record(authorization)
    preflight=record(load_json(output/'preflight.json'),'fex_service_preflight')
    need(set(preflight)=={'schema_version','record_kind','scope','authorization_sha256','commands','restricted_operations'},'service_preflight_fields')
    need(preflight['scope']=='fex_component' and preflight['restricted_operations'] is False
         and preflight['authorization_sha256']==sha256(authorization/'authorization.json'),'service_preflight_binding')
    verify_command_receipts(output,preflight['commands'],preflight_recipe(output,authorization))
    captured=read_relative(output,'captured-profile.provisionprofile',1024*1024)
    need(captured==read_relative(authorization,BUNDLE+'/Contents/embedded.provisionprofile',1024*1024),'service_preflight_capture_changed')
    auth=profile_from_receipts(output)
    need(auth['checks']==value['profile_checks'] and auth['claims']==profile_from_receipts(authorization)['claims'],'service_preflight_profile_changed')
    for row in value['native_images']:
        fact=captured_signature(output,'current.'+Path(row['path']).name,auth['claims'] if row['path']==MAIN else {},auth['claims'][TEAM_ID])
        need(fact==row['signature'],'service_preflight_signature_changed')
    return preflight


def validate_authorization(root):
    root=operation_output(root,require_empty=False,create=False)
    value=validate_authorization_record(root)
    # New private preflight output prevents overwriting earlier signature probes.
    output=operation_output('.build/task5/service-preflight-'+sha256(root/'authorization.json')[:12]+'-'+str(__import__('time').time_ns()))
    commands=[]
    try:
        auth=authorize(root/BUNDLE/'Contents/embedded.provisionprofile',output,commands)
        need(auth['profile_sha256']==value['profile_sha256'] and auth['checks']==value['profile_checks'],'service_profile_changed')
        for row in value['native_images']:
            path=root.joinpath(*relative(row['path']))
            expected=inspect_signature(path,auth['claims'] if row['path']==MAIN else {},auth['claims'][TEAM_ID],output,'current.'+path.name,commands)
            need(row['signature']==expected,'service_signature_changed')
        native(['/usr/bin/codesign','--verify','--strict',str(root/BUNDLE)],output,'current.bundle',commands)
        write_json(output/'preflight.json',{'schema_version':1,'record_kind':'fex_service_preflight','scope':'fex_component','authorization_sha256':sha256(root/'authorization.json'),'commands':commands,'restricted_operations':False})
        validate_preflight_record(output,root)
    except (Error,OSError,ValueError,KeyError) as error:
        write_json(output/'failure.json',{'schema_version':1,'record_kind':'fex_service_preflight_failure',
                   'scope':'fex_component','authorization_sha256':sha256(root/'authorization.json'),
                   'commands':commands,'error':getattr(error,'code',type(error).__name__),
                   'restricted_operations':False})
        raise
    return value,output


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--build',required=True);parser.add_argument('--profile',required=True);parser.add_argument('--output',required=True);parser.add_argument('--require-empty',action='store_true',required=True)
    args=parser.parse_args()
    try:
        prepare(args.build,args.profile,args.output);print('PASS: exact ordinary-native service bundle development-signed; no service or FEX execution');return 0
    except (Error,OSError,ValueError,KeyError,ImportError) as error:
        print('FAIL: '+(error.code if isinstance(error,Error) else type(error).__name__),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
