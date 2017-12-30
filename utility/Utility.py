'''
Utility: useful general function utilities
@author: Mark Hong
@level: debug
'''
import json, threading, greenlet
from termcolor import colored, cprint

def load_json(uri):
	try:
		with open(uri) as cf:
			return json.load(cf)
	except Exception as e:
		raise e
	pass

def printh(tip, cmd, color=None, split=' '):
	print(
		colored('[%s]%s'%(tip, split), 'magenta')
		+ colored(cmd, color)
		+ ' '
		)
	pass

def cmd_parse(str):
	op, cmd = '', []
	op_tuple = str.lower().strip().split(' ')
	op = op_tuple[0]
	if len(op_tuple) > 1:
		cmd = op_tuple[1:]
		pass
	return op, cmd
	pass

#next rewrite with greenlet, factory and collection
def exec_watch(process, hook=None, fatal=False, gen=True):
	if gen:#external loop
		process.start()
		t = threading.Thread(target=exec_watch, args=(process, hook, fatal, False))
		t.setDaemon(True)
		t.start()
		pass
	else:#internal loop
		while process.is_alive(): pass
		if fatal and hook: hook()
		pass
	pass

def join_helper(t_tuple):
	for t in t_tuple:
		try:
			if not t.is_alive(): t.join()
		except Exception as e:
			raise e
		pass
	pass
	