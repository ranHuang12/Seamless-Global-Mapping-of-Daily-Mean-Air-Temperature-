from enum import Enum

from osgeo import gdalconst


class TypeEnum(Enum):
    TEMPERATURE = gdalconst.GDT_Int32
