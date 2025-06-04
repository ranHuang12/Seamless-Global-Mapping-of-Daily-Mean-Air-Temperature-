import os.path
import shutil

from common_object.entity import BasePath
from common_util.common import get_world_tile
from common_util.path import create_path


def move_file(path: BasePath, product_list, tile_list, year_list):
    for product in product_list:
        for tile in tile_list:
            filepath = os.path.join(path.modis_data_path, product, tile)
            target_path = os.path.join(path.modis_data_path, "temp", product, tile)
            create_path(target_path)
            for filename in os.listdir(filepath):
                date = int(filename.split(".")[1][1:])
                if date // 1000 in year_list:
                    shutil.move(os.path.join(filepath, filename), target_path)
            print(product, tile)


def main():
    path = BasePath()
    product_list = ["MOD11A1", "MYD11A1", "MOD13A2", "MYD13A2"]
    tile_list = get_world_tile(path)
    year_list = list(range(2020, 2024))
    move_file(path, product_list, tile_list, year_list)


if __name__ == "__main__":
    main()
