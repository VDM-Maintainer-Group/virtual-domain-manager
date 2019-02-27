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
from functools import partial
from PluginProxy import PluginProxy

def __test():
	addPythonEnv(workShift('helper'))
	require('LogHelper', 'logHelp')("test", "require test")
	
	PluginProxy = requireInject("PluginProxy")
	PluginProxy.PluginProxy()
	pass

def pluginListSort(plgs):
	# sort plugin list for execution
	pass

def pluginEnvInject(obj):
	#user_dir_shift
	pass

class PluginOracle:
	def __init__(params):
		self.category =['dBrowser', 'dEditor', 'dSystem']
		self.repos_uri = ['/opt/domain-manager/plugins']
		self.addRepoUri(params)
		pass

	def query(name, required=False):
		'''
		one plugin name each time
		@param: plugin name
		@retval: package information after lint
		@retval: (Optional) plugin entity if *required*
		'''
		retval={}
		p = findPlguinPath(name)
		if p=="":
			return retval
		retval = load_json(pathShift(p, 'package.json'))
		pluginLint(retval)
		if required:
			# ProxyClass = requireInject("PluginProxy", globalVars).PluginProxy
			# ProxyClass(p)
			pass
		return retval

	def addRepoUri(params):
		if isinstance(params, str): params = [params]
		self.repos_uri = params + self.repos_uri
		pass

	def findPlguinPath(plg):
		for base in self.repos_uri:
			for cat in self.category:
				p = path.join(base, cat, plg)
				if path.exists(p):
					return p
				pass
			pass
		return ""

	def pluginLint(pkg):
		'''
		This function causes no failure by default.
		'''
		# __runtime = ['main', 'public', 'dependency']
		# __desc = ['name', 'author', 'license', 'keywords', 'description']
		# __lint = ['version', 'category', 'platform']
		# __scripts = ['pre-install', 'post-install', 'pre-uninstall', 'post-uninstall']
		if not pkg.has_key('name'):
			pass #impossible, i saw nothing...
		if not pkg.has_key('author'):
			pkg['author']=''
		if not pkg.has_key('license'):
			pkg['license']='LGPL-3.0'
		if not pkg.has_key('keywords'):
			pkg['keywords']=['']
		if not pkg.has_key('description'):
			pkg['description']='The author is too lazy to speak a single word...'
		if not pkg.has_key('main'):
			pkg['main']='main.py'
		if not pkg.has_key('version'):
			pkg['version']='0.1.0'
		if not (pkg.has_key('category') and pkg['category'] in ['system','broswer','editor']):
			pkg['category']= 'system'
		if not (pkg.has_key('platform') and pkg['platform'] in ['linux', 'windows', 'any']):
			pkg['platform']= 'any'
		if pkg.has_key('public'): 
			pass #TODO: expose public API here
		if pkg.has_key('dependency'):
			pluginDepsParse(pkg['dependency'])
		pass
	
	def pluginDepsParse(deps):
		__keys = ['python', 'apt']
		#TODO: check dependency here
		pass

	pass

class DomainHelper:
	"""docstring for DomainHelper
	Enum<plugin-code> ('SUCCESS', 'FAILED', 'PROXY')
	"""
	def __init__(self, ws_name, helper):
		self.name = ws_name
		self.ret_cod = helper['plugin_code']
		self.oracle = PluginOracle(helper['VDM_PLGS'])
		WRK=partial(pathShift, helper['VDM_WRKS'](ws_name))
		REP=partial(pathShift, helper['VDM_REPS'](ws_name))
		CFG=load_json(pathShift(helper['VDM_WRKS'](ws_name),'config.json'))
		self.PlgCol = dict()
		for plg in CFG['plugins']:
			self.PlgCol[plg] = self.oracle.query(plg, required=True)
			pass
		pluginListSort(self.PlgCol)
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
		for k,v in self.PlgCol.items():
			with tempSpace() as tmp:
				ret = v.onSave()
				pass
			pass
		pass

	def close_domain(self):
		for k,v in self.PlgCol.items():
			with tempSpace() as tmp:
				ret = v.onExit()
			pass
		pass

	def open_domain(self):
		for k,v in self.PlgCol.items():
			with tempSpace() as tmp:
				ret = v.onResume()
			pass
		pass