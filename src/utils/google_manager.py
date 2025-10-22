import time

from uiautomator2 import Device

from src.config import settings


class GoogleApp:
    """Класс для управления приложением Google через uiautomator2."""

    PACKAGE_NAME: str = "com.google.android.googlequicksearchbox"
    MAIN_ACTIVITY: str = "com.google.android.googlequicksearchbox.SearchActivity"

    def __init__(self, device: Device) -> None:
        """Инициализирует управление приложением Google.

        Args:
            device: Экземпляр устройства uiautomator2
        """

        self.device = device

    def start(self, wait: bool = True, timeout: float = 5.0) -> None:
        """Запускает приложение Google.

        Args:
            wait: Ожидать полной загрузки приложения
        """

        self.device.app_start(
            package_name=self.PACKAGE_NAME,
            activity=self.MAIN_ACTIVITY,
            # wait=wait,
            stop=True,
        )

        if wait:
            self.device.wait_activity(self.MAIN_ACTIVITY, timeout=timeout)

    def close(self, attempt: int = 6) -> None:
        """Закрывает приложение Google."""
        for _ in range(attempt):
            if "launcher" not in self.device.info.get("currentPackageName"):
                self.device.app_stop(package_name=self.PACKAGE_NAME)
            else:
                time.sleep(settings.timeout.action_timeout)
