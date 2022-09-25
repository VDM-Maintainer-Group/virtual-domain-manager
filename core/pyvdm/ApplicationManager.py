#!/usr/bin/env python3
import os, json
import dbus
import argparse
from pathlib import Path
from configparser import RawConfigParser
import pyvdm.core.PluginManager as P_MAN
from pyvdm.core.PluginManager import MetaPlugin
from pyvdm.core.errcode import ApplicationCode as ERR
from pyvdm.interface import CapabilityLibrary

PARENT_ROOT = Path('~/.vdm').expanduser()

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
            self.pm = P_MAN.PluginManager(root)
        else:
            assert( isinstance(pm, P_MAN.PluginManager) )
            self.pm = pm
        ##
        self.xm = CapabilityLibrary.CapabilityHandleLocal('x11-manager')
        ##
        self.applications = dict()
        self.refresh()
        # self.supported = self.probe_compatibility()
        # self.generated = self.applications / self.supported
        pass

    @staticmethod
    def __plugin_supported(plugins:dict, app_name) -> str:
        for plugin_name,targets in plugins.items():
            if isinstance(targets, list) and (app_name in targets):
                return plugin_name
            elif isinstance(targets, str) and (app_name==targets):
                return plugin_name
        return None

    def default_compatibility(self, app_name) -> MetaPlugin:
        #TODO: generate 
        pass

    def probe_compatibility(self, app_name) -> MetaPlugin:
        # sess = dbus.SessionBus()
        # _names = filter(lambda x:f'org.vdm-compatible.{self.name}' in x, sess.list_names())
        #TODO: get interface 'org.vdm-compatible' from 'org/vdm-compatible' of f'{name}'
        pass

    def refresh(self):
        _apps = self.list_all_applications()
        _plugins,_ = self.pm.getPluginsWithTarget()

        for app_name,app in _apps.items():
            if app_name not in self.applications:
                if app['compatible']:
                    _plugin = self.probe_compatibility(app)
                else:
                    plugin_name = self.__plugin_supported(_plugins, app_name)
                    if plugin_name:
                        _plugin = self.pm.getInstalledPlugin(plugin_name)
                        app['compatible'] = True # or the plugin's name
                    else:
                        _plugin = self.default_compatibility(app)
                ##
                self.applications[app_name] = app
                self.applications[app_name]['plugin'] = _plugin
        pass

    pass

def execute(am, command, args, verbose=False):
    assert( isinstance(am, ApplicationManager) )
    if command=='list':
        ret = am.list_all_applications()
        # print( list(ret.keys()) )
        print( json.dumps(ret, indent=4) )
        return ret
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
