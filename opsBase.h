
// <Platform> * <Category> * <Software>
// Category-->software, then depending on Platform
// Platform selection with #define

#ifndef __OPS_BASE_H__
#define __OPS_BASE_H__

#include "opsUtility.h"

namespace opsBase
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

class opsBase
{
public:
	const uint8_t category, software;

	opsBase(category, software);
	virtual ~opsBase() = 0 {};
	virtual template_name(std::string file) = 0;
	
private:

};

#endif
