import os
import psycopg2


def db_insert(table, column_list, value_list):
    conn = psycopg2.connect(database="hebei", user="postgres", password="123456", host="localhost", port="5432")
    cursor = conn.cursor()

    sql = 'insert into %s (%s) values (%s)' % (table, column_list, value_list)
    print(sql)

    try:
        cursor.execute(sql)
        conn.commit()
    except Exception as e:
        print('\033[31;1m%s\033[0m' % e.args[0])
        conn.rollback()


def insert_record(file_path):
    file_name = os.path.basename(file_path)
    file_type = file_name.split(".")[-1]
    if file_type in ["shp", "csv", "tif", "grd"]:
        db_insert("layerid_desc", "'file_name', 'file_type', 'file_path'", "%s, %s, %s" % (file_name, file_type, file_path))
    else:
        return


def get_files(parent_directory):
    paths = os.listdir(parent_directory)
    for path in paths:
        if os.path.isfile(path):
            insert_record(path)
        else:
            get_files(path)


if __name__ == "__main__":
    get_files(r"D:\GPS_MDPD\user_data\lother's_code")
