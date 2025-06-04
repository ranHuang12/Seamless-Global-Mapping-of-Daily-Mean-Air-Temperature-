import os
import shutil
import ssl
from urllib.error import HTTPError, URLError
from urllib.request import urlopen, Request

import pandas as pd

from common_object.enum import RegionEnum
from common_util.common import convert_to_list, concurrent_execute, get_world_tile
from common_util.path import create_path
from data_download.path import Path


def exclude_finished_url(path: Path, url_df, product, tile):
    finished_url_file = os.path.join(path.cloud_url_path, "download_in_2021", product, f"{tile}.csv")
    if os.path.isfile(finished_url_file):
        finished_url_df = pd.read_csv(finished_url_file)
        filename_list = list(finished_url_df["filename"].values)
        url_df = url_df[~url_df["filename"].isin(filename_list)]
    return url_df


def download_url(path: Path, product, tile, year):
    headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
               "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJvcmlnaW4iOiJFYXJ0aGRhdGEgTG9naW4iLCJzaWciOiJlZGxqd3RwdWJrZXlfb3BzIiwiYWxnIjoiUlMyNTYifQ.eyJ0eXBlIjoiVXNlciIsInVpZCI6Imxpc2hlbmdjaGVuZyIsImV4cCI6MTcxOTgyNTEwNiwiaWF0IjoxNzE0NjQxMTA2LCJpc3MiOiJFYXJ0aGRhdGEgTG9naW4ifQ.IhDpDPm2z962fe0Y4e4Ea2INVjKtu0OzwBe31VpSFwRHnE0ycNcVCDRFHj6L8BOqtZrFj19kQyt2PqJu7Ny49XGkTbgWmi-ghF6mWGQzljbbYPjTB3I4WW7zZqjCuU89EH6hTTVaXKCPG5opt606EfzCDbOk0836kxEm19eA-vZrdIhHfEbFkv6eMah7BdAfATjbXFZQUMvpEFkqGtforGxm9zJZK5ivTGMmowokkeqBJhHZS511tZVVfCV1JMzkUmNKmQ_PM2KNo5C65sLuSlwUBCGxnsgXfdg8YbbCKyVn1IJ4r4hwbvxlrzKQTKoU8gf2wmGxjL7qtfDQoPQUrw"}
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    url_file = os.path.join(path.cloud_url_path, product, f"{tile}.csv")
    if not os.path.isfile(url_file):
        return
    url_df = pd.read_csv(url_file)
    url_df = url_df[url_df["year"] == year].sort_values("date")
    # url_df = exclude_finished_url(path, url_df, product, tile)
    output_path = os.path.join(path.modis_data_path, product, tile)
    create_path(output_path)
    while True:
        url_list = []
        for index, row in url_df.iterrows():
            filename = row["filename"]
            file = os.path.join(output_path, filename)
            if os.path.isfile(file):
                if os.path.getsize(file) == row["filesize"]:
                    continue
            url_list.append(row["url"])
        if not url_list:
            break
        for url in url_list:
            filename = url.split("/")[-1]
            with open(os.path.join(output_path, filename), "w+b") as f:
                try:
                    fh = urlopen(Request(url, headers=headers), context=ctx, timeout=60)
                    shutil.copyfileobj(fh, f)
                    print(filename)
                except HTTPError as e:
                    print('HTTP GET error code: %d' % e.code)
                    print('HTTP GET error message: %s' % e.reason)
                except URLError as e:
                    print('Failed to make request: %s' % e.reason)
                except IOError as e:
                    print("mkdir `%s': %s" % (e.filename, e.strerror))


def download(path: Path, tile_list, product_list, year_list, pool_size=1):
    tile_list = convert_to_list(tile_list)
    year_list = convert_to_list(year_list)
    product_list = convert_to_list(product_list)
    args_list = []
    for product in product_list:
        for year in year_list:
            for tile in tile_list:
                args_list.append([path, product, tile, year])
    concurrent_execute(download_url, args_list, pool_size, False)


def main():
    path = Path()
    tile_list = get_world_tile(path)
    tile_list = RegionEnum.DONG_BEI_TILE.value
    product_list = ["MOD11A1", "MYD11A1"]
    year_list = list(range(2000, 2024))
    download(path, tile_list, product_list, year_list, 1)
    

if __name__ == '__main__':
    main()
