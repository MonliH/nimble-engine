from nimble.objects import BaseComponent, PhysicsComponent
from nimble.common import Key, Vector3

class Component(BaseComponent):
	def init(self):
		pass

	def process(self, obj):
		physics_component = self.world.get_obj_component(obj, PhysicsComponent)
		
		# Accumulate a force vector for keys
		speed = 0.7
		force = Vector3((0.0, 0.0, 0.0))
		if self.keys[Key.W] or self.keys[Key.UP]:
			force.z -= speed
		if self.keys[Key.A] or self.keys[Key.LEFT]:
			force.x -= speed
		if self.keys[Key.S] or self.keys[Key.DOWN]:
			force.z += speed
		if self.keys[Key.D] or self.keys[Key.RIGHT]:
			force.x += speed
		
		if force.length != 0.0:
			# Normalize the vector
			force = force.normalized
			# Finally, apply the force
			physics_component.apply_force(force)
		
	