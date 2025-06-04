import os.path

import numpy as np
from osgeo import gdal, gdalconst

from common_object.enum import SRSEnum, NodataEnum
from common_util.image import process_image_with_args, read_raster, create_raster, process_image_to_refer
from data_perprocessing.entity.path import Path


def reproject_climate_zone(path: Path):
    climate_file = os.path.join(path.cloud_climate_path, "Beck_KG_V1_present_0p083.tif")
    wgs_climate_file = os.path.join(path.cloud_climate_path, "wgs_climate_zone.tif")
    process_image_with_args(climate_file, wgs_climate_file, SRSEnum.WGS84.value, gdal.GRA_NearestNeighbour, 0.01, NodataEnum.CLIMATE.value, NodataEnum.CLIMATE.value, gdalconst.GDT_Int16)


def reclass_climate_zone(path: Path, reclass_dict):
    climate_zone_arr, geo_data = read_raster(os.path.join(path.cloud_climate_path, "wgs_climate_zone.tif"))
    for new_class, class_list in reclass_dict.items():
        for origin_class in class_list:
            climate_zone_arr[climate_zone_arr == origin_class] = new_class
    wgs_climate_file = os.path.join(path.cloud_climate_path, f"wgs_climate_zone_{len(reclass_dict.keys())}classes.tif")
    create_raster(wgs_climate_file, climate_zone_arr, geo_data, NodataEnum.CLIMATE.value, output_type=gdalconst.GDT_Int16)
    refer_file = os.path.join(path.annual_ta_path, "world", "mean_annual_ta_world.tif")
    climate_file = os.path.join(path.cloud_climate_path, f"climate_zone_{len(reclass_dict.keys())}classes.tif")
    process_image_to_refer(wgs_climate_file, refer_file, climate_file, NodataEnum.CLIMATE.value, NodataEnum.CLIMATE.value, resample_alg=gdal.GRA_NearestNeighbour)


def create_hemisphere_mask(path: Path):
    mean_annual_ta_arr, geo_data = read_raster(os.path.join(path.annual_ta_path, "world", "mean_annual_ta_world.tif"))
    hemisphere_mask_arr = np.full_like(mean_annual_ta_arr, 1)
    hemisphere_mask_arr[int(hemisphere_mask_arr.shape[0] / 2):, :] = -1
    create_raster(os.path.join(path.cloud_climate_path, "hemisphere_mask.tif"), hemisphere_mask_arr, geo_data, NodataEnum.MASK.value, output_type=gdalconst.GDT_Int16)
    wgs_climate_arr, geo_data = read_raster(os.path.join(path.cloud_climate_path, "wgs_climate_zone.tif"))
    wgs_hemisphere_mask_arr = np.full_like(wgs_climate_arr, 1)
    wgs_hemisphere_mask_arr[int(wgs_hemisphere_mask_arr.shape[0]/2):, :] = -1
    create_raster(os.path.join(path.cloud_climate_path, "wgs_hemisphere_mask.tif"), wgs_hemisphere_mask_arr, geo_data, NodataEnum.MASK.value, output_type=gdalconst.GDT_Int16)


def main():
    path = Path()
    reclass_dict = {1: [1],
                    2: [2],
                    3: [3],
                    4: [4, 5],
                    5: [6, 7],
                    6: [8, 11, 14],
                    7: [9, 10, 12, 13, 15, 16],
                    8: [17, 18, 21, 22, 25, 26],
                    9: [19, 20, 23, 24, 27, 28],
                    10: [29, 30]}
    # reproject_climate_zone(path)
    # reclass_climate_zone(path, reclass_dict)
    create_hemisphere_mask(path)


if __name__ == "__main__":
    main()
