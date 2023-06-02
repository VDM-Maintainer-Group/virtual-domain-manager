#!/usr/bin/env python3
import argparse
import concurrent.futures
import json
import os
from pathlib import Path
import traceback

import pyvdm.core.PluginManager as P_MAN
import pyvdm.core.DomainManager as D_MAN
import pyvdm.core.CapabilityManager as C_MAN
import pyvdm.core.ApplicationManager as A_MAN
from pyvdm.core.utils import (POSIX, StatFile)
from pyvdm.core.errcode import (ErrorCode, DomainCode, PluginCode)
from pyvdm.interface import SRC_API

try:
    from .. import __version__ # type: ignore
except:
    __version__ = '0.0.0'

VDM_HOME = Path('~/.vdm').expanduser()
PLUGIN_DIRECTORY = VDM_HOME / 'plugins'
DOMAIN_DIRECTORY = VDM_HOME / 'domains'
CAPABILITY_DIRECTORY = VDM_HOME / 'capability'

class CoreMetaPlugin(SRC_API):
    def __init__(self):
        from pyvdm.interface import CapabilityLibrary
        self.xm = CapabilityLibrary.CapabilityHandleLocal('x11-manager')

    def onStart(self): pass
    def onStop(self): pass
    def onClose(self): pass

    def onSave(self, stat_file):
        record = {
            'current_desktop': self.xm.get_current_desktop()
        }
        with open(stat_file, 'w') as f:
            json.dump(record, f)
        return 0

    def onResume(self, stat_file, new=False):
        ## load stat file with failure check
        with open(stat_file, 'r') as f:
            _file = f.read().strip()
        if len(_file)==0:
            return 0
        else:
            try:
                record = json.loads(_file)
            except:
                return -1
        ##
        self.xm.set_current_desktop( record['current_desktop'] )
        return 0

    pass

class CoreManager:
    def __init__(self):
        self.root = DOMAIN_DIRECTORY
        self.root.mkdir(exist_ok=True, parents=True)
        #
        self.dm = D_MAN.DomainManager( POSIX(DOMAIN_DIRECTORY) )
        self.cm = C_MAN.CapabilityManager( POSIX(CAPABILITY_DIRECTORY) )
        self.pm = P_MAN.PluginManager( POSIX(PLUGIN_DIRECTORY), self.cm )
        self.am = A_MAN.ApplicationManager( POSIX(VDM_HOME), self.pm )
        #
        _domain = self.dm.open_domain_name
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
        ## load global CoreMetaPlugin
        global_plugin = CoreMetaPlugin()
        global_stat   = StatFile(DOMAIN_DIRECTORY/name, '.global')
        self.plugins.update({ global_plugin : global_stat })

        return PluginCode.ALL_CLEAN

    #---------- online domain operations -----------#
    def executeBlade(self, executor, worker):
        _futures = [ executor.submit(worker, _plugin, _stat) 
                    for _plugin,_stat in self.plugins.items() ]
        ##
        results = list()
        for task in _futures:
            try:
                ret = task.result()
                if ret is not None:
                    results.append(ret)
            except Exception as e:
                print( traceback.format_exc() )
        results = None if len(results)==0 else results
        return results

    def save_domain(self, delayed=False) -> tuple:
        if not self.dm.open_domain_name:
            return (DomainCode.DOMAIN_NOT_OPEN, '')
        # save to current open domain
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                def _worker(plugin, stat):
                    if plugin.onSave( stat.getFile() ) < 0:
                        return (DomainCode.DOMAIN_SAVE_FAILED, plugin.name)
                    else:
                        if not delayed: stat.putFile()
                        return None
                #
                results = self.executeBlade(executor, _worker)
                if results: raise Exception( str(results) )
                return (DomainCode.ALL_CLEAN, '')
        except:
            return (DomainCode.DOMAIN_SAVE_FAILED, traceback.format_exc())

    def open_domain(self, name) -> tuple:
        ## prepare domain
        ret_code = self.dm.initialize_domain(name)
        if ret_code is not DomainCode.ALL_CLEAN:
            return (DomainCode.DOMAIN_START_FAILED, hex(ret_code)) #type: ignore
        ## load domain-specific plugins
        ret = self.load(name)
        if ret is not PluginCode.ALL_CLEAN:
            return (DomainCode.DOMAIN_LOAD_FAILED, ret)
        ## onStart --> onResume
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                def _worker(plugin, stat):
                    if plugin.onStart() < 0:
                        return (DomainCode.DOMAIN_START_FAILED, plugin.name)
                    if plugin.onResume( stat.getFile() ) < 0:
                        return (DomainCode.DOMAIN_RESUME_FAILED, plugin.name)
                    return None
                #
                results = self.executeBlade(executor, _worker)
                if results: raise Exception( str(results) )
                return (DomainCode.ALL_CLEAN, '')
        except:
            self.dm.finalize_domain()
            return (DomainCode.DOMAIN_START_FAILED, traceback.format_exc())
        pass

    def close_domain(self):
        if not self.dm.open_domain_name:
            return (DomainCode.DOMAIN_NOT_OPEN, '')
        # onClose --> onStop
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                def _worker(plugin, stat):
                    if plugin.onClose() < 0:
                        return (DomainCode.DOMAIN_CLOSE_FAILED, plugin.name)
                    if plugin.onStop() < 0:
                        return (DomainCode.DOMAIN_STOP_FAILED, plugin.name)
                #
                results = self.executeBlade(executor, _worker)
                if results: raise Exception( str(results) )
                self.dm.finalize_domain()
                return (DomainCode.ALL_CLEAN, '')
        except:
            return (DomainCode.DOMAIN_CLOSE_FAILED, traceback.format_exc())
        pass

    def switch_domain(self, name):
        if not self.dm.open_domain_name:
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
    if command=='run':
        _stat = StatFile(VDM_HOME).getStat()
        if _stat['name']:
            uid, gid = os.getuid(), os.getgid()
            target_pid = str(_stat['pid'])
            execute_command_line = ' '.join(args.execute_command_line)
            os.execl('/usr/bin/nsenter',
                     '/usr/bin/nsenter', '--preserve-credentials', '-U','-m','-C','-p', '-t', target_pid, '--',
                     '/usr/bin/unshare', f'--map-group={uid}', f'--map-user={gid}', '--',
                     *args.execute_command_line)
        else:
            os.execl( args.execute_command_line[0], *args.execute_command_line )
        pass

    if command in ['domain', 'dm']:
        dm = D_MAN.DomainManager( POSIX(DOMAIN_DIRECTORY) )
        return D_MAN.execute(dm, args.domain_command, args)
    
    if command in ['plugin', 'pm']:
        pm = P_MAN.PluginManager( POSIX(PLUGIN_DIRECTORY) )
        return P_MAN.execute(pm, args.plugin_command, args)

    if command in ['capability', 'cm']:
        cm = C_MAN.CapabilityManager( POSIX(CAPABILITY_DIRECTORY) )
        return C_MAN.execute(cm, args.capability_command, args)

    if command in ['application', 'am']:
        am = A_MAN.ApplicationManager( POSIX(VDM_HOME) )
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

    # run
    run_parser = subparsers.add_parser('run', help='Run specified application.')
    run_parser.add_argument('execute_command_line', nargs=argparse.REMAINDER,
        help='execute command line')

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
