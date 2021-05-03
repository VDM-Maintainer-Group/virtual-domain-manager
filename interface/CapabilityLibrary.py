#!/usr/bin/env python3
import random, time, string
import os, re, socket, struct
import json, base64
from enum import Enum
from functools import wraps
from multiprocessing import (Process, Value, Queue)
from multiprocessing.shared_memory import SharedMemory
from typing import Any

SHM_REQ_MAX_SIZE = 10*1024   #10KB
SHM_RES_MAX_SIZE = 1024*1024 #1MB
VDM_SERVER_PORT = 42000
VDM_CLIENT_ID_LEN = 16
GET_RANDOM_ID = lambda: ''.join( random.choices(string.hexdigits, k=VDM_CLIENT_ID_LEN) )

class __COMMAND(Enum): #2-byte
    ALIVE       = 0x00
    REGISTER    = 0x01
    UNREGISTER  = 0x02
    CALL        = 0x03
    ONE_WAY     = 0x04
    CHAIN_CALL  = 0x05
    pass

class __STATUS(Enum): #1-byte
    #loop operation is lockless safe
    SERVER_ON   = 0b0001
    SERVER_DONE = 0b0000
    CLIENT_ON   = 0b0010
    CLIENT_DONE = 0b0011
    pass

class AnyType(str):
    def __new__(cls, value, sig_func_args_table):
        _regex = re.compile('restype_(.*?)_(.*)')
        _tmp = _regex.split(value)
        if len(_tmp)==4:
            obj = str.__new__(cls, value)
            obj.sig, obj.func = _tmp[1], _tmp[2]
            obj.table = sig_func_args_table
            return obj
        else:
            raise Exception('Invalid value for AnyType')
    pass

def __validate(_type, x) -> bool:
    _map = {
        'Null':   lambda x:x is None,
        'Bool':   lambda x:isinstance(x, bool),
        'Number': lambda x:isinstance(x, int) or isinstance(float),
        'String': lambda x:isinstance(x, str) or isinstance(bytes),
        'Array':  lambda x:isinstance(x, list),
        'Object': lambda x:isinstance(x, dict)
    }
    _regex = re.compile('\<(.*)\>')
    #
    _nested = _regex.search(_type)
    if isinstance(x, AnyType): #only for top-level type
        return True
    else:
        if len(_nested)==3:
            if _nested[0]=='Array' and _map[_type](x):
                return __validate(_nested[1], x[0])
            elif _nested[0]=='Object' and _map[_type](x):
                key_type, val_type = _nested[1].replace(' ','').split(',')
                return key_type=='String' and __validate(key_type, x.keys()[0]) and __validate(val_type, x.values()[0])
            else:
                return False
        else:
            return _map[_type](x)
    pass

class ShmManager:
    def __init__(self, _id) -> None:
        self.id = _id
        self.shm_req = None
        self.shm_res = SharedMemory(create=True, size=SHM_RES_MAX_SIZE)
        self.shm_res.buf[0] = __STATUS.CLIENT_DONE
        pass

    def send(self, q_in: Queue, shm_req: SharedMemory, seq: Value) -> None:
        #req_header: ['status':1B, 'seq':4B, 'command':2B, 'size':2B]
        req_header = struct.Struct('1B4B2B2B')
        while True:
            command, data = q_in.get()
            data = bytearray( data.encode() )
            with seq.get_lock():
                seq.value += 1
            buffer = req_header.pack(__STATUS.CLIENT_ON, seq.value, command, len(data))
            buffer += data
            #
            while shm_req.buf[0]!=__STATUS.SERVER_DONE:
                time.sleep(0) #actual using select
            shm_req.buf[0] = __STATUS.CLIENT_ON   #assert: atomic operation
            shm_req.buf[:len(buffer)] = buffer
            shm_req.buf[0] = __STATUS.CLIENT_DONE #assert: atomic operation
        pass

    def recv(self, q_out: Queue, shm_res: SharedMemory) -> None:
        #res_header: ['status':1B, 'seq':4B, 'size':3B]
        res_header = struct.Struct('1B4B3B')
        res_header_len = len(res_header)
        while True:
            while shm_res.buf[0]!=__STATUS.SERVER_DONE:
                time.sleep(0) #actual using select
            shm_res.buf[0] = __STATUS.CLIENT_ON   #assert: atomic operation
            _, seq, _size = res_header.unpack( shm_res.buf[:res_header_len] )
            buffer = shm_res.buf[res_header_len:res_header_len+_size].copy()
            shm_res.buf[0] = __STATUS.CLIENT_DONE #assert: atomic operation
            #
            data = bytes(buffer).decode()
            q_out.put( (seq, data) )
        pass

    def start(self) -> None:
        self.shm_req = SharedMemory(name=self.id)
        assert(self.shm_req.buf[0] == __STATUS.SERVER_DONE)
        #
        self.responses = dict()
        self.seq = Value('L', 0) #unsigned long, 4B
        self.q_in, self.q_out = Queue(), Queue()
        self.send_process = Process(target=self.send, args=(self.q_in, self.shm_req, self.seq), daemon=True)
        self.recv_process = Process(target=self.recv, args=(self.q_out, self.shm_req), daemon=True)
        self.send_process.start()
        self.recv_process.start()
        pass

    def close(self) -> None:
        try:
            self.send_process.close()
            self.recv_process.close()
        except:
            pass
        finally:
            self.q_in = None
            self.q_out = None
            self.responses = None
        #
        try:
            self.shm_res.close()
            self.shm_res.unlink()
        except:
            pass
        #
        if self.shm_req is not None:
            try:
                self.shm_req.close()
                self.shm_req.unlink()
                self.shm_req = None
            except:
                pass
        pass

    def sync_response(self) -> None:
        res = self.q_out.get_nowait()
        while res is not None:
            seq, data = res
            self.responses.update( {seq:data} )
            res = self.q_out.get_nowait()
        pass

    def get_response_async(self, seq):
        self.sync_response()
        data = self.responses.pop(seq, None)
        if data is not None:
            return json.loads( data )
        return 

    def get_response(self, seq, timeout=-1):
        _start_time = time.time()
        _ddl = _start_time + timeout if timeout>=0 else 1E3
        #
        res = None
        while res is None:
            res = self.get_response_async(seq)
            if time.time() > _ddl:
                break
        return res

    def request_async(self, command, *args, **kwargs) -> int:
        request_format = {
            __COMMAND.ALIVE:        lambda :(__COMMAND.ALIVE, ''),
            __COMMAND.REGISTER:     lambda name:(__COMMAND.REGISTER, 
                json.dumps({'name': name})
            ),
            __COMMAND.UNREGISTER:   lambda name:(__COMMAND.UNREGISTER,
                json.dumps({'name': name})
            ),
            __COMMAND.CALL:         lambda sig, func, args:(__COMMAND.CALL,
                json.dumps({'sig':sig, 'func':func, 'args':args})
            ),
            __COMMAND.ONE_WAY:      lambda sig, func, args:(__COMMAND.ONE_WAY,
                json.dumps({'sig':sig, 'func':func, 'args':args})
            ),
            __COMMAND.CHAIN_CALL:   lambda sig_func_args_table:(__COMMAND.CHAIN_CALL,
                json.dumps({'sig_func_args_table':sig_func_args_table})
            )
        }
        with self.seq.get_lock():
            _seq = self.seq.value + 1
        self.q_in.put( request_format[command](*args, **kwargs) )
        return _seq

    def request(self, command, *args, **kwargs):
        _seq = self.request_async(command, *args, **kwargs)
        
        if command==__COMMAND.ONE_WAY or command==__COMMAND.UNREGISTER:
            return None
        if 'timeout' in kwargs:
            return self.get_response(_seq, timeout=kwargs['timeout'])
        else:
            return self.get_response(_seq, timeout=-1)

    def is_alive(self) -> bool:
        _proc_alive = self.send_process.is_alive() and self.recv_process.is_alive()
        if not _proc_alive:
            return False
        #
        _start = time.time()
        res = self.request(__COMMAND.ALIVE, timeout=5)
        if res==None:
            return False
        else:
            return True
        pass

    pass

class CapabilityHandle:
    def __init__(self, server: ShmManager, name, mode) -> None:
        res = server.request(__COMMAND.REGISTER, name, mode)
        if 'sig' not in res:
            raise Exception('Invalid Capability.')
        #
        self._server = server
        self._mode = mode
        self._sig = res['sig']
        self._spec = res['spec']
        #
        self._sig_func_args_table = None #for lazy response
        pass

    def __getattribute__(self, name: str):
        _spec = super().__getattribute__('_spec')
        if name in _spec.keys():
            args_spec = _spec[name]['args']
            #
            # return a wrapper:
            #   - wrap request method
            @wraps(name)
            def _wrapper(*args, **kwargs):
                _sig_func_args_table = list()
                # check spec validation with *args and **kwargs
                for i,x in enumerate(args_spec):
                    #
                    _name, _type = x.keys()[0], x.values()[0]
                    if i < len(args):
                        _arg = args[i]
                    elif _name in kwargs:
                        _arg = kwargs[_name]
                    else:
                        raise Exception('Input arguments missing.')
                    #
                    if __validate(_type, _arg):
                        args_spec[i][_name] = _arg
                        if isinstance(_arg, AnyType):
                            _sig_func_args_table.extend(_arg.table)
                    else:
                        raise Exception('Input type mismatch: "%r" for type "%s".'%(_arg, _type))
                    pass
                _sig_func_args_table.extend( [self._sig, name, args_spec] )
                # wrap request method, async or not
                if len(_sig_func_args_table) > 0 or self._mode=='async':
                    self._sig_func_args_table = _sig_func_args_table
                    res = None
                elif self._mode=='one-way':
                    res = self._server.request(__COMMAND.ONE_WAY, *_sig_func_args_table[0])
                else:
                    res = self._server.request(__COMMAND.CALL, *_sig_func_args_table[0])
                return res
            return _wrapper
        else:
            return super().__getattribute__(name)
        pass

    def execute(self, blocking=True): #not support non-blocking now
        if self._sig_func_args_table is not None:
            if len(self._sig_func_args_table) > 0:
                res = self._server.request(__COMMAND.CHAIN_CALL, self._sig_func_args_table)
            else:
                res = self._server.request(__COMMAND.CALL, *self._sig_func_args_table[0])
            self._sig_func_args_table = None
            return res
        else:
            raise Exception('No available function call table.')
        pass

    def drop(self):
        if len(self._spec):
            self._server.request(__COMMAND.UNREGISTER, self._spec['name'])
        del self._spec
        self._spec = dict()
        self._sig = None
        pass

    pass

class CapabilityLibrary:
    def __init__(self, remote='') -> None:
        if remote:
            raise Exception('Not support remote connection now.')
        random.seed( time.time() )
        self.__id = GET_RANDOM_ID()
        self.__server = None
        self.capability = dict()
        pass

    def connect(self) -> None:
        if self.__server and self.__server.is_alive():
            return
        #
        _addr = ('', VDM_SERVER_PORT)
        _sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        __server = ShmManager(self.__id)
        try:
            _sock.connect(_addr)
            _sock.sendall(self.__id)
            _tmp = _sock.recv(VDM_CLIENT_ID_LEN+1) #+1 for '\0'
            if _tmp==self.__id:
                self.__server = __server
                self.__server.start()
            else:
                raise Exception('Invalid Connection: %s'%_tmp)
        except Exception as e:
            __server.close()
            _sock.close()
            raise e
        pass

    def disconnect(self) -> None:
        if self.__server is None:
            return
        if not self.__server.is_alive():
            return
        #
        for _item in self.capability.values():
            _item.drop()
        #
        try:
            self.__server.close()
        except:
            print('broken pipe, closed anyway.')
        pass

    def getCapability(self, name:str, mode=None) -> CapabilityHandle:
        if name in self.capability.keys():
            return self.capability[name]
        #
        try:
            assert(mode in [None, 'one-way', 'async'])
            _item = CapabilityHandle(self.__server, name, mode)
        except:
            return None
        else:
            self.capability.update( {name:_item} )
            return _item
        pass

    pass
