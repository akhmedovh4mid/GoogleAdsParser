import logging
import sys
from datetime import datetime
from multiprocessing import Process
from typing import List

from uiautomator2 import Device

from src.config import settings
from src.app import GoogleParser
from src.utils import AdbDevicesManager
from src.utils import ArgsManager
from src.utils import get_logger, setup_logging

# Настраиваем логирование
setup_logging(level= logging.DEBUG, log_file=settings.path.log_file, console_output=True)
logger = get_logger(name="main.py")


class DeviceProcessLauncher:

    def __init__(self) -> None:
        self.args = ArgsManager().parse_args()
        self.device_manager = AdbDevicesManager()

    def _get_available_devices(self) -> List[str]:
        try:
            available_devices = self.device_manager.get_available_devices(
                target_serials=self.args.device_serials
            )

            if not available_devices:
                logger.warning(
                    "Не найдено устройств с серийными номерами: %s",
                    self.args.device_serials,
                )
                return []

            logger.info(
                "Найдено устройств: %s из %s. Доступные устройства: %s",
                len(available_devices),
                len(self.args.device_serials),
                available_devices,
            )

            missing_serials = set(self.args.device_serials) - set(available_devices)
            if missing_serials:
                logger.warning("Не найдены устройства: %s", list(missing_serials))

            return available_devices

        except Exception as e:
            logger.error("Ошибка при получении устройств: %s", str(e))
            return []

    def _device_worker(
        self,
        device_serial: str,
        result_dir: str,
    ) -> None:
        start_time = datetime.now()

        try:
            logger.info("[%s] Запуск worker процесса для устройства", device_serial)

            # Инициализация устройства
            device = Device(device_serial)
            logger.info("[%s] Устройство успешно инициализировано", device_serial)

            parser = GoogleParser(device=device, result_dir=result_dir)
            parser.run()

        except Exception as e:
            logger.error(
                "[%s] Критическая ошибка в worker процессе: %s",
                device_serial,
                str(e),
                exc_info=True,
            )
        finally:
            duration = datetime.now() - start_time
            logger.info(
                "[%s] Worker процесс завершен. Общее время работы: %s",
                device_serial,
                duration,
            )

    def _create_device_process(
        self,
        device_serial: str,
        result_dir: str,
    ) -> Process:
        return Process(
            name=f"Device-{device_serial}",
            target=self._device_worker,
            args=(device_serial, result_dir),
            daemon=True,
        )

    def run(self) -> None:
        available_devices = self._get_available_devices()
        if not available_devices:
            logger.error("Нет доступных устройств для обработки")
            sys.exit(1)

        processes = []
        start_time = datetime.now()

        logger.info("Запуск обработки на %s устройствах", len(available_devices))

        try:
            # Запускаем процессы для каждого устройства
            for device_serial in available_devices:
                process = self._create_device_process(
                    device_serial=device_serial,
                    result_dir=self.args.result_dir,
                )
                processes.append(process)
                process.start()
                logger.info("[%s] Запущен процесс для устройства", device_serial)

            # Ожидаем завершения всех процессов
            for process in processes:
                process.join()
                logger.info("[%s] Процесс завершен", process.name)

        except KeyboardInterrupt:
            logger.info("Получен сигнал прерывания, завершаем процессы...")
            for process in processes:
                if process.is_alive():
                    process.terminate()
                    logger.info("[%s] Процесс прерван", process.name)
        except Exception as e:
            logger.error("Критическая ошибка: %s", str(e), exc_info=True)
        finally:
            duration = datetime.now() - start_time
            logger.info("Общее время выполнения: %s", duration)

            # Завершаем программу
            sys.exit(0 if all(not p.is_alive() for p in processes) else 1)


if __name__ == "__main__":
    DeviceProcessLauncher().run()
