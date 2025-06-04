# -*- coding: utf-8 -*-
"""
Created on Mon Mar 22 09:30:32 2021

@author: junyang.zhang
"""

import torch
import numpy as np
import matplotlib.pyplot as plt

from DBN import DBN
#from sklearn.preprocessing import *
#from sklearn.metrics import mean_squared_error
from genCsvData import genDataset
import random


input_length = 21  #数据变量维度，暂为21
output_length = 1 
batch_size = 0  #没啥用，先放这里

"""
data,label = genDataset( r'CMP_data/Training', r"CMP_data/Training/CMP-training-removalrate.csv",True  ) 

val_thr = 0.01 #1822*0.05 ,一共为91段
val_num = int(len(data)*val_thr)
random.seed(0)
k = [i for i in range( len(data))]
random.shuffle(k)
val_data = data[ k[:val_num]]
val_label = label[ k[:val_num]]

np.save("val_data.npy",val_data)  
np.save("val_label.npy",val_label)   # npy文件就是这么来的


"""

#因为在我这电脑随机设定种子0，产生的随机数可能在别的电脑会不一样，为保证结果一样， 我将我电脑的测试数据保存成npy文件，再读取
val_data = np.load("val_data.npy" ,allow_pickle=True)
val_label = np.load("val_label.npy",allow_pickle=True)

dbn = torch.load('dbn.pth' ,map_location=torch.device('cpu'))

y_predict = dbn.predict(val_data, val_label  , batch_size) 

MSE=0.
t = 0
for i in range(len(y_predict)):
    y_predict_i = np.sum(y_predict[i])/len(y_predict[i]) #(N,1),N条有N个输出，对N输出取平均作为一段的预测输出值
    real_label_i = val_label[i][0] # N个值都是一样的，取第一个即可
    print("pred and test", y_predict_i , real_label_i )
    if abs(y_predict_i - real_label_i)>5.0:continue
    MSE+=np.sum(np.power((y_predict_i - real_label_i ),2))
    t+=1
print("t:", t)
MSE=MSE/t
print("RMSE:", np.sqrt(MSE) )



















