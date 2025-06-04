import os

import numpy as np
import pandas as pd
import torch
from torch import nn, optim
from torch.utils.data import DataLoader

from common_object.entity import Accuracy
from common_object.enum import ViewEnum
from common_util.array import inverse_transform
from ta_estimate.core.base_executor import BaseExecutor
from ta_estimate.entity import Path
from ta_estimate.entity.configuration import Configuration
from ta_estimate.entity.dl_dataset import DLDataset


def set_reproducible():
    np.random.seed(0)
    torch.manual_seed(0)
    torch.backends.cudnn.deterministic = True


class DLExecutor(BaseExecutor):
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')  # GPU
    BATCH_SIZE = 2048  # 批量大小
    LEARNING_RATE = 0.00001  # 学习率

    def __init__(self, config, model, dataset):
        super().__init__(config, model, dataset, True)
        self.model.to(self.DEVICE)
        set_reproducible()

    def _build_modeling_dataset(self, use_serialized_model: bool, serialize: bool):
        super()._build_modeling_dataset(use_serialized_model, serialize)
        device = self.DEVICE
        self.train_dataloader = DataLoader(DLDataset(self.train_x_arr, self.train_y_arr, device), self.BATCH_SIZE)
        self.validate_dataloader = DataLoader(DLDataset(self.validate_x_arr, self.validate_x_arr, device), self.BATCH_SIZE)
        self.test_dataloader = DataLoader(DLDataset(self.test_x_arr, self.test_x_arr, device), self.BATCH_SIZE)

    def __convert_to_tensor(self, arr):  # 转换为张量
        return torch.from_numpy(arr).float().to(self.DEVICE)

    def _fit(self, use_serialized_model, serialize):
        net = self.model

        criterion = nn.MSELoss()  # 定义损失函数
        optimizer = optim.Adam(net.parameters(), lr=self.LEARNING_RATE)  # 定义优化器
        record_df_list = []
        min_val_rmse = 0
        for epoch in range(1, 151):  # 遍历训练轮数
            net.train()  # 模型转换为训练模式
            for x, y in self.train_dataloader:
                optimizer.zero_grad()  # 梯度清零
                outputs = net(x)  # 修改此处，返回L2正则化损失
                loss_batch = criterion(outputs, y) # 添加L2正则化损失
                # l2_loss = 0
                # for param in net.parameters():
                #     l2_loss += torch.norm(param, p=2)
                # loss_batch += l2_loss*0.001
                loss_batch.backward()  # 反向传播
                optimizer.step()  # 更新参数
            pred_y_with_train_arr = self.__predict(self.train_dataloader)  # 计算训练集预测值
            pred_y_with_validate_arr = self.__predict(self.validate_dataloader)  # 计算测试集预测值
            trn_precision = Accuracy.validate(self.train_y_origin_arr.flatten(), pred_y_with_train_arr)
            val_precision = Accuracy.validate(self.validate_y_arr.flatten(), pred_y_with_validate_arr)
            print(f"epoch:{epoch}")
            print(f"train:{trn_precision}")
            print(f"validate:{val_precision}")
            record_df_list.append(pd.DataFrame({
                "epoch": [epoch],
                "trn_r2": [trn_precision.r2], "trn_rmse": [trn_precision.rmse], "trn_mae": [trn_precision.mae],
                "val_r2": [val_precision.r2], "val_rmse": [val_precision.rmse], "val_mae": [val_precision.mae]
            }))
            if min_val_rmse == 0 or min_val_rmse-val_precision.rmse > 0.001:
                min_val_rmse = val_precision.rmse
            else:
                break
        pred_y_with_test_arr = self.__predict(self.test_dataloader)
        test_precision = Accuracy.validate(self.test_y_arr.flatten(), pred_y_with_test_arr)
        print(f"test:{test_precision}")
        record_df_list.append(pd.DataFrame({
            "epoch": [151],
            "val_r2": [test_precision.r2], "val_rmse": [test_precision.rmse], "val_mae": [test_precision.mae]
        }))
        return pd.concat(record_df_list, ignore_index=True)

    def __predict(self, dataloader):  # 计算预测值
        net = self.model
        net.eval()  # 模型转换为评估模式
        yt_pred_batch_list = []
        with torch.no_grad():  # 关闭梯度计算
            for x, _ in dataloader:
                yt_pred_batch_list.append(net(x))
            pred_y_arr = torch.cat(yt_pred_batch_list, dim=0).cpu().numpy()
        net.train()  # 模型转换为训练模式
        return inverse_transform(pred_y_arr, self.y_scaler)


def main():
    config = Configuration()
    config.train_year_list = range(2000, 2021)
    config.validate_year_list = range(2021, 2023)
    config.tile_list = ["h11v04"]
    config.view = ViewEnum.TD.value
    config.modeling_x_list = ["TD"]


if __name__ == "__main__":
    main()
