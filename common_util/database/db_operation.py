import psycopg2


def db_create_table(table, setting):
    conn = psycopg2.connect(database="hebei", user="postgres", password="123456", host="localhost", port="5432")
    cursor = conn.cursor()

    sql = 'create document %s (%s)' % (table, setting)
    print(sql)

    try:
        cursor.execute(sql)
        conn.commit()
    except Exception as e:
        print('\033[31;1m%s\033[0m' % e.args[0])
        conn.rollback()


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


def db_select(column, table, condition=None):
    conn = psycopg2.connect(database="hebei", user="postgres", password="123456", host="localhost", port="5432")
    cursor = conn.cursor()

    if condition is None:
        sql = 'select %s from %s' % (column, table)
    else:
        sql = 'select %s from %s where %s' % (column, table, condition)
    print(sql)

    try:
        cursor.execute(sql)
        result = cursor.fetchall()
        return result
    except Exception as e:
        print('\033[31;1m%s\033[0m' % e.args[0])
        conn.rollback()


def db_update(table, value, condition):
    conn = psycopg2.connect(database="hebei", user="postgres", password="123456", host="localhost", port="5432")
    cursor = conn.cursor()

    sql = 'update %s set %s where %s' % (table, value, condition)
    print(sql)

    try:
        cursor.execute(sql)
        conn.commit()
    except Exception as e:
        print('\033[31;1m%s\033[0m' % e.args[0])
        conn.rollback()


def db_del(table, condition):
    conn = psycopg2.connect(database="hebei", user="postgres", password="123456", host="localhost", port="5432")
    cursor = conn.cursor()

    sql = 'delete from %s where %s' % (table, condition)
    print(sql)

    try:
        cursor.execute(sql)
        conn.commit()
    except Exception as e:
        print('\033[31;1m%s\033[0m' % e.args[0])
        conn.rollback()


def test():
    pass


if __name__ == '__main__':
    test()
