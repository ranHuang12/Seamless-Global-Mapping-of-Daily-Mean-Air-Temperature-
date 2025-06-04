import numpy as np
from sklearn.preprocessing import StandardScaler


def transform(arr, scaler=None):
    if scaler is None:
        scaler = StandardScaler()
        arr = scaler.fit_transform(arr.reshape(-1, 1)).flatten()
        return arr, scaler
    else:
        return scaler.transform(arr.reshape(-1, 1)).flatten()


def inverse_transform(arr, scaler):
    return scaler.inverse_transform(arr.reshape(-1, 1)).flatten()


def build_modeling_arr_with_std(x_arr_list, y_arr, x_scaler_list=None, y_scaler=None):
    if x_scaler_list is not None:
        x_std_arr_list = [transform(x_arr, x_scaler_list[index]) for index, x_arr in enumerate(x_arr_list)]
    else:
        x_std_arr_list = []
        x_scaler_list = []
        for x_arr in x_arr_list:
            x_std_arr, x_scaler = transform(x_arr)
            x_std_arr_list.append(x_std_arr)
            x_scaler_list.append(x_scaler)
    modeling_x_arr = np.stack(x_std_arr_list, -1)
    modeling_y_arr = None
    if y_arr is not None:
        if y_scaler is not None:
            modeling_y_arr = transform(y_arr, y_scaler)
        else:
            modeling_y_arr, y_scaler = transform(y_arr)
    return modeling_x_arr, modeling_y_arr, x_scaler_list, y_scaler


def build_modeling_arr_from_df(modeling_df, modeling_x_list, modeling_y, std=False, x_scaler_list=None, y_scaler=None):
    x_arr_list = [modeling_df[modeling_x].values for modeling_x in modeling_x_list]
    y_arr = None
    if modeling_y is not None:
        y_arr = modeling_df[modeling_y].values
    if std:
        modeling_x_arr, modeling_y_arr, x_scaler_list, y_scaler = build_modeling_arr_with_std(x_arr_list, y_arr, x_scaler_list, y_scaler)
    else:
        modeling_x_arr = np.stack(x_arr_list, -1)
        modeling_y_arr = y_arr
    return modeling_x_arr, modeling_y_arr, y_arr, x_scaler_list, y_scaler
