import os.path
import numpy as np
import pandas as pd
from enum import Enum
from multiprocessing import Manager, Process
from multiprocessing.pool import Pool
import calendar
import sys
import time
from osgeo import gdal, gdalconst, ogr
from datetime import datetime, timedelta, date


#from common_object.enum import ViewEnum, NodataEnum, LayerEnum, QcModeEnum
#from common_util.common import convert_to_list, get_world_tile, exclude_finished_tile, concurrent_execute_using_pool, \
   # convert_enum_to_value
#from common_util.date import get_all_date_by_year
#from common_util.document import to_csv, merge_csv
#from common_util.image import create_raster, read_hdf, read_raster
#from common_util.path import create_path
#from data_perprocessing.entity import Path


class LayerEnum(Enum):
    # LST
    LST_DAY = 0
    LST_QC_DAY = 1
    LST_DAY_VIEW_TIME = 2
    LST_DAY_VIEW_ANGLE = 3
    LST_NIGHT = 4
    LST_QC_NIGHT = 5
    LST_NIGHT_VIEW_TIME = 6
    LST_NIGHT_VIEW_ANGLE = 7

    # Vegetation Index
    NDVI = 0
    EVI = 1

class View(object):
    def __init__(self, view_name=None, satellite_name=None, lst_product=None, lst_8day_product=None,
                 lst_layer=None, qc_layer=None, view_time_layer=None, view_angle_layer=None):
        self.view_name = view_name
        self.satellite_name = satellite_name

        self.lst_product = lst_product
        self.lst_8day_product = lst_8day_product

        self.lst_layer = lst_layer
        self.qc_layer = qc_layer
        self.view_time_layer = view_time_layer
        self.view_angle_layer = view_angle_layer


class ViewEnum(Enum):
    TD = View(view_name="TD",
              satellite_name="TERRA",
              lst_product="MOD11A1",
              lst_8day_product="MOD11A2",
              lst_layer=LayerEnum.LST_DAY.value,
              qc_layer=LayerEnum.LST_QC_DAY.value,
              view_time_layer=LayerEnum.LST_DAY_VIEW_TIME.value,
              view_angle_layer=LayerEnum.LST_DAY_VIEW_ANGLE.value)
    TN = View(view_name="TN",
              satellite_name="TERRA",
              lst_product="MOD11A1",
              lst_8day_product="MOD11A2",
              lst_layer=LayerEnum.LST_NIGHT.value,
              qc_layer=LayerEnum.LST_QC_NIGHT.value,
              view_time_layer=LayerEnum.LST_NIGHT_VIEW_TIME.value,
              view_angle_layer=LayerEnum.LST_NIGHT_VIEW_ANGLE.value)
    AD = View(view_name="AD",
              satellite_name="AQUA",
              lst_product="MYD11A1",
              lst_8day_product="MYD11A2",
              lst_layer=LayerEnum.LST_DAY.value,
              qc_layer=LayerEnum.LST_QC_DAY.value,
              view_time_layer=LayerEnum.LST_DAY_VIEW_TIME.value,
              view_angle_layer=LayerEnum.LST_DAY_VIEW_ANGLE.value)
    AN = View(view_name="AN",
              satellite_name="AQUA",
              lst_product="MYD11A1",
              lst_8day_product="MYD11A2",
              lst_layer=LayerEnum.LST_NIGHT.value,
              qc_layer=LayerEnum.LST_QC_NIGHT.value,
              view_time_layer=LayerEnum.LST_NIGHT_VIEW_TIME.value,
              view_angle_layer=LayerEnum.LST_NIGHT_VIEW_ANGLE.value)


class NodataEnum(Enum):
    MODIS_LST = 0
    LST = 255
    VIEW_TIME = 255
    VIEW_ANGLE = 255
    VEGETATION_INDEX = -3000
    TEMPERATURE = 32767

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

class QcMode(object):
    name: str = ""
    field: str = ""

    def __init__(self, name="", field=""):
        self.name = name
        self.field = field


class QcModeEnum(Enum):
    GOOD_QUALITY = QcMode("goodquality", "GQ")
    OTHER_QUALITY = QcMode("orderquality", "OQ")
    ALL = QcMode("all", "ALL")


def convert_to_list(element):         #　输入元素转换为列表
    return [element] if not isinstance(element, list) else element


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


def exclude_from_csv(value_list, csv_file, field):
    value_df = pd.read_csv(csv_file)
    value_df = value_df[value_df[field].notnull()]
    return list(np.setdiff1d(np.array(value_list), value_df[field].values))


def exclude_finished_tile(tile_list, field, finish_csv, finish_part_csv=None):  # 从瓦片列表中排除已完成的瓦片，以便在处理数据时只关注未完成的部分
    if finish_part_csv is not None and os.path.isfile(finish_part_csv):
        return exclude_from_csv(tile_list, finish_part_csv, "tile")
    elif os.path.isfile(finish_csv):
        if str(field) in pd.read_csv(finish_csv).columns:
            return exclude_from_csv(tile_list, finish_csv, "tile")
    return tile_list


def concurrent_execute_using_pool(func, args_list, pool_size=1, use_lock=True):
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
        results.get()
    except Exception as e:
        print(e)


def convert_enum_to_value(enum_list):
    return [enum.value for enum in enum_list]

def get_day_num_by_year(year):
    return 366 if calendar.isleap(year) else 365


def get_all_date_by_year(year, start_doy=1, end_doy=366):
    year = int(year)
    start_doy = int(start_doy)
    end_doy = int(end_doy)
    return [year * 1000 + doy for doy in range(start_doy, min(get_day_num_by_year(year), end_doy) + 1)]


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


def merge_csv(csv1, csv2, on=None, how="inner", output_file=None, along_column=True):
    df1 = csv1 if isinstance(csv1, pd.DataFrame) else (pd.read_csv(csv1) if os.path.isfile(csv1) else None)
    df2 = csv2 if isinstance(csv2, pd.DataFrame) else (pd.read_csv(csv2) if os.path.isfile(csv2) else None)
    if df1 is not None and df2 is not None:
        output_df = df1.merge(df2, how, on) if along_column else pd.concat([df1, df2], ignore_index=True)
    elif df1 is not None:
        output_df = df1
    elif df2 is not None:
        output_df = df2
    else:
        output_df = None
    if output_df is not None:
        to_csv(output_df, csv1 if output_file is None else output_file, False)

def create_raster(output_file, arr, geo_data, nodata, output_type=gdal.GDT_Int16):
    np.nan_to_num(arr, nan=nodata)
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    h, w = np.shape(arr)
    oDS = driver.Create(output_file, w, h, 1, output_type, ['COMPRESS=LZW', 'BIGTIFF=YES'])
    out_band1 = oDS.GetRasterBand(1)
    for i in range(h):
        out_band1.WriteArray(arr[i].reshape(1, -1), 0, i)
    oDS.SetProjection(geo_data.projection)
    oDS.SetGeoTransform(geo_data.transform)
    out_band1.FlushCache()
    out_band1.SetNoDataValue(nodata)


class GeoData(object):
    def __init__(self, projection, transform):
        self.projection = projection
        self.transform = transform


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



modis_data_path = r"G:\MODISData"         # 输入路径
#lst_path = r'E:\LST\lst'
lst_path = r'E:\hjf\dongbei_MODIS\tif\h27v05'
mask_path = r'E:\zx\All_data\mask'
auxiliary_data_path = r'E:\LST\auxiliary_data'

def convert_lst_hdf_to_tif( product, tile, year, lock):
    if product == "MOD11A1":
        view_list = [ViewEnum.TD.value, ViewEnum.TN.value]
    else:
        view_list = [ViewEnum.AD.value, ViewEnum.AN.value]
    layer_list = []
    for view in view_list:
        create_path(os.path.join(lst_path, f"{view.view_name}_{QcModeEnum.ALL.value.name}", tile))
        create_path(os.path.join(lst_path, f"{view.view_name}_{QcModeEnum.GOOD_QUALITY.value.name}", tile))
        create_path(os.path.join(lst_path, f"{view.view_name}_angle", tile))
        layer_list.append(view.lst_layer)
        layer_list.append(view.qc_layer)
        layer_list.append(view.view_angle_layer)
    type_list = [np.float32, np.int32, np.int32, np.float32, np.int32, np.int32]
    lst_hdf_path = os.path.join(modis_data_path, product, tile)     # modis_data_path是放下载的的modis lst产品数据的
    count_dict = {view_list[0].view_name: 0, view_list[1].view_name: 0}
    for filename in os.listdir(lst_hdf_path):
        date = filename.split('.')[1][1:]
        if int(date) // 1000 != year:
            continue
        if os.path.isfile(os.path.join(lst_path, f"{view_list[1].view_name}_angle", tile, f"{view_list[1].view_name}_{tile}_angle_{date}.tif")):
            count_dict[view_list[1].view_name] += 1
            if os.path.isfile(os.path.join(lst_path, f"{view_list[0].view_name}_angle", tile, f"{view_list[0].view_name}_{tile}_angle_{date}.tif")):
                count_dict[view_list[0].view_name] += 1
            continue
        try:
            arr_dict, geo_data = read_hdf(os.path.join(lst_hdf_path, filename), layer_list, type_list)
            for view in view_list:
                lst_arr = arr_dict[view.lst_layer]
                if lst_arr[lst_arr != NodataEnum.MODIS_LST.value].size == 0:
                    continue
                for qc_mode in [QcModeEnum.ALL.value, QcModeEnum.GOOD_QUALITY.value]:
                    if qc_mode == QcModeEnum.GOOD_QUALITY.value:
                        lst_arr[arr_dict[view.qc_layer] != 0] = NodataEnum.MODIS_LST.value
                    if lst_arr[lst_arr != NodataEnum.MODIS_LST.value].size > 0:
                        lst_copy_arr = np.copy(lst_arr)
                        lst_copy_arr = (lst_copy_arr * 0.02 - 273.15) * 100
                        lst_copy_arr[lst_arr == NodataEnum.MODIS_LST.value] = NodataEnum.TEMPERATURE.value
                        create_raster(os.path.join(lst_path, f"{view.view_name}_{qc_mode.name}", tile, f"{view.view_name}_{tile}_{qc_mode.name}_{date}.tif"), lst_copy_arr, geo_data, NodataEnum.TEMPERATURE.value)
                view_angle_arr = arr_dict[view.view_angle_layer]
                if view_angle_arr[view_angle_arr != NodataEnum.VIEW_ANGLE.value].size > 0:
                    view_angle_copy_arr = np.copy(view_angle_arr)
                    view_angle_copy_arr -= 65
                    view_angle_copy_arr[view_angle_arr == NodataEnum.VIEW_ANGLE.value] = NodataEnum.VIEW_ANGLE.value
                    create_raster(os.path.join(lst_path, f"{view.view_name}_angle", tile, f"{view.view_name}_{tile}_angle_{date}.tif"), view_angle_copy_arr, geo_data, NodataEnum.VIEW_ANGLE.value)
                count_dict[view.view_name] += 1
        except Exception as e:
            print(e)
    record_df = pd.DataFrame({"tile": [tile], f"{year}_{view_list[0].view_name}": [count_dict[view_list[0].view_name]], f"{year}_{view_list[1].view_name}": [count_dict[view_list[1].view_name]]})
    to_csv(record_df, os.path.join(modis_data_path, f"finish_{product}_{year}.csv"), lock=lock)
    print(f"{tile} {count_dict}")


def generate_empty_file(tile_list, year_list):
    nodata_dict = {QcModeEnum.ALL.value.name: NodataEnum.TEMPERATURE.value, "time": NodataEnum.VIEW_TIME.value,
                   "angle": NodataEnum.VIEW_ANGLE.value}
    for tile in tile_list:
        mask_arr, geo_data = read_raster(os.path.join(mask_path, f"mask_{tile}.tif"))
        for view in convert_enum_to_value(ViewEnum):
            for field in [QcModeEnum.ALL.value.name, "time", "angle"]:
                value_path = os.path.join(lst_path, f"{view.view_name}_{field}", tile)
                empty_file_list = []
                for year in year_list:
                    for date in get_all_date_by_year(year):
                        value_file = os.path.join(value_path, f"{view.view_name}_{tile}_{field}_{date}.tif")
                        if not os.path.isfile(value_file):
                            value_arr = np.full_like(mask_arr, nodata_dict[field])
                            create_raster(value_file, value_arr, geo_data, nodata_dict[field])
                            empty_file_list.append(value_file)
                to_csv(pd.DataFrame({"empty_file": empty_file_list}), os.path.join(value_path, "empty_file.csv"), False)


def convert_vi_hdf_to_tif(product, tile, year, lock):
    for vi in ["ndvi", "evi"]:
        create_path(os.path.join(auxiliary_data_path, vi, "raw", tile))
    layer_list = [LayerEnum.NDVI.value, LayerEnum.EVI.value]
    type_list = [np.float32, np.float32]
    vi_hdf_path = os.path.join(modis_data_path, product, tile)  # 存放关于植被指数的产品数据
    count = 0
    for filename in os.listdir(vi_hdf_path):
        date = filename.split('.')[1][1:]
        if int(int(date)/1000) != year:
            continue
        if os.path.isfile(os.path.join(auxiliary_data_path, "evi", "raw", tile, f"evi_{tile}_{date}.tif")):
            count += 1
            continue
        try:
            arr_dict, geo_data = read_hdf(os.path.join(vi_hdf_path, filename), layer_list, type_list)
            not_empty = False
            for index, vi in enumerate(["ndvi", "evi"]):
                vi_arr = arr_dict[layer_list[index]]
                if vi_arr[vi_arr != NodataEnum.VEGETATION_INDEX.value].size == 0:
                    continue
                create_raster(os.path.join(auxiliary_data_path, vi, "raw", tile, f"{vi}_{tile}_{date}.tif"), vi_arr, geo_data, NodataEnum.VEGETATION_INDEX.value)
                not_empty = True
            if not_empty:
                count += 1
        except Exception as e:
            print(e)
    to_csv(pd.DataFrame({"tile": [tile], year: [count]}), os.path.join(modis_data_path, f"finish_{product}_{year}.csv"), lock=lock)
    print(f"{product} {tile} {year} {count}")


def convert_lc_hdf_to_tif(product, classification, tile, year_list):    # 这个lc hdf 是什么数据？？
    lc_path = os.path.join(auxiliary_data_path, classification, tile)
    create_path(lc_path)
    layer = getattr(LayerEnum, classification).value
    arr_type = np.int8
    lc_hdf_path = os.path.join(modis_data_path, product, tile)
    count = 0
    for filename in os.listdir(lc_hdf_path):
        year = filename.split('.')[1][1:5]
        if year in year_list:
            continue
        lc_file = os.path.join(lc_path, f"{classification}_{tile}_{year}.tif")
        if os.path.isfile(lc_file):
            count += 1
            continue
        try:
            lc_arr, geo_data = read_hdf(os.path.join(lc_hdf_path, filename), layer, arr_type)
            if lc_arr[lc_arr != NodataEnum.LAND_COVER.value].size == 0:
                continue
            create_raster(lc_file, lc_arr, geo_data, NodataEnum.LAND_COVER.value)
        except Exception as e:
            print(e)
    to_csv(pd.DataFrame({"tile": [tile], "count": [count]}), os.path.join(modis_data_path, f"finish_{product}.csv"))
    print(f"{product} {tile} {count}")


def convert_hdf_to_tif(product_list, tile_list, year_list, pool_size=1):
    product_list = convert_to_list(product_list)
    tile_list = convert_to_list(tile_list)
    year_list = convert_to_list(year_list)
    for product in product_list:
        finish_csv = os.path.join(modis_data_path, f"finish_{product}.csv")
        if product == "MCD13Q1":
            for tile in exclude_finished_tile(tile_list, "count", finish_csv):
                convert_lc_hdf_to_tif(product, "IGBP", tile, year_list)
        else:
            for year in year_list:
                finish_year_csv = os.path.join(modis_data_path, f"finish_{product}_{year}.csv")
                args_list = []
                for tile in exclude_finished_tile(tile_list, year, finish_csv, finish_year_csv):
                    args_list.append([product, tile, year])
                concurrent_execute_using_pool(convert_lst_hdf_to_tif if product in ["MOD11A1", "MYD11A1"] else convert_vi_hdf_to_tif, args_list, pool_size)
                merge_csv(finish_csv, finish_year_csv, "tile", "outer")
                os.remove(finish_year_csv)


def main():
    #path = Path()
    product_list = ["MOD11A1",'MYD11A1']
    #tile_list = get_world_tile()
    tile_list = ['h27v05']
    year_list = list(range(2000, 2022))
    convert_hdf_to_tif(product_list, tile_list, year_list, pool_size=8)


if __name__ == "__main__":
    main()
