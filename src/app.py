import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from uiautomator2 import Device

from src.config import settings
from src.core import (
    AccountSwitcher,
    ContentAnalyzer,
    DataInterpreter,
    MainClass,
    NavigationManager,
)
from src.models import ConfigItem
from src.utils import GoogleApp, get_logger

logger = get_logger(name="google-parser")


class GoogleParser(MainClass):

    def __init__(self, device: Device, result_dir: str = "./downloads/") -> None:
        super().__init__(device=device)
        logger.info("Инициализация парсера для устройства %s", device.serial)

        self.app = GoogleApp(device=device)
        self.data_interpreter = DataInterpreter(device=device)
        self.account_switcher = AccountSwitcher(device=device)
        self.navigation_manager = NavigationManager(device=device)
        self.content_analyzer = ContentAnalyzer(
            api_key=settings.env.openai_api_key,
            proxy=settings.env.proxy_url,
            prompt=self._get_prompt(),
        )
        self.config = self._get_config()

        self.download_dir = Path(result_dir) / self.device.serial
        self.download_dir.mkdir(exist_ok=True, parents=True)
        logger.debug("Директория для загрузок: %s", self.download_dir)

    def _get_prompt(self) -> str:
        prompt_file_path = settings.path.prompt_file
        logger.debug("Загрузка промпта из: %s", prompt_file_path)

        file_size = prompt_file_path.stat().st_size
        if file_size == 0:
            raise ValueError("Файл с промптом пуст: %s" % prompt_file_path)

        with prompt_file_path.open(
            mode="r",
            encoding="utf-8",
        ) as file:
            prompt = file.read().strip()

        if not prompt:
            raise ValueError(
                "Файл с промптом содержит только пробелы: %s" % prompt_file_path
            )

        logger.debug("Промпт успешно загружен")
        return prompt

    def _get_config(self) -> Optional[List[ConfigItem]]:
        device_serial = self.device.serial
        logger.debug("Загрузка конфигурации для устройства: %s", device_serial)

        config_list: List[ConfigItem] = []

        with settings.path.device_schedule_file.open(
            mode="r",
            encoding="utf-8",
        ) as file:
            schedule_config = json.load(file)

        with settings.path.region_emails_file.open(
            mode="r",
            encoding="utf-8",
        ) as file:
            region_emails = json.load(file)

        if device_serial not in schedule_config:
            logger.warning(
                "Устройство %s не найдено в конфигурации расписания", device_serial
            )
            return config_list

        device_schedule = schedule_config[device_serial]
        schedule_regions = set(device_schedule.keys())
        email_regions = set(region_emails.keys())

        config_list: List[ConfigItem] = []
        for region in schedule_regions:
            if region in email_regions:
                config_list.append(
                    ConfigItem(
                        start_time=device_schedule[region]["start_time"],
                        end_time=device_schedule[region]["end_time"],
                        email=region_emails[region],
                        region=region,
                    )
                )
                logger.debug("Добавлена конфигурация для региона %s", region)

        logger.info(
            "Загружено %d конфигураций для устройства %s",
            len(config_list),
            device_serial,
        )
        return config_list

    def _cleanup(self) -> None:
        current_package = self.device.info.get("currentPackageName")
        logger.debug("Текущее приложение: %s", current_package)

        if current_package == "com.android.chrome":
            logger.debug("Возврат к ленте новостей")
            self._back_to_feed_news()

        self.app.close()

    def get_current_config(self) -> Optional[ConfigItem]:
        if not self.config:
            logger.debug("Конфигурация отсутствует")
            return None

        current_time = datetime.now().strftime("%H:%M")
        logger.debug("Поиск активной конфигурации для времени %s", current_time)

        for region_config in self.config:
            start_time = region_config["start_time"]
            end_time = region_config["end_time"]

            if start_time > end_time:
                if current_time >= start_time or current_time < end_time:
                    logger.debug(
                        "Найдена активная конфигурация: %s", region_config["region"]
                    )
                    return region_config
            else:
                if start_time <= current_time < end_time:
                    logger.debug(
                        "Найдена активная конфигурация: %s", region_config["region"]
                    )
                    return region_config

        logger.debug("Активная конфигурация не найдена")
        return None

    def run(self) -> None:
        if self.config is None:
            logger.warning("Конфигурация не загружена, завершение работы")
            return None

        self._running = True
        logger.info("Запуск основного цикла парсера")

        try:
            self.app.start()

            while True:
                email = self.account_switcher.get_current_user()
                current_config = self.get_current_config()

                if not current_config:
                    logger.debug("Конфигурация не активна, ожидание 60 секунд")
                    time.sleep(60)
                    continue

                if email != current_config["email"]:
                    logger.info(
                        "Смена аккаунта с %s на %s", email, current_config["email"]
                    )
                    self.navigation_manager.go_to_start_feed()
                    self.account_switcher.change_user(email=current_config["email"])
                    time.sleep(0.25)
                    self.app.close()
                    self.app.start()
                    logger.debug("Приложение перезапущено после смены аккаунта")

                need_account_switch = False
                ads_count = 0
                arbitrage_count = 0

                while True:
                    for ads_node in self.navigation_manager.find_ads():
                        if need_account_switch:
                            break

                        new_config = self.get_current_config()
                        if new_config != current_config:
                            logger.info(
                                "Обнаружено изменение конфигурации, требуется смена аккаунта"
                            )
                            need_account_switch = True
                            continue

                        if ads_node:
                            image = self.data_interpreter.get_image(node=ads_node)
                            if self.content_analyzer.is_arbitrage(image=image):
                                text = self.data_interpreter.get_text(node=ads_node)
                                url = self.data_interpreter.get_link(node=ads_node)

                                if url and text:
                                    hash_name = hashlib.md5(
                                        url.encode("utf-8")
                                    ).hexdigest()
                                    download_dir: Path = (
                                        self.download_dir
                                        / current_config["region"]
                                        / hash_name
                                    )
                                    download_dir.mkdir(parents=True, exist_ok=True)

                                    image.save(download_dir / "image.png")
                                    with (download_dir / "info.txt").open(
                                        mode="w", encoding="utf-8"
                                    ) as file:
                                        data = f"url: {url}\ntext: {text}"
                                        file.write(data)

                                    logger.info(
                                        "Сохранена арбитражная реклама: %s...", url[:50]
                                    )

                    if ads_count > 0:
                        logger.debug(
                            "Обработано реклам: %d, арбитражных: %d",
                            ads_count,
                            arbitrage_count,
                        )

                    if need_account_switch:
                        break

                    logger.debug("Обновление ленты и перезапуск приложения")
                    self.app.close()
                    self.app.start()
                    self.navigation_manager.update_feed()
                    time.sleep(5)
                    ads_count = 0
                    arbitrage_count = 0

        except Exception as e:
            logger.error("Ошибка в основном цикле: %s", e)
            raise

        finally:
            self._cleanup()
            logger.info("[%s] Парсинг завершен", self.device.serial)
