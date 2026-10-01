"""Compile the current PE adapter with Wine's actual generated PE recipe.

Only one object is compiled; no retained source/object is modified, linked,
loaded or executed. The Makefile and generated headers are local compiler
inputs, not independent historical-build qualification evidence.
"""
import hashlib
from pathlib import Path
import shlex
import struct
import subprocess
import sys
import tempfile
import unittest

REPO = next(parent for parent in Path(__file__).resolve().parents
            if (parent / 'runtime/wine/patches/series.json').is_file())
sys.path.insert(0, str(REPO / 'tests/wine'))
from stage4_source import materialize

BUILD = REPO / '.build/task4/build-stage5'
TARGET = 'dlls/winemac.drv/aarch64-windows/pear_window_control.o'


def production_recipe(build, source, output):
    """Expand only the declared compiler variables; never interpret a shell."""
    lines = (build / 'objects/Makefile').read_text().splitlines()
    values = {}
    for key in ('srcdir', 'aarch64_CC', 'aarch64_CFLAGS'):
        found = [line.split(' = ', 1)[1] for line in lines if line.startswith(key + ' = ')]
        if len(found) != 1:
            raise ValueError('missing or ambiguous production recipe variable: ' + key)
        values[key] = found[0]
    starts = [i for i, line in enumerate(lines) if line.startswith(TARGET + ': ') and
              line.endswith('/pear_window_control.c')]
    if len(starts) != 1 or not lines[starts[0] + 1].startswith('\t$(aarch64_CC) '):
        raise ValueError('production adapter compile rule is missing or ambiguous')
    index, recipe = starts[0] + 1, []
    while True:
        line = lines[index]
        recipe.append(line.rstrip('\\'))
        if not line.endswith('\\'):
            break
        index += 1
    text = ' '.join(recipe)
    for key in ('aarch64_CC', 'aarch64_CFLAGS'):
        text = text.replace('$(' + key + ')', values[key])
    text = text.replace('$@', '__PEAR_OUTPUT__')
    if '$' in text:
        raise ValueError('unsupported production recipe variable')
    argv = shlex.split(text)
    argv[0] = str(REPO / '.build/task4/tools/llvm-mingw/bin/clang')
    original = values['srcdir'] + '/dlls/winemac.drv/pear_window_control.c'
    for index, word in enumerate(argv):
        if word == '__PEAR_OUTPUT__':
            argv[index] = str(output)
        elif word == original:
            argv[index] = str(source)
        elif word.startswith('-I' + values['srcdir']):
            argv[index] = '-I' + str(build / 'source') + word[len('-I' + values['srcdir']):]
    required = {'-D_UCRT', '-D__WINESRC__', '-D__WINE_PE_BUILD', '--no-default-config', '-target'}
    if not required <= set(argv) or argv[argv.index('-target') + 1] != 'aarch64-windows':
        raise ValueError('production Windows PE compilation mode changed')
    if '-I' + str(build / 'source/include/msvcrt') not in argv:
        raise ValueError('production Wine CRT include path is missing')
    return argv


class WindowControlCompileTests(unittest.TestCase):
    def test_actual_wine_pe_recipe_compiles_source_bound_adapter(self):
        compiler = REPO / '.build/task4/tools/llvm-mingw/bin/clang'
        if not compiler.is_file():
            self.skipTest('prepared ARM64 PE compiler is unavailable')
        if not (BUILD / 'objects/Makefile').is_file() or not (BUILD / 'objects/include/config.h').is_file():
            self.skipTest('configured Wine PE compile recipe/headers are unavailable')
        source_text = materialize('dlls/winemac.drv/pear_window_control.c')
        self.assertEqual(source_text, (REPO / 'tests/wine/fixtures/window_control_pe.c').read_text())
        retained = BUILD / 'source/dlls/winemac.drv/pear_window_control.c'
        before = hashlib.sha256(retained.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(prefix='pear-window-control-compile-') as name:
            root = Path(name)
            source = root / 'pear_window_control.c'
            source.write_text(source_text)
            for header in ('unixlib.h', 'stage5_protocol.h'):
                (root / header).write_text(materialize('dlls/winemac.drv/' + header))
            # The second target changes only the recorded recipe's target
            # selector. It is an object check, not an ARM64EC companion build.
            for target, machine in (('aarch64-windows', 0xaa64), ('arm64ec-windows', 0xa641)):
                with self.subTest(target=target):
                    output = root / (target + '.o')
                    command = production_recipe(BUILD, source, output)
                    command[command.index('-target') + 1] = target
                    result = subprocess.run(command, cwd=BUILD / 'objects',
                                            capture_output=True, text=True, timeout=60)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertTrue(output.is_file())
                    data = output.read_bytes()
                    self.assertGreater(len(data), 20)
                    self.assertEqual(struct.unpack_from('<H', data)[0], machine)
        self.assertEqual(hashlib.sha256(retained.read_bytes()).hexdigest(), before)


if __name__ == '__main__':
    unittest.main()
