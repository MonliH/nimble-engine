from typing import Optional
import numpy as np
from numpy import ndarray
from PIL import ImageFont, ImageDraw, Image

from nimble.common.overlay.overlay import OverlayComponent


font = ImageFont.truetype("./nimble/resources/fonts/OpenSans-Regular.ttf")


class TextOverlay(OverlayComponent):
    def __init__(self, text, font_size=32):
        self._text = text
        self._font_size = font_size
        self.position = (0, 0)
        self.font = font.font_variant(size=self.font_size)

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, text: str):
        self._text = text

    @property
    def font_size(self) -> int:
        return self._font_size

    @font_size.setter
    def font_size(self, font_size: int):
        self._font_size = font_size
        self.font = font.font_variant(size=self.font_size)

    def draw(self, buffer: Image.Image):
        draw = ImageDraw.Draw(buffer)
        draw.text(self.position, self.text, (255, 255, 255), font=self.font)
