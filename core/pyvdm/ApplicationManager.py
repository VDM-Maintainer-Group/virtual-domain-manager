#!/usr/bin/env python3
import os, json
import dbus
import time, psutil
import argparse
import subprocess
from pathlib import Path
from configparser import RawConfigParser
import pyvdm.core.PluginManager as P_MAN
from pyvdm.core.PluginManager import MetaPlugin
from pyvdm.core.errcode import ApplicationCode as ERR
from pyvdm.interface import CapabilityLibrary
from pyvdm.core.utils import retry_with_timeout

PARENT_ROOT = Path('~/.vdm').expanduser()
HINT_GENERATED = '(auto-generated)'
CHECKED_SYMBOL = '✔'

def _non_gui_filter(conf) -> bool:
    _flag = False
    _flag = _flag or ('NoDisplay' in conf['Desktop Entry'] and conf['Desktop Entry']['NoDisplay']=='true')
    # _flag = _flag or 'OnlyShowIn' in conf['Desktop Entry']
    _flag = _flag or 'NotShowIn' in conf['Desktop Entry']
    _flag = _flag or ('Terminal' in conf['Desktop Entry'] and conf['Desktop Entry']['Terminal']=='true')
    return _flag

def _compatibility_filter(conf):
    if 'Categories' in conf['Desktop Entry']:
        _cat = conf['Desktop Entry']['Categories'].split(';')
        return CHECKED_SYMBOL if ('VDM' in _cat) else None
    else:
        return None
    pass

class DefaultCompatibility:
    def __init__(self, name, conf):
        self.name = name
        self.conf = conf
        self.exec = conf['exec'].split()[0]
        self.name = Path(self.exec).name
        self.xm = CapabilityLibrary.CapabilityHandleLocal('x11-manager')
        pass

    def onClose(self) -> int:
        os.system(f'killall {self.name}')
        return 0
    
    def onSave(self, stat_file) -> int:
        record = list()
        ##
        for proc in psutil.process_iter(['name', 'pid', 'cmdline']):
            if proc.name()==self.name:
                _windows = self.xm.get_windows_by_pid( proc.pid )
                if len(_windows)==1: #only record one-to-one (pid,xid) mapping
                    record.append({
                        'cmdline': proc.cmdline(),
                        'window': {
                            'desktop': _windows[0]['desktop'],
                            'states':  _windows[0]['states'],
                            'xyhw':    _windows[0]['xyhw']
                        }
                    })
                break
            pass
        ##
        with open(stat_file, 'w') as f:
            json.dump(record, f)
        return 0

    def onResume(self, stat_file, _new:bool) -> int:
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
            # proc = subprocess.Popen(item['cmdline'], start_new_session=True)
            proc = subprocess.Popen(self.exec, start_new_session=True)
            _lambda_fn = lambda: self.xm.get_windows_by_pid(proc.pid)
            _window = retry_with_timeout(_lambda_fn)[0]
            ##
            sp = item['window']
            self.xm.set_window_by_xid(_window['xid'], sp['desktop'], sp['states'], sp['xyhw'])
        return 0

    pass

class CompatibleInterface:
    def __init__(self, sess, dbus_name) -> None:
        self.dbus_name = str( dbus_name )
        self.dbus_iface = dbus.Interface(
            sess.get_object('org.freedesktop.DBus', '/'), 'org.freedesktop.DBus')
        self.node = sess.get_object(dbus_name, '/')
        self.iface = dbus.Interface(self.node, 'org.VDMCompatible.src')
        self.props_iface = dbus.Interface(self.node, 'org.freedesktop.DBus.Properties')
        ##
        _iface = dbus.Interface(self.node, 'org.freedesktop.DBus.Introspectable')
        self.available = ( '<node name="/">' in _iface.Introspect() )
        pass

    @property
    def xid(self) -> int:
        return int( self.props_iface.Get('org.VDMCompatible.src', 'xid') )
    
    @property
    def pid(self) -> int:
        return int( self.dbus_iface.GetConnectionUnixProcessID(self.dbus_name) )

    def Save(self) -> str:
        return str( self.iface.Save() )
    
    def Resume(self, stat:str, new:bool):
        self.iface.Resume(stat, new)
    
    def Close(self):
        self.iface.Close()
    pass

class ProbedCompatibility:
    def __init__(self, name, conf):
        self.name = name
        self.conf = conf
        self.exec = conf['exec'].split()[0]
        self.xm = CapabilityLibrary.CapabilityHandleLocal('x11-manager')
        pass
    
    @property
    def app_ifaces(self):
        sess = dbus.SessionBus()
        _names = filter(lambda x:f'org.VDMCompatible.{self.name}' in x, sess.list_names())
        app_ifaces = [ CompatibleInterface(sess, x) for x in _names ]
        app_ifaces = [ x for x in app_ifaces if x.available ]
        return app_ifaces

    def onSave(self, stat_file) -> int:
        record = list()
        for app in self.app_ifaces:
            stat = app.Save()
            ##
            if not app.xid:
                _window = self.xm.get_windows_by_pid(app.pid)[0]
            else:
                _window = self.xm.get_windows_by_xid(app.xid)[0]
            ##
            record.append({
                'stat': stat,
                'window': {
                    'desktop': _window['desktop'],
                    'states':  _window['states'],
                    'xyhw':    _window['xyhw']
                }
            })
        ##
        with open(stat_file, 'w') as f:
            json.dump(record, f)
        return 0
    
    def onResume(self, stat_file, new:bool) -> int:
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
                subprocess.Popen(self.exec, start_new_session=True)
            retry_with_timeout( lambda: len(self.app_ifaces)==len(_remaining), 3 )
            ## resume stats and window positions
            for (stat,sp), app in zip(_remaining.items(), self.app_ifaces):
                app.Resume(stat, new)
            for (stat,sp), app in zip(_remaining.items(), self.app_ifaces):
                app.Save() #for possible xid update
                if not app.xid:
                    _lambda_fn = lambda: self.xm.get_windows_by_pid(app.pid)
                else:
                    _lambda_fn = lambda: self.xm.get_windows_by_xid(app.xid)
                _window = retry_with_timeout(_lambda_fn)[0]
                self.xm.set_window_by_xid(_window['xid'], sp['desktop'], sp['states'], sp['xyhw'])
        else:
            ## close the no-needed old windows
            for app in old_stats.values():
                app.Close()
        return 0

    def onClose(self) -> int:
        for app in self.app_ifaces:
            app.Close()
        return 0

    pass

class ApplicationManager:
    @staticmethod
    def get_application(name:str) -> dict:
        ##
        try:
            data_dirs = os.environ['XDG_DATA_DIRS'].split(':')
        except:
            data_dirs = ['/usr/local/share', '/usr/share']
        ##
        for xdg_path in data_dirs:
            app_file = Path(xdg_path) / 'applications' / f'{name}.desktop'
            if app_file.exists():
                app_conf = RawConfigParser(allow_no_value=True, default_section='Desktop Entry', strict=False)
                app_conf.read( app_file.as_posix() )
                try:
                    return {
                        "name": app_conf['Desktop Entry']['Name'],
                        "exec": app_conf['Desktop Entry']['Exec'],
                        "icon": app_conf['Desktop Entry']['Icon'],
                    }
                except:
                    return None
        ##
        return dict()

    @staticmethod
    def list_all_applications() -> dict:
        applications = dict()
        ##
        try:
            data_dirs = os.environ['XDG_DATA_DIRS'].split(':')
        except:
            data_dirs = ['/usr/local/share', '/usr/share']
        ##
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
        elif compatibility==CHECKED_SYMBOL:
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
                if app['compatible']!=CHECKED_SYMBOL:
                    plugin_name = self.__plugin_supported(_plugins, app_name)
                    if plugin_name:
                        app['compatible'] = plugin_name
                    else:
                        app['compatible'] = HINT_GENERATED
                ##
                self.applications[app_name] = app
        ##
        _applications = self.applications
        _applications = dict(sorted( _applications.items(), key=lambda x:x[1]['name'] ))
        _applications = dict(sorted( _applications.items(), key=lambda x:x[1]['compatible'], reverse=True ))
        self.applications = _applications
        pass

    def show_compatibility(self):
        ret = { k:v['compatible'] for k,v in self.applications.items() }
        ret = dict(sorted(ret.items(), key=lambda x:x[1], reverse=True))
        print( json.dumps(ret, indent=4) )
        return ret

    def overview_compatibility(self):
        _native, _none = 0, 0
        _total = len(self.applications)
        for k,v in self.applications.items():
            if v['compatible']==CHECKED_SYMBOL: _native += 1
            if v['compatible']==HINT_GENERATED: _none+=1
        return (_total, _native, _total-_native-_none)

    pass

def execute(am, command, args, verbose=False):
    assert( isinstance(am, ApplicationManager) )
    if command=='list':
        am.show_compatibility()
    elif command==None:
        _total, _native, _plugin = am.overview_compatibility()
        print(f'{_native} native + {_plugin} by-plugin supported, out of {_total} GUI APPs.')
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
