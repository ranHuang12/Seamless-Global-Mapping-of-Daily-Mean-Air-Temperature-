from common_object.entity import QcMode
from ta_estimate.entity.path import Path


class Configuration(object):
    tile_list: list = []
    year_list: list = []
    date_list: list = []
    validate_mode: str = ""
    validate_test_ratio: int = 0
    test_ratio: int = 0
    train_tile_list: list = []
    validate_tile_list: list = []
    test_tile_list: list = []
    train_year_list: list = []
    validate_year_list: list = []
    test_year_list: list = []
    specific_validate_file: str = ""
    specific_test_file: str = ""

    view_list: list = []
    qc_mode: QcMode = None
    auxiliary_list: list = []
    modeling_x_list: list = []
    modeling_y: str = ""
    modeling_attribute_list = []

    model: str = ""
    time_size: int = 1
    std: bool = True

    path = Path()
