import os.path

from common_object.entity import BasePath


class Path(BasePath):
    def __init__(self, root_path=None, cloud_root_path=None):
        super().__init__(root_path, cloud_root_path)
        self.__build_path()

    def __build_path(self):
        self.lst_coverage_path = os.path.join(self.lst_path, "coverage")
        self.annual_ta_path = os.path.join(self.ta_interpolate_path, "annual_ta")

        self.cloud_lst_coverage_path = os.path.join(self.cloud_lst_path, "coverage")
        return self
