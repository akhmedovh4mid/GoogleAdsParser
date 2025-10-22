import time
from typing import Generator, Optional

from uiautomator2 import Device, UiObject

from src.elements import Classes
from src.models import Coordinates
from src.utils import Tesseract, get_logger

from .main_class import MainClass

logger = get_logger("navigation-manager")


class NavigationManager(MainClass):
    def __init__(self, device: Device) -> None:
        super().__init__(device=device)

    def _scroll_content(
        self,
        edge_offset: int = 100,
        action_timeout: float = 0.1,
    ) -> None:
        """
        Скроллит контент ленты вверх.

        Args:
            edge_offset: Отступ от краев для скроллинга
        """
        content_bounds = self.get_content_area_bounds()
        self._swipe(
            start_y=content_bounds.bottom - edge_offset,
            end_y=content_bounds.top + edge_offset,
            wait_time=action_timeout,
        )

    def _scroll_to_ad(
        self,
        ads_coords: Coordinates,
        edge_offset: int = 150,
        action_timeout: float = 0.1,
    ) -> None:
        """
        Скроллит к указанному рекламному объявлению.

        Args:
            ads_coords: Координаты рекламного объявления
        """
        content_bounds = self.get_content_area_bounds()
        self._swipe(
            start_y=ads_coords.top - edge_offset,
            end_y=content_bounds.top,
            wait_time=action_timeout,
        )

    def _find_sponsored(self) -> Optional[Coordinates]:
        """
        Поиск метки 'sponsored' на экране.

        Returns:
            Координаты найденной метки или None
        """
        content_bounds = self.get_content_area_bounds()

        screenshot = self.device.screenshot()
        content_image = screenshot.crop(box=content_bounds.to_list())

        sponsored_crop_coords = Tesseract.find_matches_by_word(
            image=content_image,
            target_word="sponsored",
            scale=2,
            contrast_factor=2,
        )

        if sponsored_crop_coords and not self.nodes.buttons.more_stories.exists:
            return Coordinates(
                top=sponsored_crop_coords.top + content_bounds.top,
                left=sponsored_crop_coords.left + content_bounds.left,
                right=sponsored_crop_coords.right + content_bounds.left,
                bottom=sponsored_crop_coords.bottom + content_bounds.top,
            )

        return None

    def _ads_processing(self) -> Optional[UiObject]:
        """
        Обрабатывает текущий экран для поиска рекламных объявлений.

        Returns:
            Информация о найденной рекламе или None
        """
        sponsored_coords = self._find_sponsored()

        if sponsored_coords:
            self._scroll_to_ad(ads_coords=sponsored_coords)
            return self.get_ads_node()

        return None

    def get_content_area_bounds(self) -> Coordinates:
        """
        Получает границы области контента ленты новостей.

        Returns:
            Границы области контента
        """
        google_app_coords = self.nodes.blocks.google_app.bounds()
        coords = Coordinates(*google_app_coords)

        if self.nodes.blocks.search_box.exists:
            search_box_coords = self.nodes.blocks.search_box.bounds()
            coords.top = search_box_coords[3]

        if self.nodes.blocks.navigation_bar.exists:
            navigation_bar_coords = self.nodes.blocks.navigation_bar.bounds()
            coords.bottom = navigation_bar_coords[1]

        return coords

    def get_ads_node(self) -> Optional[UiObject]:
        """
        Находит наиболее вероятный узел с рекламным контентом.

        Returns:
            Найденный узел с рекламой или None
        """
        content_coords = self.get_content_area_bounds()
        content_height = content_coords.bottom - content_coords.top

        nodes = self.nodes.blocks.google_app.child(**Classes.view_group)
        candidate_node = None
        candidate_height = 0

        for node in nodes:
            node_bounds = node.bounds()
            node_height = node_bounds[3] - node_bounds[1]

            if node_height > content_height:
                continue

            if node_height > candidate_height and Tesseract.find_matches_by_word(
                image=node.screenshot(),
                target_word="sponsored",
            ):
                candidate_node = node
                candidate_height = node_height

        return candidate_node

    def go_to_start_feed(
        self,
        timeout: int = 15,
        edge_offset: int = 100,
        topbar_height: int = 250,
        action_timeout: float = 0.1,
    ) -> None:
        """
        Перемещает ленту в начальное положение.

        Args:
            timeout: Таймаут для ожидания элементов
            edge_offset: Отступ от краев экрана
            topbar_height: Высота области верхней панели
        """
        if self.nodes.buttons.selected_account.exists:
            return

        content_coords = self.get_content_area_bounds()
        self._swipe(
            start_y=content_coords.top + edge_offset,
            end_y=content_coords.top + edge_offset + topbar_height,
            wait_time=action_timeout,
        )

        self.nodes.buttons.home.click(timeout=timeout)
        time.sleep(action_timeout)

        content_coords = self.get_content_area_bounds()
        self._swipe(
            start_y=content_coords.bottom - edge_offset,
            end_y=content_coords.bottom - edge_offset - topbar_height,
            wait_time=action_timeout,
        )

        content_coords = self.get_content_area_bounds()
        self._swipe(
            start_y=content_coords.top + edge_offset,
            end_y=content_coords.top + edge_offset + topbar_height,
            wait_time=action_timeout,
        )

    def update_feed(
        self,
        timeout: int = 15,
        edge_offset: int = 100,
        action_timeout: float = 0.25,
    ) -> None:
        """
        Генератор для поиска рекламных объявлений в ленте.

        Yields:
            Информация о найденной рекламе или None

        Notes:
            Останавливается при появлении кнопки 'More stories'
        """
        self.go_to_start_feed(timeout=timeout, edge_offset=edge_offset)

        content_coords = self.get_content_area_bounds()
        self._swipe(
            start_y=content_coords.top + edge_offset,
            end_y=content_coords.bottom - edge_offset,
            swipe_speed_factor=15000,
            wait_time=action_timeout,
        )

    def find_ads(
        self,
        max_iterations: int = 15,
    ) -> Generator[Optional[UiObject], None, None]:
        """
        Генератор для поиска рекламных объявлений в ленте.

        Yields:
            Optional[FeedScrollerItem]: Информация о найденной рекламе или None

        Notes:
            Останавливается при появлении кнопки 'More stories'
        """
        logger.info("Запуск поиска рекламных объявлений в ленте")
        iterations = 0
        ads_found = 0

        while (
            not self.nodes.buttons.more_stories.exists and iterations <= max_iterations
        ):
            iterations += 1
            logger.debug("Итерация поиска рекламы #%d", iterations)

            if iterations == 1:
                logger.debug("Первичная обработка рекламы")
                sponsored_coords = self._find_sponsored()
                if sponsored_coords:
                    self._scroll_to_ad(ads_coords=sponsored_coords)

            ads_item = self._ads_processing()
            if ads_item:
                ads_found += 1
                logger.info("Найдено рекламное объявление #%d", ads_found)

            yield ads_item

            self._scroll_content()

        logger.info(
            "Поиск рекламы завершен. Итераций: %d, найдено реклам: %d",
            iterations,
            ads_found,
        )
