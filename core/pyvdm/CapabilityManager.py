#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path
import psutil
import requests
import shutil
import subprocess as sp
import tempfile
from urllib.parse import urlparse

from pyvdm.daemon.vdm_capability_daemon import CapabilityDaemon
from pyvdm.core.utils import (POSIX, )
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

        os.environ['VDM_CAPABILITY_OUTPUT_DIRECTORY'] = self.temp.as_posix()
        os.environ['VDM_CAPABILITY_INSTALL_DIRECTORY'] = self.root.as_posix()
        pass

    def install(self, url:str) -> ERR:
        from pyvdm.build import sbs_entry as sbs

        ## check if url is local
        if urlparse(url).scheme in ['http', 'https']:
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write( requests.get(url).content )
                _path = Path(f.name)
        elif urlparse(url).scheme in ['file', '']:
            _path = Path(url).expanduser().resolve()
        else:
            return ERR.URL_PARSE_FAILURE
        ## check if url is archive
        if _path.is_file():
            try:
                tmp_dir = self.temp / _path.name
                shutil.unpack_archive( _path.as_posix(), tmp_dir.as_posix() )
                _path = tmp_dir
            except:
                return ERR.ARCHIVE_UNPACK_FAILED
        elif _path.is_dir():
            _path = _path.expanduser().resolve()
        else:
            return ERR.URL_PARSE_FAILURE
        ##
        ret = sbs('install', [_path.as_posix()])
        if ret and ret[0]==True:
            return ERR.ALL_CLEAN
        else:
            print(ret)
            return ERR.VCD_INTERNAL_ERROR

    def uninstall(self, name:str) -> ERR:
        from pyvdm.build import sbs_entry as sbs

        ret = sbs('uninstall', [name])
        if ret and ret[0]==True:
            return ERR.ALL_CLEAN
        else:
            print(ret)
            return ERR.VCD_INTERNAL_ERROR

    def enable(self, name:str) -> ERR:
        vcd = CapabilityDaemon( root=self.root.as_posix() )
        ret = vcd.enable(name)
        if ret:
            print(ret)
            return ERR.VCD_INTERNAL_ERROR
        else:
            return ERR.ALL_CLEAN

    def disable(self, name:str) -> ERR:
        vcd = CapabilityDaemon( root=self.root.as_posix() )
        ret = vcd.disable(name)
        if ret:
            print(ret)
            return ERR.VCD_INTERNAL_ERROR
        else:
            return ERR.ALL_CLEAN

    def status(self, name=''): #-> str or dict
        vcd = CapabilityDaemon( root=self.root.as_posix() )
        if not name:
            ret = dict()
            for name,_,content in os.walk(CAPABILITY_DIRECTORY):
                if '.conf' in content:
                    _name = Path(name).name
                    ret.update({
                        _name : {
                            "name": _name,
                            "status": vcd.query(name)
                        }
                    })
            pass
        else:
            ret = vcd.query(name)
        return ret

    def daemon(self, option) -> ERR:
        name = 'VDM-Capability-Daemon'
        proc_iter = psutil.process_iter(attrs=['cmdline', 'pid'])
        proc = next( (x for x in proc_iter if name in ' '.join(x.info['cmdline'])), '' ) #type: ignore
        ##
        def _start(force=False) -> ERR:
            if proc and not force:
                return ERR.DAEMON_ALREADY_EXISTS
            _file = (self.temp/name).as_posix()
            with open(_file, 'w') as f:
                f.write('import sys; import pyvdm.core.CapabilityManager as C_MAN; C_MAN._start_daemon(sys.argv[1])')
            sp.Popen(['python3', _file, self.root.as_posix()])
            return ERR.ALL_CLEAN
        ##
        def _stop() -> ERR:
            if proc:
                psutil.Process( proc.info['pid'] ).terminate() #type: ignore
            return ERR.ALL_CLEAN
        ##
        def _restart() -> ERR:
            _stop(); _start(True)
            return ERR.ALL_CLEAN
        ##
        def _status() -> ERR:
            return ERR.DAEMON_IS_RUNNING if proc else ERR.DAEMON_IS_STOPPED
        ##
        return {'start':_start, 'stop':_stop, 'restart':_restart, 'status':_status}[option]()

    pass

def execute(cm, command, args, verbose=False):
    assert( isinstance(cm, CapabilityManager) )
    if command=='daemon':
        return cm.daemon(args.option)
    elif command=='install':
        return cm.install(args.url)
    elif command=='uninstall':
        return cm.uninstall(args.name)
    elif command=='enable':
        return cm.enable(args.name)
    elif command=='disable':
        return cm.disable(args.name)
    elif command=='status':
        ret = cm.status(args.name)
        print( json.dumps(ret, indent=4) )
        return ret
    elif command==None:
        return cm.status()
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
    p_status = subparsers.add_parser('status',
        help='query the status of the installed capability(s).')
    p_status.add_argument('name', metavar='name', nargs='?', default='',
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
        cm = CapabilityManager()
        ret = execute(cm, args.command, args)
        if isinstance(ret, ERR):
            raise Exception(ret.name)
    except Exception as e:
        raise e#pass
    finally:
        pass#exit()