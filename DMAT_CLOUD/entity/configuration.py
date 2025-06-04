from ta_interpolate.entity.path import Path


class Configuration(object):
    path: Path = Path()

    model: str = ""
    modeling_x_list: list = []
    modeling_y: str = ""
    std: bool = True
    cluster: bool = False
    processing_csv: str = None

    interpolate_refer: bool = True
    interpolate_refer_rounds: int = 5
