#!/usr/bin/env python3
''' Plugin Template
'''

def init():
	addPythonEnv(['./', '~/'])
	addCDllEnv('./bin')
	PLUGIN_ORDER = -1
	required('helper', 'PathHelper')
	# required('helper', 'HookHelper')
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
	if args[0]=='sayHello': printf("%s\n", "Hello World!")
	return 0

def onDaemon(): # not implement yet
	return 0