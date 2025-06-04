import os

import numpy as np
import pandas as pd
from osgeo import gdalconst

from common_object.enum import NodataEnum, SRSEnum
from common_util.common import get_world_tile, concurrent_execute
from common_util.date import get_all_date_by_month, get_day_num_by_month, get_day_num_by_year
from common_util.document import to_csv
from common_util.image import read_raster, create_raster, process_image_with_args
from common_util.path import create_path
from ta_estimate.post_process import merge_ta
from ta_interpolate.entity import Path


def create_annual_monthly_ta_by_tile(path: Path, tile, year_list):
    temperature_nodata = NodataEnum.TEMPERATURE.value
    mask_arr, geo_data = read_raster(os.path.join(path.cloud_mask_path, f"mask_{tile}.tif"))
    interpolate_ta_path = os.path.join(path.interpolate_ta_path, tile)
    annual_ta_path = os.path.join(path.annual_ta_path, tile)
    create_path(annual_ta_path)
    monthly_ta_path = os.path.join(path.monthly_ta_path, tile)
    create_path(monthly_ta_path)
    annual_ta_record_csv = os.path.join(path.cloud_annual_ta_path, f"annual_ta_record_{tile}.csv")
    monthly_ta_record_csv = os.path.join(path.cloud_monthly_ta_path, f"monthly_ta_record_{tile}.csv")
    for year in year_list:
        annual_ta_file = os.path.join(annual_ta_path, f"annual_ta_{tile}_{year}.tif")
        if os.path.isfile(annual_ta_file):
            continue
        annual_ta_arr = np.zeros_like(mask_arr).astype(np.int32)
        annual_condition = (mask_arr == NodataEnum.MASK.value)
        for month in range(1, 13):
            monthly_ta_file = os.path.join(monthly_ta_path, f"monthly_ta_{tile}_{year}_{str(month).zfill(2)}.tif")
            monthly_condition = (mask_arr == NodataEnum.MASK.value)
            if os.path.isfile(monthly_ta_file):
                continue
            monthly_ta_arr = np.zeros_like(mask_arr).astype(np.int32)
            for date in get_all_date_by_month(year, month):
                ta_file = os.path.join(interpolate_ta_path, f"ta_{tile}_{date}.tif")
                ta_arr = read_raster(ta_file)[0]
                annual_ta_arr += ta_arr
                monthly_ta_arr += ta_arr
                annual_condition |= (ta_arr == temperature_nodata)
                monthly_condition |= (ta_arr == temperature_nodata)
            monthly_ta_arr //= get_day_num_by_month(year, month)
            monthly_ta_arr[monthly_condition] = temperature_nodata
            create_raster(monthly_ta_file, monthly_ta_arr, geo_data, temperature_nodata)
            monthly_ta_value_arr = monthly_ta_arr[monthly_ta_arr != temperature_nodata]
            record_dict = {"month": [year*100+month], "sum": [monthly_ta_value_arr.size], "min_ta": [np.min(monthly_ta_value_arr) / 100],
                           "avg_ta": [np.average(monthly_ta_value_arr) / 100], "max_ta": [np.max(monthly_ta_value_arr) / 100]}
            to_csv(pd.DataFrame(record_dict), monthly_ta_record_csv)
        annual_ta_arr //= get_day_num_by_year(year)
        annual_ta_arr[annual_condition] = temperature_nodata
        create_raster(annual_ta_file, annual_ta_arr, geo_data, temperature_nodata)
        annual_ta_value_arr = annual_ta_arr[annual_ta_arr != temperature_nodata]
        record_dict = {"year": [year], "sum": [annual_ta_value_arr.size], "min_ta": [np.min(annual_ta_value_arr) / 100],
                       "avg_ta": [np.average(annual_ta_value_arr) / 100], "max_ta": [np.max(annual_ta_value_arr) / 100]}
        to_csv(pd.DataFrame(record_dict), annual_ta_record_csv)
        print(tile, record_dict)
    mean_annual_ta_arr = np.zeros_like(mask_arr).astype(np.int32)
    condition = (mask_arr == NodataEnum.MASK.value)
    for year in year_list:
        annual_ta_arr = read_raster(os.path.join(annual_ta_path, f"annual_ta_{tile}_{year}.tif"))[0]
        mean_annual_ta_arr += annual_ta_arr
        condition |= (annual_ta_arr == temperature_nodata)
    mean_annual_ta_arr //= len(year_list)
    mean_annual_ta_arr[condition] = temperature_nodata
    create_raster(os.path.join(annual_ta_path, f"mean_annual_ta_{tile}.tif"), mean_annual_ta_arr, geo_data, temperature_nodata)
    for month in range(1, 13):
        mean_monthly_ta_arr = np.zeros_like(mask_arr).astype(np.int32)
        condition = (mask_arr == NodataEnum.MASK.value)
        for year in year_list:
            monthly_ta_arr = read_raster(os.path.join(monthly_ta_path, f"monthly_ta_{tile}_{year}_{str(month).zfill(2)}.tif"))[0]
            mean_monthly_ta_arr += monthly_ta_arr
            condition |= (monthly_ta_arr == temperature_nodata)
        mean_monthly_ta_arr //= len(year_list)
        mean_monthly_ta_arr[condition] = temperature_nodata
        create_raster(os.path.join(monthly_ta_path, f"mean_monthly_ta_{tile}_{str(month).zfill(2)}.tif"), mean_monthly_ta_arr, geo_data, temperature_nodata)


def create_annual_monthly_ta(path: Path, tile_list, year_list, pool_size=1):
    args_list = []
    for tile in tile_list:
        args_list.append([path, tile, year_list])
    concurrent_execute(create_annual_monthly_ta_by_tile, args_list, pool_size, False)


def merge_annual_monthly_ta(path, region, tile_list, year_list):
    annual_ta_region_path = os.path.join(path.annual_ta_path, region)
    monthly_ta_region_path = os.path.join(path.monthly_ta_path, region)
    monthly_ta_record_csv = os.path.join(path.cloud_monthly_ta_path, f"monthly_ta_record_{region}.csv")
    annual_ta_record_csv = os.path.join(path.cloud_annual_ta_path, f"annual_ta_record_{region}.csv")
    for year in year_list:
        for month in range(1, 13):
            monthly_ta_region_file = os.path.join(monthly_ta_region_path, f"monthly_ta_{region}_{year}_{str(month).zfill(2)}.tif")
            if not os.path.isfile(monthly_ta_region_file):
                monthly_ta_file_list = [os.path.join(path.monthly_ta_path, tile, f"monthly_ta_{tile}_{year}_{str(month).zfill(2)}.tif") for tile in tile_list]
                merge_ta(monthly_ta_file_list, monthly_ta_region_file, monthly_ta_record_csv, "year", year * 100 + month)
        annual_ta_region_file = os.path.join(annual_ta_region_path, f"annual_ta_{region}_{year}.tif")
        if not os.path.isfile(annual_ta_region_file):
            annual_ta_file_list = [os.path.join(path.annual_ta_path, tile, f"annual_ta_{tile}_{year}.tif") for tile in tile_list]
            merge_ta(annual_ta_file_list, annual_ta_region_file, annual_ta_record_csv, "month", year)
    mean_annual_ta_region_file = os.path.join(annual_ta_region_path, f"mean_annual_ta_{region}.tif")
    if not os.path.isfile(mean_annual_ta_region_file):
        mean_annual_ta_file_list = [os.path.join(path.annual_ta_path, tile, f"mean_annual_ta_{tile}.tif") for tile in tile_list]
        merge_ta(mean_annual_ta_file_list, mean_annual_ta_region_file, annual_ta_record_csv, "year", "mean")
    for month in range(1, 13):
        mean_monthly_ta_region_file = os.path.join(monthly_ta_region_path, f"mean_monthly_ta_{region}_{str(month).zfill(2)}.tif")
        if not os.path.isfile(mean_monthly_ta_region_file):
            mean_monthly_ta_file_list = [os.path.join(path.monthly_ta_path, tile, f"mean_monthly_ta_{tile}_{str(month).zfill(2)}.tif") for tile in tile_list]
            merge_ta(mean_monthly_ta_file_list, mean_monthly_ta_region_file, monthly_ta_record_csv, "month", month)


def reproject_regional_annual_monthly_ta(path, region, year_list):
    temperature_nodata = NodataEnum.TEMPERATURE.value
    annual_ta_region_path = os.path.join(path.annual_ta_path, region)
    monthly_ta_region_path = os.path.join(path.monthly_ta_path, region)
    """
    for year in year_list:
        wgs_annual_ta_region_file = os.path.join(annual_ta_region_path, f"wgs_annual_ta_{region}_{year}.tif")
        if not os.path.isfile(wgs_annual_ta_region_file):
            annual_ta_region_file = os.path.join(annual_ta_region_path, f"annual_ta_{region}_{year}.tif")
            process_image_with_args(annual_ta_region_file, wgs_annual_ta_region_file, SRSEnum.WGS84.value, res=0.01,
                                    srcNodata=temperature_nodata, dstNodata=temperature_nodata)
            print(year)
        for month in range(1, 13):
            wgs_monthly_ta_region_file = os.path.join(monthly_ta_region_path, f"wgs_monthly_ta_{region}_{year}_{str(month).zfill(2)}.tif")
            if not os.path.isfile(wgs_monthly_ta_region_file):
                monthly_ta_region_file = os.path.join(monthly_ta_region_path, f"monthly_ta_{region}_{year}_{str(month).zfill(2)}.tif")
                process_image_with_args(monthly_ta_region_file, wgs_monthly_ta_region_file, SRSEnum.WGS84.value, res=0.01,
                                        srcNodata=temperature_nodata, dstNodata=temperature_nodata)
                print(year, month)
    """
    wgs_mean_annual_ta_region_file = os.path.join(annual_ta_region_path, f"wgs_mean_annual_ta_{region}.tif")
    if not os.path.isfile(wgs_mean_annual_ta_region_file):
        mean_annual_ta_region_file = os.path.join(annual_ta_region_path, f"mean_annual_ta_{region}.tif")
        process_image_with_args(mean_annual_ta_region_file, wgs_mean_annual_ta_region_file, SRSEnum.WGS84.value, res=0.01,
                                srcNodata=temperature_nodata, dstNodata=temperature_nodata)
        print("mean annual")
    for month in range(1, 13):
        wgs_mean_monthly_ta_region_file = os.path.join(monthly_ta_region_path, f"wgs_mean_monthly_ta_{region}_{str(month).zfill(2)}.tif")
        if not os.path.isfile(wgs_mean_monthly_ta_region_file):
            mean_monthly_ta_region_file = os.path.join(monthly_ta_region_path, f"mean_monthly_ta_{region}_{str(month).zfill(2)}.tif")
            process_image_with_args(mean_monthly_ta_region_file, wgs_mean_monthly_ta_region_file, SRSEnum.WGS84.value, res=0.01,
                                    srcNodata=temperature_nodata, dstNodata=temperature_nodata)
            print("mean monthly", month)


def main():
    path = Path()
    tile_list = get_world_tile(path)
    year_list = list(range(2020, 2024))
    region = "world"
    # create_annual_monthly_ta(path, tile_list, year_list, 16)
    # merge_annual_monthly_ta(path, region, tile_list, year_list)
    reproject_regional_annual_monthly_ta(path, region, year_list)


if __name__ == "__main__":
    main()
