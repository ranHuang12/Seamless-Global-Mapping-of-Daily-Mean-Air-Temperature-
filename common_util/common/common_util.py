import os
from multiprocessing import Manager, Process
from multiprocessing.pool import Pool

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from common_object.entity import BasePath


def convert_enum_to_value(enum_list):
    return [enum.value for enum in enum_list]


def convert_to_list(element):
    return [element] if not isinstance(element, list) else element


def build_modeling_x_list(view_list, qc_mode, auxiliary_list):
    modeling_x_list = []
    for view in view_list:
        modeling_x_list.append(f"{view.view_name}_{qc_mode.field}")
        if "ANGLE" in auxiliary_list:
            modeling_x_list.append(f"{view.view_name}_ANGLE")
    modeling_x_list.extend(auxiliary_list)
    if "ANGLE" in auxiliary_list:
        modeling_x_list.remove("ANGLE")
    return modeling_x_list


def get_world_tile(path: BasePath, inland=None, vi=None, pixel_limit=0):
    tile_df = pd.read_csv(os.path.join(path.cloud_modis_data_path, "land_tile_list.csv"))
    if inland is not None:
        if inland:
            tile_df = tile_df[tile_df["inland"] == 1]
        else:
            tile_df = tile_df[tile_df["inland"] != 1]
    if vi is not None:
        if vi:
            tile_df = tile_df[tile_df["vi"] == 1]
        else:
            tile_df = tile_df[tile_df["vi"] != 1]
    tile_df = tile_df[tile_df["count"] >= pixel_limit]
    return list(tile_df["tile"].values)


def exclude_from_csv(value_list, csv_file, field):
    value_df = pd.read_csv(csv_file)
    value_df = value_df[value_df[field].notnull()]
    return list(np.setdiff1d(np.array(value_list), value_df[field].values))


def exclude_finished_tile(tile_list, field, finish_csv, finish_part_csv=None):
    if finish_part_csv is not None and os.path.isfile(finish_part_csv):
        return exclude_from_csv(tile_list, finish_part_csv, "tile")
    elif os.path.isfile(finish_csv):
        if str(field) in pd.read_csv(finish_csv).columns:
            return exclude_from_csv(tile_list, finish_csv, "tile")
    return tile_list


def check_from_csv(value, value_csv, value_field, refer_field=None):
    if os.path.isfile(value_csv):
        value_df = pd.read_csv(value_csv)
        value_field = str(value_field)
        if value_field in value_df.columns:
            if refer_field is not None and refer_field in value_df.columns:
                value_df = value_df[value_df[refer_field].notnull()]
            return value not in value_df[value_field].values
    return True


def check_finished_tile(tile, field, finish_csv, finish_part_csv=""):
    if not check_from_csv(tile, finish_part_csv, "tile"):
        return False
    return check_from_csv(tile, finish_csv, "tile", field)


def concurrent_execute(func, args_list, pool_size=1, use_lock=True):
    pool = Pool(pool_size, )
    lock = Manager().Lock()
    results = None
    for args in args_list:
        if pool_size == 1:
            func(*args) if isinstance(args, list) else func(**args)
        else:
            if use_lock:
                if isinstance(args, list):
                    args.append(lock)
                else:
                    args["lock"] = lock
            results = pool.apply_async(func, args) if isinstance(args, list) else pool.apply_async(func, kwds=args)
    pool.close()
    pool.join()
    try:
        if results is not None:
            results.get()
    except Exception as e:
        print(e)


def concurrent_execute_using_process(func, args_list, use_lock=True):
    if len(args_list) == 1:
        args = args_list[0]
        func(*args) if isinstance(args, list) else func(**args)
    else:
        lock = Manager().Lock()
        process_list = []
        for args in args_list:
            if use_lock:
                if isinstance(args, list):
                    args.append(lock)
                else:
                    args["lock"] = lock
            process_list.append(Process(target=func, args=tuple(args)) if isinstance(args, list) else Process(target=func, kwargs=args))
        for process in process_list:
            process.start()
        for process in process_list:
            process.join()


def main():
    pass


if __name__ == "__main__":
    main()
