from pathlib import Path
from typing import Optional
from zipfile import ZipFile, BadZipfile

from rs_logger import get_logger

logger = get_logger('rs_logger')

BASE_FIAS_PATH = Path("F:/Fias")
REGIONS_TO_EXTRACT = ['45', '72']


def get_extraction_path(filename: str, version: str) -> Optional[Path]:
    """Определяет путь для распаковки файла на основе его имени или папки."""
    path_parts = Path(filename).parts
    if len(path_parts) > 1:
        region = path_parts[0]
        if region in REGIONS_TO_EXTRACT:
            return BASE_FIAS_PATH / version / region

    if path_parts[0].startswith('AS_'):
        return BASE_FIAS_PATH / version / "public"

    return None


def extract_fias_contents(zip_file_path: str) -> str:
    version = ''
    try:
        with ZipFile(zip_file_path, 'r') as zip_object:
            # 1. Поиск версии
            for item in zip_object.infolist():
                if Path(item.filename).name.startswith('version'):
                    with zip_object.open(item.filename, 'r') as f:
                        version = f.readline().strip().decode('utf-8')
                    logger.warning(f'Версия базы {version}...')
                    break

            if not version:
                logger.error("Файл версии не найден в архиве.")
                return version

            # 2. Распаковка
            for item in zip_object.infolist():
                if item.is_dir() or Path(item.filename).name.startswith('version'):
                    continue

                target_dir = get_extraction_path(item.filename, version)

                if target_dir:
                    original_filename = Path(item.filename).name
                    parts = original_filename.split('_')

                    if len(parts) > 2:
                        clean_name = "_".join(parts[:-2])
                        extension = Path(original_filename).suffix
                        n_file = f"{clean_name}{extension}"
                    else:
                        n_file = original_filename

                    target_path = target_dir / n_file
                    target_dir.mkdir(parents=True, exist_ok=True)

                    logger.warning(f'Распаковка {original_filename} -> {target_path}')

                    with zip_object.open(item.filename) as source, open(target_path, 'wb') as target:
                        while True:
                            chunk = source.read(1024 * 1024)
                            if not chunk:
                                break
                            target.write(chunk)

    except BadZipfile:
        logger.error('Ошибка: Файл не является корректным ZIP-архивом.')
    except Exception as e:
        logger.error(f'Произошла ошибка при обработке архива: {e}')

    return version
