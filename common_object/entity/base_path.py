import os.path
import platform

from common_object.enum.path_enum import PathEnum
from common_util.path import create_path


class BasePath(object):
    root_path_dict = {"DESKTOP-VVEHAFM": [PathEnum.DISK_ROOT.value, PathEnum.PC_CLOUD_ROOT.value],
                      "DESKTOP-48H9FA2": [PathEnum.DISK_ROOT.value, PathEnum.LAPTOP_CLOUD_ROOT.value],
                      "DESKTOP-T2QJ708": [PathEnum.SERVER_ROOT.value, PathEnum.SERVER_CLOUD_ROOT.value],
                      "DESKTOP-I8N3SUD": [PathEnum.SERVER_ROOT.value, PathEnum.SERVER_CLOUD_ROOT.value],
                      "DESKTOP-AF9BQ28": [PathEnum.WORKSTATION_ROOT.value, PathEnum.WORKSTATION_CLOUD_ROOT.value],
                      "node1": [PathEnum.CLUSTER_ROOT.value, PathEnum.CLUSTER_ROOT.value],
                      "node2": [PathEnum.CLUSTER_ROOT.value, PathEnum.CLUSTER_ROOT.value],
                      "node3": [PathEnum.CLUSTER_ROOT.value, PathEnum.CLUSTER_ROOT.value]}

    def __init__(self, root_path=None, cloud_root_path=None):
        if root_path is None and cloud_root_path is None:
            root_path, cloud_root_path = self.root_path_dict[platform.node()] if platform.node() in self.root_path_dict.keys()\
                else os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        self.root_path = root_path
        self.cloud_root_path = cloud_root_path
        self.modis_data_path = os.path.join(root_path, "MODISData")
        self.lst_path = os.path.join(root_path, "lst")
        self.auxiliary_data_path = os.path.join(root_path, "auxiliary_data")
        self.dem_path = os.path.join(self.auxiliary_data_path, "dem")
        self.latitude_path = os.path.join(self.auxiliary_data_path, "latitude")
        self.longitude_path = os.path.join(self.auxiliary_data_path, "longitude")
        self.climate_path = os.path.join(self.auxiliary_data_path, "climate")
        self.ta_estimate_path = os.path.join(root_path, "ta_estimate")
        self.ta_interpolate_path = os.path.join(root_path, "ta_interpolate")

        self.cloud_modis_data_path = os.path.join(cloud_root_path, "MODISData")
        self.cloud_lst_path = os.path.join(cloud_root_path, "lst")
        self.cloud_auxiliary_data_path = os.path.join(cloud_root_path, "auxiliary_data")
        self.cloud_mask_path = os.path.join(self.cloud_auxiliary_data_path, "mask")
        self.cloud_dem_path = os.path.join(self.cloud_auxiliary_data_path, "dem")
        self.cloud_latitude_path = os.path.join(self.cloud_auxiliary_data_path, "latitude")
        self.cloud_longitude_path = os.path.join(self.cloud_auxiliary_data_path, "longitude")
        self.cloud_climate_path = os.path.join(self.cloud_auxiliary_data_path, "climate")
        self.cloud_xy_index_path = os.path.join(self.cloud_auxiliary_data_path, "xy_index")
        self.cloud_ta_estimate_path = os.path.join(cloud_root_path, "ta_estimate")
        self.cloud_ta_interpolate_path = os.path.join(cloud_root_path, "ta_interpolate")
        self.cloud_picture_path = os.path.join(cloud_root_path, "picture")
        self.cloud_table_path = os.path.join(cloud_root_path, "table")

    def create_path(self):
        for attr, value in vars(self).items():
            if attr.split("_")[-1] == "path":
                try:
                    create_path(value)
                except Exception as e:
                    pass
        return self

    def __str__(self):
        string = ""
        for attr, value in vars(self).items():
            if attr.split("_")[-1] == "path":
                string += f"{attr} {value}\n"
        return string
