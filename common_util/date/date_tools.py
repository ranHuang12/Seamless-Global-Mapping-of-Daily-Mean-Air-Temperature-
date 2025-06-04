import calendar
import time
from datetime import datetime, timedelta, date

from common_object.entity import ModisDate


# def get_interval_modis_date(date, interval):
#     year = int(date/1000)
#     new_date = date+interval
#     while new_date > year*1000+get_day_num(year):
#         new_date += 1000-get_day_num(year)
#         year += 1
#     while new_date < year*1000+1:
#         new_date += get_day_num(year-1)-1000
#         year -= 1
#     return new_date


def get_interval_date(modis_date, interval):
    modis_date = int(modis_date)
    interval_date = (date(modis_date // 1000, 1, 1) + timedelta(modis_date % 1000 + int(interval) - 1))
    return interval_date.year * 1000 + interval_date.timetuple().tm_yday


# def get_modis_date_interval(start_date, end_date):
#     if start_date > end_date:
#         return -get_modis_date_interval(end_date, start_date)
#     interval = 0
#     for year in range(int(start_date/1000), int(end_date/1000)):
#         interval += get_day_num(year)
#     return interval + end_date % 1000 - start_date % 1000


def get_date_interval(start_date, end_date):
    start_date = int(start_date)
    end_date = int(end_date)
    return (date(end_date // 1000, 1, 1) + timedelta(end_date % 1000) - date(start_date // 1000, 1, 1) - timedelta(start_date % 1000)).days


def get_all_modis_date_by_year(year, start_doy=1, end_doy=366):
    year = int(year)
    start_doy = int(start_doy)
    end_doy = int(end_doy)
    return [ModisDate().parse_datetime_date(date(year, 1, 1) + timedelta(doy)) for doy in range(start_doy - 1, min(get_day_num_by_year(year), end_doy))]


def get_all_date_by_year(year, start_doy=1, end_doy=366):
    year = int(year)
    start_doy = int(start_doy)
    end_doy = int(end_doy)
    return [year * 1000 + doy for doy in range(start_doy, min(get_day_num_by_year(year), end_doy) + 1)]


def get_all_date_by_month(year, month, start_dom=1, end_dom=31):
    first_date = date(year, month, 1)
    return [first_date.year*1000+first_date.timetuple().tm_yday + dom for dom in range(start_dom-1, min(get_day_num_by_month(year, month), end_dom))]


def get_day_num_by_year(year):
    return 366 if calendar.isleap(year) else 365


def get_day_num_by_month(year, month):
    return calendar.monthrange(year, month)[1]


def main():
    print(type(get_day_num_by_month(2020, 1)))


if __name__ == "__main__":
    main()
