import os
import sys
import numpy as np
import pandas as pd
from enum import Enum
import time
from osgeo import gdal, gdalconst, ogr
#from common_object.enum import ViewEnum, NodataEnum, QcModeEnum
#from common_util.common import convert_enum_to_value, get_world_tile
#from common_util.document import to_csv
#from common_util.image import read_hdf, create_raster, read_raster, mosaic, shp_clip_tif
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

def convert_enum_to_value(enum_list):
    return [enum.value for enum in enum_list]


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


def create_path(path):
    if not os.path.exists(path):
        os.makedirs(path)


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


def convert_to_list(element):
    return [element] if not isinstance(element, list) else element


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


def create_raster(output_file, arr, geo_data, nodata, output_type=gdal.GDT_Int16):
    np.nan_to_num(arr, nan=nodata)            # 将数组中的 NaN 值替换为指定的无数据值 nodat
    driver = gdal.GetDriverByName('GTiff')    # 获取并注册 GTiff 驱动：
    driver.Register()                         # 获取数组的高度和宽度
    h, w = np.shape(arr)
    oDS = driver.Create(output_file, w, h, 1, output_type, ['COMPRESS=LZW', 'BIGTIFF=YES'])  # 创建一个新的栅格文件，使用 LZW 压缩和支持大文件
    out_band1 = oDS.GetRasterBand(1)  # 获取栅格数据集的第一个波段
    for i in range(h):                           # 按行写入数组数据
        out_band1.WriteArray(arr[i].reshape(1, -1), 0, i)
    oDS.SetProjection(geo_data.projection)      # 设置投影和地理变换信息
    oDS.SetGeoTransform(geo_data.transform)
    out_band1.FlushCache()                      # 刷新缓存并设置无数据值
    out_band1.SetNoDataValue(nodata)


def read_raster(file, get_arr=True, scale_factor=0, arr_type=None):
    ds = gdal.Open(file)                    # 打开栅格数据文件，返回数据集对象 ds
    proj = ds.GetProjection()               # 获取投影信息 proj
    transform = ds.GetGeoTransform()        # 地理变换信息 transform
    geo_data = GeoData(proj, transform)     # 创建 GeoData 对象 geo_data 来存储这些信息
    if get_arr:
        arr = ds.GetRasterBand(1).ReadAsArray()  # 读取第一个波段的数据并转换为数组 arr
        if scale_factor != 0:                    # scale_factor（不为 0），对数组进行缩放
            arr *= scale_factor
        if arr_type is not None:
            arr = arr.astype(arr_type)           #　将数组的数据类型转换为 arr_type
        return arr, geo_data
    return ds, geo_data


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


def shp_clip_tif(tif_file, shp_file, dst_file, crop_to_cutline=True):
    gdal.Warp(dst_file, tif_file, cutlineDSName=shp_file, cropToCutline=crop_to_cutline)



modis_data_path = r"G:\MODISData"

mask_path = r'E:\LST\auxiliary_data\mask'

lst_coverage_path = r'E:\zx\All_data\lst_coverage'


import os
import sys
import numpy as np
import pandas as pd
from enum import Enum
import time
from osgeo import gdal, gdalconst, ogr
#from common_object.enum import ViewEnum, NodataEnum, QcModeEnum
#from common_util.common import convert_enum_to_value, get_world_tile
#from common_util.document import to_csv
#from common_util.image import read_hdf, create_raster, read_raster, mosaic, shp_clip_tif
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

def convert_enum_to_value(enum_list):
    return [enum.value for enum in enum_list]


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


def create_path(path):
    if not os.path.exists(path):
        os.makedirs(path)


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


def convert_to_list(element):
    return [element] if not isinstance(element, list) else element


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


def create_raster(output_file, arr, geo_data, nodata, output_type=gdal.GDT_Int16):
    np.nan_to_num(arr, nan=nodata)            # 将数组中的 NaN 值替换为指定的无数据值 nodat
    driver = gdal.GetDriverByName('GTiff')    # 获取并注册 GTiff 驱动：
    driver.Register()                         # 获取数组的高度和宽度
    h, w = np.shape(arr)
    oDS = driver.Create(output_file, w, h, 1, output_type, ['COMPRESS=LZW', 'BIGTIFF=YES'])  # 创建一个新的栅格文件，使用 LZW 压缩和支持大文件
    out_band1 = oDS.GetRasterBand(1)  # 获取栅格数据集的第一个波段
    for i in range(h):                           # 按行写入数组数据
        out_band1.WriteArray(arr[i].reshape(1, -1), 0, i)
    oDS.SetProjection(geo_data.projection)      # 设置投影和地理变换信息
    oDS.SetGeoTransform(geo_data.transform)
    out_band1.FlushCache()                      # 刷新缓存并设置无数据值
    out_band1.SetNoDataValue(nodata)


def read_raster(file, get_arr=True, scale_factor=0, arr_type=None):
    ds = gdal.Open(file)                    # 打开栅格数据文件，返回数据集对象 ds
    proj = ds.GetProjection()               # 获取投影信息 proj
    transform = ds.GetGeoTransform()        # 地理变换信息 transform
    geo_data = GeoData(proj, transform)     # 创建 GeoData 对象 geo_data 来存储这些信息
    if get_arr:
        arr = ds.GetRasterBand(1).ReadAsArray()  # 读取第一个波段的数据并转换为数组 arr
        if scale_factor != 0:                    # scale_factor（不为 0），对数组进行缩放
            arr *= scale_factor
        if arr_type is not None:
            arr = arr.astype(arr_type)           #　将数组的数据类型转换为 arr_type
        return arr, geo_data
    return ds, geo_data


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


def shp_clip_tif(tif_file, shp_file, dst_file, crop_to_cutline=True):
    gdal.Warp(dst_file, tif_file, cutlineDSName=shp_file, cropToCutline=crop_to_cutline)



modis_data_path = r'G:\MODISData'

mask_path = r'H:\zx\full mask'

lst_coverage_path = r'E:\zx\All_data\lst_coverage'

longitude_path  = r'E:\zx\All_data\longitude'


def create_full_cover_mask(tile, fill_value=1):
    mask_file = os.path.join(mask_path, f"mask_{tile}.tif")
    if os.path.isfile(mask_file):
        return
    refer_arr = None
    geo_data = None
    for product in ["MOD11A1", "MYD11A1", "MOD13A2", "MYD13A2"]:
        product_path = os.path.join(modis_data_path, product, tile)
        filename_list = os.listdir(product_path)
        if os.path.exists(product_path) and len(filename_list) != 0:
            refer_arr, geo_data = read_hdf(os.path.join(product_path, filename_list[0]), 0)
            break
    mask_arr = np.full_like(refer_arr, fill_value)
    create_raster(mask_file, mask_arr, geo_data, NodataEnum.MASK.value)
    print(f"{tile} {mask_arr[mask_arr != NodataEnum.MASK.value].size}")


def create_mask_from_polygon(region, tile_list, shp_file=None, crop_to_cutline=True):
    mask_file_list = [os.path.join(mask_path, f"mask_{tile}.tif") for tile in tile_list]
    mask_file = os.path.join(mask_path, f"mask{'_'.join(tile for tile in tile_list)}.tif")
    nodata = NodataEnum.MASK.value
    mosaic(mask_file_list, mask_file, nodata, nodata)
    if shp_file is not None:
        shp_clip_tif(mask_file, shp_file, os.path.join(mask_path, f"mask_{region}.tif"), crop_to_cutline)


def create_mask_from_coverage(tile):
    mask_file = os.path.join(mask_path, f"mask_{tile}.tif")
    qc_mode_name = QcModeEnum.ALL.value.name
    mask_arr = None
    geo_data = None
    for view in convert_enum_to_value(ViewEnum):
        coverage_file = os.path.join(lst_coverage_path, tile, f"coverage_{tile}_{view.view_name}_{qc_mode_name}.tif")
        coverage_arr, geo_data = read_raster(coverage_file)
        if mask_arr is None:
            mask_arr = np.zeros_like(coverage_arr)
        mask_arr[coverage_arr != NodataEnum.COVERAGE.value] = 1
    count = mask_arr[mask_arr != NodataEnum.MASK.value].size
    create_raster(mask_file, mask_arr, geo_data, NodataEnum.MASK.value)
    to_csv(pd.DataFrame({"tile": [tile], "count": [count]}), os.path.join(mask_path, "pixel_count.csv"))
    print(f"{tile} {count}")


def create_subzone_mask(tile, row_count, column_count):
    mask_arr, geo_data = read_raster(os.path.join(mask_path, f"mask_{tile}.tif"))
    lon_arr = read_raster(os.path.join(longitude_path, f"lon_{tile}.tif"))[0]
    sub_mask_arr_list = np.array_split(mask_arr, row_count)
    sub_lon_arr_list = np.array_split(lon_arr, row_count)
    for row, sub_mask_arr in enumerate(sub_mask_arr_list):
        sub_lon_arr = sub_lon_arr_list[row]
        sub_lon_value_arr = sub_lon_arr[sub_mask_arr != NodataEnum.MASK.value]
        min_lon = np.min(sub_lon_value_arr)
        max_lon = np.max(sub_lon_value_arr)
        lon_interval = (max_lon - min_lon) // column_count
        for column in range(column_count):
            sub_mask_arr[(sub_lon_arr > min_lon + column * lon_interval) & (sub_mask_arr != NodataEnum.MASK.value)] = row * column_count + column + 1
    subzone_mask_arr = np.vstack(sub_mask_arr_list)
    create_raster(os.path.join(mask_path, f"subzone_mask_{tile}.tif"), subzone_mask_arr, geo_data, NodataEnum.MASK.value)


def create_mask(tile_list):
    for tile in tile_list:
        #create_mask_from_coverage(tile)
        create_full_cover_mask(tile,fill_value=1)



def main():
   # path = Path()
   #tile_list = ['h01v07', 'h01v08', 'h01v09', 'h02v06', 'h03v09', 'h05v10', 'h16v14', 'h17v15', 'h31v06', 'h33v07', 'h34v07']
   tile_list = get_world_tile()
   create_mask(tile_list)


if __name__ == "__main__":
    main()
