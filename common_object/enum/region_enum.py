from enum import Enum


class RegionEnum(Enum):
    ZHE_JIANG = "zhejiang"
    ZHE_JIANG_TILE = ["h28v05", "h28v06"]

    JIANG_SU = "jiangsu"
    JIANG_SU_TILE = ["h27v05", "h28v05"]

    DONG_BEI = "dongbei"
    DONG_BEI_TILE = ["h25v03", "h25v04", "h26v03", "h26v04", "h27v04", "h27v05"]

    CHINA = "China"
    CHINA_TILE = ["h23v04", "h23v05",
                  "h24v04", "h24v05",
                  "h25v03", "h25v04", "h25v05", "h25v06",
                  "h26v03", "h26v04", "h26v05", "h26v06",
                  "h27v04", "h27v05", "h27v06",
                  "h28v05", "h28v06", "h28v07", "h28v08",
                  "h29v06", "h29v07", "h29v08"]
