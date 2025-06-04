import os

import pandas as pd
from sklearn.model_selection import train_test_split

from common_object.entity.base_dataset import BaseDataset
from common_object.enum import ColumnsEnum, ValidateModeEnum, QcModeEnum, ViewEnum
from common_util.common import build_modeling_x_list, convert_enum_to_value
from common_util.document import to_csv, handle_null


class Dataset(BaseDataset):
    all_view_list = convert_enum_to_value(ViewEnum)
    all_auxiliary_list = ["EVI", "ANGLE", "LATITUDE", "LONGITUDE", "ELEVATION", "MONTH", "DOY"]

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.td_all_arr = None
        self.tn_all_arr = None
        self.ad_all_arr = None
        self.an_all_arr = None
        self.td_gq_arr = None
        self.tn_gq_arr = None
        self.ad_gq_arr = None
        self.an_gq_arr = None
        self.td_angle_arr = None
        self.tn_angle_arr = None
        self.ad_angle_arr = None
        self.an_angle_arr = None
        self.month_arr = None
        self.doy_arr = None

        self.modeling_df: pd.DataFrame() = None
        self.validate_df: pd.DataFrame() = None
        self.test_df: pd.DataFrame() = None

    def __read_modeling_csv(self):
        config = self.config
        self.modeling_df = self._read_csv(config.tile_list, config.year_list, config.modeling_attribute_list,
                                          config.path.estimate_modeling_data_path, "modeling_tile.csv", dtype=ColumnsEnum.MODELING_DATA_TYPE.value)

    def load_modeling_data(self, load_modeling_data=True, load_validate_data=True):
        config = self.config
        modeling_df = self.modeling_df
        path = config.path
        if load_modeling_data:
            self.__read_modeling_csv()
            print(f"load modeling data:{self.modeling_df.shape}")
        if load_validate_data:
            if config.validate_mode in [ValidateModeEnum.FILE_ALL.value, ValidateModeEnum.FILE_GQ.value, ValidateModeEnum.FILE_OQ.value]:
                validate_csv = os.path.join(path.estimate_validate_data_path, f"validate_{config.modeling_attribute_list[0]}_{config.modeling_attribute_list[-1]}.csv")
                test_csv = os.path.join(path.estimate_validate_data_path, f"test_{config.modeling_attribute_list[0]}_{config.modeling_attribute_list[-1]}.csv")
                if not os.path.isfile(validate_csv) or not os.path.isfile(test_csv):
                    modeling_all_df = handle_null(modeling_df, build_modeling_x_list(self.all_view_list, QcModeEnum.ALL.value, self.all_auxiliary_list))
                    modeling_gq_df = handle_null(modeling_df, build_modeling_x_list(self.all_view_list, QcModeEnum.GOOD_QUALITY.value, self.all_auxiliary_list))
                    modeling_oq_df = handle_null(modeling_all_df, build_modeling_x_list(self.all_view_list, QcModeEnum.GOOD_QUALITY.value, []), True)
                    modeling_mixed_df = pd.concat([modeling_all_df, modeling_gq_df, modeling_oq_df]).drop_duplicates(ColumnsEnum.SINGLE_METE.value, keep=False)
                    validate_test_gq_df = train_test_split(modeling_gq_df, test_size=config.validate_test_ratio, random_state=0)[1]
                    validate_gq_df, test_gq_df = train_test_split(validate_test_gq_df, test_size=config.test_ratio/config.validate_test_ratio, random_state=0)
                    validate_test_oq_df = train_test_split(modeling_oq_df, test_size=config.validate_test_ratio, random_state=0)[1]
                    validate_oq_df, test_oq_df = train_test_split(validate_test_oq_df, test_size=config.test_ratio/config.validate_test_ratio, random_state=0)
                    validate_test_mixed_df = train_test_split(modeling_mixed_df, test_size=config.validate_test_ratio, random_state=0)[1]
                    validate_mixed_df, test_mixed_df = train_test_split(validate_test_mixed_df, test_size=config.test_ratio/config.validate_test_ratio, random_state=0)
                    validate_all_df = self.validate_df = pd.concat([validate_gq_df, validate_oq_df, validate_mixed_df], ignore_index=True)
                    test_all_df = self.test_df = pd.concat([test_gq_df, test_oq_df, test_mixed_df], ignore_index=True)
                    to_csv(validate_all_df, validate_csv, False)
                    to_csv(test_all_df, test_csv, False)
                else:
                    self.validate_df = pd.read_csv(validate_csv, dtype=ColumnsEnum.MODELING_DATA_TYPE.value)
                    self.test_df = pd.read_csv(test_csv, dtype=ColumnsEnum.MODELING_DATA_TYPE.value)
            elif config.validate_mode == ValidateModeEnum.SPECIFIC_FILE.value:
                self.validate_df = pd.read_csv(config.specific_validate_file, dtype=ColumnsEnum.MODELING_DATA_TYPE.value)
                self.test_df = pd.read_csv(config.specific_test_file, dtype=ColumnsEnum.MODELING_DATA_TYPE.value)
            else:
                self.validate_df = pd.DataFrame()
                self.test_df = pd.DataFrame()
            print(f"load validate data:{self.validate_df.shape}")
            print(f"load test data:{self.test_df.shape}")
        return self
