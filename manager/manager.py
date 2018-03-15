#!/usr/bin/python
"""
Domain Manager
@author: Mark Hong
"""
import plugins
from optparse import OptionParser
from helper.ConfigHelper import *
from helper.PrintHelper import *
from helper.PathHelper import *

global options

def main():
	init_config()

	if options.open_gui:
		# call gui program here
		return

	if options.list_flag:
		# iterate all the domains
		# for x in <domains>:
		# 	if options.verbose: pass #print out details
		return

	if options.save_flag: #save current domain
		if options.verbose: pass #print out details
		return

	if options.new_ws:
		#create new domain, avoid name collision
		try:
			fixPath(VDM_REPS(options.new_ws))
			fixPath(VDM_WRKS(options.new_ws))
			fixPath(VDM_WRKS(options.new_ws+'\\config.json'), True)
		except Exception as e:
			if options.verbose: printh('manager', 'error create domain')
		return

	if options.open_ws:
		# (erect save_flag) open another workspace
		return

	if options.re_name:
		try:
			__name = getStat(VDM_CFG('domain-name'))
			fileDirRename(VDM_WRKS(__name), options.re_name)
			fileDirRename(VDM_REPS(__name), options.re_name)
			putStat(VDM_CFG('domain-name'), options.re_name)
		except Exception as e:
			if options.verbose: printh('manager', 'error rename domain')
		return
	
	printh('manager', 'main')
	print(getStat(VDM_CFG('stats')), getStat(VDM_CFG('domain-name')))
	pass

def init_config(init_stat='closed', init_name=''):
	global stats, dname

	fixPath(VDM_CFG())
	fixPath(VDM_WRKS())
	fixPath(VDM_REPS())

	if fixPath(VDM_CFG('stats'), True):
		putStat(VDM_CFG('stats'), init_stat)
	if fixPath(VDM_CFG('domain-name'), True):
		putStat(VDM_CFG('domain-name'), init_name)
	pass

if __name__ == '__main__':
	parser = OptionParser()
	parser.add_option("-v", "--verbose",
		action="store_true",
		dest="verbose", 
		default=False, 
		help="print out more information")
	parser.add_option("-g", "--gui",
		action="store_true",
		dest="open_gui", 
		default=False, 
		help="open setup GUI")
	parser.add_option("-l", "--list",
		action="store_true",
		dest="list_flag", 
		default=False, 
		help="list all the workspace")
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