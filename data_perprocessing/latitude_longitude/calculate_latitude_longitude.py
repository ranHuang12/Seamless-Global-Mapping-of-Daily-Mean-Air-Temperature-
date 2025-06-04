import os

import numpy as np
import pandas as pd
from dbfread import DBF
from osgeo import osr

from common_object.entity import BasePath
from common_object.enum import NodataEnum, SRSEnum
from common_util.common import convert_to_list, get_world_tile
from common_util.image import read_raster, create_raster, mosaic
from common_util.path import create_path


def position_shp_to_tif(shp_df, mask_file, position_file, is_lon):
    mask_arr, geo_data = read_raster(mask_file)
    position_arr = np.zeros_like(mask_arr).astype(dtype=np.float32)
    field = "POINT_X" if is_lon else "POINT_Y"
    lon_arr_1d = np.array(shp_df[field], dtype=np.float32)
    position_arr[mask_arr != 0] = lon_arr_1d
    create_raster(position_file, position_arr, geo_data, 0)


def create_position(mask_path, shp_path, position_path, region_list, merge):
    if isinstance(region_list, str):
        region_list = [region_list]
    create_path(position_path)
    lon_file_list = []
    lat_file_list = []
    for region in region_list:
        shp_file = os.path.join(shp_path, f"{region}.shp")
        mask_file = os.path.join(mask_path, f"{region}_mask.tif")
        lon_file = os.path.join(position_path, f"{region}_lon.tif")
        lat_file = os.path.join(position_path, f"{region}_lat.tif")
        if os.path.isfile(lon_file) and os.path.isfile(lat_file):
            continue
        dbf_file = shp_file.replace('.shp', '.dbf')
        dbf = DBF(dbf_file, encoding='gbk')
        shp_df = pd.DataFrame(iter(dbf))
        position_shp_to_tif(shp_df, mask_file, lon_file, True)
        lon_file_list.append(lon_file)
        position_shp_to_tif(shp_df, mask_file, lat_file, False)
        lat_file_list.append(lat_file)
    if merge:
        src_nodata = dst_nodata = NodataEnum.LATITUDE_LONGITUDE.value
        lon_file_merged = os.path.join(position_path, "China_lon.tif")
        mosaic(lon_file_list, lon_file_merged, src_nodata, dst_nodata)
        lat_file_merged = os.path.join(position_path, "China_lat.tif")
        mosaic(lat_file_list, lat_file_merged, src_nodata, dst_nodata)


def calculate_latitude_longitude_from_mask(path: BasePath, tile_list):
    tile_list = convert_to_list(tile_list)
    for tile in tile_list:
        mask_file = os.path.join(path.cloud_mask_path, f"{tile}_mask.tif")
        mask_ds, geo_data = read_raster(mask_file, False)
        src_srs = osr.SpatialReference()
        src_srs.ImportFromWkt(geo_data.projection)
        dst_srs = osr.SpatialReference()
        dst_srs.ImportFromEPSG(SRSEnum.WGS84_NUM.value)
        transformer = osr.CoordinateTransformation(src_srs, dst_srs)
        x_min, x_res, y_row, y_max, x_row, y_res = list(geo_data.transform)
        x_size = mask_ds.RasterXSize
        y_size = mask_ds.RasterYSize
        x_arr = [[x_min + (x + 0.5) * x_res + (y + 0.5) * y_row for x in range(x_size)] for y in range(y_size)]
        y_arr = [[y_max+(y+0.5)*y_res+(x+0.5)*x_row for x in range(x_size)] for y in range(y_size)]
        z_arr = np.zeros([x_size, y_size])
        point_arr = np.stack([x_arr, y_arr, z_arr], 2).reshape(-1, 3)
        point_arr = np.array(transformer.TransformPoints(point_arr)).reshape(y_size, x_size, 3)
        lat_arr = point_arr[:, :, 0]
        lon_arr = point_arr[:, :, 1]
        create_raster(os.path.join(path.cloud_latitude_path, f"{tile}_lat.tif"), lat_arr, geo_data, NodataEnum.LATITUDE_LONGITUDE.value)
        create_raster(os.path.join(path.cloud_longitude_path, f"{tile}_lon.tif"), lon_arr, geo_data, NodataEnum.LATITUDE_LONGITUDE.value)
        print(tile)


def main():
    path = BasePath()
    calculate_latitude_longitude_from_mask(path, get_world_tile(path))


if __name__ == "__main__":
    main()
