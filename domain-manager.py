#!/usr/bin/python
import runpy
from utility import PathHelper
from os import path, getcwd
from sys import argv

def m_init():
	global global_var, work_dir
	global_var = {}
	global_var['__user_dir__'] = currentPath()
	work_dir = filePath(__file__)
	global_var['__work_dir__'] = filePath(__file__)
	pass

def main():
	func_map = {
		'plugin': 'manager/plugin-manager.pyc'
	}

	with workSpace(BaseShift('manager')) as wrk:
		if len(argv)>1 and func_map.has_key(argv[1]):
			global_var['argv'] = argv[2:]
			runpy.run_path(func_map[argv[1]],
							global_var, '__main__')
			pass
		else:
			global_var['argv'] = argv
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