import os
import pickle
from copy import deepcopy

import numpy as np
import pandas as pd
from osgeo import gdalconst
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Lasso
from sklearn.svm import SVR
from xgboost import XGBRegressor

from common_object.entity import Accuracy
from common_object.enum import ViewEnum, ModelEnum, ValidateModeEnum, QcModeEnum, NodataEnum, ColumnsEnum
from common_util.array import build_modeling_arr_from_df
from common_util.common import get_world_tile, convert_enum_to_value, exclude_finished_tile, build_modeling_x_list, \
    concurrent_execute
from common_util.date import get_all_modis_date_by_year
from common_util.document import to_csv, merge_csv, handle_null
from common_util.image import read_raster, create_raster
from common_util.path import create_path
from ta_estimate.core.general_executor import GeneralExecutor
from ta_estimate.entity.configuration import Configuration
from ta_estimate.entity.dataset import Dataset
from ta_estimate.module.cnn import CNN
from ta_estimate.module.cnn_lstm import CNNLSTM
from ta_estimate.module.cnn_lstm_attn import CNNLSTMAttention
from ta_estimate.module.fc import FC


def get_model(model, feature_size=0, time_size=1):
    regressor = None
    if model == ModelEnum.CNN.value:
        regressor = CNN(feature_size)
    elif model == ModelEnum.FC.value:
        regressor = FC(feature_size)
    elif model == ModelEnum.CNN_LSTM.value:
        regressor = CNNLSTM(feature_size)
    elif model == ModelEnum.CNN_LSTM_ATTENTION.value:
        regressor = CNNLSTMAttention(feature_size, time_size)
    elif model in [ModelEnum.LINEAR.value, ModelEnum.POLYNOMIAL.value]:
        regressor = LinearRegression(n_jobs=40)
    elif model == ModelEnum.LASSO.value:
        regressor = Lasso()
    elif model == ModelEnum.RANDOM_FOREST.value:
        regressor = RandomForestRegressor(n_estimators=400, n_jobs=40, max_features=4, max_depth=40)
    elif model == ModelEnum.SUPPORT_VECTOR_MACHINE.value:
        regressor = SVR(C=10000)
    elif model == ModelEnum.GRADIENT_BOOSTING_DECISION_TREE.value:
        regressor = GradientBoostingRegressor(learning_rate=0.06, loss="squared_error", n_estimators=200,
                                              max_features=3, subsample=0.6, max_depth=18)
    elif model == ModelEnum.EXTREME_GRADIENT_BOOSTING.value:
        regressor = XGBRegressor(n_estimators=400, learning_rate=0.1, gamma=0.005, reg_lambda=13, max_depth=22,
                                 subsample=0.9, tree_method="hist", device="cuda")
    return regressor


def build_single_model(config: Configuration, dataset: Dataset, model_list, lock=None):
    executor = GeneralExecutor(config, None, dataset)
    for index, model in enumerate(model_list):
        config.model = model
        executor.model = get_model(model)
        executor.lock = lock
        executor.build_model(False, True, index == 0, True)


def build_model(config: Configuration, pool_size=1):
    validate_mode_list = [ValidateModeEnum.TIME.value]
    qc_mode_list = [QcModeEnum.ALL.value]
    views_list = [[ViewEnum.TD.value, ViewEnum.TN.value, ViewEnum.AD.value, ViewEnum.AN.value],
                  [ViewEnum.TD.value, ViewEnum.TN.value],
                  [ViewEnum.AD.value, ViewEnum.AN.value],
                  [ViewEnum.TN.value],
                  [ViewEnum.AN.value],
                  [ViewEnum.TD.value],
                  [ViewEnum.AD.value]]
    auxiliarys_list = [[],
                       ["ANGLE", "LATITUDE", "LONGITUDE", "ELEVATION", "MONTH", "DOY", "EVI"],
                       ["LATITUDE", "LONGITUDE", "ELEVATION", "MONTH", "DOY", "EVI"],
                       ["ANGLE", "LONGITUDE", "ELEVATION", "MONTH", "DOY", "EVI"],
                       ["ANGLE", "LATITUDE", "ELEVATION", "MONTH", "DOY", "EVI"],
                       ["ANGLE", "LATITUDE", "LONGITUDE", "MONTH", "DOY", "EVI"],
                       ["ANGLE", "LATITUDE", "LONGITUDE", "ELEVATION", "DOY", "EVI"],
                       ["ANGLE", "LATITUDE", "LONGITUDE", "ELEVATION", "MONTH", "EVI"],
                       ["ANGLE", "LATITUDE", "LONGITUDE", "ELEVATION", "MONTH", "DOY"],
                       ["LATITUDE", "LONGITUDE", "ELEVATION", "MONTH", "DOY"],
                       ["ANGLE", "LONGITUDE", "ELEVATION", "MONTH", "DOY"],
                       ["ANGLE", "LATITUDE", "ELEVATION", "MONTH", "DOY"],
                       ["ANGLE", "LATITUDE", "LONGITUDE", "MONTH", "DOY"],
                       ["ANGLE", "LATITUDE", "LONGITUDE", "ELEVATION", "DOY"],
                       ["ANGLE", "LATITUDE", "LONGITUDE", "ELEVATION", "MONTH"]]
    auxiliarys_list = [["ANGLE", "LATITUDE", "LONGITUDE", "ELEVATION", "MONTH", "DOY"]]
    model_list = [ModelEnum.LINEAR.value, ModelEnum.RANDOM_FOREST.value, ModelEnum.EXTREME_GRADIENT_BOOSTING.value]
    model_list = [ModelEnum.EXTREME_GRADIENT_BOOSTING.value]
    config.modeling_attribute_list = list(range(24, 25))
    dataset = Dataset(config).load_modeling_data(load_validate_data=False)
    args_list = []
    for validate_mode in validate_mode_list:
        config.validate_mode = validate_mode
        dataset.load_modeling_data(False, True)
        if validate_mode == ValidateModeEnum.TIME.value:
            config.train_year_list = list(range(2020, 2023))
            config.validate_year_list = [2023]
        for qc_mode in qc_mode_list:
            config.qc_mode = qc_mode
            for view_list in views_list:
                config.view_list = view_list
                for auxiliary_list in auxiliarys_list:
                    config.auxiliary_list = auxiliary_list
                    config.modeling_x_list = build_modeling_x_list(view_list, qc_mode, auxiliary_list)
                    args_list.append([deepcopy(config), dataset, model_list])
    concurrent_execute(build_single_model, args_list, pool_size)


def simulate_estimate_ta(config: Configuration, views_list, model_list, x_scalers_list, y_scaler_list):
    path = config.path
    config.validate_mode = ValidateModeEnum.SIMULATE.value
    dataset = Dataset(config).load_modeling_data(load_validate_data=False)
    # modeling_df = dataset.modeling_df
    # for field in ["LATITUDE", "LONGITUDE", "TEMP", "TD_ALL", "TN_ALL", "AD_ALL", "AN_ALL"]:
    #     modeling_df[field] = modeling_df[field].map(lambda value: value / 100)
    executor = GeneralExecutor(config, None, dataset)
    record_file = os.path.join(path.cloud_record_path, "modeling", f"{config.model}_accuracy.csv")
    result_df_list = []
    for index, view_list in enumerate(views_list):
        executor.model = model_list[index]
        executor.x_scaler_list = x_scalers_list[index]
        executor.y_scaler = y_scaler_list[index]
        modeling_x_list = build_modeling_x_list(view_list, config.qc_mode, config.auxiliary_list)
        modeling_df = handle_null(dataset.modeling_df, modeling_x_list)
        executor.pred_x_arr, _, y_arr, _, _ = build_modeling_arr_from_df(modeling_df, modeling_x_list, config.modeling_y, config.std, x_scalers_list[index], y_scaler_list[index])
        executor.predict(False)
        dataset.modeling_df = pd.concat([dataset.modeling_df, modeling_df]).drop_duplicates(ColumnsEnum.SINGLE_METE.value, keep=False)
        result_df_list.append(modeling_df.assign(PRED_TEMP=list(executor.pred_y_arr)))
        accuracy = Accuracy.validate(y_arr, executor.pred_y_arr, 0.01)
        view_list_str = ''.join(view.view_name for view in view_list)
        print(view_list_str, accuracy)
        record_dict = {"model": [config.model], "view_list": [view_list_str], "qc_mode": [config.qc_mode.name],
                       "auxiliary_list": [config.auxiliary_list], "modeling_y": [config.modeling_y],
                       "modeling_attribute_list": [config.modeling_attribute_list],
                       "validate_mode": [config.validate_mode], "std": [config.std], "validate_count": [accuracy.size],
                       "validate_r2": [accuracy.r2], "validate_rmse": [accuracy.rmse], "validate_mae": [accuracy.mae],
                       "validate_bias": [accuracy.bias]}
        merge_csv(record_file, pd.DataFrame(record_dict), along_column=False)
    result_df = pd.concat(result_df_list, ignore_index=True)
    accuracy = Accuracy.validate(result_df["TEMP"].values, result_df["TA"].values, 0.01)
    to_csv(result_df, os.path.join(path.estimate_validate_data_path, f"{config.model}_{config.validate_mode}_{config.qc_mode.field}_validate_result.csv"), False)
    record_dict = {"model": [config.model], "view_list": ["all"], "qc_mode": [config.qc_mode.name],
                   "auxiliary_list": [config.auxiliary_list], "modeling_y": [config.modeling_y],
                   "modeling_attribute_list": [config.modeling_attribute_list],
                   "validate_mode": [config.validate_mode], "std": [config.std], "validate_count": [accuracy.size],
                   "validate_r2": [accuracy.r2], "validate_rmse": [accuracy.rmse], "validate_mae": [accuracy.mae],
                   "validate_bias": [accuracy.bias]}
    print("all", accuracy)
    merge_csv(record_file, pd.DataFrame(record_dict), along_column=False)


def estimate_ta_by_tile(config: Configuration, tile, year, views_list, model_list, x_scalers_list, y_scaler_list, lock=None):
    path = config.path
    qc_mode = config.qc_mode
    config.modeling_y = "TA"
    ta_path = os.path.join(path.estimate_ta_path, tile)
    create_path(ta_path)
    dataset = Dataset(config)
    mask_arr, geo_data = read_raster(os.path.join(path.cloud_mask_path, f"mask_{tile}.tif"))
    dataset.mask_arr = mask_arr
    dataset.latitude_arr = read_raster(os.path.join(path.cloud_latitude_path, f"lat_{tile}.tif"))[0]
    dataset.longitude_arr = read_raster(os.path.join(path.cloud_longitude_path, f"lon_{tile}.tif"))[0]
    dataset.elevation_arr = read_raster(os.path.join(path.dem_path, f"dem_{tile}.tif"))[0]
    executor = GeneralExecutor(config, None, dataset)
    count = 0
    record_csv = os.path.join(path.cloud_estimate_record_path, f"estimate_result_{tile}.csv")
    date_list = get_all_modis_date_by_year(year)
    if os.path.isfile(record_csv):
        finished_date = np.unique(pd.read_csv(record_csv)["DATE"].values)
        finished_date = list(filter(lambda date: (date // 1000) == year, finished_date))
        count = len(finished_date)
        date_list = list(filter(lambda modis_date: modis_date.modis_date not in finished_date, date_list))
    for modis_date in date_list:
        date = modis_date.modis_date
        for view in convert_enum_to_value(ViewEnum):
            view_name = view.view_name
            lst_file = os.path.join(path.lst_path, f"{view_name}_{qc_mode.name}", tile, f"{view_name}_{tile}_{qc_mode.name}_{date}.tif")
            if os.path.isfile(lst_file):
                setattr(dataset, f"{view_name.lower()}_{qc_mode.field.lower()}_arr", read_raster(lst_file)[0])
            else:
                continue
            angle_file = os.path.join(path.lst_path, f"{view_name}_angle", tile, f"{view_name}_{tile}_angle_{date}.tif")
            if os.path.isfile(angle_file):
                setattr(dataset, f"{view_name.lower()}_angle_arr", read_raster(angle_file)[0])
        dataset.month_arr = np.full_like(mask_arr, modis_date.month)
        dataset.doy_arr = np.full_like(mask_arr, modis_date.doy)
        dataset.ta_arr = np.full_like(mask_arr, NodataEnum.TEMPERATURE.value)
        result_dict = {"DATE": [date]}
        for index, view_list in enumerate(views_list):
            config.modeling_x_list = build_modeling_x_list(view_list, qc_mode, config.auxiliary_list)
            executor.model = model_list[index]
            executor.x_scaler_list = x_scalers_list[index]
            executor.y_scaler = y_scaler_list[index]
            pixel_count = executor.predict()
            result_dict["".join(view.view_name for view in view_list)] = pixel_count
        ta_value_arr = dataset.ta_arr[dataset.ta_arr != NodataEnum.TEMPERATURE.value]
        result_dict["SUM"] = [ta_value_arr.size]
        result_dict["MIN_TA"] = result_dict["MAX_TA"] = result_dict["AVG_TA"] = [NodataEnum.TEMPERATURE.value]
        if ta_value_arr.size > 0:
            result_dict["MIN_TA"] = np.min(ta_value_arr) / 100
            result_dict["MAX_TA"] = np.max(ta_value_arr) / 100
            result_dict["AVG_TA"] = np.average(ta_value_arr) / 100
            create_raster(os.path.join(ta_path, f"ta_{tile}_{date}.tif"), dataset.ta_arr, geo_data, NodataEnum.TEMPERATURE.value, output_type=gdalconst.GDT_Int16)
            count += 1
        to_csv(pd.DataFrame(result_dict), record_csv)
    to_csv(pd.DataFrame({"tile": [tile], year: [count]}), os.path.join(path.estimate_ta_path, f"finish_ta_{year}.csv"), lock=lock)
    print(tile, year, count)


def estimate_ta(config: Configuration, pool_size=1):
    path = config.path
    config.modeling_attribute_list = list(range(24, 25))
    config.qc_mode = QcModeEnum.ALL.value
    config.model = ModelEnum.EXTREME_GRADIENT_BOOSTING.value
    views_list = [[ViewEnum.TD.value, ViewEnum.TN.value, ViewEnum.AD.value, ViewEnum.AN.value],
                  [ViewEnum.TD.value, ViewEnum.TN.value],
                  [ViewEnum.AD.value, ViewEnum.AN.value],
                  [ViewEnum.TN.value],
                  [ViewEnum.AN.value],
                  [ViewEnum.TD.value],
                  [ViewEnum.AD.value]]
    config.auxiliary_list = ["ANGLE", "LATITUDE", "LONGITUDE", "ELEVATION", "MONTH", "DOY"]
    model_list = []
    x_scalers_list = []
    y_scaler_list = []
    model_path = os.path.join(path.model_path, "3years", "24std")
    for view_list in views_list:
        view_list_str = ''.join(view.view_name for view in view_list)
        with open(os.path.join(model_path, f"{config.model}_{view_list_str}_{config.qc_mode.field}.pkl"), "rb") as file:
            model_list.append(pickle.load(file))
        if config.std:
            with open(os.path.join(model_path, f"xscaler_{view_list_str}_{config.qc_mode.field}.pkl"), "rb") as file:
                x_scalers_list.append(pickle.load(file))
            with open(os.path.join(model_path, f"yscaler_{view_list_str}_{config.qc_mode.field}.pkl"), "rb") as file:
                y_scaler_list.append(pickle.load(file))
        else:
            x_scalers_list = [None] * len(model_list)
            y_scaler_list = [None] * len(model_list)
    """
    simulate_estimate_ta(config, views_list, model_list, x_scalers_list, y_scaler_list)
    """
    finish_csv = os.path.join(path.estimate_ta_path, "finish_ta.csv")
    for year in config.year_list:
        args_list = []
        finish_year_csv = os.path.join(path.estimate_ta_path, f"finish_ta_{year}.csv")
        for tile in exclude_finished_tile(config.tile_list, year, finish_csv, finish_year_csv):
            args_list.append([config, tile, year, views_list, model_list, x_scalers_list, y_scaler_list])
        concurrent_execute(estimate_ta_by_tile, args_list, pool_size)
        merge_csv(finish_csv, finish_year_csv, "tile", "outer")
        if os.path.isfile(finish_year_csv):
            os.remove(finish_year_csv)


def modeling_data_statistics(config: Configuration):
    path = config.path
    config.modeling_attribute_list = list(range(1, 25))
    dataset = Dataset(config).load_modeling_data(load_validate_data=False)
    modeling_df = dataset.modeling_df
    record_df_list = []
    for year, modeling_year_df in modeling_df.groupby("YEAR"):
        record_dict = {"temp_attribute_list": [config.modeling_attribute_list], "year": [year], "data_size": [modeling_year_df.shape[0]], "station_size": [np.unique(modeling_year_df["STATION"].values).size]}
        record_df_list.append(pd.DataFrame(record_dict))
    record_dict = {"temp_attribute_list": [config.modeling_attribute_list], "year": ["all"], "data_size": [modeling_df.shape[0]], "station_size": [np.unique(modeling_df["STATION"].values).size]}
    record_df_list.append(pd.DataFrame(record_dict))
    to_csv(pd.concat(record_df_list, ignore_index=True), os.path.join(path.cloud_estimate_modeling_data_path, "modeling_data_statistics.csv"))


def main():
    config = Configuration()
    config.modeling_y = "TEMP"
    config.tile_list = get_world_tile(config.path)
    config.year_list = list(range(2020, 2024))
    config.std = True
    config.time_size = 1
    # build_model(config, 1)
    # estimate_ta(config, 4)
    modeling_data_statistics(config)


if __name__ == '__main__':
    main()
