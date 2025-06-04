import os

import numpy as np
import pandas as pd

from common_object.enum import NodataEnum
from common_util.array import build_modeling_arr_with_std
from common_util.document import to_csv


class BaseDataset(object):
    nodata_dict = {"GQ": NodataEnum.TEMPERATURE.value, "ALL": NodataEnum.TEMPERATURE.value,
                   "ANGLE": NodataEnum.VIEW_ANGLE.value,
                   "TA": NodataEnum.TEMPERATURE.value, "REFER": NodataEnum.TEMPERATURE.value,
                   "EVI": NodataEnum.VEGETATION_INDEX.value, "NDVI": NodataEnum.VEGETATION_INDEX.value,
                   "LATITUDE": NodataEnum.LATITUDE_LONGITUDE.value, "LONGITUDE": NodataEnum.LATITUDE_LONGITUDE.value,
                   "ELEVATION": NodataEnum.DEM.value,
                   "MONTH": NodataEnum.DATE.value, "DOY": NodataEnum.DATE.value}

    def __init__(self):
        self.mask_arr = None

        self.evi_arr = None
        self.ndvi_arr = None
        self.latitude_arr = None
        self.longitude_arr = None
        self.elevation_arr = None

        self.ta_arr = None

    @staticmethod
    def _read_csv(tile_list, year_list, temp_attribute_list, base_path, basename, usecols=None, dtype=None):
        temp_attribute_str = f"{temp_attribute_list[0]}_{temp_attribute_list[-1]}"
        value_file = os.path.join(base_path, basename.replace("tile", temp_attribute_str))
        if not os.path.isfile(value_file):
            value_df_list = []
            for tile in tile_list:
                value_tile_file = os.path.join(base_path, basename.replace("tile", tile))
                if os.path.isfile(value_tile_file):
                    value_df = pd.read_csv(value_tile_file, usecols=usecols, dtype=dtype)
                    value_df = value_df[value_df["YEAR"].isin(year_list) & value_df["TEMP_ATTRIBUTES"].isin(temp_attribute_list)]
                    if value_df.shape[0] > 0:
                        value_df_list.append(value_df)
            value_df = pd.concat(value_df_list, ignore_index=True)
            to_csv(value_df, value_file, False)
        else:
            value_df = pd.read_csv(value_file, usecols=usecols, dtype=dtype)
            value_df = value_df[value_df["YEAR"].isin(year_list)]
        return value_df

    def build_modeling_arr_from_arr(self, modeling_x_list, modeling_y, modeling=True, std=False, x_scaler_list=None, y_scaler=None):
        modeling_x_arr = None
        modeling_y_arr = None
        y_arr = getattr(self, f"{modeling_y.lower()}_arr")
        if modeling:
            condition = (y_arr != self.nodata_dict[modeling_y.split("_")[-1]]) & (self.mask_arr != NodataEnum.MASK.value)
        else:
            condition = (y_arr == self.nodata_dict[modeling_y.split("_")[-1]]) & (self.mask_arr != NodataEnum.MASK.value)
        x_arr_list = []
        for modeling_x in modeling_x_list:
            x_arr = getattr(self, f"{modeling_x.lower()}_arr")
            if x_arr is None:
                x_arr_list.clear()
                break
            x_arr_list.append(x_arr)
            condition &= (x_arr != self.nodata_dict[modeling_x.split("_")[-1]])
        y_1d_arr = y_arr[condition]
        if x_arr_list and y_1d_arr.size > 0:
            modeling_x_arr_list = [x_arr[condition] for x_arr in x_arr_list]
            if modeling:
                modeling_y_arr = y_1d_arr
            if std:
                modeling_x_arr, modeling_y_arr, x_scaler_list, y_scaler = build_modeling_arr_with_std(modeling_x_arr_list, modeling_y_arr, x_scaler_list, y_scaler)
            else:
                modeling_x_arr = np.stack(modeling_x_arr_list, -1)
        return modeling_x_arr, modeling_y_arr, condition, x_scaler_list, y_scaler
