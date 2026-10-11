"""Operator-only Stage 2 guard. No GUI execution without a pinned Root grant."""
from pathlib import Path
import argparse
import fcntl
import hashlib
import json
import os
import shutil
import signal
import stat
import subprocess
import time


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(path)


def within(path, root):
    return path == root or path.startswith(root + '/')


def inventory(root):
    root = Path(root)
    require(root.is_dir() and not root.is_symlink(), 'Invalid inventory root')
    rows = {}
    for p in sorted(root.rglob('*')):
        s = p.lstat()
        row = {'mode': stat.S_IMODE(s.st_mode)}
        if p.is_symlink():
            row.update(type='symlink', target=os.readlink(p))
        elif p.is_file():
            row.update(type='file', size=s.st_size, sha256=sha(p))
        elif p.is_dir():
            row.update(type='directory')
        else:
            raise RuntimeError('Unsupported file type')
        rows[str(p.relative_to(root))] = row
    return rows


def check_paths(ready):
    output = Path(ready['output_root'])
    require(output.is_absolute(), 'Output must be absolute')
    for name in ['trial_state', 'trial_app', 'reinstalled_app', 'trial_cache']:
        p = Path(ready[name])
        require(within(str(p), str(output)) and p != output, 'Disposable path escapes output')
        require(p.resolve() == p, 'Disposable path contains symlink')
    existing = Path(ready['existing_state'])
    require(existing.is_absolute() and not within(str(existing), str(output)) and
            not within(str(output), str(existing)), 'Existing private state overlaps disposable output')


def check_inputs(ready):
    check_paths(ready)
    for item in ready['exact_inputs']:
        p = Path(item['path'])
        require(p.is_file() and not p.is_symlink(), 'Missing or linked input')
        require(p.stat().st_size == item['size_bytes'] and sha(p) == item['sha256'],
                'Input identity changed: ' + str(p))
    require(inventory(ready['source_app']) == read(ready['app_inventory']),
            'Source app inventory changed')


def check_grant(ready_path, grant, assignment, output_exists):
    ready = read(ready_path)
    require(grant.get('consumer') == 47 and grant.get('single_use') is True,
            'Single-use Task47 grant required')
    require(grant.get('operation_id') == ready['operation_id'], 'Wrong operation')
    require(grant.get('ready', {}).get('path') == str(Path(ready_path).resolve()) and
            grant['ready'].get('sha256') == sha(ready_path), 'Wrong readiness')
    require(grant.get('allowed_phases') == ready['allowed_phases'], 'Wrong phases')
    require(assignment.get('operation_id') == ready['operation_id'] and
            assignment.get('released') is False, 'No active assignment')
    require(not output_exists, 'Single-use output already exists')


def parse_processes(text):
    result = {}
    for line in text.splitlines():
        a = line.split(None, 8)
        require(len(a) == 9, 'Unexpected process snapshot')
        result[int(a[0])] = {'ppid': int(a[1]), 'pgid': int(a[2]),
                              'birth': ' '.join(a[3:8]), 'exe': a[8]}
    return result


def identity(p):
    return (p['birth'], p['exe'])


def classify(current, baseline, seen, handle_pids, roots, supervisor):
    """Track identity, not PID alone; preserve pre-existing shared OS services."""
    next_seen = dict(seen)
    related = set(handle_pids)
    related.update(pid for pid, p in current.items()
                   if any(within(p['exe'], root) for root in roots))
    changed = True
    while changed:
        prior = len(related)
        related.update(pid for pid, p in current.items()
                       if p['ppid'] in related or p['ppid'] == supervisor)
        changed = len(related) != prior
    excluded = []
    for pid in related:
        if pid == supervisor or pid not in current:
            continue
        p = current[pid]
        if pid in baseline and identity(p) == identity(baseline[pid]):
            excluded.append(pid)
        else:
            next_seen[(pid, *identity(p))] = p
    live = sorted({key[0] for key in next_seen if key[0] in current and
                   identity(current[key[0]]) == key[1:]})
    return next_seen, live, sorted(excluded)


def system_snapshot(roots):
    q = subprocess.Popen(['/bin/ps', '-axo', 'pid=,ppid=,pgid=,lstart=,comm='],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        output, _ = q.communicate(timeout=15)
    except subprocess.TimeoutExpired:
        q.kill(); q.communicate()
        raise RuntimeError('Process inspection timed out')
    require(q.returncode == 0, 'Process inspection failed')
    processes = parse_processes(output)
    processes.pop(q.pid, None)
    q = subprocess.run(['/usr/sbin/lsof', '-nP', '-Fpn'], capture_output=True,
                       text=True, timeout=25)
    require(q.returncode == 0, 'Handle inspection failed')
    pid = None
    handles = set()
    for line in q.stdout.splitlines():
        if line.startswith('p'):
            pid = int(line[1:])
        elif line.startswith('n') and any(within(line[1:], root) for root in roots):
            handles.add(pid)
    return processes, handles


def storage(root):
    logical = allocated = 0
    for p in [Path(root), *Path(root).rglob('*')]:
        s = p.lstat()
        allocated += s.st_blocks * 512
        if stat.S_ISREG(s.st_mode):
            logical += s.st_size
    return logical, allocated


def stop_direct_child(proc):
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def partial_download(cache, name, size):
    cache = Path(cache)
    if (cache / name).exists():
        return False
    return any(not p.is_symlink() and p.is_file() and 0 < p.stat().st_size < size
               for p in cache.glob('*/' + name))


class Guard:
    def __init__(self, ready):
        self.r = ready
        self.out = Path(ready['output_root'])
        self.roots = ready['observed_roots']
        self.baseline, handles = system_snapshot(self.roots)
        require(not handles, 'Observed state already has open handles')
        self.seen = {}
        self.live = []
        self.handles = set()
        self.failed = None
        self.phase = 'prepared'
        self.history = []
        self.last_storage = 0
        self.out.mkdir(mode=0o700)
        (self.out / 'requests').mkdir(mode=0o700)
        (self.out / 'logs').mkdir(mode=0o700)
        self.started = time.monotonic()
        self.partial_seen = False
        self.sequence = 0
        self.emit()

    def emit(self):
        write(self.out / 'status.json', {
            'operation_id': self.r['operation_id'], 'owner_pid': os.getpid(),
            'owner_identity': self.baseline.get(os.getpid()), 'phase': self.phase,
            'failed': self.failed, 'released': False, 'live_owned_pids': self.live,
            'open_handle_pids': sorted(self.handles), 'partial_observed': self.partial_seen,
            'next_request_sequence': self.sequence + 1, 'history': self.history,
            'seen': [{'pid': k[0], 'birth': k[1], 'exe': k[2]} for k in self.seen]})

    def sample(self):
        current, self.handles = system_snapshot(self.roots)
        self.seen, self.live, excluded = classify(current, self.baseline, self.seen,
                                                   self.handles, self.roots, os.getpid())
        self.current = current
        self.excluded = excluded
        steam = self.r['steam_installer']
        if partial_download(self.r['trial_cache'], steam['name'], steam['size_bytes']):
            self.partial_seen = True
        if time.monotonic() - self.last_storage > 10:
            self.last_storage = time.monotonic()
            logical, allocated = storage(self.out)
            logs = sum(p.stat().st_size for p in (self.out / 'logs').glob('*') if p.is_file())
            if (max(logical, allocated) > self.r['budget']['output_stop_bytes'] or
                    logs > self.r['budget']['aggregate_log_stop_bytes'] or
                    shutil.disk_usage(self.out).free < self.r['budget']['free_stop_bytes']):
                self.failed = self.failed or 'Monitored storage/log threshold exceeded; close owned windows normally'
            if time.monotonic() - self.started > self.r['budget']['interval_stop_seconds']:
                self.failed = self.failed or 'Execution budget reached; no more launches; normal cleanup required'
        self.emit()

    def quiet(self, roots):
        self.sample()
        require(not self.live and not self.handles, 'Owned session still active')
        _, handles = system_snapshot(roots)
        require(not handles, 'Target still has handles')

    def command(self, label):
        spec = self.r['commands'][label]
        if self.failed:
            require(spec.get('cleanup') is True, 'Failed interval permits cleanup only')
        path = self.out / 'logs' / (str(self.sequence) + '-' + label + '.log')
        env = {k: os.environ[k] for k in ['HOME', 'USER', 'LOGNAME', 'TMPDIR'] if k in os.environ}
        env['PATH'] = '/usr/bin:/bin:/usr/sbin:/sbin'
        env.update(spec.get('env', {}))
        with path.open('xb') as log:
            proc = subprocess.Popen(spec['argv'], env=env, stdin=subprocess.DEVNULL,
                                    stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            deadline = time.monotonic() + spec['timeout_seconds']
            while proc.poll() is None:
                try:
                    self.sample()
                except Exception:
                    stop_direct_child(proc)
                    self.history.append({'command': label, 'stopped_direct_child_after_inspection_failure': True})
                    raise
                if (time.monotonic() >= deadline or path.stat().st_size > spec['log_stop_bytes'] or
                        (self.failed and not spec.get('cleanup'))):
                    stop_direct_child(proc)
                    self.history.append({'command': label, 'forced_direct_child_stop': True})
                    raise RuntimeError('Owned command exceeded monitored budget; dependent work stopped')
                time.sleep(.2)
        self.history.append({'command': label, 'exit_code': proc.returncode, 'log_sha256': sha(path)})
        require(proc.returncode == 0, label + ' failed')

    def dispatch(self, request):
        action = request['action']
        spec = self.r['actions'].get(action)
        require(spec is not None, 'Unknown action')
        require(self.phase in spec['from'], 'Out-of-order action')
        require(not self.failed or spec.get('cleanup'), 'Failure blocks new work')
        if spec.get('quiet'):
            self.quiet(self.roots)
        if action in ['install-app', 'reinstall-app']:
            target = Path(self.r['trial_app'] if action == 'install-app' else self.r['reinstalled_app'])
            require(not target.exists(), 'Preserve existing app target')
            if action == 'reinstall-app':
                prior = Path(self.r['trial_app'])
                require(inventory(prior) == read(self.r['app_inventory']), 'Trial app changed')
                shutil.rmtree(prior)
            if action == 'install-app':
                Path(self.r['trial_state']).parent.mkdir(parents=True, exist_ok=True)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(self.r['source_app'], target, symlinks=True)
            require(inventory(target) == read(self.r['app_inventory']), 'Copied app changed')
        if action == 'confirm-interrupted':
            require(self.partial_seen, 'No partial network download observed')
            cache = Path(self.r['trial_cache'])
            require(not any(cache.iterdir()), 'Partial cache was not cleaned')
            require(not Path(self.r['trial_state'], 'private/steam.ready').exists(), 'Steam already activated')
        if action == 'confirm-login':
            require(request.get('observation') == 'login-visible-no-signin', 'Explicit visual observation required')
            s = self.r['steam_installer']; p = Path(self.r['trial_cache']) / s['name']
            require(p.is_file() and not p.is_symlink() and p.stat().st_size == s['size_bytes'] and sha(p) == s['sha256'], 'Final download does not match pin')
            require(Path(self.r['trial_state'], 'private/steam.ready').read_text() == s['sha256'], 'Steam setup marker missing')
        if action == 'confirm-library':
            require(request.get('observation') == 'steam-library-visible', 'Explicit library observation required')
        if action == 'abort-release':
            self.failed = self.failed or 'Operator aborted; remaining cases incomplete'
        if action == 'confirm-game-exit':
            require(request.get('observation') == 'menu-input-progress-preserved-normal-exit', 'Requester observation required')
            self.sample()
            require(not any('megabonk' in self.current[pid]['exe'].lower() for pid in self.live), 'Game still active')
        if action == 'finish':
            require(not self.failed, 'Failed interval must use abort-release')
        if action in ['shutdown-trial', 'shutdown-existing']:
            self.sample()
            require(not any('megabonk' in self.current[pid]['exe'].lower() for pid in self.live),
                    'Game must exit normally before Steam shutdown')
        if 'command' in spec:
            self.command(spec['command'])
        if action == 'dispose-trial':
            require(request.get('observation') == 'no-signin-no-private-data', 'Private trial must be preserved unless no sign-in confirmed')
            state = Path(self.r['trial_state'])
            logical, allocated = storage(state)
            before = shutil.disk_usage(self.out).free
            shutil.rmtree(state)
            self.history.append({'trial_removed': True, 'logical_bytes': logical,
                                 'stat_allocated_bytes': allocated,
                                 'measured_free_delta_bytes': shutil.disk_usage(self.out).free - before})
        self.phase = spec.get('to', self.phase)
        self.history.append({'action': action, 'observation': request.get('observation')})
        self.emit()

    def loop(self):
        while self.phase != 'released':
            try:
                self.sample()
            except Exception as e:
                self.failed = self.failed or 'Inspection failed: ' + str(e)
                self.emit()
            request = self.out / 'requests' / f'{self.sequence + 1:03}.json'
            if request.exists():
                self.sequence += 1
                try:
                    require(not request.is_symlink(), 'Linked request refused')
                    self.dispatch(read(request))
                except Exception as e:
                    self.failed = self.failed or str(e)
                    self.history.append({'failed_request': self.sequence, 'error': str(e)})
                    self.emit()
            time.sleep(.5)
        return {'operation_id': self.r['operation_id'], 'status': 'failed' if self.failed else 'passed',
                'failure': self.failed, 'owner_pid': os.getpid(), 'interval_guard_finished': True,
                'released': False, 'requires_independent_owner_exit_and_lock_check': True,
                'live_owned_pids': self.live, 'open_handle_pids': sorted(self.handles),
                'preexisting_services_preserved': self.excluded, 'history': self.history}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ready', required=True, type=Path)
    parser.add_argument('--grant', type=Path)
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args()
    ready = read(args.ready)
    check_inputs(ready)
    if args.validate_only:
        print('Pinned inputs and app inventory match; no execution performed.')
        return
    require(args.grant is not None, 'Fresh Root grant required')
    grant = read(args.grant)
    assignment = read(ready['assignment_path'])
    check_grant(args.ready, grant, assignment, Path(ready['output_root']).exists())
    grant_digest = sha(args.grant)
    guard = None
    with open(ready['shared_lock'], 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(sha(args.grant) == grant_digest, 'Grant changed')
        check_grant(args.ready, grant, read(ready['assignment_path']), Path(ready['output_root']).exists())
        require(shutil.disk_usage(Path(ready['output_root']).parent).free >= ready['budget']['minimum_free_bytes'], 'Insufficient start headroom')
        guard = Guard(ready)
        def stop(signum, frame):
            guard.failed = guard.failed or f'Signal {signum}; preserve ownership and use normal cleanup'
        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)
        result = guard.loop()
        write(Path(ready['output_root']) / 'guard-result.json', result)
    print('Guard exited; independent owner/handle/lock verification is still required.')


if __name__ == '__main__':
    main()
