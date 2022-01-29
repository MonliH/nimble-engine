from pyrr import Matrix44


def create(scale: tuple, rotation: tuple, translation: tuple) -> Matrix44:
    """Create a transformation matrix from a scale, rotation, and translation."""
    return (
        Matrix44.from_scale(scale, dtype="f4")
        * Matrix44.from_eulers(rotation, dtype="f4")
        * Matrix44.from_translation(translation, dtype="f4")
    )
