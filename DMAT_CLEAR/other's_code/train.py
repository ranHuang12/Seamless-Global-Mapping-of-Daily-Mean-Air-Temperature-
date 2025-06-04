# -*- coding: utf-8 -*-
"""
Created on Tue Mar 16 14:46:44 2021

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

data,label = genDataset( r'CMP_data/Training', r"CMP_data/Training/CMP-training-removalrate.csv",True  ) 

val_thr = 0.01 #1822*0.01 ,一共为18段
val_num = int(len(data)*val_thr)
random.seed(0)
k = [i for i in range( len(data))]
random.shuffle(k)
val_data = data[k[:val_num]]
val_label = label[k[:val_num]]
train_data = data[k[val_num:]]
train_label = label[k[val_num:]]


# network
hidden_units = [128, 64,32,16]

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

if device == 'cuda':
    assert torch.cuda.is_available() is True, "cuda isn't available"
    print('Using GPU backend.\n'
          'GPU type: {}'.format(torch.cuda.get_device_name(0)))
else:
    print('Using CPU backend.')
    
epoch_pretrain = 50  #原本为100，为运行通，先取10
epoch_finetune = 10000  #原本为200，为运行通，先取10
loss_function = torch.nn.MSELoss()
optimizer = torch.optim.Adam  
adam_lr = 0.004 #finetune bp 的学习率
lr_steps = 400  


# Build model
dbn = DBN(hidden_units, input_length, output_length, device=device) 

# Train model
dbn.pretrain(train_data, train_label , epoch=epoch_pretrain, batch_size=batch_size)
dbn.finetune(train_data, train_label, epoch_finetune, batch_size, loss_function,
             optimizer(dbn.parameters(),lr=adam_lr),lr_steps,True)

torch.save(dbn, 'dbn.pth') 



 



























