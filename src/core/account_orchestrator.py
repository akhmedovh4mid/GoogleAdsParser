import time
from typing import Optional

from uiautomator2 import Device

from src.utils import get_logger

from .main_class import MainClass

logger = get_logger(name="account-switcher")


class AccountSwitcher(MainClass):
    """Класс для управления сменой аккаунтов пользователя."""

    def __init__(
        self,
        device: Device,
    ) -> None:
        """
        Инициализация AccountSwitcher.

        Args:
            device: Экземпляр устройства uiautomator2
        """
        super().__init__(device=device)
        logger.debug("AccountSwitcher инициализирован")

    def get_current_user(self) -> Optional[str]:
        """
        Получает email текущего активного пользователя.

        Returns:
            Email текущего пользователя или None, если не удалось определить
        """
        logger.debug("Получение текущего пользователя")

        if not self.nodes.buttons.selected_account.exists:
            logger.debug("Элемент выбранного аккаунта не найден")
            return None

        text: str = self.nodes.buttons.selected_account.info.get("contentDescription")
        if not text:
            logger.debug("Описание аккаунта пустое")
            return None

        lines = text.split("\n")
        email = None
        for line in lines:
            if "@" in line:
                words = line.split(" ")
                for word in words:
                    if "@" in word:
                        email = word.strip()
                        break

        if not email:
            logger.debug("Email не найден в описании аккаунта")
            return None

        email = email.split(" ")[-1] if " " in email else email
        logger.debug("Текущий пользователь: %s", email)

        return email

    def change_user(
        self,
        email: str,
        timeout: int = 15,
        enter_back_timeout: float = 0.5,
    ) -> None:
        """
        Выполняет смену текущего пользователя на указанный аккаунт.

        Args:
            email: Email аккаунта для переключения
            timeout: Таймаут ожидания элементов в секундах
            edge_offset: Смещение для свайпа
            enter_back_timeout: Таймаут после выбора аккаунта

        Raises:
            Exception: В случае критических ошибок при взаимодействии с UI
        """
        logger.info("Начало смены пользователя на: %s", email)

        # Открываем меню выбора аккаунта
        logger.debug("Открытие меню выбора аккаунта")
        self.nodes.buttons.selected_account.click_exists(timeout=timeout)

        # Переходим к списку аккаунтов
        logger.debug("Переход к списку аккаунтов")
        if not self.nodes.accounts.account_management.exists:
            self.nodes.accounts.accounts_label.click_exists(timeout=timeout)
        self.nodes.accounts.account_management.click_exists(timeout=timeout)

        # Прокручиваем список аккаунтов
        logger.debug("Прокрутка списка аккаунтов")
        accounts_box_coords = self.nodes.accounts.accounts.bounds()
        accounts_scroll_container = (
            self.nodes.accounts.accounts_scroll_container.bounds()
        )

        self._swipe(
            start_y=accounts_box_coords[1],
            end_y=accounts_scroll_container[1],
        )

        # Поиск и выбор нужного аккаунта
        logger.debug("Поиск аккаунта %s в списке", email)
        accounts = self.nodes.accounts.accounts_info
        account_found = False
        for account in accounts:
            if account.info["text"] == email:
                account.click_exists(timeout=timeout)
                account_found = True
                logger.info("Аккаунт %s успешно выбран", email)
                time.sleep(enter_back_timeout)
                break

        if not account_found:
            logger.warning("Аккаунт с email %s не найден в списке", email)

        # Возврат на ленту новостей
        logger.debug("Возврат на ленту новостей")
        self._back_to_feed_news()
        logger.info("Смена пользователя завершена")
