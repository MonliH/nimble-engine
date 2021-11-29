from typing import Tuple
from moderngl.vertex_array import VertexArray
from pyrr import Vector3

BoundingBox = Tuple[Vector3, Vector3]


def vao2bounding_box(vao: VertexArray) -> BoundingBox:
    """Create a bounding box from a vertex array."""
    _min = Vector3((0.0, 0.0, 0.0), dtype="f4")
    _max = Vector3((0.0, 0.0, 0.0), dtype="f4")
    return (_min, _max)
