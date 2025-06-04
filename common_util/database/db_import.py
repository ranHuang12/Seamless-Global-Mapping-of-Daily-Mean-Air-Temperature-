import csv
import os

from db_operation import db_select
from db_operation import db_insert
from db_operation import db_update
# from default_render_tools import get_default_settings


def get_cog_tile_new_value(keyword):
    cog_tile_new_dict = {
        '1小时降雨量': [5, '[20,30,40,50]', '["3DBA3D","61B8FF","0000FF","FF00FF","800040"]', 'manual_grade'],
        '1日降雨量': [5, '[25,50,100,250]', '["3DBA3D","61B8FF","0000FF","FF00FF","800040"]', 'manual_grade'],
        '过程降雨量': [6, '[10,25,50,100,250]', '["A6F28F","3DBA3D","61B8FF","0000FF","FF00FF","800040"]', 'manual_grade'],
        '年小时降雨量极大值': [5, '[20,30,40,50]', '["3DBA3D","61B8FF","0000FF","FF00FF","800040"]', 'manual_grade'],
        '年日降雨量极大值': [5, '[25,50,100,250]', '["3DBA3D","61B8FF","0000FF","FF00FF","800040"]', 'manual_grade'],
        '小时最大降雨量': [6, '[20,40,60,80,100]', '["A6F28F","3DBA3D","61B8FF","0000FF","FF00FF","800040"]', 'manual_grade'],
        '日最大降雨量': [7, '[50,100,150,200,250,300]', '["A6F28F","3DBA3D","61B8FF","0000FF","FF00FF","800040"]', 'manual_grade'],
        '尾矿库': [1, '[0]', '["CC6600"]', 'manual_classify'],
        '水库': [1, '[0]', '["3399FF"]', 'manual_classify'],
        '火车站': [1, '[0]', '["9933CC"]', 'manual_classify'],
        '机场': [1, '[0]', '["3333FF"]', 'manual_classify'],
        '医疗机构': [1, '[0]', '["FFCCCC"]', 'manual_classify'],
        '客运车站': [1, '[0]', '["FFCC66"]', 'manual_classify'],
        '学校': [1, '[0]', '["FFCC66"]', 'manual_classify'],
        '生命线工程单位': [1, '[0]', '["FF3300"]', 'manual_classify'],
        '大型企业': [1, '[0]', '["66FF66"]', 'manual_classify'],
        '仓储单位': [1, '[0]', '["FFCC66"]', 'manual_classify'],
        '危化企业': [1, '[0]', '["FFCC66"]', 'manual_classify'],
        '旅游文化单位': [1, '[0]', '["66FF66"]', 'manual_classify'],
        '小麦格点化': [1, 'null', '["BuGn"]', 'stretch'],
        '玉米格点化': [1, 'null', '["YlOrBr"]', 'stretch'],
        '人口': [5, '[500,1000,5000,10000]', '["00CCFF","00CC33","FFFF66","FFCC66","FF3333"]', 'manual_grade'],
        'GDP': [6, 'null', '["66CCFF","66CC99","66FF99","FFFF66","FFCC66","FF3333"]', 'quartile_grade'],
        '地质灾害隐患点': [1, '[0]', '["FF9900"]', 'manual_classify'],
        '城市易积涝点': [1, '[0]', '["33FFCC"]', 'manual_classify'],
        '山洪沟': [1, '[0]', '["CCCC99"]', 'manual_classify'],
        '地理国情总图': [12, '[1,2,3,4,5,6,7,8,9,10,11,12]', '["D7FFEE","00DB00","006030","FFFFCE","FF79BC","7B7B7B","FFA042","BBFFFF","FF9797","CA8EFF","84C1FF","6A6AFF"]', 'manual_classify'],
        '耕地': [1, 'null', '["BuGn"]', 'stretch'],
        '园地': [1, 'null', '["BuGn"]', 'stretch'],
        '林地': [1, 'null', '["BuGn"]', 'stretch'],
        '草地': [1, 'null', '["BuGn"]', 'stretch'],
        '商服用地': [1, 'null', '["YlOrBr"]', 'stretch'],
        '工矿仓储用地': [1, 'null', '["YlOrBr"]', 'stretch'],
        '住宅用地': [1, 'null', '["YlOrBr"]', 'stretch'],
        '公共管理与公共服务用地': [1, 'null', '["YlOrBr"]', 'stretch'],
        '特殊用地': [1, 'null', '["YlOrBr"]', 'stretch'],
        '交通运输用地': [1, 'null', '["YlOrBr"]', 'stretch'],
        '水域及其他水利设施用地': [1, 'null', 'null', 'stretch'],
        '其他土地': [1, 'null', '["YlOrBr"]', 'stretch'],
        '村庄': [1, 'null', '["YlOrBr"]', 'stretch'],
        '水系': [1, '[0]', '["84C1FF"]', 'manual_classify'],
        '国道': [1, '[0]', '["FF9933"]', 'manual_classify'],
        '高速': [1, '[0]', '["CC9933"]', 'manual_classify'],
        '省道': [1, '[0]', '["999999"]', 'manual_classify'],
        '快速路': [1, '[0]', '["CCCC33"]', 'manual_classify'],
        '专用公路': [1, '[0]', '["660033"]', 'manual_classify'],
        '乡道': [1, '[0]', '["33CC66"]', 'manual_classify'],
        '县道': [1, '[0]', '["669900"]', 'manual_classify'],
        '村道': [1, '[0]', '["9999CC"]', 'manual_classify'],
        '坡度': [5, '[0,0.2,0.4,0.6,0.8]', '["FFFF66","009966","00FF66","006699","CC0000"]', 'quartile_grade'],
        '坡向': [10, '[0,22.5,67.5,112.5,157.5,202.5,247.5,292.5,337.5]', '["999999","FF0000","FF6600","FFFF00","33FF00","33FFFF","3399FF","0000FF","FF00FF","FF0000"]', 'manual_grade'],
        'DEM数据': [1, 'null', '["RdYlGn_r"]', 'stretch'],
        '灾害监测点': [1, '[0]', '["FF9999"]', 'manual_classify'],
        '人影作业点': [1, '[0]', '["FF9900"]', 'manual_classify'],
        '应急避难场所': [1, '[0]', '["33CC33"]', 'manual_classify'],
        '预警终端设备布点': [1, '[0]', '["FF9900"]', 'manual_classify'],
        '直接经济损失': [3, 'null', '["33CC33","FF9933","FF0000"]', 'natural_grade'],
        '农业经济损失': [3, 'null', '["33CC33","FF9933","FF0000"]', 'natural_grade'],
        '经济作物损失': [3, 'null', '["33CC33","FF9933","FF0000"]', 'natural_grade'],
        '倒塌房屋数量': [3, 'null', '["33CC33","FF9933","FF0000"]', 'natural_grade'],
        '农作物受灾面积': [1, '[0]', '["33CC33"]', 'manual_classify'],
        '农作物成灾面积': [1, '[0]', '["FF9933"]', 'manual_classify'],
        '农作物绝收面积': [1, '[0]', '["FF0000"]', 'manual_classify'],
        '因灾减产粮食': [3, 'null', '["33CC33","FF9933","FF0000"]', 'natural_grade'],
        '受灾人口': [3, 'null', '["33CC33","FF9933","FF0000"]', 'natural_grade']
    }
    key = keyword.split(',')[0]
    if '（' in key:
        key = key[:key.find('（')]
    if key in cog_tile_new_dict:
        value = cog_tile_new_dict[key]
        return value[0], value[1], value[2], value[3]
    else:
        return 0, 0, 0, 0


def cog_tile_new_import(csv_path, txt_path):
    with open(csv_path, 'w', newline='') as f:
        records = db_select('*', 'layerid_desc', r"file_type = 'tif' and resolution = 1000 and file_path like '%GPS_MDPD\\output_data%' and file_path not like '%\\XSJYL\\%' and file_path not like '%\\RJYL\\%'")
        writer = csv.writer(f)
        writer.writerows(records)
    with open(csv_path) as f1:
        reader = csv.reader(f1)
        with open(txt_path, 'w') as f2:
            f2.write('{')
            for row in reader:
                url = row[3]
                print(url)
                if 'QXZQ' not in url:
                    key = row[8]
                    rank, interrupts, colors, rmethod = get_cog_tile_new_value(key)
                else:
                    key = row[1].split('-')[1]
                    rank, interrupts, colors, rmethod = get_cog_tile_new_value(key)
                # rank, rmethod, interrupts, colors = get_default_settings(url)
                if rank != 0:
                    if db_select('count(*)', 'cog_tile_new', "url = '%s'" % url)[0][0] == 0:
                        db_insert('cog_tile_new', 'url, rank, interrupts, colors, rmethod', "'%s', %s, '%s', '%s', '%s'" % (url, rank, interrupts, colors, rmethod))
                    else:
                        db_update('cog_tile_new', "rank = %s, interrupts = '%s', colors = '%s', rmethod = '%s'" % (rank, interrupts, colors, rmethod), "url = '%s'" % url)
                else:
                    print('\033[31;1mno match in dict\033[0m')


def main():
    csv_path = os.path.join(module_path, 'files_to_yuqie.csv')
    txt_path = os.path.join(module_path, 'default_render_settings.txt')
    cog_tile_new_import(csv_path, txt_path)


if __name__ == '__main__':
    module_path = os.path.dirname(os.path.dirname(__file__))
    main()
