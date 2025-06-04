import copy
import datetime
import os
import platform
import sys
import time

import numpy as np
import pandas as pd
import sklearn
import torch.cuda
import xgboost
from osgeo import gdalconst
from sklearn import ensemble

from common_object.enum import NodataEnum, ModelEnum
from common_util.common import convert_to_list, exclude_finished_tile, get_world_tile, concurrent_execute, \
    concurrent_execute_using_process
from common_util.document import to_csv
from common_util.image import read_raster, create_raster
from common_util.path import create_path
from ta_interpolate.core.general_executor import GeneralExecutor
from ta_interpolate.entity import Path, Configuration, Dataset
from ta_interpolate.refer_date import get_refer_date


def get_model(model, gpu_id):
    regressor = None
    if model in [ModelEnum.LINEAR.value, ModelEnum.POLYNOMIAL.value]:
        regressor = sklearn.linear_model.LinearRegression(n_jobs=40)
    elif model == ModelEnum.LASSO.value:
        regressor = sklearn.linear_model.Lasso()
    elif model == ModelEnum.RANDOM_FOREST.value:
        regressor = ensemble.RandomForestRegressor(n_estimators=400, n_jobs=40, max_features=4, max_depth=40)
    elif model == ModelEnum.SUPPORT_VECTOR_MACHINE.value:
        regressor = sklearn.svm.SVR(C=10000)
    elif model == ModelEnum.GRADIENT_BOOSTING_DECISION_TREE.value:
        regressor = ensemble.GradientBoostingRegressor(learning_rate=0.06, loss="squared_error", n_estimators=200,
                                                       max_features=3, subsample=0.6, max_depth=18)
    elif model == ModelEnum.EXTREME_GRADIENT_BOOSTING.value:
        regressor = xgboost.XGBRegressor(n_estimators=150, learning_rate=0.1, gamma=0.005, reg_lambda=13, max_depth=15,
                                         subsample=0.8, random_state=0, tree_method="hist", device=f"cuda:{gpu_id}")
    return regressor


def check_pending_tile(tile, field, processing_csv, node_name, lock):
    field = str(field)
    if sys.platform.startswith("linux"):
        return check_pending_tile_for_linux(tile, field, processing_csv, node_name)
    while True:
        try:
            if lock is not None:
                lock.acquire()
            with open(processing_csv, "a"):
                origin_modify_time = os.path.getmtime(processing_csv)
                if os.path.getsize(processing_csv) == 0:
                    pd.DataFrame({"tile": [], field: [], "time": []}).to_csv(processing_csv, index=False)
                else:
                    processing_df = pd.read_csv(processing_csv)
                    if tile in processing_df[(processing_df[field] != node_name) & processing_df[field].notnull()]["tile"].values:
                        return False
                record_df = pd.DataFrame({"tile": [tile], field: [node_name], "time": [datetime.datetime.now().strftime("%Y-%m-%d %H:%M")]})
                if os.path.getmtime(processing_csv) == origin_modify_time:
                    record_df.to_csv(processing_csv, mode="a", index=False, header=False)
                    return True
        except Exception as e:
            print(e)
            time.sleep(1)
        finally:
            if lock is not None:
                lock.release()


def check_pending_tile_for_linux(tile, field, processing_csv, node_name):
    import fcntl
    while True:
        with open(processing_csv, "a") as file:
            try:
                fcntl.flock(file, fcntl.LOCK_EX)
                if os.path.getsize(processing_csv) == 0:
                    pd.DataFrame({"tile": [], field: [], "time": []}).to_csv(processing_csv, index=False)
                else:
                    processing_df = pd.read_csv(processing_csv)
                    if tile in processing_df[(processing_df[field] != node_name) & processing_df[field].notnull()]["tile"].values:
                        return False
                pd.DataFrame({"tile": [tile], field: [node_name], "time": [datetime.datetime.now().strftime("%Y-%m-%d %H:%M")]}).to_csv(processing_csv, mode="a", index=False, header=False)
                return True
            except Exception as e:
                print(e)
                time.sleep(1)
            finally:
                fcntl.flock(file, fcntl.LOCK_UN)


def interpolate_ta_by_tile(config: Configuration, tile, year, gpu_id, lock=None):
    path = config.path
    if config.cluster and not check_pending_tile(tile, year, config.processing_csv, f"{platform.node()}_gpu{gpu_id}", lock):
        return
    torch.cuda.set_device(gpu_id)
    ta_nodata = NodataEnum.TEMPERATURE.value
    estimate_ta_path = os.path.join(path.estimate_ta_path, tile)
    interpolate_refer_path = os.path.join(path.interpolate_refer_path, tile)
    create_path(interpolate_refer_path)
    interpolate_ta_path = os.path.join(path.interpolate_ta_path, tile)
    create_path(interpolate_ta_path)
    estimate_result_df = pd.read_csv(os.path.join(path.cloud_estimate_record_path, f"estimate_result_{tile}.csv"))
    refer_date_list = pd.read_csv(os.path.join(path.cloud_refer_date_path, f"refer_date_{tile}.csv"))["DATE"].values
    dataset = Dataset()
    dataset.mask_arr, geo_data = read_raster(os.path.join(path.cloud_mask_path, f"mask_{tile}.tif"))
    mask_size = np.sum(dataset.mask_arr)
    dataset.latitude_arr = read_raster(os.path.join(path.cloud_latitude_path, f"lat_{tile}.tif"))[0]
    dataset.longitude_arr = read_raster(os.path.join(path.cloud_longitude_path, f"lon_{tile}.tif"))[0]
    dataset.elevation_arr = read_raster(os.path.join(path.dem_path, f"dem_{tile}.tif"))[0]
    executor = GeneralExecutor(config, get_model(config.model, gpu_id), dataset)
    if config.interpolate_refer:
        date_list = refer_date_list
        record_csv = os.path.join(path.cloud_interpolate_refer_record_path, f"interpolate_refer_record_{tile}.csv")
        finish_csv = os.path.join(path.cloud_interpolate_refer_path, f"finish_refer.csv")
    else:
        estimate_result_df = estimate_result_df[(estimate_result_df["DATE"].map(lambda date: date // 1000) == year)
                                                & (estimate_result_df["SUM"] >= min(mask_size * 0.01, 1000))]
        date_list = [date for date in estimate_result_df["DATE"].values if date not in refer_date_list]
        record_csv = os.path.join(path.cloud_interpolate_record_path, f"interpolate_ta_record_{tile}.csv")
        finish_csv = os.path.join(path.cloud_interpolate_ta_path, f"finish_ta_{year}.csv")
    count = 0
    if os.path.isfile(record_csv):
        finished_date_df = pd.read_csv(record_csv)
        if not config.interpolate_refer:
            finished_date_df = finished_date_df[finished_date_df["date"].map(lambda date: date // 1000) == year]
        finished_date_list = finished_date_df["date"].values
        date_list = np.setdiff1d(np.array(date_list), finished_date_list)
        count = finished_date_list.size
    date_list = np.sort(date_list)
    for date in date_list:
        ta_arr = dataset.ta_arr = read_raster(os.path.join(estimate_ta_path, f"ta_{tile}_{date}.tif"))[0]
        current_size = ta_arr[ta_arr != ta_nodata].size
        record_dict = {"date": [date], "origin_size": [current_size]}
        if config.interpolate_refer:
            dataset.train_ta_arr = copy.deepcopy(ta_arr)
            modeling_y = "TRAIN_TA"
            other_refer_date_list = list(copy.deepcopy(refer_date_list))
            other_refer_date_list.remove(date)
            if "REFER" in config.modeling_x_list:
                for i in range(1, config.interpolate_refer_rounds+1):
                    refer_date, interval = get_refer_date(date, other_refer_date_list)
                    record_dict[f"refer_date{i}"] = [refer_date]
                    if refer_date == 0:
                        record_dict[f"refer_interpolate_size{i}"] = [0]
                        continue
                    other_refer_date_list.remove(refer_date)
                    dataset.refer_arr = read_raster(os.path.join(estimate_ta_path, f"ta_{tile}_{refer_date}.tif"))[0]
                    pred_size = executor.prebuild_pred_x_arr()
                    if (pred_size == 0) or (i != 1 and current_size > mask_size * 0.95 and pred_size < mask_size * 0.01):
                        record_dict[f"refer_interpolate_size{i}"] = [0]
                        continue
                    executor.fit(modeling_y=modeling_y, prebuild_pred_x_arr=True)
                    executor.predict(prebuild_pred_x_arr=True)
                    record_dict[f"refer_interpolate_size{i}"] = [pred_size]
                    current_size = ta_arr[ta_arr != ta_nodata].size
                record_dict["refer_interpolated_size"] = [current_size]
                create_raster(os.path.join(interpolate_refer_path, f"ta_{tile}_{date}.tif"), ta_arr, geo_data, ta_nodata, output_type=gdalconst.GDT_Int16)
            modeling_x_list = [modeling_x for modeling_x in config.modeling_x_list if modeling_x != "REFER"]
            executor.fit(modeling_x_list, modeling_y)
            executor.predict(modeling_x_list)
        else:
            refer_date, interval = get_refer_date(date, refer_date_list)
            record_dict["refer_date"] = [refer_date]
            dataset.refer_arr = read_raster(os.path.join(interpolate_ta_path, f"ta_{tile}_{refer_date}.tif"))[0]
            executor.fit()
            executor.predict()
        create_raster(os.path.join(interpolate_ta_path, f"ta_{tile}_{date}.tif"), ta_arr, geo_data, ta_nodata)
        ta_value_arr = ta_arr[ta_arr != ta_nodata]
        record_dict["interpolated_size"] = ta_value_arr.size
        record_dict["min_ta"] = np.min(ta_value_arr) / 100
        record_dict["avg_ta"] = np.average(ta_value_arr) / 100
        record_dict["max_ta"] = np.max(ta_value_arr) / 100
        to_csv(pd.DataFrame(record_dict), record_csv)
        count += 1
        print(tile, date, ta_value_arr.size)
    to_csv(pd.DataFrame({"tile": [tile], year: [count]}), finish_csv, lock=lock)
    print(tile, count)


def interpolate_using_single_gpu(config: Configuration, tile_list, year_list, gpu_id, pool_size):
    path = config.path
    args_list = []
    for year in year_list:
        if config.interpolate_refer:
            config.processing_csv = os.path.join(path.cloud_interpolate_refer_path, f"processing_refer.csv")
            finish_csv = os.path.join(path.cloud_interpolate_refer_path, f"finish_refer.csv")
            finish_year_csv = ""
        else:
            config.processing_csv = os.path.join(path.cloud_interpolate_ta_path, f"processing_ta_{year}.csv")
            finish_csv = os.path.join(path.cloud_interpolate_ta_path, f"finish_ta.csv")
            finish_year_csv = os.path.join(path.cloud_interpolate_ta_path, f"finish_ta_{year}.csv")
        process_tile_list = exclude_finished_tile(tile_list, year, finish_csv, finish_year_csv)
        for tile in process_tile_list:
            args_list.append([config, tile, year, gpu_id])
    concurrent_execute(interpolate_ta_by_tile, args_list, pool_size)


def interpolate(config: Configuration, tile_list, year_list, pool_size=1):
    tile_list = convert_to_list(tile_list)
    year_list = convert_to_list(year_list)
    args_list = []
    for gpu_id in range(torch.cuda.device_count()):
        args_list.append([config, tile_list, year_list, gpu_id, pool_size])
    concurrent_execute_using_process(interpolate_using_single_gpu, args_list, False)


def handle_duplicate_record(config: Configuration, tile_list):
    path = config.path
    for tile in tile_list:
        record_csv = os.path.join(path.cloud_interpolate_refer_record_path, f"interpolate_refer_record_{tile}.csv") if config.interpolate_refer \
            else os.path.join(path.cloud_interpolate_record_path, f"interpolate_ta_record_{tile}.csv")
        record_df = pd.read_csv(record_csv).drop_duplicates("date")
        to_csv(record_df, record_csv, False)


def main():
    config = Configuration()
    config.path = Path()
    config.model = ModelEnum.EXTREME_GRADIENT_BOOSTING.value
    config.modeling_x_list = ["REFER", "LATITUDE", "LONGITUDE", "ELEVATION"]
    config.modeling_y = "TA"
    config.cluster = True
    config.interpolate_refer = False
    tile_list = get_world_tile(config.path)
    year_list = [2023]
    interpolate(config, tile_list, year_list, 1)
    # handle_duplicate_record(config, tile_list)


if __name__ == "__main__":
    main()
