#!/usr/bin/env python3
import random, math, string
import shutil
import sys, logging
import json, tempfile
from crcmod import mkCrcFun
from termcolor import colored, cprint
from pathlib import Path
from os import chdir

STAT_FILENAME = 'stat'
POSIX  = lambda x: x.as_posix() if hasattr(x, 'as_posix') else x

def R_T(text): return colored(text, 'red')
def G_T(text): return colored(text, 'green')
def B_T(text): return colored(text, 'blue')
def C_T(text): return colored(text, 'cyan')
def M_T(text): return colored(text, 'magenta')
def Y_T(text): return colored(text, 'yellow')

class WorkSpace:
    def __init__(self, p, *p_l, **kargs):
        self.wrk = Path(p, *p_l).expanduser().resolve()
        self.pwd = Path.cwd()
        if 'forceUpdate' in kargs.keys():
            self.forceUpdate = True
        else:
            self.forceUpdate = False
        pass
    
    def __enter__(self):
        if not Path(self.wrk).is_dir():
            if self.forceUpdate:
                Path(self.wrk).mkdir(mode=0o755, parents=True, exist_ok=True)
            else:
                return self.__exit__(*sys.exc_info())
        else:
            pass
        chdir(self.wrk)
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        chdir(self.pwd)
        if exc_tb: pass
        pass
    pass

class StatFile:
    def __init__(self, root, prefix=None):
        self.root = root
        if prefix:
            _stat_file = prefix+'.'+STAT_FILENAME
        else:
            _stat_file = STAT_FILENAME
        self.stat_file = Path(root, _stat_file).resolve()
        self.stat_file.touch(exist_ok=True)
        _,self.temp_file = tempfile.mkstemp()
        pass

    def getFile(self):
        shutil.copy( POSIX(self.stat_file), self.temp_file )
        return self.temp_file

    def putFile(self):
        shutil.move( self.temp_file, POSIX(self.stat_file) )
        pass

    def getStat(self):
        with open(POSIX(self.stat_file), 'r') as fd:
            _name = fd.readline()
        return _name

    def putStat(self, name):
        try:
            with open(POSIX(self.stat_file), 'w') as fd:
                fd.writelines([name])
            return True
        except Exception as e:
            return False
    pass

def json_load(filename):
    fd = open(filename, 'r')
    _dict = json.load(fd)
    fd.close()
    return _dict

def getRandomSerial(len, dtype='hex'):
    if dtype=='hex':
        return ''.join(random.choice(string.hexdigits.upper()) for _ in range(len))
    elif dtype=='dec':
        return ''.join(random.choice(string.digits) for _ in range(len))
    elif dtype=='char':
        return ''.join(random.choice(string.uppercase) for _ in range(len))
    else:
        return ''
    pass

def getChecksum(obj, dtype='crc-16'):
    _csm = ''
    #TODO: to support crc-16/md5/sha1
    return _csm