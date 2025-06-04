import time

import pandas as pd
import requests
import json
import os

from common_util.common import concurrent_execute
from common_util.date import get_all_modis_date_by_year, get_day_num_by_month
from common_util.document import to_csv, merge_csv
from common_util.path import create_path
from data_download.path import Path


def get_url_by_tile(path: Path, product, collection, year, tile, aoi, retry=None, lock=None):
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    headers = {
        'Connection': 'keep-alive',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
        'Accept': '*/*',
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua-mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': f'https://ladsweb.modaps.eosdis.nasa.gov/search/order/4/{product}--{collection}/{start_date}..{end_date}/DB/Tile:{tile}',
        'Accept-Language': 'zh-CN,zh;q=0.9,sq;q=0.8,de;q=0.7',
        'Cookie': '_ga=GA1.2.185083279.1621347950; _gid=GA1.2.998367911.1621347950; _ga=GA1.5.185083279.1621347950; _gid=GA1.5.998367911.1621347950; _gat_UA-112998278-15=1; _gat_GSA_ENOR0=1',
    }
    url_path = os.path.join(path.cloud_url_path, product)
    create_path(url_path)
    try_round = 0
    url_df_list = []
    while True:
        try:
            url_df_list = []
            response = requests.get(
                f'https://ladsweb.modaps.eosdis.nasa.gov/api/v1/files/product={product}&collection={collection}&dateRanges={start_date}..{end_date}&areaOfInterest={aoi}&dayCoverage=true&dnboundCoverage=true',
                headers=headers)
            data = json.loads(response.text)
            if data:
                for k, v in data.items():
                    filename = v["name"]
                    if filename.split(".")[2] == tile:
                        date = filename.split(".")[1][1:]
                        url_df_list.append(pd.DataFrame({
                            "year": [date[:4]],
                            "date": [date],
                            "filename": [filename],
                            "filesize": [v["size"]],
                            "url": [f"https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/{collection}/{product}/{year}/{date[4:]}/{filename}"]
                        }))
            break
        except Exception as e:
            print(e)
            time.sleep(3)
            try_round += 1
            if retry is not None and try_round >= retry:
                break
    if url_df_list:
        url_file = os.path.join(url_path, f"{tile}.csv")
        to_csv(pd.concat(url_df_list, ignore_index=True), url_file)
        url_df = pd.read_csv(url_file)
        to_csv(url_df.drop_duplicates("date").sort_values("date"), url_file, False)
    count = len(url_df_list)
    to_csv(pd.DataFrame({"tile": [tile], year: [count]}), os.path.join(path.cloud_url_path, f"{product}_World_count_{year}.csv"), lock=lock)
    print(f"{product} {tile} {year} {count}")


def get_url_by_region(path: Path, product, collection, year, region="World", aoi="x-180y90,x180y-90", lock=None):
    url_path = os.path.join(path.cloud_url_path, product)
    create_path(url_path)
    url_df_dict = {}
    start_month = 2 if (product.startswith("MOD") and year == 2000) else (7 if product.startswith("MYD") and year == 2002 else 1)
    for month in range(start_month, 13):
        start_date = f"{year}-{str(month).zfill(2)}-01"
        end_date = f"{year}-{str(month).zfill(2)}-{get_day_num_by_month(year, month)}"
        headers = {
            'Connection': 'keep-alive',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
            'Accept': '*/*',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': f'https://ladsweb.modaps.eosdis.nasa.gov/search/order/4/{product}--{collection}/{start_date}..{end_date}/DB/{region}',
            'Accept-Language': 'zh-CN,zh;q=0.9,sq;q=0.8,de;q=0.7',
            'Cookie': '_ga=GA1.2.185083279.1621347950; _gid=GA1.2.998367911.1621347950; _ga=GA1.5.185083279.1621347950; _gid=GA1.5.998367911.1621347950; _gat_UA-112998278-15=1; _gat_GSA_ENOR0=1',
        }
        try_round = 0
        while True:
            try:
                response = requests.get(
                    f'https://ladsweb.modaps.eosdis.nasa.gov/api/v1/files/product={product}&collection={collection}&dateRanges={start_date}..{end_date}&areaOfInterest={aoi}&dayCoverage=true&dnboundCoverage=true',
                    headers=headers)
                data = json.loads(response.text)
                for k, v in data.items():
                    filename = v['name']
                    date = filename.split(".")[1][1:]
                    tile = filename.split(".")[2]
                    url_df_list = url_df_dict[tile] if tile in url_df_dict.keys() else []
                    url_df_list.append(pd.DataFrame({
                        "year": [date[:4]],
                        "date": [date],
                        "filename": [filename],
                        "filesize": [v["size"]],
                        "url": [
                            f"https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/{collection}/{product}/{year}/{date[4:]}/{filename}"]
                    }))
                    url_df_dict[tile] = url_df_list
                print(year, month, len(data))
                break
            except Exception as e:
                print(e)
                time.sleep(3)
                try_round += 1
                    # if try_round >= 3:
                    #     break
    for tile, url_df_list in url_df_dict.items():
        if url_df_list:
            url_file = os.path.join(url_path, f"{tile}.csv")
            if os.path.isfile(url_file):
                url_df = pd.concat([pd.read_csv(url_file)]+url_df_list, ignore_index=True)
                url_df.drop_duplicates("filename", inplace=True)
                to_csv(url_df, url_file, False)
            else:
                to_csv(pd.concat(url_df_list, ignore_index=True), url_file)
        count = len(url_df_list)
        to_csv(pd.DataFrame({"tile": [tile], year: [count]}), os.path.join(path.cloud_url_path, f"{product}_World_count_{year}.csv"), lock=lock)


def get_url(path: Path, year_list, product_list, pool_size=1):
    collection = '61'
    tile_df = pd.read_csv(os.path.join(path.cloud_modis_data_path, "land_tile_list.csv"))
    tile_df = tile_df[tile_df["count"] >= 0]
    tile_df = tile_df[tile_df["vi"] == 1]
    for year in year_list:
        for product in product_list:
            count_year_csv = os.path.join(path.cloud_url_path, f"{product}_World_count_{year}.csv")
            finish_tile_list = []
            if os.path.isfile(count_year_csv):
                finish_tile_list = list(pd.read_csv(count_year_csv)["tile"].values)
            args_list = []
            for index, row in tile_df.iterrows():
                tile = row["tile"]
                if tile in finish_tile_list:
                    continue
                args_list.append([path, product, collection, year, tile, row["aoi"], None])
            concurrent_execute(get_url_by_tile, args_list, pool_size)
    # args_list = []
    # for product in product_list:
    #     for year in year_list:
    #         args_list.append([path, product, collection, year, "World", "x-180y90,x180y-90"])
    # concurrent_execute(get_url_by_region, args_list, pool_size)
    for product in product_list:
        for year in year_list:
            count_csv = os.path.join(path.cloud_url_path, f"{product}_World_count.csv")
            count_year_csv = os.path.join(path.cloud_url_path, f"{product}_World_count_{year}.csv")
            merge_csv(count_csv, count_year_csv, "tile", "outer")


def main():
    path = Path()
    year_list = list(range(2020, 2023))
    year_list = [2019, 2023]
    product_list = ["MOD13A2", "MYD13A2"]
    get_url(path, year_list, product_list, 4)


if __name__ == '__main__':
    main()
