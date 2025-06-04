from enum import Enum

from common_object.entity.view import View
from common_object.enum.layer_enum import LayerEnum


class ViewEnum(Enum):
    TD = View(view_name="TD",
              satellite_name="TERRA",
              lst_product="MOD11A1",
              lst_8day_product="MOD11A2",
              lst_layer=LayerEnum.LST_DAY.value,
              qc_layer=LayerEnum.LST_QC_DAY.value,
              view_time_layer=LayerEnum.LST_DAY_VIEW_TIME.value,
              view_angle_layer=LayerEnum.LST_DAY_VIEW_ANGLE.value)
    TN = View(view_name="TN",
              satellite_name="TERRA",
              lst_product="MOD11A1",
              lst_8day_product="MOD11A2",
              lst_layer=LayerEnum.LST_NIGHT.value,
              qc_layer=LayerEnum.LST_QC_NIGHT.value,
              view_time_layer=LayerEnum.LST_NIGHT_VIEW_TIME.value,
              view_angle_layer=LayerEnum.LST_NIGHT_VIEW_ANGLE.value)
    AD = View(view_name="AD",
              satellite_name="AQUA",
              lst_product="MYD11A1",
              lst_8day_product="MYD11A2",
              lst_layer=LayerEnum.LST_DAY.value,
              qc_layer=LayerEnum.LST_QC_DAY.value,
              view_time_layer=LayerEnum.LST_DAY_VIEW_TIME.value,
              view_angle_layer=LayerEnum.LST_DAY_VIEW_ANGLE.value)
    AN = View(view_name="AN",
              satellite_name="AQUA",
              lst_product="MYD11A1",
              lst_8day_product="MYD11A2",
              lst_layer=LayerEnum.LST_NIGHT.value,
              qc_layer=LayerEnum.LST_QC_NIGHT.value,
              view_time_layer=LayerEnum.LST_NIGHT_VIEW_TIME.value,
              view_angle_layer=LayerEnum.LST_NIGHT_VIEW_ANGLE.value)
