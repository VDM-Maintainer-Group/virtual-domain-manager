#!/usr/bin/env python3
# fix relative path import
import sys, inspect
from pathlib import Path
sys.path.append( Path(__file__).resolve().parent.as_posix() )
# normal import
import os, psutil, argparse
import tempfile, shutil
import subprocess as sp
from pyvdm.daemon.vdm_capability_daemon import CapabilityDaemon
from pyvdm.core.utils import *
from pyvdm.core.errcode import CapabilityCode as ERR

PARENT_ROOT = Path('~/.vdm').expanduser()
CAPABILITY_DIRECTORY = PARENT_ROOT / 'capability'

def _start_daemon(root):
    CapabilityDaemon( root ).start_daemon()

class CapabilityManager:
    def __init__(self, root=''):
        if root:
            self.root = Path(root).resolve()
        else:
            self.root = CAPABILITY_DIRECTORY
        self.root.mkdir(exist_ok=True, parents=True) #ensure root existing
        self.temp = Path( tempfile.mkdtemp() )
        pass

    def install(self, url:str) -> ERR:
        url = Path(url)
        #
        if url.is_file():
            try:
                tmp_dir = self.temp / url.name
                shutil.unpack_archive( url.as_posix(), tmp_dir.as_posix() )
                _path = tmp_dir
            except:
                return ERR.ARCHIVE_UNPACK_FAILED
        elif url.is_dir():
            _path = url.expanduser().resolve()
        else:
            return ERR.URL_PARSE_FAILURE
        #
        vcd = CapabilityDaemon( root=self.root.as_posix() )
        ret = vcd.install( _path.as_posix() )
        if ret:
            print(ret)
            return ERR.VCD_INTERNAL_ERROR
        else:
            return ERR.ALL_CLEAN

    def uninstall(self, name:str) -> ERR:
        vcd = CapabilityDaemon( root=self.root.as_posix() )
        ret = vcd.uninstall(name)
        if ret:
            print(ret)
            return ERR.VCD_INTERNAL_ERROR
        else:
            return ERR.ALL_CLEAN

    def enable(self, name:str) -> ERR:
        vcd = CapabilityDaemon( root=self.root.as_posix() )
        ret = vcd.enable(name)
        if ret:
            print(ret)
            return ERR.VCD_INTERNAL_ERROR
        else:
            return ERR.ALL_CLEAN

    def disable(self, name) -> ERR:
        vcd = CapabilityDaemon( root=self.root.as_posix() )
        ret = vcd.disable(name)
        if ret:
            print(ret)
            return ERR.VCD_INTERNAL_ERROR
        else:
            return ERR.ALL_CLEAN

    def query(self, name='') -> str:
        vcd = CapabilityDaemon( root=self.root.as_posix() )
        ret = vcd.query(name)
        print(ret)
        return ret

    def daemon(self, option) -> ERR:
        name = 'VDM-Capability-Daemon'
        proc_iter = psutil.process_iter(attrs=['cmdline', 'pid'])
        proc = next( (x for x in proc_iter if name in ' '.join(x.info['cmdline'])), '' )
        #
        def _start(force=False):
            if proc and not force:
                return ERR.DAEMON_ALREADY_EXISTS
            _file = (self.temp/name).as_posix()
            with open(_file, 'w') as f:
                f.write('import sys; import pyvdm.core.CapabilityManager as A_MAN; A_MAN._start_daemon(sys.argv[1])')
            sp.Popen(['python3', _file, self.root.as_posix()])
            return ERR.ALL_CLEAN
        def _stop():
            if proc:
                psutil.Process( proc.info['pid'] ).terminate()
            return ERR.ALL_CLEAN
        def _restart():
            _stop(); _start(True)
            return ERR.ALL_CLEAN
        def _status():
            return ERR.DAEMON_IS_RUNNING if proc else ERR.DAEMON_IS_STOPPED
        #
        return {'start':_start, 'stop':_stop, 'restart':_restart, 'status':_status}.get(option)()

    pass

def execute(am, command, args, verbose=False):
    assert( isinstance(am, CapabilityManager) )
    if command=='daemon':
        return am.daemon(args.option)
    elif command=='install':
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
    p_daemon = subparsers.add_parser('daemon',
        help='capability daemon manipulation.')
    p_daemon.add_argument('option', metavar='option', choices=['start','status','stop','restart'],
        help='[start,stop,restart,status]')
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