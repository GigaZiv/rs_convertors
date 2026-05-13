"""

"""
import xml.etree.ElementTree as ET
from typing import Any, Dict, List


def parse_rosreestr_xml(file_path: str) -> List[Dict[str, Any]]:
    """
    Универсальный парсер Росреестра для Docker-агента.
    Поддерживает: Участки, Здания, Помещения, Сооружения.
    Координаты: WKT (метры) для трансформации в SQL.
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception:
        return []

    def get_t(node, path, default=''):
        if node is None: return default
        found = node.find(path)
        return found.text if found is not None and found.text else default

    # 1. Дата выписки (общая для всего файла)
    extract_date = get_t(root, ".//date_formation") or get_t(root, ".//date_received_request")
    organ_registr_rights = get_t(root, ".//organ_registr_rights")
    registration_number = get_t(root, ".//registration_number")

    items = []
    # Теги всех возможных типов объектов
    record_tags = [".//land_record", ".//build_record", ".//room_record", ".//construction_record"]

    for tag in record_tags:
        for record in root.findall(tag):
            item = {
                'cad_number': get_t(record, ".//common_data/cad_number"),
                'quarter_cad_number': get_t(record, ".//common_data/quarter_cad_number"),
                'extract_date': extract_date,
                # 'organ_registr_rights': organ_registr_rights,
                # 'registration_number': registration_number,
                'type_value': get_t(record, ".//common_data/type/value") or "Объект недвижимости",
                'category_value': get_t(record, ".//category/type/value") or get_t(record, ".//params/category/value"),
                'permitted_use': get_t(record, ".//permitted_use_established/by_document") or get_t(record,
                                                                                                    ".//params/purpose/value"),
                'address': get_t(record, ".//address/readable_address") or get_t(record,
                                                                                 ".//address_location/address/readable_address"),
                'cost': get_t(record, ".//cost/value"),
                'area': get_t(record, ".//params/area"),
                'floors': get_t(record, ".//params/floors"),
                'year_built': get_t(record, ".//params/year_built"),
                'wkt_meters': None,
                'sk_id': None,
                'rights': [],
                'related_cad_numbers': []
            }

            # --- ГЕОМЕТРИЯ (WKT метры) ---
            polygons_raw = []
            contour_nodes = record.findall(".//contours/contour") or record.findall(".//location/contours/contour")
            for contour in contour_nodes:
                if not item['sk_id']:
                    item['sk_id'] = get_t(contour, ".//sk_id") or get_t(contour, ".//entity_spatial/sk_id")

                spatial_elements = contour.findall(".//spatial_element") or \
                                   contour.findall(".//entity_spatial/spatials_elements/spatial_element") or \
                                   ([contour] if contour.find(".//ordinate") is not None else [])

                for s_elem in spatial_elements:
                    points = []
                    for ord_node in s_elem.findall(".//ordinate"):
                        y_v = get_t(ord_node, "y").replace(',', '.')
                        x_v = get_t(ord_node, "x").replace(',', '.')
                        if x_v and y_v:
                            points.append(f"{y_v} {x_v}")  # Порядок Y X для SQL

                    if len(points) >= 3:
                        if points != points[-1]: points.append(points[0])  # Замыкаем
                        polygons_raw.append(f"(({', '.join(points)}))")

            if polygons_raw:
                item['wkt_meters'] = f"MULTIPOLYGON({', '.join(polygons_raw)})"

            # --- СВЯЗАННЫЕ ОБЪЕКТЫ ---
            cad_links = record.find(".//cad_links")
            if cad_links is not None:
                item['related_cad_numbers'] = list(set([n.text for n in cad_links.findall(".//cad_number") if n.text]))

            # --- ПРАВА И СОБСТВЕННИКИ ---
            # Ищем права внутри объекта или в корне файла
            right_records = record.findall(".//right_record") or root.findall(".//right_record")
            for rr in right_records:
                right_info = {
                    'right_type': get_t(rr, ".//right_data/right_type/value"),
                    'reg_number': get_t(rr, ".//registration/reg_number"),
                    'reg_date': get_t(rr, ".//registration/reg_date"),
                    'owners': [],
                    'underlying_documents': []
                }

                # Собственники и паспорта
                for holder in rr.findall(".//right_holders/right_holder"):
                    surname, name, patronymic = get_t(holder, ".//surname"), get_t(holder, ".//name"), get_t(holder,
                                                                                                       ".//patronymic")
                    full_name = f"{surname} {name} {patronymic}".strip()
                    if not full_name:
                        full_name = get_t(holder, ".//legal_entity/entity_common_data/name") or \
                                    get_t(holder, ".//public_formation/public_formation_type/value")

                    right_info['owners'].append({
                        'name': full_name or "Сведения ограничены (266-ФЗ)",
                        'inn': get_t(holder, ".//inn"),
                        'birth_date': get_t(holder, ".//birth_date"),
                        'identity_doc': {
                            'name': get_t(holder, ".//identity_doc/document_name") or get_t(holder,
                                                                                            ".//identity_doc/document_code/value"),
                            'series': get_t(holder, ".//identity_doc/document_series"),
                            'number': get_t(holder, ".//identity_doc/document_number"),
                            'date': get_t(holder, ".//identity_doc/document_date"),
                            'issuer': get_t(holder, ".//identity_doc/document_issuer")
                        },
                        'share': get_t(rr, ".//right_data/shares/share/value_text")
                    })

                # Документы-основания
                for und in rr.findall(".//underlying_documents/underlying_document"):
                    right_info['underlying_documents'].append({
                        'document_name': get_t(und, './/document_name'),
                        'document_number': get_t(und, './/document_number'),
                        'document_date': get_t(und, './/document_date'),
                        'document_code': get_t(und, './/code/value') or get_t(und, './/code')
                    })

                if right_info['owners']:
                    item['rights'].append(right_info)

            items.append(item)

    return items
