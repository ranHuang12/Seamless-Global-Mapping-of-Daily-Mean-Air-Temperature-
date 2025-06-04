import os

import numpy as np

from common_object.entity import BasePath
from common_object.enum import NodataEnum
from common_util.image import read_raster, create_raster


def create_xy_index_from_mask(path: BasePath, refer_tile):
    mask_arr, geo_data = read_raster(os.path.join(path.cloud_mask_path, f"{refer_tile}_mask.tif"))
    xindex_arr = np.array([range(0, np.shape(mask_arr)[0]) for i in range(0, np.shape(mask_arr)[1])])
    create_raster(os.path.join(path.cloud_xy_index_path, f"x_index.tif"), xindex_arr, geo_data, NodataEnum.XY_INDEX.value)
    yindex_arr = np.array([[index for i in range(0, np.shape(mask_arr)[1])] for index in range(0, np.shape(mask_arr)[1])])
    create_raster(os.path.join(path.cloud_xy_index_path, f"y_index.tif"), yindex_arr, geo_data, NodataEnum.XY_INDEX.value)


if __name__ == "__main__":
    path = BasePath()
    create_xy_index_from_mask(path, "h03v06")
