import logging
import sys
from pathlib import Path
from typing import Optional

# Создаем корневой логгер проекта
ROOT_LOGGER = logging.getLogger("google-parser")


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    console_output: bool = True,
) -> None:
    """Настраивает глобальное логирование для всего проекта.

    Args:
        level: Уровень логирования
        log_file: Путь к файлу для записи логов
        console_output: Выводить ли логи в консоль
    """

    # Очищаем существующие обработчики
    ROOT_LOGGER.handlers.clear()

    # Устанавливаем уровень
    ROOT_LOGGER.setLevel(level)

    # Форматтер
    formatter = logging.Formatter(
        "[%(asctime)s] [%(name)s] [%(levelname)s] - %(message)s",
        datefmt="%m-%d %H:%M:%S",
    )

    # Обработчик для консоли
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        ROOT_LOGGER.addHandler(console_handler)

    # Обработчик для файла
    if log_file:
        # Создаем директорию если нужно
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        ROOT_LOGGER.addHandler(file_handler)

    # Отключаем propagation для избежания дублирования
    ROOT_LOGGER.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Возвращает логгер с указанным именем.

    Args:
        name: Имя логгера (обычно __name__ модуля)

    Returns:
        Настроенный логгер
    """

    return ROOT_LOGGER.getChild(name)
