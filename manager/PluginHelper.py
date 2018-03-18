"""
Plugin Helper Class
@author: Mark Hong
@level: debug
"""
from helper.LogHelper import *
from helper.PathHelper import *
from helper.ImportHelper import *

def plugEnvInject(obj):
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