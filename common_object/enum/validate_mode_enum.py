from enum import Enum


class ValidateModeEnum(Enum):
    RANDOM = "random"
    TILE = "tile"
    TIME = "time"
    FILE_ALL = "file_all"
    FILE_GQ = "file_gq"
    FILE_OQ = "file_oq"
    SPECIFIC_FILE = "specific_file"
    SIMULATE = "simulate"
    NONE = "none"

    ESTIMATE = "estimate"
    INTERPOLATE_REFER = "interpolate_refer"
    INTERPOLATE_OTHER = "interpolate_other"
    INTERPOLATE = "interpolate"
    OVERALL = "overall"
