#!/usr/bin/env python3
import random, time, string
import os, re, socket, struct, signal
import json, base64
from enum import Enum
from functools import wraps
from multiprocessing import (Process, Value, Queue)
from multiprocessing.shared_memory import SharedMemory
from posix_ipc import (Semaphore, O_CREX)

SHM_REQ_MAX_SIZE = 10*1024   #10KB
SHM_RES_MAX_SIZE = 1024*1024 #1MB
VDM_SERVER_PORT = 42000
VDM_CLIENT_ID_LEN = 16
GET_RANDOM_ID = lambda: ''.join( random.choices(string.hexdigits, k=VDM_CLIENT_ID_LEN) )

class _COMMAND(Enum): #2-byte
    ALIVE       = 0x00
    REGISTER    = 0x01
    UNREGISTER  = 0x02
    CALL        = 0x03
    ONE_WAY     = 0x04
    CHAIN_CALL  = 0x05
    pass

class AnyType(str):
    def __new__(cls, value, restype, sig_func_args_table):
        _regex = re.compile('restype_(.*?)_(.*)')
        _tmp = _regex.split(value)
        if len(_tmp)==4:
            obj = str.__new__(cls, value)
            obj.sig, obj.func = _tmp[1], _tmp[2]
            obj.restype = restype
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
        return (_type==x.restype)
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
        self.req_id = _id+'_req'
        self.res_id = _id+'_res'
        #
        self.shm_req = SharedMemory(name=self.req_id, create=True, size=SHM_REQ_MAX_SIZE)
        self.sem_req = Semaphore('/'+self.req_id, flags=O_CREX, initial_value=1)
        self.shm_res = None
        self.sem_res = None
        pass

    def send(self, q_in: Queue, shm_req: SharedMemory, sem_req: Semaphore, seq: Value) -> None:
        #req_header: ['seq':4B, 'command':2B, 'size':2B]
        req_header = struct.Struct('4B2B2B')
        try:
            signal.signal(signal.SIGTERM, lambda: (_ for _ in ()).throw(Exception()) )
            signal.signal(signal.SIGKILL, lambda: (_ for _ in ()).throw(Exception()) )
            while True:
                with sem_req as sm: #acquire lock until data is ready (to send)
                    command, data = q_in.get(timeout=15)
                    data = bytearray( data.encode() )
                    with seq.get_lock(): #read
                        buffer = req_header.pack(seq.value, command, len(data))
                        buffer += data
                    shm_req.buf[:len(buffer)] = buffer
                    pass
                time.sleep(0) #transfer to other process
        except:
            self.close()
        pass

    def recv(self, q_out: Queue, shm_res: SharedMemory, sem_res: Semaphore) -> None:
        #res_header: ['seq':4B, 'size':4B]
        res_header = struct.Struct('4B4B')
        res_header_len = len(res_header)
        try:
            signal.signal(signal.SIGTERM, lambda: (_ for _ in ()).throw(Exception()) )
            signal.signal(signal.SIGKILL, lambda: (_ for _ in ()).throw(Exception()) )
            while True:
                with sem_res as sm: #get lock once data is ready (to recv)
                    seq, _size = res_header.unpack( shm_res.buf[:res_header_len] )
                    buffer = shm_res.buf[res_header_len:res_header_len+_size].copy()
                #
                data = bytes(buffer).decode()
                q_out.put( (seq, data) )
        except:
            self.close()
        pass

    def start(self) -> None:
        self.shm_res = SharedMemory(name=self.res_id)
        self.sem_res = Semaphore(name='/'+self.res_id)
        #
        self.responses = dict()
        self.seq = Value('L', 0) #unsigned long, 4B
        self.q_in, self.q_out = Queue(), Queue()
        self.send_process = Process(target=self.send, args=(self.q_in, self.shm_req, self.sem_req, self.seq), daemon=True)
        self.recv_process = Process(target=self.recv, args=(self.q_out, self.shm_res, self.sem_res), daemon=True)
        self.send_process.start()
        self.recv_process.start()
        time.sleep(0.1) #promise "send" process starts
        pass

    def close(self) -> None:
        # stop the processes
        try:
            self.send_process.close()
            self.recv_process.close()
        except:
            pass
        finally:
            self.q_in = None
            self.q_out = None
            self.responses = None
        # shm_res: close and unlink
        try:
            self.shm_res.close()
            self.shm_res.unlink()
        except:
            pass
        # sem_res: close and unlink
        try:
            self.sem_res.close()
            self.sem_res.unlink()
        except:
            pass
        # shm_req: close and unlink
        if self.shm_req is not None:
            try:
                self.shm_req.close()
                self.shm_req.unlink()
                self.shm_req = None
            except:
                pass
        # sen_req: close and unlink
        if self.sem_req is not None:
            try:
                self.sem_req.close()
                self.sem_req.unlink()
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

    def request_async(self, command: _COMMAND, *args, **kwargs) -> int:
        request_format = {
            _COMMAND.ALIVE:        lambda :(_COMMAND.ALIVE, ''),
            _COMMAND.REGISTER:     lambda name:(_COMMAND.REGISTER, 
                json.dumps({'name': name})
            ),
            _COMMAND.UNREGISTER:   lambda name:(_COMMAND.UNREGISTER,
                json.dumps({'name': name})
            ),
            _COMMAND.CALL:         lambda sig, func, args:(_COMMAND.CALL,
                json.dumps({'sig':sig, 'func':func, 'args':args})
            ),
            _COMMAND.ONE_WAY:      lambda sig, func, args:(_COMMAND.ONE_WAY,
                json.dumps({'sig':sig, 'func':func, 'args':args})
            ),
            _COMMAND.CHAIN_CALL:   lambda sig_func_args_table:(_COMMAND.CHAIN_CALL,
                json.dumps({'sig_func_args_table':sig_func_args_table})
            )
        }
        with self.seq.get_lock(): #read-and-write
            _seq = self.seq.value + 1
            self.seq.value = _seq
        self.q_in.put( request_format[command](*args, **kwargs) )
        return _seq

    def request(self, command: _COMMAND, *args, **kwargs):
        _seq = self.request_async(command, *args, **kwargs)
        
        if command==_COMMAND.ONE_WAY or command==_COMMAND.UNREGISTER:
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
        res = self.request(_COMMAND.ALIVE, timeout=5)
        if res==None:
            return False
        else:
            return True
        pass

    pass

class CapabilityHandle:
    def __init__(self, server: ShmManager, name, mode) -> None:
        res = server.request(_COMMAND.REGISTER, name)
        if 'sig' not in res:
            raise Exception('Invalid Capability.')
        #
        self._server = server
        self.mode = mode
        self._sig = res['sig']
        self._spec = res['spec']
        #
        self._sig_func_args_table = None #for lazy response
        pass

    def __getattribute__(self, name: str):
        _spec = super().__getattribute__('_spec')
        _mode = super().__getattribute__('mode')
        if name in _spec.keys():
            args_spec = _spec[name]['args']
            _restype  = _spec[name]['restype']

            @wraps(name)
            def _wrapper(*args, **kwargs):
                _sig_func_args_table = list()
                # check spec validation with *args and **kwargs
                for i,x in enumerate(args_spec):
                    _name, _type = x.keys()[0], x.values()[0]
                    if i < len(args):
                        _arg = args[i]
                    elif _name in kwargs:
                        _arg = kwargs[_name]
                    else:
                        raise Exception('Input argument missing: %s.'%_name)
                    #
                    if __validate(_type, _arg):
                        args_spec[i][_name] = _arg
                        if isinstance(_arg, AnyType):
                            _sig_func_args_table.extend(_arg.table)
                    else:
                        raise Exception('Input type mismatch: "%r" for type "%s".'%(_arg, _type))
                    pass
                _sig_func_args_table.extend( [self._sig, name, args_spec] )
                # wrap request method, lazy or not
                if len(_sig_func_args_table) > 0 or _mode=='lazy':
                    self._sig_func_args_table = _sig_func_args_table
                    res = AnyType( 'restype_%s_%s'%(self._sig, name), _restype, _sig_func_args_table )
                elif _mode=='one-way':
                    res = self._server.request(_COMMAND.ONE_WAY, *_sig_func_args_table[0])
                else:
                    res = self._server.request(_COMMAND.CALL, *_sig_func_args_table[0])
                return res
            
            return _wrapper
        else:
            return super().__getattribute__(name)
        pass

    def execute(self, blocking=True): #not support non-blocking now
        if self._sig_func_args_table is not None:
            _request_method = self._server.request if blocking else self._server.request_async
            if len(self._sig_func_args_table) > 0:
                res = _request_method(_COMMAND.CHAIN_CALL, self._sig_func_args_table)
            else:
                res = _request_method(_COMMAND.CALL, *self._sig_func_args_table[0])
            self._sig_func_args_table = None
            return res
        else:
            raise Exception('No available function call table.')
        pass

    def drop(self):
        if len(self._spec):
            self._server.request(_COMMAND.UNREGISTER, self._spec['name'])
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
            # handshake-I
            _sock.connect(_addr)
            _sock.sendall(self.__id)
            # handshake-II
            _tmp = _sock.recv(VDM_CLIENT_ID_LEN+1) #+1 for '\0'
            if _tmp==self.__id:
                self.__server = __server
                self.__server.start()
            else:
                raise Exception('Invalid Connection: %s'%_tmp)
            # handshake-III
            _sock.sendall(self.__id)
        except Exception as e:
            __server.close()
            raise e
        finally:
            _sock.close()
        pass

    def disconnect(self) -> None:
        if self.__server is None:
            return
        if not self.__server.is_alive(): #abnormal server exit
            self.__server.close()
            return
        #
        for _item in self.capability.values():
            _item.drop()
        self.__server.close()
        pass

    def getCapability(self, name:str, mode=None) -> CapabilityHandle:
        if name in self.capability.keys():
            return self.capability[name]
        #
        try:
            assert(mode in [None, 'one-way', 'lazy'])
            _item = CapabilityHandle(self.__server, name, mode)
        except:
            return None
        else:
            self.capability.update( {name:_item} )
            return _item
        pass

    pass

class CapabilityContext:
    def __init__(self, name=None, remote=''):
        self.lib = CapabilityLibrary(remote)
        self.name = name
        pass

    def __enter__(self):
        self.lib.connect()
        if self.name:
            self.capability = self.lib.getCapability(self.name)
            return self.capability
        else:
            return self.lib

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.name:
            self.capability.drop()
        self.lib.disconnect()
        pass
    pass
