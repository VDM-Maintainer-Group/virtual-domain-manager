
// <Platform> * <Category> * <Software>
// Category-->software, then depending on Platform
// Platform selection with #define

#ifndef __OPS_BASE_H__
#define __OPS_BASE_H__

#include "opsUtility.h"

class opsBase
{
public:
	const uint8_t category, software;

	opsBase(category, software);
	virtual ~opsBase() = 0 {};
	virtual template_name(std::string file) = 0;

	virtual void load(int code=0, char* param);
	virtual void fetch(int code=0);
	
private:

};

#endif
