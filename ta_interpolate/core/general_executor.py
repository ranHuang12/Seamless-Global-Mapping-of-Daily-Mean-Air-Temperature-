import cupy

from common_util.array import inverse_transform
from ta_interpolate.entity import Configuration, Dataset


class GeneralExecutor(object):
    def __init__(self, config=None, model=None, dataset=None):
        self.config: Configuration = config
        self.model = model
        self.dataset: Dataset = dataset

        self.pred_x_arr = None
        self.condition = None

        self.x_scaler_list = None
        self.y_scaler = None

    def prebuild_pred_x_arr(self, modeling_x_list=None, modeling_y=None):
        config = self.config
        modeling_x_list = config.modeling_x_list if modeling_x_list is None else modeling_x_list
        modeling_y = config.modeling_y if modeling_y is None else modeling_y
        self.pred_x_arr, _, self.condition, self.x_scaler_list, _ = self.dataset.build_modeling_arr_from_arr(modeling_x_list, modeling_y, False, config.std)
        return self.pred_x_arr.shape[0] if self.pred_x_arr is not None else 0

    def fit(self, modeling_x_list=None, modeling_y=None, prebuild_pred_x_arr=False):
        config = self.config
        dataset = self.dataset
        modeling_x_list = config.modeling_x_list if modeling_x_list is None else modeling_x_list
        modeling_y = config.modeling_y if modeling_y is None else modeling_y
        if prebuild_pred_x_arr:
            train_x_arr, train_y_arr, _, _, self.y_scaler = dataset.build_modeling_arr_from_arr(modeling_x_list, modeling_y, True, config.std, self.x_scaler_list)
        else:
            train_x_arr, train_y_arr, _, self.x_scaler_list, self.y_scaler = dataset.build_modeling_arr_from_arr(modeling_x_list, modeling_y, True, config.std)
        if train_x_arr is not None:
            train_x_arr = cupy.array(train_x_arr)
            train_y_arr = cupy.array(train_y_arr)
            self.model.fit(train_x_arr, train_y_arr)
            return train_y_arr.size
        return 0

    def predict(self, modeling_x_list=None, modeling_y=None, prebuild_pred_x_arr=False):
        config = self.config
        dataset = self.dataset
        modeling_x_list = config.modeling_x_list if modeling_x_list is None else modeling_x_list
        modeling_y = config.modeling_y if modeling_y is None else modeling_y
        if prebuild_pred_x_arr:
            pred_x_arr = self.pred_x_arr
            condition = self.condition
        else:
            pred_x_arr, _, condition, _, _ = dataset.build_modeling_arr_from_arr(modeling_x_list, modeling_y, False, config.std, self.x_scaler_list)
        pred_size = 0
        if pred_x_arr is not None:
            pred_x_arr = cupy.array(pred_x_arr)
            pred_y_arr = self.model.predict(pred_x_arr)
            dataset.ta_arr[condition] = inverse_transform(pred_y_arr, self.y_scaler) if config.std else pred_y_arr
            pred_size = pred_y_arr.size
        return pred_size
