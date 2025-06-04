from enum import Enum

from common_object.entity.qc_mode import QcMode


class QcModeEnum(Enum):
    GOOD_QUALITY = QcMode("goodquality", "GQ")
    OTHER_QUALITY = QcMode("orderquality", "OQ")
    ALL = QcMode("all", "ALL")
