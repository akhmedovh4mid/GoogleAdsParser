from typing import List, Optional

import adbutils
from adbutils import AdbDevice


class AdbDevicesManager:
    """Менеджер для работы с ADB устройствами."""

    def __init__(self) -> None:
        """Инициализирует менеджер устройств ADB."""

        self._devices: List[AdbDevice] = []
        self._serials: List[str] = []

    def _refresh_connected_devices(self) -> None:
        """Обновляет список подключенных устройств и их серийных номеров."""

        self._connected_devices = list(adbutils.adb.device_list())
        self._available_serials = [device.serial for device in self._connected_devices]

    def get_available_device(self, serial: str) -> Optional[str]:
        """Проверяет доступность устройства по серийному номеру.

        Args:
            serial: Серийный номер устройства для проверки

        Returns:
            Optional[str]: Серийный номер если устройство доступно, иначе None
        """

        self._refresh_connected_devices()
        if serial in self._available_serials:
            return serial
        return None

    def get_available_devices(self, target_serials: List[str]) -> List[str]:
        """Возвращает список доступных устройств из указанного списка.

        Args:
            target_serials: Список серийных номеров для проверки доступности

        Returns:
            List[str]: Список доступных серийных номеров
        """

        self._refresh_connected_devices()
        available_serials = []
        for serial in target_serials:
            if serial in self._available_serials:
                available_serials.append(serial)
        return available_serials
