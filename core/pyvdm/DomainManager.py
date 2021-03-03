#!/usr/bin/env python3
# fix relative path import
import sys, time
from pathlib import Path
sys.path.append( Path(__file__).resolve().parent.as_posix() )
# normal import
import os, argparse, re, shutil
import pyvdm.core.PluginManager as P_MAN
from pyvdm.core.utils import *
from pyvdm.core.errcode import DomainCode

PARENT_ROOT = Path('~/.vdm').expanduser()
DOMAIN_DIRECTORY = PARENT_ROOT / 'domains'
CONFIG_FILENAME = 'config.json'

class DomainManager():
    def __init__(self, root=''):
        if root:
            self.root = Path(root).resolve()
        else:
            self.root = DOMAIN_DIRECTORY
        self.root.mkdir(exist_ok=True, parents=True)
        self.stat = StatFile( POSIX(self.root.parent) )
        self.stat.touch()
        pass

    def getDomainConfig(self, name):
        _filename = POSIX(self.root / name / CONFIG_FILENAME)
        return json_load(_filename)

    def setDomainConfig(self, name, config):
        _filename = POSIX(self.root / name / CONFIG_FILENAME)
        json_dump(_filename, config)
        pass

    def configTui(self, name, config=None):
        if not isinstance(config, dict):
            config = dict()
        # create/update domain name
        if 'name' not in config:
            if not Tui.confirm('Create new domain \"%s\"?'%name):
                return None #error
            config['name'] = name
        else:
            config['name'] = Tui.ask('Domain Name', default=name)
        # ask for plugins selection
        _plugins = P_MAN.PluginManager().list()
        all_plugin_names = list( _plugins.keys() )
        _plugin_names = list( config['plugins'].keys() ) if 'plugins' in config else None
        _selected = Tui.select('Plugins', all_plugin_names, _plugin_names)
        config['plugins'] = dict()
        for idx in _selected:
            _name = all_plugin_names[idx]
            _version = _plugins[_name][0]['version']
            config['plugins'].update( {_name:_version} )
        # update timestamp
        config['last_update_time'] = int( time.time() )
        if 'created_time' not in config:
            config['created_time'] = config['last_update_time']
        return config

    #---------- offline domain operations ----------#
    def create_domain(self, name, config):
        # return if already exist
        if (self.root / name).exists():
            return DomainCode['DOMAIN_ALREADY_EXIST']
        # 
        if not config:
            config = self.configTui(name)
        if not config:
            return DomainCode['DOMAIN_CONFIG_FAILED']
        # fix path existence when create
        domain_path = self.root / name
        domain_path.mkdir(exist_ok=True, parents=True)
        # save the config file
        self.setDomainConfig(name, config)
        # update enabled plugins folder (and touch the stat file)
        for _name in config['plugins'].keys():
            StatFile(domain_path, _name).touch()
        print('Domain \"%s\" created.'%name)
        return True

    def update_domain(self, name, config):
        # check if domain open
        if self.stat.getStat()==name:
            return DomainCode['DOMAIN_IS_OPEN']
        # check if domain exists
        if not (self.root / name).exists():
            return DomainCode['DOMAIN_NOT_EXIST']
        #
        ori_config = self.getDomainConfig(name)
        if not config:
            config = self.configTui(name, ori_config)
        if not config:
            return DomainCode['DOMAIN_CONFIG_FAILED']
        # rename the domain if necessary
        if config['name']!=name:
            shutil.move( POSIX(self.root/name), POSIX(self.root/config['name']) )
            name = config['name']
            pass
        # save the config file
        self.setDomainConfig(name, config)
        # update enabled plugins folder (and touch the stat file)
        for _name in config['plugins'].keys():
            StatFile(self.root / name, _name).touch()
        print('Domain \"%s\" updated.'%name)
        return True

    def delete_domain(self, name):
        # check if domain open
        if self.stat.getStat()==name:
            return DomainCode['DOMAIN_IS_OPEN']
        #
        shutil.rmtree( POSIX(self.root/name) )
        return True

    def list_domain(self, names=[]):
        result = dict()
        for item in self.root.iterdir():
            _config = item / CONFIG_FILENAME
            if item.is_dir() and (len(names)==0 or item.stem in names) and _config.is_file():
                result[item.stem] = json_load( POSIX(_config) )
            pass
        print( result )
        return result

    pass

def execute(dm, command, args, verbose=False):
    assert( isinstance(dm, DomainManager) )
    if command=='add':
        return dm.create_domain(args.name, args.config)
    elif command=='update':
        return dm.update_domain(args.name, args.config)
    elif command=='rm' or command=='remove':
        return dm.delete_domain(args.name)
    elif command=='ls' or command=='list':
        return dm.list_domain(args.names)
    else:
        print('The command <{}> is not supported.'.format(command))
    return

def init_subparsers(subparsers):
    #
    p_add = subparsers.add_parser('add',
        help='create a new domain.')
    p_add.add_argument('name', metavar='domain_name',
        help='the domain name.')
    p_add.add_argument('config', metavar='config_file', nargs='?',
        help='(Optional) the path to the configuration file.')
    #
    p_update = subparsers.add_parser('update',
        help='update an existing domain.')
    p_update.add_argument('name', metavar='domain_name',
        help='the domain name.')
    p_update.add_argument('config', metavar='config_file', nargs='?',
        help='(Optional) the path to the configuration file.')
    #
    p_remove = subparsers.add_parser('remove',
        help='remove and existing domain.')
    p_remove.add_argument('name', metavar='domain_name',
        help='the domain name.')
    #
    p_list = subparsers.add_parser('list',
        help='list all available domains.')
    p_list.add_argument('names', metavar='domain_names', nargs='*',
        help='(Optional) only list the specified domains.')
    pass

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(
            description='VDM Domain Manager.')
        parser.add_argument('-v', '--verbose', action='store_true',
            help='enable verbose information logging.')
        subparsers = parser.add_subparsers(dest='command')
        init_subparsers(subparsers)
        #
        args = parser.parse_args()
        dm = DomainManager()
        execute(dm, args.command, args)
    except Exception as e:
        raise e if args.verbose else 0
    finally:
        0 if args.verbose else exit()
