# -*- coding: utf-8 -*-
"""
Created on Tue Mar 16 18:53:28 2021

@author: junyang.zhang
"""

import torch
import numpy as np
import matplotlib.pyplot as plt

from DBN import DBN
#from sklearn.preprocessing import *
#from sklearn.metrics import mean_squared_error
from genCsvData import genDataset




input_length = 21  #数据变量维度，暂为21
output_length = 1 
batch_size = 0  #没啥用，先放这里
test_data,test_label = genDataset( r'CMP_data/Testing', r"CMP_data/Testing/CMP-test-removalrate.csv",True  )



dbn = torch.load('dbn.pth',map_location=torch.device('cpu'))
y_predict = dbn.predict(test_data, test_label  , batch_size) 


MSE=0.
for i in range(len(y_predict)):
    y_predict_i = np.sum(y_predict[i])/len(y_predict[i]) #(N,1),N条有N个输出，对N输出取平均作为一段的预测输出值
    real_label_i = test_label[i][0] # N个值都是一样的，取第一个即可
    MSE+=np.sum(np.power((y_predict_i - real_label_i ),2))
    print( abs( y_predict_i - real_label_i) )
 
print("RMSE:", np.sqrt(MSE) )

""" 
scaler = StandardScaler()

y_predict =  y_predict.reshape(-1, 1) 
y_real =  test_label.reshape(-1, 1) 
print( y_predict )
plt.figure(1)
plt.plot(y_real, label='real')
plt.plot(y_predict, label='prediction')
plt.xlabel('MSE Error: {}'.format(mean_squared_error(y_real, y_predict)))
plt.legend()
plt.title('Prediction result')
plt.show()   """















