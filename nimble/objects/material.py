from typing import Optional
from moderngl.program import Program
import moderngl as mgl
from pyrr.objects.matrix44 import Matrix44
from nimble.common.shader_manager import Shaders
from nimble.interface.orbit_camera import OrbitCamera

from nimble.objects.geometry import Geometry


class Material:
    def __init__(
        self,
        shader: Program,
        pass_mvp: bool = False,
        draw_wireframe: bool = False,
        draw_bounding_box: bool = False,
        pass_model_matrix: bool = True,
    ):
        self.shader = shader

        self.wireframe = draw_wireframe
        self.wireframe_shader = Shaders()["constant_color"]
        self.wireframe_shader["color"] = (1, 1, 1)

        self.draw_bounding_box = draw_bounding_box

        self.pass_mvp = pass_mvp
        self.pass_model_matrix = pass_model_matrix

    def write_matrix(self, camera: OrbitCamera, model: Optional[Matrix44] = None):
        if self.pass_mvp:
            self.shader["mvp"].write(camera.proj * camera.view * model)
            return

        self.shader["view"].write(camera.view)
        self.shader["proj"].write(camera.proj)

        if self.pass_model_matrix and model is not None:
            self.shader["model"].write(model)

    def render(
        self,
        camera: OrbitCamera,
        geometry: Geometry,
        model: Matrix44,
        bounding_box_buffer: mgl.VertexArray,
    ):
        self.write_matrix(camera, model)
        geometry.vao.render(self.shader, mode=mgl.TRIANGLES)

        if self.wireframe:
            self.wireframe_shader["mvp"].write(camera.proj * camera.view * model)
            geometry.vao.render(self.wireframe_shader, mode=mgl.LINES)

        if self.draw_bounding_box and bounding_box_buffer is not None:
            bounding_box_buffer.program["color"] = (1, 1, 1)
            bounding_box_buffer.program["vp"].write(camera.proj * camera.view)
            bounding_box_buffer.render(mgl.LINE_LOOP)
