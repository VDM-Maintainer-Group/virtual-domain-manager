#!/usr/bin/env python3
# fix relative path import
import sys
from pathlib import Path
sys.path.append( Path(__file__).resolve().parent.as_posix() )
# normal import
import os, argparse, re
import tempfile, shutil
import pyvdm.core.PluginManager as P_MAN
import pyvdm.core.DomainManager as D_MAN
from pyvdm.core.utils import *

PARENT_ROOT = Path('~/.vdm').expanduser()
PLUGIN_DIRECTORY = PARENT_ROOT / 'plugins'
DOMAIN_DIRECTORY = PARENT_ROOT / 'domains'

class CoreManager:
    def __init__(self):
        self.root = DOMAIN_DIRECTORY
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
        _config = self.dm.getDomainConfig(name)['plugins']
        for _name,_ver in _config.items():
            _plugin = self.pm.getInstalledPlugin(_name, _ver)
            _stat   = StatFile(DOMAIN_DIRECTORY, _name)
            self.plugins.update( {_plugin: _stat} )
        pass

    #---------- online domain operations -----------#
    def save_domain(self, delayed=False):
        if not self.stat.getStat():
            return
        # save to current open domain
        for _plugin,_stat in self.plugins.items():
            _plugin.onSave( _stat.getFile() )
            if not delayed: _stat.putFile()
            pass
        pass

    def open_domain(self, name):
        self.load(name)
        # onStart --> onResume
        for _plugin,_ in self.plugins.items():
            _plugin.onStart()
        for _plugin,_stat in self.plugins.items():
            _plugin.onResume( _stat.getFile() )
        # put new stat
        self.stat.putStat(name)
        pass

    def close_domain(self):
        if not self.stat.getStat():
            return # no open domain
        # onClose --> onStop
        for _plugin,_stat in self.plugins.items():
            _plugin.onClose()
            _plugin.onStop()
        # put empty stat
        self.stat.putStat('')
        pass

    def switch_domain(self, name):
        if not self.stat.getStat():
            self.open_domain(name)
        else:
            #TODO: restore, if re-open the same domain and the stat files changed
            self.save_domain()
            self.close_domain()
            self.open_domain(name)
        pass

    pass

def execute(command, args):
    if command=='domain':
        dm = D_MAN.DomainManager(DOMAIN_DIRECTORY)
        D_MAN.execute(dm, args.domain_command, args)
        return
    
    if command=='plugin':
        pm = P_MAN.PluginManager(PLUGIN_DIRECTORY)
        P_MAN.execute(pm, args.plugin_command, args)
        return

    cm = CoreManager()
    if args.save_flag:
        cm.save_domain()
    elif args.close_flag:
        cm.close_domain()
    elif args.domain_name:
        cm.switch_domain(args.domain_name)
    else:
        print('<Current Domain Status>')
    pass

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
    execute(args.command, args)
    pass

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        raise e#print(e)
    finally:
        pass#exit()
