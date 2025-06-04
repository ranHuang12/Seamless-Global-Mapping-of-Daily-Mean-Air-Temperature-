from osgeo import gdal
import os
import shutil


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


def reprojection(input_file, ref_file, output):
    input_ds = gdal.Open(input_file)
    ref_proj = read_raster(ref_file)[3]
    gdal.Warp(output, input_ds, dstSRS=ref_proj)
    print('%s reprojeted' % input_file)
    input_ds = None


def select(input_file, ref_file, output):
    # 计算参考影像四至范围
    arr, x_size, y_size, proj, transform = read_raster(ref_file)
    x_min, x_res, _, y_max, _, y_res = list(transform)
    x_max = x_min + x_res * x_size
    y_min = y_max + y_res * y_size

    # 计算待选择影像四至范围
    arr1, x_size1, y_size1, proj1, transform1 = read_raster(input_file)
    x_min1, x_res1, _, y_max1, _, y_res1 = list(transform1)
    x_max1 = x_min1 + x_res1 * x_size1
    y_min1 = y_max1 + y_res1 * y_size1

    # 模糊筛选
    if x_min1 >= x_max or x_max1 <= x_min or y_min1 >= y_max or y_max1 <= y_min:
        print('%s is out of range' % input_file)
    else:
        print('%s selected' % input_file)
        shutil.copy(input_file, output)


def main():
    # 读取mask下全部tif文件文件名
    all_mask_filenames = os.listdir(mask_path)
    mask_filenames = []
    for filename in all_mask_filenames:
        if filename.endswith('tif'):
            mask_filenames.append(filename)

    # 读取SRTMData下全部img文件文件名
    all_srtm_filenames = os.listdir(srtm_path)
    srtm_filenames = []
    for filename in all_srtm_filenames:
        if filename.endswith('img'):
            srtm_filenames.append(filename)

    reproj_mask_path = os.path.join(mask_path, 'reproj')
    if not os.path.exists(os.path.join(reproj_mask_path)):
        os.makedirs(reproj_mask_path)

    mosaic_path = os.path.join(temp_path, 'mosaic')
    if not os.path.exists(mosaic_path):
        os.makedirs(mosaic_path)

    for mask_filename in mask_filenames:
        tile = mask_filename.split('_')[0]
        print('%s start' % tile)
        # mask_file = os.path.join(mask_path, mask_filename)
        select_path = os.path.join(srtm_path, tile)
        if not os.path.exists(select_path):
            os.makedirs(select_path)

        # for srtm_filename in srtm_filenames:
        #     srtm_file = os.path.join(srtm_path, srtm_filename)
        #
        #     # mask重投影至与srtm一致
        #     reproj_mask_file = os.path.join(reproj_mask_path, mask_filename)
        #     if not os.path.isfile(reproj_mask_file):
        #         reprojection(mask_file, srtm_file, reproj_mask_file)
        #
        #     # 选取与mask外切矩形存在重叠的srtm
        #     select_file = os.path.join(select_path, srtm_filename)
        #     if not os.path.isfile(select_file):
        #         select(srtm_file, reproj_mask_file, select_file)

        # 读取tile下全部img文件文件名
        # all_select_filenames = os.listdir(select_path)
        # select_filenames = []
        # for filename in all_select_filenames:
        #     if filename.endswith('img'):
        #         select_filenames.append(filename)

        # 镶嵌
        mosaic_file = os.path.join(mosaic_path, 'dem_%s_90m.tif' % tile)
        if not os.path.isfile(mosaic_file):
            command = r'Python E:\PythonProject\make_dem_mask\python_code\gdal_merge_my.py -o %s %s\*.img' % (mosaic_file, select_path)
            os.system(command)

    # 重采样及裁切
    clip_path = os.path.join(temp_path, 'clip')
    resample_path = os.path.join(temp_path, 'resample')
    command = r'Python E:\PythonProject\make_dem_mask\python_code\dem_reproj_resample_clip.py %s %s %s %s' % (mosaic_path, mask_path, resample_path, clip_path)
    os.system(command)


if __name__ == '__main__':
    srtm_path = r'E:\PythonProject\make_dem_mask\SRTMData'
    mask_path = r'E:\PythonProject\make_dem_mask\mask'
    temp_path = r'E:\PythonProject\make_dem_mask\temp'
    main()
