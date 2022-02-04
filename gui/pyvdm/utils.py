#!/usr/bin/env python3
import pkg_resources, configparser
from pathlib import Path
from collections.abc import MutableMapping
from pyvdm.core.manager import PARENT_ROOT
from PyQt5.QtCore import (QObject, QThread)

POSIX  = lambda x: x.as_posix() if hasattr(x, 'as_posix') else x
ASSETS = lambda _: pkg_resources.resource_filename('pyvdm', 'assets/'+_)
THEMES = lambda _: pkg_resources.resource_filename('pyvdm', 'assets/themes/'+_)
THEMES_FOLDER = PARENT_ROOT / 'themes'; THEMES_FOLDER.mkdir(parents=True, exist_ok=True)

def signal_emit(_signal, _slot, _msg=None):
    _signal.connect(_slot)
    _signal.emit(*_msg) if _msg else _signal.emit()
    _signal.disconnect(_slot)
    pass

class MFWorker(QObject):
    def __init__(self, func, args=()):
        super().__init__(None)
        self.func = func
        self.args = args
        self.thread = QThread()
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
        self.config_file = POSIX(PARENT_ROOT/'pyvdm-gui.conf')
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