from osgeo import gdal
from osgeo.gdalconst import GDT_Float32
import numpy as np
import sys
import os
driver = gdal.GetDriverByName('GTiff')
driver.Register()  # 单独注册某一类型（GTiff）的数据驱动，可读可写，可新建数据集


def read_raster(raster_file):
    ds = gdal.Open(raster_file)

    x_size = ds.RasterXSize
    y_size = ds.RasterYSize
    proj = ds.GetProjection()
    transform = ds.GetGeoTransform()

    band = ds.GetRasterBand(1)
    arr = band.ReadAsArray()

    ds = None
    band = None

    return arr, x_size, y_size, proj, transform


# def read_hdf(hdf_file):
#     ds = gdal.Open(hdf_file)
#     subdatasets = ds.GetSubDatasets()
#     day_ds = gdal.Open(subdatasets[0][0])
#
#     x_size = day_ds.RasterXSize
#     y_size = day_ds.RasterYSize
#     proj = day_ds.GetProjection()
#     transform = day_ds.GetGeoTransform()
#
#     ds = None
#     day_ds = None
#
#     return x_size, y_size, proj, transform


def create_raster(output_path, arr, proj, transform, nodata):
    h, w = np.shape(arr)  # 读取矩阵各纬度的长度
    oDS = driver.Create(output_path, w, h, 1, GDT_Float32, ['COMPRESS=LZW', 'BIGTIFF=YES'])
    # 创建GroTiff格式栅格影像，参数依次为路径、图像大小、波段数（单波段），数据类型（32位浮点型），压缩方式：Deflate
    outband1 = oDS.GetRasterBand(1)

    for i in range(h):
        outband1.WriteArray(arr[i].reshape(1, -1), 0, i)
    oDS.SetProjection(proj)
    oDS.SetGeoTransform(transform)
    outband1.FlushCache()
    outband1.SetNoDataValue(nodata)


def tif_clip_tif(in_tiff, clip_tiff, output):
    in_arr, x_size, y_size, proj, transform = read_raster(in_tiff)
    clip_arr = read_raster(clip_tiff)[0]
    in_arr[clip_arr == 0] = -32768
    create_raster(output, in_arr, proj, transform, -32768)
    print('%s clip completed' % in_tiff)


if __name__ == '__main__':
    input_file = r"C:\Users\dell\Nutstore\1\我的坚果云\Data\dem_h28v05.tif"
    mask_file = r"E:\LST\surface_data\mask\h28v05_mask.tif"
    output_file = r"E:\LST\surface_data\dem\h28v05_dem.tif"
    tif_clip_tif(input_file, mask_file, output_file)
