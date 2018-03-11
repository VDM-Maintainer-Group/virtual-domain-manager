#!/usr/bin/python
"""
Plugin Proxy Class
@author: Mark Hong
#Use runpy to change work-dir
"""

class PluginProxy(object):
	"""docstring for PluginProxy"""
	def __init__(self, fpath):
		super(PluginProxy, self).__init__()
		self.global_vars = {}
		# fpath = path.realpath(fpath)
		# self.fpath = 
		# (
		# 	path.realpath(path.join(__user_dir__, fpath))
		# 	if not path.isabs(fpath) else self.fpath = fpath
		# )
		pass

	def call(self):

		pass