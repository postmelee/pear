# SPDX-License-Identifier: MIT
"""Independently require all finite v2 refusal, sharing and rollback controls."""
import re
from tools.dxmt.translated_inputs import need
CASES=[('getter_present',0),('version',2),('size',3),('features',4),('null_output',1),
       ('valid_table',0),('invalid_window',5),('null_device',7),('wrong_context',11),
       ('allocation_rollback',8),('allocation_no_client',6),('registration_rollback',8),
       ('registration_no_client',6),('create_missing',0),('share_owned',0),
       ('release_first',0),('remaining_live',0),('release_last',0),('recreate_missing',0),('detached_stale',10),('detached_release',0),('final_no_client',6),
       ('foreign_surface',11)]

def controls(stderr):
    records=[]
    for line in stderr.splitlines():
        if not line.startswith(b'PEAR_SURFACE_CONTROL'):continue
        m=re.fullmatch(rb'PEAR_SURFACE_CONTROL name=(\w+) status=(\d+) expected=(\d+) facts=(\d+)',line)
        need(m is not None,'surface_control_malformed')
        name=m[1].decode();status,expected,facts=map(int,m.groups()[1:]);records.append((name,status,expected,facts))
    need([r[0] for r in records]==[r[0] for r in CASES],'surface_control_set')
    need(all((status,expected,facts)==(want,want,1) for (_,status,expected,facts),(_,want) in zip(records,CASES)),
         'surface_control_failed')
    return dict(passed=True,case_count=len(records),cases=[dict(name=n,status=s) for n,s,e,f in records])
