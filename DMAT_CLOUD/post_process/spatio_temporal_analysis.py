import os.path

import numpy as np
import pandas as pd

from common_object.enum import NodataEnum
from common_util.document import to_csv
from common_util.image import read_raster
from ta_interpolate.entity import Path


def calculate_ta_with_lat(path: Path, month_list, lat_width=1):
    record_dict = {"lat": [lat for lat in range(90, -90, -lat_width)]}
    step_size = int(lat_width*100)
    file_list = [os.path.join(path.monthly_ta_path, "world", f"wgs_mean_monthly_ta_world_{str(month).zfill(2)}.tif") for month in month_list]
    file_list.append(os.path.join(path.annual_ta_path, "world", "wgs_mean_annual_ta_world.tif"))
    for index, file in enumerate(file_list):
        field = index + 1
        ta_arr = read_raster(file)[0]
        avg_ta_list = []
        for row in range(0, ta_arr.shape[0], step_size):
            ta_lat_arr = ta_arr[row: row+step_size, :]
            ta_lat_arr = ta_lat_arr[ta_lat_arr != NodataEnum.TEMPERATURE.value]
            avg_ta_list.append(np.average(ta_lat_arr))
        record_dict[f"{field}_avg"] = avg_ta_list
        print(len(avg_ta_list))
    to_csv(pd.DataFrame(record_dict), os.path.join(os.path.join(path.cloud_monthly_ta_path, f"monthly_ta_with_lat_{lat_width}.csv")), False)


def calculate_ta_with_climate_zone(path: Path, month_list):
    climate_zone_arr = read_raster(os.path.join(path.climate_path, "climate_zone_10classes.tif"))[0]
    hemisphere_mask_arr = read_raster(os.path.join(path.climate_path, "hemisphere_mask.tif"))[0]
    climate_value_list = list(np.unique(climate_zone_arr[climate_zone_arr != NodataEnum.CLIMATE.value]))
    record_dict = {"climate_zone": [f"{climate_value}{'N' if hemisphere==1 else 'S'}" for climate_value in climate_value_list for hemisphere in [1, -1]]}
    record_dict["size"] = [climate_zone_arr[(climate_zone_arr == climate_value) & (hemisphere_mask_arr == hemisphere)].size for climate_value in climate_value_list for hemisphere in [1, -1]]
    for month in month_list:
        record_dict[month] = []
        ta_arr = read_raster(os.path.join(path.monthly_ta_path, "world", f"mean_monthly_ta_world_{str(month).zfill(2)}.tif"))[0]
        for climate_value in climate_value_list:
            for hemisphere in [1, -1]:
                record_dict[month].append(np.average(ta_arr[(ta_arr != NodataEnum.TEMPERATURE.value) & (climate_zone_arr == climate_value) & (hemisphere_mask_arr == hemisphere)]))
        print(record_dict[month])
    to_csv(pd.DataFrame(record_dict), os.path.join(os.path.join(path.cloud_monthly_ta_path, "monthly_ta_with_climate_zone_10classes.csv")), False)


def main():
    path = Path()
    month_list = list(range(1, 13))
    calculate_ta_with_lat(path, month_list, 1)
    # calculate_ta_with_climate_zone(path, month_list)


if __name__ == "__main__":
    main()
