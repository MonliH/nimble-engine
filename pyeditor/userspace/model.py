from typing import Tuple
from pyrr import Matrix44, Vector3
import moderngl_window as mglw
import moderngl as mgl


BoundingBox = Tuple[Vector3, Vector3]


class Model:
    def __init__(self, camera, prog, bounding_box: BoundingBox = None):
        self.camera = camera
        self.prog = prog
        self.rotation = Vector3((0, 0, 0), dtype="f4")
        self.translation = Vector3((0, 0, 0), dtype="f4")
        self.scale = Vector3((1, 1, 1), dtype="f4")

        if bounding_box is None:
            self.bounding_box = (
                Vector3((0, 0, 0), dtype="f4"),
                Vector3((0, 0, 0), dtype="f4"),
            )
        else:
            self.bounding_box = bounding_box

    def write_camera_matrix(self):
        self.prog["view"].write(self.camera.view)
        self.prog["proj"].write(self.camera.proj)

    @property
    def model(self):
        return (
            Matrix44.from_eulers(self.rotation, dtype="f4")
            * Matrix44.from_translation(self.translation, dtype="f4")
            * Matrix44.from_scale(self.scale, dtype="f4")
        )

    @property
    def bounding_box_world(self):
        world_transform = self.model
        return (world_transform * self.bounding_box[0]), (
            world_transform * self.bounding_box[1]
        )

    def render(self):
        self.write_camera_matrix()

        self.prog["model"].write(self.model)


class Cube(Model):
    def __init__(self, camera, prog):
        super().__init__(
            camera,
            prog,
            bounding_box=(Vector3((-0.5, -0.5, -0.5)), Vector3((0.5, 0.5, 0.5))),
        )
        self.cube = mglw.geometry.cube(size=(1, 1, 1))

    def render(self):
        super().render()
        self.prog["color"].value = (
            0.1,
            0.1,
            0.1,
        )
        self.cube.render(self.prog)

        # 1) Render scene to fbo with color and depth texture attachment
        # 2) Render a quick blur of the linearlized depth buffer with a 3 x 3
        #    kernel to the screen. Treat 1.0 as 0 and anything below 1.0 as 1.0.
        #    so you deal with a simple mask
        # 3) Render the scene from the first fbo on top (with blending or discard fragments with alpha 0)


class Sphere(Model):
    def __init__(self, camera, prog):
        super().__init__(camera, prog)
        self.sphere = mglw.geometry.sphere()

    def render(self):
        super().render()
        self.prog["color"].value = (
            0.1,
            0.1,
            0.1,
        )
        self.sphere.render(self.prog)


class Cylinder(Model):
    def __init__(self, camera, prog, ctx: mgl.Context):
        super().__init__(camera, prog)
        vbo = ctx.buffer(cylinder)
        self.cylinder = ctx.vertex_array()
