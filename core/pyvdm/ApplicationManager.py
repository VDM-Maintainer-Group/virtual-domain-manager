#!/usr/bin/env python3
import os, json
import dbus
import argparse
from pathlib import Path
from configparser import RawConfigParser
import pyvdm.core.PluginManager as P_MAN
from pyvdm.core.PluginManager import MetaPlugin
from pyvdm.core.errcode import ApplicationCode as ERR

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

def _plugin_supported(conf) -> bool:
    #TODO: invoke plugin manager
    return False

class ApplicationManager:
    @staticmethod
    def list_all_applications() -> dict:
        applications = dict()
        ##
        data_dirs = os.environ['XDG_DATA_DIRS'].split(':')
        for _path in data_dirs:
            app_dir = Path(_path) / 'applications'
            if app_dir.exists():
                for app_file in app_dir.glob('*.desktop'):
                    app_conf = RawConfigParser(allow_no_value=True, default_section='Desktop Entry', strict=False)
                    app_conf.read( app_file.as_posix() )
                    if not _non_gui_filter(app_conf):
                        try:
                            applications[ app_file.stem ] = {
                                "name": app_conf['Desktop Entry']['Name'],
                                "exec": app_conf['Desktop Entry']['Exec'],
                                "type": app_conf['Desktop Entry']['Type'],
                                "compatible":  _compatibility_filter(app_conf) 
                            }
                        except Exception as e:
                            pass
                    pass
            pass
        return applications

    def __init__(self):
        self.applications = dict()
        self.refresh()
        # self.supported = self.probe_compatibility()
        # self.generated = self.applications / self.supported
        pass

    def refresh(self):
        _apps = self.list_all_applications()
        for app in _apps:
            app_name = app['name']
            if app_name not in self.applications:
                if app['compatible']:
                    _plugin = self.probe_compatibility(app)
                elif _plugin_supported(app):
                    _plugin = None #TODO: PM.getInstalledPlugin(app_name)
                    app['compatible'] = 'plugin'
                else:
                    _plugin = self.default_compatibility(app)
                ##
                self.applications[app_name] = app
                self.applications[app_name]['plugin'] = _plugin
        pass
        pass

    def default_compatibility(self, app_name) -> MetaPlugin:
        #TODO: generate 
        pass

    def probe_compatibility(self, app_name) -> MetaPlugin:
        #TODO: first try dbus interface
        #TODO: then try application file section
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
