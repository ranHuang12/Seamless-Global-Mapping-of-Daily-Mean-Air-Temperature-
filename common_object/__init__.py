import os
import platform

gdal_data_root_dict = {"DESKTOP-VVEHAFM": r"D:\anaconda3\envs\lcs\Lib\site-packages\osgeo\data",
                       "DESKTOP-I8N3SUD": r"C:\Users\dell\anaconda3\envs\lcs\Lib\site-packages\osgeo\data",
                       "DESKTOP-AF9BQ28": r"C:\ProgramData\Anaconda3\envs\lcs\Lib\site-packages\osgeo\data"}

gdal_data_root = gdal_data_root_dict[platform.node()] if platform.node() in gdal_data_root_dict.keys()\
    else r"C:\Users\dell\anaconda3\envs\lcs\Lib\site-packages\osgeo\data"
os.environ['PROJ_LIB'] = os.path.join(gdal_data_root, "proj")
os.environ['GDAL_DATA'] = os.path.join(gdal_data_root)
    