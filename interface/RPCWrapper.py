#!/usr/bin/env python3
import random, time, string
import os, socket, struct
import json, base64
import asyncio
from functools import wraps

COMMAND_REGISTER    = 'register'
COMMAND_UNREGISTER  = 'unregister'
COMMAND_CALL        = 'call'

VDM_SERVER_PORT = 42000
VDM_CLIENT_ID_LEN = 32
GET_RANDOM_ID = lambda: ''.join( random.choices(string.hexdigits, k=VDM_CLIENT_ID_LEN) )

class RPCRequestWrapper:
    template = struct.Struct('IB1024B') #{Seq:u32, subSeq:u8, data:[u8;1024]}

    def __init__(self, raw_handle, raw_send, raw_recv):
        self.seq = 0
        self.raw_handle = raw_handle
        self.raw_send = raw_send
        self.raw_recv = raw_recv
        pass

    def pack(self, raw_data):
        pass #return list of packages

    async def send(self, data):
        pass

    async def recv(self, seq):
        pass

    def request(self, command, *args):
        if command==COMMAND_REGISTER:
            pass
        elif command==COMMAND_UNREGISTER:
            pass
        elif command==COMMAND_CALL:
            pass
        else:
            pass
        pass

    def close(self):
        self.raw_handle.close()
        pass

    pass

class CapabilityHandle:
    def __init__(self, server: RPCRequestWrapper, spec):
        self.server = server
        self.spec = spec
        pass

    def __getattribute__(self, name: str):
        _spec = super().__getattribute__('spec')
        if name in _spec.keys():
            # return a wrapper:
            #   - check spec validation
            #   - validate *args and **kargs
            #   - wrap request method
            @wraps(name)
            def _wrapper(*args, **kargs):
                #TODO:
                pass
            return _wrapper
        else:
            return super().__getattribute__(name)
        pass

    def drop(self):
        if len(self.spec):
            self.server.request(COMMAND_UNREGISTER)
        del self.spec
        self.spec = dict()
        pass

    pass

class RPCWrapper:
    def __init__(self, remote_addr=''):
        if remote_addr:
            self.remote_addr = remote_addr
            self.type = 'rpc'
        else:
            self.remote_addr = ''
            self.type = 'pipe'
        #
        random.seed( time.time() )
        self.id = GET_RANDOM_ID()
        self.server = None
        self.capability = dict()
        pass

    #Reference: https://www.eadan.net/blog/ipc-with-named-pipes/
    def connect(self):
        _addr = (self.remote_addr, VDM_SERVER_PORT)
        _sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _sock.connect(_addr)
        _sock.sendall(self.id)
        try:
            _tmp = _sock.recv(VDM_CLIENT_ID_LEN+1) #+1 for '\0'
            if _tmp==self.id:
                if self.type=='rpc':
                    raw_send = lambda data:_sock.sendall(data)
                    raw_recv = lambda buff_len:_sock.recv(buff_len)
                    self.server = RPCRequestWrapper(_sock, raw_send, raw_recv)
                elif self.type=='pipe': #FIXME: for elegant impl.
                    _pipe = os.mkfifo(self.id)
                    raw_send = lambda data: _pipe.write(data)
                    raw_recv = lambda buff_len: _pipe.read(buff_len)
                    self.server = RPCRequestWrapper(_pipe, raw_send, raw_recv)
                    _sock.close()
                else:
                    _sock.close()
                    raise Exception( 'Unsupported RPC type: %s'%self.type )
            else:
                raise Exception('Invalid Connection: %s'%_tmp)
        except Exception as e:
            raise e
        pass

    def disconnect(self):
        try:
            for _item in self.capability.values():
                _item.drop()
                pass
            self.server.close()
        except Exception as e:
            print('broken pipe, closed anyway.')
        pass

    def getCapability(self, name):
        if name in self.capability.keys():
            return self.capability['name']
        #
        spec = self.server.request(COMMAND_REGISTER, 'name')
        if spec is None:
            return None
        else:
            _item = CapabilityHandle(self.server, spec)
            self.capability.update( {name:_item} )
            return _item
        pass

    pass
