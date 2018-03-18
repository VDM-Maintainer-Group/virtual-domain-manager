#!/usr/bin/python
import runpy
from sys import argv
from functools import partial
from enum import Enum
from helper.PathHelper import *
from helper.ConfigHelper import load_json

plugin_schema={
	'version': str(),
	'plugins': list()
}
plugin_cat={
	'SYSTEM':'os_status', 
	'BROSWER':'webpages',
	'EDITOR':'documents'
}
plugin_code=Enum('plugin-code', ('SUCCESS', 'FAILED', 'PROXY'))

def m_init():
	global global_var, work_dir, __config, __helper
	global_var = {}

	work_dir = fileDirPath(__file__)
	__config = load_json(pathShift(work_dir, 'config.json'))

	global_var.update({'VDM_ENV':		__config})
	global_var.update({'userShift':		partial(pathShift, currentPath())})
	global_var.update({'workShift':		partial(pathShift, work_dir)})
	global_var.update({'VDM_WRKS':	partial(pathShift, 
				fileFullPath(__config['workspace-dir']))})
	global_var.update({'VDM_REPS':	partial(pathShift, 
				fileFullPath(__config['repo-dir']))})

	__helper = {
		'plugin_schema':	plugin_schema,
		'plugin_code':		plugin_code,
		'plugin_cat':		plugin_cat,
		'__user_dir__':		currentPath(),
		'__work_dir__':		fileDirPath(__file__),
		'VDM_WRKS':			global_var['VDM_WRKS'],
		'VDM_REPS':			global_var['VDM_REPS']
	}
	global_var.update({'__helper': __helper})
	pass

def main():
	func_map = {
		'plugin': 'plugin-manager.pyc'
	}

	with workSpace(pathShift(work_dir, 'manager')) as wrk:
		if len(argv)>1 and func_map.has_key(argv[1]):
			global_var.update({'argv':	argv[2:]})
			runpy.run_path(func_map[argv[1]],
							global_var, '__main__')
			pass
		else:
			global_var.update({'argv':	argv})
			global_var.update({'VDM_CFG':	partial(pathShift, 
				fileFullPath(__config['config-dir']))})
			runpy.run_path('manager.pyc',
							global_var, '__main__')
			pass
		pass
	pass

if __name__ == '__main__':
	m_init()
	try: #cope with Interrupt Signal
		main()
	except Exception as e:
		print(e) #for debug
	finally:
		exit()