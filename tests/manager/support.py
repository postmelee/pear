"""Task #9 glue reusing #3 build verification and bounded process capture."""
import importlib.util
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
experiment_build = load('task9_original_build', REPO / 'experiments/manager/build.py')
experiment_cases = load('task9_original_cases', REPO / 'experiments/manager/run_cases.py')
