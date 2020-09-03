#!/usr/bin/python
"""
Plugin Manager
@author: Mark Hong
#call: temporarily register
#install: cp plugin files to install dir
"""
import plugins
from optparse import OptionParser
from helper.ImportHelper import *
from helper.PathHelper import *
from helper.LogHelper import *
from helper.ConfigHelper import *

def pluginDepsParse(deps):
	__keys = ['python', 'apt']
	pass

def pluginPkgLint(pkg):
	__desc = ['name', 'author', 'license', 'keywords','description']
	__lint = ['version', 'category', 'platform']
	__runtime = ['main', 'dependency']
	__scripts = ['pre-install', 'post-install', 'pre-uninstall', 'post-uninstall']
	pass

def main():
	global IMPORT_PYENV
	logHelp('Plugin Manager', 'main')
	print([__helper['__user_dir__'], workShift()])
	pass

if __name__ == '__main__':
	global options
	parser = OptionParser()
	parser.add_option("-l", "--list",
		action="store_true",
		dest="list_flag", 
		default=False, 
		help="list all plugins.")
	parser.add_option("-q", "--quiet",
		action="store_true",
		dest="verbose", 
		default=False, 
		help="silent without debug information")
	parser.add_option("-a", "--add",
		dest="plugin_name", 
		default="", 
		help="install a new plugin from PWD")
	parser.add_option("", "--run",
		dest="plugin_name", 
		default="", 
		help="run an existing plugin function")
	parser.add_option("-r", "--remove",
		dest="plugin_name", 
		default="", 
		help="remove an existing plugin")
	parser.add_option("", "--debug",
		dest="plugin_name", 
		default="", 
		help="test environment for developing plugin")

	(options, args) = parser.parse_args()
	main()