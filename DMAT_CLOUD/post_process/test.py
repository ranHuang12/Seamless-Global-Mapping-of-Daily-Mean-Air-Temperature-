import os.path
import sys
import time
import numpy as np
import pandas as pd
from enum import Enum
from osgeo import gdal, gdalconst, ogr
import os.path

#from common_object.enum import NodataEnum
#from common_util.common import get_world_tile
from common_util.date import get_date_interval
#from common_util.document import to_csv
#from common_util.image import read_raster
#from common_util.path import create_path
#from ta_estimate.post_process import merge_ta
#from ta_interpolate.entity import Path


def read_hdf(file, layer_list, type_list=None):
    layer_list = convert_to_list(layer_list)
    sub_datasets = gdal.Open(file).GetSubDatasets()
    first_ds = gdal.Open(sub_datasets[0][0])
    proj = first_ds.GetProjection()
    trans = first_ds.GetGeoTransform()
    geo_data = GeoData(proj, trans)
    arr_dict = {}
    if type_list is None:
        type_list = [np.float32 for _ in layer_list]
    else:
        type_list = convert_to_list(type_list)
    for index, layer in enumerate(layer_list):
        arr_dict[layer] = gdal.Open(sub_datasets[layer][0]).ReadAsArray().astype(type_list[index])
    if len(layer_list) == 1:
        return arr_dict[layer_list[0]], geo_data
    return arr_dict, geo_data


def convert_to_list(element):
    return [element] if not isinstance(element, list) else element

def mosaic(src_file_list, dst_file, src_nodata, dst_nodata, output_type=gdalconst.GDT_Int16, layer=0, dstSRS=None):
    if len(src_file_list) <= 1:
        return
    src_ds_list = []
    for src_file in src_file_list:
        if src_file.endswith(".hdf"):
            src_ds_list.append(read_hdf(src_file, layer)[0])
        else:
            src_ds_list.append(read_raster(src_file, False)[0])
    gdal.Warp(dst_file, src_ds_list, srcNodata=src_nodata, dstNodata=dst_nodata, dstSRS=dstSRS, outputType=output_type, creationOptions=['COMPRESS=LZW'])
    print(dst_file)



def get_world_tile(inland=None, vi=None, pixel_limit=0):
    tile_df = pd.read_csv(os.path.join(modis_data_path, "land_tile_list.csv"))
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

def merge_ta(ta_file_list, ta_file, record_file, field, date):
    create_path(os.path.dirname(ta_file))
    mosaic(ta_file_list, ta_file, NodataEnum.TEMPERATURE.value, NodataEnum.TEMPERATURE.value)
    ta_arr = read_raster(ta_file)[0]
    ta_value_arr = ta_arr[ta_arr != NodataEnum.TEMPERATURE.value]
    record_dict = {field: [date], "sum": [ta_value_arr.size], "min_ta": [np.min(ta_value_arr) / 100],
                   "avg_ta": [np.average(ta_value_arr) / 100], "max_ta": [np.max(ta_value_arr) / 100]}
    to_csv(pd.DataFrame(record_dict), record_file)
    print(record_dict)


def to_csv(df, csv_file, append=True, lock=None):
    create_path(os.path.dirname(csv_file))
    if sys.platform.startswith("linux"):
        return __to_csv_for_linux(df, csv_file, append)
    while True:
        try:
            if lock is not None:
                lock.acquire()
            if append and os.path.isfile(csv_file):
                df.to_csv(csv_file, mode="a", index=False, header=False, encoding="utf-8")
            else:
                df.to_csv(csv_file, index=False, encoding="utf-8")
            return True
        except Exception as e:
            print(e)
            time.sleep(1)
        finally:
            if lock is not None:
                lock.release()


def __to_csv_for_linux(df, csv_file, append=True):
    import fcntl
    while True:
        with open(csv_file, "a") as file:
            try:
                fcntl.flock(file, fcntl.LOCK_EX)
                if append and os.path.getsize(csv_file) != 0:
                    df.to_csv(csv_file, mode="a", index=False, header=False)
                else:
                    df.to_csv(csv_file, index=False)
                return True
            except Exception as e:
                print(e)
                time.sleep(1)
            finally:
                fcntl.flock(file, fcntl.LOCK_UN)

class NodataEnum(Enum):
    MODIS_LST = 0
    LST = 255
    VIEW_TIME = 255
    VIEW_ANGLE = 255
    VEGETATION_INDEX = -3000
    TEMPERATURE = 32767
    LAND_COVER = 255

    GVE_DEM = 9998
    GVE_WATER = -9999
    GMTED_DEM = -32768
    DEM = 32767
    LATITUDE_LONGITUDE = 32767
    MASK = 0
    STATION = 0
    XY_INDEX = 1200
    CLIMATE = 0

    DATE = 0

    COVERAGE = 0

class GeoData(object):
    def __init__(self, projection, transform):
        self.projection = projection
        self.transform = transform


def read_raster(file, get_arr=True, scale_factor=0, arr_type=None):
    ds = gdal.Open(file)
    proj = ds.GetProjection()
    transform = ds.GetGeoTransform()
    geo_data = GeoData(proj, transform)
    if get_arr:
        arr = ds.GetRasterBand(1).ReadAsArray()
        if scale_factor != 0:
            arr *= scale_factor
        if arr_type is not None:
            arr = arr.astype(arr_type)
        return arr, geo_data
    return ds, geo_data


def create_path(path):
    if not os.path.exists(path):
        os.makedirs(path)







def merge_daily_ta(path: Path, tile_list, date, region="world"):
    region_ta_path = os.path.join(path.interpolate_ta_path, "world")
    ta_file_list = [os.path.join(path.interpolate_ta_path, tile, f"ta_{tile}_{date}.tif") for tile in tile_list]
    ta_file = os.path.join(region_ta_path, f"ta_{region}_{date}.tif")
    record_file = os.path.join(path.cloud_interpolate_record_path, f"interpolate_ta_record_{region}.csv")
    merge_ta(ta_file_list, ta_file, record_file, "date", date)



def main()
    tile_list = get_world_tile()
    for date in [2022099, 2022285, 2022101, 2022102]:
        merge_daily_ta(tile_list, date)



if __name__ == "__main__":
    main()
