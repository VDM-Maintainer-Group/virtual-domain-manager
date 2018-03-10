'''
ImportHelper: import helper function utilities
@author: Mark Hong
@level: debug
'''
from runpy import run_path
from os.path import isdir, relpath

def require(file_path, globalVars=None):
	if not isdir(file_path):
		file_path += '.pyc'
	run_path(file_path, globalVars, None)
	pass

def requireLib():
	pass

# __os_none__.path.isdir(__os_none__.path.join(__system_dir__, __system_file__))
# __system_dir__ = __os_none__.path.dirname(__file__)
# __import__(__system_file__, globals(), locals())