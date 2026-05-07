"""
    Конвертор адресного классификатора
    Версия 3.0.0

    logger.info(f"Увеличим память для обслуживания индексов...")
    async with pool.acquire() as conn:
        await conn.execute("SET maintenance_work_mem = '2GB';")
"""
import asyncio
import time
from datetime import datetime
from datetime import timedelta
from pathlib import Path

import asyncpg
from lxml import etree

from rs_logger import get_logger

logger = get_logger('rs_logger')

LIMIT = 7000
SCHEMA_NAME = 'rs'
MAX_CONCURRENT_FILES = 4

# Какие регионы загружать
FOLDERS = ["public", "45"]

DB_CONFIG = {
    'user': 'rs_admin',
    'password': 'q1w2e3r4t%',
    'database': 'rs-seven',
    'host': '10.8.8.77',
    'min_size': 10,
    'max_size': 20,
    'server_settings': {
        'search_path': 'public, rs'
    }
}


def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None


def safe_int(val):
    try:
        return int(val) if val else None
    except (ValueError, TypeError):
        return None


def to_int(val):
    """"""
    try:
        if val is None or val == '':
            return 0
        return int(val)
    except (ValueError, TypeError):
        return 0


def to_boolean(val):
    """"""
    try:
        if val is None or val == '':
            return False
        str_val = str(val).lower().strip()
        if str_val in ('1', 'true', 't', 'y', 'yes'):
            return True
        return False
    except (ValueError, TypeError):
        return False


MAPPING_FUNCS = {
    'i': to_int,
    's': lambda x: x or '-',
    'd': parse_date,
    'b': to_boolean
}

FILE_CONFIGS = {
    "AS_HOUSE_TYPES.XML": {
        "table": "nsi_gar_house_types",
        "fields": [
            ("ID", "i"), ("NAME", "s"), ("SHORTNAME", "s"), ("DESC", "s"), ("ISACTIVE", "b"),
            ("UPDATEDATE", "d"), ("STARTDATE", "d"), ("ENDDATE", "d")
        ],
        "fields_db": [
            "id", "name", "short_name", "desc", "is_active", "update_date", "start_date", "end_date"
        ],
        "tags": ("HOUSETYPE",)
    },
    "AS_ADDHOUSE_TYPES.XML": {
        "table": "nsi_gar_addhouse_types",
        "fields": [
            ("ID", "i"), ("NAME", "s"), ("SHORTNAME", "s"), ("DESC", "s"), ("ISACTIVE", "b"),
            ("UPDATEDATE", "d"), ("STARTDATE", "d"), ("ENDDATE", "d")
        ],
        "fields_db": [
            "id", "name", "short_name", "desc", "is_active", "update_date", "start_date", "end_date"
        ],
        "tags": ("HOUSETYPE",)
    },
    "AS_ADDR_OBJ_TYPES.XML": {
        "table": "nsi_gar_address_object_type",
        "fields": [
            ("ID", "i"), ("LEVEL", "i"), ("NAME", "s"), ("SHORTNAME", "s"), ("DESC", "s"), ("ISACTIVE", "b"),
            ("UPDATEDATE", "d"), ("STARTDATE", "d"), ("ENDDATE", "d")
        ],
        "fields_db": [
            "id", "level", "name", "short_name", "desc", "is_active", "update_date", "start_date", "end_date"
        ],
        "tags": ("ADDRESSOBJECTTYPE",)
    },
    "AS_ROOM_TYPES.XML": {
        "table": "nsi_gar_room_types",
        "fields": [
            ("ID", "i"), ("NAME", "s"), ("SHORTNAME", "s"), ("DESC", "s"), ("ISACTIVE", "b"),
            ("UPDATEDATE", "d"), ("STARTDATE", "d"), ("ENDDATE", "d")
        ],
        "fields_db": [
            "id", "name", "short_name", "desc", "is_active", "update_date", "start_date", "end_date"
        ],
        "tags": ("ROOMTYPE",)
    },
    "AS_APARTMENT_TYPES.XML": {
        "table": "nsi_gar_apartment_types",
        "fields": [
            ("ID", "i"), ("NAME", "s"), ("SHORTNAME", "s"), ("DESC", "s"), ("ISACTIVE", "b"),
            ("UPDATEDATE", "d"), ("STARTDATE", "d"), ("ENDDATE", "d")
        ],
        "fields_db": [
            "id", "name", "short_name", "desc", "is_active", "update_date", "start_date", "end_date"
        ],
        "tags": ("APARTMENTTYPE",)
    },
    "AS_OBJECT_LEVELS.XML": {
        "table": "nsi_gar_object_level",
        "fields": [
            ("LEVEL", "i"), ("NAME", "s"), ("STARTDATE", "d"), ("ENDDATE", "d"), ("UPDATEDATE", "d"), ("ISACTIVE", "b"),
        ],
        "fields_db": [
            'level', 'name', 'start_date', 'end_date', 'update_date', 'is_active'
        ],
        "tags": ("OBJECTLEVEL",),
        "id": "level"

    },
    "AS_OPERATION_TYPES.XML": {
        "table": "nsi_gar_operation_types",
        "fields": [
            ("ID", "i"), ("NAME", "s"), ("ISACTIVE", "b"),
            ("UPDATEDATE", "d"), ("STARTDATE", "d"), ("ENDDATE", "d")
        ],
        "fields_db": [
            "id", "name", "is_active", "update_date", "start_date", "end_date"
        ],
        "tags": ("OPERATIONTYPE",)
    },
    "AS_PARAM_TYPES.XML": {
        "table": "nsi_gar_param_types",
        "fields": [
            ("ID", "i"), ("NAME", "s"), ("CODE", "s"), ("DESC", "s"), ("ISACTIVE", "b"),
            ("UPDATEDATE", "d"), ("STARTDATE", "d"), ("ENDDATE", "d")
        ],
        "fields_db": [
            "id", "name", "code", "desc", "is_active", "update_date", "start_date", "end_date"
        ],
        "tags": ("PARAMTYPE",)
    },
    "AS_NORMATIVE_DOC.XML": {
        "table": "nsi_gar_normative_doc",
        "fields": [
            ("ID", "i"), ("NAME", "s")
        ],
        "fields_db": [
            "id", "name"
        ],
        "tags": ("NDOCKIND",)
    },
    "AS_NORMATIVE_DOCS.XML": {
        "table": "nsi_gar_normative_docs",
        "fields": [
            ("ID", "i"), ("NAME", "s"), ("DATE", "d"), ("NUMBER", "s"), ("UPDATEDATE", "d"), ("ORGNAME", "s"),
            ("REGNUMBER", "s"), ("REGDATE", "d"), ("DATE", "d"), ("COMMENT", "s"), ("KIND", "i"), ("TYPE", "i")
        ],
        "fields_db": [
            'id', 'name', 'date', 'number', 'update_date', 'org_name', 'reg_num', 'reg_date', 'acc_date', 'comment',
            'kind_id', 'type_id'
        ],
        "tags": ("NORMDOC",)
    },
    "AS_NORMATIVE_DOCS_KINDS.XML": {
        "table": "nsi_gar_normative_docs_kings",
        "fields": [
            ("ID", "i"), ("NAME", "s")
        ],
        "fields_db": [
            "id", "name"
        ],
        "tags": ("NDOCKIND",)
    },
    "AS_NORMATIVE_DOCS_TYPES.XML": {
        "table": "nsi_gar_normative_docs_types",
        "fields": [
            ("ID", "i"), ("NAME", "s")
        ],
        "fields_db": [
            "id", "name"
        ],
        "tags": ("NDOCTYPE",)
    },
    "AS_CARPLACES_PARAMS.XML": {
        "table": "nsi_gar_car_places_params",
        "fields": [
            ("ID", "i"), ("OBJECTID", "i"), ("CHANGEID", "i"), ("VALUE", "s"), ("UPDATEDATE", "d"), ("STARTDATE", "d"),
            ("ENDDATE", "d"), ("TYPEID", "i"), ("CHANGEIDEND", "i")
        ],
        "fields_db": [
            'id', 'object_id', 'change_id', 'value', 'update_date', 'start_date', 'end_date', 'type_id', 'change_id_end'
        ],
        "tags": ("PARAM",)
    },
    "AS_ADDR_OBJ_PARAMS.XML": {
        "table": "nsi_gar_address_object_params",
        "fields": [
            ("ID", "i"), ("OBJECTID", "i"), ("CHANGEID", "i"), ("VALUE", "s"), ("UPDATEDATE", "d"), ("STARTDATE", "d"),
            ("ENDDATE", "d"), ("TYPEID", "i"), ("CHANGEIDEND", "i")
        ],
        "fields_db": [
            'id', 'object_id', 'change_id', 'value', 'update_date', 'start_date', 'end_date', 'type_id', 'change_id_end'
        ],
        "tags": ("PARAM",)
    },
    "AS_ADDR_OBJ_DIVISION.XML": {
        "table": "nsi_gar_address_object_division",
        "fields": [
            ("ID", "i"), ("PARENTID", "i"), ("CHILDID", "i"), ("CHANGEIDEND", "i")
        ],
        "fields_db": [
            'id', 'parent_id', 'child_id', 'change_id'
        ],
        "tags": ("ITEM",)
    },

    "AS_ADDR_OBJ.XML": {
        "table": "nsi_gar_address_objects",
        "fields": [
            ("ID", "i"), ("OBJECTID", "i"), ("OBJECTGUID", "s"), ("CHANGEID", "i"), ("NAME", "s"), ("TYPENAME", "s"),
            ("PREVID", "i"), ("NEXTID", "i"), ("UPDATEDATE", "d"), ("STARTDATE", "d"), ("ENDDATE", "d"),
            ("ISACTUAL", "b"), ("ISACTIVE", "b"), ("LEVEL", "i"), ("OPERTYPEID", "i")
        ],
        "fields_db": [
            'id', 'object_id', 'object_guid', 'change_id', 'name', 'type_name', 'prev_id', 'next_id', 'update_date',
            'start_date', 'end_date', 'is_actual', 'is_active', 'level_type_id', 'operation_type_id'
        ],
        "tags": ("OBJECT",)
    },
    "AS_CHANGE_HISTORY.XML": {
        "table": "nsi_gar_change_history",
        "fields": [
            ("CHANGEID", "i"), ("OBJECTID", "i"), ("ADROBJECTID", "s"), ("NDOCID", "i"), ("CHANGEDATE", "d"),
            ("OPERTYPEID", "i")
        ],
        "fields_db": [
            'change_id', 'object_id', 'adr_object_id', 'normative_docs_id', 'change_date',
            'oper_type_id'
        ],
        "tags": ("ITEM",),
        "id": "change_id"
    },
    "AS_REESTR_OBJECTS.XML": {
        "table": "nsi_gar_reestr_objects",
        "fields": [
            ("OBJECTID", "i"), ("OBJECTGUID", "s"), ("CHANGEID", "i"), ("ISACTIVE", "b"), ("LEVELID", "i"),
            ("CREATEDATE", "d"), ("UPDATEDATE", "d")
        ],
        "fields_db": [
            'object_id', 'object_guid', 'change_id', 'is_active', 'level_id', 'create_date', 'update_date'
        ],
        "tags": ("OBJECT",),
        "id": "object_id"

    },
    "AS_ADM_HIERARCHY.XML": {
        "table": "nsi_gar_adm_hierarchy",
        "fields": [
            ("ID", "i"), ("OBJECTID", "i"), ("PARENTOBJID", "i"), ("CHANGEID", "i"), ("REGIONCODE", "s"),
            ("AREACODE", "s"),
            ("CITYCODE", "s"), ("PLACECODE", "s"), ("PLANCODE", "s"), ("STREETCODE", "s"),
            ("PREVID", "i"), ("NEXTID", "i"), ("UPDATEDATE", "d"),
            ("STARTDATE", "d"), ("ENDDATE", "d"),
            ("ISACTIVE", "b"), ("PATH", "s")
        ],
        "fields_db": [
            'id', 'object_id', 'parent_obj_id', 'change_id', 'region_code', 'area_code',
            'city_code', 'place_code', 'plan_code', 'street_code', 'prev_id', 'next_id', 'update_date',
            'start_date', 'end_date', 'is_active', 'path'

        ],
        "tags": ("ITEM",)
    },
    "AS_MUN_HIERARCHY.XML": {
        "table": "nsi_gar_mun_hierarchy",
        "fields": [
            ("ID", "i"), ("OBJECTID", "i"), ("PARENTOBJID", "i"), ("CHANGEID", "i"), ("OKTMO", "s"),
            ("PREVID", "i"), ("NEXTID", "i"), ("UPDATEDATE", "d"), ("STARTDATE", "d"), ("ENDDATE", "d"),
            ("ISACTIVE", "b"), ("PATH", "s")
        ],
        "fields_db": [
            'id', 'object_id', 'parent_obj_id', 'change_id', 'oktmo', 'prev_id', 'next_id', 'update_date',
            'start_date', 'end_date', 'is_active', 'path'

        ],
        "tags": ("ITEM",)
    },
    "AS_HOUSES.XML": {
        "table": "nsi_gar_houses",
        "fields": [
            ("ID", "i"), ("OBJECTID", "i"), ("OBJECTGUID", "s"), ("CHANGEID", "i"), ("HOUSENUM", "s"),
            ("ADDNUM1", "s"), ("ADDNUM2", "s"),
            ("PREVID", "i"), ("NEXTID", "i"), ("UPDATEDATE", "d"), ("STARTDATE", "d"), ("ENDDATE", "d"),
            ("ISACTUAL", "b"), ("ISACTIVE", "b"), ("OPERTYPEID", "i"), ("HOSETYPE", "i")
        ],
        "fields_db": [
            'id', 'object_id', 'object_guid', 'change_id', 'house_num', 'addnum1', 'addnum2', 'prev_id', 'next_id',
            'update_date',
            'start_date', 'end_date', 'is_actual', 'is_active', 'operation_type_id', 'house_type_id'

        ],
        "tags": ("HOUSE",)
    },
    "AS_HOUSES_PARAMS.XML": {
        "table": "nsi_gar_houses_params",
        "fields": [
            ("ID", "i"), ("OBJECTID", "i"), ("CHANGEID", "i"), ("CHANGEIDEND", "i"), ("VALUE", "s"),
            ("UPDATEDATE", "d"), ("STARTDATE", "d"), ("ENDDATE", "d"), ("TYPEID", "i")
        ],
        "fields_db": [
            'id', 'object_id', 'change_id', 'change_id_end', 'value', 'update_date',
            'start_date', 'end_date', 'type_id'

        ],
        "tags": ("PARAM",)
    },
    "AS_STEADS_PARAMS.XML": {
        "table": "nsi_gar_steads_params",
        "fields": [
            ("ID", "i"), ("OBJECTID", "i"), ("CHANGEID", "i"), ("CHANGEIDEND", "i"), ("VALUE", "s"),
            ("UPDATEDATE", "d"), ("STARTDATE", "d"), ("ENDDATE", "d"), ("TYPEID", "i")
        ],
        "fields_db": [
            'id', 'object_id', 'change_id', 'change_id_end', 'value', 'update_date',
            'start_date', 'end_date', 'type_id'

        ],
        "tags": ("PARAM",)
    },
    "AS_ROOMS.XML": {
        "table": "nsi_gar_rooms",
        "fields": [
            ("ID", "i"), ("OBJECTID", "i"), ("CHANGEID", "i"), ("OBJECTGUID", "s"), ("NUMBER", "s"),
            ("UPDATEDATE", "d"), ("STARTDATE", "d"), ("ENDDATE", "d"), ("ROOMTYPE", "i"), ("TYPEID", "i"),
            ("ISACTUAL", "b"), ("ISACTIVE", "b")
        ],
        "fields_db": [
            'id', 'object_id', 'change_id', 'object_guid', 'room_number', 'update_date',
            'start_date', 'end_date', 'room_type_id', 'oper_type_id', 'is_actual', 'is_active'

        ],
        "tags": ("ROOM",)
    },
    "AS_STEADS.XML": {
        "table": "nsi_gar_steads",
        "fields": [
            ("ID", "i"), ("OBJECTID", "i"), ("CHANGEID", "i"), ("OBJECTGUID", "s"), ("NUMBER", "s"),
            ("UPDATEDATE", "d"), ("STARTDATE", "d"), ("ENDDATE", "d"), ("TYPEID", "i"),
            ("ISACTUAL", "b"), ("ISACTIVE", "b")
        ],
        "fields_db": [
            'id', 'object_id', 'change_id', 'object_guid', 'number', 'update_date',
            'start_date', 'end_date', 'oper_type_id', 'is_actual', 'is_active'

        ],
        "tags": ("STEAD",)
    },
    "AS_CARPLACES.XML": {
        "table": "nsi_gar_car_places",
        "fields": [
            ("ID", "i"), ("OBJECTID", "i"), ("CHANGEID", "i"), ("OBJECTGUID", "s"), ("NUMBER", "s"),
            ("PREVID", "i"), ("NEXTID", "i"),
            ("UPDATEDATE", "d"), ("STARTDATE", "d"), ("ENDDATE", "d"), ("OPERTYPEID", "i"),
            ("ISACTUAL", "b"), ("ISACTIVE", "b")
        ],
        "fields_db": [
            'id', 'object_id', 'change_id', 'object_guid', 'number', 'prev_id', 'next_id',
            'update_date', 'start_date', 'end_date', 'oper_type_id', 'is_actual', 'is_active'

        ],
        "tags": ("CARPLACE",)
    },
    "AS_ROOMS_PARAMS.XML": {
        "table": "nsi_gar_rooms_params",
        "fields": [
            ("ID", "i"), ("OBJECTID", "i"), ("CHANGEID", "i"), ("CHANGEIDEND", "i"), ("VALUE", "s"),
            ("UPDATEDATE", "d"), ("STARTDATE", "d"), ("ENDDATE", "d"), ("TYPEID", "i")
        ],
        "fields_db": [
            'id', 'object_id', 'change_id', 'change_id_end', 'value', 'update_date',
            'start_date', 'end_date', 'type_id'

        ],
        "tags": ("PARAM",)
    },
    "AS_APARTMENTS.XML": {
        "table": "nsi_gar_apartments",
        "fields": [
            ("ID", "i"), ("OBJECTID", "i"), ("OBJECTGUID", "s"), ("CHANGEID", "i"), ("NUMBER", "s"),
            ("PREVID", "i"), ("NEXTID", "i"), ("UPDATEDATE", "d"), ("STARTDATE", "d"), ("ENDDATE", "d"),
            ("ISACTUAL", "b"), ("ISACTIVE", "b"), ("APARTTYPE", "i"), ("OPERTYPEID", "i")
        ],
        "fields_db": [
            'id', 'object_id', 'object_guid', 'change_id', 'number', 'prev_id', 'next_id', 'update_date', 'start_date',
            'end_date', 'is_actual', 'is_active', 'apart_type_id', 'oper_type_id'

        ],
        "tags": ("APARTMENT",)
    },
    "AS_APARTMENTS_PARAMS.XML": {
        "table": "nsi_gar_apartment_params",
        "fields": [
            ("ID", "i"), ("OBJECTID", "i"), ("CHANGEID", "i"), ("CHANGEIDEND", "i"), ("VALUE", "s"),
            ("UPDATEDATE", "d"), ("STARTDATE", "d"), ("ENDDATE", "d"), ("TYPEID", "i")
        ],
        "fields_db": [
            'id', 'object_id', 'change_id', 'change_id_end', 'value', 'update_date',
            'start_date', 'end_date', 'type_id'

        ],
        "tags": ("PARAM",)
    },

}


async def import_fias(base_path="F:/Fias/2026.05.05/", clean_start=False):
    """
    Подготовка файлов
    :param base_path: Базовый каталог загрузки
    :param clean_start: Очистка таблиц
    :return:
    """
    start_time = time.time()

    pool = await asyncpg.create_pool(**DB_CONFIG, command_timeout=3600)

    try:
        if clean_start:
            logger.info("ВНИМАНИЕ: Запущена полная очистка таблиц ГАР перед импортом...")
            async with pool.acquire() as conn:
                await conn.execute(f"CALL {SCHEMA_NAME}.prc_truncate_gar_tables();")
            logger.info("Очистка завершена.")
        else:
            logger.info("Режим обновления: данные будут добавлены или изменены (UPSERT).")

        for folder in FOLDERS:
            current_path = Path(base_path) / folder
            if not current_path.exists():
                logger.warning(f"Путь не найден, пропускаю: {current_path}")
                continue

            xml_files = list(Path(current_path).glob('*.xml'))
            logger.info(f"Найдено файлов для обработки: {len(xml_files)}")

            sem = asyncio.Semaphore(MAX_CONCURRENT_FILES)

            async def sem_task(file):
                async with sem:
                    await process_xml(pool, file)

            if xml_files:
                tasks = [sem_task(f) for f in xml_files]
                await asyncio.gather(*tasks)
                logger.info(f"Папка {folder} полностью загружена.")

        logger.info("Все регионы загружены. Начинаю сборку поисковой витрины...")
        async with pool.acquire() as conn:
            await conn.execute(f"CALL {SCHEMA_NAME}.prc_refresh_address_search_data_a();")

        logger.info("Сборка завершена. Очистка мусора (VACUUM)...")
        async with pool.acquire() as conn:
            await conn.execute("VACUUM ANALYZE rs.address_search_data;")

        logger.info("Поисковая витрина успешно обновлена!")

    except Exception as e:
        logger.warning(f"Критическая ошибка во время импорта: {e}")

    finally:
        if pool:
            await pool.close()
            logger.warning(f"Пул соединений успешно закрыт.")

            end_time = time.time()
            total_duration = end_time - start_time

            logger.info(f"Общее время: {str(timedelta(seconds=int(total_duration)))}")


async def process_xml(pool, file_path):
    """Загрузка файлов"""
    config = None
    sorted_configs = sorted(FILE_CONFIGS.items(), key=lambda x: len(x[0]), reverse=True)
    # parts = file_path.name.split('_')

    # for key, cfg in FILE_CONFIGS.items():
    for key, cfg in sorted_configs:
        if key in file_path.name:
            # if any(key == f"{parts[i]}_{parts[i + 1]}_{parts[i + 2]}" for i in range(len(parts) - 2)):
            config = cfg
            break

    if not config:
        logger.warning(f"Пропуск: нет конфига для {file_path.name}")
        return

    columns = [f.lower() for f in config["fields_db"]]

    temp_table = f"loading_{config['table']}_{asyncio.get_event_loop().time()}".replace('.', '_')

    async with pool.acquire() as conn:

        logger.info(f"Начинаю грузить: {file_path.name}")

        await conn.execute(f"CREATE UNLOGGED TABLE {SCHEMA_NAME}.{temp_table} (LIKE {SCHEMA_NAME}.{config['table']})")

        try:
            context = etree.iterparse(file_path, events=('end',), tag=config['tags'])

            batch = []
            count = 0

            for _, elem in context:
                row = []

                for attr_name, func_type in config["fields"]:
                    raw_val = elem.get(attr_name)
                    processed_val = MAPPING_FUNCS[func_type](raw_val)
                    row.append(processed_val)

                batch.append(row)

                if len(batch) >= LIMIT:
                    await conn.copy_records_to_table(
                        temp_table,
                        schema_name=SCHEMA_NAME,
                        records=batch,
                        columns=columns
                    )
                    count += len(batch)
                    logger.info(f"Загружено в {temp_table}: {count} строк...")
                    batch = []

                elem.clear()
                while elem.getprevious() is not None:
                    del elem.getparent()[0]

            if batch:
                logger.info(f"Окончание загрузки {file_path.name}, {temp_table}")
                await conn.copy_records_to_table(
                    temp_table,
                    schema_name=SCHEMA_NAME,
                    records=batch,
                    columns=columns
                )

            cols_str = ", ".join([f'"{c}"' for c in columns])
            update_str = ", ".join([f'"{c}" = EXCLUDED."{c}"' for c in columns if c != 'id'])
            id_key = config.get("id", 'id')

            logger.info(f"Слияние таблицы {SCHEMA_NAME}.{temp_table} в {SCHEMA_NAME}.{config['table']}...")

            await conn.execute(f"""
                INSERT INTO {SCHEMA_NAME}.{config['table']} ({cols_str})
                SELECT {cols_str} FROM {SCHEMA_NAME}.{temp_table}                                
                ON CONFLICT ({id_key}) DO UPDATE SET {update_str}
            """)
        except Exception as err_process:
            logger.error(f"Ошибка: {err_process}, {temp_table}")

        finally:
            await conn.execute(f"DROP TABLE IF EXISTS {SCHEMA_NAME}.{temp_table}")
            logger.warning(f"Готово: {file_path.name}")
