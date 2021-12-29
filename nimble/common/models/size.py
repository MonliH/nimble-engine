from typing import Tuple
from nimble.common.event_listener import WindowObserver


class Size:
    def __init__(self, width: int, height: int):
        self._width = width
        self._height = height

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def set_dims(self, new_width: int, new_height: int):
        self._width = new_width
        self._height = new_height

    @property
    def as_tuple(self) -> Tuple[int, int]:
        return self._width, self._height

    @property
    def aspect_ratio(self) -> float:
        return self._width / self._height


class ViewportSize(Size, WindowObserver):
    def __init__(self, *args):
        super().__init__(*args)

    def window_resized(self, width: int, height: int):
        self.set_dims(width, height)
