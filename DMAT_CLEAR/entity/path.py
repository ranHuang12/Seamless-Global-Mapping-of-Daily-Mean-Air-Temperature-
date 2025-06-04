import os.path

from common_object.entity import BasePath


class Path(BasePath):
    def __init__(self, root_path=None, cloud_root_path=None):
        super().__init__(root_path, cloud_root_path)
        self.mete_data_path = os.path.join(self.ta_estimate_path, "mete_data")
        self.mete_data_gosd_path = os.path.join(self.mete_data_path, "GSOD")
        self.mete_data_date_path = os.path.join(self.mete_data_path, "date")
        self.mete_data_station_path = os.path.join(self.mete_data_path, "station")
        self.mete_data_tile_path = os.path.join(self.mete_data_path, "tile")
        self.station_path = os.path.join(self.ta_estimate_path, "station")
        self.station_tile_path = os.path.join(self.station_path, "tile")
        self.estimate_modeling_data_path = os.path.join(self.ta_estimate_path, "modeling_data")
        self.estimate_validate_data_path = os.path.join(self.ta_estimate_path, "validate_data")
        self.model_path = os.path.join(self.ta_estimate_path, "model")
        self.estimate_ta_path = os.path.join(self.ta_estimate_path, "ta")
        self.estimate_coverage_path = os.path.join(self.ta_estimate_path, "coverage")

        self.cloud_station_path = os.path.join(self.cloud_ta_estimate_path, "station")
        self.cloud_station_tile_path = os.path.join(self.cloud_station_path, "tile")
        self.cloud_mete_data_path = os.path.join(self.cloud_ta_estimate_path, "mete_data")
        self.cloud_mete_data_station_path = os.path.join(self.cloud_mete_data_path, "station")
        self.cloud_estimate_modeling_data_path = os.path.join(self.cloud_ta_estimate_path, "modeling_data")
        self.cloud_estimate_validate_data_path = os.path.join(self.cloud_ta_estimate_path, "validate_data")
        self.cloud_estimate_coverage_path = os.path.join(self.cloud_ta_estimate_path, "coverage")
        self.cloud_record_path = os.path.join(self.cloud_ta_estimate_path, "record")
        self.cloud_modeling_record_path = os.path.join(self.cloud_record_path, "modeling")
        self.cloud_estimate_record_path = os.path.join(self.cloud_record_path, "estimate")
        self.cloud_model_path = os.path.join(self.cloud_ta_estimate_path, "model")
        self.cloud_estimate_picture_path = os.path.join(self.cloud_picture_path, "ta_estimate")
