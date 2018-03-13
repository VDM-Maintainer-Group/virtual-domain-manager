
def init(): # one-time@startup
	required('helper.HookHelper')
	required('helper.PathHelper')
	required('helper.ImportHelper')
	required('sys', 'argv')
	PLUGIN_ORDER = -1
	pass

def onSave():
	pass

def onResume():
	pass

def onExit():
	pass

def onTrigger(*args): # manually by user
	pass

def onDaemon(): # not implement yet
	pass