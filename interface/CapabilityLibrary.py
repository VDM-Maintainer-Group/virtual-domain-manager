#!/usr/bin/env python3
import random, time, string
import os, sys, re, socket, struct, signal, mmap, copy
import json, base64
from enum import IntEnum
from functools import wraps
from multiprocessing import (Process, Value, Queue)
from posix_ipc import (SharedMemory, Semaphore, O_CREX, unlink_semaphore, unlink_shared_memory)

SHM_REQ_MAX_SIZE = 10*1024   #10KB
SHM_RES_MAX_SIZE = 1024*1024 #1MB
VDM_SERVER_PORT = 42000
VDM_CLIENT_ID_LEN = 16
GET_RANDOM_ID = lambda: ''.join( random.choices(string.hexdigits, k=VDM_CLIENT_ID_LEN) )

class _COMMAND(IntEnum): #2-byte
    ALIVE       = 0x00
    REGISTER    = 0x01
    UNREGISTER  = 0x02
    CALL        = 0x03
    ONE_WAY     = 0x04
    CHAIN_CALL  = 0x05
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

set_mask   = lambda x: x | 0x80
unset_mask = lambda x: x & 0x7F
test_mark  = lambda x: not (x & 0x80 == 0)

class ShmContext:
    def __init__(self, sem, shm, write:bool) -> None:
        self.write_flag = write
        self.sem = sem
        self.shm = shm
        pass

    def __enter__(self):
        shm_buf = mmap.mmap(self.shm.fd, self.shm.size)
        while True:
            self.sem.acquire()
            if test_mark(shm_buf[3])==self.write_flag:
                self.sem.release()
                time.sleep(0)
                continue
            break
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        shm_buf = mmap.mmap(self.shm.fd, self.shm.size)
        if self.write_flag:
            shm_buf[3] = set_mask(shm_buf[3])
        else:
            shm_buf[3] = unset_mask(shm_buf[3])
        self.sem.release()
        pass
    pass

class ShmManager:
    def __init__(self, _id) -> None:
        self.req_id = _id+'_req'
        self.res_id = _id+'_res'
        #
        self.shm_req = SharedMemory(self.req_id, flags=O_CREX, size=SHM_REQ_MAX_SIZE)
        self.sem_req = Semaphore(self.req_id, flags=O_CREX, initial_value=0)
        self.shm_res = None
        self.sem_res = None
        pass

    def send(self, q_in: Queue, shm_req: SharedMemory, sem_req: Semaphore, seq: Value) -> None:
        #req_header: ['seq':4B/I, 'command':2B/H, 'size':2B/H]
        req_header = struct.Struct('IHH')
        shm_buf = mmap.mmap(shm_req.fd, shm_req.size)
        try:
            sem_req.release() #ready to write
            while True:
                with ShmContext(sem_req, shm_req, write=True): #acquire lock until data is ready (to send)
                    command, data = q_in.get(timeout=5)
                    data = bytearray( data.encode() )
                    with seq.get_lock(): #read
                        buffer = req_header.pack(seq.value, command, len(data))
                        buffer += data
                    shm_buf[:len(buffer)] = buffer
                pass
        except Exception as e:
            self.close()
            raise e
        pass

    def recv(self, q_out: Queue, shm_res: SharedMemory, sem_res: Semaphore) -> None:
        #res_header: ['seq':4B/I, 'size':4B/I]
        res_header = struct.Struct('II')
        res_header_len = res_header.size
        shm_buf = mmap.mmap(shm_res.fd, shm_res.size)
        try:
            while True:
                with ShmContext(sem_res, shm_res, write=False): #get lock once data is ready (to recv)
                    seq, _size = res_header.unpack( shm_buf[:res_header_len] )
                    buffer = copy.copy( shm_buf[res_header_len:res_header_len+_size] )
                    pass
                #
                data = bytes(buffer).decode()
                q_out.put( (seq&0x7FFF, data) )
        except Exception as e:
            self.close()
            raise e
        pass

    def start(self) -> None:
        signal.signal( signal.SIGTERM, lambda _num,_frame:self.close() )
        signal.signal( signal.SIGINT,  lambda _num,_frame:self.close() )
        #
        self.shm_res = SharedMemory(name=self.res_id)
        self.sem_res = Semaphore(name=self.res_id)
        #
        self.responses = dict()
        self.seq = Value('L', 0) #unsigned long, 4B
        self.q_in, self.q_out = Queue(), Queue()
        self.send_process = Process(target=self.send, args=(self.q_in, self.shm_req, self.sem_req, self.seq), daemon=True)
        self.recv_process = Process(target=self.recv, args=(self.q_out, self.shm_res, self.sem_res), daemon=True)
        self.send_process.start()
        self.recv_process.start()
        time.sleep(0.01) #promise "send" process starts
        pass

    def close(self,_num='',_frame='') -> None:
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
            unlink_shared_memory(self.shm_res.name)
        except:
            pass
        # sem_res: close and unlink
        try:
            self.sem_res.close()
            unlink_semaphore(self.sem_res.name)
        except:
            pass
        # shm_req: close and unlink
        try:
            unlink_shared_memory(self.shm_req.name)
            self.shm_req = None
        except:
            pass
        # sem_req: close and unlink
        try:
            self.sem_req.close()
            unlink_semaphore(self.sem_req.name)
        except:
            pass
        # sys.exit(0) #FIXME:

    def get_response(self, seq, blocking=True, timeout=-1):
        data = self.responses.pop(seq, None)
        if data is not None:
            return json.loads(data)
        #
        def _process(res):
            _seq, _data = res
            result = None
            if _seq==seq:
                try:
                    result = json.loads(_data) if _data else ''
                except:
                    result = json.loads('null')
            else:
                self.responses.update({_seq:_data})
            return result
        #
        if blocking:
            _ddl = time.time() + (timeout if timeout>0 else 1E3)
            exit_bounded = lambda: _ddl - time.time() < 0
            q_get = lambda: self.q_out.get(timeout=_ddl-time.time())
        else:
            exit_bounded = False
            q_get = lambda: self.q_out.get_nowait()
        #
        data = _process( q_get() )
        while (data is not None) and exit_bounded():
            data = _process( q_get() )
        return data

    def request_async(self, command: _COMMAND, *args, **kwargs) -> int:
        request_format = {
            _COMMAND.ALIVE:        lambda **kwargs:(_COMMAND.ALIVE, ''),
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
                        args_spec[i] = _arg #feed in: dict -> arg
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
            _id = self.__id.encode()
            # handshake-I
            _sock.connect(_addr)
            _sock.sendall(_id)
            # handshake-II
            _tmp = _sock.recv(VDM_CLIENT_ID_LEN)
            if _tmp==_id:
                self.__server = __server
                self.__server.start()
            else:
                raise Exception('Invalid Connection: %s'%_tmp)
            # handshake-III
            _sock.sendall(_id)
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

    def is_alive(self) -> bool:
        return self.__server.is_alive()

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
