import pandas as pd

from common_object.entity.base_dataset import BaseDataset
from common_object.enum import ColumnsEnum, ValidateModeEnum
from ta_interpolate.entity.path import Path


class Dataset(BaseDataset):
    def __init__(self):
        super().__init__()
        self.refer_arr = None
        self.train_ta_arr = None

        self.validate_estimate_df = None
        self.validate_refer_df = None
        self.validate_other_df = None
        self.validate_overall_df = None

        self.path = Path()

    def __read_validate_csv(self, tile_list, year_list, validate_attribute_list, validate_mode):
        path = self.path
        base_path = path.estimate_validate_data_path if validate_mode == ValidateModeEnum.ESTIMATE.value \
            else (path.interpolate_validate_refer_path if validate_mode == ValidateModeEnum.INTERPOLATE_REFER.value
                  else path.interpolate_validate_path)
        usecols = (ColumnsEnum.VALIDATE_REFER_DATA if validate_mode == ValidateModeEnum.INTERPOLATE_REFER.value else ColumnsEnum.VALIDATE_DATA).value
        dtype = (ColumnsEnum.VALIDATE_REFER_DATA_TYPE if validate_mode == ValidateModeEnum.INTERPOLATE_REFER.value else ColumnsEnum.VALIDATE_DATA_TYPE).value
        validate_df = self._read_csv(tile_list, year_list, validate_attribute_list, base_path, f"validate_{validate_mode.split('_')[-1]}_tile.csv", usecols, dtype)
        return validate_df

    def loading_validate_data(self, tile_list, year_list, validate_attribute_list, load_estimate_data=True):
        validate_refer_df = self.__read_validate_csv(tile_list, year_list, validate_attribute_list, ValidateModeEnum.INTERPOLATE_REFER.value)
        validate_other_df = self.__read_validate_csv(tile_list, year_list, validate_attribute_list, ValidateModeEnum.INTERPOLATE_OTHER.value)
        self.validate_overall_df = pd.concat([validate_refer_df, validate_other_df], ignore_index=True)
        print(f"load validate data:{validate_refer_df.shape} {validate_other_df.shape} {self.validate_overall_df.shape}")
        if load_estimate_data:
            self.validate_estimate_df = self.__read_validate_csv(tile_list, year_list, validate_attribute_list, ValidateModeEnum.ESTIMATE.value)
            print(f"load validate estimate data:{self.validate_estimate_df.shape}")
            exclude_df = self.validate_estimate_df[ColumnsEnum.SINGLE_METE.value]
            self.validate_refer_df = pd.concat([validate_refer_df, exclude_df]).drop_duplicates(ColumnsEnum.SINGLE_METE.value, keep=False)
            print(f"load validate refer data:{self.validate_refer_df.shape}")
            self.validate_other_df = pd.concat([validate_other_df, exclude_df]).drop_duplicates(ColumnsEnum.SINGLE_METE.value, keep=False)
            print(f"load validate other data:{self.validate_other_df.shape}")
        return self
