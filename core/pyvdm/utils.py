#!/usr/bin/env python3
import json
from os import chdir
from pathlib import Path
import random
import shutil
import string
import sys
import tempfile

STAT_FILENAME = 'stat'
POSIX  = lambda x: x.as_posix() if hasattr(x, 'as_posix') else x

class KeyringEnDec:
    import crypt
    from cryptography.fernet import Fernet
    import keyring

    def __init__(self, default_password='pyvdm'):
        self.set_default_password( default_password )
        pass

    def salted_password(self, password:str) -> str:
        _salt = self.crypt.mksalt( self.crypt.METHOD_SHA512 )
        return self.crypt.crypt(password, _salt)

    def set_default_password(self, password:str):
        self.default_password = self.salted_password(password)
        pass

    def set_password(self, service:str, password:str):
        # only support set password at first time
        if self.keyring.get_password('pyvdm', service):
            return
        # store salted password
        salted_password = self.salted_password( password )
        self.keyring.set_password('pyvdm', service, salted_password)
        pass

    def encrypt(self, service:str, data:str) -> str:
        password = self.keyring.get_password('pyvdm', service)
        password = password if password else self.default_password
        ##
        data = self.Fernet(password).encrypt( data.encode() ).decode()
        return data

    def decrypt(self, service:str, data:str) -> str:
        password = self.keyring.get_password('pyvdm', service)
        password = password if password else self.default_password
        ##
        data = self.Fernet(password).decrypt( data.encode() ).decode()
        return data

class Tui:
    def __init__(self):
        pass
    
    @staticmethod
    def cls():
        pass

    @staticmethod
    def confirm(message, yes=True):
        _opt = '([Y]/N)' if yes else '(Y/[N])'
        print( '%s %s'%(message, _opt) )
        #
        _res = input('>>> ').strip()
        if not _res:
            return yes
        elif _res in ['Y', 'y']:
            return True
        elif _res in ['N', 'n']:
            return False
        else:
            print('Invalid Input. Please try again.')
            return Tui.confirm(message, yes) #repeat
        pass

    @staticmethod
    def ask(message, default=''):
        _opt = '' if not default else ' (default: \"%s\")'%default
        print( '%s%s'%(message, _opt) )
        #
        _res = input('>>> ').strip()
        if _res:
            return _res
        elif default:
            return default
        else:
            return Tui.ask(message, default)
        pass

    @staticmethod
    def select(message, candidates, defaults=None, multi=True, retry=False):
        assert( isinstance(candidates, list) )
        if not retry:
            _title = '======== %s ========'%message
            _opt = [ '[%d] %s'%(idx+1,name) for idx,name in enumerate(candidates) ]
            _opt = '\t'.join(_opt)
            print(_title); print(_opt)
        if defaults:
            defaults = [candidates.index(x) for x in defaults]
            _selected = ['[%d]'%(x+1) for x in defaults]
            _selected = ', '.join(_selected)
            print('Default selection: %s'%_selected)
        #
        _res = input('(split by space) >>> ').strip().split()
        if len(_res)==0 and defaults:
            return defaults
        else:
            _res = [ int(x)-1 for x in _res ]
            _res = list( filter(lambda x: x>=0 and x<len(candidates), _res) )
            if len(_res)==0:
                print('Invalid Selection. Please try again.')
                return Tui.select(message, candidates, defaults, multi, retry=True)
            else:
                return _res if multi else [_res[0]]
    pass

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
        sys.path.insert(0, self.wrk.as_posix())
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        sys.path.pop(0)
        chdir(self.pwd)
        if exc_tb: pass
        pass
    pass

class StatFile:
    def __init__(self, root, prefix=None, touch=True):
        self.root = root
        if prefix:
            _stat_file = prefix+'.'+STAT_FILENAME
        else:
            _stat_file = STAT_FILENAME
        self.stat_file = Path(root, _stat_file).resolve()
        self.stat_file.touch(exist_ok=True)
        _,self.temp_file = tempfile.mkstemp()
        pass

    def touch(self):
        self.stat_file.touch(exist_ok=True)
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
    fd = open(filename, 'r+')
    _dict = json.load(fd)
    fd.close()
    return _dict

def json_dump(filename, config):
    fd = open(filename, 'w+')
    json.dump(config, fd)
    fd.close()
    pass

def retry_with_timeout(lamb_fn, default=None, timeout=1):
    import time
    _now = time.time()
    ##
    try:
        ret = lamb_fn()
    except:
        ret = default
    ##
    while not ret and time.time()-_now<timeout:
        try:
            ret = lamb_fn()
        except:
            ret = default
        time.sleep(0.1)
    return ret

def getRandomSerial(len, dtype='hex'):
    if dtype=='hex':
        return ''.join(random.choice(string.hexdigits.upper()) for _ in range(len))
    elif dtype=='dec':
        return ''.join(random.choice(string.digits) for _ in range(len))
    elif dtype=='char':
        return ''.join(random.choice(string.ascii_uppercase) for _ in range(len))
    else:
        return ''
    pass
