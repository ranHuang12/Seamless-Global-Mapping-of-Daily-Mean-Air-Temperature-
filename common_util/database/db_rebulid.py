import csv
from db_operation import db_create_table
from db_operation import db_insert


def rebulid_layerid_desc(csv_path):
    try:
        db_create_table("public.layerid_desc", "id int4 default nextval('layerid_desc_id_seq'::regclass) not null,"
                                        "file_name text,"
                                        "file_type text,"
                                        "file_path text,"
                                        "resolution int4,"
                                        "year_num int4,"
                                        "month_num int4,"
                                        "date_time date,"
                                        "keyword text,"
                                        "jsonpath text,"
                                        "primary key(id)")
    except:
        pass
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            for i in range(1, 10):
                if not row[i]:
                    row[i] = 'null'
            if row[7] != 'null':
                db_insert('layerid_desc',
                          "file_name, file_type, file_path, resolution, year_num, month_num, date_time, keyword, jsonpath",
                          "'%s', '%s', '%s', %s, %s, %s, '%s', '%s', '%s'" % (row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]))
            else:
                db_insert('layerid_desc',
                          "file_name, file_type, file_path, resolution, year_num, month_num, date_time, keyword, jsonpath",
                          "'%s', '%s', '%s', %s, %s, %s, %s, '%s', '%s'" % (row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]))


def rebulid_cog_tile_new(csv_path):
    try:
        db_create_table("public.cog_tile_new", "url text not null,"
                                               "rank int4,"
                                               "interrupts text,"
                                               "colors text,"
                                               "rmethod text,"
                                               "nodata_value text,"
                                               "color_dict text,"
                                               "primary key(url)")
    except:
        pass
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            db_insert('cog_tile_new',
                      "url, rank, interrupts, colors, rmethod, nodata_value, color_dict",
                      "'%s', %s, '%s', '%s', '%s', '%s', '%s'" % (row[0], row[1], row[2], row[3], row[4], row[5], row[6]))


def main():
    # csv_path = r'E:\Project_of_Hebei\DataBase\layerid_desc(2).csv'
    # rebulid_layerid_desc(csv_path)
    csv_path2 = r'E:\Project_of_Hebei\DataBase\cog_tile_new.csv'
    rebulid_cog_tile_new(csv_path2)


if __name__ == '__main__':
    main()
