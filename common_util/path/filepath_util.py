import os.path


def create_path(path):
    if not os.path.exists(path):
        os.makedirs(path)
