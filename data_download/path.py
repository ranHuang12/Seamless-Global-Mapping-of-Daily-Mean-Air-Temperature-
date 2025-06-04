import os.path

from common_object.entity import BasePath


class Path(BasePath):
    def __init__(self, root_path=None, cloud_root_path=None):
        super().__init__(root_path, cloud_root_path)
        self.__build_path()

    def __build_path(self):
        self.cloud_url_path = os.path.join(self.cloud_modis_data_path, "url")
        return self
