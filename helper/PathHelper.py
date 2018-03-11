'''
PathHelper: useful path helper function utilities
@author: Mark Hong
@level: debug
'''
from os import path, getcwd, mknod, makedirs, chdir, remove, removedirs
from tempfile import mkdtemp

def checkPath(path_name, isFile=False):
	path_name = fileFullPath(path_name)
	if path.exists(path_name):
		if path.isfile(path_name)==isFile:
			return
		else:
			removedirs(path_name) if isFile else remove(path_name)
			pass
		pass
	# create at last
	mknod(path_name) if isFile else makedirs(path_name)
	pass

def validPath(path_name):
	return path.exists(path_name)

def currentPath():
	return getcwd()

def fileDirPath(file_path):
	return path.dirname(fileFullPath(file_path))

def fileFullPath(file_path):
	return path.realpath(path.expanduser(file_path))
	pass

def pathShift(basePath=None, relPath=""):
	if basePath:
		return path.join(basePath, relPath)
	else:
		return path.join(getcwd(), relPath)
	pass

class workSpace:
	"""docstring for workSpace"""
	def __init__(self, wrk):
		self.wrk = wrk
		self.pwd = getcwd()
	
	def __enter__(self):
		chdir(self.wrk)
		return self

	def __exit__(self, exc_type, exc_value, exc_tb):
		chdir(self.pwd)
		if exc_tb:
			# cope with exception
			pass
		pass

class tempSpace:
	"""docstring for tempSpace"""
	def __init__(self):
		self.pwd = getcwd()
		self.tmp = mkdtemp()
	
	def __enter__(self):
		chdir(self.tmp)
		return self

	def __exit__(self, exc_type, exc_value, exc_tb):
		chdir(self.pwd)
		removedirs(self.tmp)
		pass