from osgeo import gdal,ogr,osr
import os
import time
from shutil import copy


def read_tif(file_path):
    dataset = gdal.Open(file_path)
    band = dataset.GetRasterBand(1)
    data = band.ReadAsArray()
    info = dataset.GetGeoTransform()
    return info,dataset,data


def read_tifandshp(tile,file_path):
    src_ds = gdal.Open(r'E:\pcm\nc\out.tif')
    if src_ds == None:
        print('打开tif文件失败！')
    info = src_ds.GetGeoTransform()
    print(info)
    if file_path[-4:] == '.tif':
        return info

    if file_path[-4:] == '.shp':
        # tile = file_path.split('.')[0][-6:]
        # print(tile)
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

def folder_clean(path):
    files = os.listdir(path)
    for file in files:
        file_path = os.path.join(path,file)
        os.remove(file_path)

def read_shp_proj(path):
    if not path.endswith('.shp'):
        print('请输入shp文件')
        return 0
    driver = ogr.GetDriverByName('ESRI Shapefile')
    ds = driver.Open(path)
    layer0 = ds.GetLayerByIndex(0)
    extent = layer0.GetExtent()
    return extent


def merging(tile,list):
    print('{} 包含 {} 个格子'.format(tile,len(list)))
    merged_grids = ''
    for grid in list:
        merged_grids = merged_grids+grid+' '
    return merged_grids


def main():

    # 读取用来裁剪的矢量边界，并调整其投影与栅格图像一致
    origin_tiles = r'E:\modis\modis_sinusoidal\tiles'
    tiles = os.listdir(origin_tiles)
    print(tiles)
    for tile in tiles:
        if not tile.endswith('.shp'):
            continue
        tile = tile[:6]
        # if tile in 'h26v06':
        #     continue
        if tile != 'h25v04':
            continue
        print('tile {} 遍历中……'.format(tile))


        tile_name = tile+'.shp'
        tile_shp_path = os.path.join(r'E:\modis\modis_sinusoidal','tiles',tile_name)
        print(tile_shp_path)
        read_tifandshp(tile,tile_shp_path)

        # 读取重投影后的矢量边界，得到其四至范围
        shp_proj_path = os.path.join(r'E:\modis\modis_sinusoidal\projection',tile_name)
        shp_extent = read_shp_proj(shp_proj_path)
        shp_min_lon = round(shp_extent[0])
        shp_max_lon = round(shp_extent[1])
        shp_min_lat = round(shp_extent[2])
        shp_max_lat = round(shp_extent[3])


        extract_folder_path = r'E:\pcm\nc\extract'
        folder_clean(extract_folder_path)
        # 遍历每个栅格影像
        tif_for_tile = []
        path = r'E:\pcm\nc\merge_example'
        path = r'G:\china_DEM'
        tif_paths = os.listdir(path)
        for tif in tif_paths:
            print('    '+tif)
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
                print('    不符')
                continue
            if tif_min_lat > shp_max_lat:
                print('    不符')
                continue
            if tif_max_lon < shp_min_lon:
                print('    不符')
                continue
            if tif_min_lon > shp_max_lon:
                print('    不符')
                continue
            new_path = r'G:\classified_DEM'
            new_tile_path = os.path.join(new_path,tile)
            if not os.path.exists(new_tile_path):
                os.mkdir(new_tile_path)
            new_file_path = os.path.join(new_tile_path,tif)
            copy(tif_path,new_file_path)
        tile_dem_name = tile+'_DEM_sin_30m.tif'
        tile_dem_path = os.path.join(r'G:\china_DEM_30m',tile_dem_name)
        print(tile_dem_path)
        # comm = 'python '+'E:\pcm\\nc\gdal_merge.py'+' -o '+'G:\\a\\1.tif'+' '+merged_grids
        comm = 'E:\pcm\\nc\gdal_merge_my.py' + ' -o ' + 'G:\\a\\{}.tif'.format(tile) + ' ' + new_tile_path + '\\*.tif'
        print(comm)
        os.system(comm)


begintime = time.time()
main()
endtime = time.time()
print('共用时 {} 秒'.format(endtime-begintime))

