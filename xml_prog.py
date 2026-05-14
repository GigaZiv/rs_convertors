import os
import xml.etree.ElementTree as ET

from convertors.rs_cnv_format import parse_rosreestr_xml

def process_folder(folder_path):
    """"""
    for filename in os.listdir(folder_path):
        if filename.endswith('.xml'):
            process_file(os.path.join(folder_path, filename))

def get_root_tag(file_path):
    """Быстро достает имя корневого тега без парсинга всего файла"""
    try:
        # Читаем только начало файла для экономии памяти
        context = ET.iterparse(file_path, events=('start',))
        _, elem = next(context)
        return elem.tag.split('}')[-1]

    except FileNotFoundError:
        print(f"Ошибка: Файл не найден по пути {file_path}")
        return None

    except (PermissionError, IsADirectoryError) as e:
        print(f"Ошибка доступа к файлу: {e}")
        return None

    except StopIteration:
        print("Ошибка: XML-файл абсолютно пустой")
        return None

    except (ET.ParseError, UnicodeDecodeError) as e:
        print(f"Ошибка синтаксиса или кодировки XML: {e}")
        return None

    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")
        return None

def process_file(file_path):
    tag = get_root_tag(file_path)

    # Список тегов, которые мы умеем обрабатывать нашей универсальной функцией
    ALLOWED_TAGS = [
        'extract_base_params_land',
        'extract_base_params_build',
        'extract_base_params_room',
        'extract_base_params_construction'
    ]

    if tag in ALLOWED_TAGS:
        print(f"Обработка {os.path.basename(file_path)} (Тип: {tag})...")
        data = parse_rosreestr_xml(file_path, str(tag))
        return data
    else:
        print(f"Пропуск: Тип '{tag}' в файле {os.path.basename(file_path)} не поддерживается.")
        return None
