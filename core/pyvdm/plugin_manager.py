#!/usr/bin/env python3
# fix relative path import
from core.pyvdm.utils import WorkSpace
import sys
from pathlib import Path
sys.path.append( Path(__file__).resolve().parent.as_posix() )
# normal import
import json, argparse
import tempfile, shutil
from pyvdm.interface import SRC_API
from utils import * #from pyvdm.core.utils import *

# set(CONFIG_DIR "$HOME/.vdm")
PLUGIN_DIRECTORY= Path('~/.vdm/plugins').expanduser()
REQUIRED_FIELDS = ['name', 'version', 'author', 'main', 'license']
OPTIONAL_FIELDS = ['description', 'keywords', 'capability', 'scripts']
OPTIONAL_SCRIPTS= ['pre-install', 'post-install', 'pre-uninstall', 'post-uninstall']
global args

class PluginWrapper:
    def __init__(self):
        pass
    pass

class PluginManager:
    def __init__(self, root=''):
        if root:
            self.root = Path(root).resolve()
        else:
            self.root = PLUGIN_DIRECTORY
        self.temp = Path( tempfile.gettempdir() )
        pass

    def install(self, url):
        #TODO: if with online url, download as file in _path
        _path = Path(url).expanduser().resolve()
        # whethere a file provided or not
        if not _path.is_file():
            return False #file_error
        # try to unpack the file
        try:
            tmp_dir = self.temp / _path.stem
            shutil.unpack_archive(_path, tmp_dir.as_posix())
            with WorkSpace(tmp_dir) as ws:
                _plugin = PluginWrapper()
                pass
        except Exception as e:
            return False #file_error
        pass

    def uninstall(self, names):
        pass

    def list(self, name=[]):
        pass

    def run(self, name, function):
        pass

    pass

def execute(pm, command, args):
    assert( isinstance(pm, PluginManager) )
    if command=='install':
        pm.install(args.url)
    elif command=='uninstall':
        pm.uninstall(args.names)
    elif command=='list':
        pm.list(args.names)
    elif command=='run':
        pm.run(args.plugin_name, args.plugin_function)
    else:
        print('The command <{}> is not supported.'.format(command))
    pass

def init_subparsers(subparsers):
    p_install = subparsers.add_parser('install',
        help='install a new VDM plugin.')
    p_install.add_argument('url', metavar='plugin_file',
        help='the path to the plugin file in .zip format')
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
        help='run the function of an existing plugin.')
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
        execute(pm, args.command, args)
    except Exception as e:
        raise e#print(e)
    finally:
        pass#exit()
