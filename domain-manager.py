#!/usr/bin/python
from os import path, _exit
from optparse import OptionParser
from Utility.Utility import printh, load_json
from manager import *

def m_exit():
	_exit(-1)
	pass

def main():
	print(path.dirname(path.realpath(__file__)))
	pass

if __name__ == '__main__':
	global options
	parser = OptionParser()
	parser.add_option("-a", "--new",
		dest="new_name", 
		default="", 
		help="create a new workspace")
	parser.add_option("-s", "--save",
		dest="save_dest", 
		default="", 
		help="save the current workspace")
	parser.add_option("-o", "--open",
		dest="open_name", 
		default="", 
		help="open an existing workspace")
	parser.add_option("-r", "--rename",
		dest="rename", 
		default="", 
		help="rename an existing workspace")
	(options, args) = parser.parse_args()

	try: #cope with Interrupt Signal
		main()
	except Exception as e:
		printh('Terminal', e, 'red') #for debug
		pass
	finally:
		m_exit()