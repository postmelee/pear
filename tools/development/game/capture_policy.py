# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: MIT
"""Owned Megabonk window eligibility, including its observed fullscreen layer."""
import math

def eligible(row,pid):
    if type(pid) is not int or pid<=0 or row.get('kCGWindowOwnerPID')!=pid:
        return False
    ident=row.get('kCGWindowNumber');layer=row.get('kCGWindowLayer')
    if type(ident) is not int or ident<=0 or type(layer) is not int or layer not in (0,26):
        return False
    if row.get('kCGWindowIsOnscreen') is not True:return False
    bounds=row.get('kCGWindowBounds',{})
    if not isinstance(bounds,dict):return False
    for key in ('Width','Height'):
        value=bounds.get(key)
        if type(value) not in (int,float) or not math.isfinite(value) or value<100:return False
    return True
