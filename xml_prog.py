
import xml.etree.ElementTree as ET
from typing import Any, Dict


def parse_build_with_owners(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    def get_t(node, path, default=''):
        if node is None: return default
        found = node.find(path)
        return found.text if found is not None and found.text else default

    items = []

    # 1. Определяем типы объектов
    record_tags = [".//land_record", ".//build_record", ".//room_record"]

    for tag in record_tags:
        for record in root.findall(tag):
            item_data = {
                'cad_number': get_t(record, ".//common_data/cad_number"),
                'quarter_cad_number': get_t(record, ".//common_data/quarter_cad_number"),
                'area': get_t(record, ".//params/area"),
                'floors': get_t(record, ".//params/floors"),
                'purpose': get_t(record, ".//params/purpose/value"),
                'year_built': get_t(record, ".//params/year_built"),
                'cost': get_t(record, ".//cost/value"),
                'owners': [],
                'related_cad_numbers': [],
                'extract_date': get_t(root, ".//date_formation") or get_t(root, ".//date_received_request"),
            }

            # Извлечение связанных кадастровых номеров (cad_links)
            cad_links = record.find(".//cad_links")
            if cad_links is not None:
                for linked_num in cad_links.findall(".//cad_number"):
                    if linked_num.text and linked_num.text not in item_data['related_cad_numbers']:
                        item_data['related_cad_numbers'].append(linked_num.text)

            # 2. Поиск прав (right_record)
            rights = record.findall(".//right_record") or root.findall(".//right_record")

            for right in rights:
                right_type = get_t(right, ".//right_data/right_type/value")
                reg_num = get_t(right, ".//registration/reg_number")

                # 3. Извлечение собственников
                holders = right.findall(".//right_holders/right_holder")
                for holder in holders:
                    name = ""
                    # Физлицо
                    surname = get_t(holder, ".//individual/surname")
                    firstname = get_t(holder, ".//individual/name")
                    patronymic = get_t(holder, ".//individual/patronymic")
                    name = f"{surname} {firstname} {patronymic}".strip()

                    # Юрлицо
                    if not name:
                        name = get_t(holder, ".//legal_entity/entity_common_data/name")

                    # Муниципальная собственность
                    if not name:
                        name = get_t(holder, ".//public_formation/public_formation_type/value")
                        full_pub_name = get_t(holder, ".//public_formation/content")
                        if full_pub_name:
                            name = f"{name}: {full_pub_name}"

                    if not name:
                        name = "Сведения о собственнике отсутствуют (ограничено законом)"

                    item_data['owners'].append({
                        'name': name,
                        'right_type': right_type,
                        'reg_num': reg_num,
                        'inn': get_t(holder, ".//inn")
                    })

            items.append(item_data)

    return items

def parse_rosreestr_xml_lang_records(file_path: str) -> Dict[str, Any]:
    """
    Парсит XML выписку Росреестра (Земельный участок)
    Возвращает словарь, готовый для создания Django-моделей.
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        return f"Ошибка при чтении файла: {e}"

    # Вспомогательная функция для безопасного извлечения текста
    def get_t(node, path, default=''):
        if node is None: return default
        found = node.find(path)
        return found.text if found is not None and found.text else default

    # 1. Шапка документа
    dict_our = {
        'head': {
            'organ_registr_rights': get_t(root, ".//details_statement/group_top_requisites/organ_registr_rights"),
            'date_received_request': get_t(root, ".//details_request/date_received_request") or get_t(root,
                                                                                                      ".//date_formation"),
            'registration_number': get_t(root, ".//registration_number")
        },
        'items': []
    }

    # 2. Ищем записи объектов (Участки, Здания, Сооружения, Помещения)
    # Используем .//, так как в разных типах выписок вложенность отличается
    object_nodes = root.findall(".//land_record") + \
                   root.findall(".//build_record") + \
                   root.findall(".//construction_record") + \
                   root.findall(".//room_record")

    for obj in object_nodes:
        item = {
            'cad_number': get_t(obj, ".//common_data/cad_number"),
            'type_value': get_t(obj, ".//common_data/type/value") or "Объект недвижимости",
            'category_value': get_t(obj, ".//category/type/value") or get_t(obj, ".//params/category/value"),
            'permitted_use': get_t(obj, ".//permitted_use_established/by_document") or get_t(obj, ".//params/purpose"),
            'address': get_t(obj, ".//address/readable_address") or get_t(obj,
                                                                          ".//address_location/address/readable_address"),
            'cost': get_t(obj, ".//cost/value"),
            'area': get_t(obj, ".//params/area"),
            'contours': [],
            'rights': []
        }

        # 3. Геометрия (Многоконтурные участки и здания)
        # Ищем все контуры (в зданиях они могут быть в location/contours)
        contour_nodes = obj.findall(".//contours/contour") or obj.findall(".//location/contours/contour")
        for contour in contour_nodes:
            contour_data = {
                'number_pp': get_t(contour, "number_pp"),
                'sk_id': get_t(contour, ".//sk_id") or get_t(contour, ".//entity_spatial/sk_id"),
                'elements': []
            }

            # В каждом контуре может быть несколько элементов (внешний контур и дырки)
            spatial_elements = contour.findall(".//spatial_element") or contour.findall(
                ".//entity_spatial/spatials_elements/spatial_element")
            if not spatial_elements and contour.find(".//ordinate") is not None:
                # Случай, когда ординаты идут сразу в контуре
                spatial_elements = [contour]

            for s_elem in spatial_elements:
                ordinates = []
                for ord_node in s_elem.findall(".//ordinate"):
                    ordinates.append({
                        'x': get_t(ord_node, "x"),
                        'y': get_t(ord_node, "y"),
                        'ord_nmb': get_t(ord_node, "ord_nmb")
                    })
                if ordinates:
                    contour_data['elements'].append(ordinates)

            if contour_data['elements']:
                item['contours'].append(contour_data)

        # 4. Права собственности
        # Ищем .//right_record по всему дереву объекта
        # Если правообладателей несколько, будет несколько блоков или один со списком
        right_records = obj.findall(".//right_record") or root.findall(".//right_record")

        for rr in right_records:
            # Важно: если в файле несколько объектов, проверяем связь (опционально)
            # Для простоты считаем, что права относятся к текущему объекту
            right_info = {
                'right_type': get_t(rr, ".//right_data/right_type/value"),
                'reg_number': get_t(rr, ".//registration/reg_number"),
                'reg_date': get_t(rr, ".//registration/reg_date"),
                'owners': [],
                'underlying_documents': []
            }

            for holder in rr.findall(".//right_holders/right_holder"):
                # Собираем ФИО (Физики)
                surname = get_t(holder, ".//individual/surname")
                name = get_t(holder, ".//individual/name")
                patronymic = get_t(holder, ".//individual/patronymic")
                full_name = f"{surname} {name} {patronymic}".strip()

                # Собираем Юрлица / Муниципалитеты
                if not full_name:
                    full_name = get_t(holder, ".//legal_entity/entity_common_data/name") or \
                                get_t(holder, ".//public_formation/public_formation_type/value")

                if not full_name:
                    full_name = "Сведения отсутствуют (закон №266-ФЗ)"

                right_info['owners'].append({
                    'name': full_name,
                    'birth_date': get_t(holder, ".//birth_date"),
                    'birth_place': get_t(holder, ".//birth_place"),
                    'inn': get_t(holder, ".//inn"),
                    'identity_doc' : {
                        'code': get_t(holder, ".//identity_doc/document_code/code"),
                        'value': get_t(holder, ".//identity_doc/document_code/value"),
                        'document_name': get_t(holder, ".//document_name"),
                        'document_series': get_t(holder, ".//document_series"),
                        'document_number': get_t(holder, ".//document_number"),
                        'document_date': get_t(holder, ".//document_date"),
                        'document_issuer': get_t(holder, ".//document_issuer"),
                    },
                    'contacts': {
                        'mailing_addess': get_t(holder, ".//individual/contacts/mailing_addess"),
                    },
                    'share': get_t(rr, ".//right_data/shares/share/value_text")
                })

            for underlying in rr.findall(".//underlying_documents/underlying_document"):
                right_info['underlying_documents'].append({
                    'underlying_document': {
                        'code': get_t(underlying, './/code'),
                        'value': get_t(underlying, './/value')
                    },
                    'document_name': get_t(underlying, './/document_name'),
                    'document_number': get_t(underlying, './/document_number'),
                    'document_date': get_t(underlying, './/document_date'),
                })

            if right_info['owners']:
                item['rights'].append(right_info)

        dict_our['items'].append(item)

    return dict_our