import os
import shutil
from file_download import download_url
from pyhdf.SD import SD
from multiprocessing import Process, Queue


def position_check(data_path, wrong_path):
    product_list = os.listdir(data_path)
    for product in product_list:
        product_path = os.path.join(data_path, product)
        tile_list = os.listdir(product_path)  # 多个tile组成的列表
        for tile in tile_list:  # 遍历各个tile
            tile_path = os.path.join(product_path, tile)
            file_list = os.listdir(tile_path)  # tile文件夹下下载的额数据组成的列表
            for file in file_list:
                if file[:7] != product or file[17:23] != tile:
                    original_path = os.path.join(tile_path, file)
                    new_path = os.path.join(data_path, file[:7], file[17:23], file)
                    if not os.path.exists(os.path.join(data_path, file[:7], file[17:23])) or os.path.isfile(new_path):
                        shutil.move(original_path, os.path.join(wrong_path, file))
                        print('\033[31;1m%s moved to wrong_file\033[0m' % file)
                    else:
                        shutil.move(original_path, new_path)
                        print('\033[31;1m%s moved to %s\033[0m' % (file, new_path))
            print('\033[32;1m%s-%s latitude_longitude checked!\033[0m' % (product, tile))


def download_check(url_path, data_path):
    product_list = os.listdir(url_path)
    t_list = []
    while True:
        all_url_list = []
        for product in product_list:
            product_path = os.path.join(url_path, product)
            txt_list = os.listdir(product_path)
            for txt in txt_list:
                tile = txt.split('.')[0]
                path = os.path.join(data_path, product, tile)
                url_list = []
                with open(os.path.join(product_path, txt)) as f:
                    url = f.readline().strip()
                    while url:
                        filename = url[-45:]
                        loadingfile = '%s.crdownload' % filename
                        if os.path.isfile(os.path.join(path, loadingfile)) is True:
                            os.remove(os.path.join(path, loadingfile))
                        if os.path.isfile(os.path.join(path, filename)) is False:
                            url_list.append(url)
                            all_url_list.append(url)
                            print('\033[31;1m%s not found\033[0m' % filename)
                        url = f.readline().strip()
                if url_list:
                    # download(path, url_list)
                    # 多线程
                    # t = threading.Thread(target=download, args=(path, url_list))
                    # t.start()
                    # t_list.append(t)
                    # 多进程
                    process = Process(target=download_url, args=(path, url_list))
                    process.start()
                    t_list.append(process)
        for t in t_list:
            t.join()
        if not all_url_list:
            break
    print('\033[32;1mdownload checked!\033[0m')


def repeat_check(data_path, wrong_path):
    product_list = os.listdir(data_path)
    for product in product_list:
        product_path = os.path.join(data_path, product)
        tile_list = os.listdir(product_path)
        for tile in tile_list:
            tile_path = os.path.join(product_path, tile)
            file_list = os.listdir(tile_path)
            for index, file in enumerate(file_list):
                if len(file) != 45:
                    shutil.move(os.path.join(tile_path, file), os.path.join(wrong_path, file))
                    # os.remove(os.path.join(tile_path, file))
                    print('\033[33;1m%s format error, move to wrong_file\033[0m' % file)
                else:
                    for new_file in file_list[index+1:]:
                        if new_file[9:16] == file[9:16]:
                            if file[24:27] != '006':
                                shutil.move(os.path.join(tile_path, file), os.path.join(wrong_path, file))
                                print('\033[33;1m%s repeated, move to wrong_file\033[0m' % file)
                            elif new_file[24:27] != '006':
                                shutil.move(os.path.join(tile_path, new_file), os.path.join(wrong_path, new_file))
                                print('\033[33;1m%s repeated, move to wrong_file\033[0m' % new_file)
                                # os.remove(os.path.join(tile_path, file))
            print('\033[32;1m%s-%s repeat checked!\033[0m' % (product, tile))


def hdf_file_check(tile_path, wrong_path, q):
    file_list = os.listdir(tile_path)  # tile文件夹下下载的额数据组成的列表
    datasets_nums = []  # 以列表形式储存同一tile下不同file的数据集个数
    datasets_names = []  # 以列表形式储存同一tile下不同file的数据集名称
    # pixel_num = 0
    file_num = 1
    for file in file_list:
        file_path = os.path.join(tile_path, file)
        new_path = os.path.join(wrong_path, file)
        try:
            hdf = SD(file_path)
            datasets_num = hdf.info()[0]
            datasets_nums.append(datasets_num)
            # 第1次判断：数据集数量是否与前文件一致
            if len(datasets_nums) == 1:
                pass
            else:
                if datasets_nums[-1] != datasets_nums[-2]:
                    shutil.move(file_path, new_path)
                    print('\033[31;1m%s dataset_num error, move to wrong_path\033[0m' % file)
                    datasets_nums.pop()
                    q.put(file)
                    continue
            # 第2次判断：数据集名称是否与前文件一致
            data = hdf.datasets()
            dataset_names = []
            for sds in data:
                dataset_names.append(sds)
            datasets_names.append(dataset_names)
            # if len(datasets_names) == 1:
            #     pass
            # else:
            #     if datasets_names[-1] != datasets_names[-2]:
            #         print('\033[31;1m%s datasets_names error\033[0m' % file)
            #         datasets_names.pop()
            #         dataset_names_error.append('%s datasets_names error' % file)
            #         continue
            # 第3次判断:各数据集像元数是否一致
            try:
                for dataset in dataset_names:
                    content = hdf.select(dataset).get()
                file_num += 1
                print("\033[32:1m%s hdf checked!\033[0m" % file)
                #     pixel_count = 0
                #     for i in range(len(content)):
                #         pixel_count += len(content[i])
                #     if file_num == 1:
                #         pixel_num = pixel_count
                #     else:
                #         if pixel_count != pixel_num:
                #             print('\033[31;1m%s pixel_count error\033[0m' % file)
                #             pixel_num_error.append('%s pixel_count error' % file)
                #             break
                # if file_num == 1:
                #     print('pixel_num:', pixel_num)
            except Exception as e:
                shutil.move(file_path, new_path)
                print('\033[31;1m%s dataset open error, move to wrong_path\033[0m' % file)
                q.put(file)
        except Exception as e:
            shutil.move(file_path, new_path)
            print('\033[31;1m%s open error\033[0m' % file)
            q.put(file)


def hdf_check(data_path, wrong_path):
    product_list = os.listdir(data_path)
    t_list = []
    q = Queue()
    for product in product_list:
        product_path = os.path.join(data_path, product)
        tile_list = os.listdir(product_path)
        for tile in tile_list:
            tile_path = os.path.join(product_path, tile)
            t = Process(target=hdf_file_check, args=(tile_path, wrong_path, q))
            t.start()
            t.join()
    #         t_list.append(t)
    # for t in t_list:
    #     t.join()
    file_to_redownload = []
    while not q.empty():
        file_to_redownload.append(q.get())
    for file in file_to_redownload:
        with open(os.path.join(wrong_path, 'file_to_redownload.txt'), 'a') as f:
            f.write('%s\n' % file)
    print('\033[32;1mhdf checked!\033[0m')


def redownload(url_path, wrong_path):
    file_list = []
    with open(os.path.join(wrong_path, 'file_to_redownload.txt')) as f:
        file = f.readline().strip()
        while file:
            file_list.append(file)
            file = f.readline().strip()
    download_list = []
    for file in file_list:
        product = file[:7]
        tile = file[17:23]
        with open(os.path.join(url_path, product, '%s.txt' % tile)) as f:
            url = f.readline().strip()
            while url:
                if url[-45:] == file:
                    download_list.append(url)
                    print('\033[32;1m%s\033[0m' % url)
                url = f.readline().strip()
    path = os.path.join(wrong_path, 'redownload_file')
    if os.path.exists(path) is False:
        os.makedirs(path)
    while True:
        url_list = []
        for download_url in download_list:
            file = download_url[-45:]
            if not os.path.isfile(os.path.join(path, file)):
                url_list.append(download_url)
        if url_list:
            download_url(path, url_list)
        else:
            break
    print('\033[32;1mredownload completed!\033[0m')


def recheck(wrong_path):
    all_file_path = os.path.join(wrong_path, 'redownload_file')
    file_list = os.listdir(all_file_path)
    file_to_redownload = []
    for file in file_list:
        file_path = os.path.join(all_file_path, file)
        try:
            hdf = SD(file_path)
            data = hdf.datasets()
            dataset_names = []
            for sds in data:
                dataset_names.append(sds)
            try:
                for dataset in dataset_names:
                    content = hdf.select(dataset).get()
                print("\033[32:1m%s hdf checked!\033[0m" % file)
            except Exception as e:
                os.remove(file_path)
                file_to_redownload.append(file)
                print('\033[31;1m%s dataset open error, remove\033[0m' % file)
        except Exception as e:
            os.remove(file_path)
            file_to_redownload.append(file)
            print('\033[31;1m%s open error, remove\033[0m' % file)
    if file_to_redownload:
        for file in file_to_redownload:
            with open(os.path.join(wrong_path, 'file_failed_again.txt'), 'a') as f:
                f.write('%s\n' % file)
    print('\033[32;1mrecheck completed!\033[0m')


def move_file(data_path, wrong_path):
    all_file_path = os.path.join(wrong_path, 'redownload_file')
    file_list = os.listdir(all_file_path)
    for file in file_list:
        product = file.split('.')[0]
        tile = file.split('.')[2]
        file_path = os.path.join(all_file_path, file)
        new_path = os.path.join(data_path, product, tile, file)
        shutil.move(file_path, new_path)
        print('\033[32;1m%s move to original latitude_longitude\033[0m' % file)


if __name__ == '__main__':
    url_path = r'E:\PythonProject\MODISData_download\url_for_check'  # 待检查文件对应url所在文件夹
    data_path = r'I:\MODISData'  # 待检查文件所在文件夹
    wrong_path = r'I:\wrong_file'  # 存放错误文件的文件夹，注意要在被循环文件夹的同级或上级目录
    if not os.path.exists(wrong_path):
        os.makedirs(wrong_path)
    # position_check(data_path, wrong_path)
    # download_check(url_path, data_path)
    # repeat_check(data_path, wrong_path)
    # download_check(url_path, data_path)
    # hdf_check(data_path, wrong_path)
    if os.path.isfile(os.path.join(wrong_path, 'file_to_redownload.txt')):
        # redownload(url_path, wrong_path)
        # recheck(wrong_path)
        # move_file(data_path, wrong_path)
        position_check(data_path, wrong_path)
        download_check(url_path, data_path)
        repeat_check(data_path, wrong_path)
        download_check(url_path, data_path)
    print('\033[32;1mall check completed, please handle manually!\033[0m')
