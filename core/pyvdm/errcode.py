
from enum import Enum,auto

class PluginCode(Enum):
    _ = 1
    CONFIG_REQUIRED_FIELD_MISSING = auto()
    CONFIG_MAIN_ENTRY_ILLEGAL = auto()
    CONFIG_MAIN_ENTRY_MISSING = auto()
    CONFIG_FILE_MISSING = auto()
    ARCHIVE_INVALID = auto()
    ARCHIVE_UNPACK_FAILED = auto()
    PLUGIN_BUILD_FAILED = auto()
    PLUGIN_LOAD_FAILED = auto()
    PLUGIN_WRAPPER_FAILED = auto()
    PLUGIN_HIGHER_VERSION = auto()
    pass

class DomainCode(Enum):
    _ = 1
    DOMAIN_ALREADY_EXIST = auto()
    DOMAIN_CONFIG_FAILED = auto()
    DOMAIN_IS_OPEN = auto()
    DOMAIN_NOT_EXIST = auto()
    pass
