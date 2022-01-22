#!/usr/bin/env python3
# fix relative path import
import sys, inspect
from pathlib import Path
sys.path.append( Path(__file__).resolve().parent.as_posix() )
# normal import
import os, argparse, re
import tempfile, shutil
import ctypes
import multiprocessing as mp
# from importlib.machinery import SourceFileLoader
from distutils.version import LooseVersion
from functools import partial, wraps
from pyvdm.interface import SRC_API
from pyvdm.core.utils import *
from pyvdm.core.errcode import PluginCode as ERR

PLUGIN_BUILD_LEVEL = 'release'
CONFIG_FILENAME    = 'package.json'
PARENT_ROOT = Path('~/.vdm').expanduser()
PLUGIN_DIRECTORY= PARENT_ROOT / 'plugins'
REQUIRED_FIELDS = ['name', 'version', 'author', 'main', 'license']
OPTIONAL_FIELDS = ['description', 'keywords', 'capability', 'scripts']
OPTIONAL_SCRIPTS= ['pre-install', 'post-install', 'pre-uninstall', 'post-uninstall']

class PluginWrapper():
    def __init__(self, config, entry):
        self.config = config
        self.name = config['name']
        self.root = Path.cwd()
        if entry.endswith('.py'):
            self.load_python(entry)
            self.type = 'python'
        elif entry.endswith('.so'):
            self.load_cdll(entry)
            self.type = 'cdll'
        else:
            raise Exception('Unsupported plugin entry.')
        pass

    def __getattribute__(self, name):
        try:
            _func = getattr(self.obj, name)
            _func = self.wrap_call_in_process(_func)
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
                handle = pool.apply_async(func, args=args, kwargs=kwargs)
                return handle.get(timeout=None)
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
        _module = __import__( Path(entry).stem )
        for _,obj in inspect.getmembers(_module):
            if inspect.isclass(obj) and issubclass(obj, SRC_API) and (obj is not SRC_API):
                self.obj = obj() #instantiate the abstract class
                break
            pass
        pass

    def load_cdll(self, entry):
        obj = ctypes.CDLL( POSIX(Path(entry).resolve()) )
        obj.onSave = self.wrap_call_on_string(obj.onSave)
        obj.onResume = self.wrap_call_on_string(obj.onResume)
        #obj.onTrigger
        self.obj = obj
        pass

    pass

class PluginManager:
    def __init__(self, root=''):
        if root:
            self.root = Path(root).resolve()
        else:
            self.root = PLUGIN_DIRECTORY
        self.root.mkdir(exist_ok=True, parents=True) #ensure root existing
        self.temp = Path( tempfile.mkdtemp() )
        pass

    @staticmethod
    def test_config(config):
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
            for item in config['capability']:
                #TODO: invoke dependency check from `CapabilityManager`
                pass
            pass
        # test build command and build plugin
        if not _pre_built and _post_built:
            ret = os.system(config['scripts']['pre-install'])
            if (ret < 0) or (not Path(PLUGIN_BUILD_LEVEL, config['main']).exists()):
                return ERR.PLUGIN_BUILD_FAILED
        # all test pass
        return True

    def getInstalledPlugin(self, name, required_version=None):
        _installed = list(sorted(self.root.glob( '%s-*.*'%name ), reverse=True))
        # select the only plugin
        _selected  = None
        if not required_version:
            _selected = _installed[0].name
        else:
            _regex = re.compile( '%s-(\d\.\d.*)'%name )
            for item in _installed:
                _version = _regex.findall(item.name)[0]
                if LooseVersion(_version) >= LooseVersion(required_version):
                    _selected = item.name
                    break
            pass
        if not _selected:
            return ERR.PLUGIN_LOAD_FAILED
        #
        with WorkSpace(self.root, _selected) as ws:
            _config = json_load(CONFIG_FILENAME)
            ret = self.test_config(_config)
            if ret!=True:
                return ret
            pass
        #
        with WorkSpace(self.root, _selected, PLUGIN_BUILD_LEVEL) as ws:
            try:
                _plugin = PluginWrapper(_config, _config['main'])
            except Exception as e:
                return ERR.PLUGIN_WRAPPER_FAILED
            pass
        return _plugin

    def install(self, url):
        #TODO: if with online url, download as file in _path
        _path = Path(url).expanduser().resolve()
        # test whether a file provided or not
        if not _path.is_file():
            return ERR.ARCHIVE_INVALID
        # try to unpack the file to tmp_dir
        try:
            tmp_dir = self.temp / _path.name
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
                _plugin = PluginWrapper(_config, _config['main'])
            except Exception as e:
                # raise e
                return ERR.PLUGIN_WRAPPER_FAILED
            pass
        # move to root dir with new name
        _regex = re.compile( '%s-(\d\.\d.*)'%_config['name'] )
        _installed = sorted(self.root.glob( '%s-*.*'%_config['name'] ))
        for item in _installed:
            _version = _regex.findall(item.name)[0]
            if LooseVersion(_version) < LooseVersion(_config['version']):
                shutil.rmtree(item)
                print('Remove elder version: %s'%item.name)
            else:
                print('Higher version already installed: %s'%item.name)
                return ERR.PLUGIN_HIGHER_VERSION
            pass
        _new_name = _config['name']+'-'+_config['version']
        shutil.move( POSIX(tmp_dir), POSIX(self.root / _new_name) )
        print('Plugin installed: %s'%_new_name)
        #NOTE: disable 'post-install' for safety issue
        # with WorkSpace(self.root) as ws:
        #     if ('scripts' in _config) and ('post-install' in _config['scripts']):
        #         ret = os.system(_config['scripts']['post-install'])
        #     pass
        return True

    def uninstall(self, names):
        names = list(names)
        with WorkSpace(self.root) as ws:
            for name in names:
                _regex = re.compile( '%s-(\d\.\d.*)'%name )
                _installed = sorted(self.root.glob( '%s-*.*'%name ))
                for item in _installed:
                    _version = _regex.findall(item.name)[0]
                    shutil.rmtree(item)
                    print('Removed plugin: %s'%item.name)
                pass
            pass
        return True #always

    def list(self, names=[]):
        _regex = re.compile('(?P<name>.+)-(?P<version>\d\.\d.*)')
        _installed = sorted( self.root.glob( '*-*.*' ) )
        result = dict()

        for item in _installed:
            (_name, _version) = _regex.findall(item.name)[0]
            if len(names)==0 or (_name in names):
                _config = json_load( POSIX(item / CONFIG_FILENAME) )
                if _name not in result:
                    result[_name] = [_config]
                else:
                    result[_name].append(_config)
            pass
        print(result)

        return result

    def run(self, name, function, *args):
        ret = self.getInstalledPlugin(name)
        if isinstance(ret, PluginWrapper):
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
        return pm.list(args.names)
    elif command=='run':
        return pm.run(args.plugin_name, args.plugin_function)
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
