import numpy as np
from typing import Optional
from PIL import Image
from moderngl.texture import Texture

from nimble.common.ecs import Processor
from nimble.common.world import World


class OverlayComponent:
    """A 2D component that overlays the 3D scene."""

    def draw(self, buffer: Image.Image):
        """Draws the image to the screen."""
        raise NotImplementedError


class OverlayProcessor(Processor):
    def __init__(self, texture: Optional[Texture] = None):
        self.texture = texture

        if self.texture is not None:
            # Create an empty screen buffer
            self.screen_buffer = Image.new(
                "RGBA", self.texture.size + (4,), (0, 0, 0, 0)
            )
        else:
            self.screen_buffer = None

    def texture_resized(self, texture: Optional[Texture]):
        self.texture = texture
        self.screen_buffer = Image.new("RGBA", self.texture.size, (0, 0, 0, 0))

    def process(self):
        """Draws all overlays to the OpenGL texture."""
        if self.texture is None:
            return

        size = self.screen_buffer.size
        self.screen_buffer.paste((0, 0, 0, 0), (0, 0, *size))  # Fill with black
        self.world: World = self.world

        for _, overlay_component in self.world.get_component(OverlayComponent):
            # Draw all the overlays onto the screen buffer
            overlay_component.draw(self.screen_buffer)

        # Flip the image, because OpenGL expects it that way
        texture = np.flip(np.array(self.screen_buffer), axis=0).astype("u1")

        # Load the image to the texture
        self.texture.write(texture.tobytes())
