import os

from ta_estimate.entity import Path as TaEstimatePath


class Path(TaEstimatePath):
    def __init__(self, root_path=None, cloud_root_path=None):
        super().__init__(root_path, cloud_root_path)
        self.interpolate_ta_path = os.path.join(self.ta_interpolate_path, "ta")
        self.interpolate_refer_path = os.path.join(self.interpolate_ta_path, "refer")
        self.interpolate_record_path = os.path.join(self.ta_interpolate_path, "record")
        self.interpolate_refer_record_path = os.path.join(self.interpolate_record_path, "refer")
        self.annual_ta_path = os.path.join(self.ta_interpolate_path, "annual_ta")
        self.monthly_ta_path = os.path.join(self.ta_interpolate_path, "monthly_ta")
        self.interpolate_validate_path = os.path.join(self.ta_interpolate_path, "validate")
        self.interpolate_validate_refer_path = os.path.join(self.interpolate_validate_path, "refer")

        self.cloud_refer_date_path = os.path.join(self.cloud_ta_interpolate_path, "refer_date")
        self.cloud_interpolate_ta_path = os.path.join(self.cloud_ta_interpolate_path, "ta")
        self.cloud_annual_ta_path = os.path.join(self.cloud_ta_interpolate_path, "annual_ta")
        self.cloud_monthly_ta_path = os.path.join(self.cloud_ta_interpolate_path, "monthly_ta")
        self.cloud_interpolate_refer_path = os.path.join(self.cloud_interpolate_ta_path, "refer")
        self.cloud_interpolate_record_path = os.path.join(self.cloud_ta_interpolate_path, "record")
        self.cloud_interpolate_refer_record_path = os.path.join(self.cloud_interpolate_record_path, "refer")
        self.cloud_interpolate_validate_path = os.path.join(self.cloud_ta_interpolate_path, "validate")
