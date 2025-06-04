import os.path

import numpy as np
import pandas as pd

from common_object.enum import NodataEnum
from common_util.common import get_world_tile
from common_util.date import get_date_interval
from common_util.document import to_csv
from common_util.image import read_raster
from common_util.path import create_path
from ta_estimate.post_process import merge_ta
from ta_interpolate.entity import Path


def merge_daily_ta(path: Path, tile_list, date, region="world"):
    region_ta_path = os.path.join(path.interpolate_ta_path, "world")
    ta_file_list = [os.path.join(path.interpolate_ta_path, tile, f"ta_{tile}_{date}.tif") for tile in tile_list]
    ta_file = os.path.join(region_ta_path, f"ta_{region}_{date}.tif")
    record_file = os.path.join(path.cloud_interpolate_record_path, f"interpolate_ta_record_{region}.csv")
    merge_ta(ta_file_list, ta_file, record_file, "date", date)


def get_tile_border_daily_ta(path: Path, date, tile_list, axis, offset, shape):
    source_ta_path = path.estimate_ta_path
    border_path = os.path.join(path.cloud_interpolate_ta_path, "border")
    create_path(border_path)
    first_tile = tile_list[0]
    # current_ds, geo_data = read_raster(os.path.join(source_ta_path, first_tile, f"ta_{first_tile}_{date}.tif"), False)
    for index in range(1, len(tile_list)):
        current_tile = tile_list[index-1]
        next_tile = tile_list[index]
        current_h = int(current_tile.split("h")[-1].split("v")[0])
        current_v = int(current_tile.split("v")[-1])
        next_h = int(next_tile.split("h")[-1].split("v")[0])
        next_v = int(next_tile.split("v")[-1])
        # x_size = int(current_ds.RasterXSize * shape[1])
        # y_size = int(current_ds.RasterYSize * shape[0])
        # top_left_x, x_res, x_ro, top_left_y, y_ro, y_res = geo_data.transform
        # current_arr = current_ds.GetRasterBand(1).ReadAsArray()
        # next_ds, next_geo_data = read_raster(os.path.join(source_ta_path, next_tile, f"ta_{next_tile}_{date}.tif"), False)
        # next_arr = next_ds.GetRasterBand(1).ReadAsArray()
        # border_arr = np.zeros([y_size, x_size])
        border_arr = np.zeros([1, 1])
        x_offset = y_offset = 0
        if axis == 0 and current_v == next_v and next_h-current_h == 1:
        #     x_offset = int(current_ds.RasterXSize * (1 - shape[1] / 2))
        #     y_offset = int(current_ds.RasterYSize * offset)
        #     border_arr[:, :int(x_size / 2)] = current_arr[y_offset:y_offset + y_size, x_offset:]
        #     border_arr[:, int(x_size / 2):] = next_arr[y_offset:y_offset + y_size, :int(x_size / 2)]
            border_arr = read_raster(os.path.join(border_path, f"ta_{current_tile}_{next_tile}_{date}.tif"))[0]
        elif current_h == next_h and next_v-current_v == 1:
        #     x_offset = int(current_ds.RasterXSize * offset)
        #     y_offset = int(current_ds.RasterYSize * (1 - shape[0] / 2))
        #     border_arr[:int(y_size / 2), :] = current_arr[y_offset:, x_offset: x_offset + x_size]
        #     border_arr[int(y_size / 2):, :] = next_arr[:int(y_size / 2), x_offset: x_offset + x_size]
            border_arr = read_raster(os.path.join(border_path, f"ta_{current_tile}_{next_tile}_{date}.tif"))[0]
        if border_arr[border_arr != 0].size > 0:
            # top_left_x += x_offset * x_res
            # top_left_y += y_offset * y_res
            # geo_data.transform = (top_left_x, x_res, x_ro, top_left_y, y_ro, y_res)
            # create_raster(os.path.join(border_path, f"ta_{current_tile}_{next_tile}_{date}.tif"), border_arr, geo_data,
            #               NodataEnum.AMBIENT_TEMPERATURE.value, output_type=gdalconst.GDT_Int16)

            border_value_arr = border_arr[border_arr != NodataEnum.AIR_TEMPERATURE.value]
            to_csv(pd.DataFrame({"tile": [f"{current_tile}_{next_tile}"], "date": [date], "sum": [border_value_arr.size],
                                 "min": [np.min(border_value_arr)], "avg": [np.average(border_value_arr)], "max": [np.max(border_value_arr)]}),
                   os.path.join(path.cloud_estimate_record_path, "border_record.csv"))
            print(current_tile, next_tile)
        # current_ds = next_ds
        # geo_data = next_geo_data


def merge_interpolate_refer_record(path: Path, tile_list, year_list):
    df_list = []
    for tile in tile_list:
        record_dict = {"tile": [tile]}
        record_df = pd.read_csv(os.path.join(path.cloud_interpolate_refer_record_path, f"interpolate_refer_record_{tile}.csv"))
        record_df = record_df[record_df["date"].map(lambda date: date // 1000).isin(year_list)]
        if record_df.size == 0:
            continue
        record_dict["count"] = record_df.shape[0]
        refer_count = 0
        for rounds in range(1, 6):
            refer_count += record_df[record_df[f"refer_interpolate_size{rounds}"] != 0].shape[0]
        record_dict["avg_refer_count"] = refer_count / record_dict["count"]
        size_arr = record_df["refer_interpolated_size"].values
        record_dict["min_size"] = np.min(size_arr)
        record_dict["avg_size"] = np.mean(size_arr)
        record_dict["max_size"] = np.max(size_arr)
        mask_arr = read_raster(os.path.join(path.cloud_mask_path, f"mask_{tile}.tif"))[0]
        mask_size = mask_arr[mask_arr != NodataEnum.MASK.value].size
        record_dict["min_ratio"] = np.min(size_arr) / mask_size
        record_dict["avg_ratio"] = np.mean(size_arr) / mask_size
        record_dict["max_ratio"] = np.max(size_arr) / mask_size
        print(record_dict)
        df_list.append(pd.DataFrame(record_dict))
    to_csv(pd.concat(df_list), os.path.join(path.cloud_interpolate_refer_record_path, f"interpolate_refer_record_tile.csv"), False)


def merge_interpolate_record(path: Path, tile_list, year_list):
    df_list = []
    interval_df_list = []
    for tile in tile_list:
        record_dict = {"tile": [tile]}
        record_df = pd.read_csv(os.path.join(path.cloud_interpolate_record_path, f"interpolate_ta_record_{tile}.csv"))
        record_df = record_df[record_df["date"].map(lambda date: date // 1000).isin(year_list)]
        temporal_interpolate_df = record_df[(record_df["origin_size"] < 1000) & (record_df.eval("origin_size/interpolated_size") < 0.01)]
        record_dict["temporal_interpolate"] = temporal_interpolate_df.shape[0]
        mask_arr = read_raster(os.path.join(path.cloud_mask_path, f"mask_{tile}.tif"))[0]
        mask_size = mask_arr[mask_arr != NodataEnum.MASK.value].size
        record_df = record_df[(record_df["origin_size"] >= min(mask_size * 0.01, 1000))]
        record_dict["count"] = record_df.shape[0]
        size_arr = record_df["origin_size"].values
        record_dict["min_size"] = np.min(size_arr)
        record_dict["avg_size"] = np.mean(size_arr)
        record_dict["max_size"] = np.max(size_arr)
        record_dict["min_ratio"] = np.min(size_arr) / mask_size
        record_dict["avg_ratio"] = np.mean(size_arr) / mask_size
        record_dict["max_ratio"] = np.max(size_arr) / mask_size
        df_list.append(pd.DataFrame(record_dict))
        interval_df = record_df[["date", "refer_date"]]
        interval_df.loc[:, "tile"] = tile
        interval_df["interval"] = record_df.apply(lambda row: abs(get_date_interval(row["date"], row["refer_date"])), axis=1)
        interval_df["interval_1year"] = interval_df["interval"].apply(lambda interval: interval if interval <= 30 else None)
        interval_df["interval_2years"] = interval_df["interval"].apply(lambda interval: interval if (interval in range(31, 367)) else None)
        interval_df["interval_3years"] = interval_df["interval"].apply(lambda interval: interval if (interval in range(367, 733)) else None)
        interval_df["interval_4years"] = interval_df["interval"].apply(lambda interval: interval if interval > 733 else None)
        interval_df_list.append(interval_df)
        print(record_dict)
    to_csv(pd.concat(df_list), os.path.join(path.cloud_interpolate_record_path, "interpolate_ta_record_tile.csv"), False)
    to_csv(pd.concat(interval_df_list), os.path.join(path.cloud_refer_date_path, "match_record.csv"), False)


def main():
    path = Path()
    tile_list = get_world_tile(path)
    year_list = list(range(2020, 2024))
    # merge_interpolate_refer_record(path, tile_list, year_list)
    merge_interpolate_record(path, tile_list, year_list)
    # for date in [2022099, 2022285, 2022101, 2022102]:
    #     merge_daily_ta(path, tile_list, date)
    # tile_list = [tile for tile in tile_list if tile.split("v")[-1] == "05"]
    # tile_list = [tile for tile in tile_list if tile.split("h")[-1].split("v")[0] == "21"]
    # get_tile_border_daily_ta(path, 2022285, tile_list, 1, 0, [0.5, 0.5])


if __name__ == "__main__":
    main()
