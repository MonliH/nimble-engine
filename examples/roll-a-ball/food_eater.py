from nimble.objects import BaseComponent, PhysicsComponent, CustomComponentQuery
from nimble.common import TextOverlay

class Component(BaseComponent):
	def init(self):
		self.score = 0
		self.text_overlay = TextOverlay("")
		self.text_overlay.font_size = 50
		self.text_overlay.position = (10, 0)
		self.world.add_overlay_component(self.world.create_entity(), self.text_overlay)
		self.update_text()
	
	def update_text(self):
		self.text_overlay.text = f"Score: {self.score}"

	def process(self, obj):
		physics_component = self.world.get_obj_component(obj, PhysicsComponent)
		
        # Loop through all the food objects with physics components and script called "food"
		for id, components in self.world.get_components(PhysicsComponent, CustomComponentQuery("food")):
			food_collider = components[0]
			if physics_component.collides_with(food_collider):
				food_collider.model.set_active(False)
				self.score += 1
				self.update_text()