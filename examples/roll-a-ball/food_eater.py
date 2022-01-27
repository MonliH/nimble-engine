from nimble.objects import BaseComponent, PhysicsComponent, CustomComponentQuery
from nimble.common import TextOverlay, OverlayComponent

class Component(BaseComponent):
	def init(self):
		# Initializer; run once when the game starts.
		self.score = 0
		self.text_overlay = TextOverlay("")
		self.text_overlay.font_size = 50
		self.text_overlay.position = (10, 0)
		self.world.add_overlay_component(self.world.create_entity(), self.text_overlay)
		self.update_text()
	
	def update_text(self):
		self.text_overlay.text = f"Score: {self.score}"

	def process(self, obj):
		# Update loop; runs 60 times a second.
		# `obj` an object that this component is currently attached to.
		#
		# Note: the `obj` object could differ betweent calls if this 
		# component is attached to multiple objects.
		physics_component = self.world.get_obj_component(obj, PhysicsComponent)
		
		for id, components in self.world.get_components(PhysicsComponent, CustomComponentQuery("food")):
			food_collider = components[0]
			if physics_component.collides_with(food_collider):
				food_collider.model.set_active(False)
				self.score += 1
				self.update_text()

