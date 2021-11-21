from pyrr import Matrix44
import moderngl_window as mglw


class Model:
    def __init__(self, camera, prog):
        self.camera = camera
        self.prog = prog
        self.rotation = Matrix44.from_eulers((0.0, 0.0, 0.0), dtype="f4")
        self.translation = Matrix44.from_translation((0.0, 0.0, 0.0), dtype="f4")

    def write_camera_matrix(self):
        self.prog["view"].write(self.camera.matrix)
        self.prog["proj"].write(self.camera.projection.matrix)

    def render(self):
        self.write_camera_matrix()

        model = self.translation * self.rotation
        self.prog["model"].write(model)


class Cube(Model):
    def __init__(self, camera, prog):
        super().__init__(camera, prog)
        self.cube = mglw.geometry.cube(size=(1, 1, 1))

    def render(self):
        super().render()
        self.prog["color"].value = (
            0.1,
            0.1,
            0.1,
        )
        self.cube.render(self.prog)


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
