"""Finite synthetic observer peer; no real process/module observation authority."""
import copy
import hashlib
import json
import socket
import struct
import threading
import time

def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def reference(record,path):return {'ref_type':'record','path':path,'record_kind':'launch','schema_version':record['schema_version'],'digest':{'algorithm':'sha256','scope':'exact_utf8_file_bytes','value':hashlib.sha256(encoded(record)).hexdigest()}}
class Peer:
    def __init__(self,mode='normal'):
        self.client,self.server=socket.socketpair();self.server.settimeout(.1);self.client.setsockopt(socket.SOL_SOCKET,socket.SO_SNDBUF,1024)
        self.release_ready=threading.Event();self.mode=mode;self.stop=threading.Event();self.events=[];self.error=None;self.ready_sent=threading.Event();self.hello_seen=threading.Event();self.thread=threading.Thread(target=self.run,daemon=True)
    def start(self):self.thread.start()
    def close(self):
        self.stop.set();self.client.close()
        try:self.server.shutdown(socket.SHUT_RDWR)
        except OSError:pass
        self.server.close();self.thread.join(timeout=3)
        if self.thread.is_alive():raise AssertionError('synthetic peer did not stop')
    def receive(self):
        def read(size):
            data=b''
            while len(data)<size:
                if self.stop.is_set():raise EOFError
                try:part=self.server.recv(size-len(data))
                except socket.timeout:continue
                if not part:raise EOFError
                data+=part
            return data
        length=struct.unpack('!I',read(4))[0]
        if not 0<length<=262144:raise ValueError('frame bound')
        return json.loads(read(length))
    def send(self,value):
        body=encoded(value);self.server.sendall(struct.pack('!I',len(body))+body)
    def run(self):
        try:
            if self.mode=='no_read':self.stop.wait(4);return
            hello=self.receive();self.hello_seen.set();q=hello['record'];capture=hello['capture_id']
            request_ref=reference(q,'records/request.json');request_ref['digest']['value']=hello['request_sha256']
            ready={'record_kind':'launch','schema_version':q['schema_version'],'record_context':q['record_context'],'record_id':capture+'-observer-0','disclosure':{'mode':'full','withheld':[],'origin_token':None},'variant':'event','request':request_ref,'run_id':q['run_id'],'producer':'observer','sequence':0,'previous':None,'event':'observer_ready','clock_id':capture,'elapsed_ns':0,'process':None,'status':'passed','covers':[],'ready_ack':None,'completed_exits':[]}
            packet={**hello,'record':ready}
            if self.mode in ('silent','cancel_before'):self.stop.wait(4);return
            if self.mode=='disconnect':return
            if self.mode in ('partial_header','partial_body','partial_header_eof','partial_body_eof','drip','zero','oversize','malformed'):
                body=encoded(packet);frame=struct.pack('!I',len(body))+body
                if self.mode in ('partial_header','partial_header_eof'):self.server.sendall(frame[:2])
                if self.mode in ('partial_body','partial_body_eof'):self.server.sendall(frame[:20])
                if self.mode.endswith('_eof'):return
                if self.mode=='zero':self.server.sendall(b'\0\0\0\0')
                if self.mode=='oversize':self.server.sendall(struct.pack('!I',262145))
                if self.mode=='malformed':self.server.sendall(struct.pack('!I',1)+b'{')
                if self.mode=='drip':
                    for byte in frame[:8]:self.server.sendall(bytes([byte]));self.stop.wait(.4)
                self.stop.wait(3);return
            if self.mode=='wrong_hash':packet['request_sha256']='0'*64
            if self.mode=='stale_capture':packet['capture_id']='old-capture'
            if self.mode=='wrong_run':ready['run_id']='old-run'
            if self.mode=='wrong_sequence':ready['sequence']=1
            if self.mode=='hold_ready':self.release_ready.wait(1.2)
            self.send(packet);self.events.append(ready);self.ready_sent.set()
            if self.mode=='after_ready_no_read':self.stop.wait(4);return
            if self.mode=='after_ready_partial':self.server.sendall(b'\0\0');self.stop.wait(4);return
            if self.mode=='after_ready_disconnect':
                deadline=time.monotonic()+2
                while not (self.work/'state/prefix/child.json').exists() and time.monotonic()<deadline:self.stop.wait(.005)
                return
            while not self.stop.is_set():
                packet=self.receive();event=packet['record'];self.events.append(event)
                if event['event']=='exited':
                    complete={**ready,'record_id':capture+'-observer-1','sequence':1,'previous':reference(ready,'observer/0.json'),'event':'observer_complete','elapsed_ns':event['elapsed_ns']+1,'covers':[event['process']['token']],'completed_exits':[reference(event,'supervisor/1.json')]}
                    if self.mode=='detached_helper':
                        trace=json.loads((self.work/'state/prefix/detached.json').read_bytes())
                        if trace['pgid']==event['process']['pid']:raise AssertionError('helper did not detach')
                        complete.update(status='unsupported')
                    if self.mode=='gap':complete.update(event='gap',status='failed',covers=[],completed_exits=[])
                    if self.mode=='wrong_completion':complete['completed_exits']=[]
                    self.send({**hello,'record':complete});self.events.append(complete);self.stop.wait(.1);return
        except (EOFError,BrokenPipeError,ConnectionResetError):pass
        except BaseException as error:
            if not self.stop.is_set():self.error=type(error).__name__
        finally:
            try:self.server.shutdown(socket.SHUT_RDWR)
            except OSError:pass
