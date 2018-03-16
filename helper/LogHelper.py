'''
PrintHelper: useful print function utilities
@author: Mark Hong
@level: debug
'''
from __future__ import print_function
from termcolor import colored, cprint

def R_T(text): return colored(text, 'red')
def G_T(text): return colored(text, 'green')
def B_T(text): return colored(text, 'blue')
def C_T(text): return colored(text, 'cyan')
def M_T(text): return colored(text, 'magenta')
def M_T(text): return colored(text, 'yellow')

def printh(tip, cmd, tip_color=None, cmd_color=None, split=' ', end='\n'):
	print(colored('[%s]%s'%(tip, split), tip_color) 
			+ colored(cmd, cmd_color), end=end)

def logArgsHelper(args, kwargs):
	if len(args)==1: args=args[0]
	return str(args)

def logNormal(*args, **kwargs):
	args = logArgsHelper(args, kwargs)
	printh('LOGGING',	args,	None,None,			' '*2)
	pass

def logSuccess(*args, **kwargs):
	args = logArgsHelper(args, kwargs)
	printh('SUCCESS',	args,	'green','green',	' '*2)
	pass

def logWarning(*args, **kwargs):
	args = logArgsHelper(args, kwargs)
	printh('WARNING',	args,	'yellow','yellow',	' '*2)
	pass

def logError(*args, **kwargs):
	args = logArgsHelper(args, kwargs)
	printh('ERROR',		args,	'red','red',		' '*4)
	pass

def logHelp(*args, **kwargs):
	text = logArgsHelper(args[1:], kwargs)
	printh(args[0],		text,	'magenta',None,		' '*2)
	pass

def logConsole(*args, **kwargs):
	__text = logArgsHelper(args[1:], kwargs)
	__text += '\n>>> '
	printh(args[0],		__text,	'magenta',None,		' '*1, end='')
	__text = raw_input()
	return __text if __text!='' else kwargs['default']