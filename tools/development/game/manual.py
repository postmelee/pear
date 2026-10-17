# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: MIT
"""Manual-only real-game input; unchanged capture, witness and terminal guards."""
from pathlib import Path
from time import monotonic_ns
from pear_runtime.fixtures.inputs import need,fact
from tools.development.game.inputs import coordination_read
from tools.development.game.adapter import Adapter
class ManualAdapter(Adapter):
    def input(self,request):
        # Refuse before consulting permissions or posting any event.
        need(False,'play_manual_only_no_automated_input')
    def verify(self,request):
        need(request['observed_by']=='assistant_visual_inspection','play_manual_visual_observer')
        need(request.get('input_source')=='human' and 'input_evidence' not in request,'play_manual_input_source')
        refs=request['evidence'];need(type(refs) is list and len(refs)==2 and refs[0]!=refs[1],'play_manual_frame_pair')
        rows=[]
        for ref in refs:
            need(ref in self.frames and fact(ref['path'])==ref,'play_manual_frame_reference')
            row=coordination_read(ref['path'])
            need(row['renderer']==self.renderer.binding and row['owner']==self.owner.binding and row['window_id']==self.window and fact(row['image']['path'])==row['image'],'play_manual_frame_binding')
            need(self.renderer.ready_ns<=row['started_ns']<=row['ended_ns']<=request['at_ns'] and request['at_ns']-row['ended_ns']<=60_000_000_000,'play_manual_frame_age');rows.append(row)
        need(rows[0]['ended_ns']<rows[1]['started_ns'],'play_manual_frame_order')
        need(request['response_observed']=='in-game movement or action changed visibly','play_manual_response')
        # Human testimony is retained as testimony, not a generated input receipt.
        ref=request['human_observation'];path=Path(ref['path'])
        need(path.parent==self.root and path.name=='human-observation.json' and not path.is_symlink() and path.stat().st_size<=16384 and fact(path)==ref,'play_manual_human_reference')
        human=coordination_read(path)
        need(human['source']=='direct_user_message' and type(human['message']) is str and 0<len(human['message'])<=4096,'play_manual_human_source')
        need(human['renderer']==self.renderer.binding and human['owner']==self.owner.binding and human['window_id']==self.window and human['operation_id']==self.operation,'play_manual_human_binding')
        need(human['actual_play'] is True and human['input_responsive'] is True,'play_manual_human_claim')
        need(type(human['recorded_ns']) is int and rows[0]['started_ns']<=human['recorded_ns']<=request['at_ns'],'play_manual_human_time')
        need(self.input_count==0 and not self.input_records and self.pending_key is None,'play_manual_zero_posted_input')
        now=monotonic_ns()
        expiry=min(*(row['ended_ns']+60_000_000_000 for row in rows),human['recorded_ns']+60_000_000_000)
        need(request['at_ns']<=now<expiry,'play_manual_evidence_expired')
        request['evidence_deadline_ns']=expiry
        return True
