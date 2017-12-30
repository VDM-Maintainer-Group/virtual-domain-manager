'''
Math: useful math function utilities
@author: Mark Hong
@level: release
'''
import random, math, string
from crcmod import mkCrcFun

def sign(num):
	return num/abs(num)

def pos(num):
	return 0 if num>0 else 1

def randomString(len, dtype='hex'):
	data = ''
	if dtype=='hex':
		data = ''.join(random.choice(string.hexdigits.upper()) for x in xrange(len))
	elif dtype=='dec':
		data = ''.join(random.choice(string.digits) for x in xrange(len))
	elif dtype=='char':
		data = ''.join(random.choice(string.uppercase) for x in xrange(len))
	else:
		pass
	return data

def crcFactory(dtype='crc-16'):
	if dtype=='crc-32':
		return mkCrcFun(0x104C11DB7, initCrc=0x00000000, xorOut=0xFFFFFFFF)
	elif dtype=='crc-8':
		return mkCrcFun(0x107, rev=False, initCrc=0x00, xorOut=0x00)
	else:
		return mkCrcFun(0x18005, initCrc=0x0000, xorOut=0x0000)
	pass
