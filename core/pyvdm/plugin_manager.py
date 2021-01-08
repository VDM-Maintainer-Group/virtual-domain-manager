#!/usr/bin/env python3
# fix relative path import
import sys
from pathlib import Path
sys.path.append( Path(__file__).resolve().parent.as_posix() )
# normal import
import json, argparse
from utils import *

# set(CONFIG_DIR "$HOME/.vdm")
# set(PLUGINS_DIR "$HOME/.vdm/plugins")
REQUIRED_FIELDS = ['name', 'version', 'author', 'main', 'license']
OPTIONAL_FIELDS = ['description', 'keywords', 'capability', 'scripts']
OPTIONAL_SCRIPTS= ['pre-install', 'post-install', 'pre-uninstall', 'post-uninstall']
global args

class PluginWrapper:
    def __init__(self):
        pass
    pass

class PluginManager:
    def __init__(self):
        pass

    def install(self):
        pass

    def uninstall(self):
        pass

    def list(self):
        pass

    def run(self):
        pass

    pass

def main(args):
    # print('The command <{}> is not supported.'.format(args.command[0]))
    pass

if __name__ == '__main__':
    try:
        # help="silent without debug information"
        parser = argparse.ArgumentParser(
            description='VDM Plugin Manager.')
        subparsers = parser.add_subparsers(dest='command')
        #
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
        #
        p_run = subparsers.add_parser('run',
            help='run the function of an existing plugin.')
        p_run.add_argument('plugin_name',
            help='plugin name')
        p_run.add_argument('plugin_function',
            help='plugin function name')
        #
        args = parser.parse_args()
        print(args)
        main(args)
    except Exception as e:
        raise e#print(e)
    finally:
        pass#exit()
