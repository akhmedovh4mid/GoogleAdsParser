from dataclasses import dataclass
from typing import List


@dataclass
class Coordinates:
    """Класс для работы с координатами"""

    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    @property
    def center_x(self) -> int:
        return (self.left + self.right) // 2

    @property
    def center_y(self) -> int:
        return (self.top + self.bottom) // 2

    def to_list(self) -> List[int]:
        return [self.left, self.top, self.right, self.bottom]
