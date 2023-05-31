#!/usr/bin/env python3
from collections.abc import MutableMapping
import configparser
from pathlib import Path
import pkg_resources
from PyQt5.QtCore import (Qt, QObject, QThread)
import time

from pyvdm.core.manager import VDM_HOME

POSIX  = lambda x: x.as_posix() if hasattr(x, 'as_posix') else x
ASSETS = lambda _: pkg_resources.resource_filename('pyvdm', 'assets/'+_)
THEMES = lambda _: pkg_resources.resource_filename('pyvdm', 'assets/themes/'+_)
THEMES_FOLDER = VDM_HOME / 'themes'

THEMES_FOLDER.mkdir(parents=True, exist_ok=True)

def signal_emit(_signal, _slot, _msg=None):
    _signal.connect(_slot)
    _signal.emit(*_msg) if _msg else _signal.emit()
    _signal.disconnect(_slot)
    pass

def smooth_until(view, avg_cond=None, min_cond=None, max_cond=None,
                 interval=0.1, window_size=3, timeout=5):
    ptr = 0
    start_time = time.time()
    ##
    sliding_window = [0] * window_size
    for i in range(window_size):
        sliding_window[i] = view()
        time.sleep( interval )
    ##
    while time.time() - start_time < timeout:
        _flag = True
        sliding_window[ptr] = view()
        ptr = (ptr + 1) % window_size
        ##
        if avg_cond: _flag = _flag and avg_cond( sum(sliding_window)/window_size )
        if min_cond: _flag = _flag and min_cond( min(sliding_window) )
        if max_cond: _flag = _flag and max_cond( max(sliding_window) )
        ##
        if _flag: break
        time.sleep( interval )
    pass

class KeysReactor:

    keySpecs = {
        Qt.Key_Control: 0x01, # type: ignore
        Qt.Key_Alt:     0x02, # type: ignore
        Qt.Key_Shift:   0x04, # type: ignore
    }
    keySpecsKeys = keySpecs.keys()

    def __init__(self, parent, name='Default'):
        self.name = name
        self.key_list = [0x00]
        self.reactor  = dict()
        self.press_hook_pre    = None
        self.press_hook_post   = None
        self.release_hook_pre  = None
        self.release_hook_post = None

        if parent:
            self.parent = parent
            self.super  = super(type(parent), parent)
            parent.keyPressEvent   = lambda e: self.pressed(e.key(), e)
            parent.keyReleaseEvent = lambda e: self.released(e.key(), e)
        pass
    
    def __str__(self):
        ret = []
        ret.append('Ctrl')  if self.key_list[0]&0x01 else None
        ret.append('Alt')   if self.key_list[0]&0x02 else None
        ret.append('Shift') if self.key_list[0]&0x04 else None
        ret += [str(x) for x in self.key_list[1:]]
        return '[%s] %s'%(self.name, '+'.join(ret))
    
    @staticmethod
    def parse_keys(keys):
        ret = list()
        try:
            for _key in keys:
                _key = _key.strip().upper()
                if _key=='CTRL':    _key = 'Control'
                elif _key=='ALT':   _key = 'Alt'
                elif _key=='SHIFT': _key = 'Shift'
                elif _key=='ENTER': _key = 'Enter'
                elif _key=='RETURN':_key = 'Return'
                elif _key in ['ESC','ESCAPE']:
                    _key = 'Escape'
                if hasattr(Qt, 'Key_'+_key):
                    ret.append( getattr(Qt, 'Key_'+_key) )
        finally:
            return ret

    def register(self, keys, hookfn):
        key_hash = [0x00]
        keys = self.parse_keys(keys)
        ##
        for tmp_key in keys:
            if tmp_key in self.keySpecsKeys: # for specific keys
                key_hash[0] = key_hash[0] | self.keySpecs[tmp_key]
            else:                            # for general keys
                key_hash.append(tmp_key)
            pass
        key_hash = '_'.join([str(x) for x in key_hash])
        self.reactor[key_hash] = hookfn
        pass
    
    def pressed(self, key, e=None):
        #NOTE: pre hook
        if self.press_hook_pre:
            self.press_hook_pre(e)

        #NOTE: press keys
        if key in self.keySpecsKeys:
            self.key_list[0] = self.key_list[0] | self.keySpecs[key] #append specific keys
        else:
            self.key_list.append(key)
        key_hash = '_'.join([str(x) for x in self.key_list])
        if key_hash in self.reactor:
            ret = self.reactor[key_hash]() #unused ret code
        else:
            self.super.keyPressEvent(e)
        
        #NOTE: post hook
        if self.press_hook_post:
            self.press_hook_post(e)
        pass
    
    def released(self, key, e=None):
        #NOTE: pre hook
        if self.release_hook_pre:
            self.release_hook_pre(e)
        
        #NOTE: remove keys
        if key in self.keySpecsKeys:                # remove a special key
            self.key_list[0] = self.key_list[0] & (~self.keySpecs[key]) #remove specific keys
        elif key in self.key_list:                  # remove a common key
            self.key_list.remove(key)
        elif key in [Qt.Key_Return, Qt.Key_Enter]:  # reset the list # type: ignore
            self.key_list = [0x00]
        self.super.keyReleaseEvent(e)
        if self.key_list[0]==0x00: #reset, if no specific keys presented
            self.key_list = [0x00]

        #NOTE: post hook
        if self.release_hook_post:
            self.release_hook_post(e)
        pass

    def hasSpecsKeys(self):
        return self.key_list[0] != 0x00

    def clear(self):
        self.key_list = [0x00]
        pass

    def setKeyPressHook(self, press_hook, post=True):
        if post:
            self.press_hook_post = press_hook
        else:
            self.press_hook_pre  = press_hook
        pass

    def setKeyReleaseHook(self, release_hook, post=True):
        if post:
            self.release_hook_post = release_hook
        else:
            self.release_hook_pre  = release_hook
        pass

    pass

class MFWorker(QObject):
    def __init__(self, func, args=()):
        super().__init__(None)
        self.func = func
        self.args = args
        self.thread = QThread() # type: ignore
        self.moveToThread(self.thread)
        self.thread.started.connect(self.run)
        pass

    def isRunning(self):
        return self.thread.isRunning()

    def start(self):
        self.thread.start()
        pass
    
    def terminate(self):
        self.thread.exit(0)
        pass

    def run(self):
        self.func(*self.args)
        self.terminate()
        pass
    pass

class ConfigFile(MutableMapping):

    def __init__(self):
        #
        self.global_config = configparser.ConfigParser(allow_no_value=True, default_section='default')
        self.global_config.read( ASSETS('pyvdm-gui.conf') )
        #
        self.config_file = POSIX(VDM_HOME/'pyvdm-gui.conf')
        self.user_config = configparser.ConfigParser(allow_no_value=True, default_section='default')
        try:
            self.user_config.read( self.config_file )
            self.global_config.read( self.config_file )
        except:
            pass
        pass

    def __getitem__(self, key):
        sec, key = self._getsection(key)
        value = self.global_config[sec][key]
        #
        if sec=='theme':
            _global_value = THEMES(value)
            if Path(_global_value).exists():
                return _global_value
            else:
                return POSIX(THEMES_FOLDER/value)
        #
        if sec=='assets':
            return ASSETS(value)
        #
        return self.global_config[sec][key]

    def __setitem__(self, key, value):
        sec, key = self._getsection(key)
        self.global_config[sec][key] = value
        #
        if sec not in self.user_config:
            self.user_config[sec] = {}
        self.user_config[sec][key] = value
        with open(self.config_file, 'w+') as fh:
            self.user_config.write(fh)
        pass

    def __delitem__(self, key):
        sec, key = self._getsection(key)
        try:
            del self.global_config[sec][key]
            del self.user_config[sec][key]
        except:
            pass

    def __iter__(self):
        return iter(self.global_config.sections())

    def __len__(self):
        return len(self.global_config)

    def _getsection(self, key:str):
        if key.startswith('THEME_'):
            return ( 'theme', key.split('_',1)[1] )
        elif key.startswith('ASSETS_'):
            return ( 'assets', key.split('_',1)[1] )
        elif key.startswith('DEFAULT_'):
            return ( 'default', key.split('_',1)[1] )
        else:
            return ( 'default', key )

    pass

CONFIG = ConfigFile()