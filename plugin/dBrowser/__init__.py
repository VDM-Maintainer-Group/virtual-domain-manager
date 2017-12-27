import os as __os_none__

__all__ = []
__broswer_dir__ = __os_none__.path.dirname(__file__)

for __broswer_file__ in __os_none__.listdir(__broswer_dir__):
	if __os_none__.path.isdir(__os_none__.path.join(__broswer_dir__, __broswer_file__)):
		__import__(__broswer_file__, globals(), locals())
