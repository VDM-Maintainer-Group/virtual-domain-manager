'''
PathHelper: useful path helper function utilities
@author: Mark Hong
@level: debug
'''
from os import path, mknod, makedirs, chdir, remove, removedirs
from os import getcwd, listdir, rename
from tempfile import mkdtemp

def fixPath(path_name, isFile=False):
	path_name = fileFullPath(path_name)
	if path.exists(path_name):
		if path.isfile(path_name)==isFile:
			return False
		else:
			removedirs(path_name) if isFile else remove(path_name)
			pass
	mknod(path_name) if isFile else makedirs(path_name) # create at last
	return True

def existPath(path_name, isFile=False):
	if not isinstance(path_name, list):
		path_name = [path_name]
	for p in path_name:
		if validPath(p, isFile): return p
	return None

def validPath(path_name, isFile=False):
	tmp=fileFullPath(path_name) 
	return (path.exists(tmp) and (path.isfile(tmp)==isFile))

def listPathDir(path_name, isFile=False):
	tmp=listdir(fileFullPath(path_name))
	tmp=[fileFullPath(t) for t in tmp]
	for t in tmp:
		if path.isfile(t)!=isFile: tmp.remove(t)
	return [str(path.basename(t)) for t in tmp]

def fileDirRename(old_name, new_name):
	if validPath(old_name):
		rename(old_name, new_name)
	else:
		raise Exception('Error rename domain')
	pass

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

def workShift(relPath=""):
	return path.join(getcwd(), relPath)

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