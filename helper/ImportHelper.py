'''
ImportHelper: import helper function utilities
@author: Mark Hong
@level: debug
'''
import sys
from runpy import run_path
from ctypes import cdll
from PathHelper import *

IMPORT_PYENV=['./']
IMPORT_DLENV=['./']
IMPORT_BLACK=['os', 'sys']

def addPythonEnv(param):
	global IMPORT_PYENV
	if isinstance(param, str):
		param = [param]
	IMPORT_PYENV.extend([fileFullPath(p) for p in param])
	pass

def addCDllEnv(param):
	global IMPORT_DLENV
	if isinstance(param, str):
		param = [param]
	IMPORT_DLENV.extend([fileFullPath(p) for p in param])
	pass

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

def requireInject(mod_path, globalVars=None):
	global IMPORT_PYENV
	try:
		tmp_path = sys.path
		sys.path = IMPORT_PYENV + sys.path #check customs first
		tmp_module = __import__(mod_path)
		tmp_module.__dict__.update(globalVars)
		return tmp_module
	except ImportError as e:
		print(e)
	finally:
		sys.path = tmp_path
	pass

def require(file_path, *args):
	global IMPORT_PYENV, IMPORT_DLENV
	fp_tmp = file_path.split('.')
	if fp_tmp[0] in IMPORT_BLACK: return None

	__module = None
	try: # try python module
		tmp_path = sys.path
		sys.path = IMPORT_PYENV + sys.path #check customs first
		__module = __import__(file_path)
		pass
	except ImportError as e:
		try: # try dynamic library
			__ENV = existPath(
				[pathShift(env, file_path) for env in IMPORT_DLENV])
			file_path = __ENV if __ENV else file_path
			__module = cdll.LoadLibrary(file_path)
			pass
		except OSError as e:
			pass
	finally:
		sys.path = tmp_path
		pass

	# getattr
	if __module==None: return None

	if len(args)==0:
		return __module
	elif len(args)>1:
		tmp_dict = dict()
		for x in args:
			if hasattr(__module, x):
				tmp_dict[x] = getattr(__module, x)
			else:
				tmp_dict[x] = None
		return ModuleClass(tmp_dict)
	elif hasattr(__module, args[0]):
		return getattr(__module, args[0])
	else:
		return None
	pass

def require_cur(file_path, *args, **kwargs):
	mod = require(file_path, *args)
	if isinstance(mod, ModuleClass):
		kwargs['this'].__dict__.update(mod)
		pass
	else:
		__key = file_path if not args else args[0]
		kwargs['this'].__dict__.update({__key: mod})
		pass
	return mod

def run_file(file_name, globalVars=None, callback=None):
	# use runpy with: 
	# 	*injection* and *callback* and *status code*
	return True