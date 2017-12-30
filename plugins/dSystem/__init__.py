import os as __os_none__

__system_dir__ = __os_none__.path.dirname(__file__)

for __system_file__ in __os_none__.listdir(__system_dir__):
	if __os_none__.path.isdir(__os_none__.path.join(__system_dir__, __system_file__)):
		try:
			__import__(__system_file__, globals(), locals())
		except Exception as e:
			print(e)
			pass
