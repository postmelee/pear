"""Finite owned-stdin controls; all FD/process/selector operations are mocked."""
from pathlib import Path
import ast
import errno
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
IMPLEMENTATION=Path(os.environ.get('PEAR_TEST_IMPLEMENTATION_ROOT',str(ROOT/'tools/dxmt')))
spec=importlib.util.spec_from_file_location('candidate_metal_stdin',IMPLEMENTATION/'metal_stdin.py')
metal=importlib.util.module_from_spec(spec);spec.loader.exec_module(metal)

class Stream:
    def __init__(self,close_error=None):self.closed=False;self.close_calls=0;self.close_error=close_error
    def fileno(self):return 19
    def flush(self):pass
    def close(self):
        self.close_calls+=1
        if self.close_error is not None:raise self.close_error
        self.closed=True

class Process:
    def __init__(self,polls=None,waits=None,close_error=None):
        self.stdin=Stream(close_error);self.returncode=None;self.polls=list(polls or []);self.waits=list(waits or []);self.wait_calls=[]
    def poll(self):
        self.returncode=self.polls.pop(0)if self.polls else(0 if self.stdin.closed else None)
        return self.returncode
    def wait(self,timeout):
        self.wait_calls.append(timeout)
        outcome=self.waits.pop(0)if self.waits else 0
        if isinstance(outcome,BaseException):raise outcome
        self.returncode=outcome;self.polls.insert(0,outcome);return outcome

class Selector:
    def __init__(self,actions=None,close_error=None):
        self.events={};self.actions=list(actions or []);self.register_calls=[];self.unregister_calls=[];self.close_calls=0;self.close_error=close_error
    def register(self,fd,event):self.register_calls.append((fd,event));self.events[fd]=event
    def unregister(self,fd):self.unregister_calls.append(fd);del self.events[fd]
    def select(self,timeout):
        action=self.actions.pop(0)if self.actions else True
        if isinstance(action,BaseException):raise action
        if not action:return []
        return [(types.SimpleNamespace(fd=fd),event)for fd,event in self.events.items()]
    def close(self):
        self.close_calls+=1
        if self.close_error is not None:raise self.close_error

class Clock:
    def __init__(self,step=.001):self.value=0;self.step=step
    def monotonic(self):self.value+=self.step;return self.value

class IO:
    def __init__(self,writes=None,sizes=None,blocking_error=None):
        self.writes=list(writes or []);self.sizes=list(sizes or []);self.delivered=bytearray();self.requested=[];self.blocking=[];self.blocking_error=blocking_error
    def set_blocking(self,fd,flag):
        self.blocking.append((fd,flag))
        if self.blocking_error is not None:raise self.blocking_error
    def write(self,fd,raw):
        self.requested.append(bytes(raw));outcome=self.writes.pop(0)if self.writes else len(raw)
        if isinstance(outcome,BaseException):raise outcome
        if type(outcome)is int and 0<outcome<=len(raw):self.delivered.extend(raw[:outcome])
        return outcome
    def fstat(self,fd):return types.SimpleNamespace(st_size=self.sizes.pop(0)if self.sizes else 0)

class Pump(unittest.TestCase):
    def run_pump(self,raw=b'abcdef',process=None,selector=None,ops=None,clock=None):
        process=process or Process();selector=selector or Selector();ops=ops or IO();clock=clock or Clock()
        logs=[types.SimpleNamespace(fileno=lambda:10),types.SimpleNamespace(fileno=lambda:11)]
        with patch.object(metal,'os',ops),patch.object(metal,'selectors',types.SimpleNamespace(DefaultSelector=lambda:selector,EVENT_WRITE=2)),patch.object(metal,'time',clock):
            value=metal.pump_stdin(process,raw,logs,0)
        return value,process,selector,ops
    def test_short_writes_preserve_offset_and_exact_bytes(self):
        raw=bytes(range(256))*81;ops=IO(writes=[512,1,4096,17])
        n,p,s,o=self.run_pump(raw,ops=ops)
        self.assertEqual(n,len(raw));self.assertEqual(bytes(o.delivered),raw)
        self.assertEqual(o.blocking,[(19,False)]);self.assertEqual(p.stdin.close_calls,1)
        self.assertEqual(s.register_calls,[(19,2)]);self.assertEqual(s.unregister_calls,[19])
    def test_eagain_and_eintr_do_not_duplicate_or_drop_bytes(self):
        raw=b'abcdefgh';ops=IO(writes=[1,BlockingIOError(errno.EAGAIN,'pressure'),InterruptedError(errno.EINTR,'signal'),2])
        n,p,s,o=self.run_pump(raw,ops=ops);self.assertEqual(n,8);self.assertEqual(o.delivered,raw)
        self.assertEqual(o.requested[1:4],[raw[1:],raw[1:],raw[1:]])
    def test_select_interrupt_and_empty_wait_keep_offset(self):
        s=Selector(actions=[False,InterruptedError(errno.EINTR,'signal'),False,True]);n,p,s,o=self.run_pump(selector=s)
        self.assertEqual(n,6);self.assertEqual(o.delivered,b'abcdef');self.assertEqual(p.stdin.close_calls,1)
    def test_empty_input_closes_eof_without_write(self):
        n,p,s,o=self.run_pump(b'');self.assertEqual(n,0);self.assertEqual(o.requested,[]);self.assertEqual(p.stdin.close_calls,1)
    def test_wait_timeout_after_eof_keeps_log_and_deadline_checks(self):
        p=Process(polls=[None,None,None,None],waits=[subprocess.TimeoutExpired('metal',.1),0])
        n,p,s,o=self.run_pump(process=p);self.assertEqual(n,6);self.assertEqual(len(p.wait_calls),2)
        self.assertTrue(all(0<x<=.1 for x in p.wait_calls));self.assertEqual(p.stdin.close_calls,1)
    def test_poll_zero_before_complete_refuses_success(self):
        p=Process(polls=[0]);ops=IO()
        with self.assertRaisesRegex(metal.Error,'shader_stdin_incomplete'):self.run_pump(process=p,ops=ops)
        self.assertEqual(ops.delivered,b'');self.assertEqual(p.stdin.close_calls,1)
    def test_nonzero_exit_retained_as_compiler_failure(self):
        p=Process(polls=[7])
        with self.assertRaisesRegex(metal.Error,'shader_compiler_exit'):self.run_pump(process=p)
        self.assertEqual(p.returncode,7)
    def test_boolean_exit_is_not_integer_status(self):
        with self.assertRaisesRegex(metal.Error,'shader_compiler_exit_unknown'):self.run_pump(process=Process(polls=[False]))
    def test_partial_timeout_closes_owned_pipe_and_retains_offset(self):
        ops=IO(writes=[1]+[BlockingIOError(errno.EAGAIN,'pressure')]*20);p=Process();s=Selector()
        with patch.object(metal,'TIMEOUT',.015),self.assertRaisesRegex(metal.Error,'shader_timeout'):
            self.run_pump(process=p,selector=s,ops=ops,clock=Clock(.004))
        self.assertLess(len(ops.delivered),6);self.assertEqual(p.stdin.close_calls,1);self.assertEqual(s.close_calls,1)
    def test_output_limit_checked_before_writing(self):
        ops=IO(sizes=[metal.MAX_LOG+1])
        with self.assertRaisesRegex(metal.Error,'shader_output_bound'):self.run_pump(ops=ops)
        self.assertEqual(ops.delivered,b'')
    def test_output_limit_after_final_write_still_refuses(self):
        ops=IO(sizes=[0,0,0,0,metal.MAX_LOG+1])
        with self.assertRaisesRegex(metal.Error,'shader_output_bound'):self.run_pump(ops=ops)
        self.assertEqual(ops.delivered,b'abcdef')
    def test_invalid_write_counts_cannot_advance(self):
        for written in [0,-1,7,True,None]:
            with self.subTest(written=written),self.assertRaisesRegex(metal.Error,'shader_stdin_write_count'):
                self.run_pump(ops=IO(writes=[written]))
    def test_broken_pipe_preserves_actual_errno(self):
        error=BrokenPipeError(errno.EPIPE,'closed')
        with self.assertRaises(BrokenPipeError)as caught:self.run_pump(ops=IO(writes=[error]))
        self.assertIs(caught.exception,error);self.assertEqual(caught.exception.errno,errno.EPIPE)
    def test_primary_write_errno_survives_both_cleanup_failures(self):
        original=OSError(errno.EACCES,'write');p=Process(close_error=OSError(errno.EIO,'close'));s=Selector(close_error=OSError(errno.ENOSPC,'selector'))
        with self.assertRaises(OSError)as caught:self.run_pump(process=p,selector=s,ops=IO(writes=[original]))
        self.assertIs(caught.exception,original)
        self.assertEqual([r['native_error']['code']for r in original.shader_stdin_cleanup_errors],[errno.EIO,errno.ENOSPC])
        self.assertEqual([r['operation']for r in original.shader_stdin_cleanup_errors],['close_stdin','close_stdin_selector'])
    def test_close_failure_is_primary_after_complete_delivery(self):
        original=OSError(errno.EIO,'close');p=Process(close_error=original)
        with self.assertRaises(OSError)as caught:self.run_pump(process=p)
        self.assertIs(caught.exception,original);self.assertEqual(p.stdin.close_calls,1)
    def test_selector_close_failure_blocks_positive_return(self):
        original=OSError(errno.EIO,'selector')
        with self.assertRaises(OSError)as caught:self.run_pump(selector=Selector(close_error=original))
        self.assertIs(caught.exception,original)
    def test_nonblocking_setup_failure_preserves_errno(self):
        original=OSError(errno.EPERM,'nonblocking')
        with self.assertRaises(OSError)as caught:self.run_pump(ops=IO(blocking_error=original))
        self.assertIs(caught.exception,original)
    def test_unowned_event_refused(self):
        s=Selector();s.select=lambda _: [(types.SimpleNamespace(fd=22),2)]
        with self.assertRaisesRegex(metal.Error,'shader_stdin_event'):self.run_pump(selector=s)
    def test_payload_type_checked(self):
        with self.assertRaisesRegex(metal.Error,'shader_stdin_bytes'):self.run_pump(bytearray(b'x'))
    def test_production_bounds_and_success_schema_unchanged(self):
        self.assertEqual(metal.TIMEOUT,600);self.assertEqual(metal.MAX_LOG,1024**2)
        self.assertEqual(metal.SOURCES['src/dxmt/dxmt_command.metal'],('8c07739065fd1b6c0b6d4aebc1e70473ec4918c540cb79f789db8ea113cf2ff0',20732))
        self.assertEqual(metal.HEADER_PIN,('6145cddd7ea3885c1885f1920768c6843655ca178647924a527f91f717ac57d9',627))

if __name__=='__main__':unittest.main()
