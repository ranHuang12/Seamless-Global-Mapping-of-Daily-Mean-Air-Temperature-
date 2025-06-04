import os
import sys
import time

import pandas as pd

from common_util.common import convert_to_list
from common_util.path import create_path


def handle_null(df: pd.DataFrame(), field_list, keep=False):
    field_list = convert_to_list(field_list)
    for field in field_list:
        if field in df.columns:
            if keep:
                df = df[df[field].isnull()]
            else:
                df = df[df[field].notnull()]
    return df


def to_csv(df, csv_file, append=True, lock=None):
    create_path(os.path.dirname(csv_file))
    if sys.platform.startswith("linux"):
        return __to_csv_for_linux(df, csv_file, append)
    while True:
        try:
            if lock is not None:
                lock.acquire()
            if append and os.path.isfile(csv_file):
                df.to_csv(csv_file, mode="a", index=False, header=False, encoding="utf-8")
            else:
                df.to_csv(csv_file, index=False, encoding="utf-8")
            return True
        except Exception as e:
            print(e)
            time.sleep(1)
        finally:
            if lock is not None:
                lock.release()


def __to_csv_for_linux(df, csv_file, append=True):
    import fcntl
    while True:
        with open(csv_file, "a") as file:
            try:
                fcntl.flock(file, fcntl.LOCK_EX)
                if append and os.path.getsize(csv_file) != 0:
                    df.to_csv(csv_file, mode="a", index=False, header=False)
                else:
                    df.to_csv(csv_file, index=False)
                return True
            except Exception as e:
                print(e)
                time.sleep(1)
            finally:
                fcntl.flock(file, fcntl.LOCK_UN)


def merge_csv(csv1, csv2, on=None, how="inner", output_file=None, along_column=True):
    df1 = csv1 if isinstance(csv1, pd.DataFrame) else (pd.read_csv(csv1) if os.path.isfile(csv1) else None)
    df2 = csv2 if isinstance(csv2, pd.DataFrame) else (pd.read_csv(csv2) if os.path.isfile(csv2) else None)
    if df1 is not None and df2 is not None:
        output_df = df1.merge(df2, how, on) if along_column else pd.concat([df1, df2], ignore_index=True)
    elif df1 is not None:
        output_df = df1
    elif df2 is not None:
        output_df = df2
    else:
        output_df = None
    if output_df is not None:
        to_csv(output_df, csv1 if output_file is None else output_file, False)


def main():
    to_csv(pd.DataFrame({"test": ["test"]}), r"D:\我的坚果云\test.csv", False)


if __name__ == "__main__":
    main()
