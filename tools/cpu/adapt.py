# SPDX-License-Identifier: MIT
"""Declared input adaptations for hosting fixed-address ASM inside a Windows PE.

Upstream source bytes and all original defined outcomes remain unchanged in the
source manifest. This separate contract records the actual generated inputs.
"""
import copy
import json
from pathlib import Path

PATH=Path(__file__).resolve().parents[2]/'tests/cpu/adaptations.json'


def rules():
    return json.loads(PATH.read_text())


def effective_case(case):
    rule=rules()['cases'].get(case['id'])
    if rule is None:return case
    if case['sha256']!=rule['source_sha256']:raise ValueError('adaptation_source_changed')
    c=copy.deepcopy(case);old=rule['original_data_page'];new=rule['effective_data_page']
    if c['contract']['regions']!=[dict(address=old,size=4096)]:raise ValueError('adaptation_region_changed')
    c['contract']['regions'][0]['address']=new
    for item in c['contract']['initial_memory']:
        if not old<=item['address']<old+4096:raise ValueError('adaptation_initial_memory')
        item['address']+=new-old
    c['contract']['expectations'].append(rule['additional_expectation'])
    c['masks'].append(dict(bits='0xffffffffffffffff',reason='Preserve the original upper signed disp32 LEA boundary independently of data placement.'))
    return c


def adapt_body(case, body):
    if case['id'] not in rules()['cases']:return body
    effective_case(case)
    # Exact reviewed operands only; never rewrite an arbitrary instruction or
    # silently alter golden values. The extra LEA preserves the original edge.
    if body.count('0x7FFF_F000')!=1 or body.count('0x7FFF_FFF8')!=2 or body.count('hlt')!=1:
        raise ValueError('adaptation_operands_changed')
    return (body.replace('0x7FFF_F000','0x1000_F000').replace('0x7FFF_FFF8','0x1000_FFF8')
            .replace('hlt','lea r8, [abs 0x7FFF_FFF8]\nhlt'))
