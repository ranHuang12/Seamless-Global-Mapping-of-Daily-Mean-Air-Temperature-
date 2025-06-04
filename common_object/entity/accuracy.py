import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error, root_mean_squared_error

from common_object.enum import NodataEnum


class Accuracy(object):
    def __init__(self, size=0, r2=0, rmse=0, mae=0, bias=0):
        self.size = size
        self.r2 = r2
        self.rmse = rmse
        self.mae = mae
        self.bias = bias

    def __str__(self):
        return f"size:{self.size} r2:{self.r2} rmse:{self.rmse} mae:{self.mae} bias:{self.bias}"

    @staticmethod
    def validate(true_arr, pred_arr, scaler_factor=1, filter_nodata=False, true_nodata=NodataEnum.TEMPERATURE.value, pred_nodata=NodataEnum.TEMPERATURE.value, format_str=".4g"):
        if filter_nodata:
            condition = (true_arr != true_nodata) & (pred_arr != pred_nodata)
            true_arr = true_arr[condition]
            pred_arr = pred_arr[condition]
        true_arr = true_arr.astype(np.float32)
        pred_arr = pred_arr.astype(np.float32)
        true_arr *= scaler_factor
        pred_arr *= scaler_factor
        accuracy = Accuracy()
        accuracy.size = true_arr.size
        if accuracy.size != 0:
            accuracy.r2 = format(r2_score(true_arr, pred_arr), format_str)
            accuracy.rmse = format(root_mean_squared_error(true_arr, pred_arr), format_str)
            accuracy.mae = format(mean_absolute_error(true_arr, pred_arr), format_str)
            # precision.mare = np.mean(np.abs((true_arr - pred_arr) / true_arr))
            accuracy.bias = format(np.mean(pred_arr - true_arr), format_str)
        return accuracy
