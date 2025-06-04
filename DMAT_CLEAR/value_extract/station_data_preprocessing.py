import os

import numpy as np
import pandas as pd
from osgeo import osr

from common_object.entity import ModisDate
from common_object.enum import ColumnsEnum, NodataEnum, SRSEnum
from common_util.common import get_world_tile
from common_util.document import to_csv, merge_csv
from common_util.image import read_raster, create_raster
from ta_estimate.entity.path import Path


def gather_station_from_gsod(path: Path, year_list):
    station_file = os.path.join(path.cloud_station_path, f"station_gsod.csv")
    station_df_list = []
    for year in year_list:
        mete_path = os.path.join(path.mete_data_gosd_path, str(year))
        for filename in os.listdir(mete_path):
            mete_file = os.path.join(mete_path, filename)
            station_df = pd.read_csv(mete_file, usecols=ColumnsEnum.STATION_GSOD.value, dtype=ColumnsEnum.STATION_GSOD_TYPE.value)
            station_df_list.append(station_df.drop_duplicates())
        print(year)
    station_df = pd.concat(station_df_list).drop_duplicates()
    station_df = station_df[station_df["STATION"].notnull() & station_df["LATITUDE"].notnull() & station_df["LONGITUDE"].notnull() & station_df["ELEVATION"].notnull()]
    origin_station_file = os.path.join(path.cloud_station_path, f"station_gsod_{year_list[0]}_{year_list[-1]}.csv")
    to_csv(station_df, origin_station_file, False)
    return
    station_df = pd.read_csv(origin_station_file, dtype=ColumnsEnum.STATION_GSOD_TYPE.value).drop_duplicates("STATION")
    station_df.sort_values("STATION", inplace=True, ignore_index=True)
    src_srs = osr.SpatialReference()
    src_srs.ImportFromEPSG(SRSEnum.WGS84_NUM.value)
    dst_srs = osr.SpatialReference()
    geo_data = read_raster(os.path.join(path.cloud_mask_path, "h03v06_mask.tif"))[1]
    dst_srs.ImportFromWkt(geo_data.projection)
    transformer = osr.CoordinateTransformation(src_srs, dst_srs)
    lat_arr = station_df["LATITUDE"].values
    lon_arr = station_df["LONGITUDE"].values
    z_arr = np.zeros_like(lat_arr)
    point_arr = np.stack([lat_arr, lon_arr, z_arr], 1)
    point_arr = np.array(transformer.TransformPoints(point_arr)).reshape(-1, 3)
    station_df["SIN_X"] = point_arr[:, 0]
    station_df["SIN_Y"] = point_arr[:, 1]
    to_csv(station_df, station_file, False)


def gather_station_by_tile(path: Path, tile_list):
    station_df = pd.read_csv(os.path.join(path.cloud_station_path, f"station_gsod.csv"), dtype=ColumnsEnum.STATION_TYPE.value)
    for tile in tile_list:
        mask_arr, geo_data = read_raster(os.path.join(path.cloud_mask_path, f"{tile}_mask.tif"))
        y_size, x_size = np.shape(mask_arr)
        min_x, x_res, x_row, max_y, y_row, y_res = geo_data.transform
        max_x = min_x+x_size*x_res+y_size*x_row
        min_y = max_y+y_size*y_res+x_size*y_row
        station_tile_df = station_df[(station_df["SIN_X"] > min_x) & (station_df["SIN_X"] < max_x)
                                     & (station_df["SIN_Y"] > min_y) & (station_df["SIN_Y"] < max_y)]
        csv_count = station_tile_df.shape[0]
        tif_count = 0
        if csv_count > 0:
            station_arr = np.full((y_size, x_size), NodataEnum.STATION.value)
            index_x_list = []
            index_y_list = []
            for index, row in station_tile_df.iterrows():
                index_x = int((row["SIN_X"] - min_x) / x_res)
                index_y = int((row["SIN_Y"] - max_y) / y_res)
                index_x_list.append(index_x)
                index_y_list.append(index_y)
                station_arr[index_y][index_x] = 1
            station_tile_df.insert(7, "INDEX_X", index_x_list)
            station_tile_df.insert(8, "INDEX_Y", index_y_list)
            station_tile_df.insert(0, "TILE", [tile]*station_tile_df.shape[0])
            to_csv(station_tile_df, os.path.join(path.cloud_station_tile_path, f"station_{tile}.csv"), False)
            create_raster(os.path.join(path.cloud_station_tile_path, f"station_{tile}.tif"), station_arr, geo_data, NodataEnum.STATION.value)
            tif_count = station_arr[station_arr != NodataEnum.STATION.value].size
        to_csv(pd.DataFrame({"tile": [tile], "csv": [csv_count], "tif": [tif_count]}), os.path.join(path.cloud_station_tile_path, "station_tile.csv"))
        print(tile, csv_count, tif_count)


def extract_station_properties_by_tile(path: Path, tile_list):
    station_df_list = []
    for tile in tile_list:
        station_csv = os.path.join(path.cloud_station_tile_path, f"station_{tile}.csv")
        if os.path.isfile(station_csv):
            station_df = pd.read_csv(station_csv, dtype=ColumnsEnum.STATION_TILE_TYPE.value)
            station_arr = read_raster(os.path.join(path.cloud_station_tile_path, f"station_{tile}.tif"))[0]
            xindex_arr = read_raster(os.path.join(path.cloud_xy_index_path, f"x_index.tif"))[0]
            yindex_arr = read_raster(os.path.join(path.cloud_xy_index_path, f"y_index.tif"))[0]
            dem_arr = read_raster(os.path.join(path.dem_path, f"{tile}_dem.tif"))[0]
            dem_arr_record = dem_arr[(station_arr != NodataEnum.STATION.value) & (dem_arr != NodataEnum.DEM.value)]
            xindex_arr_record = xindex_arr[(station_arr != NodataEnum.STATION.value) & (dem_arr != NodataEnum.DEM.value)]
            yindex_arr_record = yindex_arr[(station_arr != NodataEnum.STATION.value) & (dem_arr != NodataEnum.DEM.value)]
            station_df_list.append(station_df.merge(pd.DataFrame({"INDEX_X": xindex_arr_record, "INDEX_Y": yindex_arr_record, "DEM": dem_arr_record}), "left", ["INDEX_X", "INDEX_Y"]))
            print(tile)
    station_df = pd.concat(station_df_list, ignore_index=True)
    station_df.sort_values("STATION", inplace=True)
    to_csv(station_df, os.path.join(path.cloud_station_path, f"station_global.csv"), False)


def gather_mete_data_by_station(path: Path, year_list):
    for year in year_list:
        mete_year_path = os.path.join(path.mete_data_gosd_path, str(year))
        for filename in os.listdir(mete_year_path):
            station = os.path.splitext(filename)[0]
            mete_file = os.path.join(mete_year_path, filename)
            mete_df = pd.read_csv(mete_file, dtype=ColumnsEnum.METE_GSOD_TYPE.value)
            mete_df["TEMP"] = mete_df["TEMP"].map(lambda temp: (temp - 32) / 1.8 if temp != 9999.9 else temp)
            mete_df["DATE"] = mete_df["DATE"].map(
                lambda date: ModisDate().parse_separated_date(date, date[4]).modis_date)
            to_csv(mete_df, os.path.join(path.mete_data_station_path, f"{station}.csv"))
        print(year)
    record_df_list = []
    for filename in os.listdir(path.mete_data_station_path):
        station = os.path.splitext(filename)[0]
        mete_file = os.path.join(path.mete_data_station_path, filename)
        mete_df = pd.read_csv(mete_file, dtype=ColumnsEnum.METE_GSOD_TYPE.value)
        record_df_list.append(pd.DataFrame({"STATION": [station], "SIZE": [mete_df.shape[0]], "MAX_TEMP_ATTRIBUTES": np.max(mete_df["TEMP_ATTRIBUTES"].values)}))
        print(station)
    count_df = pd.concat(record_df_list)
    station_df = pd.read_csv(os.path.join(path.cloud_station_path, f"station_gsod.csv"), dtype=ColumnsEnum.STATION_TYPE.value)
    station_without_position_df = pd.read_csv(os.path.join(path.cloud_station_path, f"station_gsod_without_position.csv"), dtype=ColumnsEnum.STATION_GSOD_TYPE.value)
    merge_csv(station_df, count_df, on="STATION", output_file=os.path.join(path.cloud_mete_data_station_path, f"count_mete_data_station_with_position.csv"))
    merge_csv(station_without_position_df, count_df, on="STATION", output_file=os.path.join(path.cloud_mete_data_station_path, f"count_mete_data_station_without_position.csv"))


def main():
    path = Path()
    tile_list = get_world_tile(path)
    year_list = list(range(2020, 2024))
    gather_station_from_gsod(path, year_list)
    # extract_station_properties_by_tile(path, tile_list)


if __name__ == "__main__":
    main()
