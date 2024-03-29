#!/usr/bin/env python3
import argparse
import ctypes
from distutils.version import LooseVersion
from functools import wraps
from importlib import import_module
import inspect
import multiprocessing as mp
import os
from pathlib import Path
import re
import requests
import shutil
import sys
import tempfile
from urllib.parse import urlparse

from pyvdm.interface import SRC_API
from pyvdm.core.utils import (POSIX, WorkSpace, json_load)
from pyvdm.core.errcode import PluginCode as ERR
from pyvdm.core.CapabilityManager import CapabilityManager

PLUGIN_BUILD_LEVEL = 'release'
CONFIG_FILENAME    = 'package.json'
PARENT_ROOT = Path('~/.vdm').expanduser()
PLUGIN_DIRECTORY= PARENT_ROOT / 'plugins'
CAPABILITY_DIRECTORY = PARENT_ROOT / 'capability'
REQUIRED_FIELDS = ['name', 'version', 'author', 'main', 'license']
OPTIONAL_FIELDS = ['target', 'description', 'keywords', 'capability', 'scripts']
OPTIONAL_SCRIPTS= ['test', 'pre-install', 'post-install', 'pre-uninstall', 'post-uninstall']

class MetaPlugin(SRC_API):
    def __init__(self, name:str, obj):
        self.name = name
        self.obj = obj

    def onStart(self):
        if hasattr(self.obj, 'onStart'):
            return self.obj.onStart()
        return 0

    def onStop(self):
        if hasattr(self.obj, 'onStop'):
            return self.obj.onStop()
        return 0

    def onSave(self, stat_file):
        if hasattr(self.obj, 'onSave'):
            return self.obj.onSave(stat_file)
        return 0

    def onResume(self, stat_file, new=False):
        if hasattr(self.obj, 'onResume'):
            return self.obj.onResume(stat_file, new)
        return 0

    def onClose(self):
        if hasattr(self.obj, 'onClose'):
            return self.obj.onClose()
        return 0
    pass

class PluginWrapper:
    def __init__(self, entry):
        self.root = Path.cwd()
        ##
        if entry.endswith('.py'):
            self.load_python(entry)
            self.type = 'python'
        elif entry.endswith('.so'):
            self.load_cdll(entry)
            self.type = 'cdll'
        else:
            self.obj = None
            raise Exception('Unsupported plugin entry.')
        pass

    def __getattribute__(self, name):
        try:
            _func = getattr(self.obj, name)
            _func = self.wrap_call_in_workspace(_func)
            return _func
        except:
            return super().__getattribute__(name)
            # print('%s is an illegal function name.'%name)
        pass

    @staticmethod
    def wrap_call_on_string(func):
        @wraps(func)
        def _wrap(*args):
            args = tuple( [x.encode() if isinstance(x,str) else x for x in args] )
            return func( *args )
        return _wrap

    @staticmethod
    def wrap_call_in_process(func):
        @wraps(func)
        def _wrap(*args, **kwargs):
            with mp.Pool() as pool:
                handle = pool.apply_async(func, args=args, kwds=kwargs)
                return handle.get(timeout=None) # remote exception may raise here
        return _wrap

    def wrap_call_in_workspace(self, func):
        @wraps(func)
        def _wrap(*args, **kwargs):
            with WorkSpace( POSIX(self.root) ):
                ret = func(*args, **kwargs)
            return ret
        return _wrap

    def load_python(self, entry):
        self.obj = None
        ##
        module_name = Path(entry).stem
        if module_name in sys.modules:
            sys.modules.pop(module_name)
        self._module = import_module(module_name)
        ##
        for _,obj in inspect.getmembers(self._module):
            if inspect.isclass(obj) and issubclass(obj, SRC_API) and (obj is not SRC_API):
                self.obj = obj() #instantiate the abstract class
                break
            pass
        pass

    def load_cdll(self, entry):
        obj = ctypes.CDLL( POSIX(Path(entry).resolve()) )
        obj.onSave.argtypes = [ctypes.c_char_p, ctypes.c_int]
        obj.onSave.restype = ctypes.c_int
        obj.onResume.argtypes = [ctypes.c_char_p, ctypes.c_int]
        obj.onResume.restype = ctypes.c_int
        #obj.onTrigger
        self.obj = obj
        pass

    pass

class PluginManager:
    def __init__(self, root='', cm=None):
        if root:
            self.root = Path(root).resolve()
        else:
            self.root = PLUGIN_DIRECTORY
        if cm:
            self.cm = cm
        else:
            self.cm = CapabilityManager()
        self.root.mkdir(exist_ok=True, parents=True) #ensure root existing
        pass

    def test_config(self, config) -> ERR:
        # test required config fields
        for key in REQUIRED_FIELDS:
            if key not in config:
                return ERR.CONFIG_REQUIRED_FIELD_MISSING
        # test whether main entry is legal (*.py or *.so)
        if not (config['main'].endswith('.py') or config['main'].endswith('.so')):
            return ERR.CONFIG_MAIN_ENTRY_ILLEGAL
        # test whether main entry is provided
        _pre_built = Path(PLUGIN_BUILD_LEVEL, config['main']).exists()
        _post_built= ('scripts' in config) and ('pre-install' in config['scripts'])
        if not (_pre_built or _post_built):
            return ERR.CONFIG_MAIN_ENTRY_MISSING
        # test capability requirement
        if ('capability' in config) and isinstance(config['capability'], list):
            with WorkSpace('.') as ws:
                for item in config['capability']:
                    if self.cm.status(item) == 'N/A':
                        return ERR.PLUGIN_CAPABILITY_MISSING
                    pass
                pass
        # test build command and build plugin
        if not _pre_built and _post_built:
            ret = os.system(config['scripts']['pre-install'])
            if (ret < 0) or (not Path(PLUGIN_BUILD_LEVEL, config['main']).exists()):
                return ERR.PLUGIN_BUILD_FAILED
        # all test pass
        return ERR.ALL_CLEAN

    def getInstalledPlugin(self, name, required_version=None) -> MetaPlugin:
        _installed = list(sorted(self.root.glob( '%s-*.*'%name ), reverse=True))
        # select the only plugin
        _selected  = None
        if not required_version:
            _selected = _installed[0].name
        else:
            _regex = re.compile( '%s-(\\d\\.\\d.*)'%name )
            for item in _installed:
                _version = _regex.findall(item.name)[0]
                if LooseVersion(_version) >= LooseVersion(required_version):
                    _selected = item.name
                    break
            pass
        if not _selected:
            return ERR.PLUGIN_LOAD_FAILED # type: ignore
        #
        with WorkSpace(self.root, _selected) as ws:
            _config = json_load(CONFIG_FILENAME)
            ret = self.test_config(_config)
            if ret!=True:
                return ret # type: ignore
            pass
        #
        with WorkSpace(self.root, _selected, PLUGIN_BUILD_LEVEL) as ws:
            try:
                _obj = PluginWrapper(_config['main'])
                _plugin = MetaPlugin( name, _obj )
            except Exception as e:
                return ERR.PLUGIN_WRAPPER_FAILED # type: ignore
            pass
        return _plugin

    def getPluginsWithTarget(self) -> tuple:
        gui_plugins, other_plugins = dict(), dict()
        info = self.list()
        for k,v in info.items():
            if 'target' in v:
                gui_plugins[k] = v['target']
            else:
                other_plugins[k] = v
        return (gui_plugins, other_plugins)

    def install(self, url) -> ERR:
        # if with online url, download as file in _path
        if urlparse(url).scheme in ['http', 'https']:
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write( requests.get(url).content )
                _path = Path(f.name)
        elif urlparse(url).scheme in ['file', '']:
            _path = Path(url).expanduser().resolve()
        else:
            return ERR.ARCHIVE_INVALID
        # test whether a file provided or not
        if not _path.is_file():
            return ERR.ARCHIVE_INVALID
        # try to unpack the file to tmp_dir
        with tempfile.TemporaryDirectory() as _tmp_dir:
            try:
                tmp_dir = Path(_tmp_dir) / _path.name
                shutil.unpack_archive( POSIX(_path), POSIX(tmp_dir) )
            except:
                return ERR.ARCHIVE_UNPACK_FAILED
            # try to test plugin integrity
            with WorkSpace(tmp_dir) as ws:
                try:
                    _config = json_load(CONFIG_FILENAME)
                    ret = self.test_config(_config)
                    if ret!=True:
                        return ret
                except Exception as e:
                    return ERR.CONFIG_FILE_MISSING
                pass
            # try to load plugin
            with WorkSpace(tmp_dir, PLUGIN_BUILD_LEVEL) as ws:
                try:
                    _plugin = PluginWrapper(_config['main'])
                except Exception as e:
                    # raise e
                    return ERR.PLUGIN_WRAPPER_FAILED
                pass
            # move to root dir with new name
            _regex = re.compile( '%s-(\\d\\.\\d.*)'%_config['name'] )
            _installed = sorted(self.root.glob( '%s-*.*'%_config['name'] ))
            for item in _installed:
                _version = _regex.findall(item.name)[0]
                if LooseVersion(_version) < LooseVersion(_config['version']):
                    shutil.rmtree(item)
                    print('Remove elder version: %s'%item.name)
                else:
                    print('Higher version already installed: %s'%item.name)
                    return ERR.PLUGIN_HIGHER_VERSION_EXISTS
                pass
            _new_name = _config['name']+'-'+_config['version']
            shutil.move( POSIX(tmp_dir), POSIX(self.root / _new_name) )
            print('Plugin installed: %s'%_new_name)
            #NOTE: disable 'post-install' for safety issue
            # with WorkSpace(self.root) as ws:
            #     if ('scripts' in _config) and ('post-install' in _config['scripts']):
            #         ret = os.system(_config['scripts']['post-install'])
            #     pass
        return ERR.ALL_CLEAN

    def uninstall(self, names) -> ERR:
        names = names if isinstance(names, list) else [names]
        with WorkSpace(self.root) as ws:
            for name in names:
                _regex = re.compile( '%s-(\\d\\.\\d.*)'%name )
                _installed = sorted(self.root.glob( '%s-*.*'%name ))
                for item in _installed:
                    _version = _regex.findall(item.name)[0]
                    shutil.rmtree(item)
                    print('Removed plugin: %s'%item.name)
                pass
            pass
        return ERR.ALL_CLEAN #always

    def list(self, names=[]) -> dict:
        _regex = re.compile('(?P<name>.+)-(?P<version>\\d\\.\\d.*)')
        _installed = sorted( self.root.glob( '*-*.*' ) )
        result = dict()

        for item in _installed:
            (_name, _version) = _regex.findall(item.name)[0]
            if len(names)==0 or (_name in names):
                _config = json_load( POSIX(item / CONFIG_FILENAME) )
                if _name not in result: #ignore duplicate plugins
                    result[_name] = _config
            pass

        return result

    def run(self, name, function, args):
        ret = self.getInstalledPlugin(name)
        if isinstance(ret, MetaPlugin):
            return getattr(ret, function)(*args)
        else:
            return ret
        pass

    pass

def execute(pm, command, args, verbose=False):
    assert( isinstance(pm, PluginManager) )
    if command=='install':
        return pm.install(args.url)
    elif command=='uninstall':
        return pm.uninstall(args.names)
    elif command=='list':
        _res = pm.list(args.names); print(_res)
        return _res
    elif command=='run':
        return pm.run(args.plugin_name, args.plugin_function) # type: ignore
    elif command==None:
        print('<Plugin Directory Status>')
    else:
        print('The command <{}> is not supported.'.format(command))
    return

def init_subparsers(subparsers):
    p_install = subparsers.add_parser('install',
        help='install a new VDM plugin.')
    p_install.add_argument('url', metavar='plugin_file',
        help='the path to the plugin file in .zip format.')
    #
    p_uninstall = subparsers.add_parser('uninstall',
        help='uninstall VDM plugins.')
    p_uninstall.add_argument('names', metavar='plugin_names', nargs='+',
        help='the plugin name(s) to uninstall.')
    #
    p_list = subparsers.add_parser('list',
        help='list information of installed VDM plugins.')
    p_list.add_argument('names', metavar='plugin_names', nargs='*',
        help='the specified plugin name(s) to list.')
    #
    p_run = subparsers.add_parser('run',
        help='run the function of an existing VDM plugin.')
    p_run.add_argument('plugin_name',
        help='plugin name')
    p_run.add_argument('plugin_function',
        help='plugin function name')
    pass

if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(
            description='VDM Plugin Manager.')
        subparsers = parser.add_subparsers(dest='command')
        init_subparsers(subparsers)
        #
        args = parser.parse_args()
        pm = PluginManager()
        ret = execute(pm, args.command, args)
        if isinstance(ret, ERR):
            raise Exception(ret.name)
    except Exception as e:
        raise e#pass
    finally:
        pass#exit()
