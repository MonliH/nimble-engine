from typing import Tuple
from pyrr import Vector3, Vector4
from interface.orbit_camera import OrbitCamera
from userspace.bounding_box import BoundingBox


# (origin, direction, inv_direction, sign)
Ray = Tuple[Vector3, Vector3, Vector3, Tuple[int, int, int]]


def create_ray(origin: Vector3, direction: Vector3) -> Ray:
    inv_direction = Vector3((1.0 / direction.x, 1.0 / direction.y, 1.0 / direction.z))
    sign = (inv_direction.x < 0, inv_direction.y < 0, inv_direction.z < 0)
    return (origin, direction, inv_direction, sign)


def get_ray(x: int, y: int, camera: OrbitCamera) -> Ray:
    width, height = camera.width, camera.height
    x = (2.0 * x) / width - 1.0
    y = 1.0 - (2.0 * y) / height
    z = 1.0

    ray_nds = Vector3((x, y, z), dtype="f4")
    ray_clip = Vector4((ray_nds.x, ray_nds.y, -1.0, 1.0), dtype="f4")
    ray_eye = (~camera.proj) * ray_clip
    ray_eye = Vector4((ray_eye.x, ray_eye.y, -1.0, 0.0), dtype="f4")

    ray_wor = Vector3(((~camera.view) * ray_eye).xyz, dtype="f4").normalized
    orig = camera.position
    ray = create_ray(orig, ray_wor)

    return ray


def does_intersect(
    bounds: BoundingBox,
    r: Ray,
) -> bool:
    (orig, dir, invdir, sign) = r

    tmin = (bounds[sign[0]].x - orig.x) * invdir.x
    tmax = (bounds[1 - sign[0]].x - orig.x) * invdir.x

    tymin = (bounds[sign[1]].y - orig.y) * invdir.y
    tymax = (bounds[1 - sign[1]].y - orig.y) * invdir.y

    if (tmin > tymax) or (tymin > tmax):
        return False
    if tymin > tmin:
        tmin = tymin
    if tymax < tmax:
        tmax = tymax

    tzmin = (bounds[sign[2]].z - orig.z) * invdir.z
    tzmax = (bounds[1 - sign[2]].z - orig.z) * invdir.z

    if (tmin > tzmax) or (tzmin > tmax):
        return False
    if tzmin > tmin:
        tmin = tzmin
    if tzmax < tmax:
        tmax = tzmax

    return True
