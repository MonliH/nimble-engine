from nimble.objects import BaseComponent

class Component(BaseComponent):
	def init(self):
		# Initializer; run once when the game starts.
		self.time = 0

	def process(self, obj):
		# Update loop; runs 60 times a second.
		# `obj` an object that this component is currently attached to.
		#
		# Note: the `obj` object could differ betweent calls if this 
		# component is attached to multiple objects.
		speed = 0.0015
		obj.set_rotation((self.time*speed, self.time*speed*2, self.time*speed*3))
		
		self.time += 1
