from __future__ import annotations

import sys
import platform
import subprocess
from typing import List

from src.utils import get_logger, setup_logging
from src.utils import ArgsManager, ArgsResult
from src.config import settings

# Настраиваем логирование
setup_logging(log_file=settings.path.log_file, console_output=True)
logger = get_logger(name="start.py")


class VenvManager:
    """Менеджер виртуального окружения."""

    def __init__(self) -> None:
        self.requirements = self._get_requirements()
        self.is_windows = platform.system() == "Windows"
        self.scripts_dir = "Scripts" if self.is_windows else "bin"

        self.python_path = (
            settings.path.venv_path
            / self.scripts_dir
            / ("python.exe" if self.is_windows else "python")
        )

    def _get_requirements(self) -> List[str]:
        """Получает список зависимостей из requirements.txt."""

        if not settings.path.requirements_path.exists():
            logger.warning("Файл требований %s не найден", settings.path.requirements_path)
            return []

        if not settings.path.requirements_path.is_file():
            logger.warning("%s не является файлом", settings.path.requirements_path)
            return []

        try:
            with settings.path.requirements_path.open("r", encoding="utf-8") as file:
                requirements = []
                for line in file:
                    line = line.strip()
                    # Пропускаем пустые строки и комментарии
                    if line and not line.startswith("#"):
                        requirements.append(line)
                return requirements
        except UnicodeDecodeError:
            logger.error("Ошибка декодирования файла %s", settings.path.requirements_path)
            return []

    def _create_venv(self) -> bool:
        """Создает виртуальное окружение."""

        try:
            if settings.path.venv_path.exists():
                logger.info("Виртуальное окружение '%s' уже существует", settings.path.venv_path)
                return True

            logger.info("Создаем виртуальное окружение '%s'...", settings.path.venv_path)
            result = subprocess.run(
                [sys.executable, "-m", "venv", str(settings.path.venv_path)],
                check=True,
                capture_output=True,
                text=True,
                timeout=300,  # Таймаут 5 минут
            )

            if result.stdout:
                logger.debug("Вывод создания venv: %s", result.stdout)
            logger.info("Виртуальное окружение успешно создано")
            return True

        except subprocess.CalledProcessError as e:
            logger.error("Ошибка при создании venv: %s", e)
            if e.stderr:
                logger.error("Stderr: %s", e.stderr)
            return False
        except subprocess.TimeoutExpired:
            logger.error("Таймаут при создании виртуального окружения")
            return False
        except Exception as e:
            logger.exception("Непредвиденная ошибка при создании venv: %s", e)
            return False

    def _install_packages(self) -> bool:
        """Устанавливает пакеты в виртуальное окружение."""

        if not self.requirements:
            logger.info("Нет пакетов для установки")
            return True

        try:
            # Обновление pip
            logger.info("Обновление pip...")
            update_cmd = [
                str(self.python_path),
                "-m",
                "pip",
                "install",
                "--upgrade",
                "pip",
            ]
            subprocess.run(update_cmd, check=True, capture_output=True, timeout=600)
            logger.info("Pip успешно обновлен")

            # Установка всех пакетов одной командой (быстрее)
            logger.info("Установка пакетов...")
            install_cmd = [
                str(self.python_path),
                "-m",
                "pip",
                "install",
            ] + self.requirements
            result = subprocess.run(
                install_cmd,
                capture_output=True,
                text=True,
                timeout=1200,  # Таймаут 20 минут
            )

            if result.returncode != 0:
                logger.error("Ошибка установки пакетов: %s", result.stderr)
                return False

            logger.info("Все пакеты успешно установлены")
            return True

        except subprocess.CalledProcessError as e:
            logger.error("Ошибка при обновлении pip: %s", e.stderr)
            return False
        except subprocess.TimeoutExpired:
            logger.error("Таймаут при установке пакетов")
            return False
        except Exception as e:
            logger.exception("Непредвиденная ошибка при установке пакетов: %s", e)
            return False

    def _verify_installation(self) -> bool:
        """Проверяет успешность установки пакетов."""

        if not self.requirements:
            return True

        try:
            result = subprocess.run(
                [str(self.python_path), "-m", "pip", "list", "--format", "freeze"],
                capture_output=True,
                text=True,
                check=True,
            )

            installed_packages = {
                line.split("==")[0].lower(): line.split("==")[1]
                for line in result.stdout.splitlines()
                if "==" in line
            }

            missing_packages = []
            for req in self.requirements:
                pkg_name = (
                    req.split(">")[0]
                    .split("<")[0]
                    .split("=")[0]
                    .split("[")[0]
                    .strip()
                    .lower()
                )
                if pkg_name not in installed_packages:
                    missing_packages.append(req)

            if missing_packages:
                logger.warning(
                    "Не удалось установить пакеты: %s", ", ".join(missing_packages)
                )
                return False

            logger.info("Все пакеты успешно установлены и проверены")
            return True

        except subprocess.CalledProcessError as e:
            logger.error("Ошибка при проверке пакетов: %s", e.stderr)
            return False
        except Exception as e:
            logger.exception("Ошибка при проверке пакетов: %s", e)
            return False

    def build(self) -> bool:
        """Создает и настраивает виртуальное окружение."""

        logger.info("=== Начало настройки окружения ===")

        if not self._create_venv():
            logger.error("Создание venv завершилось с ошибкой")
            return False

        if not self._install_packages():
            logger.error("Установка пакетов завершилась с ошибкой")
            return False

        if not self._verify_installation():
            logger.warning("Некоторые пакеты не установились корректно")

        logger.info("=== Конец настройки окружения ===")
        return True


def setup_environment() -> bool:
    """Настраивает виртуальное окружение."""

    venv_manager = VenvManager()

    if not settings.path.venv_path.exists():
        return venv_manager.build()

    # Проверяем, что окружение рабочее
    if not venv_manager.python_path.exists():
        logger.warning("Обнаружена поврежденная виртуальная среда, пересоздаем...")
        # Удаляем и создаем заново
        import shutil

        shutil.rmtree(settings.path.venv_path)
        return venv_manager.build()

    return True


def run_main_script(args: ArgsResult) -> bool:
    """Запускает основной скрипт в виртуальном окружении."""

    if not settings.path.main_script_path.exists():
        logger.error("Ошибка: Файл %s не найден!", settings.path.main_script_path)
        return False

    venv_manager = VenvManager()

    # Формируем команду для запуска
    cmd_args = [    
        str(venv_manager.python_path),
        str(settings.path.main_script_path),
        "-s",
        *args.device_serials,
        "-m",
        args.processing_mode,
        "-l",
        str(args.links_file_path),
    ]

    try:
        logger.info("Запуск %s...", settings.path.main_script_path)
        result = subprocess.run(cmd_args, check=True, timeout=3600)  # Таймаут 1 час
        return result.returncode == 0

    except subprocess.CalledProcessError as e:
        logger.error("Ошибка при выполнении скрипта: %s", e)
        return False
    except subprocess.TimeoutExpired:
        logger.error("Таймаут при выполнении основного скрипта")
        return False
    except KeyboardInterrupt:
        logger.info("Выполнение прервано пользователем")
        return False
    except Exception as e:
        logger.exception("Непредвиденная ошибка: %s", e)
        return False


def main() -> None:
    """Основная функция."""

    try:
        # Парсинг аргументов
        args = ArgsManager().parse_args()

        # Настройка окружения
        if not setup_environment():
            sys.exit(1)

        # Запуск основного скрипта
        success = run_main_script(args)
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.info("Программа прервана пользователем")
        sys.exit(1)
    except Exception as e:
        logger.exception("Критическая ошибка: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
