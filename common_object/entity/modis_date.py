import time
from datetime import timedelta, date


class ModisDate(object):
    def __init__(self):
        self.py_date = None

    def __fill_field(self):
        self.year = self.py_date.year
        self.month = self.py_date.month
        self.day = self.py_date.day
        self.doy = self.py_date.timetuple().tm_yday
        self.modis_date = self.year * 1000 + self.doy
        self.eight_bit_date = self.year * 10000 + self.month * 100 + self.day
        return self

    def parse_datetime_date(self, py_date):
        self.py_date = py_date
        return self.__fill_field()

    def parse_modis_date(self, modis_date):
        modis_date = int(modis_date)
        self.py_date = date(modis_date // 1000, 1, 1) + timedelta(modis_date % 1000 - 1)
        return self.__fill_field()

    def parse_year_month_day(self, year, month, day):
        self.py_date = date(year, month, day)
        return self.__fill_field()

    def parse_eight_bit_date(self, eight_bit_date):
        eight_bit_date = int(eight_bit_date)
        return self.parse_year_month_day(eight_bit_date // 10000, (eight_bit_date % 10000) // 100, eight_bit_date % 100)

    def parse_separated_date(self, separated_date, separator):
        year, month, day = str(separated_date).split(separator)
        return self.parse_year_month_day(int(year), int(month), int(day))

    def to_separated_date(self, separator):
        return f"{self.year}{separator}{str(self.month).zfill(2)}{separator}{str(self.day).zfill(2)}"

    def __str__(self):
        return f"{self.modis_date} {self.eight_bit_date}"


def main():
    modis_date = ModisDate().parse_eight_bit_date(20220731)
    print(modis_date)


if __name__ == "__main__":
    main()
