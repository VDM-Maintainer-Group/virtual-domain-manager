#!/usr/bin/python
"""
Plugin Proxy Class
@author: Mark Hong
@level: debug
"""
class PluginProxy:
	"""docstring for PluginProxy"""
	def __init__(self):
		os = require('os')
		print('os: ', os)

		required('Queue.Queue')
		print('Queue.Queue: ', Queue)
		pass