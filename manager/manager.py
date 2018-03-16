#!/usr/bin/python
"""
Domain Manager
@author: Mark Hong
"""
import plugins
from optparse import OptionParser
from helper.ConfigHelper import *
from helper.LogHelper import *
from helper.PathHelper import *

global options

def list_domain():
	tmp = listPathDir(VDM_WRKS())
	logHelp('manager', str(tmp))
	if options.verbose:
		for t in tmp:
			print('%s: '%t)
			#print out details
			pass
	pass

def create_domain(ws_name):
	__checked = logConsole('config', 'New domain %s? %s'%(G_T(ws_name), '(Y/[N])'), default='N')
	if not __checked[0] in ['Y', 'y']: return
	
	try:
		__plugins = logConsole('config', 'Plugins? (splitted by SPACE)', default=list()).split(' ')
		fixPath(VDM_REPS(ws_name))
		fixPath(VDM_WRKS(ws_name))

		__config=pathShift(VDM_WRKS(ws_name),'config.json')
		fixPath(__config, True)
		plugin_schema['version'] = 'v0.1'
		plugin_schema['plugins'] = __plugins
		save_json(plugin_schema, __config)
	except Exception as e:
		if options.verbose: logHelp('manager', 'error create domain')
	pass

def rename_domain(ws_name):
	try:
		__name = getStat(VDM_CFG('domain-name'))
		fileDirRename(VDM_WRKS(__name), ws_name)
		fileDirRename(VDM_REPS(__name), ws_name)
		putStat(VDM_CFG('domain-name'), ws_name)
	except Exception as e:
		if options.verbose: logHelp('manager', 'error rename domain')
	pass

def save_domain():
	pass

def open_domain(ws_name):
	pass

def close_domain():
	pass

def main():
	init_config()

	# GUI Configuration #
	if options.open_gui:
		# call gui program here
		return

	# domain directory operation #
	if options.list_flag:
		list_domain()
	elif options.new_ws:
		return create_domain(options.new_ws)
	elif options.re_name:
		return rename_domain(options.re_name)

	# domain content operation #
	if options.save_flag:
		save_domain()
	elif options.open_ws:
		return open_domain(options.open_ws)
	elif options.exit_ws:
		return close_domain()

	logHelp('manager', 'main')
	logNormal( getStat(VDM_CFG('stats')), getStat(VDM_CFG('domain-name')) )
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
	parser.add_option("-x", "--exit",
		action="store_true",
		dest="exit_ws", 
		default=False, 
		help="close current workspace")
	parser.add_option("-r", "--rename",
		dest="re_name", 
		default="", 
		help="rename an existing workspace")

	(options, args) = parser.parse_args()
	main()