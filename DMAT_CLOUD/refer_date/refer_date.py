import os.path

import numpy as np
import pandas as pd

from common_object.enum import NodataEnum
from common_util.common import get_world_tile, convert_to_list
from common_util.date import get_date_interval, get_interval_date
from common_util.document import to_csv
from common_util.image import read_raster, csv_join_shp
from ta_interpolate.entity import Path


def get_nearest_date(target_date, refer_date_list):
    refer_date_list = np.array(refer_date_list)
    interval_list = np.array([abs(get_date_interval(target_date, refer_date)) for refer_date in refer_date_list])
    interval = np.sort(interval_list)[0]
    return refer_date_list[interval_list == interval][0], interval


def get_refer_date(target_date, refer_date_list, use_adjacent_years=True, use_threshold=True, interval_threshold=30):
    refer_date_list = np.array(refer_date_list)
    if use_adjacent_years:
        year_order_dict = {2020: [2020, 2021, 2022, 2023], 2021: [2021, 2020, 2022, 2023],
                           2022: [2022, 2021, 2023, 2020], 2023: [2023, 2022, 2021, 2020]}
    else:
        year_order_dict = {2020: [2020], 2021: [2021], 2022: [2022], 2023: [2023]}
    target_date = int(target_date)
    target_year = target_date // 1000
    target_doy = target_date % 1000
    for refer_year in year_order_dict[target_year]:
        target_date = refer_year * 1000 + target_doy
        filtered_refer_date_list = refer_date_list[(refer_date_list >= get_interval_date(target_date, -interval_threshold)) & (refer_date_list <= get_interval_date(target_date, interval_threshold))] if use_threshold else refer_date_list
        if len(filtered_refer_date_list) == 0:
            continue
        return get_nearest_date(target_date, filtered_refer_date_list)
    return 0, 0


def validate_refer_date_list(date_list, refer_date_list, use_adjacent_years):
    for target_date in date_list:
        refer_date, interval = get_refer_date(target_date, refer_date_list, use_adjacent_years)
        if refer_date == 0:
            return False
    return True


def search_index_for_refer_dates(date_list, use_adjacent_years=False, append=False, original_refer_date_list=None):
    left = 0
    right = date_list.size
    while left <= right:
        mid = (left + right) // 2
        refer_date_list = np.concatenate([original_refer_date_list, date_list[:mid]]) if append else date_list[:mid]
        if validate_refer_date_list(date_list, refer_date_list, use_adjacent_years):
            right = mid - 1
        else:
            left = mid + 1
    return left


def generate_refer_dates(path: Path, tile_list, append=False, append_year_list=None):
    tile_list = convert_to_list(tile_list)
    for tile in tile_list:
        mask_arr = read_raster(os.path.join(path.cloud_mask_path, f"mask_{tile}.tif"))[0]
        mask_pixel_count = mask_arr[mask_arr != NodataEnum.MASK.value].size
        ta_estimate_result_df = pd.read_csv(os.path.join(path.cloud_estimate_record_path, f"estimate_result_{tile}.csv"), usecols=["DATE", "SUM"]).sort_values("SUM", ascending=False)
        date_list = ta_estimate_result_df["DATE"].values
        refer_date_file = os.path.join(path.cloud_refer_date_path, f"refer_date_{tile}.csv")
        append_ta_estimate_result_df = None
        original_refer_date_df = None
        original_refer_date_list = None
        append_date_list = None
        if append:
            append_ta_estimate_result_df = ta_estimate_result_df[ta_estimate_result_df["DATE"].map(lambda date: date // 1000).isin(append_year_list)]
            original_refer_date_df = pd.read_csv(refer_date_file)
            original_refer_date_list = original_refer_date_df["DATE"].values
            append_date_list = append_ta_estimate_result_df["DATE"].values
        for use_adjacent_years in [False, True]:
            index = search_index_for_refer_dates(append_date_list if append else date_list, use_adjacent_years, append, original_refer_date_list)
            count = original_refer_date_list.size + index
            if count < date_list.size * 0.3:
                break
        if append:
            refer_date_df = pd.concat([original_refer_date_df, append_ta_estimate_result_df[:index]]).sort_values("SUM", ascending=False)
        else:
            refer_date_df = ta_estimate_result_df[:index]
        to_csv(refer_date_df, refer_date_file, False)
        sum_arr = refer_date_df["SUM"].values
        min_pixel = np.min(sum_arr)
        avg_pixel = np.average(sum_arr)
        max_pixel = np.max(sum_arr)
        record_dict = {"tile": [tile], "mask": [mask_pixel_count], "use_adjacent_years": [use_adjacent_years],
                       "count": [count], "min_pixel": [min_pixel], "avg_pixel": [avg_pixel], "max_pixel": [max_pixel],
                       "min_ratio": [float(format(min_pixel / mask_pixel_count, '.4g'))],
                       "avg_ratio": [float(format(avg_pixel / mask_pixel_count, '.4g'))],
                       "max_ratio": [float(format(max_pixel / mask_pixel_count, '.4g'))]}
        to_csv(pd.DataFrame(record_dict), os.path.join(path.cloud_refer_date_path, "refer_date1.csv"))
        print(record_dict)


def generate_refer_dates_shp(path: Path):
    shp_file = os.path.join(path.cloud_mask_path, "polygon", "瓦片矢量", "used_modis_tile_polygon.shp")
    csv_file = os.path.join(path.cloud_refer_date_path, "refer_date.csv")
    output_file = os.path.join(path.cloud_mask_path, "polygon", "瓦片矢量", "modis_tile_refer_date_polygon.shp")
    csv_join_shp(shp_file, csv_file, output_file, "tile", "tile", ["count", "class"], {"count": int, "class": int})


def main():
    path = Path()
    tile_list = get_world_tile(path)
    # generate_refer_dates(path, tile_list, True, [2023])
    generate_refer_dates_shp(path)


if __name__ == "__main__":
    main()
