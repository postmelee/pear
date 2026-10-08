# SPDX-License-Identifier: MIT
"""Replay the final #8 candidate's finite graphics and CPU evidence."""
from pathlib import Path
from tools.dxmt.translated_inputs import REPO, read, save, fact, need

REQUIRED = ('runtime', 'device', 'presentation', 'pairing', 'rendering', 'cpu_dependencies')
FILENAMES = dict(runtime='runtime.json', device='case.json', presentation='case.json',
                 pairing='result.json', rendering='case.json')

def references(index):
    need(index.get('scope') == 'translated_graphics_stage4' and index.get('stage') == 4,
         'graphics_final_scope')
    refs = index.get('references', {})
    need(set(refs) == set(REQUIRED), 'graphics_final_reference_set')
    for key, row in refs.items():
        need(key not in FILENAMES or Path(row['path']).name == FILENAMES[key],
             'graphics_final_reference_filename')
        need(fact(row['path']) == row, 'graphics_final_reference_changed')
    return {key: Path(row['path']) for key, row in refs.items()}

def verify(index_path):
    from tools.dxmt.translated_surface_runtime import admit
    from tools.dxmt.translated_check import device
    from tools.dxmt.translated_present_check import stage_three
    index = read(index_path)
    paths = references(index)
    runtime = paths['runtime'].parent
    need(runtime.parent == REPO / '.build/task8', 'graphics_final_runtime_location')
    value = admit(runtime)
    # The overlay admissions recursively check actual source/patch/tool/build and
    # payload origins. Existing readers reopen logs, images and native references;
    # a previously saved assessment's boolean cannot satisfy this gate.
    current_device = device(paths['device'].parent, runtime)
    integrated = stage_three(paths['presentation'].parent, runtime,
                             paths['pairing'].parent, paths['rendering'].parent,
                             paths['cpu_dependencies'])
    need(current_device['passed'] and integrated['passed'], 'graphics_final_incomplete')
    need(len(integrated['visible']) == 18 and integrated['native']['physical_destroyed'] == 9,
         'graphics_final_display_lifetime')
    result = dict(scope='bounded_translated_d3d11_correctness', stage=4, passed=True,
                  index_ref=fact(index_path), references=index['references'],
                  cases_ref=fact(REPO / 'tests/dxmt/translated_cases.json'),
                  checker_ref=fact(Path(__file__)),
                  runtime_source_identity='recursive source, patch, tool, build, payload and signature records',
                  native_image_count=len(value['native_images']), device=current_device,
                  integrated=integrated, replay_only=True,
                  no_rosetta_in_observed_processes_and_images=True,
                  complete_late_load_coverage=False, game_qualified=False,
                  distribution_qualified=False, performance_qualified=False)
    return result
