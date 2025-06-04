class View(object):
    def __init__(self, view_name=None, satellite_name=None, lst_product=None, lst_8day_product=None,
                 lst_layer=None, qc_layer=None, view_time_layer=None, view_angle_layer=None):
        self.view_name = view_name
        self.satellite_name = satellite_name

        self.lst_product = lst_product
        self.lst_8day_product = lst_8day_product

        self.lst_layer = lst_layer
        self.qc_layer = qc_layer
        self.view_time_layer = view_time_layer
        self.view_angle_layer = view_angle_layer
