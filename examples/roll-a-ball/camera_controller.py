from nimble.objects import BaseComponent
from math import radians

class Component(BaseComponent):
	def init(self):
		self.camera = self.world.get_camera()
		spherical_coords = self.camera.spherical
		spherical_coords.phi = radians(50)
		spherical_coords.theta = radians(0)
		spherical_coords.radius = 6

	def process(self, obj):
		# Make camera follow object
		self.camera.target = obj.position
		self.camera.target.y = 0.001
