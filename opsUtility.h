#ifndef __OPS_UTILITY_H__
#define __OPS_UTILITY_H__

#define Linux	0x0
#define Windows 0x1

#include <boost/crc.hpp> //for hashName

namespace opsUtility
{
	uint8_t hashName(const std::string& appName);
	
	void createJSON(QString* str, const QJsonObject& obj);
	void parseJSON(const QString& str, QJsonObject *obj);

	int execShell(char* param);
	int execShellSync(char* param);
}

/*Begin: Compiling Parameter Section*/
#define Platform Linux // or Windows
/*End: Compiling Parameter Section*/

#endif