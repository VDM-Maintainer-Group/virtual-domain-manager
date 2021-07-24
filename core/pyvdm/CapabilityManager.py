#!/usr/bin/env python3
# fix relative path import
import sys, inspect
from pathlib import Path
sys.path.append( Path(__file__).resolve().parent.as_posix() )
# normal import
import argparse
import tempfile
import pyvdm.core.vdm_capability_daemon as vcd
from pyvdm.core.utils import *
from pyvdm.core.errcode import CapabilityCode as ERR

PARENT_ROOT = Path('~/.vdm').expanduser()
CAPABILITY_DIRECTORY = PARENT_ROOT / 'capability'

class CapabilityManager:
    def __init__(self, root=''):
        if root:
            self.root = Path(root).resolve()
        else:
            self.root = CAPABILITY_DIRECTORY
        self.root.mkdir(exist_ok=True, parents=True) #ensure root existing
        self.temp = Path( tempfile.mkdtemp() )
        pass

    def install(self, url):
        pass

    def uninstall(self, name):
        pass

    def enable(self, name):
        pass

    def disable(self, name):
        pass

    def query(self, name=''):
        pass

    pass

def execute(am, command, args, verbose=False):
    assert( isinstance(am, CapabilityManager) )
    if command=='install':
        return am.install(args.url)
    elif command=='uninstall':
        return am.uninstall(args.name)
    elif command=='enable':
        return am.enable(args.name)
    elif command=='disable':
        return am.disable(args.name)
    elif command=='query':
        return am.query(args.name)
    elif command==None:
        return am.query()
    else:
        print('The command <{}> is not supported.'.format(command))
    return

def init_subparsers(subparsers):
    p_install = subparsers.add_parser('install',
        help='install an external capability library')
    p_install.add_argument('url', metavar='url',
        help='the path to the capability library in .zip format.')
    #
    p_uninstall = subparsers.add_parser('uninstall',
        help='uninstall VDM capability library')
    p_uninstall.add_argument('name', metavar='name',
        help='the capability name')
    #
    p_enable = subparsers.add_parser('enable',
        help='enable an installed capability.')
    p_enable.add_argument('name', metavar='name',
        help='the capability name')
    #
    p_disable = subparsers.add_parser('disable',
        help='disable an installed capability.')
    p_disable.add_argument('name', metavar='name',
        help='the capability name')
    #
    p_query = subparsers.add_parser('query',
        help='query the status of installed capability.')
    p_query.add_argument('name', metavar='name', nargs='?',
        help='the capability name')
    pass

if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(
            description='VDM Capability Manager.')
        subparsers = parser.add_subparsers(dest='command')
        init_subparsers(subparsers)
        #
        args = parser.parse_args()
        am = CapabilityManager()
        ret = execute(am, args.command, args)
        if isinstance(ret, ERR):
            raise Exception(ret.name)
    except Exception as e:
        raise e#pass
    finally:
        pass#exit()