# SPDX-License-Identifier: MIT
"""Admit #7's corrected loader and the exact source interface used by #8."""
from pathlib import Path
from tools.dxmt.translated_inputs import REPO,pin,read,digest,fact
from tools.dxmt.deterministic_native import adapter
from tools.wine.common import need

RECEIPT='ac845ea04a80096be20e2057efa38339d5dd3576a3b78d23d39c949fa29f95e6'

def admit(inputs,build):
    repo=Path(inputs['graphics_repo']);root=repo/'.build/task7/stage5-loader-final3'
    pin(root/'loader.json',RECEIPT)
    with adapter(repo,repo/'tools/dxmt',loader_reservation=root) as reused:
        value=reused.loader_module.verify(root,reused)
    # Loader source and shared declarations must match the combined Wine build.
    for name in ('source/loader/main.c','source/loader/main.h',
                 'source/include/wine/pear_bootstrap.h','source/include/wine/pear_stage3.h'):
        need(digest((build/name).read_bytes())==value['inputs'][name]['sha256'],'translated_loader_interface')
    return root/'second/wine',dict(receipt=fact(root/'loader.json'),source=fact(root/'main.c'),
                                 artifact=fact(root/'second/wine'),layout=value['layout'])
