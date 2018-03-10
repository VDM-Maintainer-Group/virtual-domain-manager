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