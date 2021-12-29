from typing import Tuple
from moderngl.vertex_array import VertexArray
from pyrr import Vector3
import numpy as np
from pyrr.objects.matrix44 import Matrix44

BoundingBox = Tuple[Vector3, Vector3]


def vao2bounding_box(vao: VertexArray) -> BoundingBox:
    """Create a bounding box from a vertex array."""
    _min = Vector3((0.0, 0.0, 0.0), dtype="f4")
    _max = Vector3((0.0, 0.0, 0.0), dtype="f4")
    return (_min, _max)


def join(b1: BoundingBox, b2: BoundingBox) -> BoundingBox:
    """Join two bounding boxes."""
    points = np.stack([b1[0], b2[0], b1[1], b2[1]])
    mi = Vector3(np.amin(points, axis=0), dtype="f4")
    ma = Vector3(np.amax(points, axis=0), dtype="f4")
    return (mi, ma)


def apply_world_transform(b: BoundingBox, transform: Matrix44) -> BoundingBox:
    """Convert a bounding box into world space."""
    transformed = get_bounding_box_points(b)
    points = transformed.dot(transform.T)
    points = np.true_divide(points[:, :3], points[:, [-1]])
    mi = Vector3(np.amin(points, axis=0), dtype="f4")
    ma = Vector3(np.amax(points, axis=0), dtype="f4")
    return (mi, ma)


def get_bounding_box_points(b: BoundingBox) -> np.ndarray:
    """Get all 8 points of a bounding box."""
    _1 = b[0]
    _2 = b[1]
    return np.array(
        [
            [_1[0], _1[1], _1[2], 1],
            [_2[0], _2[1], _2[2], 1],
            [_2[0], _1[1], _1[2], 1],
            [_1[0], _2[1], _1[2], 1],
            [_1[0], _1[1], _2[2], 1],
            [_2[0], _1[1], _2[2], 1],
            [_2[0], _2[1], _1[2], 1],
            [_1[0], _2[1], _2[2], 1],
        ],
        dtype="f4",
    )
