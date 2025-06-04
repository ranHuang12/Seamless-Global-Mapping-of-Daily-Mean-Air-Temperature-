import os.path

import numpy as np
import pandas as pd

from common_object.entity import BasePath
from common_object.enum import NodataEnum, QcModeEnum, ViewEnum
from common_util.common import get_world_tile, concurrent_execute, convert_enum_to_value
from common_util.document import to_csv
from common_util.image import read_raster, create_raster, mosaic
from common_util.path import create_path
from data_perprocessing.entity.path import Path


def calculate_single_coverage_by_tile(path: BasePath, value_path, year_list, coverage_file, record_file, stack, lock=None):
    if not os.path.exists(value_path):
        return
    tile = os.path.basename(value_path)
    mask_arr, geo_data = read_raster(os.path.join(path.cloud_mask_path, f"mask_{tile}.tif"))
    coverage_arr = np.zeros_like(mask_arr)
    for year in year_list:
        coverage_year_file = coverage_file.replace(".tif", f"_{year}.tif")
        if os.path.isfile(coverage_year_file):
            coverage_arr += read_raster(coverage_year_file)[0]
        else:
            coverage_year_arr = np.zeros_like(mask_arr)
            for filename in os.listdir(value_path):
                if int(filename.split(".")[0].split("_")[-1]) // 1000 == year:
                    coverage_year_arr[read_raster(os.path.join(value_path, filename))[0] != NodataEnum.TEMPERATURE.value] += 1
            coverage_value_arr = coverage_year_arr[coverage_year_arr != NodataEnum.COVERAGE.value]
            if coverage_value_arr.size > 0:
                coverage_arr += coverage_year_arr
                create_raster(coverage_year_file, coverage_year_arr, geo_data, NodataEnum.COVERAGE.value)
            to_csv(pd.DataFrame({"tile": [tile], "year": year, "sum": [coverage_value_arr.size],
                                 "min_coverage": [np.min(coverage_value_arr)],
                                 "avg_coverage": [np.mean(coverage_value_arr)],
                                 "max_coverage": [np.max(coverage_value_arr)]}), record_file.replace(".csv", f"_{year}.csv"), lock=lock)
            print(coverage_year_file, np.mean(coverage_value_arr))
    coverage_value_arr = coverage_arr[coverage_arr != NodataEnum.COVERAGE.value]
    if stack and coverage_value_arr.size > 0:
        create_raster(coverage_file, coverage_arr, geo_data, NodataEnum.COVERAGE.value)
    to_csv(pd.DataFrame({"tile": [tile], "sum": [coverage_value_arr.size],
                         "min_coverage": [np.min(coverage_value_arr)],
                         "avg_coverage": [np.mean(coverage_value_arr)],
                         "max_coverage": [np.max(coverage_value_arr)]}), record_file, lock=lock)


def calculate_coverage_by_tile(path: Path, tile, qc_mode_list, view_list, year_list, stack, lock=None):
    for qc_mode in qc_mode_list:
        for view in view_list:
            lst_path = os.path.join(path.lst_path, f"{view.view_name}_{qc_mode.name}", tile)
            coverage_path = os.path.join(path.lst_coverage_path, tile)
            create_path(coverage_path)
            coverage_file = os.path.join(coverage_path, f"coverage_{view.view_name}_{qc_mode.name}_{tile}.tif")
            record_file = os.path.join(path.cloud_lst_coverage_path, f"coverage_record_{view.view_name}_{qc_mode.name}.csv")
            calculate_single_coverage_by_tile(path, lst_path, year_list, coverage_file, record_file, stack, lock)


def merge_coverage(coverage_file_list, coverage_file, record_file, region):
    create_path(os.path.dirname(coverage_file))
    mosaic(coverage_file_list, coverage_file, NodataEnum.COVERAGE.value, NodataEnum.COVERAGE.value)
    coverage_arr = read_raster(coverage_file)[0]
    coverage_value_arr = coverage_arr[coverage_arr != NodataEnum.COVERAGE.value]
    to_csv(pd.DataFrame({"tile": [region], "sum": [coverage_value_arr.size],
                         "min_coverage": [np.min(coverage_value_arr)],
                         "avg_coverage": [np.mean(coverage_value_arr)],
                         "max_coverage": [np.max(coverage_value_arr)]}), record_file)


def calculate_coverage(path: Path, tile_list, qc_mode_list, view_list, year_list, stack=False, merge=False, region=None, pool_size=1):
    args_list = []
    for tile in tile_list:
        args_list.append([path, tile, qc_mode_list, view_list, year_list, stack])
    concurrent_execute(calculate_coverage_by_tile, args_list, pool_size)
    if merge:
        for qc_mode in qc_mode_list:
            for view in view_list:
                coverage_file_list = [os.path.join(path.lst_coverage_path, tile, f"coverage_{view.view_name}_{qc_mode.name}_{tile}.tif") for tile in tile_list]
                coverage_file = os.path.join(path.lst_coverage_path, region, f"coverage_{view.view_name}_{qc_mode.name}_{region}.tif")
                record_file = os.path.join(path.cloud_lst_coverage_path, f"coverage_record_{view.view_name}_{qc_mode.name}.csv")
                merge_coverage(coverage_file_list, coverage_file, record_file, region)


def main():
    path = Path()
    tile_list = get_world_tile(path)
    qc_mode_list = [QcModeEnum.GOOD_QUALITY.value, QcModeEnum.ALL.value]
    view_list = convert_enum_to_value(ViewEnum)
    year_list = list(range(2020, 2024))
    calculate_coverage(path, tile_list, qc_mode_list, view_list, year_list, True, True, "world", 8)


if __name__ == "__main__":
    main()
