from typing import Optional, Tuple

from PIL.Image import Image
from uiautomator2 import Device, UiObject

from src.elements import Buttons, Classes
from src.utils import Tesseract, get_logger

from .main_class import MainClass

logger = get_logger(name="data-interpreter")


class DataInterpreter(MainClass):
    """Класс для извлечения и интерпретации данных из UI элементов."""

    def __init__(
        self,
        device: Device,
    ) -> None:
        super().__init__(device=device)

    def _get_largest_image_node(
        self,
        node: UiObject,
    ) -> Optional[UiObject]:
        """
        Находит дочерний элемент с наибольшей высотой среди ImageView.

        Args:
            node: Родительский UI элемент

        Returns:
            UiObject или None, если подходящий элемент не найден
        """
        image_nodes = node.child(**Classes.image_view)
        candidate_node = None
        max_height = 0

        for image_node in image_nodes:
            try:
                node_bounds = image_node.bounds()
                node_height = node_bounds[3] - node_bounds[1]

                if node_height > max_height:
                    candidate_node = image_node
                    max_height = node_height
            except Exception as e:
                logger.warning(f"Ошибка при обработке элемента изображения: {e}")
                continue

        return candidate_node

    def _extract_text_from_description(
        self,
        node: UiObject,
    ) -> Optional[str]:
        """
        Извлекает текст из contentDescription кнопки share.

        Args:
            node: UI элемент с кнопкой share

        Returns:
            Извлеченный текст или None
        """
        share_button = node.child(**Buttons.share)
        if not share_button.exists:
            logger.debug("Кнопка share не найдена")
            return None

        node_desc = share_button.info.get("contentDescription", "")
        if node_desc:
            text = node_desc.replace("Share ", "").strip()
            return text if text else None

        return None

    def _find_sponsored_node(
        self,
        node: UiObject,
    ) -> Optional[UiObject]:
        """
        Находит элемент, содержащий текст 'sponsored'.

        Args:
            node: Родительский UI элемент

        Returns:
            UiObject или None, если элемент не найден
        """
        view_group_nodes = node.child(**Classes.view_group)

        for view_node in view_group_nodes:
            try:
                if Tesseract.find_matches_by_word(
                    image=view_node.screenshot(), target_word="sponsored"
                ):
                    if Tesseract.find_matches_by_word(
                        image=view_node.screenshot(), target_word="google play:"
                    ):
                        return None
                    return view_node
            except Exception as e:
                logger.warning(f"Ошибка при обработке view group элемента: {e}")
                continue

        logger.debug("Элемент со словом 'sponsored' не найден")
        return None

    def _extract_link_from_content(
        self,
        content_text: str,
    ) -> Optional[str]:
        """
        Извлекает ссылку из текста контента.

        Args:
            content_text: Текст содержащий ссылку

        Returns:
            Извлеченная ссылка или None
        """
        if not content_text:
            return None

        parts = content_text.strip().split()
        return parts[-1] if parts else None

    def get_image(
        self,
        node: UiObject,
    ) -> Optional[Image]:
        """
        Получает скриншот наибольшего изображения в элементе.

        Args:
            node: Родительский UI элемент

        Returns:
            PIL Image или None, если изображение не найдено
        """
        try:
            image_node = self._get_largest_image_node(node)
            if image_node:
                return image_node.screenshot()

            logger.debug("Элементы изображений не найдены")
            return None

        except Exception as e:
            logger.error(f"Ошибка при получении изображения: {e}")
            return None

    def get_text(
        self,
        node: UiObject,
    ) -> Optional[str]:
        """
        Получает текст из элемента через кнопку share.

        Args:
            node: Родительский UI элемент

        Returns:
            Текст или None, если текст не найден
        """
        try:
            return self._extract_text_from_description(node)
        except Exception as e:
            logger.error(f"Ошибка при извлечении текста: {e}")
            return None

    def get_link(
        self,
        node: UiObject,
        timeout: int = 10,
    ) -> Optional[str]:
        """
        Получает ссылку из спонсируемого контента.

        Args:
            node: Родительский UI элемент
            timeout: Таймаут ожидания элементов

        Returns:
            Ссылка или None, если ссылка не найдена
        """
        try:
            # Находим спонсируемый элемент
            sponsored_node = self._find_sponsored_node(node)
            if not sponsored_node:
                logger.debug("Спонсируемый элемент не найден")
                return None

            if not sponsored_node.click_exists(timeout=timeout):
                logger.debug("Не удалось кликнуть на спонсируемый элемент")
                return None

            if not self.nodes.buttons.share_link.click_exists(timeout=timeout):
                logger.debug("Кнопка share link не найдена или недоступна для клика")
                return None

            link_data = self.nodes.items.content_preview_text.get_text(timeout=timeout)
            if not link_data:
                logger.debug("Данные ссылки не найдены")
                return None

            return self._extract_link_from_content(link_data)

        except Exception as e:
            logger.error(f"Ошибка при извлечении ссылки: {e}")
            return None

        finally:
            self._back_to_feed_news()

    def get_all_data(
        self,
        node: UiObject,
        timeout: int = 10,
    ) -> Tuple[Optional[Image], Optional[str], Optional[str]]:
        """
        Получает все данные из элемента: изображение, текст и ссылку.

        Args:
            node: Родительский UI элемент
            timeout: Таймаут ожидания элементов

        Returns:
            Кортеж (image, text, link)
        """
        image = self.get_image(node)
        text = self.get_text(node)
        link = self.get_link(node, timeout)

        logger.debug(
            f"Получены данные: изображение={'есть' if image else 'нет'}, "
            f"текст={'есть' if text else 'нет'}, ссылка={'есть' if link else 'нет'}"
        )

        return image, text, link
