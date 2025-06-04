from enum import Enum


class LayerEnum(Enum):
    # LST
    LST_DAY = 0
    LST_QC_DAY = 1
    LST_DAY_VIEW_TIME = 2
    LST_DAY_VIEW_ANGLE = 3
    LST_NIGHT = 4
    LST_QC_NIGHT = 5
    LST_NIGHT_VIEW_TIME = 6
    LST_NIGHT_VIEW_ANGLE = 7

    # Vegetation Index
    NDVI = 0
    EVI = 1

    # LandCover
    IGBP = 0
    UMD = 1
    LAI = 2
    BGC = 3
    PFT = 4
    LCCS1 = 5
    LCCS2 = 6
    LCCS3 = 7
