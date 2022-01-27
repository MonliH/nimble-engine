import io
from PyQt5.QtCore import QFile
from PIL import ImageFont, ImageDraw, Image

from nimble.common.overlay.overlay import OverlayComponent


class TextOverlay(OverlayComponent):
    def __init__(self, text, font_size=32):
        file = QFile(":/fonts/OpenSans-Regular.ttf")
        file.setOpenMode(QFile.ReadOnly)
        self.font_bytes = io.BytesIO(file.readAll().data())

        self._text = text
        self._font_size = font_size
        self.position = (0, 0)

    def update_font(self):
        self.font = ImageFont.truetype(self.font_bytes, size=self.font_size)

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
        self.update_font()

    def draw(self, buffer: Image.Image):
        draw = ImageDraw.Draw(buffer)
        draw.text(self.position, self.text, (255, 255, 255), font=self.font)
