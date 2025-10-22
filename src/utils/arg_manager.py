from argparse import ArgumentParser
from dataclasses import dataclass
from typing import List


@dataclass
class ArgsResult:
    """Результат парсинга аргументов командной строки."""

    device_serials: List[str]
    result_dir: str


class ArgsManager:
    """Менеджер для обработки аргументов командной строки."""

    def __init__(self) -> None:
        self.parser = ArgumentParser(description="Парсер рекламы YouTube")
        self._add_arguments()

    def _add_arguments(self) -> None:
        """Добавляет аргументы командной строки."""

        self.parser.add_argument(
            "-s",
            "--serials",
            nargs="+",
            help="Список серийных номеров устройств",
            required=True,
        )
        self.parser.add_argument(
            "-r",
            "--result-dir",
            type=str,
            default="result",
            help="Путь к папке куда будут сохранены результаты (по умолчанию: results)",
        )

    def parse_args(self) -> ArgsResult:
        """Парсит аргументы командной строки.

        Returns:
            ArgsResult: Объект с распарсенными аргументами
        """

        parsed_args = self.parser.parse_args()
        return ArgsResult(
            device_serials=parsed_args.serials,
            result_dir=parsed_args.result_dir,
        )
