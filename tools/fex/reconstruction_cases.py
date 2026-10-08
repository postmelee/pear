#!/usr/bin/env python3
"""Run the required original CPU fixtures on one freshly reconstructed pair.

Reuse signing, current authorization, owned supervision and result readers.
Every case starts with an empty synthetic prefix. Stop on a failed required case
and preserve all original outputs; this command performs no cleanup or upload.
"""
from pathlib import Path
import argparse
import json
import subprocess
import sys
if not __package__:
    here = Path(__file__).resolve().parent
    sys.path[:] = [p for p in sys.path if Path(p or '.').resolve() != here]
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.fex.common import REPO, need, sha256
from tools.fex.integration_fixture import CASES
from tools.fex.reconstruct import save


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('wine', 'fex', 'compiler', 'helper', 'profile', 'reuse', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--cases', choices=CASES, nargs='+', default=list(CASES))
    args = p.parse_args()
    root = args.output.absolute()
    need(root.parent == REPO / '.build/task5' and not root.exists() and
         len(args.cases) == len(set(args.cases)), 'reconstruction_cases_output')
    root.mkdir()
    value = dict(scope='fresh_finite_cpu_integration', passed=False, cases=[],
                 wine_sha256=sha256(args.wine / 'build.json'), fex_sha256=sha256(args.fex / 'build.json'),
                 game_execution=False, distribution_qualified=False)
    def invoke(name, options):
        subprocess.run([sys.executable, str(REPO / 'tools/fex' / name),
                        *map(str, options)], cwd=REPO, check=True)
    try:
        for case in args.cases:
            print('Required fresh-pair case: ' + case, flush=True)
            paths = {name: root.parent / (root.name + '-' + case + '-' + name)
                     for name in ('fixture', 'runtime', 'run', 'assessment')}
            invoke('integration_fixture.py', ['--case', case, '--compiler', args.compiler,
                   '--wire', args.fex / 'wire', '--output', paths['fixture']])
            invoke('integration_runtime.py', ['--reconstruction', '--base', args.wine,
                   '--paired', args.wine, '--fex', args.fex, '--linked', args.fex,
                   '--fixture', paths['fixture'], '--helper', args.helper, '--profile', args.profile,
                   '--signing-source', args.reuse, '--output', paths['runtime']])
            invoke('integration_run.py', ['--runtime', paths['runtime'], '--output', paths['run'],
                   '--reuse', args.reuse])
            invoke('integration_assess.py', ['--runtime', paths['runtime'], '--run', paths['run'],
                   '--output', paths['assessment']])
            row = json.loads((paths['assessment'] / 'control.json').read_text())
            need(row['passed'] and row['source_receipts']['paired'] == value['wine_sha256'] and
                 row['source_receipts']['fex'] == value['fex_sha256'], 'reconstruction_case_pair_changed')
            value['cases'].append(dict(case=case, paths={k:str(v) for k,v in paths.items()}, result=row))
        value['passed'] = True
    finally:
        save(root / 'control.json', value)
        (root / 'producer.py').write_bytes(Path(__file__).read_bytes())


if __name__ == '__main__':
    main()
