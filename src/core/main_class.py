import time

from uiautomator2 import Device

from src.elements import Nodes


class MainClass:

    def __init__(self, device: Device) -> None:
        self.device = device
        self.nodes = Nodes(device=device)

        self._screen_width = self.device.info["displayWidth"]
        self._screen_height = self.device.info["displayHeight"]

    def _swipe(
        self,
        start_y: int,
        end_y: int,
        min_swipe_length: int = 35,
        swipe_speed_factor: int = 2000,
        wait_time: float = 0.1,
    ) -> None:
        """
        Выполняет свайп по вертикали.

        Args:
            start_y: Начальная координата Y
            end_y: Конечная координата Y
            min_swipe_length: Минимальная длина свайпа
            swipe_speed_factor: Фактор скорости свайпа
            wait_time: Время ожидания после свайпа
        """
        swipe_length = abs(start_y - end_y)
        if swipe_length < min_swipe_length:
            return None

        duration = 1 * (swipe_length / swipe_speed_factor)
        self.device.swipe_points(
            points=[
                (self._screen_width // 2, start_y),
                (self._screen_width // 2, end_y),
            ],
            duration=duration,
        )
        time.sleep(wait_time)

    def _back_to_feed_news(
        self,
        timeout: float = 0.5,
        max_back_presses: int = 3,
    ) -> None:
        """
        Возвращает в ленту новостей с помощью кнопки 'Назад'.

        Args:
            max_back_presses: Максимальное количество нажатий
        """
        back_presses = 0

        while (
            not self.nodes.blocks.google_app.exists and back_presses < max_back_presses
        ):
            self.device.press("back")
            back_presses += 1
            time.sleep(timeout)
