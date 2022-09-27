#!/usr/bin/env python3
import os, json
import dbus
import time, psutil
import argparse
import subprocess as sp
from pathlib import Path
from configparser import RawConfigParser
import pyvdm.core.PluginManager as P_MAN
from pyvdm.core.PluginManager import MetaPlugin
from pyvdm.core.errcode import ApplicationCode as ERR
from pyvdm.interface import CapabilityLibrary

PARENT_ROOT = Path('~/.vdm').expanduser()
HINT_GENERATED = '(auto-generated)'

def _non_gui_filter(conf) -> bool:
    _flag = False
    _flag = _flag or 'NoDisplay' in conf['Desktop Entry']
    _flag = _flag or 'OnlyShowIn' in conf['Desktop Entry']
    _flag = _flag or 'NotShowIn' in conf['Desktop Entry']
    _flag = _flag or ('Terminal' in conf['Desktop Entry'] and conf['Desktop Entry']['Terminal']=='true')
    return _flag

def _compatibility_filter(conf) -> bool:
    if 'Categories' in conf['Desktop Entry']:
        _cat = conf['Desktop Entry']['Categories'].split(';')
        return ('VDM' in _cat)
    else:
        return False
    pass

class DefaultCompatibility:
    def __init__(self, name, conf):
        self.name = name
        self.conf = conf
        self.xm = CapabilityLibrary.CapabilityHandleLocal('x11-manager')
        pass

    def onClose(self):
        os.system(f'killall {self.cmd}')
    
    def onSave(self, stat_file):
        record = list()
        ##
        for proc in psutil.process_iter(['name', 'pid', 'cmdline']):
            if proc.name==self.name:
                _windows = self.xm.get_windows_by_pid(proc.pid)
                if len(_windows)==1: #only record one-to-one (pid,xid) mapping
                    record.append({
                        'cmdline': proc.cmdline,
                        'window': {
                            'desktop': _windows[0]['desktop'],
                            'states':  _windows[0]['states'],
                            'xyhw':    _windows[0]['xyhw']
                        }
                    })
            pass
        ##
        with open(stat_file, 'w') as f:
            json.dump(record, f)
        pass

    def onResume(self, stat_file):
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
        ## rearrange windows by pid
        for item in record:
            proc = sp.Popen(item['cmdline'], start_new_session=True)
            time.sleep(0.1)
            ##
            _window = self.xm.get_windows_by_pid(proc.pid)[0]
            sp = record['window']
            self.xm.set_window_by_xid(_window['xid'], sp['desktop'], sp['states'], sp['xyhw'])
        pass

    pass

class CompatibleInterface:
    def __init__(self, sess, dbus_name) -> None:
        self.dbus_name = dbus_name
        self.dbus_iface = dbus.Interface(
            sess.get_object('org.freedesktop.DBus', '/'), 'org.freedesktop.DBus')
        self.node = sess.get_object(dbus_name, '/')
        self.iface = dbus.Interface(self.node, 'org.vdm-compatible.src')
        self.props_iface = dbus.Interface(self.node, 'org.freedesktop.DBus.Properties')
        pass

    @property
    def xid(self):
        return self.props_iface.Get('org.vdm-compatible.src', 'xid')
    
    @property
    def pid(self):
        return self.dbus_iface.GetConnectionUnixProcessID(self.dbus_name)

    def Save(self) -> str:
        return self.iface.Save()
    
    def Resume(self, stat:str):
        self.iface.Resume(stat)
    
    def Close(self):
        self.iface.Close()
    pass

class ProbedCompatibility:
    def __init__(self, name, conf):
        self.name = name
        self.conf = conf
        self.xm = CapabilityLibrary.CapabilityHandleLocal('x11-manager')
        pass
    
    @property
    def app_ifaces(self):
        sess = dbus.SessionBus()
        _names = filter(lambda x:f'org.vdm-compatible.{self.name}' in x, sess.list_names())
        app_ifaces = [ CompatibleInterface(sess, x) for x in _names ]
        return app_ifaces

    def onSave(self, stat_file):
        record = list()
        for app in self.app_ifaces:
            if not app.xid:
                _window = self.xm.get_windows_by_pid(app.pid)[0]
            else:
                _window = self.xm.get_windows_by_xid(app.xid)[0]
            ##
            record.append({
                'stat': app.Save(),
                'window': {
                    'desktop': _window['desktop'],
                    'states':  _window['states'],
                    'xyhw':    _window['xyhw']
                }
            })
        ##
        with open(stat_file, 'w') as f:
            json.dump(record, f)
        pass
    
    def onResume(self, stat_file):
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
        
        old_stats = { x.Save():x for x in self.app_ifaces }
        new_stats = { x['stat']:x['window'] for x in record }
        ## keep no-change-needed windows
        _remaining = dict()
        for stat,sp in new_stats.items():
            if stat in old_stats:
                app = old_stats.pop(stat)
                if not app.xid:
                    _window = self.xm.get_windows_by_pid(app.pid)[0]
                else:
                    _window = self.xm.get_windows_by_xid(app.xid)[0]
                self.xm.set_window_by_xid(_window['xid'], sp['desktop'], sp['states'], sp['xyhw'])
            else:
                _remaining.update({ stat : sp })
        ## manipulate with the remaining
        if _remaining:
            ## create new windows
            for _ in range( len(_remaining)-len(old_stats) ):
                sp.Popen(self.conf['exec'], start_new_session=True)
                time.sleep(0.1)
            ## resume stats and window positions
            for (stat,sp), app in zip(_remaining.items(), self.app_ifaces):
                app.Resume(stat)
                if not app.xid:
                    _window = self.xm.get_windows_by_pid(app.pid)[0]
                else:
                    _window = self.xm.get_windows_by_xid(app.xid)[0]
                self.xm.set_window_by_xid(_window['xid'], sp['desktop'], sp['states'], sp['xyhw'])
        else:
            ## close the no-needed old windows
            for app in old_stats.values():
                app.Close()
        pass

    def onClose(self):
        for app in self.app_ifaces:
            app.Close()
        pass

    pass

class ApplicationManager:
    @staticmethod
    def list_all_applications() -> dict:
        applications = dict()
        ##
        data_dirs = os.environ['XDG_DATA_DIRS'].split(':')
        for xdg_path in data_dirs:
            app_dir = Path(xdg_path) / 'applications'
            if app_dir.exists():
                for app_file in app_dir.glob('*.desktop'):
                    app_conf = RawConfigParser(allow_no_value=True, default_section='Desktop Entry', strict=False)
                    app_conf.read( app_file.as_posix() )
                    if not _non_gui_filter(app_conf):
                        try:
                            applications[ app_file.stem ] = {
                                "name": app_conf['Desktop Entry']['Name'],
                                "exec": app_conf['Desktop Entry']['Exec'],
                                "icon": app_conf['Desktop Entry']['Icon'],
                                "compatible": _compatibility_filter(app_conf) 
                            }
                        except Exception as e:
                            pass
                    pass
            pass
        return applications

    def __init__(self, root='', pm=None):
        if root:
            self.root = Path(root).resolve()
        else:
            self.root = PARENT_ROOT
        ##
        if not pm:
            self.pm = P_MAN.PluginManager( self.root/'plugins' )
        else:
            assert( isinstance(pm, P_MAN.PluginManager) )
            self.pm = pm
        ##
        self.applications = dict()
        self.refresh()
        pass

    @staticmethod
    def __plugin_supported(plugins:dict, app_name) -> str:
        for plugin_name,targets in plugins.items():
            if isinstance(targets, list) and (app_name in targets):
                return plugin_name
            elif isinstance(targets, str) and (app_name==targets):
                return plugin_name
        return None

    def instantiate_plugin(self, app_name) -> MetaPlugin:
        app = self.applications[app_name]
        compatibility = app['compatible']
        ##
        if not compatibility:
            return None 
        elif compatibility==True:
            return MetaPlugin( app_name, ProbedCompatibility(app_name, app) )
        elif compatibility==HINT_GENERATED:
            return MetaPlugin( app_name, DefaultCompatibility(app_name, app) )
        else:
            return self.pm.getInstalledPlugin(compatibility)
        pass

    def refresh(self):
        _apps = self.list_all_applications()
        _plugins,_ = self.pm.getPluginsWithTarget()
        ##
        for app_name,app in _apps.items():
            if app_name not in self.applications:
                if app['compatible']!=True:
                    plugin_name = self.__plugin_supported(_plugins, app_name)
                    if plugin_name:
                        app['compatible'] = plugin_name
                    else:
                        app['compatible'] = HINT_GENERATED
                ##
                self.applications[app_name] = app
        pass

    pass

def execute(am, command, args, verbose=False):
    assert( isinstance(am, ApplicationManager) )
    if command=='list':
        ret = { k:v['compatible'] for k,v in am.applications.items() }
        ret = dict(sorted(ret.items(), key=lambda x:x[1], reverse=True))
        print( json.dumps(ret, indent=4) )
    elif command==None:
        _native, _none = 0, 0
        _total = len(am.applications)
        for k,v in am.applications.items():
            if v['compatible']==True: _native += 1
            if v['compatible']==HINT_GENERATED: _none+=1
        print(f'{_native} native + {_total-_native-_none} by-plugin supported, out of {_total} GUI APPs.')
    else:
        print('The command <{}> is not supported.'.format(command))
    pass

def init_subparsers(subparsers):
    p_list = subparsers.add_parser('list',
        help='list all supported applications.')
    pass

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(
            description='VDM Application Manager.')
        subparsers = parser.add_subparsers(dest='command')
        init_subparsers(subparsers)
        #
        args = parser.parse_args()
        am = ApplicationManager()
        ret = execute(am, args.command, args)
        if isinstance(ret, ERR):
            raise Exception(ret.name)
    except Exception as e:
        raise e#pass
    finally:
        pass#exit()
