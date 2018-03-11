'''
ImportHelper: import helper function utilities
@author: Mark Hong
@level: debug
'''
import sys
from os.path import realpath

IMPORT_ENV=['./']
IMPORT_BLACK=['os', 'sys']

class ModuleClass(dict):
	"""docstring for ModuleClass"""
	def __init__(self, items):
		super(ModuleClass, self).__init__(items)
		pass

	def __getattr__(self, key):
		if self.has_key(key):
			return self[key]
		else:
			return None

def requireInject(file_path, globalVars=None):
	global IMPORT_ENV
	tmp_path = sys.path
	try:
		IMPORT_ENV = [realpath(x) for x in IMPORT_ENV]
		sys.path += IMPORT_ENV
		tmp_module = __import__(file_path)
		tmp_module.__dict__.update(globalVars)
		return tmp_module
	except Exception as e:
		print(e)
	finally:
		sys.path = tmp_path
	pass

def require(file_path, *args):
	global IMPORT_ENV

	if file_path in IMPORT_BLACK: return None

	tmp_path = sys.path
	try:
		IMPORT_ENV = [realpath(x) for x in IMPORT_ENV]
		sys.path += IMPORT_ENV
		tmp_module = __import__(file_path)
		
		if len(args)==0:
			return tmp_module
		elif len(args)>1:
			tmp_dict = dict()
			for x in args:
				if hasattr(tmp_module, x):
					tmp_dict[x] = getattr(tmp_module, x)
				else:
					tmp_dict[x] = None
			return ModuleClass(tmp_dict)
		else:
			if hasattr(tmp_module, args[0]):
				return getattr(tmp_module, args[0])
			else:
				return None
		pass
	except Exception as e:
		print(e)
	finally:
		sys.path = tmp_path
	pass