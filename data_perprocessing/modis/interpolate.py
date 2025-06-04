import os

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter

from common_object.entity import BasePath
from common_object.enum import NodataEnum
from common_util.common import convert_to_list, exclude_finished_tile, concurrent_execute
from common_util.date import get_date_interval, get_interval_date, get_day_num_by_year
from common_util.document import to_csv, merge_csv
from common_util.image import read_raster, create_raster
from common_util.path import create_path


def interpolate_daily_vi(path: BasePath, vi, tile, year, max_length=64, series_num=0, arm_length=15, polyorder=3, kind="linear", lock=None):
    max_length = min(max_length, 64)
    no_data = NodataEnum.VEGETATION_INDEX.value
    vi_raw_path = os.path.join(path.auxiliary_data_path, vi, "raw", tile)
    vi_path = os.path.join(path.auxiliary_data_path, vi, tile)
    create_path(vi_path)
    date_list = []
    for filename in os.listdir(vi_raw_path):
        date_list.append(int(filename.split(".")[0].split("_")[-1]))
    date_list.sort()
    first_date = year*1000+1
    last_date = year*1000+get_day_num_by_year(year)
    first_index = next(index for index, date in enumerate(date_list) if date >= first_date)
    last_index = len(date_list) - next(index for index, date in enumerate(reversed(date_list)) if date <= last_date) - 1
    extend_size = min((max_length - last_index + first_index - 1) // 2, first_index, len(date_list)-last_index-1)
    mask_arr, geo_data = read_raster(os.path.join(path.cloud_mask_path, f"{tile}_mask.tif"))
    series_arr = np.zeros_like(mask_arr).astype(np.int64)
    multiplier = 1
    interval_list = []
    raw_vi_arr_list = []
    for index in range(first_index-extend_size, last_index+extend_size+1):
        date = date_list[index]
        vi_arr = read_raster(os.path.join(vi_raw_path, f"{vi}_{tile}_{date}.tif"))[0]
        series_arr[vi_arr != no_data] += multiplier
        multiplier *= 2
        interval_list.append(get_date_interval(first_date, date))
        raw_vi_arr_list.append(vi_arr)
    series_arr_1d = series_arr[series_arr != 0]
    series_value_arr = np.unique(series_arr_1d)
    count_list = [series_arr_1d[series_arr_1d == series_value].size for series_value in series_value_arr]
    sorted_series_value_list = sorted(zip(list(series_value_arr), count_list), key=lambda value: value[1], reverse=True)
    vi_arr_list = [np.full_like(mask_arr, no_data) for _ in range(-arm_length, get_day_num_by_year(year)+arm_length)]
    pixel_count = 0
    for series_value, count in (sorted_series_value_list if series_num == 0 else sorted_series_value_list[:series_num]):
        series = np.array(list(bin(series_value)[2:].zfill(len(interval_list))))[::-1]
        train_x = np.array(interval_list)[series == '1']
        if (train_x[0] <= -arm_length) and (train_x[-1] >= get_day_num_by_year(year)+arm_length-1):
            train_y = np.stack(np.array([vi_arr[series_arr == series_value] for vi_arr in raw_vi_arr_list])[series == '1'], -1)
            func = interp1d(train_x, train_y, kind)
            for pred_x in range(-arm_length, get_day_num_by_year(year)+arm_length):
                vi_arr_list[pred_x+arm_length][series_arr == series_value] = func(pred_x)
            pixel_count += count
    filtered_arr_list = savgol_filter(np.stack(vi_arr_list, -1), 2*arm_length+1, polyorder)
    for index in range(0, get_day_num_by_year(year)):
        date = get_interval_date(first_date, index)
        create_raster(os.path.join(vi_path, f"{vi}_{tile}_{date}.tif"), filtered_arr_list[:, :, index+arm_length], geo_data, no_data)
    to_csv(pd.DataFrame({"tile": [tile], year: [pixel_count]}), os.path.join(path.auxiliary_data_path, vi, f"finish_{vi}_{year}.csv"), lock=lock)
    print(vi, tile, year, pixel_count)


def interpolate(path: BasePath, vi_list, tile_list, year_list, pool_size):
    vi_list = convert_to_list(vi_list)
    tile_list = convert_to_list(tile_list)
    year_list = convert_to_list(year_list)
    for vi in vi_list:
        for year in year_list:
            finish_csv = os.path.join(path.auxiliary_data_path, vi, f"finish_{vi}.csv")
            finish_year_csv = os.path.join(path.auxiliary_data_path, vi, f"finish_{vi}_{year}.csv")
            args_list = []
            for tile in exclude_finished_tile(tile_list, year, finish_csv, finish_year_csv):
                args_list.append([path, vi, tile, year, 64, 0, 15, 3, "linear"])
                concurrent_execute(interpolate_daily_vi, args_list, pool_size)
            merge_csv(finish_csv, finish_year_csv, "tile", "outer")
            os.remove(finish_year_csv)


def main():
    path = BasePath()
    interpolate(path, ["ndvi", "evi"], "h16v02", [2020, 2021], 16)


if __name__ == "__main__":
    main()
