import os

from osgeo import gdalconst

from common_object.enum import NodataEnum, QcModeEnum, ViewEnum, RegionEnum
from common_util.common import convert_enum_to_value, concurrent_execute
from common_util.date import get_all_date_by_year
from common_util.image import mosaic, process_image_to_refer, read_raster, create_raster
from common_util.path import create_path
from data_perprocessing.entity import Path


def multi_data_to_region_by_year(path: Path, region, year, value_path, basename, tile_list, nodata, resample_alg=gdalconst.GRA_Bilinear):
    tile_list_str = "_".join(tile for tile in tile_list)
    mask_file = os.path.join(path.cloud_mask_path, f"mask_{region}.tif")
    mask_arr, geo_data = read_raster(mask_file)
    merged_path = os.path.join(value_path, tile_list_str)
    create_path(merged_path)
    clipped_path = os.path.join(value_path, region)
    create_path(clipped_path)
    if isinstance(year, list):
        date_list = year
    else:
        date_list = get_all_date_by_year(year)
    for date in date_list:
        basename_date = basename.replace("date", str(date))
        clipped_file = os.path.join(clipped_path, basename_date.replace("tile", region))
        if not os.path.isfile(clipped_file):
            value_file_list = [os.path.join(value_path, tile, basename_date.replace("tile", tile)) for tile in tile_list]
            value_file_list = list(filter(lambda value_file: os.path.isfile(value_file), value_file_list))
            if len(value_file_list) > 1:
                merged_file = os.path.join(merged_path, basename_date.replace("tile", tile_list_str))
                if not os.path.isfile(merged_file):
                    mosaic(value_file_list, merged_file, nodata, nodata)
                process_image_to_refer(merged_file, mask_file, clipped_file, nodata, nodata, resample_alg)
                clipped_arr = read_raster(clipped_file)[0]
                clipped_arr[mask_arr == NodataEnum.MASK.value] = nodata
                create_raster(clipped_file, clipped_arr, geo_data, nodata)
    print(basename, region, year)


def single_data_to_region(path: Path, region, value_path, basename, tile_list, nodata, resample_alg=gdalconst.GRA_Bilinear):
    tile_list_str = "_".join(tile for tile in tile_list)
    mask_file = os.path.join(path.cloud_mask_path, f"mask_{region}.tif")
    mask_arr, geo_data = read_raster(mask_file)
    clipped_file = os.path.join(value_path, basename.replace("tile", region))
    if not os.path.isfile(clipped_file):
        value_file_list = [os.path.join(value_path, basename.replace("tile", tile)) for tile in tile_list]
        value_file_list = list(filter(lambda value_file: os.path.isfile(value_file), value_file_list))
        if len(value_file_list) > 1:
            merged_file = os.path.join(value_path, basename.replace("tile", tile_list_str))
            if not os.path.isfile(merged_file):
                mosaic(value_file_list, merged_file, nodata, nodata)
            process_image_to_refer(merged_file, mask_file, clipped_file, nodata, nodata, resample_alg)
            clipped_arr = read_raster(clipped_file)[0]
            clipped_arr[mask_arr == NodataEnum.MASK.value] = nodata
            create_raster(clipped_file, clipped_arr, geo_data, nodata)
    print(basename, region)


def lst_data_to_region(path: Path, region, tile_list, year_list, pool_size=1):
    nodata_dict = {QcModeEnum.ALL.value.name: NodataEnum.TEMPERATURE.value, "time": NodataEnum.VIEW_TIME.value,
                   "angle": NodataEnum.VIEW_ANGLE.value}
    for view in convert_enum_to_value(ViewEnum):
        for field in [QcModeEnum.ALL.value.name, "time", "angle"]:

            value_path = os.path.join(path.lst_path, f"{view.view_name}_{field}")
            basename = f"{view.view_name}_tile_{field}_date.tif"
            args_list = []
            for year in year_list:
                args_list.append([path, region, year, value_path, basename, tile_list, nodata_dict[field], gdalconst.GRA_Bilinear])
            concurrent_execute(multi_data_to_region_by_year, args_list, pool_size)


def auxiliary_data_to_region(path: Path, region, tile_list):
    value_path = os.path.join(path.cloud_auxiliary_data_path, "latitude")
    basename = "lat_tile.tif"
    single_data_to_region(path, region, value_path, basename, tile_list, NodataEnum.LATITUDE_LONGITUDE.value)


def lc_data_to_region(path: Path, classification, region, tile_list, year_list):
    value_path = os.path.join(path.auxiliary_data_path, classification)
    basename = f"{classification}_tile_date.tif"
    multi_data_to_region_by_year(path, region, year_list, value_path, basename, tile_list, NodataEnum.LAND_COVER.value, resample_alg=gdalconst.GRA_NearestNeighbour)


def main():
    path = Path()
    region = RegionEnum.JIANG_SU.value
    tile_list = RegionEnum.JIANG_SU_TILE.value
    year_list = list(range(2000, 2024))
    # auxiliary_data_to_region(path, region, tile_list)
    lc_data_to_region(path, "IGBP", region, tile_list, year_list)


if __name__ == "__main__":
    main()
