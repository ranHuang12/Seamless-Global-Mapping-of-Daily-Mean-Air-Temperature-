from osgeo import gdal, ogr, osr
import os
import numpy as np
import pprint


def read_raster(file_path):
    dataset = gdal.Open(file_path)
    band = dataset.GetRasterBand(1)
    data = band.ReadAsArray()
    info = dataset.GetGeoTransform()
    return info, dataset, data


def read_raster(file_path):
    dataset = gdal.Open(file_path)
    band = dataset.GetRasterBand(1)
    proj = dataset.GetProjection()
    transform = dataset.GetGeoTransform()
    arr = band.ReadAsArray()
    return arr, proj, transform


def read_tifandshp(file_path):
    src_ds = gdal.Open(r'E:\pcm\nc\out.tif')
    if src_ds == None:
        print('打开tif文件失败！')
    info = src_ds.GetGeoTransform()
    print(info)
    if file_path[-4:] == '.tif':
        return info

    if file_path[-4:] == '.shp':
        tile = file_path.split('.')[0][-6:]
        print(tile)
        tileshp = tile+'.shp'

        # 读取tif投影，确定EPSG_code
        tif_prj = src_ds.GetProjection()
        EPSG = tif_prj[tif_prj.rfind(',') + 2:-3]
        print('tif_EPGS:',EPSG)
        # 读取shp投影
        gdal.SetConfigOption("GDAL_FILENAME_IS_UTF8", "YES")
        gdal.SetConfigOption("SHAPE_ENCODING", "gbk")
        driver = ogr.GetDriverByName('ESRI Shapefile')
        ds = driver.Open(file_path)
        layer0 = ds.GetLayerByIndex(0)
        # 定义投影转换函数
        # 投影参数设置
        inosr = layer0.GetSpatialRef()
        print(str(inosr))

        shp_EPSG = str(inosr)[str(inosr).rfind(',') + 2:-3]
        print('shp_EPGS:',shp_EPSG)
        if not shp_EPSG == EPSG:
            outosr = osr.SpatialReference()
            outosr.ImportFromEPSG(int(EPSG))
            prj = outosr.ExportToWkt()
            outosr.ImportFromProj4(outosr.ExportToProj4())
            trans = osr.CoordinateTransformation(inosr, outosr)

            # 读取输入文件
            inds = ds
            inLayer = inds.GetLayer(0)

            outfn = os.path.join(r'E:\modis\modis_sinusoidal\projection',tileshp)
            # 创建输出文件
            if os.path.exists(outfn):
                driver.DeleteDataSource(outfn)
            outds = driver.CreateDataSource(outfn)
            outLayer = outds.CreateLayer(os.path.basename(outfn)[:-4], geom_type=inLayer.GetLayerDefn().GetGeomType())

            # 遍历输入要素，复制到新文件
            infeature = inLayer.GetNextFeature()
            featuredefn = outLayer.GetLayerDefn()
            while infeature:
                # 投影转换对象geometry
                geom = infeature.GetGeometryRef()
                geom.Transform(trans)
                # 创建输出要素
                outfeature = ogr.Feature(featuredefn)
                # 添加几何体
                outfeature.SetGeometry(geom)
                # 添加要素到图层
                outLayer.CreateFeature(outfeature)
                # 清除缓存，获取下一输入要素
                infeature = None
                outfeature = None
                infeature = inLayer.GetNextFeature()
            # 写入投影文件
            prjfile = open(outfn.replace('.shp', '.prj'), 'w')
            prjfile.write(prj)
            prjfile.close()
            # 写入编码文件
            cpgfile = open(outfn.replace('.shp', '.cpg'), 'w')
            cpgfile.write('gbk')
            cpgfile.close()


def read_shp_proj(path):
    if not path.endswith('.shp'):
        print('请输入shp文件')
        return 0
    driver = ogr.GetDriverByName('ESRI Shapefile')
    ds = driver.Open(path)
    layer0 = ds.GetLayerByIndex(0)
    extent = layer0.GetExtent()
    return extent


def main():

    # 读取用来裁剪的矢量边界，并调整其投影与栅格图像一致
    tile = 'h25v06'
    tile_name = tile+'.shp'
    tile_shp_path = os.path.join(r'E:\modis\modis_sinusoidal',tile_name)
    read_tifandshp(tile_shp_path)

    # 读取重投影后的矢量边界，得到其四至范围
    shp_proj_path = os.path.join(r'E:\modis\modis_sinusoidal\projection',tile_name)
    shp_extent = read_shp_proj(shp_proj_path)
    shp_min_lon = round(shp_extent[0])
    shp_max_lon = round(shp_extent[1])
    shp_min_lat = round(shp_extent[2])
    shp_max_lat = round(shp_extent[3])


    extract_folder_path = r'E:\pcm\nc\extract'
    # 遍历每个栅格影像
    tif_for_tile = []
    path = r'G:\china_DEM'
    tif_paths = os.listdir(path)
    for tif in tif_paths:
        print(tif)
        if not tif.endswith('tif'):
            continue

        # 读取栅格影像，并得到四至范围
        tif_path = os.path.join(path, tif)
        tif_extent = read_tif(tif_path)
        tif_min_lat = round(tif_extent[0][3]) - 1
        tif_max_lat = round(tif_extent[0][3])
        tif_min_lon = round(tif_extent[0][0])
        tif_max_lon = round(tif_extent[0][0]) + 1

        # 先进行简单的判断，剔出大量不符栅格
        if tif_max_lat < shp_min_lat:
            print('不符')
            continue
        if tif_min_lat > shp_max_lat:
            print('不符')
            continue
        if tif_max_lon < shp_min_lon:
            print('不符')
            continue
        if tif_min_lon > shp_max_lon:
            print('不符')
            continue

        # 用重投影后的矢量边界裁剪栅格
        tif_extract_name = tif[:-4]+'_extract.tif'
        tif_extract_path = os.path.join(extract_folder_path,tif_extract_name)
        gdal.Warp(tif_extract_path, tif_extent[1], cutlineDSName=shp_proj_path, cropToCutline=False)

        # 读取裁剪后的栅格数据，若不全为0，则存至tif_for_tile列表
        data = read_tif(tif_extract_path)[2]
        if np.any(data != 0):
            tif_for_tile.append(tif_path)
    pprint.pprint(tif_for_tile)


if __name__ == '__main__':
    main()
