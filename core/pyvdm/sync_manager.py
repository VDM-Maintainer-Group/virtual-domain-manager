#!/usr/bin/python3
"""
Sync Manager
@author: Mark Hong
@desc: sync your domain space and repo, support git etc.
"""
from optparse import OptionParser

def main():
	pass

if __name__ == '__main__':
	global options
	parser = OptionParser()
	parser.add_option("-l", "--list",
		action="store_true",
		dest="list_flag", 
		default=False, 
		help="list domain sync status.")

	(options, args) = parser.parse_args()
	main()