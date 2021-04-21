#!/usr/bin/env python3
# fix relative path import
from core.pyvdm.errcode import ErrorCode
import sys
from pathlib import Path
sys.path.append( Path(__file__).resolve().parent.as_posix() )
# normal import
import os, argparse, re
import tempfile, shutil
import pyvdm.core.PluginManager as P_MAN
import pyvdm.core.DomainManager as D_MAN
from pyvdm.core.utils import *
from pyvdm.core.errcode import *

PARENT_ROOT = Path('~/.vdm').expanduser()
PLUGIN_DIRECTORY = PARENT_ROOT / 'plugins'
DOMAIN_DIRECTORY = PARENT_ROOT / 'domains'

class CoreManager:
    def __init__(self):
        self.root = DOMAIN_DIRECTORY
        self.root.mkdir(exist_ok=True, parents=True)
        #
        self.stat = StatFile(PARENT_ROOT)
        self.dm = D_MAN.DomainManager(DOMAIN_DIRECTORY)
        self.pm = P_MAN.PluginManager(PLUGIN_DIRECTORY)
        #
        _domain = self.stat.getStat()
        if _domain:
            self.load(_domain)
        pass

    def load(self, name):
        if hasattr(self, 'plugins'):
            del self.plugins #cleanup
        self.plugins = dict()
        #
        _config = self.dm.getDomainConfig(name)
        if isinstance(_config, DomainCode):
            return _config
        _config = _config['plugins']
        for _name,_ver in _config.items():
            _item = self.pm.getInstalledPlugin(_name, _ver)
            if isinstance(_item, PluginCode):
                return _item #return plugin error code
            _stat   = StatFile(DOMAIN_DIRECTORY/name, _name)
            self.plugins.update( {_item: _stat} )
        return True

    #---------- online domain operations -----------#
    def save_domain(self, delayed=False):
        if not self.stat.getStat():
            return (DomainCode.DOMAIN_NOT_OPEN, '')
        # save to current open domain
        for _plugin,_stat in self.plugins.items():
            if _plugin.onSave( _stat.getFile() ) < 0:
                return (DomainCode.DOMAIN_SAVE_FAILED, _plugin.name)
            if not delayed: _stat.putFile()
            pass
        return True

    def open_domain(self, name):
        ret = self.load(name)
        if ret is not True:
            return (DomainCode.DOMAIN_LOAD_FAILED, ret)
        # onStart --> onResume
        for _plugin,_ in self.plugins.items():
            if _plugin.onStart() < 0:
                return (DomainCode.DOMAIN_START_FAILED, _plugin.name)
        for _plugin,_stat in self.plugins.items():
            if _plugin.onResume( _stat.getFile() ) < 0:
                return (DomainCode.DOMAIN_RESUME_FAILED, _plugin.name)
        # put new stat
        self.stat.putStat(name)
        return True

    def close_domain(self):
        if not self.stat.getStat():
            return (DomainCode.DOMAIN_NOT_OPEN, '')
        # onClose --> onStop
        for _plugin,_stat in self.plugins.items():
            if _plugin.onClose() < 0:
                return (DomainCode.DOMAIN_CLOSE_FAILED, _plugin.name)
            if _plugin.onStop() < 0:
                return (DomainCode.DOMAIN_STOP_FAILED, _plugin.name)
        # put empty stat
        self.stat.putStat('')
        return True

    def switch_domain(self, name):
        if not self.stat.getStat():
            ret = self.open_domain(name)
            if ret is not True: return ret
        else:
            #TODO: restore, if re-open the same domain and the stat files changed
            ret = self.save_domain()
            if ret is not True: return ret
            #
            ret = self.close_domain()
            if ret is not True: return ret
            #
            ret = self.open_domain(name)
            if ret is not True: return ret
        return True

    pass

def execute(command, args):
    if command=='domain':
        dm = D_MAN.DomainManager(DOMAIN_DIRECTORY)
        return D_MAN.execute(dm, args.domain_command, args)
    
    if command=='plugin':
        pm = P_MAN.PluginManager(PLUGIN_DIRECTORY)
        return P_MAN.execute(pm, args.plugin_command, args)

    cm = CoreManager()
    if args.save_flag:
        return cm.save_domain()
    elif args.close_flag:
        return cm.close_domain()
    elif args.domain_name:
        return cm.switch_domain(args.domain_name)
    else:
        print('<Current Domain Status>')
    return

def main():
    parser = argparse.ArgumentParser(
        description = 'The VDM Core.'
    )
    parser.add_argument('--save', dest='save_flag', action='store_true',
        help='save the current open domain.')
    parser.add_argument('--open', dest='domain_name',
        help='open an existing domain.')
    parser.add_argument('--close', dest='close_flag', action='store_true',
        help='close the current open domain.')
    subparsers = parser.add_subparsers(dest='command')

    # domain_manager
    dm_parser = subparsers.add_parser('domain',
        help='Call VDM Domain Manager.')
    dm_subparsers = dm_parser.add_subparsers(dest='domain_command')
    D_MAN.init_subparsers(dm_subparsers)

    # plugin_manager
    pm_parser = subparsers.add_parser('plugin',
        help='Call VDM Plugin Manager.')
    pm_subparsers = pm_parser.add_subparsers(dest='plugin_command')
    P_MAN.init_subparsers(pm_subparsers)

    # sync_manager
    #TODO: add sync_manager    
    
    args = parser.parse_args()
    ret = execute(args.command, args)
    if isinstance(ret, ErrorCode):
        raise Exception( '%s: %s'%(type(ret).__name__, ret.name) )
    pass

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        raise e#print(e)
    finally:
        pass#exit()
