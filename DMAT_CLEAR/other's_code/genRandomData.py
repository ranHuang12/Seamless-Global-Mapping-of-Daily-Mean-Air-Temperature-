# -*- coding: utf-8 -*-
"""
Created on Fri Mar 12 17:51:25 2021

@author: junyang.zhang
"""

from torch.utils.data import Dataset,DataLoader
import numpy as np
import random
import torch


class MyDataset(Dataset):
    def __init__(self,  transform=None, target_transform=None ):
        imgs = []
        
        for t in range(10000): #这里假设数据读出来，一个是100段，每段64个25维向量,实际应用则转为读取csv,先做均值方差归一化
            num =64 #64个时间上连续,重要参数
            y = random.randint(1,5)
            x = np.random.randn( num,25)*y
            imgs.append([x, y])

        self.imgs = imgs
        self.target_transform = target_transform
         

    def __getitem__(self, index):
        fn, label = self.imgs[index]
         
        return torch.from_numpy(fn),label

    def __len__(self):
        return len(self.imgs)


def dLoader( ):
    train_data = MyDataset()
    train_loader = DataLoader(dataset=train_data, batch_size=1, shuffle=True )
    return train_loader  

def getDataset( data_num =1000 , batch_size = 128 , dim = 25 ):
    train_data,train_label =  [],[ ]
    
    dim=25
    for t in range(data_num): #这里假设数据读出来，一个是10000段，每段64个25维向量,实际应用则转为读取csv,先做均值方差归一化
    #64个时间上连续,重要参数
        y = random.randint(1,5)
        x = y*0.1+np.random.randint( 1,10,size=(batch_size,dim) )*0.01
        train_data.append( x.tolist() )
        train_label.append(  [y,]*batch_size )
        #注释部分相当于产生的是 64个dim维数据，每个dim维数据对应的label不同
        """
        x_tmp=[]
        y_tmp = []
        for k in range(num):
            y = random.randint(0,5)
            x = np.random.randn( 1,dim)*(y+1)*0.1
            x_tmp.append(x)
            y_tmp.append(y)
            
        train_data.append( x_tmp )
        train_label.append(  y_tmp )  """
        
    train_data =  np.array(train_data)
    train_label = np.array(train_label)
    train_data.reshape(-1,batch_size,dim)
    train_label.reshape( -1 , batch_size )
    
    return  train_data ,  train_label  


if __name__=="__main__":
    train_data = MyDataset()
    train_loader = DataLoader(dataset=train_data, batch_size=1, shuffle=True )
    
    
    
    
    
    
    