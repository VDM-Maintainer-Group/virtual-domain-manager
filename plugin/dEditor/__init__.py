import os as __os_none__

__editor_dir__ = __os_none__.path.dirname(__file__)

for __editor_file__ in __os_none__.listdir(__editor_dir__):
	if __os_none__.path.isdir(__os_none__.path.join(__editor_dir__, __editor_file__)):
		__import__(__editor_file__, globals(), locals())
