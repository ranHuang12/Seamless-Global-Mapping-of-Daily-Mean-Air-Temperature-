import os

import numpy as np
import pandas as pd

from common_object.entity import Accuracy, ModisDate
from common_object.enum import NodataEnum, ValidateModeEnum, ColumnsEnum
from common_util.common import convert_to_list, get_world_tile, exclude_finished_tile, concurrent_execute
from common_util.document import to_csv, merge_csv, handle_null
from common_util.image import read_raster
from ta_estimate.value_extract.value_extract import extract_value_from_tif
from ta_interpolate.entity import Path, Dataset


def gather_validate_data_by_tile(path: Path, tile, year_list, validate_mode, lock=None):
    station_df = pd.read_csv(os.path.join(path.cloud_station_tile_path, f"station_{tile}.csv"), dtype=ColumnsEnum.STATION_TILE_TYPE.value)
    mete_data_station_df_list = []
    for station in station_df["STATION"].values:
        mete_df = pd.read_csv(os.path.join(path.mete_data_station_path, f"{station}.csv"), usecols=ColumnsEnum.METE_ONLY.value, dtype=ColumnsEnum.METE_ONLY_TYPE.value)
        mete_data_station_df_list.append(mete_df[mete_df["DATE"].map(lambda date: date // 1000).isin(year_list) & (mete_df["TEMP_ATTRIBUTES"] >= 24)].sort_values("DATE"))
    mete_data_df = pd.concat(mete_data_station_df_list, ignore_index=True)
    validate_data_df = station_df.merge(mete_data_df, on=["STATION"])
    date_list = np.unique(mete_data_df["DATE"].values)
    refer_date_list = pd.read_csv(os.path.join(path.cloud_refer_date_path, f"refer_date_{tile}.csv"))["DATE"].values
    estimate_date_list = pd.read_csv(os.path.join(path.cloud_estimate_record_path, f"estimate_result_{tile}.csv"))["DATE"].values
    if validate_mode == ValidateModeEnum.ESTIMATE.value:
        date_list = np.intersect1d(date_list, estimate_date_list)
    elif validate_mode == ValidateModeEnum.INTERPOLATE_REFER.value:
        date_list = np.intersect1d(date_list, refer_date_list)
    elif validate_mode == ValidateModeEnum.INTERPOLATE_OTHER.value:
        date_list = np.setdiff1d(date_list, refer_date_list)
    station_arr = read_raster(os.path.join(path.cloud_station_tile_path, f"station_{tile}.tif"))[0]
    xindex_arr_1d = read_raster(os.path.join(path.cloud_xy_index_path, "x_index.tif"))[0][station_arr != NodataEnum.STATION.value]
    yindex_arr_1d = read_raster(os.path.join(path.cloud_xy_index_path, "y_index.tif"))[0][station_arr != NodataEnum.STATION.value]
    ta_df_list = []
    for date in date_list:
        ta_file = os.path.join(path.estimate_ta_path if validate_mode == ValidateModeEnum.ESTIMATE.value else path.interpolate_ta_path, tile, f"ta_{tile}_{date}.tif")
        ta_arr = read_raster(ta_file)[0]
        ta_df_list.append(extract_value_from_tif(ta_arr, NodataEnum.TEMPERATURE.value, "PRED_TA", station_arr, xindex_arr_1d, yindex_arr_1d, date))
    ta_df = pd.concat(ta_df_list, ignore_index=True) if ta_df_list else pd.DataFrame({"INDEX_X": [], "INDEX_Y": [], "DATE": [], "PRED_TA": []})
    validate_data_df = validate_data_df.merge(ta_df, "inner", ColumnsEnum.MERGE_METE.value)
    if validate_mode == ValidateModeEnum.INTERPOLATE_REFER.value and validate_data_df.size > 0:
        refer_ta_df_list = []
        for date in date_list:
            refer_ta_file = os.path.join(path.interpolate_refer_path, tile, f"ta_{tile}_{date}.tif")
            refer_ta_arr = read_raster(refer_ta_file)[0]
            refer_ta_df_list.append(extract_value_from_tif(refer_ta_arr, NodataEnum.TEMPERATURE.value, "REFER_TA", station_arr, xindex_arr_1d, yindex_arr_1d, date))
        refer_ta_df = pd.concat(refer_ta_df_list, ignore_index=True) if refer_ta_df_list else pd.DataFrame({"INDEX_X": [], "INDEX_Y": [], "DATE": [], "REFER_TA": []})
        validate_data_df = validate_data_df.merge(refer_ta_df, "left", ColumnsEnum.MERGE_METE.value)
    field = validate_mode.split("_")[-1]
    if validate_data_df.size > 0:
        validate_data_df["TEMP"] = validate_data_df["TEMP"].map(lambda temp: int(temp * 100))
        validate_data_df["YEAR"] = validate_data_df["DATE"].map(lambda date: date // 1000)
        validate_data_df["MONTH"] = validate_data_df["DATE"].map(lambda date: ModisDate().parse_modis_date(date).month)
        validate_data_df.drop(["NAME", "SIN_X", "SIN_Y", "INDEX_X", "INDEX_Y"])
        validate_csv = os.path.join(path.estimate_validate_data_path if validate_mode == ValidateModeEnum.ESTIMATE.value
                                    else (path.interpolate_validate_refer_path if validate_mode == ValidateModeEnum.INTERPOLATE_REFER.value
                                          else path.interpolate_validate_path), f"validate_{field}_{tile}.csv")
        to_csv(validate_data_df, validate_csv, False)
    to_csv(pd.DataFrame({"tile": [tile], field: [validate_data_df.shape[0]]}), os.path.join(path.interpolate_validate_path, f"finish_validate_{field}.csv"), lock=lock)
    print(tile, field, validate_data_df.shape)


def gather_validate_data(path: Path, tile_list, year_list, validate_mode, pool_size=1):
    tile_list = convert_to_list(tile_list)
    year_list = convert_to_list(year_list)
    finish_csv = os.path.join(path.interpolate_validate_path, f"finish_validate.csv")
    field = validate_mode.split("_")[-1]
    finish_part_csv = os.path.join(path.interpolate_validate_path, f"finish_validate_{field}.csv")
    args_list = []
    for tile in exclude_finished_tile(tile_list, field, finish_csv, finish_part_csv):
        args_list.append([path, tile, year_list, validate_mode])
    concurrent_execute(gather_validate_data_by_tile, args_list, pool_size)
    merge_csv(finish_csv, finish_part_csv, "tile", "outer")
    if os.path.isfile(finish_part_csv):
        os.remove(finish_part_csv)


def get_validate_df_by_mode(dataset: Dataset, validate_mode):
    validate_df = None
    if validate_mode == ValidateModeEnum.ESTIMATE.value:
        validate_df = dataset.validate_estimate_df
    elif validate_mode == ValidateModeEnum.INTERPOLATE_REFER.value:
        validate_df = dataset.validate_refer_df
    elif validate_mode == ValidateModeEnum.INTERPOLATE_OTHER.value:
        validate_df = dataset.validate_other_df
    elif validate_mode == ValidateModeEnum.INTERPOLATE.value:
        validate_df = pd.concat([dataset.validate_refer_df, dataset.validate_other_df], ignore_index=True)
    elif validate_mode == ValidateModeEnum.OVERALL.value:
        validate_df = dataset.validate_overall_df
    return validate_df


def validate_by_mode(path: Path, validate_df: pd.DataFrame, validate_mode, validate_type):
    pred_field = "REFER_TA" if validate_type == "with_refer" else "PRED_TA"
    record_file = os.path.join(path.cloud_interpolate_validate_path, f"validate_{validate_mode}_record.csv")
    validate_df = handle_null(validate_df, ["TEMP", pred_field])
    for year, validate_year_df in validate_df.groupby("YEAR"):
        accuracy = Accuracy.validate(validate_year_df["TEMP"].values, validate_year_df[pred_field].values)
        to_csv(pd.DataFrame({"mode": [validate_mode], "year": [year], "type": [validate_type], "size": [accuracy.size],
                             "r2": [accuracy.r2], "rmse": [accuracy.rmse], "mae": [accuracy.mae], "bias": [accuracy.bias]}), record_file)
        print(validate_type, year, accuracy)
    year_list = list(np.unique(validate_df["YEAR"].values))
    accuracy = Accuracy.validate(validate_df["TEMP"].values, validate_df[pred_field].values)
    to_csv(pd.DataFrame({"mode": [validate_mode], "year": [year_list], "type": [validate_type], "size": [accuracy.size],
                         "r2": [accuracy.r2], "rmse": [accuracy.rmse], "mae": [accuracy.mae], "bias": [accuracy.bias]}), record_file)
    print(validate_type, accuracy)


def validate(path: Path, tile_list, year_list, modeling_attribute_list, validate_mode_list):
    tile_list = convert_to_list(tile_list)
    year_list = convert_to_list(year_list)
    dataset = Dataset().loading_validate_data(tile_list, year_list, modeling_attribute_list, not all(validate_mode == ValidateModeEnum.OVERALL.value for validate_mode in validate_mode_list))
    for validate_mode in validate_mode_list:
        validate_df = get_validate_df_by_mode(dataset, validate_mode)
        if validate_mode == ValidateModeEnum.INTERPOLATE_REFER.value:
            validate_by_mode(path, validate_df, validate_mode, "with_refer")
            validate_by_mode(path, handle_null(validate_df, "REFER_TA", True), validate_mode, "without_refer")
        validate_by_mode(path, validate_df, validate_mode, validate_mode)


def main():
    path = Path()
    tile_list = get_world_tile(path)
    year_list = list(range(2020, 2024))
    # gather_validate_data(path, tile_list, year_list, ValidateModeEnum.ESTIMATE.value, 8)
    validate_attribute_list = list(range(24, 25))
    validate_mode_list = [ValidateModeEnum.ESTIMATE.value, ValidateModeEnum.INTERPOLATE_REFER.value,
                          ValidateModeEnum.INTERPOLATE_OTHER.value, ValidateModeEnum.INTERPOLATE.value,
                          ValidateModeEnum.OVERALL.value]
    # validate(path, tile_list, year_list, validate_attribute_list, validate_mode_list)
    

if __name__ == "__main__":
    main()
