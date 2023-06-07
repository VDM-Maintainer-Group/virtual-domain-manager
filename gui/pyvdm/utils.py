#!/usr/bin/env python3
from collections.abc import MutableMapping
import configparser
from pathlib import Path
import pkg_resources
from PyQt5.QtCore import (Qt, QObject, QThread, QTimer)
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
    def __init__(self, parent=None):
        self.key_list = list()
        self.reactor  = dict()

        if parent:
            self.parent = parent
            self.super  = super(type(parent), parent)
            parent.keyPressEvent   = lambda e: self.pressed(e.key(), e)
            parent.keyReleaseEvent = lambda e: self.released(e.key(), e)
        pass
    
    def __str__(self):
        return self.keys_hash

    @staticmethod
    def parse_keys(keys_str:list) -> list:
        shorthands = {
            'Ctrl':'Control', 'Super':'Meta', 'Win':'Meta',
            'Esc':'Escape', 'Del':'Delete',
        }
        keys = [ x.strip().capitalize() for x in keys_str ]
        keys = [ shorthands.get(x,x) for x in keys ]
        keys = [ getattr(Qt.Key, f'Key_{x}') for x in keys ]
        return keys

    @staticmethod
    def keys_to_hash(keys:list) -> str:
        return '_'.join([ str(x) for x in sorted(keys) ])

    @property
    def key_list_hash(self):
        self.key_list.sort()
        return self.keys_to_hash(self.key_list)

    def register(self, keys_str:list, callback):
        key_hash = self.keys_to_hash( self.parse_keys(keys_str) )
        self.reactor[key_hash] = callback
        pass
    
    def pressed(self, key, e=None):
        self.key_list.append(key)
        if self.key_list_hash in self.reactor:
            ret = self.reactor[self.key_list_hash]()
        else:
            self.super.keyPressEvent(e)
        pass
    
    def released(self, key, e=None):
        if key in [Qt.Key.Key_Meta, Qt.Key.Key_Control]:
            self.key_list.clear()
        ##
        QTimer.singleShot(150, lambda: self.key_list.remove(key)) # remove only once
        self.super.keyReleaseEvent(e)
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
        sec, key = self._get_section(key)
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
        sec, key = self._get_section(key)
        self.global_config[sec][key] = value
        #
        if sec not in self.user_config:
            self.user_config[sec] = {}
        self.user_config[sec][key] = value
        with open(self.config_file, 'w+') as fh:
            self.user_config.write(fh)
        pass

    def __delitem__(self, key):
        sec, key = self._get_section(key)
        try:
            del self.global_config[sec][key]
            del self.user_config[sec][key]
        except:
            pass

    def __iter__(self):
        return iter(self.global_config.sections())

    def __len__(self):
        return len(self.global_config)

    def _get_section(self, key:str):
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