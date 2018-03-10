'''
PathHelper: useful path helper function utilities
@author: Mark Hong
@level: debug
'''
from os import path, getcwd, chdir

def currentPath():
	return getcwd()

def filePath(file_path):
	return path.dirname(path.realpath(file_path))

def BaseShift(relPath):
	if work_dir in globals():
		return path.join(work_dir, relPath)
	else:
		return path.join(getcwd(), relPath)
	pass

class workSpace:
	"""docstring for workSpace"""
	def __init__(self, wrk):
		self.wrk = wrk
		self.pwd = getcwd()
	
	def __enter__(self):
		chdir(wrk)
		return self

	def __exit__(self, exc_type, exc_value, exc_tb):
		chdir(pwd)
		if exc_tb:
            # cope with exception
            pass
		pass