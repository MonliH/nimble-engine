from pyrr import Matrix44


def create(scale: tuple, rotate: tuple, translate: tuple) -> Matrix44:
    return (
        Matrix44.from_scale(scale, dtype="f4")
        * Matrix44.from_eulers(rotate, dtype="f4")
        * Matrix44.from_translation(translate, dtype="f4")
    )
