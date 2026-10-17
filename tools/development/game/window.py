# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: MIT
"""Read owned window metadata and post bounded events to that exact process only."""
import ctypes,plistlib
from pear_runtime.fixtures.inputs import need
from tools.development.game.capture_policy import eligible
class Point(ctypes.Structure):_fields_=[('x',ctypes.c_double),('y',ctypes.c_double)]
class Windows:
    def __init__(self):
        self.cg=ctypes.CDLL('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics');self.cf=ctypes.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
        signatures={
          'CGWindowListCopyWindowInfo':([ctypes.c_uint32,ctypes.c_uint32],ctypes.c_void_p),
          'CGPreflightScreenCaptureAccess':([],ctypes.c_bool),
          'CGPreflightPostEventAccess':([],ctypes.c_bool),
          'CGEventCreateMouseEvent':([ctypes.c_void_p,ctypes.c_uint32,Point,ctypes.c_uint32],ctypes.c_void_p),
          'CGEventCreateKeyboardEvent':([ctypes.c_void_p,ctypes.c_uint16,ctypes.c_bool],ctypes.c_void_p),
          'CGEventPostToPid':([ctypes.c_int,ctypes.c_void_p],None)}
        for name,(args,result) in signatures.items():
            fn=getattr(self.cg,name);fn.argtypes=args;fn.restype=result
        self.cf.CFPropertyListCreateData.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_long,ctypes.c_ulong,ctypes.POINTER(ctypes.c_void_p)];self.cf.CFPropertyListCreateData.restype=ctypes.c_void_p
        self.cf.CFDataGetLength.argtypes=[ctypes.c_void_p];self.cf.CFDataGetLength.restype=ctypes.c_long
        self.cf.CFDataGetBytePtr.argtypes=[ctypes.c_void_p];self.cf.CFDataGetBytePtr.restype=ctypes.c_void_p
        self.cf.CFRelease.argtypes=[ctypes.c_void_p]
    def rows(self,pid):
        array=self.cg.CGWindowListCopyWindowInfo(16,0);need(array,'play_window_list')
        error=ctypes.c_void_p();data=None
        try:
            data=self.cf.CFPropertyListCreateData(None,array,100,0,ctypes.byref(error));need(data,'play_window_serialization')
            size=self.cf.CFDataGetLength(data);need(0<size<8*1024**2,'play_window_metadata_limit')
            rows=plistlib.loads(ctypes.string_at(self.cf.CFDataGetBytePtr(data),size))
            return [r for r in rows if eligible(r,pid)]
        finally:
            if data:self.cf.CFRelease(data)
            if error.value:self.cf.CFRelease(error)
            self.cf.CFRelease(array)
    def exact(self,pid,window_id):
        rows=[r for r in self.rows(pid) if r['kCGWindowNumber']==window_id];need(len(rows)==1,'play_window_changed');return rows[0]
    def post(self,pid,event):
        need(event,'play_input_event')
        try:
            need(self.cg.CGPreflightPostEventAccess(),'play_input_permission_unavailable')
            self.cg.CGEventPostToPid(pid,event)
        finally:self.cf.CFRelease(event)
    def click(self,pid,row,x,y):
        need(type(x) is int and type(y) is int and 0<=x<=1000 and 0<=y<=1000,'play_click_position')
        b=row['kCGWindowBounds'];point=Point(b['X']+b['Width']*x/1000,b['Y']+b['Height']*y/1000)
        for kind in (1,2):self.post(pid,self.cg.CGEventCreateMouseEvent(None,kind,point,0))
    def key(self,pid,key,down):
        need(key in ('w','a','s','d','space','escape'),'play_key_scope')
        code={'w':13,'a':0,'s':1,'d':2,'space':49,'escape':53}[key]
        self.post(pid,self.cg.CGEventCreateKeyboardEvent(None,code,down))
