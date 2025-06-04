import os

import numpy as np
import pandas as pd

from common_object.enum import NodataEnum
from common_util.common import get_world_tile
from common_util.date import get_all_date_by_year, get_interval_date
from common_util.document import to_csv
from common_util.image import read_raster, create_raster
from common_util.path import create_path
from ta_interpolate.entity import Path


def get_nearest_file(path: Path, tile, date, front=True):
    ta_path = os.path.join(path.interpolate_ta_path, tile)
    interval = 1
    while True:
        target_date = get_interval_date(date, -interval if front else interval)
        target_file = os.path.join(ta_path, f"ta_{tile}_{target_date}.tif")
        if os.path.isfile(target_file):
            return target_file, target_date, interval
        interval += 1


def temporal_interpolate(path: Path, tile, year):
    ta_path = os.path.join(path.interpolate_ta_path, tile)
    ta_temp_path = os.path.join(path.interpolate_ta_path, "temp", tile)
    create_path(ta_temp_path)
    record_csv = os.path.join(path.cloud_interpolate_record_path, f"interpolate_ta_record_{tile}.csv")
    for date in get_all_date_by_year(year):
        ta_file = os.path.join(ta_path, f"ta_{tile}_{date}.tif")
        if os.path.isfile(ta_file):
            continue
        record_dict = {"date": [date], "origin_size": [0]}
        front_file, front_date, front_interval = get_nearest_file(path, tile, date)
        behind_file, behind_date, behind_interval = get_nearest_file(path, tile, date, False)
        front_arr, geo_data = read_raster(front_file, arr_type=np.int64)
        behind_arr = read_raster(behind_file, arr_type=np.int64)[0]
        ta_arr = (front_interval * behind_arr + behind_interval * front_arr) / (front_interval + behind_interval)
        record_dict["refer_date"] = [[front_date, behind_date]]
        record_dict["interpolate_size"] = record_dict["interpolated_size"] = ta_arr[ta_arr != NodataEnum.TEMPERATURE.value].size
        create_raster(os.path.join(ta_temp_path, f"ta_{tile}_{date}.tif"), ta_arr, geo_data, NodataEnum.TEMPERATURE.value)
        to_csv(pd.DataFrame(record_dict), record_csv)
        print(f"{tile} {date} front:{front_date} behind:{behind_date}")


def main():
    path = Path()
    tile_list = get_world_tile(path)
    year_list = list(range(2020, 2024))
    for tile in tile_list:
        for year in year_list:
            temporal_interpolate(path, tile, year)


if __name__ == "__main__":
    main()
