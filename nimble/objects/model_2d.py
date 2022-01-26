from __future__ import annotations
from PIL import ImageFont, ImageDraw, Image
from typing import Optional
from moderngl.texture import Texture
import numpy as np

from nimble.objects.base_model import BaseModel
from nimble.objects.material import Material

Vector2 = np.array


class Basic2DMaterial(Material):
    def __init__(self):
        self.color = (1, 1, 1)
        self.params = {"color": self.color}


class Model2D(BaseModel):
    """Objects that are overlayed over the 3D scene, e.g. UI elements"""

    def __init__(self, position: Optional[Vector2] = None, **kwargs):
        super().__init__(**kwargs)
        self.position = position if position is not None else Vector2((0, 0))
        self.material = Basic2DMaterial()

    def render(self, screen: Texture):
        raise NotImplementedError


class TextModel(Model2D):
    def __init__(self, initial_text: str = "", font_size: int = 10, **kwargs):
        super().__init__(**kwargs)
        self.kwargs = {"font_size": font_size, "initial_text": initial_text}
        self.text = initial_text

        self.font_size = font_size
        self.font = ImageFont.truetype("./nimble/resources/fonts/OpenSans-Regular.ttf")

        self.update_bitmap()

    def set_font_size(self, size: int):
        self.kwargs["font_size"] = self.font_size = size
        self.update_bitmap()

    def set_text(self, text: str):
        self.text = text
        self.update_bitmap()

    def set_initial_text(self, text: str):
        self.kwargs["initial_text"] = self.text = text
        self.update_bitmap()

    def update_bitmap(self):
        image = Image.new("RGBA", (600, 150), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        self.font = self.font.font_variant(size=self.font_size)
        draw.text((0, 0), self.text, fill=(255, 255, 255), font=self.font)
        self.image = np.array(image.resize((188, 45), Image.ANTIALIAS))
        print(self.image.shape)

    def position_changed(self):
        pass

    def render(self, screen: Texture):
        pass
