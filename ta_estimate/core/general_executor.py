import cupy
import numpy as np

from common_object.entity import Accuracy
from common_object.enum import ModelEnum
from common_util.array import inverse_transform
from ta_estimate.core.base_executor import BaseExecutor


class GeneralExecutor(BaseExecutor):
    def __init__(self, config, model, dataset):
        super().__init__(config, model, dataset, False)

    def _build_modeling_dataset(self, use_serialized_model: bool, serialize: bool):
        super()._build_modeling_dataset(use_serialized_model, serialize)
        if self.test_x_arr.size != 0:
            self.validate_x_arr = np.stack([self.validate_x_arr, self.test_x_arr])
            self.validate_y_arr = np.stack([self.validate_y_arr, self.test_y_arr])
            self.test_x_arr = self.test_y_arr = np.array([])
            print(f"train:{self.train_x_arr.shape}")
            print(f"validate:{self.validate_x_arr.shape}")

    def _fit(self, use_serialized_model: bool, serialize: bool):
        config = self.config
        modeling_x_list = config.modeling_x_list
        regressor = self.model
        super()._fit(use_serialized_model, serialize)
        if config.model == ModelEnum.LINEAR.value:
            express = "TEMP="
            for i in range(0, len(modeling_x_list)):
                operator = "+" if i > 0 and regressor.coef_[i] > 0 else ""
                express += f"{operator}{regressor.coef_[i]}*{modeling_x_list[i]}"
            operator = "+" if regressor.intercept_ > 0 else ""
            express += f"{operator}{regressor.intercept_}"
            print(express)
        train_x_arr = cupy.array(self.train_x_arr)
        validate_x_arr = cupy.array(self.validate_x_arr)
        if config.std:
            pred_y_with_train_arr = inverse_transform(regressor.predict(train_x_arr), self.y_scaler)
            pred_y_with_validate_arr = inverse_transform(regressor.predict(validate_x_arr), self.y_scaler)
        else:
            pred_y_with_train_arr = regressor.predict(train_x_arr)
            pred_y_with_validate_arr = regressor.predict(validate_x_arr)
        self.train_precision = Accuracy.validate(self.original_train_y_arr, pred_y_with_train_arr, 0.01)
        self.validate_precision = Accuracy.validate(self.validate_y_arr, pred_y_with_validate_arr, 0.01)
        # to_csv(pd.DataFrame({config.modeling_y: self.validate_y_arr, f"PRED_{config.modeling_y}": pred_y_with_validate_arr}),
        #        os.path.join(path.estimate_validate_data_path, f"{config.model}_{''.join(view.view_name for view in config.view_list)}_{config.qc_mode.field}_validate_result.csv"),
        #        False)
        print(f"train:{self.train_precision}")
        print(f"validate:{self.validate_precision}")
        # self.importance_list = [round(importance, 4) for importance in regressor.feature_importances_]
        # print(self.importance_list)

    def predict(self, estimate_ta=True):
        config = self.config
        dataset = self.dataset
        if estimate_ta:
            self.pred_x_arr, _, condition, _, _ = dataset.build_modeling_arr_from_arr(config.modeling_x_list, config.modeling_y, False, config.std, self.x_scaler_list)
            size = 0
            if self.pred_x_arr is not None:
                super().predict()
                dataset.ta_arr[condition] = self.pred_y_arr
                size = self.pred_y_arr.size
            return size
        else:
            super().predict()


def main():
    pass


if __name__ == "__main__":
    main()
