
from enum import Enum,IntEnum

class ErrorCode(Enum): pass

## Enum Code Section
class PluginCode(ErrorCode):
    ALL_CLEAN = 0x0000
    CONFIG_REQUIRED_FIELD_MISSING = 0x1001
    CONFIG_MAIN_ENTRY_ILLEGAL     = 0x1002
    CONFIG_MAIN_ENTRY_MISSING     = 0x1003
    CONFIG_FILE_MISSING           = 0x1004
    ARCHIVE_INVALID               = 0x1005
    ARCHIVE_UNPACK_FAILED         = 0x1006
    PLUGIN_BUILD_FAILED           = 0x1007
    PLUGIN_LOAD_FAILED            = 0x1008
    PLUGIN_WRAPPER_FAILED         = 0x1009
    PLUGIN_HIGHER_VERSION_EXISTS  = 0x100A
    PLUGIN_CAPABILITY_MISSING     = 0x100B
    pass

class DomainCode(ErrorCode):
    ALL_CLEAN = 0x0000
    DOMAIN_ALREADY_EXIST    = 0x1010
    DOMAIN_CONFIG_FAILED    = 0x1020
    DOMAIN_IS_OPEN          = 0x1030
    DOMAIN_NOT_EXIST        = 0x1040
    #
    DOMAIN_NOT_OPEN         = 0x1050
    DOMAIN_LOAD_FAILED      = 0x1060
    DOMAIN_SAVE_FAILED      = 0x1070
    DOMAIN_START_FAILED     = 0x1080
    DOMAIN_RESUME_FAILED    = 0x1090
    DOMAIN_CLOSE_FAILED     = 0x10A0
    DOMAIN_STOP_FAILED      = 0x10B0
    DOMAIN_NAME_INVALID     = 0x10C0
    DOMAIN_NESTED_DOMAIN    = 0x10D0
    pass

class CapabilityCode(ErrorCode):
    ALL_CLEAN = 0x0000
    VCD_INTERNAL_ERROR    = 0x1100
    ARCHIVE_UNPACK_FAILED = 0x1200
    URL_PARSE_FAILURE     = 0x1300
    DAEMON_ALREADY_EXISTS = 0x1400
    DAEMON_IS_RUNNING     = 0x1500
    DAEMON_IS_STOPPED     = 0x1600
    pass

class ApplicationCode(ErrorCode):
    ALL_CLEAN = 0x0000
    pass

## Bare Code Section
ALL_CLEAN = 0x0000
# for plugin use
CONFIG_REQUIRED_FIELD_MISSING   = 0x1001
CONFIG_MAIN_ENTRY_ILLEGAL       = 0x1002
CONFIG_MAIN_ENTRY_MISSING       = 0x1003
CONFIG_FILE_MISSING             = 0x1004
ARCHIVE_INVALID                 = 0x1005
ARCHIVE_UNPACK_FAILED           = 0x1006
PLUGIN_BUILD_FAILED             = 0x1007
PLUGIN_LOAD_FAILED              = 0x1008
PLUGIN_WRAPPER_FAILED           = 0x1009
PLUGIN_HIGHER_VERSION           = 0x100A
PLUGIN_CAPABILITY_MISSING       = 0x100B
# for domain use
DOMAIN_ALREADY_EXIST            = 0x1010
DOMAIN_CONFIG_FAILED            = 0x1020
DOMAIN_IS_OPEN                  = 0x1030
DOMAIN_NOT_EXIST                = 0x1040
DOMAIN_NOT_OPEN                 = 0x1050
DOMAIN_LOAD_FAILED              = 0x1060
DOMAIN_SAVE_FAILED              = 0x1070
DOMAIN_START_FAILED             = 0x1080
DOMAIN_RESUME_FAILED            = 0x1090
DOMAIN_CLOSE_FAILED             = 0x10A0
DOMAIN_STOP_FAILED              = 0x10B0
DOMAIN_NAME_INVALID             = 0x10C0
DOMAIN_NESTED_DOMAIN            = 0x10D0
# for capability use
VCD_INTERNAL_ERROR              = 0x1100
ARCHIVE_UNPACK_FAILED           = 0x1200
URL_PARSE_FAILURE               = 0x1300
DAEMON_ALREADY_EXISTS           = 0x1400
DAEMON_IS_RUNNING               = 0x1500
DAEMON_IS_STOPPED               = 0x1600
