from enum import Enum


class NodataEnum(Enum):
    MODIS_LST = 0
    LST = 255
    VIEW_TIME = 255
    VIEW_ANGLE = 255
    VEGETATION_INDEX = -3000
    TEMPERATURE = 32767
    LAND_COVER = 255

    GVE_DEM = 9998
    GVE_WATER = -9999
    GMTED_DEM = -32768
    DEM = 32767
    LATITUDE_LONGITUDE = 32767
    MASK = 0
    STATION = 0
    XY_INDEX = 1200
    CLIMATE = 0

    DATE = 0

    COVERAGE = 0
