#!/usr/bin/python
"""
Domain Manager
@author: Mark Hong
"""
import plugins
from os import chdir, getcwd, path, _exit
from optparse import OptionParser
from utility import PrintHelper, PathHelper

def main():
	printh('Domain Manager', 'main')
	print([__user_dir__, __work_dir__, getcwd()])
	pass

if __name__ == '__main__':
	global options
	parser = OptionParser()
	parser.add_option("-q", "--quiet",
		action="store_true",
		dest="verbose", 
		default=False, 
		help="silient without debug information")
	parser.add_option("-g", "--gui",
		action="store_true",
		dest="open_gui", 
		default=False, 
		help="open setup GUI")
	parser.add_option("-s", "--save",
		action="store_true",
		dest="save_flag", 
		default=False, 
		help="save the current workspace")
	parser.add_option("-a", "--new",
		dest="new_ws", 
		default="", 
		help="create a new workspace")
	parser.add_option("-o", "--open",
		dest="open_ws", 
		default="", 
		help="open an existing workspace")
	parser.add_option("-r", "--rename",
		dest="re_name", 
		default="", 
		help="rename an existing workspace")

	(options, args) = parser.parse_args()
	main()