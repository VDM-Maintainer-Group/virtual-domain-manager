#!/usr/bin/python3
"""
Domain Manager
@author: Mark Hong
"""
import runpy
from sys import argv
from enum import Enum
from functools import partial
from optparse import OptionParser
from helper.ConfigHelper import *
from helper.LogHelper import *
from helper.PathHelper import *
from helper.DomainHelper import DomainHelper

global options, ph

# plugin_schema={
# 	'version': str(),
# 	'plugins': list()
# }
# plugin_cat={
# 	'system': 'settings', 
# 	'browser':'webpages',
# 	'editor': 'documents'
# }
# plugin_code=Enum('plugin-code', ('SUCCESS', 'FAILED', 'PROXY'))

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

		for item in __helper['plugin_cat'].values():
			fixPath(pathShift(VDM_WRKS(ws_name), item))
			pass
		fixPath(pathShift(VDM_WRKS(ws_name), 'entites'))	# for Notify
		fixPath(pathShift(VDM_WRKS(ws_name), 'notes'))		# for Notes

		__config=pathShift(VDM_WRKS(ws_name),'config.json')
		fixPath(__config, True)
		__tmp = {
			'version': 'v0.1',
			'plugins': __plugins
		}
		save_json(__tmp, __config)
	except Exception as e:
		if options.verbose: logError('error creating domain', e.message)
	pass

def rename_domain(ws_name):
	try:
		__name = getStat(VDM_CFG('domain-name'))
		fileDirRename(VDM_WRKS(__name), ws_name)
		fileDirRename(VDM_REPS(__name), ws_name)
		putStat(VDM_CFG('domain-name'), ws_name)
	except Exception as e:
		if options.verbose: logError('error rename domain')
	pass

def save_domain(): #onSave
	try:
		ph.save_domain()
	except Exception as e:
		if options.verbose: logError('error saving domain')
	else:
		pass
	pass

def open_domain(): #onResume
	try:
		ph.open_domain()
	except Exception as e:
		print(e)
		if options.verbose: logError('error opening domain')
	else:
		putStat(VDM_CFG('domain-name'), ph.name)
		putStat(VDM_CFG('stats'), 'pending')
	pass

def close_domain(): #onExit
	if getStat(VDM_CFG('stats'))=='closed': return
	try:
		ph.close_domain()
	except Exception as e:
		if options.verbose: logError('error close domain')
	else:
		putStat(VDM_CFG('domain-name'), '')
		putStat(VDM_CFG('stats'), 'closed')
	pass

def m_init():
	global global_var, work_dir, __config, __helper
	global_var = {}

	work_dir = fileDirPath(__file__)
	__config = load_json(pathShift(work_dir, 'config.json'))

	global_var.update({'VDM_ENV':		__config})
	global_var.update({'userShift':		partial(pathShift, workShift())})
	global_var.update({'VDM_WRKS':	partial(pathShift, 
				fileFullPath(__config['workspace-dir']))})
	global_var.update({'VDM_REPS':	partial(pathShift, 
				fileFullPath(__config['repo-dir']))})

	__helper = {
		'plugin_code':		plugin_code,
		'plugin_cat':		plugin_cat,
		'VDM_WRKS':			global_var['VDM_WRKS'],
		'VDM_REPS':			global_var['VDM_REPS'],
		'VDM_PLGS':			pathShift(work_dir, 'plugins')
	}
	global_var.update({'__helper': __helper})
	pass

def main():
	# func_map = {
	# 	'plugin': 'plugin-manager.pyc',
	# 	'sync': 'sync-manager.pyc',
	# }

	# with workSpace(pathShift(work_dir, 'manager')) as wrk:
	# 	if len(argv)>1 and func_map.has_key(argv[1]):
	# 		global_var.update({'argv':	argv[2:]})
	# 		runpy.run_path(func_map[argv[1]],
	# 						global_var, '__main__')
	# 		pass
	# 	else:
	# 		global_var.update({'argv':	argv})
	# 		global_var.update({'VDM_CFG':	partial(pathShift, 
	# 			fileFullPath(__config['config-dir']))})
	# 		runpy.run_path('manager.pyc',
	# 						global_var, '__main__')
	# 		pass
	# 	pass

	init_config()

	''' GUI Configuration '''
	if options.open_gui:
		# call gui program here
		logWarning('Nothing happend...')
		return

	''' domain directory operation '''
	if options.list_ws:
		return list_domain()
	elif options.new_ws:
		return create_domain(options.new_ws)
	elif options.re_name:
		return rename_domain(options.re_name)

	''' domain plugins operation
	|      |    closed    |            open            |
	| :--: | :----------: | :------------------------: |
	| Name | (NEED RESET) | SAVE, CLOSE, OPEN, RESTORE |
	| None |     OPEN     |        (NEED RESET)        |
	'''
	global ph, fsm_stat
	__name = getStat(VDM_CFG('domain-name'))
	__stat = getStat(VDM_CFG('stats'))

	if not (testStat(__name) or testStat(__stat)):
		fsm_stat = 0 #normally close
	elif testStat(__name) and testStat(__stat):
		fsm_stat = 1 #normally open
	else:
		fsm_stat = -1 #abnormal

	if fsm_stat==-1: #NOTE: reset abnormal status for now
		putStat(VDM_CFG('domain-name'), '')
		putStat(VDM_CFG('stats'), 'closed')
		pass

	if fsm_stat==1:
		ph = DomainHelper(__name, __helper) #for current workspace
		if options.save_ws:	save_domain()
		if options.exit_ws:	return close_domain()
	elif options.open_ws and fsm_stat>=0:
		close_domain()
		if testStat(options.open_ws):
			ph = DomainHelper(options.open_ws, __helper) #for new workspace
		open_domain()
		return
	
	logHelp('manager', 'main')
	logNormal(__name, __stat)
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
		dest="list_ws", 
		default=False, 
		help="list all the workspace")
	parser.add_option("-s", "--save",
		action="store_true",
		dest="save_ws", 
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
	
	m_init()
	try: #cope with Interrupt Signal
		main()
	except Exception as e:
		print(e) #for debug
	finally:
		exit()