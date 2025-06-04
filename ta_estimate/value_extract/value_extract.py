import math
import os

import numpy as np
import pandas as pd

from common_object.entity import ModisDate
from common_object.enum import ViewEnum, ColumnsEnum, NodataEnum, QcModeEnum
from common_util.common import convert_to_list, convert_enum_to_value, get_world_tile, exclude_finished_tile, \
    concurrent_execute
from common_util.date import get_date_interval
from common_util.document import to_csv, merge_csv
from common_util.image import read_raster
from ta_estimate.entity.path import Path


def extract_value_from_tif(value_arr, value_nodata, field, station_arr, xindex_arr_1d, yindex_arr_1d, date):
    value_arr_1d = value_arr[station_arr != NodataEnum.STATION.value]
    xindex_arr_record = xindex_arr_1d[value_arr_1d != value_nodata]
    yindex_arr_record = yindex_arr_1d[value_arr_1d != value_nodata]
    value_arr_record = value_arr_1d[value_arr_1d != value_nodata]
    date_arr_record = np.zeros_like(value_arr_record) + date
    return pd.DataFrame({"INDEX_X": xindex_arr_record, "INDEX_Y": yindex_arr_record, "DATE": date_arr_record, field: value_arr_record})


def extract_value_from_path(tif_path, tif_nodata, field, station_arr, xindex_arr_1d, yindex_arr_1d, date_list):
    value_df = None
    if os.path.exists(tif_path):
        first_filename = os.listdir(tif_path)[0]
        base_filename = first_filename[:first_filename.rfind("_")]
        value_df_list = []
        for date in date_list:
            tif_file = os.path.join(tif_path, f"{base_filename}_{date}.tif")
            if os.path.isfile(tif_file):
                try:
                    value_arr = read_raster(tif_file)[0]
                    value_df_list.append(extract_value_from_tif(value_arr, tif_nodata, field, station_arr, xindex_arr_1d, yindex_arr_1d, date))
                except Exception as e:
                    print(e)
        if value_df_list:
            value_df = pd.concat(value_df_list, ignore_index=True)
    return value_df


def rounding_value(modeling_data_df, field_list=["LATITUDE", "LONGITUDE", "ELEVATION", "TEMP"],
                   scaler_factor_list=[100, 100, 1, 100]):
    for index, field in enumerate(field_list):
        modeling_data_df[field] = modeling_data_df[field].map(lambda value: value if math.isnan(value) else int(value * scaler_factor_list[index])).astype("Int16")


def extract_value_by_tile(path: Path, tile, year, extract_value_list, append=False, lock=None):
    extract_value_list = convert_to_list(extract_value_list)
    modeling_data_file = os.path.join(path.estimate_modeling_data_path, f"{tile}_modeling.csv")
    station_df = pd.read_csv(os.path.join(path.cloud_station_tile_path, f"station_{tile}.csv"), dtype=ColumnsEnum.STATION_TILE_TYPE.value)
    mete_station_df_list = []
    for station in station_df["STATION"].values:
        mete_df = pd.read_csv(os.path.join(path.mete_data_station_path, f"{station}.csv"), dtype=ColumnsEnum.METE_STATION_TYPE.value)
        mete_df = mete_df[mete_df["DATE"]//1000 == year]
        mete_station_df_list.append(mete_df)
    mete_station_df = pd.concat(mete_station_df_list, ignore_index=True)
    mete_station_df.drop(["LATITUDE", "LONGITUDE", "ELEVATION", "NAME"], axis=1, inplace=True)
    modeling_data_df = station_df.merge(mete_station_df, on=["STATION"])
    station_arr = read_raster(os.path.join(path.cloud_station_tile_path, f"station_{tile}.tif"))[0]
    xindex_arr_1d = read_raster(os.path.join(path.cloud_xy_index_path, f"x_index.tif"))[0][station_arr != NodataEnum.STATION.value]
    yindex_arr_1d = read_raster(os.path.join(path.cloud_xy_index_path, f"y_index.tif"))[0][station_arr != NodataEnum.STATION.value]
    date_list = []
    for extract_value in extract_value_list:
        date_list = np.unique(modeling_data_df["DATE"].values)
        if extract_value == "LST" or extract_value == "LST_GQ":
            lst_df = pd.DataFrame(columns=["INDEX_X", "INDEX_Y", "DATE"])
            qc_mode = QcModeEnum.ALL.value if extract_value == "LST" else QcModeEnum.GOOD_QUALITY.value
            for view in convert_enum_to_value(ViewEnum):
                lst_path = os.path.join(path.lst_path, f"{view.view_name}_{qc_mode.name}", tile)
                lst_view_df = extract_value_from_path(lst_path, NodataEnum.TEMPERATURE.value, f"{view.view_name}_{qc_mode.field}", station_arr, xindex_arr_1d, yindex_arr_1d, date_list)
                if lst_view_df is not None:
                    lst_df = lst_df.merge(lst_view_df, "outer", ["INDEX_X", "INDEX_Y", "DATE"])
            how = "inner" if extract_value == "LST" else "left"
            modeling_data_df = modeling_data_df.merge(lst_df, how, ["INDEX_X", "INDEX_Y", "DATE"])
        elif extract_value == "LST_ANGLE":
            angle_df = pd.DataFrame(columns=["INDEX_X", "INDEX_Y", "DATE"])
            for view in convert_enum_to_value(ViewEnum):
                angle_path = os.path.join(path.lst_path, f"{view.view_name}_angle", tile)
                angle_view_df = extract_value_from_path(angle_path, NodataEnum.VIEW_ANGLE.value, f"{view.view_name}_ANGLE", station_arr, xindex_arr_1d, yindex_arr_1d, date_list)
                if angle_view_df is not None:
                    angle_df = angle_df.merge(angle_view_df, "outer", ["INDEX_X", "INDEX_Y", "DATE"])
            modeling_data_df = modeling_data_df.merge(angle_df, "left", ["INDEX_X", "INDEX_Y", "DATE"])
        elif extract_value == "VI":
            vi_df = pd.DataFrame(columns=["INDEX_X", "INDEX_Y", "DATE"])
            for vi in ["NDVI", "EVI"]:
                vi_path = os.path.join(path.auxiliary_data_path, vi.lower(), tile)
                vi_type_df = extract_value_from_path(vi_path, NodataEnum.VEGETATION_INDEX.value, vi, station_arr, xindex_arr_1d, yindex_arr_1d, date_list)
                if vi_type_df is not None:
                    vi_df = vi_df.merge(vi_type_df, "outer", ["INDEX_X", "INDEX_Y", "DATE"])
            modeling_data_df = modeling_data_df.merge(vi_df, "left", ["INDEX_X", "INDEX_Y", "DATE"])
    modeling_data_df["YEAR"] = modeling_data_df["DATE"].map(lambda date: date // 1000)
    modeling_data_df["MONTH"] = modeling_data_df["DATE"].map(lambda date: ModisDate().parse_modis_date(date).month)
    modeling_data_df["DOY"] = modeling_data_df["DATE"].map(lambda date: date % 1000)
    modeling_data_df["INTERVAL"] = modeling_data_df["DATE"].map(lambda date: get_date_interval(2000001, date))
    rounding_value(modeling_data_df)
    if modeling_data_df.shape[0] > 0:
        if append:
            original_modeling_data_df = pd.read_csv(modeling_data_file, dtype=ColumnsEnum.MODELING_DATA_TYPE.value)
            merge_csv(original_modeling_data_df, modeling_data_df, output_file=modeling_data_file, along_column=False)
        else:
            to_csv(modeling_data_df, os.path.join(path.estimate_modeling_data_path, f"modeling_{tile}.csv"), False)
    to_csv(pd.DataFrame({"tile": [tile], year: [f"{len(date_list)}-{modeling_data_df.shape}"]}), os.path.join(path.estimate_modeling_data_path, f"modeling_data_count_{year}.csv"), lock=lock)
    print(tile, len(date_list), modeling_data_df.shape)


def extract_value(path: Path, tile_list, year_list, extract_value_list, append=False, pool_size=1):
    tile_list = convert_to_list(tile_list)
    year_list = convert_to_list(year_list)
    extract_value_list = convert_to_list(extract_value_list)
    for year in year_list:
        finish_csv = os.path.join(path.estimate_modeling_data_path, f"modeling_data_count.csv")
        finish_year_csv = os.path.join(path.estimate_modeling_data_path, f"modeling_data_count_{year}.csv")
        args_list = []
        for tile in exclude_finished_tile(tile_list, year, finish_csv, finish_year_csv):
            args_list.append([path, tile, year, extract_value_list, append])
        concurrent_execute(extract_value_by_tile, args_list, pool_size)
        merge_csv(finish_csv, finish_year_csv, "tile", "outer")
        os.remove(finish_year_csv)


def main():
    path = Path()
    target_tile_list = ['h15v02', 'h16v01', 'h16v02', 'h17v00', 'h17v01', 'h17v02', 'h17v03', 'h17v04', 'h17v05',
                        'h18v00', 'h18v01', 'h18v02', 'h18v03', 'h18v04', 'h18v05', 'h19v01', 'h19v02', 'h19v03',
                        'h20v10', 'h23v05']
    tile_list = get_world_tile(path)
    year_list = [2022]
    extract_value_list = ["LST", "LST_ANGLE"]
    extract_value(path, ["h03v06"], year_list, extract_value_list, True, 1)


if __name__ == "__main__":
    main()

