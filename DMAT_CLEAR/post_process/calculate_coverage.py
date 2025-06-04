import os

from common_util.common import convert_to_list, get_world_tile, concurrent_execute
from common_util.path import create_path
from data_perprocessing.modis.calculate_coverage import calculate_single_coverage_by_tile, merge_coverage
from ta_estimate.entity import Path


def calculate_coverage_by_tile(path: Path, tile, year_list, stack, lock=None):
    coverage_path = os.path.join(path.estimate_coverage_path, tile)
    create_path(coverage_path)
    coverage_file = os.path.join(coverage_path, f"coverage_ta_{tile}.tif")
    ta_path = os.path.join(path.estimate_ta_path, tile)
    record_file = os.path.join(path.cloud_estimate_coverage_path, "coverage_record_ta.csv")
    calculate_single_coverage_by_tile(path, ta_path, year_list, coverage_file, record_file, stack, lock)


def calculate_coverage(path: Path, tile_list, year_list, stack=False, merge=False, region=None, pool_size=1):
    tile_list = convert_to_list(tile_list)
    year_list = convert_to_list(year_list)
    args_list = []
    for tile in tile_list:
        args_list.append([path, tile, year_list, stack])
    concurrent_execute(calculate_coverage_by_tile, args_list, pool_size)
    if merge:
        coverage_file_list = [os.path.join(path.estimate_coverage_path, tile, f"coverage_ta_{tile}.tif") for tile in tile_list]
        coverage_file = os.path.join(path.estimate_coverage_path, region, f"coverage_ta_{region}.tif")
        record_file = os.path.join(path.cloud_estimate_coverage_path, "coverage_record_ta.csv")
        merge_coverage(coverage_file_list, coverage_file, record_file, region)


def mian():
    path = Path()
    tile_list = get_world_tile(path)
    year_list = list(range(2020, 2024))
    calculate_coverage(path, tile_list, year_list, True, True, "world", 8)


if __name__ == "__main__":
    mian()
