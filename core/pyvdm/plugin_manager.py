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
global options

class PluginWrapper:
    def __init__(self):
        pass
    pass

class PluginManager(object):
    def __init__(self):
        pass
    pass

def main_install(argv):
    args = parser.parse_args(args=argv)
    # help="install a new plugin from PWD"
    # help="silent without debug information"
    pass

def main_uninstall(argv):
    args = parser.parse_args(args=argv)
    # "remove an existing plugin"
    pass

def main_list(argv):
    args = parser.parse_args(args=argv)
    # help="list all plugins."
    pass

def main_run(argv):
    args = parser.parse_args(args=argv)
    # "run an existing plugin function"
    pass

def main(args):
    _func = 'main_'+args.command[0]
    if _func in __dict__.keys() and callable(__dict__[_func]):
        #FIXME: __dict__ not defined
        __dict__[_func](args.args)
    else:
        print('The command {} is not supported.'.format(R_T(args.command[0])))
    pass

if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(
            description='VDM Plugin Manager.')
        parser.add_argument('command', nargs=1,
            help="install / uninstall / list / run")
        parser.add_argument('args', metavar="arguments", nargs='*')
        args = parser.parse_args()
        main(args)
    except Exception as e:
        print(e)
    finally:
        exit()
