from typing import Literal, TypedDict


class ClassificationResult(TypedDict):
    label: Literal["arbitrage", "non_arbitrage"]
    confidence: float
