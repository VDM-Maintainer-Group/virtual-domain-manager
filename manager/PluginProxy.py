"""
Plugin Proxy Class
@author: Mark Hong
@level: debug
"""
class PluginProxy:
	"""docstring for PluginProxy"""
	def __init__(self, name):
		os = require('os')
		print('os: ', os)

		required('Queue', 'Queue')
		print('Queue.Queue: ', Queue)

		required('libc.so.6', 'printf')
		printf("%s\n", "Hello World!")
		pass