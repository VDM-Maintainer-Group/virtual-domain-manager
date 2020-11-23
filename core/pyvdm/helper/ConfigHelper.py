'''
ConfigHelper: useful configuration function utilities
@author: Mark Hong
@level: debug
'''
import json

def testStat(stat):
	if stat=='' or stat=='closed':
		return False
	elif stat=='open':
		return True
	else:
		return None

def putStat(uri, stat):
	with open(uri, 'w') as f:
		f.write(stat)
	pass

def getStat(uri):
	with open(uri, 'r') as f:
		return f.read()
	return ""

def load_json(uri):
	try:
		with open(uri, 'r') as cf:
			return json.load(cf)
	except Exception as e:
		raise e
	pass

def save_json(config, uri):
	try:
		with open(uri, 'w') as cf:
			json.dump(config, cf)
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