import os

import numpy as np
import pandas as pd
from dbfread import DBF
from osgeo import gdal, gdalconst, ogr

from common_object.entity import GeoData
from common_util.common import convert_to_list
from common_util.date import get_interval_date


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


def reclass_lc(lc_arr):
    vegetated_condition = (lc_arr <= 10) | (lc_arr == 12) | (lc_arr == 14)
    water_condition = (lc_arr == 11) | (lc_arr == 17)
    non_vegetated_condition = (lc_arr == 13) | (lc_arr == 15) | (lc_arr == 16)
    lc_arr[vegetated_condition] = 0
    lc_arr[water_condition] = 1
    lc_arr[non_vegetated_condition] = 2
    return lc_arr


def read_lc(lc_file, lc_values):
    lc_arrs = []
    lc_arr = read_raster(lc_file)[0]
    lc_arr[(lc_arr <= 10) | (lc_arr == 12) | (lc_arr == 14)] = 1
    lc_arr[(lc_arr == 11) | (lc_arr == 17)] = 2
    lc_arr[(lc_arr == 13) | (lc_arr == 15) | (lc_arr == 16)] = 3
    for lc_value in lc_values:
        lc_arrs.append(np.where(lc_arr == lc_value, 1, 0))
    return lc_arrs


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


def create_validate_set(source_arr, ratio, validate_true_file, geo_data, create_file=True):
    valid_shape = source_arr[source_arr != 255]
    select_valid_arr = np.random.randint(0, 10000, np.shape(valid_shape))
    select_valid_arr[select_valid_arr < ratio] = 1
    select_valid_arr[select_valid_arr != 1] = 0
    select_arr = np.zeros_like(source_arr)
    select_arr[source_arr != 255] = select_valid_arr
    validate_true_arr = np.where(select_arr == 1, source_arr, 255)
    if create_file:
        create_raster(validate_true_file, validate_true_arr, geo_data, 255)
    return validate_true_arr


def lessen_scale(origin_arr, r1, r2):
    h1, w1 = np.shape(origin_arr)
    scale = int(r2 / r1)
    h2 = int(h1 * r1 / r2)
    w2 = int(w1 * r1 / r2)
    target_arr = np.zeros((h2, w2))
    for i in range(scale):
        for j in range(scale):
            target_arr += origin_arr[i:h2*scale:scale, j:w2*scale:scale]
    return target_arr, h2, w2


def get_block(arr):
    arr[arr == 255] = 0
    arr[arr != 0] = 1
    arr = lessen_scale(arr, 1, 65)[0]
    arr[arr < 4225 / 2] = 0
    arr[arr >= 4225 / 2] = 1
    return np.sum(arr)


def get_index_file(evi_path, lst_date, index, tile):
    for interval in range(0, 16):
        date_front = get_interval_date(lst_date, -interval)
        file_front = os.path.join(evi_path, "%s_%s_%s.tif" % (index, tile, str(date_front)))
        if os.path.isfile(file_front):
            print(file_front)
            return file_front
        date_behind = get_interval_date(lst_date, interval)
        file_behind = os.path.join(evi_path, "%s_%s_%s.tif" % (index, tile, str(date_behind)))
        if os.path.isfile(file_behind):
            print(file_behind)
            return file_behind


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


def process_image_with_args(src_file, dst_file, dst_srs, resample_alg=gdalconst.GRA_Bilinear, res=None, srcNodata=None, dstNodata=None, output_type=gdalconst.GDT_Int16):
    src_ds = read_raster(src_file, False)[0] if isinstance(src_file, str) else src_file
    gdal.Warp(dst_file, src_ds, xRes=res, yRes=res, dstSRS=dst_srs, srcNodata=srcNodata, dstNodata=dstNodata,
              resampleAlg=resample_alg, outputType=output_type, creationOptions=['COMPRESS=LZW'])


def process_image_to_refer(src_file, refer_file, dst_file, src_nodata, dst_nodata, resample_alg=gdalconst.GRA_Bilinear, output_type=gdalconst.GDT_Int16):
    src_ds = gdal.Open(src_file) if isinstance(src_file, str) else src_file
    refer_ds, geo_data = read_raster(refer_file, False)
    x_size = refer_ds.RasterXSize
    y_size = refer_ds.RasterYSize
    x_min, x_res, _, y_max, _, y_res = list(geo_data.transform)
    x_max = x_min + x_res * x_size
    y_min = y_max + y_res * y_size
    gdal.Warp(dst_file, src_ds, dstSRS=geo_data.projection, xRes=x_res, yRes=y_res, srcNodata=src_nodata,
              dstNodata=dst_nodata, resampleAlg=resample_alg, outputBounds=(x_min, y_min, x_max, y_max),
              outputType=output_type, creationOptions=['COMPRESS=LZW'])
    print(dst_file)


def shp_to_csv(shp_file, csv_file):
    dbf_file = shp_file.replace('.shp', '.dbf')
    dbf = DBF(dbf_file, encoding='gbk')
    shp_df = pd.DataFrame(iter(dbf))
    shp_df.to_csv(csv_file)


def csv_join_shp(shp_file, csv_file, output_file, shp_on, csv_on, csv_field=None, csv_dtype=None, how="left"):
    csv_field = convert_to_list(csv_field)
    if csv_on not in csv_field:
        csv_field.append(csv_on)
    dbf_file = shp_file.replace('.shp', '.dbf')
    shp_df = pd.DataFrame(iter(DBF(dbf_file)))
    print(shp_df)
    csv_df = pd.read_csv(csv_file, usecols=csv_field, dtype=csv_dtype)
    print(csv_df)
    output_df = shp_df.merge(csv_df, how, left_on=shp_on, right_on=csv_on)
    output_df.drop_duplicates(inplace=True)
    # output_df.dropna(subset=["tile"], inplace=True)
    gdal.SetConfigOption("GDAL_FILENAME_IS_UTF8", "YES")
    gdal.SetConfigOption("SHAPE_ENCODING", "gbk")
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(output_file):
        driver.DeleteDataSource(output_file)
    output_ds = driver.CreateDataSource(output_file)
    shp_ds = driver.Open(shp_file, 0)
    shp_layer = shp_ds.GetLayer(0)
    output_layer = output_ds.CreateLayer(os.path.basename(output_file)[:-4], geom_type=shp_layer.GetLayerDefn().GetGeomType())
    output_field_list = output_df.columns
    for field_name in output_field_list:
        field = ogr.FieldDefn(field_name, ogr.OFTString)
        field.SetWidth(50)
        output_layer.CreateField(field)
    shp_feature = shp_layer.GetNextFeature()
    count = 0
    while shp_feature:
        if str(output_df.loc[count, "used"]) == "1.0":
            output_feature = ogr.Feature(output_layer.GetLayerDefn())
            output_feature.SetGeometry(shp_feature.GetGeometryRef())
            for field in output_field_list:
                output_feature.SetField(field, str(output_df.loc[count, field]))
            output_layer.CreateFeature(output_feature)
        count += 1
        shp_feature = shp_layer.GetNextFeature()
    with open(output_file.replace('.shp', '.prj'), 'w') as file:
        with open(shp_file.replace(".shp", ".prj")) as input_file:
            file.write(input_file.read())
    with open(output_file.replace('.shp', '.cpg'), 'w') as file:
        file.write('gbk')
    shp_ds.Destroy()
    output_ds.Destroy()


def main():
    print(read_raster(r"C:\Users\dell\Documents\Tencent Files\2248289167\FileRecv\2022_01_01.tif")[0])


if __name__ == "__main__":
    main()
