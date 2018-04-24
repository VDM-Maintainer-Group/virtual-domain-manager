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
from manager.PluginHelper import PluginHelper

global options, ph

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
		__tmp = dict(__helper['plugin_schema'])
		__tmp['version'] = 'v0.1'
		__tmp['plugins'] = __plugins
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
		if options.verbose: logError('error save domain')
	else:
		pass
	pass

def open_domain(): #onResume
	try:
		ph.open_domain()
	except Exception as e:
		print(e)
		if options.verbose: logError('error open domain')
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

def main():
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
		ph = PluginHelper(__name, __helper) #for current workspace
		if options.save_ws:	save_domain()
		if options.exit_ws:	return close_domain()
	elif options.open_ws and fsm_stat>=0:
		close_domain()
		if testStat(options.open_ws):
			ph = PluginHelper(options.open_ws, __helper) #for new workspace
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
	main()