#!/usr/bin/env python3
# fix relative path import
import sys
from pathlib import Path
sys.path.append( Path(__file__).resolve().parent.as_posix() )
# normal import
import os, argparse, re
import tempfile, shutil
import PluginManager as P_MAN
from utils import *

DOMAIN_ROOT = Path('~/.vdm').expanduser()
CONFIG_FILENAME = 'config.json'

class CoreManager:
    def __init__(self):
        pass

    def getDomainConfig(self, name):
        pass

    def setDomainConfig(self, name, config):
        pass

    def testStat(self):
        # test and normalize the stat file
        pass

    def getStat(self):
        # read the stat file: createdTime + lastUpdatedTime
        pass

    def putStat(self): #setStat
        pass

    #---------- offline domain operations ----------#
    def create_domain(self, name):
        # if exist 
        # interactive, or not?
        # fix path existence when create (and touch the stat file)
        # record enabled plugins folder
        # save the config file
        pass

    def update_domain(self, name, config):
        # allow rename the domain (remember to update stat file)
        pass

    def delete_domain(self, name):
        pass

    def list_domain(self):
        pass

    #---------- online domain operations -----------#
    def save_domain(self):
        # onSave
        # save to current open domain
        pass

    def open_domain(self, name):
        # onStart --> onResume
        # return if re-open the open domain
        pass

    def close_domain(self):
        # onSave --> onClose --> onStop
        # close current open domain (return if no open)
        pass

    def close_and_open(self, name):
        # don't have to restart all plugins
        # return if re-open the open domain
        pass

    pass

if __name__ == '__main__':
    #"-l", "--list", help="list all the workspace"
    #"-s", "--save", help="save the current workspace"
    #"-a", "--new",  help="create a new workspace"
    #"-o", "--open", help="open an existing workspace"
    #"-x", "--exit", help="close current workspace"
    #"-r", "--rename",help="rename an existing workspace"
    pass
