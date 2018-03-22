"""
Plugin Helper Class
@author: Mark Hong
@level: debug
"""
import apt, apt_pkg
from helper.LogHelper import *
from helper.PathHelper import *
from helper.ImportHelper import *

def pluginDepsParse(deps):
	__keys = ['python', 'apt']
	pass

def pluginPkgLint(pkg):
	__desc = ['name', 'author', 'license', 'keywords','description']
	__lint = ['version', 'category', 'platform']
	__runtime = ['main', 'dependency']
	__scripts = ['pre-install', 'post-install', 'pre-uninstall', 'post-uninstall']
	pass

def pluginEnvInject(obj):
	#user_dir_shift
	#work_dir_shift
	pass

class PluginHelper:
	"""docstring for PluginHelper"""
	def __init__(self, name, helper):
		self.name = name
		self.helper = helper
		pass

	def save_domain(self):
		pass

	def close_domain(self):
		pass

	def open_domain(self):
		pass