# SPDX-License-Identifier: MIT
"""Replay the complete #40 Stage 3 claim without asserting playable support."""
from pathlib import Path
import argparse,json
from tools.wine.image_admission_inputs import REPO,read,save,fact,need
from tools.wine.image_admission_correction_runtime import admit
from tools.wine.image_initialization_check import inspect
from tools.wine.image_initialization_regression import corpus
from tools.wine.image_initialization_matrix import matrix

def verify(index,verify_only=False):
    q=read(index);runtime=Path(q['runtime']).resolve();v=admit(runtime)
    need(q['runtime_ref']==fact(runtime/'runtime.json'),'image_qualification_candidate')
    cpu=Path(q['cpu_repo']).resolve();game=Path(q['game_run']).resolve()
    initialized,_=inspect(game,require_initialized=True)
    need(initialized['runtime_ref']==q['runtime_ref'],'image_game_candidate')
    comparison=corpus(runtime,cpu,Path(v['graphics_repo']),REPO/'.build/task40/stage3-cpu.json','stage3',verify_only=True)
    graphics=matrix(runtime,cpu,REPO/'.build/task40/stage3-matrix.json',verify_only=True)
    need(comparison['runtime_ref']==q['runtime_ref']==graphics['runtime_ref'],'image_matrix_candidate')
    recoveries={}
    for case in ('rendering-original','presentation-original'):
        raw=REPO/'.build/task40'/('stage3-'+case)/'run/loader.stderr.log'
        need(b'Unaligned.repaired' in raw.read_bytes(),'image_original_recovery_missing')
        recoveries[case]=dict(observed=True,log_ref=fact(raw))
    result=dict(scope='gameassembly_initialization_and_finite_regression',passed=True,stage=3,
                runtime_ref=q['runtime_ref'],game=initialized,cpu=comparison,ordering_graphics=graphics,scalar_repair=recoveries,
                checker=fact(Path(__file__)),
                readers=[fact(p) for p in sorted((REPO/'tools/wine').glob('image_initialization*.py'))]+
                        [fact(REPO/'tools/dxmt'/name) for name in ('translated_check.py','translated_render_check.py','translated_present_check.py','translated_surface_check.py','run_pairing.py')],
                gameplay_qualified=False,m1_qualified=False,
                next_blocker=dict(owner_issue=11,observation='Startup did not finish within 120 seconds after IL2CPP metadata open and GC finalizer startup.',cause='unresolved; repeated native/guest continuation is an observation, not a diagnosed cause'),
                steam_qualification_issue=11,gameplay_persistence_issue=12,complete_observation_issue=10)
    result=json.loads(json.dumps(result))
    output=index.with_name('stage3-qualification.json')
    if verify_only:need(read(output)==result,'image_qualification_replay')
    else:save(output,result)
    print(dict(passed=True,stage=3,dll_initialized=True,next_phase_confirmed=True,gameplay_qualified=False))
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--index',type=Path,required=True);p.add_argument('--verify-only',action='store_true');a=p.parse_args();verify(a.index.resolve(),a.verify_only)
