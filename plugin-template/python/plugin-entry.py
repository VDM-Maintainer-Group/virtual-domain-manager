
def init():
	addPythonEnv(['./', '~/'])
	addCDllEnv(['./bin', '/usr/bin'])
	PLUGIN_ORDER = -1
	required('helper', 'PathHelper')
	required('helper', 'HookHelper')
	required('helper', 'IpcHelper')
	required('helper', 'WindowHelper')
	required('helper', 'ThreadHelper')
	required('libc.so.6', 'printf')
	required('sys', 'argv')
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