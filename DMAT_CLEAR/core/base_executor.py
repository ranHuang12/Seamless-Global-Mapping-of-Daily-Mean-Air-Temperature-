import os
import pickle

import cupy
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from common_object.entity import Accuracy
from common_object.enum import ValidateModeEnum, QcModeEnum, ViewEnum, ColumnsEnum
from common_util.array import build_modeling_arr_from_df, inverse_transform
from common_util.common import build_modeling_x_list, convert_enum_to_value
from common_util.date import get_date_interval
from common_util.document import to_csv, handle_null
from ta_estimate.entity.configuration import Configuration
from ta_estimate.entity.dataset import Dataset


class BaseExecutor(object):
    all_view_list = convert_enum_to_value(ViewEnum)
    all_auxiliary_list = ["EVI", "ANGLE", "LATITUDE", "LONGITUDE", "ELEVATION", "MONTH", "DOY"]

    def __init__(self, config, model, dataset, time_series):
        self.config: Configuration = config
        self.model = model
        self.dataset: Dataset = dataset
        self.time_series = time_series

        self.x_scaler_list = None
        self.y_scaler = None

        self.train_x_arr, self.train_y_arr, self.original_train_y_arr = None, None, None
        self.validate_x_arr, self.validate_y_arr = None, None
        self.test_x_arr, self.test_y_arr = None, None
        self.pred_x_arr, self.pred_y_arr = None, None

        self.train_precision: Accuracy = Accuracy()
        self.validate_precision: Accuracy = Accuracy()
        self.test_precision: Accuracy = Accuracy()

        self.importance_list = None

        self.lock = None

    # 时间序列相关均为测试代码，未完善，未实际使用
    def __convert_to_time_series(self, modeling_df, dataset_name, time_size):
        time_size_file = os.path.join(self.config.path.estimate_modeling_data_path, f"{dataset_name}_modeling_t{time_size}.csv")
        if os.path.isfile(time_size_file):
            modeling_df = pd.read_csv(time_size_file)
        else:
            modeling_df = modeling_df.sort_values("DATE")
            station_df_list = []
            for station, station_df in modeling_df.groupby("STATION"):
                station_df.sort_values("DATE")
                for index in range(time_size - 1, station_df.shape[0]):
                    prev_index = index - time_size + 1
                    if get_date_interval(station_df.iloc[prev_index]["DATE"], station_df.iloc[index]["DATE"]) == time_size - 1:
                        station_df_list.append(station_df.iloc[prev_index:index + 1])
            modeling_df = pd.concat(station_df_list)
            to_csv(modeling_df, time_size_file, False)
        return modeling_df

    def __build_modeling_arr(self, modeling_df, modeling_x_list=None):
        if modeling_df.size == 0:
            return np.array([]), np.array([]), np.array([])
        if modeling_x_list is None:
            modeling_x_list = self.config.modeling_x_list
        modeling_y = self.config.modeling_y
        for modeling_x in modeling_x_list:
            modeling_df = modeling_df[modeling_df[modeling_x].notnull()]
        time_size = self.config.time_size
        if time_size != 1:
            modeling_df = self.__convert_to_time_series(modeling_df, "", time_size)
        x_arr, y_arr, original_y_arr, self.x_scaler_list, self.y_scaler =\
            build_modeling_arr_from_df(modeling_df, modeling_x_list, modeling_y, self.config.std, self.x_scaler_list, self.y_scaler)
        if time_size != 1:
            x_arr = x_arr.reshape(-1, time_size, len(modeling_x_list))
            if not self.time_series:
                x_arr = x_arr[:, time_size-1, :]
            y_arr = y_arr.reshape(-1, time_size)[:, time_size-1]
            original_y_arr = original_y_arr.reshape(-1, time_size)[:, time_size-1]
        return x_arr, y_arr, original_y_arr

    # 保留了适应深度学习的train-validate-test数据集划分部分代码，但目前仅使用train-validate数据集划分
    def _build_modeling_dataset(self, use_serialized_model: bool, serialize: bool):
        config = self.config
        dataset = self.dataset
        modeling_df = dataset.modeling_df
        path = config.path
        validate_mode = config.validate_mode
        serialized_xscaler_file = os.path.join(path.model_path, f"xscaler_{''.join(view.view_name for view in config.view_list)}_{config.qc_mode.field}.pkl")
        serialized_yscaler_file = os.path.join(path.model_path, f"yscaler_{''.join(view.view_name for view in config.view_list)}_{config.qc_mode.field}.pkl")
        if use_serialized_model and config.std and os.path.isfile(serialized_xscaler_file) and os.path.isfile(serialized_yscaler_file):
            with open(serialized_xscaler_file, "rb") as file:
                self.x_scaler_list = pickle.load(file)
            with open(serialized_yscaler_file, "rb") as file:
                self.y_scaler = pickle.load(file)
        validate_x_list = config.modeling_x_list
        if validate_mode == ValidateModeEnum.RANDOM.value:
            train_df, validate_test_df = train_test_split(modeling_df, test_size=config.validate_test_ratio, random_state=0)
            validate_df, test_df = train_test_split(validate_test_df, test_size=config.test_ratio/config.validate_test_ratio, random_state=0)
        elif validate_mode == ValidateModeEnum.TILE.value:
            train_df = modeling_df[modeling_df["TILE"].isin(config.train_tile_list)]
            validate_df = modeling_df[modeling_df["TILE"].isin(config.validate_tile_list)]
            test_df = modeling_df[modeling_df["TILE"].isin(config.test_tile_list)]
        elif validate_mode == ValidateModeEnum.TIME.value:
            train_df = modeling_df[modeling_df["YEAR"].isin(config.train_year_list)]
            validate_df = modeling_df[modeling_df["YEAR"].isin(config.validate_year_list)]
            test_df = modeling_df[modeling_df["YEAR"].isin(config.test_year_list)]
        elif validate_mode in [ValidateModeEnum.FILE_ALL.value, ValidateModeEnum.FILE_GQ.value, ValidateModeEnum.FILE_OQ.value]:
            train_df = pd.concat([modeling_df, dataset.validate_df]).drop_duplicates(ColumnsEnum.SINGLE_METE.value, keep=False)
            if validate_mode == ValidateModeEnum.FILE_ALL.value:
                validate_df = dataset.validate_df
                test_df = dataset.test_df
                validate_x_list = build_modeling_x_list(config.view_list, QcModeEnum.ALL.value, config.auxiliary_list)
            elif validate_mode == ValidateModeEnum.FILE_GQ.value:
                validate_df = handle_null(dataset.validate_df, build_modeling_x_list(self.all_view_list, QcModeEnum.GOOD_QUALITY.value, self.all_auxiliary_list))
                test_df = handle_null(dataset.test_df, build_modeling_x_list(self.all_view_list, QcModeEnum.GOOD_QUALITY.value, self.all_auxiliary_list))
                validate_x_list = build_modeling_x_list(config.view_list, QcModeEnum.GOOD_QUALITY.value, config.auxiliary_list)
            else:
                validate_df = handle_null(dataset.validate_df, build_modeling_x_list(self.all_view_list, QcModeEnum.ALL.value, []), True)
                test_df = handle_null(dataset.test_df, build_modeling_x_list(self.all_view_list, QcModeEnum.ALL.value, []), True)
                validate_x_list = build_modeling_x_list(config.view_list, QcModeEnum.ALL.value, config.auxiliary_list)
        elif validate_mode == ValidateModeEnum.SPECIFIC_FILE.value:
            train_df = modeling_df
            validate_df = dataset.validate_df
            test_df = dataset.test_df
        else:
            train_df = modeling_df
            validate_df = test_df = pd.DataFrame([])
        self.train_x_arr, self.train_y_arr, self.original_train_y_arr = self.__build_modeling_arr(train_df)
        self.validate_x_arr, _, self.validate_y_arr = self.__build_modeling_arr(validate_df, validate_x_list)
        self.test_x_arr, _, self.test_y_arr = self.__build_modeling_arr(test_df, validate_x_list)
        if serialize and config.std:
            with open(serialized_xscaler_file, "wb") as file:
                pickle.dump(self.x_scaler_list, file)
            with open(serialized_yscaler_file, "wb") as file:
                pickle.dump(self.y_scaler, file)
        print(validate_mode, config.qc_mode.name, "".join(view.view_name for view in config.view_list), config.model)
        print(f"train:{self.train_x_arr.shape}")
        print(f"validate:{self.validate_x_arr.shape}")
        print(f"test:{self.test_x_arr.shape}")

    def _fit(self, use_serialized_model: bool, serialize: bool):
        config = self.config
        model = self.model
        serialized_file = os.path.join(config.path.model_path, f"{config.model}_{''.join(view.view_name for view in config.view_list)}_{config.qc_mode.field}.pkl")
        if use_serialized_model and os.path.isfile(serialized_file):
            with open(serialized_file, "rb") as file:
                self.model = pickle.load(file)
        else:
            train_x_arr = cupy.array(self.train_x_arr)
            train_y_arr = cupy.array(self.train_y_arr)
            model.fit(train_x_arr, train_y_arr)
        if serialize:
            with open(serialized_file, "wb") as file:
                pickle.dump(model, file)

    def build_model(self, use_serialized_model=False, serialize=False, build_dataset=True, record_to_csv=True):
        if build_dataset:
            self._build_modeling_dataset(use_serialized_model, serialize)
        self._fit(use_serialized_model, serialize)
        if record_to_csv:
            config = self.config
            train_precision = self.train_precision
            validate_precision = self.validate_precision
            test_precision = self.test_precision
            record_dict = {"model": [config.model], "view_list": [''.join(view.view_name for view in config.view_list)],
                           "qc_mode": [config.qc_mode.name], "auxiliary_list": [config.auxiliary_list],
                           "modeling_y": [config.modeling_y], "modeling_attribute_list": [config.modeling_attribute_list],
                           "validate_mode": [config.validate_mode], "std": [config.std],
                           "train_count": [self.train_precision.size], "train_r2": [train_precision.r2], "train_rmse": [train_precision.rmse], "train_mae": [train_precision.mae], "train_bias": [train_precision.bias],
                           "validate_count": [self.validate_precision.size], "validate_r2": [validate_precision.r2], "validate_rmse": [validate_precision.rmse], "validate_mae": [validate_precision.mae], "validate_bias": [validate_precision.bias]}
            if self.test_x_arr.size != 0:
                record_dict.update({"test_count": [self.test_precision.size], "test_r2": [test_precision.r2], "test_rmse": [test_precision.rmse], "test_mae": [test_precision.mae], "test_bias": [test_precision.bias]})
            to_csv(pd.DataFrame(record_dict), os.path.join(config.path.cloud_record_path, "modeling", f"{config.model}_accuracy.csv"), lock=self.lock)
            """
            importance_dict = {"model": [config.model], "view_list": [config.view_list], "qc_mode": [config.qc_mode], "auxiliary_list": config.auxiliary_list, "modeling_y": [config.modeling_y]}
            for modeling_x in build_modeling_x_list(convert_enum_to_value(ViewEnum), config.qc_mode, config.auxiliary_list):
                importance_dict[modeling_x] = 0
            for index, modeling_x in enumerate(config.modeling_x_list):
                importance_dict[modeling_x] = self.importance_list[index]
            to_csv(pd.DataFrame(importance_dict), os.path.join(config.path.cloud_record_path, "modeling", f"{config.model}_importance.csv"), lock=self.lock)
            """

    def predict(self):
        pred_x_arr = cupy.array(self.pred_x_arr)
        pred_y_arr = self.model.predict(pred_x_arr)
        self.pred_y_arr = inverse_transform(pred_y_arr, self.y_scaler) if self.config.std else pred_y_arr
