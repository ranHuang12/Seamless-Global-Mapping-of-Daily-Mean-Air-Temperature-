import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error

import torch
import torch.nn as nn
import torch.optim as optim
from torch.nn import TransformerEncoder, TransformerEncoderLayer

# 设置GPU
DEVICE = torch.device('cuda:0')  # GPU

def set_reproducible():  # 设置随机种子
    np.random.seed(0)  # 随机种子
    torch.manual_seed(0)  # 随机种子
    torch.backends.cudnn.deterministic = True  # 随机种子

set_reproducible()  # 设置随机种子

def calc_r_squared(y_true, y_pred): # 计算R2
    ss_residual = np.sum((y_true - y_pred) ** 2) # 残差平方和
    ss_total = np.sum((y_true - np.mean(y_true)) ** 2) # 总平方和
    r_squared = 1 - (ss_residual / ss_total) # R2
    return r_squared # 返回R2
def calc_mare(y_true, y_pred):
    return np.mean(np.abs((y_true - y_pred) / y_true))

df_raw = pd.read_csv('0.csv', na_values='#REF!') # 读取数据
df_raw = df_raw.dropna()  # 删除包含缺失值的行
num_train = df_raw[(df_raw.year>=2008)&(df_raw.year<2015)].index  # 训练集索引
num_val = df_raw[(df_raw.year>=2015)&(df_raw.year<=2016)].index  # 测试集索引
num_test = df_raw[df_raw.year==2017].index
col_names = []
for name in ['lon','lat','dem','p','sm','t','sun','evi']:
    col_names += [name + '_' + str(i) for i in range(16, 33)]
x_train = df_raw.loc[num_train, col_names].values  #  训练集特征

# 训练集目标变量
y_train = df_raw.loc[num_train, 'yield'].values

from sklearn.preprocessing import StandardScaler
yield_scaler = StandardScaler()
y_train = yield_scaler.fit_transform(y_train.reshape(-1, 1)).flatten()

x_val = df_raw.loc[num_val, col_names].values  # 测试集特征
y_val = yield_scaler.transform(df_raw.loc[num_val, 'yield'].values.reshape(-1, 1)).flatten()  # 测试集目标变量

scaler = StandardScaler()  # 标准化
hidden_size = 128  # 设置隐藏层
num_layers = 2  # 设置LSTM层数

xt_train = torch.from_numpy(x_train[:300].reshape(300, 17, 8)).float().to(DEVICE)  # 转换为张量
yt_train = torch.from_numpy(y_train[:300]).float().to(DEVICE)  # 转换为张量

# 修改prepare_tensor函数
def prepare_tensor(x, y):  # 转换为张量
    return (
        torch.from_numpy(x.reshape(-1, 17, 8)).float().to(DEVICE),  # 转换为张量
        torch.from_numpy(y).float().to(DEVICE)  # 转换为张量
    )


class CNNTLSTM(nn.Module):
    def __init__(self):
        super(CNNTLSTM, self).__init__()

        # CNN Layers
        self.conv1 = nn.Conv1d(in_channels=8, out_channels=128, kernel_size=3, stride=1, padding=1)
        self.bn1 = nn.BatchNorm1d(128)  # 添加BatchNorm1d层
        self.relu = nn.ReLU()

        # LSTM Layer
        self.lstm = nn.LSTM(input_size=128, hidden_size=hidden_size, num_layers=num_layers, batch_first=True)

        # Fully Connected Layer
        self.fc = nn.Linear(hidden_size, 1)
        self.lambda_l2 = 0.001

    def forward(self, x):
        # CNN Forward
        x = x.view(-1, 8, 17)
        x = self.conv1(x)
        x = self.bn1(x)  # 在激活函数前添加BatchNorm
        x = self.relu(x)
        x = x.permute(0, 2, 1)

        # LSTM Forward
        lstm_out, _ = self.lstm(x)
        lstm_out = self.relu(lstm_out)

        # Fully Connected Layer
        fc_out = self.fc(lstm_out[:, -1, :])

        # L2 Loss (This part is retained as is from your code)
        l2_loss = 0
        for param in self.parameters():
            l2_loss += torch.norm(param, p=2)

        return fc_out.squeeze()

net = CNNTLSTM() # 实例化模型
net.to(DEVICE) # 模型放入GPU

BSZ = 512 # 设置批量大小
lr = 0.00001 # 设置学习率
momentum = 0.9 # 设置动量

criterion = nn.MSELoss() # 定义损失函数
optimizer = optim.Adam(net.parameters(), lr=lr) # 定义优化器

# 计算测试集预测值
def calc_test_pred(net, x, y):
    net.eval()
    with torch.no_grad():
        xt, yt = prepare_tensor(x, y)
        yt_pred, _ = net(xt)
    # net.train()
    return yt_pred.cpu().numpy()

def prepare_tensor(x, y): # 转换为张量
    return (
        torch.from_numpy(x.reshape(-1, 8, 1)).float().to(DEVICE), # 转换为张量
        torch.from_numpy(y).float().to(DEVICE) # 转换为张量
    )

def calc_pred(net, x, y): # 计算预测值
    net.eval() # 模型转换为评估模式
    yt_pred_batch_list = [] # 初始化预测值列表
    with torch.no_grad(): # 关闭梯度计算
        for i in range(0, x.shape[0], BSZ): # 遍历数据集
            xt, yt = prepare_tensor(x[i:i + BSZ], y[i:i + BSZ]) # 转换为张量
            yt_pred_batch, _ = net(xt)  # 修改此处，不返回L2正则化损失
            yt_pred_batch_list.append(yt_pred_batch) # 添加预测值
    y_pred = torch.cat(yt_pred_batch_list, dim=0).cpu().numpy() # 合并预测值
    net.train() # 模型转换为训练模式
    return y_pred # 返回预测值

def calc_all_indicators(y_true, y_pred): # 计算所有评价指标
    mse = mean_squared_error(y_true, y_pred) # 计算MSE
    rmse = np.sqrt(mse) # 计算RMSE
    return mse, rmse # 返回MSE和RMSE

loss_train_list, rmse_train_list, rmse_val_list, r2_val_list,r2_train_list = [], [], [], [],[] # 初始化列表

for epoch in range(1, 2000): # 遍历训练轮数
    net.train() # 模型转换为训练模式
    for i in range(0, x_train.shape[0], BSZ): # 遍历数据集
        xt_train, yt_train = prepare_tensor(x_train[i:i + BSZ], y_train[i:i + BSZ]) # 转换为张量
        optimizer.zero_grad() # 梯度清零
        outputs, l2_loss = net(xt_train) # 修改此处，返回L2正则化损失
        loss_batch = criterion(outputs, yt_train) + l2_loss  # 添加L2正则化损失
        loss_batch.backward() # 反向传播
        optimizer.step() # 更新参数

    y_train_pred = calc_pred(net, x_train, y_train) # 计算训练集预测值
    loss_train, rmse_train = calc_all_indicators(y_train, y_train_pred) # 计算训练集损失和RMSE
    r2_train = calc_r_squared(y_train, y_train_pred) # 计算训练集 R^2  ----- 添加的部分
    r2_train_list.append(r2_train) # 添加训练集 R^2  ----- 添加的部分
    loss_train_list.append(loss_train) # 添加训练集损失
    rmse_train_list.append(rmse_train) # 添加训练集RMSE
    y_val_pred = calc_pred(net, x_val, y_val) # 计算测试集预测值
    _, rmse_val = calc_all_indicators(y_val, y_val_pred) # 计算测试集RMSE
    rmse_val_list.append(rmse_val) # 添加测试集RMSE
    r2_val = calc_r_squared(y_val, y_val_pred) # 计算测试集R^2
    r2_val_list.append(r2_val) # 添加测试集R^2
    mare_val=calc_mare(y_val,y_val_pred)
    print('[epoch {:d}] val MARE: {:.4f}, training rmse: {:.4f}, val rmse: {:.4f}, val R^2: {:.4f}, train R^2: {:.4f}'.format(epoch, mare_val, rmse_train, rmse_val, r2_val, r2_train)) # 修改此处，添加训练集 R^2

    if (r2_val>0.4): # 如果测试集RMSE小于等于1.008
        # 使用StandardScaler进行反归一化
        wanted_pred_t = yield_scaler.inverse_transform(y_val_pred.reshape(-1, 1)).flatten() # 保存测试集预测值
        torch.save(net.state_dict(), 'model.pth') # 保存模型参数

model=CNNTLSTM()
model.load_state_dict(torch.load('model.pth'))
model.eval()
x_test = df_raw.loc[num_test, col_names].values  # 测试集特征
y_test = yield_scaler.transform(df_raw.loc[num_test, 'yield'].values.reshape(-1, 1)).flatten() # 测试集标签

xt_test = torch.from_numpy(x_test.reshape(-1, 17, 8)).float().to(DEVICE)  # 转换为张量
yt_test = torch.from_numpy(y_test).float().to(DEVICE)  # 转换为张量

y_test_pred = calc_test_pred(net, x_test, y_test)  # 计算测试集预测值
wanted_pred_t = yield_scaler.inverse_transform(y_test_pred.reshape(-1, 1)).flatten()  # 保存验证集预测值
# 计算测试集评价指标
mse_test, rmse_test = calc_all_indicators(y_test, y_test_pred)  # 计算测试集的MSE和RMSE
r2_test = calc_r_squared(y_test, y_test_pred)  # 计算测试集的R^2
r_test = np.sqrt(r2_test) # 计算R值
mare_test = calc_mare(y_test, y_test_pred)

print('测试集结果:')
print('Test MSE: {:.4f}'.format(mse_test))
print('Test RMSE: {:.4f}'.format(rmse_test))
print('Test MARE: {:.4f}'.format(mare_test))
print('Test R^2: {:.4f}'.format(r2_test))
print('Test R: {:.4f}'.format(r_test)) # 输出R值

pd.DataFrame(wanted_pred_t).to_csv('CNN-LSTM-gpp.csv', header=None, index=None)