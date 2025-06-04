import os

# os.chdir(r'C:\Users\dell\Nutstore\1\我的坚果云\Data')
# cmd_str = 'gdaldem slope srtm_h28v06.tif slope_h28v0690m.tif'
# os.system(cmd_str)

os.chdir(r'E:\LST\surface_data\dem')
cmd_str = 'gdaldem aspect zhejiang_dem.tif zhejiang_aspect.tif'
os.system(cmd_str)