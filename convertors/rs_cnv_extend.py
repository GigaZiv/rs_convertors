"""


    Формат Геометрии: В коде выше я предполагаю, что ваш Python-агент внутри parse_generic_xml не просто
    трансформирует точки, а собирает их в строку WKT (например, POLYGON((lon1 lat1, lon2 lat2, ...))).
    Это проще всего передать в SQL.
"""
import xml.etree.ElementTree as ET
import json

def to_wkt(contours):
    polys = []
    for c in contours:
        for elem in c['elements']:
            pts = [f"{p['lon']} {p['lat']}" for p in elem]
            polys.append(f"(({', '.join(pts)}))")
    return f"MULTIPOLYGON({', '.join(polys)})" if polys else None


def xml_to_dict(element):
    # Убираем пространство имен (Namespace) из тега, если оно есть
    tag = element.tag.split('}')[-1]

    res = {}
    # Обрабатываем атрибуты (например, <tag id="123">)
    for key, value in element.attrib.items():
        res[f"@{key}"] = value

    # Обрабатываем дочерние элементы
    for child in element:
        child_res = xml_to_dict(child)
        child_tag = child.tag.split('}')[-1]

        if child_tag not in res:
            res[child_tag] = child_res
        else:
            # Если тегов с одним именем несколько, делаем из них список
            if not isinstance(res[child_tag], list):
                res[child_tag] = [res[child_tag]]
            res[child_tag].append(child_res)

    # Если у узла нет детей, но есть текст (например, <name>Иван</name>)
    if not res:
        return element.text

    return res


# Запуск
tree = ET.parse('vypiska.xml')
root = tree.getroot()
json_data = json.dumps({root.tag.split('}')[-1]: xml_to_dict(root)}, ensure_ascii=False, indent=2)
