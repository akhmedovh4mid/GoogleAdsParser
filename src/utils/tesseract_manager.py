import math
from dataclasses import dataclass
from typing import List, Literal, Optional, Tuple

import pytesseract
from PIL.Image import Image as PILImage
from PIL.ImageEnhance import Contrast


@dataclass(frozen=True)
class TesseractCoords:
    """Координаты распознанного текстового блока."""

    top: int
    left: int
    width: int
    height: int

    @property
    def bottom(self) -> int:
        """Нижняя координата блока."""

        return self.top + self.height

    @property
    def right(self) -> int:
        """Правая координата блока."""

        return self.left + self.width

    @property
    def center(self) -> Tuple[int, int]:
        """Центральные координаты блока."""

        return (self.left + self.width // 2, self.top + self.height // 2)


@dataclass
class TesseractResult:
    """Результат распознавания текста Tesseract OCR."""

    level: List[int]
    page_num: List[int]
    block_num: List[int]
    par_num: List[int]
    line_num: List[int]
    word_num: List[int]
    left: List[int]
    top: List[int]
    width: List[int]
    height: List[int]
    conf: List[float]
    text: List[str]

    def get_word_count(self) -> int:
        """Возвращает количество распознанных слов."""

        return len([t for t in self.text if t.strip()])

    def get_average_confidence(self) -> float:
        """Возвращает среднюю уверенность распознавания."""

        valid_confidences = [c for c in self.conf if c != -1]
        return (
            sum(valid_confidences) / len(valid_confidences)
            if valid_confidences
            else 0.0
        )


class Tesseract:
    """Класс для работы с Tesseract OCR."""

    DEFAULT_LANG = "eng"
    SUPPORTED_SCALES = (2, 4, 8)

    @staticmethod
    def get_screen_data(
        image: PILImage,
        lang: str = DEFAULT_LANG,
        contrast_factor: float = 1.5,
        scale: Optional[Literal[2, 4, 8]] = None,
        config: Optional[str] = None,
    ) -> TesseractResult:
        """Распознает текст на изображении с помощью Tesseract OCR.

        Args:
            image: Изображение для распознавания
            lang: Язык для распознавания (по умолчанию "eng")
            contrast_factor: Коэффициент контрастности (1.0 - без изменений)
            scale: Масштаб увеличения изображения перед распознаванием
            config: Дополнительные параметры конфигурации Tesseract

        Returns:
            TesseractResult: Результат распознавания с координатами и текстом

        Raises:
            ValueError: Если передан неподдерживаемый масштаб
        """

        if scale and scale not in Tesseract.SUPPORTED_SCALES:
            raise ValueError(
                f"Масштаб должен быть одним из: {Tesseract.SUPPORTED_SCALES}"
            )

        processed_image = image.copy()

        # Масштабирование изображения
        if scale:
            new_size = (processed_image.width * scale, processed_image.height * scale)
            processed_image = processed_image.resize(new_size)

        # Настройка языка
        actual_lang = lang
        if lang != Tesseract.DEFAULT_LANG:
            actual_lang = f"{lang}+{Tesseract.DEFAULT_LANG}"

        # Коррекция контрастности
        if contrast_factor != 1.0:
            processed_image = Contrast(processed_image).enhance(contrast_factor)

        # Конфигурация Tesseract
        tesseract_config = config or "--oem 3 --psm 6"

        # Распознавание текста
        data_dict: dict = pytesseract.image_to_data(
            image=processed_image,
            lang=actual_lang,
            output_type=pytesseract.Output.DICT,
            config=tesseract_config,
        )

        data = TesseractResult(**data_dict)

        # Масштабирование координат обратно
        if scale:
            data.top = [math.floor(i / scale) for i in data.top]
            data.left = [math.floor(i / scale) for i in data.left]
            data.width = [math.ceil(i / scale) for i in data.width]
            data.height = [math.ceil(i / scale) for i in data.height]

        return data

    @staticmethod
    def find_matches_by_word(
        image: PILImage,
        target_word: str,
        lang: str = DEFAULT_LANG,
        contrast_factor: float = 1.5,
        scale: Optional[Literal[2, 4, 8]] = None,
        min_confidence: float = 60.0,
    ) -> Optional[TesseractCoords]:
        """Находит координаты целевого слова или фразы на изображении.

        Args:
            image: Изображение для поиска
            target_word: Слово или фраза для поиска
            lang: Язык для распознавания
            contrast_factor: Коэффициент контрастности
            scale: Масштаб увеличения изображения
            min_confidence: Минимальная уверенность распознавания

        Returns:
            TesseractCoords: Координаты найденного текста или None
        """

        if not target_word.strip():
            return None

        image_data = Tesseract.get_screen_data(
            image=image,
            scale=scale,
            lang=lang,
            contrast_factor=contrast_factor,
        )

        target_words = target_word.lower().split()
        words = [w.lower() if w else "" for w in image_data.text]

        # Поиск последовательности слов
        for i in range(len(words) - len(target_words) + 1):
            # Проверка уверенности распознавания
            if any(
                image_data.conf[i + j] < min_confidence
                for j in range(len(target_words))
            ):
                continue

            # Проверка совпадения слов
            if words[i : i + len(target_words)] == target_words:
                indices = range(i, i + len(target_words))

                # Вычисление bounding box для всей фразы
                top = min(image_data.top[j] for j in indices)
                left = min(image_data.left[j] for j in indices)
                right = max(image_data.left[j] + image_data.width[j] for j in indices)
                bottom = max(image_data.top[j] + image_data.height[j] for j in indices)

                return TesseractCoords(
                    top=top, left=left, width=right - left, height=bottom - top
                )

        return None

    @staticmethod
    def find_all_matches_by_word(
        image: PILImage,
        target_word: str,
        lang: str = DEFAULT_LANG,
        contrast_factor: float = 1.5,
        scale: Optional[Literal[2, 4, 8]] = None,
        min_confidence: float = 60.0,
    ) -> List[TesseractCoords]:
        """Находит все вхождения целевого слова или фразы на изображении.

        Args:
            image: Изображение для поиска
            target_word: Слово или фраза для поиска
            lang: Язык для распознавания
            contrast_factor: Коэффициент контрастности
            scale: Масштаб увеличения изображения
            min_confidence: Минимальная уверенность распознавания

        Returns:
            List[TesseractCoords]: Список координат всех найденных вхождений
        """

        if not target_word.strip():
            return []

        image_data = Tesseract.get_screen_data(
            image=image,
            scale=scale,
            lang=lang,
            contrast_factor=contrast_factor,
        )

        target_words = target_word.lower().split()
        words = [w.lower() if w else "" for w in image_data.text]

        matches = []

        for i in range(len(words) - len(target_words) + 1):
            # Проверка уверенности распознавания
            if any(
                image_data.conf[i + j] < min_confidence
                for j in range(len(target_words))
            ):
                continue

            # Проверка совпадения слов
            if words[i : i + len(target_words)] == target_words:
                indices = range(i, i + len(target_words))

                # Вычисление bounding box для всей фразы
                top = min(image_data.top[j] for j in indices)
                left = min(image_data.left[j] for j in indices)
                right = max(image_data.left[j] + image_data.width[j] for j in indices)
                bottom = max(image_data.top[j] + image_data.height[j] for j in indices)

                matches.append(
                    TesseractCoords(
                        top=top, left=left, width=right - left, height=bottom - top
                    )
                )

        return matches

    @staticmethod
    def extract_text(
        image: PILImage,
        lang: str = DEFAULT_LANG,
        contrast_factor: float = 1.5,
        scale: Optional[Literal[2, 4, 8]] = None,
    ) -> str:
        """Извлекает весь текст с изображения.

        Args:
            image: Изображение для распознавания
            lang: Язык для распознавания
            contrast_factor: Коэффициент контрастности
            scale: Масштаб увеличения изображения

        Returns:
            str: Распознанный текст
        """

        image_data = Tesseract.get_screen_data(
            image=image,
            scale=scale,
            lang=lang,
            contrast_factor=contrast_factor,
        )

        return " ".join([text for text in image_data.text if text.strip()])
