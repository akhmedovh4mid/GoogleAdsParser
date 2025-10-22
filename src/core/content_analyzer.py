import base64
import json
from io import BytesIO
from typing import Optional

import requests
from httpx import Client
from openai import OpenAI
from PIL.Image import Image

from src.models import ClassificationResult
from src.utils import get_logger

logger = get_logger(name="content-analyzer")


class ContentAnalyzer:
    """Классификатор рекламных объявлений для определения арбитража трафика."""

    def __init__(self, api_key: str, prompt: str, proxy: Optional[str] = None) -> None:
        self.model = "gpt-4o"
        self.prompt = prompt
        self.client = OpenAI(api_key=api_key, http_client=Client(proxy=proxy))
        logger.info("ContentAnalyzer инициализирован")

    def _image_to_base64(self, image: Image) -> str:
        """Конвертирует изображение в base64 data URL."""
        try:
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/png;base64,{img_str}"
        except Exception as e:
            logger.error("Ошибка конвертации изображения: %s", str(e))
            raise

    def classify_arbitrage(
        self, image: Image, description: str = ""
    ) -> ClassificationResult:
        """Классифицирует рекламное объявление на предмет арбитража трафика."""
        logger.info("Начата классификация рекламного объявления")

        try:
            image_data_url = self._image_to_base64(image)

            user_content = []
            if description:
                user_content.append(
                    {"type": "text", "text": f"Контекст: {description}"}
                )
            user_content.append(
                {"type": "image_url", "image_url": {"url": image_data_url}}
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"},
            )

            response_data = response.choices[0].message.content
            data = json.loads(response_data)
            result = ClassificationResult(**data)

            logger.info(
                "Классификация завершена: %s (confidence: %.2f)",
                result["label"],
                result["confidence"],
            )
            return result

        except json.JSONDecodeError as e:
            logger.error("Ошибка парсинга JSON: %s. Ответ: %s", str(e), response_data)
            raise
        except Exception as e:
            logger.error("Ошибка классификации: %s", str(e))
            raise

    def is_arbitrage(self, image: Image, min_confidence: float = 0.6) -> bool:
        """Проверяет, является ли объявление арбитражем трафика."""
        logger.info("Проверка на арбитраж с уверенностью: %.2f", min_confidence)

        try:
            result = self.classify_arbitrage(image)
            is_arbitrage = (
                result["label"] == "arbitrage"
                and result["confidence"] >= min_confidence
            )

            logger.info("Результат проверки: %s", is_arbitrage)
            return is_arbitrage

        except Exception as e:
            logger.error("Ошибка проверки на арбитраж: %s", str(e))
            return False
