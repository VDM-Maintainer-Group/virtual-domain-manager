'''
ConfigHelper: useful configuration function utilities
@author: Mark Hong
@level: debug
'''
import json

def load_json(uri):
	try:
		with open(uri) as cf:
			return json.load(cf)
	except Exception as e:
		raise e
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