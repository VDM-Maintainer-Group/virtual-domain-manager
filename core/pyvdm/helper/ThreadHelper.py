'''
ThreadHelper: useful thread function utilities
@author: Mark Hong
@level: debug
'''
import time, threading, greenlet

def startThread(target, args=()):
	''' start a daemon default thread
	'''
	args = tuple(args)
	t = threading.Thread(target=target, args=args)
	t.setDaemon(True)
	t.start()
	return t

def watchLoop(handle_t, hook=None, interval=0.5):
	while True:
		for t in handle_t:
			if not t.isAlive():
				if hook==None:
					exit()
				else:
					hook()
				pass
			pass
		time.sleep(interval)
		pass
	pass

#TODO: next rewrite with greenlet, factory and collection
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

def joinHelper(t_tuple):
	for t in t_tuple:
		try:
			if not t.is_alive(): t.join()
		except Exception as e:
			raise e
		pass
	pass