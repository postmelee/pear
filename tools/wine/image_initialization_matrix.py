# SPDX-License-Identifier: MIT
"""Run the approved ordering and graphics matrix once on one admitted candidate."""
from pathlib import Path
import argparse,fcntl,json
from tools.wine.image_admission_inputs import REPO,read,save,fact,need
from tools.wine.image_admission_correction_runtime import admit
from tools.wine.image_initialization_regression import ordered
from tools.wine.image_initialization_regression_run import run
from tools.wine import image_initialization_graphics as graphics,image_initialization_pairing as pairing

def matrix(runtime,cpu,output,verify_only=False):
    v=admit(runtime);i=read(Path(v['image_admission_correction_overlay']['inputs_ref']['path']))
    reuse=Path(v['graphics_repo']);seed=Path(i['seed_ref']['path']).parent;root=REPO/'.build/task40'
    result=dict(scope='image_initialization_ordering_graphics',passed=False,runtime_ref=fact(runtime/'runtime.json'),observations={},game_qualified=False)
    try:
        result['observations']['ordering']=ordered(runtime,cpu,reuse,root/'stage3-ordering.json','stage3',seed=seed,verify_only=verify_only)
        device=root/'stage3-device';native=root/'stage3-native'
        for case in ('device','native','rendering','presentation-frames','rendering-original','presentation-original'):
            print('Graphics regression: '+case,flush=True)
            folder=root/('stage3-'+case)
            if not folder.exists():
                need(not verify_only,'image_graphics_missing_run')
                if case=='native':pairing.run(runtime,folder,reuse,device)
                else:run(runtime,folder,reuse,case,seed=seed)
            result['observations'][case]=graphics.native(runtime,folder) if case=='native' else graphics.verify(folder,runtime,native)
        result['passed']=True
    finally:
        if not verify_only:save(output,result)
    # Existing presentation readers return callback tuples; JSON stores arrays.
    result=json.loads(json.dumps(result))
    if verify_only:need(read(output)==result,'image_matrix_replay')
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('runtime','cpu-repo','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--verify-only',action='store_true');a=p.parse_args()
    with open('/private/tmp/pear-native-compilation.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);matrix(a.runtime.resolve(),a.cpu_repo.resolve(),a.output.resolve(),a.verify_only)
