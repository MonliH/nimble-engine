from nimble.objects import BaseComponent
from nimble.common import TextOverlay, OverlayComponent


class Component(BaseComponent):
	def init(self):
		# Initializer; run once when the game starts.
		self.text_entity = self.world.create_entity()
		self.world.add_overlay_component(self.text_entity, TextOverlay("Hello"))

	def process(self, obj):
		# Update loop; runs 60 times a second.
		# `obj` an object that this component is currently attached to.
		#
		# Note: the `obj` object could differ betweent calls if this 
		# component is attached to multiple objects.
		pass
