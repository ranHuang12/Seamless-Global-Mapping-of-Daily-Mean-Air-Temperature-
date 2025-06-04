import os

import numpy as np
import pandas as pd

from common_object.enum import NodataEnum
from common_util.common import get_world_tile
from common_util.date import get_all_modis_date_by_year
from common_util.document import to_csv
from common_util.image import mosaic, read_raster
from common_util.path import create_path
from ta_estimate.entity import Configuration, Path


def merge_ta(ta_file_list, ta_file, record_file, field, date):
    create_path(os.path.dirname(ta_file))
    mosaic(ta_file_list, ta_file, NodataEnum.TEMPERATURE.value, NodataEnum.TEMPERATURE.value)
    ta_arr = read_raster(ta_file)[0]
    ta_value_arr = ta_arr[ta_arr != NodataEnum.TEMPERATURE.value]
    record_dict = {field: [date], "sum": [ta_value_arr.size], "min_ta": [np.min(ta_value_arr) / 100],
                   "avg_ta": [np.average(ta_value_arr) / 100], "max_ta": [np.max(ta_value_arr) / 100]}
    to_csv(pd.DataFrame(record_dict), record_file)
    print(record_dict)


def merge_estimate_ta(config: Configuration, region="world"):
    path = config.path
    qc_mode = config.qc_mode
    ta_region_path = os.path.join(path.estimate_ta_path, region)
    create_path(ta_region_path)
    for year in config.year_list:
        date_list = config.date_list if config.date_list else get_all_modis_date_by_year(year)
        for modis_date in date_list:
            date = modis_date.modis_date
            ta_file_list = []
            for tile in config.tile_list:
                ta_file = os.path.join(path.estimate_ta_path, tile, f"ta_{tile}_{date}.tif")
                if os.path.isfile(ta_file):
                    ta_file_list.append(ta_file)
            ta_world_file = os.path.join(ta_region_path, f"ta_{region}_{date}.tif")
            mosaic(ta_file_list, ta_world_file, NodataEnum.AIR_TEMPERATURE.value,
                   NodataEnum.AIR_TEMPERATURE.value, hdf=False)
            ta_arr = read_raster(ta_world_file)[0]
            ta_value_arr = ta_arr[ta_arr != NodataEnum.AIR_TEMPERATURE.value]
            tile_count = len(ta_file_list)
            pixel_count = ta_value_arr.size
            min_ta = np.min(ta_value_arr) / 100
            max_ta = np.max(ta_value_arr) / 100
            avg_ta = np.average(ta_value_arr) / 100
            # to_csv(pd.DataFrame({"DATE": [date], "TILE": [tile_count], "QC_MODE": [qc_mode.name], "SUM": [pixel_count], "MIN_TA": [min_ta], "MAX_TA": [max_ta], "AVG_TA": [avg_ta]}),
            #        os.path.join(path.cloud_record_path, f"estimate_result_{region}.csv"))
            print(date, tile_count, qc_mode.name, pixel_count, min_ta, max_ta, avg_ta)


def merge_estimate_record_by_tile(path: Path, tile_list):
    record_df_list = []
    for tile in tile_list:
        record_dict = {"tile": [tile]}
        estimate_record_df = pd.read_csv(os.path.join(path.cloud_estimate_record_path, f"estimate_result_{tile}.csv"))
        estimate_record_df = estimate_record_df[estimate_record_df["SUM"] != 0]
        record_dict["days"] = estimate_record_df.shape[0]
        for field in ["TDTNADAN", "TDTN", "ADAN", "TN", "AN", "TD", "AD", "SUM"]:
            record_dict[field] = np.sum(estimate_record_df[field].values)
        record_dict["MIN_TA"] = np.min(estimate_record_df["MIN_TA"].values)
        record_dict["AVG_TA"] = np.sum(estimate_record_df.eval("SUM*AVG_TA").values) / record_dict["SUM"]
        record_dict["MAX_TA"] = np.max(estimate_record_df["MAX_TA"].values)
        mask_arr = read_raster(os.path.join(path.cloud_mask_path, f"mask_{tile}.tif"))[0]
        mask_size = mask_arr[mask_arr != NodataEnum.MASK.value].size
        record_dict["coverage"] = record_dict["SUM"] / (mask_size*1096)
        record_df_list.append(pd.DataFrame(record_dict))
        print(tile)
    to_csv(pd.concat(record_df_list, ignore_index=True), os.path.join(path.cloud_estimate_record_path, "estimate_result_tile.csv"), False)


def merge_estimate_record_by_date(path: Path, tile_list):
    result_df = None
    for tile in tile_list:
        estimate_record_df = pd.read_csv(os.path.join(path.cloud_estimate_record_path, f"estimate_result_{tile}.csv"),
                                         usecols=["DATE", "TDTNADAN", "TDTN", "ADAN", "TN", "AN", "TD", "AD", "SUM"])
        if result_df is None:
            result_df = estimate_record_df
        else:
            for field in ["TDTNADAN", "TDTN", "ADAN", "TN", "AN", "TD", "AD", "SUM"]:
                new_field = f"{field}_add"
                estimate_record_df = estimate_record_df.rename(columns={field: new_field})
                result_df = result_df.merge(estimate_record_df[["DATE", new_field]], on="DATE")
                result_df[field] += result_df[new_field]
                result_df.drop(columns=[new_field], inplace=True)
        print(tile)
    to_csv(result_df, os.path.join(path.cloud_estimate_record_path, f"estimate_result_date.csv"), False)


def main():
    path = Path()
    tile_list = get_world_tile(path)
    # merge_estimate_record_by_tile(path, tile_list)
    merge_estimate_record_by_date(path, tile_list)


if __name__ == "__main__":
    main()
