#ifndef __OPS_COLLECTION_H__
#define __OPS_COLLECTION_H__

#include "opsBase.h"

namespace opsCollection
{
	//no enumerations for *Platform*, by compiling defines

	enum Category
	{
		documents	=	0x01,
		entities	=	0x02,
		notes		=	0x03,
		os_status	=	0x04,
		webpages	=	0x05
	};

	enum Software
	{
		//documents
		FoxitReader	=	0xB7,
		WPS-Writer	=	0xD4,
		WPS-PPT		=	0x82,
		//entity
		Notifier	=	0xA0,
		//notes
		gedit		=	0xF3,
		Typora		=	0xB1,
		Sublime		=	0xA4,
		//os_status
		Modifier	=	0x0B,
		//webpages
		Chrome		=	0x04,
		Firefox		=	0x02
	};
}

class web_chrome_op : opsBase
{
public:
	web_chrome_op();
	~web_chrome_op();
	
};

class opsCollection
{
public:
	opsCollection();
	~opsCollection();
	
};


#endif
