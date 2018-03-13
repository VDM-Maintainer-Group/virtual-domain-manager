'''
ImportHelper: import helper function utilities
@author: Mark Hong
@level: debug
'''
import sys
from runpy import run_path
from ctypes import cdll
from PathHelper import *

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
		IMPORT_ENV = [fileFullPath(x) for x in IMPORT_ENV]
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
	fp_tmp = file_path.split('.')
	if not(fp_tmp in ['dll', 'so']):
		file_path = fp_tmp
		if file_path[0] in IMPORT_BLACK: return None
	else:
		file_path = [file_path] #wrap for continuity
		pass

	tmp_path = sys.path
	try:
		# iterate enviroment path
		IMPORT_ENV = [fileFullPath(x) for x in IMPORT_ENV]
		isBinary = None
		for x in IMPORT_ENV:
			if validPath(x, True):
				isBinary = x
				break
			pass
		# load temp module
		if not isBinary:
			sys.path = IMPORT_ENV + sys.path #check customs first
			tmp_module = __import__(file_path[0])
		else:
			tmp_module = cdll.LoadLibrary(isBinary)
			pass
		# load attribute of module
		for x in file_path[1:]:
			if hasattr(tmp_module, x):
				tmp_module = getattr(tmp_module, x)
			else:
				return None
		# wrap module with args
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

def require_cur(file_path, this, *args):
	mod = require(file_path, *args)
	file_path = file_path.split('.')[-1]
	this.__dict__.update({file_path: mod})
	return mod

def run_file(file_name, globalVars=None, callback=None):
	# use runpy with: 
	# 	*injection* and *callback* and *status code*
	return True