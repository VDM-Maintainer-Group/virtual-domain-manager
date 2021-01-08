#!/usr/bin/env python3
import random, math, string
from crcmod import mkCrcFun
import logging
from termcolor import colored, cprint

def R_T(text): return colored(text, 'red')
def G_T(text): return colored(text, 'green')
def B_T(text): return colored(text, 'blue')
def C_T(text): return colored(text, 'cyan')
def M_T(text): return colored(text, 'magenta')
def Y_T(text): return colored(text, 'yellow')

def getRandomSerial(len, dtype='hex'):
    if dtype=='hex':
        return ''.join(random.choice(string.hexdigits.upper()) for _ in range(len))
    elif dtype=='dec':
        return ''.join(random.choice(string.digits) for _ in range(len))
    elif dtype=='char':
        return ''.join(random.choice(string.uppercase) for _ in range(len))
    else:
        return ''
    pass

def getChecksum(obj, dtype='crc-16'):
    _csm = ''
    #TODO: to support crc-16/md5/sha1
    return _csm