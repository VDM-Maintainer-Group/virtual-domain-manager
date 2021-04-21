#!/usr/bin/env python3
import json, base64
import socket

VDM_SERVER_PORT = 42000

class CapabilityHandler:
    def __init__(self):
        pass

    def __getattribute__(self, name: str):
        super().__getattribute__('template')
        # acquire result from remote function 
        return super().__getattribute__(name)
    
    pass

class RPCWrapper:
    def __init__(self, addr):
        pass

    def connect(self):
        pass

    def disconnect(self):
        pass

    def getCapability(self):
        pass

    pass
