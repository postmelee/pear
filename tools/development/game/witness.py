# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: MIT
"""Independent read-only parent continuity witness; never launches/signals a game."""
from pathlib import Path
from types import SimpleNamespace
import argparse,json,os,re,select,time
from pear_runtime.fixtures.inputs import read,need,fact
from tools.development.game.watch import QueueTap

def atomic(path,value):
    path=Path(path);temporary=path.with_suffix(path.suffix+'.tmp')
    with temporary.open('w') as stream:json.dump(value,stream,sort_keys=True);stream.write('\n')
    temporary.replace(path)

def live_stamp(root,deadline,clock=time.monotonic_ns):
    need(type(deadline) is int and 0<deadline<2**63,'play_witness_deadline')
    now=clock()
    need(type(now) is int and 0<now<deadline,'play_witness_expired')
    need(not (Path(root)/'witness-stop').exists(),'play_witness_stopped')
    return now

def publish_positive(path,value,deadline,clock=time.monotonic_ns):
    path=Path(path);temporary=path.with_suffix(path.suffix+'.tmp')
    value.update(deadline_ns=deadline,at_ns=live_stamp(path.parent,deadline,clock))
    with temporary.open('w') as stream:json.dump(value,stream,sort_keys=True);stream.write('\n')
    # Evidence is as-of at_ns. Expiry or stop during serialization must not
    # publish a new positive receipt; consumers also recheck time/liveness.
    live_stamp(path.parent,deadline,clock)
    temporary.replace(path)

def witness(config, *, observer_factory):
    config=Path(config);need(not config.is_symlink() and config.stat().st_size<=65536,'play_witness_config')
    v=read(config);root=Path(v['output']);need(root.is_dir() and root.resolve()==root and not root.is_symlink(),'play_witness_output')
    parent=v['owner_identity'];need(parent['pid']==os.getppid(),'play_witness_parent')
    live_stamp(root,v['deadline_ns'])
    original=observer_factory();tap=QueueTap(original.queue);observer=SimpleNamespace(queue=tap,identity=original.identity,executable=original.executable,refresh=lambda:tap.control(None,8,0))
    row=SimpleNamespace(pid=parent['pid'],identity=parent,allowed_paths={v['owner_executable']},exited=False,reaped=False)
    value=dict(schema=1,config=fact(config),operation_id=v['operation_id'],watcher_pid=os.getpid(),watcher_identity=original.identity(os.getpid()),owner_identity=parent,run=v['run'],candidate=v['candidate'],valid=False)
    try:
        need(observer.identity(row.pid)==parent and observer.executable(row.pid)==v['owner_executable'],'play_witness_initial_identity')
        tap.control([select.kevent(row.pid,filter=select.KQ_FILTER_PROC,flags=select.KQ_EV_ADD|select.KQ_EV_ENABLE|select.KQ_EV_CLEAR,fflags=select.KQ_NOTE_EXEC|select.KQ_NOTE_EXIT)],0,0)
        segment=tap.arm(observer,row,v['run'],v['candidate'],role='owner')
        value.update(segment=segment.snapshot(),valid=True);publish_positive(root/'witness-ready.json',value,v['deadline_ns'])
        last=None
        while time.monotonic_ns()<v['deadline_ns'] and not (root/'witness-stop').exists():
            tap.fresh(observer,row)
            need(os.getppid()==parent['pid'],'play_witness_reparented')
            path=root/'witness-challenge.json'
            if path.exists():
                need(not path.is_symlink() and path.stat().st_size<=65536,'play_witness_challenge_file')
                challenge=read(path)
                need(challenge['operation_id']==v['operation_id'] and challenge['owner']==segment.binding and re.fullmatch('[0-9a-f]{32}',challenge['nonce']) is not None,'play_witness_challenge_binding')
                if challenge['nonce']!=last:
                    tap.fresh(observer,row);now=time.monotonic_ns()
                    need(type(challenge['after_ns']) is int and segment.ready_ns<=challenge['after_ns']<=now,'play_witness_challenge_clock')
                    last=challenge['nonce'];value.update(valid=True,segment=segment.snapshot(),at_ns=now,nonce=last,request_id=challenge['request_id'])
                    publish_positive(root/'witness-response.json',value,v['deadline_ns'])
            time.sleep(.02)
        value.update(valid=False,reason='stopped' if (root/'witness-stop').exists() else 'deadline',at_ns=time.monotonic_ns())
    except BaseException as error:
        value.update(valid=False,reason=str(error),at_ns=time.monotonic_ns());raise
    finally:
        tap.close();value.update(segment=tap.segment.snapshot() if tap.segment else None);atomic(root/'witness-final.json',value)

def main(argv=None):
    """Admit the parent's exact provider binding before entering the witness."""
    from pear_runtime.fixtures.supervision import companion_provider
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,required=True)
    config=parser.parse_args(argv).config
    reference=fact(config);value=read(config)
    with companion_provider(value['provider_root'], provider_ref=value['provider_ref'],
                            source_refs=value['source_refs']) as namespace:
        need(fact(config)==reference,'play_witness_config_changed')
        witness(config,observer_factory=namespace.DarwinObserver)
        need(fact(config)==reference,'play_witness_config_changed')


if __name__=='__main__':main()
