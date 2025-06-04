import os.path

from osgeo import gdalconst

from common_object.enum import NodataEnum
from common_util.common import convert_to_list, get_world_tile
from common_util.image import mosaic, process_image_to_refer, read_raster, create_raster, process_image_with_args
from data_perprocessing.entity.path import Path


def create_dem(path: Path, tile_list):
    tile_list = convert_to_list(tile_list)
    gve_path = os.path.join(path.dem_path, "GVE")
    world_dem_file = os.path.join(gve_path, "gve_v2_global.tif")
    if not os.path.isfile(world_dem_file):
        wgs_world_dem_file = os.path.join(gve_path, "wgs_gve_v2_global.tif")
        if not os.path.isfile(wgs_world_dem_file):
            gve_file_list = [os.path.join(gve_path, filename) for filename in os.listdir(gve_path) if filename.split("_")[2] == "v2"]
            mosaic(gve_file_list, wgs_world_dem_file, NodataEnum.GMTED_DEM.value, NodataEnum.GMTED_DEM.value, gdalconst.GDT_Int16, False)
            world_dem_arr, geo_data = read_raster(wgs_world_dem_file)
            world_dem_arr[world_dem_arr == NodataEnum.GVE_WATER.value] = NodataEnum.GVE_DEM.value
            create_raster(wgs_world_dem_file, world_dem_arr, geo_data, NodataEnum.GVE_DEM.value)
        geo_data = read_raster(os.path.join(path.cloud_mask_path, f"{tile_list[0]}_mask.tif"))[1]
        process_image_with_args(wgs_world_dem_file, world_dem_file, geo_data.projection)
    world_dem_ds = read_raster(world_dem_file, False)[0]
    for tile in tile_list:
        mask_file = os.path.join(path.cloud_mask_path, f"{tile}_mask.tif")
        dem_file = os.path.join(path.dem_path, f"{tile}_dem.tif")
        process_image_to_refer(world_dem_ds, mask_file, dem_file, NodataEnum.GVE_DEM.value, NodataEnum.DEM.value, gdalconst.GRA_Average)
        geo_data = read_raster(mask_file)[1]
        dem_v1_arr = read_raster(os.path.join(path.dem_path, "version1", f"{tile}_dem.tif"))[0]
        dem_v2_arr = read_raster(dem_file)[0]
        dem_v2_arr[dem_v2_arr == NodataEnum.DEM.value] = dem_v1_arr[dem_v2_arr == NodataEnum.DEM.value]
        create_raster(dem_file, dem_v1_arr, geo_data, NodataEnum.DEM.value)
        print(tile)


def merge_region_dem(path: Path, tile_list, region="world"):
    dem_file_list = [os.path.join(path.cloud_dem_path, f"{tile}_dem.tif") for tile in tile_list]
    regional_dem_file = os.path.join(path.cloud_dem_path, f"{region}_dem.tif")
    mosaic(dem_file_list, regional_dem_file, NodataEnum.DEM.value, NodataEnum.DEM.value, gdalconst.GDT_Int16, False)
    regional_dem_arr = read_raster(regional_dem_file)[0]
    print(regional_dem_arr[regional_dem_arr != NodataEnum.DEM.value].size)


def main():
    path = Path()
    tile_list = get_world_tile(path)
    create_dem(path, tile_list)
    # merge_region_dem(path, tile_list)


if __name__ == "__main__":
    main()
