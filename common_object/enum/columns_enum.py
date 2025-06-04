import copy
from enum import Enum


class ColumnsEnum(Enum):
    STATION_GSOD = ["STATION", "LATITUDE", "LONGITUDE", "ELEVATION", "NAME"]
    STATION_GSOD_TYPE = {"STATION": str, "LATITUDE": float, "LONGITUDE": float, "ELEVATION": float, "NAME": str}

    STATION = ["STATION", "LATITUDE", "LONGITUDE", "ELEVATION", "NAME", "SIN_X", "SIN_Y"]
    STATION_TYPE = {"STATION": str, "LATITUDE": float, "LONGITUDE": float, "ELEVATION": float, "NAME": str,
                    "SIN_X": float, "SIN_Y": float}

    STATION_TILE = ["TILE", "STATION", "LATITUDE", "LONGITUDE", "ELEVATION", "NAME", "SIN_X", "SIN_Y", "INDEX_X", "INDEX_Y"]
    STATION_TILE_TYPE = {"TILE": str, "STATION": str, "LATITUDE": float, "LONGITUDE": float, "ELEVATION": float,
                         "NAME": str, "SIN_X": float, "SIN_Y": float, "INDEX_X": int, "INDEX_Y": int}

    METE_GSOD = ["STATION", "DATE", "LATITUDE", "LONGITUDE", "ELEVATION", "TEMP", "TEMP_ATTRIBUTES"]
    METE_GSOD_TYPE = {"STATION": str, "DATE": str, "LATITUDE": float, "LONGITUDE": float, "ELEVATION": float,
                      "TEMP": float, "TEMP_ATTRIBUTES": int}

    METE_STATION = ["STATION", "DATE", "LATITUDE", "LONGITUDE", "ELEVATION", "TEMP", "TEMP_ATTRIBUTES"]
    METE_STATION_TYPE = {"STATION": str, "DATE": int, "LATITUDE": float, "LONGITUDE": float, "ELEVATION": float,
                      "TEMP": float, "TEMP_ATTRIBUTES": int}

    METE_ONLY = ["STATION", "DATE", "TEMP", "TEMP_ATTRIBUTES"]
    METE_ONLY_TYPE = {"STATION": str, "DATE": int, "TEMP": float, "TEMP_ATTRIBUTES": int}

    MODELING_DATA = ["STATION", "LATITUDE", "LONGITUDE", "ELEVATION", "DATE", "TEMP", "TEMP_ATTRIBUTES", "TD_ALL",
                     "TN_ALL", "AD_ALL", "AN_ALL", "TD_ANGLE", "TN_ANGLE", "AD_ANGLE", "AN_ANGLE", "YEAR", "MONTH",
                     "DOY"]
    MODELING_DATA_TYPE = {"TILE": str, "STATION": str, "LATITUDE": "Int16", "LONGITUDE": "Int16", "ELEVATION": "Int16",
                          "DATE": "Int32", "TEMP": "Int16", "TEMP_ATTRIBUTES": "Int16", "TD_ALL": "Int16",
                          "TN_ALL": "Int16", "AD_ALL": "Int16", "AN_ALL": "Int16", "TD_ANGLE": "Int16",
                          "TN_ANGLE": "Int16", "AD_ANGLE": "Int16", "AN_ANGLE": "Int16", "YEAR": "Int16",
                          "MONTH": "Int16", "DOY": "Int16"}

    VALIDATE_DATA = ["TILE", "STATION", "LATITUDE", "LONGITUDE", "ELEVATION", "DATE", "TEMP", "TEMP_ATTRIBUTES", "PRED_TA", "YEAR", "MONTH"]
    VALIDATE_DATA_TYPE = {"TILE": str, "STATION": str, "LATITUDE": float, "LONGITUDE": float, "ELEVATION": float,
                          "DATE": int, "TEMP": float, "TEMP_ATTRIBUTES": int, "PRED_TA": int, "YEAR": int, "MONTH": int}

    VALIDATE_REFER_DATA = VALIDATE_DATA + ["REFER_TA"]
    VALIDATE_REFER_DATA_TYPE = VALIDATE_DATA_TYPE | {"REFER_TA": "Int16"}

    SINGLE_STATION_TYPE = {"STATION": str}

    SINGLE_METE = ["STATION", "DATE"]
    SINGLE_METE_TYPE = {"STATION": str, "DATE": int}

    MERGE_METE = ["INDEX_X", "INDEX_Y", "DATE"]
    MERGE_METE_TYPE = {"INDEX_X": int, "INDEX_Y": int, "DATE": int}
