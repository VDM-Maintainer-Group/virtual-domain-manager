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

class CoreManager:
    def __init__(self):
        # createdTime + lastUpdatedTime
        self.root = D_MAN.DOMAIN_ROOT
        self.stat = StatFile(self.root)
        pass

    #---------- online domain operations -----------#
    def save_domain(self, delayed=False):
        # onSave
        # save to current open domain
        # if delayed: return the list of StatFile, without `putFile`
        pass

    def open_domain(self, name):
        # onStart --> onResume
        # return if re-open the open domain
        pass

    def close_domain(self):
        # onClose --> onStop
        # close current open domain (return if no open)
        pass

    def switch_domain(self, name):
        # if is_domain_open:
        #   open_domain()
        # else:
        #   save_domain() --> close_domain() --> open_domain()
        #   #restore, if re-open the same domain and the stat files changed
        pass

    pass

def execute(command, args):
    if command=='domain':
        dm = D_MAN.DomainManager()
        D_MAN.execute(dm, args.domain_command, args)
        return
    
    if command=='plugin':
        pm = P_MAN.PluginManager()
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

if __name__ == '__main__':
    try:
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
    except Exception as e:
        raise e#print(e)
    finally:
        pass#exit()
