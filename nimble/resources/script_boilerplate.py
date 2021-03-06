"""Default script file."""

SCRIPT = """\
from nimble.objects import BaseComponent


class Component(BaseComponent):
\tdef init(self):
\t\t# Initializer; run once when the game starts.
\t\tpass

\tdef process(self, obj):
\t\t# Update loop; runs 60 times a second.
\t\t# `obj` an object that this component is currently attached to.
\t\t#
\t\t# Note: the `obj` object could differ betweent calls if this 
\t\t# component is attached to multiple objects.
\t\tpass
"""
