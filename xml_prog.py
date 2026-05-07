import random
import string

from pathlib import Path
from functools import partial
from io import DEFAULT_BUFFER_SIZE
from pprint import pprint
from types import NoneType
from typing import Any


# def parseXml(chunkiness=8192):
#     downloadD()

def downloadD():
    import urllib.request
    from zipfile import ZipFile

    # temp = tempfile.TemporaryFile()

    # sslVer()

    # with tempfile.TemporaryDirectory() as d:
    #     temp_dir = d
    #     file_Path = os.path.join(temp_dir, generate_temp_filename())
    #     urllib.request.urlretrieve(url, file_Path)
    #
    #     with ZipFile(file_Path) as zObject:
    #         zObject.extractall(temp_dir)
    #
    #     print(temp_dir)
    #
    # with ZipFile('C:\\456\\r.zip') as zObject:
    #     for x in zObject.filelist:
    #         if Path(x.filename).suffix.startswith(".xml"):
    #             zObject.extract(x.filename, "C:\\456")
    #             parseXmlMy(x.filename)




def parseXmlMy(file: str):
    import xml.etree.ElementTree as ET

    tree = ET.parse("C:\\456\\"+file)
    root = tree.getroot()

    dict_our: dict[str, Any] = {}


# with open("output.csv", "w", newline="") as f:

    organ_registr_rights = root.find("./details_statement/group_top_requisites/organ_registr_rights")
    date_received_request = root.find("./details_request/date_received_request")

    dict_our |= {
        'head': {
            'organ_registr_rights': organ_registr_rights.text,
            'date_received_request': date_received_request.text
        },
        'items': []
    }


    for land_record in root.findall("./cadastral_blocks/cadastral_block/record_data/base_data/land_records/"):

        item: dict[str, Any] = {}

        common_data_cad_number = land_record.find("./object/common_data/cad_number")
        common_data_code =  land_record.find("./object/common_data/type/code")
        common_data_value = land_record.find("./object/common_data/type/value")

        category_code = land_record.find("./params/category/type/code")
        category_value = land_record.find("./params/category/type/value")

        permitted_use_by_document = land_record.find("./params/permitted_use/permitted_use_established/by_document")

        address_fias_okato = land_record.find("./address_location/address/address_fias/level_settlement/okato")
        address_fias_kladr = land_record.find("./address_location/address/address_fias/level_settlement/kladr")
        address_fias_postal_code = land_record.find("./address_location/address/address_fias/level_settlement/postal_code")
        address_readable_address = land_record.find("./address_location/address/readable_address")

        cost_value = land_record.find("./cost/value")

        contours_location_number_pp = land_record.find("./contours_location/contours/contour/number_pp")
        contours_location_sk_id = land_record.find("./contours_location/contours/contour/entity_spatial/sk_id")

        try:
            item |= {
                'common_data_cad_number': common_data_cad_number.text,
                'common_data_code': common_data_code.text,
                'common_data_value': common_data_value.text,
                'category_code': category_code.text,
                'category_value': category_value.text,
                'permitted_use_by_document': permitted_use_by_document.text if permitted_use_by_document is not None else '',
                'address_fias_okato': address_fias_okato.text,
                'address_fias_kladr': address_fias_kladr.text if address_fias_kladr is not None else '',
                'address_fias_postal_code': address_fias_postal_code.text if address_fias_postal_code is not None else '',
                'address_readable_address': address_readable_address.text if address_readable_address is not None else '',
                'cost_value': cost_value.text,
                'contours_location_number_pp': contours_location_number_pp.text if contours_location_number_pp is not None else '',
                'contours_location_sk_id': contours_location_sk_id.text if contours_location_sk_id is not None else '',
                'contours_location_ordinates': []
            }
        except NoneType:
            pass

        contours_location_ordinates = land_record.find("./contours_location/contours/contour/entity_spatial/spatials_elements/spatial_element/ordinates")

        if contours_location_ordinates is not None:
            for ordinate in contours_location_ordinates.findall("./ordinate"):
                dict_values: dict[str, Any] = {
                    'x': ordinate.find("x").text,
                    'y': ordinate.find("y").text,
                    'ord_nmb': ordinate.find("ord_nmb").text if ordinate.find("ord_nmb") is not None else '',
                    'num_geopoint':  ordinate.find("num_geopoint").text if ordinate.find("num_geopoint") is not None else '',
                    'delta_geopoint': ordinate.find("delta_geopoint").text if ordinate.find("delta_geopoint") is not None else ''
                }

                item['contours_location_ordinates'].append(dict_values)

        dict_our['items'].append(item)

    pprint(dict_our)

# def sslVer():
#     import socket
#     import ssl
#
#     hostname = 'www.google.com'
#     context = ssl.create_default_context()
#
#     with socket.create_connection((hostname, 443)) as sock:
#         with context.wrap_socket(sock, server_hostname=hostname) as ssock:
#             print(ssock.version())
#
#
#
# def generate_temp_filename() -> str:
#     return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
#     # return os.path.join(tempfile.gettempdir(), random_string)
#
# def bytes_from_file(filename, chunksize=8192):
#     with open(filename, "rb") as f:
#         while True:
#             chunk = f.read(chunksize)
#             if chunk:
#                 for b in chunk:
#                     yield b
#             else:
#                 break
#
#
# def file_byte_iterator(path):
#     """given a path, return an iterator over the file
#     that lazily loads the file
#     """
#     path = Path(path)
#     with path.open('rb') as file:
#         reader = partial(file.read1, DEFAULT_BUFFER_SIZE)
#         file_iterator = iter(reader, bytes())
#         for chunk in file_iterator:
#             yield from chunk


# Source - https://stackoverflow.com/a
# Posted by Zubo, modified by community. See post 'Timeline' for change history
# Retrieved 2025-12-03, License - CC BY-SA 4.0

# import urllib.request
# import shutil
#
# with urllib.request.urlopen("http://www.unece.org/fileadmin/DAM/cefact/locode/2015-2_UNLOCODE_SecretariatNotes.pdf") as response, open("downloaded_file.pdf", 'w') as out_file:
#     shutil.copyfileobj(response, out_file)



# import zipfile
# import os
# from pathlib import Path
#
# def extract(zip_path, target_path):
#     block_size = 8192
#     z = zipfile.ZipFile(zip_path)
#     for entry_name in z.namelist():
#         entry_info = z.getinfo(entry_name)
#         i = z.open(entry_name)
#         print(entry_name)
#         if entry_name[-1] != '/':
#             dir_name = os.path.dirname(entry_name)
#             p = Path(f"{target_path}/{dir_name}")
#             p.mkdir(parents=True, exist_ok=True)
#             o = open(f"{target_path}/{entry_name}", 'wb')
#             offset = 0
#             while True:
#                 b = i.read(block_size)
#                 offset += len(b)
#                 print(float(offset)/float(entry_info.file_size) * 100.)
#                 if b == b'':
#                     break
#                 o.write(b)
#             o.close()
#         i.close()
#     z.close()
#
# extract("test.zip", "test")

#
# import xml.etree.ElementTree as ET
# import os
# from typing import Any
# from pprint import pprint
#
#
# def get_element_text(parent: ET.Element, xpath: str, default: str = "") -> str:
#     """Вспомогательная функция для безопасного получения текста из элемента."""
#     element = parent.find(xpath)
#     return element.text if element is not None and element.text is not None else default
#
#
# def parse_xml_data(file_name: str, base_path: str = "C:\\456\\"):
#     full_path = os.path.join(base_path, file_name)
#     tree = ET.parse(full_path)
#     root = tree.getroot()
#
#     result_data = {
#         'head': {
#             'organ_registr_rights': get_element_text(root,
#                                                      "./details_statement/group_top_requisites/organ_registr_rights"),
#             'date_received_request': get_element_text(root, "./details_request/date_received_request")
#         },
#         'items': []
#     }
#
#     land_records_path = "./cadastral_blocks/cadastral_block/record_data/base_data/land_records/"
#     for land_record in root.findall(land_records_path):
#         item = {
#             'common_data_cad_number': get_element_text(land_record, "./object/common_data/cad_number"),
#             'common_data_code': get_element_text(land_record, "./object/common_data/type/code"),
#             'common_data_value': get_element_text(land_record, "./object/common_data/type/value"),
#             'category_code': get_element_text(land_record, "./params/category/type/code"),
#             'category_value': get_element_text(land_record, "./params/category/type/value"),
#             'permitted_use_by_document': get_element_text(land_record,
#                                                           "./params/permitted_use/permitted_use_established/by_document"),
#             'address_fias_okato': get_element_text(land_record,
#                                                    "./address_location/address/address_fias/level_settlement/okato"),
#             'address_fias_kladr': get_element_text(land_record,
#                                                    "./address_location/address/address_fias/level_settlement/kladr"),
#             'address_fias_postal_code': get_element_text(land_record,
#                                                          "./address_location/address/address_fias/level_settlement/postal_code"),
#             'address_readable_address': get_element_text(land_record, "./address_location/address/readable_address"),
#             'cost_value': get_element_text(land_record, "./cost/value"),
#             'contours_location_number_pp': get_element_text(land_record,
#                                                             "./contours_location/contours/contour/number_pp"),
#             'contours_location_sk_id': get_element_text(land_record,
#                                                         "./contours_location/contours/contour/entity_spatial/sk_id"),
#             'contours_location_ordinates': []
#         }
#
#         ordinates_xpath = "./contours_location/contours/contour/entity_spatial/spatials_elements/spatial_element/ordinates"
#         ordinates_element = land_record.find(ordinates_xpath)
#
#         if ordinates_element is not None:
#             for ordinate in ordinates_element.findall("./ordinate"):
#                 ordinate_data = {
#                     'x': get_element_text(ordinate, "x"),
#                     'y': get_element_text(ordinate, "y"),
#                     'ord_nmb': get_element_text(ordinate, "ord_nmb"),
#                     'num_geopoint': get_element_text(ordinate, "num_geopoint"),
#                     'delta_geopoint': get_element_text(ordinate, "delta_geopoint")
#                 }
#                 item['contours_location_ordinates'].append(ordinate_data)
#
#         result_data['items'].append(item)
#
#     pprint(result_data)