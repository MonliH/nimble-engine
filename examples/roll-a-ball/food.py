from nimble.objects import BaseComponent

class Component(BaseComponent):
	def init(self):
		self.speed = 0.012

	def process(self, obj):
		obj.rotate((self.speed, self.speed*2, self.speed*3))
