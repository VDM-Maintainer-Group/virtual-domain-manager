'''
PrintHelper: useful print function utilities
@author: Mark Hong
@level: debug
'''
from termcolor import colored, cprint

def printh(tip, cmd, color=None, split=' '):
	print(
		colored('[%s]%s'%(tip, split), 'magenta')
		+ colored(cmd, color)
		+ ' '
		)
	pass

def log_sucess(prompt):
	pass

def log_normal(prompt):
	pass

def log_warn(prompt):
	pass

def log_error(prompt):
	pass