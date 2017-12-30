#!/usr/bin/python3
"""
Plugin Manager
@author: Mark Hong
#call: temporarily register
#install: cp plugin files to install dir
"""
from optparse import OptionParser
from utility.Utility import printh, load_json

def main():
	printh('Plugin Manager', 'main')
	print([__user_dir__, __work_dir__])
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
		help="silient without debug information")
	parser.add_option("-a", "--add",
		dest="plugin_name", 
		default="", 
		help="install a new plugin from PWD")
	parser.add_option("-r", "--remove",
		dest="plugin_name", 
		default="", 
		help="remove an existing plugin")
	parser.add_option("-d", "--debug",
		dest="plugin_name", 
		default="", 
		help="debug an developing plugin")

	(options, args) = parser.parse_args()
	main()