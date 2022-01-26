from typing import Optional, Tuple
from pyrr import Vector3, Vector4
from nimble.interface.orbit_camera import OrbitCamera
from nimble.common.models.bounding_box import BoundingBox
from nimble.objects import Model3D


# (origin, direction, inv_direction, sign)
Ray = Tuple[Vector3, Vector3, Vector3, Tuple[int, int, int]]


def create_ray(origin: Vector3, direction: Vector3) -> Ray:
    inv_direction = Vector3((1.0 / direction.x, 1.0 / direction.y, 1.0 / direction.z))
    sign = (inv_direction.x < 0, inv_direction.y < 0, inv_direction.z < 0)
    return (origin, direction, inv_direction, sign)


def get_ray(x: int, y: int, camera: OrbitCamera) -> Ray:
    ray_wor = unproject(x, y, camera).normalized
    orig = camera.position
    ray = create_ray(orig, ray_wor)

    return ray


def unproject(x: int, y: int, camera: OrbitCamera) -> Vector3:
    """Unproject a vector from the viewport to the world."""
    width, height = camera.size.width, camera.size.height
    x = (2.0 * x) / width - 1.0
    y = 1.0 - (2.0 * y) / height

    clip = Vector4((x, y, 0.5, 1.0), dtype="f4")
    eye = (~camera.proj) * clip
    eye = Vector4((eye.x, eye.y, -1.0, 0.0), dtype="f4")

    world = Vector3(((~camera.view) * eye).xyz, dtype="f4")

    return world


def get_pos(x: int, y: int, camera: OrbitCamera) -> Vector3:
    """Get position of mouse in world space with depth."""
    world = unproject(x, y, camera)
    world -= camera.position
    world.normalise()

    return world


def get_ray_between(camera: OrbitCamera, obj: Model3D) -> Ray:
    """Get the ray between the camera and an object in the global axes."""
    direction = (obj.model_matrix * obj.position) - camera.position
    return create_ray(camera.position, direction)


def does_intersect(
    bounds: BoundingBox,
    r: Ray,
) -> bool:
    return ray_intersect(bounds, r) is not None


def ray_intersect(bounds: BoundingBox, r: Ray) -> Optional[Tuple[float, float]]:
    (orig, _dir, invdir, sign) = r

    tmin = (bounds[sign[0]].x - orig.x) * invdir.x
    tmax = (bounds[1 - sign[0]].x - orig.x) * invdir.x

    tymin = (bounds[sign[1]].y - orig.y) * invdir.y
    tymax = (bounds[1 - sign[1]].y - orig.y) * invdir.y

    if (tmin > tymax) or (tymin > tmax):
        return None
    if tymin > tmin:
        tmin = tymin
    if tymax < tmax:
        tmax = tymax

    tzmin = (bounds[sign[2]].z - orig.z) * invdir.z
    tzmax = (bounds[1 - sign[2]].z - orig.z) * invdir.z

    if (tmin > tzmax) or (tzmin > tmax):
        return None
    if tzmin > tmin:
        tmin = tzmin
    if tzmax < tmax:
        tmax = tzmax

    return (tmin, tmax)
