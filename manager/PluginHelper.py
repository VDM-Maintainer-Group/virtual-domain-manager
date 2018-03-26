"""
Plugin Helper Class
@author: Mark Hong
@level: debug
"""
# import apt, apt_pkg
from helper.LogHelper import *
from helper.ConfigHelper import load_json
from helper.PathHelper import *
from helper.ImportHelper import *
from PluginProxy import PluginProxy

def pluginDepsParse(deps):
	__keys = ['python', 'apt']
	pass

def pluginPkgLint(pkg):
	__desc = ['name', 'author', 'license', 'keywords','description']
	__lint = ['version', 'category', 'platform']
	__runtime = ['main', 'dependency']
	__scripts = ['pre-install', 'post-install', 'pre-uninstall', 'post-uninstall']
	pass

def pluginListSort(plgs):
	# sort plugin list for execution
	pass

def pluginEnvInject(obj):
	#user_dir_shift
	pass

def __test():
	addPythonEnv(workShift('helper'))
	require('LogHelper', 'logHelp')("test", "require test")
	
	PluginProxy = requireInject("PluginProxy")
	PluginProxy.PluginProxy()
	pass

class PluginHelper:
	"""docstring for PluginHelper
	Enum<plugin-code> ('SUCCESS', 'FAILED', 'PROXY')
	"""
	def __init__(self, ws_name, helper):
		self.name = ws_name
		self.helper = helper
		self.ret_code = helper['plugin_code']
		WRK=partial(pathShift, helper['VDM_WRKS'](ws_name))
		CFG=load_json(pathShift(helper['VDM_WRKS'](ws_name),'config.json'))

		#CFG['version']
		self.PLGS = dict()
		for plg in CFG['plugins']: self.PLGS[plg] = PluginProxy(plg)
		pluginListSort(self.PLGS)
		pass

	def ret_check(ret):
		if isinstance(ret, tuple): ret, param = ret[0], ret[1:]
		if ret==self.ret_code.SUCCESS:
			return True
		elif ret==self.ret_code.FAILED:
			logError(str(param))
			return False
		else:
			exit() #got proxy
		pass

	def save_domain(self):
		for k,v in self.PLGS.items():
			ret = v.onSave()
			pass
		pass

	def close_domain(self):
		for k,v in self.PLGS.items():
			ret = v.onExit()
			pass
		pass

	def open_domain(self):
		for k,v in self.PLGS.items():
			ret = v.onResume()
			pass
		pass