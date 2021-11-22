from pathlib import Path

resource_dir = (Path(__file__).parent / "resources").resolve()


def shader(name) -> Path:
    return resource_dir / "shaders" / name
