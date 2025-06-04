from osgeo import gdal
import numpy as np

from common_util.image import read_raster, create_raster


def validate(src_files, dst_file, src_nodata, dst_nodata):
    src_arrs = []
    for src_file in src_files:
        src_arrs.append(read_raster(src_file)[0].astype(np.float32))
    validate_arr = src_arrs[0]
    for src_arr in src_arrs[1:]:
        validate_arr = np.vstack((validate_arr, src_arr))
    # sum_value = 0
    # for src_arr in src_arrs:
    #     sum_value += np.sum(src_arr[src_arr != src_nodata])
    #     print(np.sum(src_arr[src_arr != src_nodata]))
    dst_arr = read_raster(dst_file)[0]
    condi = (validate_arr != src_nodata) & (validate_arr != dst_arr)
    # print(sum_value)
    # print(np.sum(dst_arr[dst_arr != dst_nodata]))
    validate_err = validate_arr[condi]
    condi2 = (dst_arr != dst_nodata) & (validate_arr != dst_arr)
    dst_err = dst_arr[condi2]
    if (validate_err.size > 0) | (dst_err.size > 0):
        print(dst_file)
        print(validate_err)
        print(dst_err)


def mask(input_file, output_file, mask_arr, geo_data, nodata):
    input_arr = read_raster(input_file)[0]
    print(input_arr)
    # output_arr = input_arr[1000:1650, 250:900]
    input_arr[mask_arr==0] = nodata
    create_raster(output_file, input_arr, geo_data, nodata)


def main():
    '''拼接LST tif数据
    input_path = r"E:\LST\step1_interpolate"
    all_output_path = r"E:\LST\step2_fillall\h28v05v06"
    for qc_mode in ["highquality", "allvalue"]:
        for transit_time in ["TD", "TN", "AD", "AN"]:
            output_path = os.path.join(all_output_path, "%s_%s_source" % (transit_time, qc_mode))
            FilePathUtil.create_path(output_path)
            if transit_time in ["TD", "TN"]:
                product = "MOD11A1"
            else:
                product = "MYD11A1"
            for year in range(2000, 2022):
                dates = get_all_dates(year)
                for date in dates:
                    input_files = []
                    for tile in ["h28v05", "h28v06"]:
                        lst_file = os.path.join(input_path, tile, "%s_%s_source" % (transit_time, qc_mode),
                                                "%s_%s_%s_%s_source.tif" % (transit_time, tile, date, qc_mode))
                        if not os.path.isfile(lst_file):
                            hdf_file_list = glob.glob(os.path.join(r"E:\LST\MODISData", product, tile, product+".A"+str(date)+"."+tile+"*"))
                            if len(hdf_file_list) == 0:
                                continue
                            lst_arr, geo_data = read_lst_hdf(hdf_file_list[0], transit_time, qc_mode)
                            lst_arr = lst_arr*0.02-273.15
                            create_raster(lst_file, lst_arr, geo_data, -273.15, False)
                        input_files.append(lst_file)
                    output_file = os.path.join(output_path,"%s_h28v05v06_%s_%s_source.tif" % (transit_time, date, qc_mode))
                    if os.path.isfile(output_file):
                        continue
                    mosaic(input_files, output_file, -273.15, 255, gdalconst.GDT_Float32)
    '''
    '''拼接EVI hdf数据为tif数据
    input_path = r"E:\LST\MODISData\MOD13Q1\h28v05"
    output_path = r"E:\LST\step1_interpolate\h28v05v06"
    mask_file = r"E:\LST\surface_data\mask\h28v05v06_mask.tif"
    mask_arr, geo_data = read_raster(mask_file)
    FilePathUtil.create_path(output_path)
    for filename in os.listdir(input_path):
        index_file1 = os.path.join(input_path, filename)
        index_date = filename.split(".")[1][1:]
        index_file2_list = glob.glob(os.path.join(r"E:\LST\MODISData\MOD13Q1\h28v06", "MOD13Q1.A" + str(index_date) + ".h28v06*"))
        if len(index_file2_list) != 1:
            continue
        input_files = []
        input_files.append(index_file1)
        input_files.append(index_file2_list[0])
        output_file = os.path.join(output_path, "EVI_h28v05v06_%s.tif" % index_date)
        mosaic(input_files, output_file, -3000, -3000, gdalconst.GDT_Float32)
        output_file2 = os.path.join(output_path, "temp", "EVI_h28v05v06_%s.tif" % index_date)
        resample(output_file, output_file2, geo_data.transform)
        output_file3 = os.path.join(output_path, "EVI", "EVI_h28v05v06_%s.tif" % index_date)
        index_arr = read_raster(output_file2)[0]
        index_arr[index_arr == -3000] = -20000
        index_arr *= 0.0001
        index_arr = np.where(mask_arr == 1, index_arr, -2)
        create_raster(output_file3, index_arr, geo_data, -2, False)
        print(output_file3)
        os.remove(output_file)
        os.remove(output_file2)
    '''
    '''裁剪数据至浙江矩形
    input_path = r"E:\LST\step2_fillall\h28v05v06"
    mask_file = r"E:\LST\surface_data\mask\zhejiang_mask.tif"
    mask_arr, geo_data = read_raster(mask_file)
    all_output_path = r"E:\LST\step2_fillall\zhejiang"
    filter_modes = ["highquality", "allvalue"]
    temporal_list = ["TD", "TN", "AD", "AN"]
    for filter_mode in filter_modes:
        for temporal in temporal_list:
            for year in range(2000, 2023):
                date_list = get_all_dates(year)
                for date in date_list:
                    input_file = os.path.join(input_path, "%s_%s_source" % (temporal, filter_mode),
                                              "%s_h28v05v06_%s_%s_source.tif" % (temporal, date, filter_mode))
                    if not os.path.isfile(input_file):
                        continue
                    output_path = os.path.join(all_output_path, "%s_%s_source" % (temporal, filter_mode))
                    FilePathUtil.create_path(output_path)
                    output_file = os.path.join(output_path,
                                               "%s_zhejiang_%s_%s_source.tif" % (temporal, date, filter_mode))
                    mask(input_file, output_file, mask_arr, geo_data, 255)
                    print(output_file)
    '''
    '''裁剪LC tif至浙江矩形
    input_path = r"E:\LST\surface_data\landcover\h28v05v06"
    mask_file = r"E:\LST\surface_data\mask\zhejiang_mask.tif"
    mask_arr, geo_data = read_raster(mask_file)
    output_path = r"E:\LST\surface_data\landcover\zhejiang"
    FilePathUtil.create_path(output_path)
    for year in range(2003, 2021):
        input_file = os.path.join(input_path, "IGBP_h28v05v06_%s.tif" % year)
        if not os.path.isfile(input_file):
            continue
        output_file = os.path.join(output_path, "IGBP_zhejiang_%s.tif" % year)
        mask(input_file, output_file, mask_arr, geo_data, 255)
        print(output_file)
    '''
    input_file = r"E:\LST\surface_data\dem\zhejiang_aspect_add.tif"
    output_file = r"E:\LST\surface_data\dem\zhejiang_aspect1.tif"
    mask_file = r"E:\LST\surface_data\mask\zhejiang_mask.tif"
    mask_arr, geo_data = read_raster(mask_file)
    mask(input_file, output_file, mask_arr, geo_data, -9999)


if __name__ == "__main__":
    main()
