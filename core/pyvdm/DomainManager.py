#!/usr/bin/env python3
# fix relative path import
import sys
from pathlib import Path
sys.path.append( Path(__file__).resolve().parent.as_posix() )
# normal import
import os, argparse, re
import tempfile, shutil
import pyvdm.core.PluginManager as P_MAN
from pyvdm.core.utils import *

DOMAIN_ROOT = Path('~/.vdm').expanduser()
CONFIG_FILENAME = 'config.json'

class DomainManager():
    def __init__(self, root=''):
        if root:
            self.root = Path(root).resolve()
        else:
            self.root = DOMAIN_ROOT
        self.root.mkdir(exist_ok=True, parents=True)
        (self.root / STAT_FILENAME).touch(exist_ok=True)
        self.stat = StatFile(self.root)
        pass

    def getDomainConfig(self, name):
        pass

    def setDomainConfig(self, name, config):
        pass

    #---------- offline domain operations ----------#
    def create_domain(self, name, config):
        # if exist: return
        # if not config: enter interactive tui
        # fix path existence when create (and touch the stat file)
        # record enabled plugins folder
        # save the config file
        pass

    def update_domain(self, name, config):
        # allow rename the domain (remember to update stat file)
        pass

    def delete_domain(self, name):
        pass

    def list_domain(self, names=[]):
        pass

    pass

def execute(dm, command, args):
    assert( isinstance(dm, DomainManager) )
    if command=='add':
        dm.create_domain(args.name, args.config)
    elif command=='update':
        dm.update_domain(args.name, args.config)
    elif command=='rm':
        dm.delete_domain(args.name)
    elif command=='list':
        dm.list_domain(args.names)
    else:
        print('The command <{}> is not supported.'.format(command))
    pass

def init_subparsers(subparsers):
    #
    p_add = subparsers.add_parser('add',
        help='create a new domain.')
    p_add.add_argument('name', metavar='domain_name',
        help='the domain name.')
    p_add.add_argument('config', metavar='config_file', nargs='*',
        help='(Optional) the path to the configuration file.')
    #
    p_update = subparsers.add_parser('update',
        help='update an existing domain.')
    p_update.add_argument('name', metavar='domain_name',
        help='the domain name.')
    p_update.add_argument('config', metavar='config_file', nargs='*',
        help='(Optional) the path to the configuration file.')
    #
    p_rm = subparsers.add_parser('rm',
        help='remove and existing domain.')
    p_rm.add_argument('name', metavar='domain_name',
        help='the domain name.')
    #
    p_list = subparsers.add_parser('list',
        help='list all available domains.')
    p_list.add_argument('names', metavar='domain_names', nargs='*',
        help='(Optional) only list the specified domains.')
    pass

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(
            description='VDM Domain Manager.')
        subparsers = parser.add_subparsers(dest='command')
        init_subparsers(subparsers)
        #
        args = parser.parse_args()
        dm = DomainManager()
        execute(dm, args.command, args)
    except Exception as e:
        raise e#print(e)
    finally:
        pass#exit()
