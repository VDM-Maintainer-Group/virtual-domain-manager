#include "opsUtility.h"

using namespace opsUtility;

uint8_t hashName(const std::string& appName)//CRC8-ATM
{
	boost::crc_optimal<8, 0x07, 0xFF, 0, false, false> crc8_atm;
    crc8_atm.process_bytes(appName.data(), appName.length());
    return crc8_atm.checksum();
}

void createJSON(QString* str, const QJsonObject& obj)
{
	QJsonDocument document;
	document.setObject(obj);
	QByteArray byte_array = document.toJson(QJsonDocument::Compact);
	str = std::move(json_str(byte_array));
}

void parseJSON(const QString& str, QJsonObject *obj)
{
	QJsonDocument doc = QJsonDocument::fromJson(str.toUtf8());
	obj = doc.object();
	//QJsonValue val = obj.value(QString("key_name"));
	//QJsonObject item = val.toObject();
	//(QJsonValue)(item["key_name_value"]).toString()
	//(QJsonValue)(item["key_name_array"]).toArray(), QJsonArray
}
