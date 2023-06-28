#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
import psutil
import re
import shutil
import tempfile
import time

import pyvdm.core.ApplicationManager as A_MAN
from pyvdm.core.ApplicationManager import HINT_GENERATED

from pyvdm.core.utils import (POSIX, SHELL_POPEN, STAT_POSTFIX, StatFile, Tui, json_load, json_dump)
from pyvdm.core.errcode import DomainCode as ERR

PARENT_ROOT = Path('~/.vdm').expanduser()
DOMAIN_DIRECTORY = PARENT_ROOT / 'domains'
CONFIG_FILENAME = 'config.json'
OVERLAY_DIRECTORY = '.overlay'

DOMAIN_NAME_BLACKLIST = [CONFIG_FILENAME, STAT_POSTFIX, OVERLAY_DIRECTORY]

def _run_process(cmd:str, stdin:list):
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
    def __init__(self, root='', am=None):
        if root:
            self.root = Path(root).resolve()
        else:
            self.root = DOMAIN_DIRECTORY
        ##
        if not am:
            self.am = A_MAN.ApplicationManager(root)
        else:
            self.am = am
        ##
        self.root.mkdir(exist_ok=True, parents=True)
        self.stat = StatFile( POSIX(self.root.parent) )
        self.stat.touch()
        pass

    @property
    def open_domain_name(self):
        return self.stat.getStat()['name']

    def defaultConfig(self, name, full_feature=True):
        config = self.getDomainConfig(name)
        if type(config)==dict:
            return config
        ##
        if full_feature:
            _,_plugins = self.am.pm.getPluginsWithTarget()
            plugins = { name:plugin['version'] for name,plugin in _plugins.items() }
            _applications = self.am.refresh()
            applications = [k for k,v in _applications.items() if v['compatible']!=HINT_GENERATED]
        else:
            plugins = dict()
            applications = list()
        return {
            'name':name,
            'plugins':plugins,
            'applications':applications,
            'created_time':int(time.time()),
            'last_update_time':int(time.time())
        }

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
        full_config = self.defaultConfig(name, full_feature=True)
        if not isinstance(config, dict):
            config = full_config
        ## create/update domain name
        config['name'] = Tui.ask('Domain Name', default=name)
        ## ask for application selection
        _all_apps = list( self.am.refresh() )
        _candidates = config.get('applications', [])
        _selected = Tui.select('Applications', _all_apps, _candidates)
        config['applications'] = [ _all_apps[idx] for idx in _selected ] #type: ignore
        ## ask for plugins selection
        _all_plugins = list( full_config['plugin'].keys() )
        _candidates = config.get('plugins', {})
        _selected = Tui.select('Plugins', _all_plugins, list(_candidates))
        config['plugins'] = { full_config[ _all_plugins[idx] ] for idx in _selected } #type: ignore
        ## update timestamp
        config['last_update_time'] = int( time.time() )
        if 'created_time' not in config:
            config['created_time'] = config['last_update_time']
        return config

    #---------- online domain operations -----------#
    def __init_overlay(self, _child_name:str):
        child_name   = Path(_child_name)
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
                    shutil.move(parent_overlay, tmp_lowerdir)
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
            overlay.unlink() if overlay.is_symlink() else shutil.move(overlay, upperdir)
        overlay.symlink_to(upperdir)
        ## prepare workdir
        workdir = tmpdir / f'vdm-{child_name.stem}-workdir'
        workdir.unlink(missing_ok=True)
        return (lowerdir, upperdir, workdir)

    def __fini_overlay(self, _child_name:str):
        child_name = Path(_child_name)
        tmpdir = Path( tempfile.gettempdir() )
        ## move back upperdir
        overlay = self.root / child_name / OVERLAY_DIRECTORY
        upperdir = tmpdir / f'vdm-{child_name.stem}-upperdir'
        overlay.unlink(missing_ok=True)
        shutil.move(upperdir, overlay)
        ## move back lowerdir
        parent_names = list( child_name.parents )[:-1]
        for name in parent_names:
            parent_overlay = self.root / name / OVERLAY_DIRECTORY
            tmp_lowerdir = tmpdir / f'vdm-{name.stem}-lowerdir'
            if tmp_lowerdir.exists():
                parent_overlay.unlink(missing_ok=True)
                shutil.move(tmp_lowerdir, parent_overlay)
        pass

    def initialize_domain(self, name:str) -> ERR:
        stat = self.stat.getStat()
        ## check if domain already open
        if stat['name'] and psutil.pid_exists( int(stat['pid']) ):
            return ERR.DOMAIN_IS_OPEN
        ## setup lowerdir, upperdir, workdir
        (lowerdir, upperdir, workdir) = self.__init_overlay(name)
        (process, stderr) = _run_process(
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
        self.stat.putStat('')
        ## move back lowerdir and upperdir
        self.__fini_overlay( stat['name'] )
        pass

    #---------- offline domain operations ----------#
    def create_domain(self, name:str, config:dict, tui:bool=True) -> ERR:
        # return if already exist
        if (self.root / name).exists():
            return ERR.DOMAIN_ALREADY_EXIST
        # 
        if not config:
            config = self.configTui(name) if tui else self.defaultConfig(name)
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

    def update_domain(self, name:str, config:dict, tui:bool=True, new_name='') -> ERR:
        ## check if domain open
        if Path(self.open_domain_name).is_relative_to(name):
            return ERR.DOMAIN_IS_OPEN
        ## check if nested domain exists
        domain_folder = self.root / name
        child_domains = list( domain_folder.glob(f'[!.]*/{CONFIG_FILENAME}') )
        if len(child_domains)>0:
            return ERR.DOMAIN_NESTED_DOMAIN
        ## check if domain exists
        if not domain_folder.exists():
            return ERR.DOMAIN_NOT_EXIST
        ## reconfigure the domain
        ori_config = self.getDomainConfig(name)
        if type(ori_config)==ERR:
            return ori_config
        if not config:
            config = self.configTui(name, ori_config) if tui else self.defaultConfig(name)
            if new_name: config['name'] = new_name
        if not config:
            return ERR.DOMAIN_CONFIG_FAILED
        ## rename the domain folder if needed
        assert( Path(config['name']).parent == Path(name).parent )
        if config['name']!=name:
            try:
                domain_folder.replace( self.root / config['name'] )
            except:
                return ERR.DOMAIN_NAME_INVALID
            name = config['name']
            pass
        ## save the config file
        ret = self.setDomainConfig(name, config)
        if ret!=ERR.ALL_CLEAN:
            return ret
        ## update enabled plugins folder (and touch the stat file)
        for _name in config['plugins'].keys():
            StatFile(self.root / name, _name).touch()
        print('Domain \"%s\" updated.'%name)
        return ERR.ALL_CLEAN

    def fork_domain(self, _parent_name:str, copy:bool) -> ERR:
        ## check if parent domain exists
        parent_name = Path(_parent_name)
        parent_path = self.root / parent_name
        if not parent_path.exists():
            return ERR.DOMAIN_NOT_EXIST
        ## check base name: Copy/Derive
        if copy:    # A --> A*1
            _parent = parent_path.stem#re.sub(r'\*\d+$', '', parent_path.stem)
            _name = f'{_parent}*'
            _path = parent_path.parent
        else:       # A --> A+1
            _parent = parent_path.stem#re.sub(r'\+\d+$', '', parent_path.stem)
            _name = f'{_parent}+'
            _path = parent_path
        ## check existing name collision
        cnt = 1; t_name = f'{_name}{cnt}'
        while (_path / t_name).exists():
            cnt += 1; t_name = f'{_name}{cnt}'
        child_name = _path.relative_to(self.root) / t_name
        child_path = _path / t_name
        child_path.mkdir(exist_ok=True, parents=True)
        ## fork the parent domain: config file
        _conf = json_load( parent_path/CONFIG_FILENAME )
        _conf['name'] = POSIX(child_name)
        _conf['created_time'] = int(time.time())
        _conf['last_update_time'] = int(time.time())
        json_dump( child_path/CONFIG_FILENAME, _conf )
        ## fork the parent domain: stat files
        for stat_file in parent_path.glob(f'.*{STAT_POSTFIX}'):
            shutil.copyfile( stat_file, child_path/stat_file.name )
        ## if parent domain is open, switch to child domain
        stat = self.stat.getStat()
        if stat['name']==parent_name:
            ppid, pid = stat['ppid'], stat['pid']
            (lowerdir, upperdir, workdir) = self.__init_overlay( POSIX(child_name) )
            process, stderr = _run_process(
                f'/usr/bin/nsenter --preserve-credentials -U -m -p -t {pid}',
                [
                    f'umount $HOME\n',
                    f'mount -t overlay overlay -o lowerdir={lowerdir},upperdir={upperdir},workdir={workdir} $HOME\n',
                ]
            )
            self.stat.putStat(POSIX(child_name), ppid=ppid, pid=pid)
        ## fork the parent domain: overlay folder
        if copy:
            child_overlay   = child_path / OVERLAY_DIRECTORY
            parent_overlay  = parent_path / OVERLAY_DIRECTORY
            parent_upperdir = Path(tempfile.gettempdir()) / f'vdm-{parent_name.stem}-upperdir'
            ##
            parent_overlay.unlink(missing_ok=True)
            try:
                parent_upperdir.replace(parent_overlay)
                shutil.copyfile(parent_overlay, child_overlay)
            except:
                pass
        return ERR.ALL_CLEAN

    def delete_domain(self, name:str, allow_recursive:bool=False) -> ERR:
        ## check if domain open
        if Path(self.open_domain_name).is_relative_to(name):
            return ERR.DOMAIN_IS_OPEN
        ## check if nested domain exists
        domain_folder = self.root / name
        child_domains = list( domain_folder.glob(f'[!.]*/{CONFIG_FILENAME}') )
        if len(child_domains)>0 and not allow_recursive:
            return ERR.DOMAIN_NESTED_DOMAIN
        ## TODO: merge overlay before delete
        ## delete the content recursively
        shutil.rmtree(domain_folder, ignore_errors=True)
        return ERR.ALL_CLEAN

    def list_child_domain(self, name:str='') -> list:
        domain_folder = self.root / name
        child_domains = list( domain_folder.glob(f'[!.]*/{CONFIG_FILENAME}') )
        return [POSIX(item.parent.relative_to(self.root)) for item in child_domains]

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
