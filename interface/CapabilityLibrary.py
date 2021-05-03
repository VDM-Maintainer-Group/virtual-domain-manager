#!/usr/bin/env python3
import random, time, string
import os, socket, struct
import json, base64
from enum import Enum
from functools import wraps
from multiprocessing import (Process, Value, Queue)
from multiprocessing.shared_memory import SharedMemory

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
        return self.responses(seq, None)

    def get_response(self, seq, timeout=-1):
        _start_time = time.time()
        _ddl = _start_time + timeout if timeout>=0 else 1E3
        #
        while seq not in self.responses:
            self.sync_response()
            if time.time() > _ddl:
                break
        return self.responses.pop(seq, None)

    def request_async(self, command, *args, **kwargs) -> int:
        request_format = {
            __COMMAND.ALIVE:        lambda :(__COMMAND.ALIVE, ''),
            __COMMAND.REGISTER:     lambda name:(__COMMAND.REGISTER, 
                json.dumps({'name': name})
            ),
            __COMMAND.UNREGISTER:   lambda name:(__COMMAND.UNREGISTER,
                json.dumps({'name': name})
            ),
            __COMMAND.CALL:         lambda capability, func, args:(__COMMAND.CALL,
                json.dumps({'capability':capability, 'func':func, 'args':args})
            ),
            __COMMAND.ONE_WAY:      lambda capability, func, args:(__COMMAND.ONE_WAY,
                json.dumps({'capability':capability, 'func':func, 'args':args})
            ),
            __COMMAND.CHAIN_CALL:   lambda capability_func_list, args_list:(__COMMAND.CHAIN_CALL,
                json.dumps({'capability_func_list':capability_func_list, 'args_list':args_list})
            )
        }
        with self.seq.get_lock():
            _seq = self.seq.value + 1
        self.q_in.put( request_format[command](*args, **kwargs) )
        return _seq

    def request(self, command, *args, **kwargs):
        _seq = self.request_async(command, *args, **kwargs)
        if 'timeout' in kwargs:
            self.get_response(_seq, timeout=kwargs['timeout'])
        else:
            self.get_response(_seq, timeout=-1)
        pass

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
    def __init__(self, server: ShmManager, name) -> None:
        spec = server.request(__COMMAND.REGISTER, name)
        if spec is None:
            raise Exception('Invalid Capability.')
        #
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
                pass
            return _wrapper
        else:
            return super().__getattribute__(name)
        pass

    def drop(self):
        if len(self.spec):
            self.server.request(__COMMAND.UNREGISTER, self.spec['name'])
        del self.spec
        self.spec = dict()
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

    def getCapability(self, name:str) -> CapabilityHandle:
        if name in self.capability.keys():
            return self.capability[name]
        #
        try:
            _item = CapabilityHandle(self.__server, name)
        except:
            return None
        else:
            self.capability.update( {name:_item} )
            return _item
        pass

    pass
