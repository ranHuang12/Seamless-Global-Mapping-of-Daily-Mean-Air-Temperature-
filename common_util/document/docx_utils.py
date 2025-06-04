# import os
#
# from docx import Document
#
# from common_object.entity import BasePath
# from common_util.common import convert_to_list
#
#
# def create_table(path: BasePath, value_arr_list, table_name_list, filename, append=False):
#     value_arr_list = convert_to_list(value_arr_list)
#     table_name_list = convert_to_list(table_name_list)
#     document_file = os.path.join(path.cloud_table_path, f"{filename}.docx")
#     if append and os.path.isfile(document_file):
#         document = Document(document_file)
#     else:
#         document = Document()
#     for index, value_arr in enumerate(value_arr_list):
#         document.add_heading(table_name_list[index])
#         table = document.add_table(rows=value_arr.shape[0], cols=value_arr.shape[1])
#         for row in range(value_arr.shape[0]):
#             for col in range(value_arr.shape[1]):
#                 table.cell(row, col).text = str(value_arr[row, col])
#     document.save(document_file)
#
#
# def main():
#     path = BasePath()
#     pass
#
#
# if __name__ == "__main__":
#     main()
