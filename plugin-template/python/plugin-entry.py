
def init(): # one-time@startup
	required('helper.HookHelper')
	required('helper.PathHelper')
	required('helper.ImportHelper')
	required('sys', 'argv')
	PLUGIN_ORDER = -1
	pass

def onSave():
	return 0

def onResume():
	return 0

def onExit():
	return 0

def onTrigger(*args): # manually by user
	return 0

def onDaemon(): # not implement yet
	return 0