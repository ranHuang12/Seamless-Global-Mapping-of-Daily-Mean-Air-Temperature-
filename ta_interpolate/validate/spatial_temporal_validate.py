import os

import numpy as np
import pandas as pd

from common_object.entity import Accuracy
from common_object.enum import ValidateModeEnum, ColumnsEnum
from common_util.common import get_world_tile
from common_util.document import to_csv, handle_null
from ta_interpolate.entity import Path, Dataset
from ta_interpolate.validate.validate_daily_ta import get_validate_df_by_mode


def validate_by_station(path: Path, validate_df, validate_mode):
    spatial_validate_df_list = []
    for station, station_validate_df in validate_df.groupby("STATION"):
        if station_validate_df.shape[0] < 2:
            continue
        accuracy = Accuracy.validate(station_validate_df["TEMP"].values, station_validate_df["PRED_TA"].values, 0.01)
        spatial_validate_df_list.append(pd.DataFrame({"STATION": [station], "SIZE": [accuracy.size], "R2": [accuracy.r2], "RMSE": [accuracy.rmse], "MAE": [accuracy.mae], "BIAS": [accuracy.bias]}))
        print(validate_mode, station, accuracy)
    spatial_validate_df = pd.concat(spatial_validate_df_list, ignore_index=True)
    station_df = pd.read_csv(os.path.join(path.cloud_station_path, "station_gsod.csv"), dtype=ColumnsEnum.STATION_TYPE.value)
    spatial_validate_df = station_df.merge(spatial_validate_df, on="STATION")
    to_csv(spatial_validate_df, os.path.join(path.cloud_interpolate_validate_path, f"validate_{validate_mode}_by_station_record.csv"), False)


def validate_by_latitude(path: Path, validate_df, validate_mode, step_size):
    record_df_list = []
    for lat in range(-90, 91, step_size):
        sub_validate_df = validate_df[(validate_df["LATITUDE"] >= lat) & (validate_df["LATITUDE"] < lat + step_size)]
        accuracy = Accuracy.validate(sub_validate_df["TEMP"].values, sub_validate_df["PRED_TA"].values, 0.01)
        record_df_list.append(pd.DataFrame(
            {"LATITUDE": [f"{lat}_{lat + step_size}"], "SIZE": [accuracy.size], "R2": [accuracy.r2],
             "RMSE": [accuracy.rmse], "MAE": [accuracy.mae], "BIAS": [accuracy.bias]}))
        print(validate_mode, lat, accuracy)
    to_csv(pd.concat(record_df_list, ignore_index=True), os.path.join(path.cloud_interpolate_validate_path, f"validate_{validate_mode}_by_latitude_record.csv"), False)


def validate_by_month(path: Path, validate_df, validate_mode):
    temporal_validate_df_list = []
    for month, month_validate_df in validate_df.groupby("MONTH"):
        if month_validate_df.shape[0] < 2:
            continue
        accuracy = Accuracy.validate(month_validate_df["TEMP"].values, month_validate_df["PRED_TA"].values, 0.01)
        temp_arr = month_validate_df["TEMP"].values * 0.01
        temporal_validate_df_list.append(pd.DataFrame({"MONTH": [month], "SIZE": [accuracy.size], "VAR": [np.var(temp_arr, ddof=1)], "STD": [np.std(temp_arr)], "R2": [accuracy.r2], "RMSE": [accuracy.rmse], "MAE": [accuracy.mae], "BIAS": [accuracy.bias]}))
        print(validate_mode, month, accuracy)
    to_csv(pd.concat(temporal_validate_df_list, ignore_index=True), os.path.join(path.cloud_interpolate_validate_path, f"validate_{validate_mode}_by_month_record.csv"), False)


def validate(path: Path, tile_list, year_list, validate_attribute_list, validate_mode_list):
    dataset = Dataset().loading_validate_data(tile_list, year_list, validate_attribute_list, not all(validate_mode == ValidateModeEnum.OVERALL.value for validate_mode in validate_mode_list))
    for validate_mode in validate_mode_list:
        validate_df = get_validate_df_by_mode(dataset, validate_mode)
        handle_null(validate_df, "PRED_TA")
        validate_by_month(path, validate_df, validate_mode)


def generate_used_station(path: Path, tile_list, year_list, validate_attribute_list):
    dataset = Dataset().loading_validate_data(tile_list, year_list, validate_attribute_list, False)
    used_station_df = dataset.validate_overall_df[["STATION"]].drop_duplicates(["STATION"])
    station_df = pd.read_csv(os.path.join(path.cloud_station_path, "station_gsod.csv"), dtype=ColumnsEnum.STATION_TYPE.value)
    used_station_df = station_df.merge(used_station_df, on=["STATION"])
    to_csv(used_station_df, os.path.join(path.cloud_station_path, f"used_station_{year_list[0]}_{year_list[-1]}.csv"), False)


def main():
    path = Path()
    tile_list = get_world_tile(path)
    year_list = list(range(2023, 2024))
    validate_attribute_list = list(range(24, 25))
    validate_mode_list = [ValidateModeEnum.ESTIMATE.value, ValidateModeEnum.OVERALL.value]
    validate(path, tile_list, year_list, validate_attribute_list, validate_mode_list)
    # generate_used_station(path, tile_list, year_list, validate_attribute_list)


if __name__ == "__main__":
    main()
