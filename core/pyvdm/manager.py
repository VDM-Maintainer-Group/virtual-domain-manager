#!/usr/bin/env python3
# fix relative path import
import sys
from pathlib import Path
sys.path.append( Path(__file__).resolve().parent.as_posix() )
# normal import
import os, argparse, re
import tempfile, shutil
import concurrent.futures
import pyvdm.core.PluginManager as P_MAN
import pyvdm.core.DomainManager as D_MAN
import pyvdm.core.CapabilityManager as C_MAN
import pyvdm.core.ApplicationManager as A_MAN
from pyvdm.core.utils import *
from pyvdm.core.errcode import *

try:
    from .. import __version__
except:
    __version__ = '0.0.0'

PARENT_ROOT = Path('~/.vdm').expanduser()
PLUGIN_DIRECTORY = PARENT_ROOT / 'plugins'
DOMAIN_DIRECTORY = PARENT_ROOT / 'domains'
CAPABILITY_DIRECTORY = PARENT_ROOT / 'capability'

class CoreManager:
    def __init__(self):
        self.root = DOMAIN_DIRECTORY
        self.root.mkdir(exist_ok=True, parents=True)
        #
        self.stat = StatFile(PARENT_ROOT)
        self.dm = D_MAN.DomainManager(DOMAIN_DIRECTORY)
        self.pm = P_MAN.PluginManager(PLUGIN_DIRECTORY)
        self.cm = C_MAN.CapabilityManager(CAPABILITY_DIRECTORY)
        self.am = A_MAN.ApplicationManager(PARENT_ROOT, self.pm)
        #
        _domain = self.stat.getStat()
        if _domain:
            self.open_domain(_domain)
        pass

    def load(self, name):
        ## load config
        _config = self.dm.getDomainConfig(name)
        if isinstance(_config, DomainCode):
            return _config
        ## cleanup old plugins
        if hasattr(self, 'plugins'):
            del self.plugins #cleanup
        self.plugins = dict()
        ## load GUI APP plugins
        for _name in _config['applications']:
            _plugin = self.am.instantiate_plugin(_name)
            if isinstance(_plugin, PluginCode):
                return _plugin #return plugin error code
            _stat = StatFile(DOMAIN_DIRECTORY/name, _name)
            self.plugins.update( {_plugin: _stat} )
            pass
        ## load other plugins
        for _name,_ver in _config['plugins'].items():
            _plugin = self.pm.getInstalledPlugin(_name, _ver)
            if isinstance(_plugin, PluginCode):
                return _plugin #return plugin error code
            _stat   = StatFile(DOMAIN_DIRECTORY/name, _name)
            self.plugins.update( {_plugin: _stat} )
        return True

    #---------- online domain operations -----------#
    def executeBlade(self, executor, worker):
        _futures = [ executor.submit(worker, _plugin, _stat) 
                    for _plugin,_stat in self.plugins.items() ]
        ##
        try:
            _results = [ x.result() for x in _futures ]
            _results = list( filter(lambda x:x is not None, _results) )
        except Exception as e:
            return _results
        else:
            _results = None if len(_results)==0 else _results
            return _results
        pass

    def save_domain(self, delayed=False):
        if not self.stat.getStat():
            return (DomainCode.DOMAIN_NOT_OPEN, '')
        # save to current open domain
        with concurrent.futures.ThreadPoolExecutor() as executor:
            def _worker(plugin, stat):
                if plugin.onSave( stat.getFile() ) < 0:
                    return (DomainCode.DOMAIN_SAVE_FAILED, plugin.name)
                else:
                    if not delayed: stat.putFile()
                    return None
            #
            results = self.executeBlade(executor, _worker)
            if results: return results
            return True

    def open_domain(self, name):
        ret = self.load(name)
        if ret is not True:
            return (DomainCode.DOMAIN_LOAD_FAILED, ret)
        # onStart --> onResume
        with concurrent.futures.ThreadPoolExecutor() as executor:
            def _worker(plugin, stat):
                if plugin.onStart() < 0:
                    return (DomainCode.DOMAIN_START_FAILED, plugin.name)
                if plugin.onResume( stat.getFile() ) < 0:
                    return (DomainCode.DOMAIN_RESUME_FAILED, plugin.name)
                return None
            #
            results = self.executeBlade(executor, _worker)
            if results: return results
            # put new stat
            self.stat.putStat(name)
            return True

    def close_domain(self):
        if not self.stat.getStat():
            return (DomainCode.DOMAIN_NOT_OPEN, '')
        # onClose --> onStop
        with concurrent.futures.ThreadPoolExecutor() as executor:
            def _worker(plugin, stat):
                if plugin.onClose() < 0:
                    return (DomainCode.DOMAIN_CLOSE_FAILED, plugin.name)
                if plugin.onStop() < 0:
                    return (DomainCode.DOMAIN_STOP_FAILED, plugin.name)
            #
            results = self.executeBlade(executor, _worker)
            if results: return results
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
    if command in ['domain', 'dm']:
        dm = D_MAN.DomainManager(DOMAIN_DIRECTORY)
        return D_MAN.execute(dm, args.domain_command, args)
    
    if command in ['plugin', 'pm']:
        pm = P_MAN.PluginManager(PLUGIN_DIRECTORY)
        return P_MAN.execute(pm, args.plugin_command, args)

    if command in ['capability', 'cm']:
        cm = C_MAN.CapabilityManager(CAPABILITY_DIRECTORY)
        return C_MAN.execute(cm, args.capability_command, args)

    if command in ['application', 'am']:
        am = A_MAN.ApplicationManager(PARENT_ROOT)
        return A_MAN.execute(am, args.application_command, args)

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
    parser.add_argument('-V', '--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('--open', dest='domain_name', metavar='domain',
        help='open an existing domain')
    parser.add_argument('--save', dest='save_flag', action='store_true',
        help='save the current open domain')
    parser.add_argument('--close', dest='close_flag', action='store_true',
        help='close the current open domain')
    subparsers = parser.add_subparsers(dest='command')

    # domain_manager
    dm_parser = subparsers.add_parser('domain', aliases=['dm'],
        help='Call VDM Domain Manager.')
    dm_subparsers = dm_parser.add_subparsers(dest='domain_command')
    D_MAN.init_subparsers(dm_subparsers)

    # plugin_manager
    pm_parser = subparsers.add_parser('plugin', aliases=['pm'],
        help='Call VDM Plugin Manager.')
    pm_subparsers = pm_parser.add_subparsers(dest='plugin_command')
    P_MAN.init_subparsers(pm_subparsers)

    # capability_manager
    cm_parser = subparsers.add_parser('capability', aliases=['cm'],
        help='Call VDM Capability Manager.')
    cm_subparsers = cm_parser.add_subparsers(dest='capability_command')
    C_MAN.init_subparsers(cm_subparsers)

    # application_manager
    am_parser = subparsers.add_parser('application', aliases=['am'],
        help='Call VDM Application Manager.')
    am_subparsers = am_parser.add_subparsers(dest='application_command')
    A_MAN.init_subparsers(am_subparsers)

    # sync_manager
    #TODO: add sync_manager    
    
    args = parser.parse_args()
    ret = execute(args.command, args)
    if isinstance(ret, ErrorCode):
        print( '%s: %s'%(type(ret).__name__, ret.name) )
    pass

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        raise e#print(e)
    finally:
        pass#exit()
