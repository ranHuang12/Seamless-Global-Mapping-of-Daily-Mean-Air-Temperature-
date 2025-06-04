# -*- coding: utf-8 -*-

# 模块导入
import numpy as np
import netCDF4 as nc
from osgeo import gdal, osr, ogr
import os
import glob


# 单个nc数据ndvi数据读取为多个tif文件，并将ndvi值化为-1-1之间
def NC_to_tiffs(data, Output_folder):
    nc_data_obj = nc.BaseDataset(data)
    Lon = nc_data_obj.variables['lon'][:]
    Lat = nc_data_obj.variables['lat'][:]
    ndvi_arr = np.asarray(nc_data_obj.variables['ASTER_GDEM_DEM'])  # 将ndvi数据读取为数组
    ndvi_arr = np.asarray(nc_data_obj.variables['ASTER_GDEM_DEM'])  # 将ndvi数据读取为数组
    # ndvi_arr_float = ndvi_arr.astype(float) / 10000  # 将int类型改为float类型,并化为-1 - 1之间

    # 影像的左上角和右下角坐标
    LonMin, LatMax, LonMax, LatMin = [Lon.min(), Lat.max(), Lon.max(), Lat.min()]

    # 分辨率计算
    N_Lat = len(Lat)
    N_Lon = len(Lon)
    Lon_Res = (LonMax - LonMin) / (float(N_Lon) - 1)
    Lat_Res = (LatMax - LatMin) / (float(N_Lat) - 1)

    # for i in range(len(ndvi_arr[:])):
        # 创建.tif文件
    driver = gdal.GetDriverByName('GTiff')
    out_tif_name = Output_folder + '\\' + data.split('\\')[-1].split('.')[0] + '_' + str(1) + '.tif'
    out_tif = driver.Create(out_tif_name, N_Lon, N_Lat, 1, gdal.GDT_Int16)

    # 设置影像的显示范围
    # -Lat_Res一定要是-的
    geotransform = (LonMin, Lon_Res, 0, LatMax, 0, -Lat_Res)
    out_tif.SetGeoTransform(geotransform)

    # 获取地理坐标系统信息，用于选取需要的地理坐标系统
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)  # 定义输出的坐标系为"WGS 84"，AUTHORITY["EPSG","4326"]
    out_tif.SetProjection(srs.ExportToWkt())  # 给新建图层赋予投影信息

    # 数据写出
    # out_tif.GetRasterBand(1).WriteArray(ndvi_arr_float[i])  # 将数据写入内存，此时没有写入硬盘
    out_tif.GetRasterBand(1).WriteArray(ndvi_arr)  # 将数据写入内存，此时没有写入硬盘
    out_tif.FlushCache()  # 将数据写入硬盘
    out_tif = None  # 注意必须关闭tif文件


def main():
    Input_folder = 'E:\\pcm\\nc\\example'
    Output_folder = 'E:\\pcm\\nc\\result'

    # 读取所有nc数据
    data_list = glob.glob(Input_folder + '\\*.nc')

    for i in range(len(data_list)):
        data = data_list[i]
        NC_to_tiffs(data, Output_folder)
        print(data + '-----转tif成功')

    print('----转换结束----')

main()

