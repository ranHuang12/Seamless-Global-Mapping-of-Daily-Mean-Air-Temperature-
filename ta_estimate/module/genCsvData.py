# -*- coding: utf-8 -*-
"""
Created on Tue Mar 16 19:25:25 2021

@author: junyang.zhang
"""

import numpy as np
import random
import csv
import os

from torch.utils.data import Dataset


def getResMap(rate_path):
    res_map = {}
    file = open(rate_path)     
    reader = csv.reader(file)
    info_list = list(reader)
    
    for e in info_list[1:]:
        if e[2].strip(" ") =="?": v = e[2] # 如果是Testing文件夹的磨光率，为"?"，不能转为float
        else:v = float(e[2]) 
        
        res_map[ e[0]+e[1] ] = v  #键为前两列数字合起来,值为第3列      
    
    return res_map


def getOneRow(e):
    tmp = []
    #未完，待续
    tmp.append(float(e[2] ) ) #先直接加载时间戳，后再计算为时间长度
    if e[4] == "A": # STAGE为A则为0 B 为 1
        tmp.append( 1. ) 
    else:
        tmp.append( 0. ) 
    
    for item in e[6:]: #加载从x7开始
        tmp.append(float( item) )    

    return tmp


def genDataset( csv_r   , rate_path , normalize = False  ):
    train_map = getResMap( rate_path ) 
    
    train_data,train_label = [],[]
    p_l = os.listdir(csv_r)
    #p_l =  ["CMP-training-000.csv" ,]
    for p in p_l:
        if p[-8:-4] == "rate":continue  #removalrate.csv不读
        
        file = open(os.path.join( csv_r,p))
        reader = csv.reader(file)
        info_list = list(reader)
        
        data_tmp , label_tmp = [],[] 
        for e in info_list[1:]:
            
            reg_v = train_map[ e[3]+e[4] ] #回归值  
            
            
            data_v = getOneRow(e)
                       
            if label_tmp == []:
                label_tmp.append( reg_v )   #先加载入标签
                data_tmp.append( data_v ) 
            else:
                if label_tmp[-1] != reg_v: #段结束
                    if len(label_tmp) !=0:train_label.append(np.array(label_tmp))
                    
                    label_tmp = []
                    # 计算读取的一段的时间长短
                    t_v = data_tmp[-1][0]-data_tmp[0][0]
                    for idx in range( len(data_tmp)):
                        data_tmp[idx][0] = t_v #把时间戳改为时间长度
                    
                    train_data.append(data_tmp)
                    data_tmp = []
                label_tmp.append(reg_v)
                data_tmp.append( data_v )
                
    train_label = np.array( train_label   )    #转为numpy后 ,(P,N) 为 P个 长为 N的list 组成numpy      
    train_data = np.array( train_data )  #转为numpy后 ,(P,N,M) 为 P个 长为 N的list 组成numpy,N的list由N个长为M的list组成
    
    if not normalize :return train_data,train_label  # normalize 默认为False,为True，则做归一化，mean和std需先运行calTrainMeanStd得到
    
    return normalization(train_data),train_label


#先从训练数据集中抽取一定值计算均值和方差
def calTrainMeanStd():
    train_data,train_label = genDataset( r'CMP_data/Training', r"CMP_data/Training/CMP-training-removalrate.csv"  ) 
    
    n = 50 #训练集随机取n段，求n段的方差和均值       
    d = [ i for i in range(len(train_data) )]
    random.shuffle(d) #打乱
    s_d = d[:n] #取前50个

    sample_data =  train_data[s_d]
    np_data = []
    for i in range(n):
        for j in range(len(sample_data[i]) ): 
            np_data.append( sample_data[i][j])
            
    np_data = np.array( np_data,dtype=np.float )
    
    return np.mean(np_data,0) ,np.std(np_data, 0)  

def normalization(train_data):
  
    for i in range( train_data.shape[0] ):
        np_d = np.array( train_data[i] ,dtype=np.float )
        for j in range(np_d.shape[0]):
            np_d[j] = (np_d[j] - mean_l)/std_l
        train_data[i]  = np_d   
    
    return train_data
    
mean_l = [3.61841943e+02, 4.95355290e-01, 5.42174061e+03, 3.70690853e+02, # mean 和 std 通过先运行 calTrainMeanStd得到
       1.70125557e+02, 3.51825106e+03, 5.08367084e+01, 1.56726240e+02,
       4.04550458e+01, 1.23684625e+03, 6.02989724e+00, 6.42894167e+01,
       1.62652227e+03, 4.14069516e+00, 7.50739388e-01, 2.50878514e+02,
       1.24252933e+01, 5.39711317e+01, 1.59977223e+02, 4.42091929e-01,
       2.88830213e+01]    
std_l = [7.63016617e+01, 4.99978426e-01, 3.41918961e+03, 2.15951769e+02,
       9.07847771e+01, 4.91348718e+02, 3.89794738e+01, 1.30148948e+02,
       3.36206219e+01, 1.50509891e+03, 4.97969704e+00, 4.05437506e+01,
       1.02575691e+03, 6.46795030e+00, 4.60479782e-01, 2.12438364e+02,
       1.61507588e+01, 9.30734350e+01, 6.71412298e+00, 4.96635334e-01,
       2.41658498e+01]


class indefDataSet(Dataset):
    def __init__(self, sent, sent_label):
        self.sent = sent
        self.sent_label = sent_label

    def __getitem__(self, item):
        return  self.sent[item] , self.sent_label[item] 

    def __len__(self):
        return len(self.sent)



def genDataset_2( csv_r   , rate_path , normalize = False  ):
    data = []
    label = []
    
    for i in range(50):
        k = random.randint(100,200)
        data.append( np.random.rand(k, 21 ) )
        label.append( np.random.rand( k ) )
    
    return np.array(data), np.array(label)
    



if __name__ =="__main__":
    #print(calTrainMeanStd())     #一开始运行该函数得到训练集的均值和方差
    
    #运行以下语句得到的是 train_data ,train_label 为 numpy形式，但维度不一致，无法转为tensor ;  
    train_data,train_label = genDataset( r'CMP_data/Training', r"CMP_data/Training/CMP-training-removalrate.csv",True  )    
    print(len(train_data))
    
    """
    #可以以下面方式随机抽取一段数据做运算
    dataset = indefDataSet(train_data, train_label)
    train_loader = DataLoader(dataset=dataset, batch_size=1, shuffle=True ) 
    for xi, yi in train_loader:
        print(  xi.shape, yi.shape  )   """












