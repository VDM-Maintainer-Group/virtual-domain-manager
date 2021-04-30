#!/usr/bin/env python3
import random, time, string
import os, socket, struct, asyncio
import json, base64
from enum import Enum
from functools import wraps
from multiprocessing import shared_memory

VDM_SERVER_PORT = 42000
VDM_CLIENT_ID_LEN = 32
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
    SERVER_ON   = 0x01 #b0001
    SERVER_DONE = 0x00 #b0000
    CLIENT_ON   = 0x02 #b0010
    CLIENT_DONE = 0x03 #b0011
    pass

class __HEADER:
    pass

class ShmManager:
    def __init__(self, __id) -> None:
        shared_memory.SharedMemory(name=__id)
        pass

    def is_alive(self) -> bool:
        pass

    def request(self, command:__COMMAND, *args, **kwargs):
        pass

    pass

class CapabilityHandle:
    def __init__(self, server: ShmManager, spec: dict):
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
        try:
            _sock.connect(_addr)
            _sock.sendall(self.__id)
            _tmp = _sock.recv(VDM_CLIENT_ID_LEN+1) #+1 for '\0'
            if _tmp==self.__id:
                self.__server = ShmManager(self.__id)
            else:
                raise Exception('Invalid Connection: %s'%_tmp)
        except Exception as e:
            raise e
        pass

    def disconnect(self) -> None:
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
        spec = self.__server.request(__COMMAND.REGISTER, name)
        if spec is None:
            return None
        else:
            _item = CapabilityHandle(self.server, spec)
            self.capability.update( {name:_item} )
            return _item
        pass

    pass
