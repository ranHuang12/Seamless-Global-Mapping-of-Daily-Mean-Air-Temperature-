from enum import Enum


class PathEnum(Enum):
    DISK_ROOT = "F:\\"

    LAPTOP_ROOT = r""
    LAPTOP_CLOUD_ROOT = r"D:\586_paper_maker\LST"

    PC_ROOT = r"E:\LST"
    PC_CLOUD_ROOT = r"D:\586_paper_maker\LST"

    SERVER_ROOT = r"E:\LST"
    SERVER_CLOUD_ROOT = r"C:\Users\dell\Nutstore\1\586_paper_maker\LST"

    WORKSTATION_ROOT = "G:\\"
    WORKSTATION_CLOUD_ROOT = r"C:\Users\User\Nutstore\1\586_paper_maker\LST"

    CLUSTER_ROOT = "/home/ylb/LST"
