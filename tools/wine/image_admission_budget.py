# SPDX-License-Identifier: MIT
"""Read-only PE relocation and arena payload accounting; not a runtime grant."""
from pathlib import Path
import argparse,struct
from tools.wine.image_admission_inputs import admit,checked,fact,read,save,need,digest

def budget(inputs,run):
    i=admit(inputs);r=read(run/'case.json');assessment=read(run/'assessment.json')
    need(assessment['passed'] and assessment['run_ref']==fact(run/'case.json'),'image_budget_unassessed')
    need(r['inputs_ref']==fact(inputs/'inputs.json'),'image_budget_inputs')
    raw=(Path(i['game'])/'GameAssembly.dll').read_bytes();p=i['pe']
    def offset(rva,size):
        for s in p['sections']:
            if s['rva']<=rva and rva+size<=s['rva']+s['raw_bytes']:return s['raw_offset']+rva-s['rva']
        need(False,'image_relocations_unmapped')
    start=offset(p['relocation_rva'],p['relocation_directory_bytes']);end=start+p['relocation_directory_bytes'];cursor=start;types={};targets=[];blocks=0
    need(end<=len(raw),'image_relocations_file_bounds')
    while cursor<end:
        need(cursor+8<=end,'image_relocation_header');page,size=struct.unpack_from('<II',raw,cursor)
        need(size>=8 and size%2==0 and cursor+size<=end and page%4096==0,'image_relocation_block')
        for pos in range(cursor+8,cursor+size,2):
            item=struct.unpack_from('<H',raw,pos)[0];kind=item>>12;types[str(kind)]=types.get(str(kind),0)+1
            need(kind in (0,10),'image_relocation_type')
            if kind:
                target=page+(item&4095);need(target+8<=p['image_bytes'],'image_relocation_target')
                targets.append(target)
        blocks+=1;cursor+=size
    ordered=sorted(targets);need(all(a+8<=b for a,b in zip(ordered,ordered[1:])),'image_relocation_overlap')
    publications=[e for e in r['events']['loader'] if e['event']=='arena_publish']
    arena=next(e for e in r['events']['loader'] if e['event']=='arena_reserve')
    used=max(e['base']+e['capacity']-arena['interior_base'] for e in publications)
    need(used<=arena['interior_bytes'],'image_arena_accounting')
    ceiling=64*1024**2
    v=dict(scope='image_admission_budget_proposal',producer=fact(Path(__file__)),inputs_ref=fact(inputs/'inputs.json'),assessment_ref=fact(run/'assessment.json'),
           image_sha256=p['sha256'],image_bytes=p['image_bytes'],slot_bytes=p['slot_bytes'],relocation_blocks=blocks,relocation_types=types,
           dir64_relocations=len(targets),relocation_overlap_count=0,staging_bytes=p['staging_bytes'],page_metadata_bytes=p['page_metadata_bytes'],
           relocation_array_allocated_bytes=p['conservative_relocation_array_bytes'],plan_struct_bytes=88,
           actual_temporary_payload_upper=p['staging_bytes']+p['page_metadata_bytes']+p['conservative_relocation_array_bytes']+88,
           observed_published_images=len(publications),end_of_diagnostic_pe_high_water_bytes=used,
           with_target_high_water_bytes=used+p['slot_bytes'],interior_bytes=arena['interior_bytes'],headroom_after_target=arena['interior_bytes']-used-p['slot_bytes'],
           proposed_max_image_bytes=ceiling,proposed_plan_payload_bound=ceiling+ceiling//4096+ceiling//8*4+88,
           proposed_mapping_change=False,proposed_slot_count_change=False,proposed_fex_geometry_change=False,
           budget_approved=False,game_qualified=False,
           limitations=['Payload bytes exclude allocator bookkeeping and other process memory.','Observed image set is diagnostic-only; later game loads are not bounded by this observation.','Relocation storage is the current parser allocation, not just the count of nonpadding entries.'])
    save(run/'budget.json',v);print({k:v[k] for k in ('dir64_relocations','actual_temporary_payload_upper','headroom_after_target','proposed_max_image_bytes')})
    return v

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inputs',type=Path,required=True);p.add_argument('--run',type=Path,required=True)
    a=p.parse_args();budget(a.inputs.resolve(),a.run.resolve())
