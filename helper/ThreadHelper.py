'''
ThreadHelper: useful thread function utilities
@author: Mark Hong
@level: debug
'''
import threading, greenlet

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

def joinHelper(t_tuple):
	for t in t_tuple:
		try:
			if not t.is_alive(): t.join()
		except Exception as e:
			raise e
		pass
	pass