#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
import psutil
import re
import tempfile
import time

import pyvdm.core.PluginManager as P_MAN
from pyvdm.core.utils import (POSIX, SHELL_POPEN, STAT_FILENAME, StatFile, Tui, json_load, json_dump)
from pyvdm.core.errcode import DomainCode as ERR

PARENT_ROOT = Path('~/.vdm').expanduser()
DOMAIN_DIRECTORY = PARENT_ROOT / 'domains'
CONFIG_FILENAME = 'config.json'
OVERLAY_DIRECTORY = '.overlay'

DOMAIN_NAME_BLACKLIST = [CONFIG_FILENAME, STAT_FILENAME, OVERLAY_DIRECTORY]

def __run_process(cmd:str, stdin:list):
    process = SHELL_POPEN(cmd)
    assert( process.stdin is not None )
    process.stdin.writelines(stdin)
    ##
    if process.poll():
        _, stderr = process.communicate()
        return (process, stderr)
    else:
        return (process, '')
    pass

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

    @property
    def open_domain_name(self):
        return self.stat.getStat()['name']

    def getDomainConfig(self, name):
        name = str(name)
        if not (self.root / name).exists():
            return ERR.DOMAIN_NOT_EXIST
        _filename = POSIX(self.root / name / CONFIG_FILENAME)
        return json_load(_filename)

    def setDomainConfig(self, name, config):
        if name in DOMAIN_NAME_BLACKLIST:
            return ERR.DOMAIN_NAME_INVALID
        _filename = POSIX(self.root / name / CONFIG_FILENAME)
        json_dump(_filename, config)
        return ERR.ALL_CLEAN

    def configTui(self, name, config={}) -> dict:
        if not isinstance(config, dict):
            config = dict()
        # create/update domain name
        if 'name' not in config:
            if not Tui.confirm('Create new domain \"%s\"?'%name):
                return {} #error
            config['name'] = name
        else:
            config['name'] = Tui.ask('Domain Name', default=name)
        # ask for plugins selection
        _, _plugins = P_MAN.PluginManager().getPluginsWithTarget()
        all_plugin_names = list( _plugins.keys() )
        _plugin_names = list( config['plugins'].keys() ) if 'plugins' in config else None
        _selected = Tui.select('Plugins', all_plugin_names, _plugin_names)
        config['plugins'] = dict()
        for idx in _selected:
            _name = all_plugin_names[idx]
            _version = _plugins[_name]['version']
            config['plugins'].update( {_name:_version} )
        # update timestamp
        config['last_update_time'] = int( time.time() )
        if 'created_time' not in config:
            config['created_time'] = config['last_update_time']
        return config

    #---------- online domain operations -----------#
    def __init_overlay(self, child_name:str):
        child_name   = Path(child_name)
        parent_names = list( Path(child_name).parents )[:-1]
        tmpdir = Path( tempfile.gettempdir() )
        ## prepare lower_dirs
        lower_dirs = []
        for name in parent_names:
            parent_overlay = self.root / name / OVERLAY_DIRECTORY
            if parent_overlay.exists():
                tmp_lowerdir = tmpdir / f'vdm-{name.stem}-lowerdir'
                if parent_overlay.is_symlink():
                    parent_overlay.unlink()
                else:
                    parent_overlay.replace(tmp_lowerdir)
                    lower_dirs.append( tmp_lowerdir.as_posix() )
                parent_overlay.symlink_to(tmp_lowerdir)
        ## prepare lowerdir
        lower_dirs.append( Path.home().as_posix() ) # rightmost $HOME as is the lowest
        lowerdir = ':'.join(lower_dirs)
        ## prepare upperdir
        overlay  = self.root / child_name / OVERLAY_DIRECTORY
        upperdir = tmpdir / f'vdm-{child_name.stem}-upperdir'
        upperdir.mkdir(parents=True, exist_ok=True)
        if overlay.exists():
            overlay.unlink() if overlay.is_symlink() else overlay.replace(upperdir)
        overlay.symlink_to(upperdir)
        ## prepare tempdir
        tempdir = tempfile.mkdtemp()
        return (lowerdir, upperdir)

    def __fini_overlay(self, child_name:str):
        child_name = Path(child_name)
        tmpdir = Path( tempfile.gettempdir() )
        ## move back upperdir
        overlay = self.root / child_name / OVERLAY_DIRECTORY
        upperdir = tmpdir / f'vdm-{child_name.stem}-upperdir'
        overlay.unlink(missing_ok=True)
        upperdir.replace(overlay)
        ## move back lowerdir
        parent_names = list( child_name.parents )[:-1]
        for name in parent_names:
            parent_overlay = self.root / name / OVERLAY_DIRECTORY
            tmp_lowerdir = tmpdir / f'vdm-{name.stem}-lowerdir'
            parent_overlay.unlink(missing_ok=True)
            tmp_lowerdir.replace(parent_overlay)
        pass

    def initialize_domain(self, name:str) -> ERR:
        stat = self.stat.getStat()
        ## check if domain already open
        if stat['name'] and psutil.pid_exists(stat['pid']):
            return ERR.DOMAIN_IS_OPEN
        ## setup lowerdir, upperdir, workdir
        (lowerdir, upperdir, workdir) = self.__init_overlay(name)
        (process, stderr) = __run_process(
            'exec /usr/bin/unshare -rmCp --fork --kill-child --mount-proc -- /bin/sh --norc',
            [
                f'mount -o bind,noexec,nosuid,nodev {workdir} /tmp\n',
                f'mount -t overlay overlay -o lowerdir={lowerdir},upperdir={upperdir},workdir={workdir} $HOME\n',
                'sleep infinity\n',
            ]
        )
        ## check if process failed
        if stderr:
            return ERR.DOMAIN_START_FAILED
        ## wait for the child process to start
        while not psutil.Process(process.pid).children():
            time.sleep(0.001)
        ppid = process.pid
        pid  = psutil.Process(ppid).children()[0].pid
        ##
        self.stat.putStat(name, ppid=ppid, pid=pid)
        return ERR.ALL_CLEAN

    def finalize_domain(self):
        stat = self.stat.getStat()
        if not stat['name']:
            return
        ## kill the daemon process
        ppid = stat['ppid']
        os.system(f'kill -9 {ppid}')
        ## move back lowerdir and upperdir
        self.__fini_overlay( stat['name'] )
        self.stat.putStat('')
        pass

    #---------- offline domain operations ----------#
    def create_domain(self, name:str, config:dict) -> ERR:
        # return if already exist
        if (self.root / name).exists():
            return ERR.DOMAIN_ALREADY_EXIST
        # 
        if not config:
            config = self.configTui(name)
        if not config:
            return ERR.DOMAIN_CONFIG_FAILED
        # fix path existence when create
        domain_path = self.root / name
        domain_path.mkdir(exist_ok=True, parents=True)
        # save the config file
        ret = self.setDomainConfig(name, config)
        if ret!=ERR.ALL_CLEAN:
            return ret
        # update enabled plugins folder (and touch the stat file)
        for _name in config['plugins'].keys():
            StatFile(domain_path, _name).touch()
        print('Domain \"%s\" created.'%name)
        return ERR.ALL_CLEAN

    def update_domain(self, name:str, config:dict) -> ERR:
        # check if domain open
        if self.open_domain_name==name:
            return ERR.DOMAIN_IS_OPEN
        # check if domain exists
        if not (self.root / name).exists():
            return ERR.DOMAIN_NOT_EXIST
        #
        ori_config = self.getDomainConfig(name)
        if type(ori_config)==ERR:
            return ori_config
        if not config:
            config = self.configTui(name, ori_config)
        if not config:
            return ERR.DOMAIN_CONFIG_FAILED
        # rename the domain if necessary
        if config['name']!=name:
            ( self.root / name ).replace( self.root / config['name'] )
            name = config['name']
            pass
        # save the config file
        ret = self.setDomainConfig(name, config)
        if ret!=ERR.ALL_CLEAN:
            return ret
        # update enabled plugins folder (and touch the stat file)
        for _name in config['plugins'].keys():
            StatFile(self.root / name, _name).touch()
        print('Domain \"%s\" updated.'%name)
        return ERR.ALL_CLEAN

    def fork_domain(self, parent_name:str, copy:bool) -> ERR:
        ## check if parent domain exists
        parent_name = Path(parent_name)
        parent_path = self.root / parent_name
        if not parent_path.exists():
            return ERR.DOMAIN_NOT_EXIST
        ## check base name: Copy/Derive
        if copy:    # A --> A*1
            _parent = re.sub(r'\*\d+$', '', parent_path.stem)
            _name = '{parent}*'.format(_parent)
            _path = parent_path.parent
        else:       # A --> A+1
            _parent = re.sub(r'\+\d+$', '', parent_path.stem)
            _name = '{parent}+'.format(_parent)
            _path = parent_path
        ## check existing name collision
        cnt = 1; _name = f'{_name}{cnt}'
        while (_path / _name).exists():
            cnt += 1; _name = f'{_name}{cnt}'
        ## fork the parent domain: config file, plugin stat files;
        child_path = _path / _name
        child_name = parent_name / _name
        child_path.mkdir(exist_ok=True, parents=True)
        ( parent_path/CONFIG_FILENAME ).copy( child_path/CONFIG_FILENAME )
        parent_path.glob(f'*{STAT_FILENAME}').copy( child_path )
        ## switch to child domain
        stat = self.stat.getStat()
        if stat['name']==parent_name:
            ppid, pid = stat['ppid'], stat['pid']
            (lowerdir, upperdir, workdir) = self.__init_overlay(child_name)
            process, stderr = __run_process(
                f'/usr/bin/nsenter --preserve-credentials -U -m -p -t {pid}',
                [
                    f'umount $HOME\n',
                    f'mount -t overlay overlay -o lowerdir={lowerdir},upperdir={upperdir},workdir={workdir} $HOME\n',
                ]
            )
            self.stat.putStat(child_name, ppid=ppid, pid=pid)
        ## fork the parent domain: overlay folder
        if copy:
            child_overlay   = child_path / OVERLAY_DIRECTORY
            parent_overlay  = parent_path / OVERLAY_DIRECTORY
            parent_upperdir = Path(tempfile.gettempdir()) / f'vdm-{parent_name.stem}-upperdir'
            ##
            parent_overlay.unlink(missing_ok=True)
            parent_overlay.replace(parent_overlay)
            parent_upperdir.copy(child_overlay)
        return ERR.ALL_CLEAN

    def delete_domain(self, name:str) -> ERR:
        # check if domain open
        if self.open_domain_name==name:
            return ERR.DOMAIN_IS_OPEN
        #
        (self.root / name).unlink(missing_ok=True)
        return ERR.ALL_CLEAN

    def list_domain(self, names=[]) -> dict:
        result = dict()
        for item in self.root.iterdir():
            _config = item / CONFIG_FILENAME
            if item.is_dir() and (len(names)==0 or item.stem in names) and _config.is_file():
                result[item.stem] = json_load( POSIX(_config) )
            pass
        return result

    pass

def execute(dm, command, args, verbose=False):
    assert( isinstance(dm, DomainManager) )
    if command=='create':
        return dm.create_domain(args.name, args.config)
    elif command=='update':
        return dm.update_domain(args.name, args.config)
    elif command=='fork':
        return dm.fork_domain(args.name, args.copy)
    elif command=='rm' or command=='remove':
        return dm.delete_domain(args.name)
    elif command=='ls' or command=='list':
        ret = dm.list_domain(args.names)
        print(ret)
        return ret
    elif command==None:
        print('<Domain Directory Status>')
    else:
        print('The command <{}> is not supported.'.format(command))
    return

def init_subparsers(subparsers):
    #
    p_create = subparsers.add_parser('create',
        help='create a new domain.')
    p_create.add_argument('name', metavar='domain_name',
        help='the domain name.')
    p_create.add_argument('config', metavar='config_file', nargs='?',
        help='(Optional) the path to the configuration file.')
    #
    p_update = subparsers.add_parser('update',
        help='update an existing domain.')
    p_update.add_argument('name', metavar='domain_name',
        help='the domain name.')
    p_update.add_argument('config', metavar='config_file', nargs='?',
        help='(Optional) the path to the configuration file.')
    #
    p_fork = subparsers.add_parser('fork',
        help='fork an existing domain.')
    p_fork.add_argument('name', metavar='domain_name',
        help='the domain name.')
    p_fork.add_argument('-c', '--copy', action='store_true', default=False,
        help='copy the domain instead of derive.')
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
        subparsers = parser.add_subparsers(dest='command')
        init_subparsers(subparsers)
        #
        args = parser.parse_args()
        dm = DomainManager()
        ret = execute(dm, args.command, args)
        if isinstance(ret, ERR):
            raise Exception(ret.name)
    except Exception as e:
        raise e#pass
    finally:
        pass#exit()
