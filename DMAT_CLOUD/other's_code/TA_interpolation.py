#encoding = utf-8
from osgeo import gdal,ogr 
import numpy as np
from osgeo.gdalconst import GDT_Float32 #为什么要导入GDT_Float32
import os
import gc


def readRaster(file_path): #读单波段tif数据
    ds=gdal.Open(file_path) #dataset=gdal.open("filename")  文件名，如*.tif
    if ds==None:
        print ("failed to open file")
    band=ds.GetRasterBand(1)
    h=band.YSize; w=band.XSize #波段图像的宽和高
    proj=ds.GetProjection()
    transform=ds.GetGeoTransform()
    arr=np.zeros((h,w))
    arr=band.ReadAsArray(0,0,w,h)
    return arr,proj,transform
 #band.DataType  图像中实际数值的数据类型，具体的数据类型定义在gdalconst模块里，需import

def CreatRaster(output_path,arr,proj,transform,nodata):
    #写栅格，将数组写成带有地理位置信息的tif数据
    driver=gdal.GetDriverByName('GTiff')
    h,w=np.shape(arr)
    driver.Register()
    oDS=driver.Create(output_path,w,h,1,GDT_Float32,['COMPRESS=DEFLATE'])
    outband1=oDS.GetRasterBand(1)
    for i in range(h):
        outband1.WriteArray(arr[i].reshape(1,-1),0,i) #可以直接写入整个矩阵吗？
    oDS.SetProjection(proj)
    oDS.SetGeoTransform(transform)
    outband1.FlushCache()
    outband1.SetNoDataValue(nodata)
    '''
    新建栅格数据集
    将刚才计算得到的数据写入新的栅格数据集之中
    首先要复制一份数据驱动：
    driver = inDataset.GetDriver()
    之后新建数据集
    Create(<filename>, <xsize>, <ysize>, [<bands>], [<GDALDataType>])
    其中bands的默认值为1，GDALDataType的默认类型为GDT_Byte，例如
    outDataset = driver.Create(filename, cols, rows, 1, GDT_Float32)
    在这条语句的执行过程中，存储空间已经被分配到硬盘上了
    在写入之前，还需要先引入波段对象
    outBand = outDataset.GetRasterBand(1)
    波段对象支持直接写入矩阵，两个参数分别为x向偏移和y向偏移
    outBand.WriteArray(ndvi, 0, 0)
    '''

def read_lc_HDF(landcover_file):
    path,hdf_file = os.path.split(landcover_file)
    name,ext=os.path.splitext(hdf_file)
    if ext!='.hdf':
        return
    name_list=name.split('.')
    list1 =[name_list[1][1:],name_list[2]] #2001001，h00v08
    name= ".".join(list1)
    
    ds = gdal.Open(landcover_file)
    subdatasets = ds.GetSubDatasets() #GetSubDatasets方法返回元组列表，每个子数据集有一个元组。每个元组按顺序包含子数据集的名称和描述。
    
    lc_type_ds=gdal.Open(subdatasets[0][0])

    proj= lc_type_ds.GetProjection()
    transform= lc_type_ds.GetGeoTransform()
    
    lc_path = path+"\\HDF_tif\\"
    if not os.path.exists(lc_path):
        os.mkdir(lc_path)
    temp_path =  path+"\\temp\\"
    if not os.path.exists(temp_path):
        os.mkdir(temp_path)
    lc_arr = lc_type_ds.ReadAsArray()
    lc_arr[np.where((lc_arr==13)|(lc_arr==16))]=23#表示建筑物
    lc_arr[np.where((lc_arr==15)|(lc_arr==17))]=22#表示水体
    lc_arr[np.where(lc_arr==11)]=21#表示湿地
    lc_arr[np.where((lc_arr==1)|(lc_arr==2)|(lc_arr==3)|(lc_arr==4)|(lc_arr==5)|(lc_arr==6)|(lc_arr==7)|(lc_arr==8)|(lc_arr==9)|(lc_arr==10))]=20#表示植被
    print(lc_arr)
    CreatRaster(temp_path+name+".tif",lc_arr,proj,transform,255)
    ds_evi=gdal.Open(temp_path+name+".tif")
    gdal.Warp(lc_path+name+".tif",ds_evi,xRes=926.6254331, yRes=926.6254331)#重采样
    #evi_arr_1 = readRaster(EVI_path+name+".tif")[0]
    ds_evi = None
    os.remove(temp_path+name+".tif")
    
def mosaic(data_list, out_path,nodata):

    # 读取其中一个栅格数据来确定镶嵌图像的一些属性
    o_ds = gdal.Open(data_list[0])
    # 投影
    Projection = o_ds.GetProjection()
    # 波段数据类型
    o_ds_array = o_ds.ReadAsArray() #没有详细的参数？？

    if 'int8' in o_ds_array.dtype.name: #数据类型不太懂
        datatype = gdal.GDT_Byte
    elif 'int16' in o_ds_array.dtype.name:
        datatype = gdal.GDT_UInt16
    else:
        datatype = gdal.GDT_Float32

    # 像元大小
    transform = o_ds.GetGeoTransform()
    pixelWidth = transform[1]
    pixelHeight = transform[5]

    del o_ds

    minx_list = []
    maxX_list = []
    minY_list = []
    maxY_list = []

    # 对于每一个需要镶嵌的数据，读取它的角点坐标
    for data in data_list:

        # 读取数据
        ds = gdal.Open(data)
        rows = ds.RasterYSize
        cols = ds.RasterXSize

        # 获取角点坐标
        transform = ds.GetGeoTransform()
        minX = transform[0]
        maxY = transform[3]
        pixelWidth = transform[1]
        pixelHeight = transform[5]  # 注意pixelHeight是负值
        maxX = minX + (cols * pixelWidth)
        minY = maxY + (rows * pixelHeight)

        minx_list.append(minX)
        maxX_list.append(maxX)
        minY_list.append(minY)
        maxY_list.append(maxY)

        del ds #不能覆盖的吗？需要每次都del吗？

    # 获取输出图像坐标
    minX = min(minx_list)
    maxX = max(maxX_list)
    minY = min(minY_list)
    maxY = max(maxY_list)

    # 获取输出图像的行与列
    cols = int(round((maxX - minX) / pixelWidth)) #要四舍五入的吗？
    rows = int(round((maxY - minY) / abs(pixelHeight)))# 注意pixelHeight是负值

    # 计算每个图像的偏移值
    xOffset_list = []
    yOffset_list = []
    i = 0

    for data in data_list:
        xOffset = int((minx_list[i] - minX) / pixelWidth) #取整会让相对位置不准吗？
        yOffset = int((maxY_list[i] - maxY) / pixelHeight)
        xOffset_list.append(xOffset)
        yOffset_list.append(yOffset)
        i += 1

    # 创建一个输出图像
    driver = gdal.GetDriverByName("GTiff")
    dsOut = driver.Create(out_path , cols, rows, 1, datatype) 
    bandOut = dsOut.GetRasterBand(1)
    bandOut.SetNoDataValue(nodata)

    i = 0
    #将原始图像写入新创建的图像
    for data in data_list:
        # 读取数据
        ds = gdal.Open(data)
        data_band = ds.GetRasterBand(1)
        data_rows = ds.RasterYSize
        data_cols = ds.RasterXSize

        data = data_band.ReadAsArray(0, 0, data_cols, data_rows)
        bandOut.WriteArray(data, xOffset_list[i], yOffset_list[i])
        

        del ds
        i += 1

    # 设置输出图像的几何信息和投影信息
    geotransform = [minX, pixelWidth, 0, maxY, 0, pixelHeight]
    dsOut.SetGeoTransform(geotransform)
    dsOut.SetProjection(Projection)
    bandOut.SetNoDataValue(0) #为什么有时候是0有时候是其他

    del dsOut
def clip(tif_file,shpfile,outpath,nodata):
    src_ds=gdal.Open(tif_file)
    gdal.Warp(outpath,src_ds,cutlineDSName=shpfile,srcNodata=nodata, dstNodata=nodata) #这个里面的参数类型还不太懂

def merge(sq_list,TA_path,out_path):
    """
    :param1 sq_list: 平台融合顺序
    :param2 TA_path:日平均气温影像所在路径
    :param3 out_path:平台融合后的气温数据输出路径
    """
    info_list = []
    for i in sq_list:
        if i == 12:
            l_type = 'MOD'
            time = 'night'
        elif i == 22:
            l_type = 'MYD'
            time = 'night'
        elif i == 11:
            l_type = 'MOD'
            time = 'day'
        else:
            l_type = 'MYD'
            time = 'day'
        list1=[l_type,time]
        info_list.append(list1)
    out_path1 = out_path + "type_merge\\"
    if not os.path.exists(out_path1):
        os.makedirs(out_path1)
    count = len(info_list)
    TA_path1=TA_path + (info_list[0])[0]+"_LST_to_TA\\" #I:\TA\DATA\out\MOD_LST_to_TA\
    for TA_file in os.listdir(TA_path1):
        name,ext=os.path.splitext(TA_file)
        if ext!='.tif':
            continue
        name_list = name.split('.')
        date = name_list[1]
        # time = name_list[-1]
        time = name_list[-2]
        if time != (info_list[0])[1]:
            continue
        TA_arr,proj,trans=readRaster(TA_path1+TA_file)
        for i in range(1,count):
            TA_file1=TA_path + (info_list[i])[0]+"_LST_to_TA\\" +(info_list[i])[0]+'.'+date+'.'+(info_list[i])[1]+".tif.tif" #加了一下下
            print(TA_file1)
            # I:\TA\DATA\out\MOD_LST_to_TA\MOD.2010001.night.tif.tif
            if os.path.exists(TA_file1):
                TA_arr1,proj,trans=readRaster(TA_file1)
            else:
                TA_arr1=np.zeros_like(TA_arr)
            TA_arr[TA_arr==0]=TA_arr1[TA_arr==0] #有改动
            # print(TA_arr)
        outname = out_path1+date+".tif"
        CreatRaster(outname,TA_arr, proj, trans,0)


def getCloudyPercent(TA_path,lc_path,year,CloudThreshold):
    """
    :param1 TA_path: 气温数据所在目录
    :param2 year: 需要插补的LST数据的年份
    :param3 CloudThreshold: 云量阈值
    :param4 mask_file:掩膜文件
    :param4 type:搭载的卫星种类
    :param5 lst_time: lst成像时间，lst_time=0表示白天，lst_time=1表示夜间
    :param6 select_type: 质量筛选办法，等于或不等于1。等于1表示高质量筛选，不等于1表示有效值筛选
    
    return 参考影像日期数组
    """
    lc_file = lc_path + str(year*1000+1)+".tif"
    lc_arr,proj,trans = readRaster(lc_file)
    total_pixel = np.sum(lc_arr!=255)
    #求每个路径下的不同传感器参考参考影像的覆盖率    
    useful_date=[]
    for TA_file in os.listdir(TA_path):#返回指定的文件夹包含的文件或文件夹的名字的列表。这个列表以字母顺序
        name,ext=os.path.splitext(TA_file)  # 将文件名和扩展名分开
        if ext==".tif" :
            file_date = int((name.split('.')[0]))#根据文件名获取日期
            TA_arr,proj,trans = readRaster(TA_path+TA_file)
            #计算有效像元覆盖度
            pixel_sum=np.sum(TA_arr!=0)
            percent=1.0*pixel_sum/total_pixel
            if percent>=CloudThreshold:
                useful_date.append(file_date)
                print ("%s is more than %f" %(TA_file,CloudThreshold))
        else:
            continue
    return np.array(useful_date)


def getreferencedate(date,referencedate):#文件下LST与所有少云的参考LST影像的时间比较
    """
    :param1 date:待插值影像日期
    :param2 referencedate:参考影像列表
    return 距离应待插值影像最近的参考影像日期
    """
    #两个日期所间隔的天数
    diff=np.abs((referencedate//1000-date//1000)*365+referencedate%1000-date%1000)#前面是年份，后面是天数
    
    mindiff=np.min(diff)#所有影像与参考影像相距时间最短
    if mindiff==0:#参考影像与待比较影响是同一幅影像
        return 0
    if mindiff>30:#最短时间超过30天
        step=1
        mindiff1=40
        while mindiff1>30:
            #挑出相距一年的参考影像的日期
            subreferencelist=referencedate[np.abs(referencedate//1000-date//1000)==step]
            diff1=np.abs(subreferencelist%1000-date%1000)#相差一年的影像相差的天数
            mindiff1=np.min(diff1)#天数最小
            if mindiff1<=30:#最小天数小于30天
                return subreferencelist[diff1==mindiff1][0]#第二年相距最近
            else:
                step+=1
                return 0 #不懂这里的效果是什么
    return  referencedate[diff==mindiff][0]#一年内相距最近  

def TA_interpolation(reference_Lst_arr,interpolate_LST_arr,lc_arr): 
    inter_arr = np.zeros_like(reference_Lst_arr)
    for i in [20,21,22,23]:
        con_w=(reference_Lst_arr!=0)&(interpolate_LST_arr!=0)&(lc_arr==i) 
        # diff_w = reference_Lst_arr[con_w] - interpolate_LST_arr[con_w]#求差值

        diff_w = reference_Lst_arr - interpolate_LST_arr
        diff_w[con_w==False]=0

        con_w1=(reference_Lst_arr!=0)&(interpolate_LST_arr==0)&(lc_arr==i)
        # print(inter_arr.shape,reference_Lst_arr.shape,interpolate_LST_arr.shape,diff_w.shape,lc_arr.shape)
        inter_arr[con_w1] = reference_Lst_arr[con_w1] - diff_w[con_w1]
        con=(interpolate_LST_arr!=0)&(lc_arr==i) 
        inter_arr[con]=interpolate_LST_arr[con]
    return inter_arr


import sys
import shutil
def main(argv):
    import argparse 
    DESC = "interpolate the missing values of TA data"   
    parser = argparse.ArgumentParser(prog=argv[0], description=DESC)
    parser.add_argument('-start', '--start', dest='start', metavar='Number', help='start year', required=True)
    parser.add_argument('-end', '--end', dest='end', metavar='Number', help='end year', required=True)
    parser.add_argument('-TA', '--TA', dest='TA', metavar='DIR', help='Input path of TA data',required=True)
    parser.add_argument('-lc', '--landcover', dest='lc', metavar='DIR', help='Input path of landcover',required=True)
    parser.add_argument('-shp', '--shpfile', dest='shp', metavar='DIR', help='Input path of vector boundary file', required=True)
    parser.add_argument('-out', '--out', dest='out', metavar='DIR', help='Storage path of TA data after interpolation', required=True)
    parser.add_argument('-tile', '--tile', dest='tile', metavar='list',default=['h28v06','h28v05'], help="Tile list of LST data,default is ['h28v06','h28v05']")
    parser.add_argument('-sq_list', '--sq_list', dest='sq_list', metavar='list',default=[12,22,11,21], help="Platform merge sequence,1for MOD and day,2 for MYD and night. default is [12,22,11,21]")
    parser.add_argument('-Th', '--Threshold', dest='CloudThresholde', metavar='Number',default='0.6', help="Cloud cover threshold,default is 0.6")
    
    
    args = parser.parse_args(argv[1:])
    
    year_start = eval(args.start)#开始年份
    year_end = eval(args.end)
    
    TA_path = args.TA
    if not os.path.exists(TA_path):
        print("输入的气温数据不存在，请检查！！！")
        os._exit(0)
            
    lc_path = args.lc
    if not os.path.exists(lc_path):
        print("输入的植被指数数据不存在，请检查！！！")
        os._exit(0)
        
    shpfile = args.shp
    if not os.path.exists(shpfile):
        print("输入的矢量边界数据不存在，请检查！！！")
        os._exit(0)
            
    out_path = args.out
    if not os.path.exists(out_path):
        print ('here1')
        os.makedirs(out_path)
    tile_list = eval(args.tile) 
    sq_list = eval(args.sq_list)
    if len(sq_list)<1 or len(sq_list)>4:
        print ("平台融合顺序输入不符合要求，请检查！")
    cloudThreshold = eval(args.CloudThresholde)
    merge(sq_list,TA_path,out_path)#进行平台融合
    print ("平台融合完成")
    for hdf_file in os.listdir(lc_path):
        read_lc_HDF(lc_path+hdf_file)  # I:\TA\DATA\landcover\MCD12Q1.A2010001.h28v05.006.2018054202115.hdf
    tif_path = lc_path+"HDF_tif\\"

    mosaic_path = lc_path+'mosaic\\'
    if not os.path.exists(mosaic_path):
        os.makedirs(mosaic_path)
    for year in range(year_start,year_end+1):
        lc_list=[]
        for tile in tile_list:
            TA_file = tif_path +str(year*1000+1)+"."+tile+".tif"
            if not os.path.exists(TA_file):
                break
            lc_list.append(TA_file)
        out=mosaic_path+str(year*1000+1)+".tif"

        mosaic(lc_list, out,255)
        print(TA_file + "镶嵌结束")
        
    out =lc_path+"clip\\"
    if not os.path.exists(out):
        os.makedirs(out)
    for tif_file in os.listdir(mosaic_path):
        name,ext=os.path.splitext(tif_file)
        if ext!='.tif':
            continue
        clip(mosaic_path+tif_file,shpfile,out+tif_file,255)

    for year in range(year_start,year_end+1): 
        out_path1 = out_path+str(year)+"\\" # I:\TA\DATA\TA_interpolation\2010\
        if not os.path.exists(out_path1):
            os.makedirs(out_path1)
        ref_date_list = getCloudyPercent("I:\\TA\\DATA\\TA_interpolation\\type_merge\\", out, year, cloudThreshold)
        for TA_file in os.listdir(out_path + "type_merge\\"): 
            name_list = TA_file.split('.')
            null_date = name_list[0] #2010001
            null_year = int(null_date[:4])
            if  name_list[-1] =='tif' and null_year==year:
                null_arr,proj,transform = readRaster(out_path+"type_merge\\"+TA_file)
                ref_date=getreferencedate(int(null_date), ref_date_list)
                if ref_date==0:#即本次就是参考影像
                    dst=out_path1+TA_file
                    CreatRaster(dst,null_arr,proj,transform,0)
                    continue
                ref_file = out_path+"type_merge\\" + str(ref_date)+".tif"
                reference_arr,proj,transform = readRaster(ref_file)
                lc_file = lc_path+"clip\\"+str(year*1000+1)+".tif"
                lc_arr,proj,transform = readRaster(lc_file)
                interpolation_arr = TA_interpolation(reference_arr,null_arr,lc_arr)
                dst=out_path1+str(year*1000+int(null_date))+".tif"
                CreatRaster(dst,interpolation_arr,proj,transform,0)
    #删除中间文件
    shutil.rmtree(lc_path+"clip\\")
    shutil.rmtree(mosaic_path)
    print ("气温插补完成")
      
if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv))
    except KeyboardInterrupt:
        sys.exit(-1)
    sys.exit(0)
        
    
    
