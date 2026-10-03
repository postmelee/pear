"""Independent finite original-continuation transcript controls; no host admission."""
from copy import deepcopy
import unittest
from tools.fex import memory_resume_checks as checks
from tools.fex.common import Error, need
from tests.fex.test_memory_check import atomic_rows

class AtomicTranscriptControls(unittest.TestCase):
    def test_current_epoch_resume_consumes_only_original_pin(self):
        value=checks.validate(atomic_rows(),need)
        self.assertEqual(value['committed_resumes'],1)
        self.assertFalse(value['source_lifetime_qualified'])
        self.assertFalse(value['fex_initialization'])

    def test_invented_or_lost_pin_cannot_become_a_retry_proof(self):
        for field,value in [('continuation_id',0),('continuation_id',32),('write_epoch',37),
                ('generation',20),('executor_id',24),('executor_state',2),('protection',2)]:
            rows=atomic_rows();row=next(r for r in rows if r['control']=='atomic_refusal_preserves_original_pin')
            row[field]=value
            with self.subTest(field=field,value=value),self.assertRaises(Error):checks.validate(rows,need)

    def test_committed_resume_requires_exact_current_epoch_and_rx_active(self):
        for field,value in [('write_epoch',29),('continuation_id',31),('executor_state',3),
                ('allocation_id',18),('extent_size',32768),('lifecycle',2),('protection',1),
                ('operation_size','0000000000000000'),('operation_offset','0000000000000004')]:
            rows=atomic_rows();row=next(r for r in rows if r['control']=='atomic_consume_original_pin_on_current_epoch')
            row[field]=value
            with self.subTest(field=field,value=value),self.assertRaises(Error):checks.validate(rows,need)

    def test_retirement_and_consumed_continuation_refusals_cannot_be_relabelled(self):
        for name in ('atomic_retirement_preserves_original_pin','atomic_original_epoch_requires_retry',
                     'atomic_consumed_continuation_cannot_repeat'):
            rows=atomic_rows();next(r for r in rows if r['control']==name)['status']=0
            with self.subTest(control=name),self.assertRaises(Error):checks.validate(rows,need)

    def test_poll_and_commit_must_follow_their_actual_operations(self):
        for left,right in [(2,3),(21,22),(22,23),(23,24)]:
            rows=atomic_rows();rows[left],rows[right]=rows[right],rows[left]
            with self.subTest(pair=(left,right)),self.assertRaises(Error):checks.validate(rows,need)

    def test_missing_duplicate_and_extra_controls_do_not_complete(self):
        rows=atomic_rows()
        for damaged in (rows[:-1],rows+[deepcopy(rows[2])],rows[:3]+rows[4:]):
            with self.subTest(length=len(damaged)),self.assertRaises(Error):checks.validate(damaged,need)

    def test_exit_is_checked_and_keeps_current_allocation_identity(self):
        for field,value in [('executor_state',2),('write_epoch',29),('continuation_id',31),
                ('executor_id',24),('protection',2)]:
            rows=atomic_rows();rows[-1][field]=value
            with self.subTest(field=field),self.assertRaises(Error):checks.validate(rows,need)

if __name__=='__main__':unittest.main()
